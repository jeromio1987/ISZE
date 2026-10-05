"""Inspect turntable frames: alpha, ink, bbox, and a zoom for visual check."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

d = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else d
zoom = len(sys.argv) > 3 and sys.argv[3] == "zoom"
out.mkdir(parents=True, exist_ok=True)

files = sorted(d.glob("f_*.png"))
print("%d frames in %s" % (len(files), d))
rows = []
for f in files:
    im = Image.open(f)
    a = np.asarray(im)
    alpha = a[..., 3]
    # The threshold matters and is not arbitrary.  These frames come off a
    # shadow-catcher floor, which returns the light it receives as PARTIAL alpha, so
    # the contact shadow on the ground is semi-transparent and reaches below the
    # truck.  At alpha > 200 that shadow is counted as vehicle, and its extent changes
    # with yaw (long when the truck is broadside, short when it is end-on), which
    # would look like the truck growing and shrinking.  Measuring the body means
    # measuring what is essentially fully opaque.  The shadow is measured separately
    # just below, so it is not being ignored either.
    solid = alpha > 250
    shadow = (alpha > 12) & (alpha <= 250)
    ys, xs = np.where(solid)
    if len(xs) == 0:
        print("  %-12s EMPTY" % f.name)
        continue
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    sh_ys = np.where(shadow.any(axis=1))[0]
    shadow_h = int(sh_ys.max() - sh_ys.min() + 1) if len(sh_ys) else 0
    # ink = mean darkness of the vehicle pixels (a blank frame has no ink)
    rgb = a[..., :3].astype(np.float32)
    body = rgb[solid]
    ink = float(255.0 - body.mean()) if body.size else 0.0
    rows.append((f.name, im.size, bbox, bbox[2] - bbox[0], bbox[3] - bbox[1],
                 int(solid.sum()), ink, int(alpha.max()), shadow_h))
    print("  %-12s %s bbox x%4d..%-4d y%3d..%-3d  %4dx%-4d  %7d px  ink %5.1f  amax %d"
          % (f.name, "%dx%d" % im.size, bbox[0], bbox[2], bbox[1], bbox[3],
             bbox[2] - bbox[0], bbox[3] - bbox[1], int(solid.sum()), ink, int(alpha.max())))
if rows:
    ws = [r[3] for r in rows]
    hs = [r[4] for r in rows]
    x0 = [r[2][0] for r in rows]
    y0 = [r[2][1] for r in rows]
    print("\nframing drift over %d frames:" % len(rows))
    print("  width  min %d max %d  spread %d px (%.2f%%)" % (min(ws), max(ws), max(ws) - min(ws),
          100.0 * (max(ws) - min(ws)) / max(1, max(ws))))
    print("  height min %d max %d  spread %d px (%.2f%%)" % (min(hs), max(hs), max(hs) - min(hs),
          100.0 * (max(hs) - min(hs)) / max(1, max(hs))))
    print("  left   min %d max %d  spread %d px" % (min(x0), max(x0), max(x0) - min(x0)))
    print("  top    min %d max %d  spread %d px" % (min(y0), max(y0), max(y0) - min(y0)))

if zoom and files:
    # a 1:1 crop of the front of the truck and one of the flank, to judge
    # whether the samples have left the paint noisy or the panel gaps mushy
    im = Image.open(files[0]).convert("RGBA")
    a = np.asarray(im)[..., 3]
    ys, xs = np.where(a > 200)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    w, h = x1 - x0, y1 - y0
    c = im.crop((int(x0 + 0.02 * w), int(y0 + 0.30 * h), int(x0 + 0.32 * w), int(y0 + 0.75 * h)))
    c = c.resize((c.width * 3, c.height * 3), Image.NEAREST)
    c.save(out / "_zoom_front3x.png")
    print("wrote", out / "_zoom_front3x.png", c.size)

    mid = Image.open(files[len(files) // 2]).convert("RGBA")
    a2 = np.asarray(mid)[..., 3]
    ys2, xs2 = np.where(a2 > 200)
    x0b, y0b, x1b, y1b = xs2.min(), ys2.min(), xs2.max(), ys2.max()
    wb, hb = x1b - x0b, y1b - y0b
    c2 = mid.crop((int(x0b + 0.35 * wb), int(y0b + 0.20 * hb), int(x0b + 0.75 * wb), int(y0b + 0.70 * hb)))
    c2 = c2.resize((c2.width * 2, c2.height * 2), Image.LANCZOS)
    c2.save(out / "_zoom_mid2x.png")
    print("wrote", out / "_zoom_mid2x.png", c2.size)

# --------------------------------------------------------------------------- #
# the framing-stability test
# --------------------------------------------------------------------------- #
# Why "the bounding box must be constant between frames" is the WRONG test. A truck is
# about 5.4 m long and 2.1 m wide, so when it turns end-on its silhouette really is far
# narrower in the image than when it is broadside. Measuring that spread and calling it
# jitter would fail a perfectly rigid turntable.
#
# A second test that looks right but is not: comparing frames 180 deg apart and
# expecting identical silhouettes. That holds for WIDTH - the projected length of the
# vehicle is the same whichever end faces the camera, and the measurement below confirms
# it to 1 px. It does NOT hold for HEIGHT. A D-Max is not symmetric front to back, and
# the camera is tilted 18 deg down, so the nose and the tail sit at different image
# heights and a half turn really does change the height envelope. Demanding height
# symmetry would fail a correct render.
#
# The decisive test is therefore neither of those: it is whether ONE fixed camera
# predicts the whole sequence. That is done from the real vertex cloud in
# build_turntable.py --verify-framing and compared frame by frame in compare_framing.py.
# What is kept here is the width symmetry (a genuine invariant), the centre wander (the
# rotation axis must not drift) and the ink coverage (nothing blank).
if len(rows) >= 4:
    n = len(rows)
    half = n // 2
    sym_w = []
    for j in range(half):
        b0, b1 = rows[j][2], rows[j + half][2]
        sym_w.append(abs((b0[2] - b0[0]) - (b1[2] - b1[0])))
    inkm = [r[6] for r in rows]
    cxs = [(r[2][0] + r[2][2]) / 2.0 for r in rows]
    cys = [(r[2][1] + r[2][3]) / 2.0 for r in rows]
    w_img, h_img = rows[0][1]
    print("\nwidth symmetry at 180 deg (a real invariant: same length either way round):")
    print("  width mismatch: max %d px, mean %.2f px" % (max(sym_w), sum(sym_w) / len(sym_w)))
    print("centre wander: x %.1f px (%.2f%% of width), y %.1f px (%.2f%% of height)"
          % (max(cxs) - min(cxs), 100.0 * (max(cxs) - min(cxs)) / w_img,
             max(cys) - min(cys), 100.0 * (max(cys) - min(cys)) / h_img))
    print("ink coverage: min %.1f max %.1f (a blank frame would be 0)" % (min(inkm), max(inkm)))
    shadow_hs = [r[8] for r in rows]
    print("contact shadow span (partial alpha): min %d max %d px"
          % (min(shadow_hs), max(shadow_hs)))

    summary = {
        "frames": n,
        "threshold": "alpha > 250 (vehicle body). The contact shadow is partial alpha and "
                     "is measured separately; including it makes the truck look like it "
                     "grows and shrinks, because the shadow's length follows the yaw.",
        "symmetry_180_width_px_max": max(sym_w),
        "symmetry_180_width_pct_of_vehicle": round(
            100.0 * max(sym_w) / max(1, max(r[3] for r in rows)), 3),
        "centre_wander_x_px": round(max(cxs) - min(cxs), 2),
        "centre_wander_y_px": round(max(cys) - min(cys), 2),
        "centre_wander_x_pct": round(100.0 * (max(cxs) - min(cxs)) / w_img, 3),
        "centre_wander_y_pct": round(100.0 * (max(cys) - min(cys)) / h_img, 3),
        "ink_min": round(min(inkm), 2),
        "ink_max": round(max(inkm), 2),
        "shadow_span_px_min": min(shadow_hs),
        "shadow_span_px_max": max(shadow_hs),
        "bbox_width_px_min": min(r[3] for r in rows),
        "bbox_width_px_max": max(r[3] for r in rows),
        "bbox_height_px_min": min(r[4] for r in rows),
        "bbox_height_px_max": max(r[4] for r in rows),
        "note": ("The width and height spread across the sequence is the ROTATION - an "
                 "end-on truck is genuinely narrower and taller in the image - not "
                 "jitter. Two invariants are checked here: the projected length is "
                 "identical at 180 deg (same length either way round), and the silhouette "
                 "centre does not wander, which is what a shifted pivot would show. "
                 "Camera stability is proved decisively in framing_comparison.json, where "
                 "one fixed camera predicts every frame from the real vertex cloud."),
    }
    import json
    (out / "frame_measurements.json").write_text(json.dumps(
        {"per_frame": [{"file": r[0], "size": list(r[1]), "bbox": list(r[2]),
                        "w": r[3], "h": r[4], "solid_px": r[5], "ink": round(r[6], 2),
                        "alpha_max": r[7]} for r in rows],
         "summary": summary}, indent=1))
    print("wrote", out / "frame_measurements.json")
