"""Turn the turntable RGBA frames into the opaque frames the page shows.

The frames come off the same shadow-catcher floor the hero used, so each one carries
a real contact shadow.  A shadow catcher returns the studio light it receives as
partial alpha, which fogs the whole background - the hero had exactly the same
problem and solved it in compose_dmax.py by laying the render over a generated
studio sweep.  This does the same, and reuses compose_dmax.py's own
studio_background() so the turntable ground and backdrop cannot drift from the hero.

The one thing that must not move between frames is the crop.  Fitting each frame to
its own bounding box would make the truck jump and breathe as it turned, which is the
jitter this whole build exists to avoid.  So the crop box is computed ONCE, from the
union of every frame's bounding box, and applied to all of them identically.  The
horizon the background gradient is anchored to is likewise fixed, computed from the
camera geometry rather than read off each frame.

Run:  python compose_turntable.py --raw _raw_tt --out . --frames 36 --outw 1240
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
HERO_DIR = os.path.dirname(HERE)


def _load_compose_dmax():
    """Import compose_dmax.py by path, purely for studio_background()."""
    path = os.path.join(HERO_DIR, "compose_dmax.py")
    spec = importlib.util.spec_from_file_location("compose_dmax", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--frames", type=int, required=True)
    p.add_argument("--outw", type=int, default=1240, help="embed width; height follows aspect")
    p.add_argument("--quality", type=int, default=86)
    p.add_argument("--margin", type=float, default=0.02)
    return p.parse_args()


def vehicle_bbox(alpha, thresh=200):
    solid = alpha > thresh
    rows = np.where(solid.any(axis=1))[0]
    cols = np.where(solid.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return None
    return int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1


def main() -> int:
    a = parse()
    raw = a.raw if os.path.isabs(a.raw) else os.path.join(HERE, a.raw)
    out = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
    framedir = os.path.join(out, "frames")
    os.makedirs(framedir, exist_ok=True)

    cd = _load_compose_dmax()
    print("studio_background reused from", os.path.join(HERO_DIR, "compose_dmax.py"))

    with open(os.path.join(raw, "turntable_render_report.json")) as fh:
        rep = json.load(fh)
    resx, resy = rep["resolution"]
    print("render report: %d frames at %dx%d, ortho_scale %.4f, az %.1f el %.1f"
          % (rep["motion"]["frames"], resx, resy, rep["camera"]["ortho_scale_used"],
             rep["camera"]["az_deg"], rep["camera"]["el_deg"]))

    # ---------------------------------------------------------------- read + measure
    frames, boxes = [], []
    for j in range(a.frames):
        f = os.path.join(raw, "f_%03d.png" % j)
        if not os.path.exists(f):
            raise SystemExit("missing frame %s" % f)
        im = Image.open(f)
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        if im.size != (resx, resy):
            raise SystemExit("frame %d is %s, expected %dx%d" % (j, im.size, resx, resy))
        arr = np.asarray(im)
        bb = vehicle_bbox(arr[..., 3])
        if bb is None:
            raise SystemExit("frame %d has no solid pixels" % j)
        frames.append(im)
        boxes.append(bb)

    ux0 = min(b[0] for b in boxes)
    uy0 = min(b[1] for b in boxes)
    ux1 = max(b[2] for b in boxes)
    uy1 = max(b[3] for b in boxes)
    print("union vehicle bbox over %d frames: x %d..%d (w %d)  y %d..%d (h %d)"
          % (len(boxes), ux0, ux1, ux1 - ux0, uy0, uy1, uy1 - uy0))

    # ONE crop box, used for every frame.  Nothing is fitted per frame.
    uw, uh = ux1 - ux0, uy1 - uy0
    mx = int(round(uw * a.margin))
    my = int(round(uh * a.margin))
    cx0, cy0 = max(0, ux0 - mx), max(0, uy0 - my)
    cx1, cy1 = min(resx, ux1 + mx), min(resy, uy1 + my)
    cw, ch = cx1 - cx0, cy1 - cy0
    print("fixed crop, identical for all frames: (%d,%d)-(%d,%d) -> %dx%d"
          % (cx0, cy0, cx1, cy1, cw, ch))

    # ---------------------------------------------------------------- horizon
    # Anchor the background gradient to the real ground line, from the camera that
    # made the render, not from each frame's silhouette.  The camera never moves,
    # so this number is the same for every frame by construction.
    M = np.array(rep["camera"]["matrix"], dtype=float)
    scale = float(rep["camera"]["ortho_scale_used"])
    half_w = scale / 2.0
    half_h = half_w * resy / resx
    Minv = np.linalg.inv(M)

    def project(p):
        v = Minv @ np.array([p[0], p[1], p[2], 1.0])
        return ((v[0] / half_w * 0.5 + 0.5) * resx, (0.5 - v[1] / half_h * 0.5) * resy)

    fa = rep["model"]["size_m"]  # only used for the log line
    ground_rows = {}
    for name, y in (("front_axle", -1.729605950856934), ("rear_axle", 1.3953940491430659),
                    ("nose", -2.7021021842956543), ("tail", 2.7021031379699707)):
        ground_rows[name] = round(project((0.0, y, 0.0))[1], 1)
    horizon_render = max(ground_rows.values())          # lowest contact line on screen
    horizon_crop = horizon_render - cy0
    horizon_frac = float(np.clip(horizon_crop / ch, 0.05, 0.98))
    print("ground line rows (render px): %s -> horizon %.1f (crop %.1f, %.3f of height)"
          % (ground_rows, horizon_render, horizon_crop, horizon_frac))

    # ---------------------------------------------------------------- composite
    bg = cd.studio_background(cw, ch, horizon_crop)
    bga = np.asarray(bg).astype(np.float32) / 255.0

    ow = a.outw
    oh = int(round(ow * ch / cw))
    written, sizes, crops = [], [], []
    for j, im in enumerate(frames):
        crop = im.crop((cx0, cy0, cx1, cy1))
        ca = np.asarray(crop).astype(np.float32)
        a_lin = ca[..., 3:4] / 255.0
        rgb_lin = ca[..., :3] / 255.0
        comp = rgb_lin * a_lin + bga * (1.0 - a_lin)
        img = Image.fromarray((comp * 255.0).clip(0, 255).astype(np.uint8), "RGB")
        # the same slight S-curve the hero got, so the two match
        hn = np.asarray(img).astype(np.float32) / 255.0
        hn = np.clip(hn, 0.0, 1.0)
        hn = hn * hn * (3.0 - 2.0 * hn) * 0.55 + hn * 0.45
        img = Image.fromarray((hn * 255.0).clip(0, 255).astype(np.uint8), "RGB")
        if (ow, oh) != (cw, ch):
            img = img.resize((ow, oh), Image.LANCZOS)
        fn = "t_%03d.jpg" % j
        img.save(os.path.join(framedir, fn), "JPEG", quality=a.quality,
                 optimize=True, progressive=False, subsampling=1)
        sz = os.path.getsize(os.path.join(framedir, fn))
        written.append(fn)
        sizes.append(sz)
        crops.append([crop.getbbox()[0] if crop.getbbox() else 0])
        if (j + 1) % 6 == 0 or j == 0:
            print("  composited %2d/%d  %s  %.1f KB" % (j + 1, a.frames, fn, sz / 1024.0))

    total = sum(sizes)
    print("\n%d frames, %.2f MB JPEG total, mean %.1f KB, max %.1f KB"
          % (len(written), total / 1048576.0, total / len(written) / 1024.0,
             max(sizes) / 1024.0))

    # ---------------------------------------------------------------- drift check
    widths = [b[2] - b[0] for b in boxes]
    heights = [b[3] - b[1] for b in boxes]
    cx_img, cy_img = resx / 2.0, resy / 2.0
    centres = [((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0) for b in boxes]

    # scale stability: the ratio of each frame's silhouette to its own yaw is not
    # constant (a truck is longer than it is wide), so scale is proved a different
    # way - the camera is fixed and the fit was taken once, so the only thing that
    # can change is yaw.  What is measured here is that the truck's centre stays put.
    drift = {
        "crop_box_render_px": [cx0, cy0, cx1, cy1],
        "crop_size": [cw, ch],
        "crop_identical_all_frames": True,
        "embed_size": [ow, oh],
        "frames": len(written),
        "bbox_width_px": {"min": min(widths), "max": max(widths),
                          "spread": max(widths) - min(widths)},
        "bbox_height_px": {"min": min(heights), "max": max(heights),
                           "spread": max(heights) - min(heights)},
        "bbox_centre_offset_from_image_centre_px": {
            "max_abs_x": round(max(abs(c[0] - cx_img) for c in centres), 1),
            "max_abs_y": round(max(abs(c[1] - cy_img) for c in centres), 1),
            "x_pct_of_width": round(100.0 * max(abs(c[0] - cx_img) for c in centres) / resx, 2),
            "y_pct_of_height": round(100.0 * max(abs(c[1] - cy_img) for c in centres) / resy, 2),
        },
        "note": ("The bbox width changes by design: an end-on truck really does project "
                 "narrower than a broadside one, so width spread is the rotation, not "
                 "jitter. Scale stability is guaranteed structurally instead - the camera "
                 "is fixed and ortho_scale is computed once over the union of all yaws, so "
                 "no frame can grow or shrink. The centre offset is the check that the "
                 "rotation axis is centred in frame."),
        "horizon_row_render_px": horizon_render,
        "ground_rows_render_px": ground_rows,
        "jpeg_bytes": sizes,
        "jpeg_total_bytes": total,
    }

    doc = {
        "source_render": os.path.join(raw, "turntable_render_report.json"),
        "render": {"resolution": [resx, resy],
                   "frames": rep["motion"]["frames"],
                   "step_deg": rep["motion"]["step_deg"],
                   "samples": rep["samples"],
                   "ortho_scale_used": rep["camera"]["ortho_scale_used"],
                   "az_deg": rep["camera"]["az_deg"], "el_deg": rep["camera"]["el_deg"]},
        "drift": drift,
        "frames": written,
        "background": ("studio sweep from compose_dmax.studio_background(), the same "
                       "function that backs dmax_hero.png"),
    }
    with open(os.path.join(out, "turntable_frames.json"), "w") as fh:
        json.dump(doc, fh, indent=1)
    print("wrote", os.path.join(out, "turntable_frames.json"))
    print("=== COMPOSE DONE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
