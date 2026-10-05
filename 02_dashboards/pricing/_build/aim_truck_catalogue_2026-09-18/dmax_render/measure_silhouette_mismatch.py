"""Measure the render's silhouette at the HERO camera angle against a real D-Max.

Reference: `01_data/90_INBOX/_truck_ref/cut/dmax_a.png` - a 1320 x 951 isolated
D-Max double cab on a flat field, which segments exactly.  This is the reference
that makes the measurement meaningful; the press photograph named in the brief
could not be segmented reliably (see the note in the output document).

This script measures the angle the hero was ACTUALLY shot from, read out of
_raw/cam_hero.json, rather than re-fitting an angle and reporting that instead.  A
sweep is still run if asked, but the headline number is the hero's own angle.

Run: python measure_silhouette_mismatch.py [--sweep]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
REF_CUT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_truck_ref\cut\dmax_a.png"
HERO_REPORT = os.path.join(HERE, "_raw", "cam_hero.json")
RES = (1400, 600)
SAMPLES = 22


def largest_component(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    best_id, best_n, cur = 0, 0, 0
    ys, xs = np.where(mask)
    for sy, sx in zip(ys, xs):
        if lab[sy, sx]:
            continue
        cur += 1
        stack = [(sy, sx)]
        lab[sy, sx] = cur
        n = 0
        while stack:
            y, x = stack.pop()
            n += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = cur
                        stack.append((ny, nx))
        if n > best_n:
            best_n, best_id = n, cur
    return lab == best_id


def fill_holes(mask):
    h, w = mask.shape
    outside = np.zeros((h, w), bool)
    stack = []
    for x in range(w):
        for y in (0, h - 1):
            if not mask[y, x] and not outside[y, x]:
                outside[y, x] = True
                stack.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if not mask[y, x] and not outside[y, x]:
                outside[y, x] = True
                stack.append((y, x))
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not mask[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                stack.append((ny, nx))
    return mask | ~outside


def ref_mask():
    a = np.asarray(Image.open(REF_CUT).convert("RGB")).astype(np.float32)
    lum = a.mean(2)
    bg = float(np.median(np.concatenate([lum[:8].ravel(), lum[-8:].ravel(),
                                         lum[:, :8].ravel(), lum[:, -8:].ravel()])))
    m = np.abs(lum - bg) > 18
    m = fill_holes(largest_component(m))
    ys, xs = np.where(m)
    print("reference: background level %.0f, vehicle %d px, bbox %dx%d"
          % (bg, int(m.sum()), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1], bg


def render_mask(path):
    im = Image.open(path)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    a = np.asarray(im)[..., 3] > 128
    ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def norm(b, W=420, H=180):
    """Stretch to a common box so the comparison tests SHAPE only.

    Normalising by height alone still leaves the apparent length free, and a
    three-quarter view's apparent length depends on the azimuth, so the fit gets
    contaminated: the optimiser could make the render look 'narrower' by rotating
    toward the front instead of by matching the shape.
    """
    im = Image.fromarray((b * 255).astype(np.uint8))
    return np.asarray(im.resize((W, H), Image.LANCZOS)) > 127


def score(r, n):
    """Compare two silhouettes, each normalised into the same box."""
    def body(m):
        rows = m.sum(1)
        peak = int(np.argmax(rows))
        keep = np.where(rows > 0.25 * rows[peak])[0]
        return m[keep.min():keep.max() + 1]

    r = norm(body(r))
    n = norm(body(n))
    n_flip = n[:, ::-1].copy()

    def pair(a, b):
        inter = int((a & b).sum())
        union = int((a | b).sum())
        iou = inter / union if union else 0.0
        only_a = int((a & ~b).sum())
        only_b = int((~a & b).sum())

        def edges(m, which):
            v = np.full(m.shape[1], np.nan)
            for x in range(m.shape[1]):
                c = np.where(m[:, x])[0]
                if len(c):
                    v[x] = c.min() if which == "top" else c.max()
            return v

        out = {"iou": round(iou, 4),
               "sym_diff_pct": round(100.0 * (only_a + only_b) / max(1, a.sum()), 2),
               "ref_only_pct": round(100.0 * only_a / max(1, a.sum()), 2),
               "render_only_pct": round(100.0 * only_b / max(1, a.sum()), 2)}
        H = a.shape[0]
        for which in ("top", "bottom"):
            ea, eb = edges(a, which), edges(b, which)
            ok = ~np.isnan(ea) & ~np.isnan(eb)
            e = np.abs(ea[ok] - eb[ok]) if ok.any() else np.array([H])
            out["%s_edge_mean_pct_h" % which] = round(100.0 * float(e.mean()) / H, 2)
            out["%s_edge_p95_pct_h" % which] = round(
                100.0 * float(np.percentile(e, 95)) / H, 2)
        return out, a, b

    m0, a0, b0 = pair(r, n)
    m1, a1, b1 = pair(r, n_flip)
    if m1["iou"] > m0["iou"]:
        m1["orientation"] = "mirrored"
        return m1, a1, b1
    m0["orientation"] = "as rendered"
    return m0, a0, b0


def render_at(az, el, tag):
    png = os.path.join(HERE, "_raw", "rgba_%s.png" % tag)
    if not os.path.exists(png):
        cmd = [BLENDER, "--background", "--python",
               os.path.join(HERE, "build_dmax_render.py"), "--",
               "--outdir", HERE, "--tag", tag, "--samples", str(SAMPLES),
               "--resx", str(RES[0]), "--resy", str(RES[1]),
               "--az", str(az), "--el", str(el), "--paint", "white",
               "--details", "0"]
        log = open(os.path.join(HERE, "_raw", "%s.log" % tag), "w")
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
        log.close()
    return png if os.path.exists(png) else None


def main() -> int:
    do_sweep = "--sweep" in sys.argv
    with open(HERO_REPORT) as f:
        hero = json.load(f)
    az, el = float(hero["az_deg"]), float(hero["el_deg"])
    print("hero camera: azimuth %.1f, elevation %.1f  (from %s)"
          % (az, el, os.path.basename(HERO_REPORT)))

    ref, bg = ref_mask()

    all_results = []
    if do_sweep:
        for a in (56, 64, 72, 80, 88):
            for e in (10, 14, 18, 22):
                png = render_at(a, e, "sil3_az%d_el%d" % (a, e))
                if not png:
                    continue
                m, _, _ = score(ref, render_mask(png))
                m["az"], m["el"] = a, e
                all_results.append(m)
                print("  az %2d el %2d  IoU %.3f  sym-diff %5.1f%%  top %.1f%%H  bottom %.1f%%H"
                      % (a, e, m["iou"], m["sym_diff_pct"],
                         m["top_edge_mean_pct_h"], m["bottom_edge_mean_pct_h"]))

    tag = "hero_meas_az%d_el%d" % (int(round(az)), int(round(el)))
    png = render_at(az, el, tag)
    if not png:
        print("could not render at the hero angle")
        return 1
    m, r, n = score(ref, render_mask(png))
    m["az"], m["el"] = az, el

    print("\nHERO ANGLE: azimuth %.0f, elevation %.0f" % (az, el))
    print("  intersection over union       %.3f" % m["iou"])
    print("  symmetric difference          %.1f%% of the reference area" % m["sym_diff_pct"])
    print("  reference only / render only  %.1f%% / %.1f%%"
          % (m["ref_only_pct"], m["render_only_pct"]))
    print("  top edge error                %.1f%% of height (p95 %.1f%%)"
          % (m["top_edge_mean_pct_h"], m["top_edge_p95_pct_h"]))
    print("  bottom edge error             %.1f%% of height (p95 %.1f%%)"
          % (m["bottom_edge_mean_pct_h"], m["bottom_edge_p95_pct_h"]))
    print("  orientation                   %s" % m.get("orientation"))

    H, W = r.shape
    vis = np.zeros((H, W, 3), np.uint8)
    vis[r & n] = [236, 236, 236]
    vis[r & ~n] = [40, 110, 235]
    vis[~r & n] = [225, 60, 40]
    ov = Image.fromarray(vis)
    ImageDraw.Draw(ov).text((8, 6), "grey = agreement   blue = real D-Max only   "
                                   "red = this render only", fill=(20, 20, 20))
    ov.save(os.path.join(HERE, "_qa_silhouette_diff.png"))
    print("\nwrote _qa_silhouette_diff.png")

    # the previous build's headline, for the before/after line
    prev = None
    prev_path = os.path.join(HERE, "_raw", "silhouette_previous.json")
    if os.path.exists(prev_path):
        with open(prev_path) as f:
            prev = json.load(f)

    doc = {
        "reference": {
            "file": REF_CUT,
            "what": "isolated 2021 D-Max double cab on a flat light field, 1320x951",
            "background_level": round(bg, 1),
            "segmentation": "flat-background threshold + hole fill + largest blob; exact",
        },
        "why_this_reference": (
            "The photograph named in the original brief (dmax_spec_p8_0.jpeg) is a 483x297 px "
            "crop of a booklet page in which the vehicle merges with a dark setting and is "
            "clipped at the edge, so it cannot be segmented to a number. This cutout is the "
            "same model year and body style on a flat background and segments exactly."),
        "method": (
            "Both silhouettes are trimmed to the widest-row span to drop the contact shadow, "
            "stretched into the same box (which removes scale and aspect, so only the OUTLINE "
            "is compared), and scored for intersection over union plus the mean and p95 error "
            "of the top and bottom edges as a percentage of vehicle height. Both orientations "
            "are tried, because the reference is viewed from the opposite flank to the render."),
        "hero_angle": {
            "azimuth_deg": az, "elevation_deg": el,
            "orientation": m.get("orientation"),
            "intersection_over_union": m["iou"],
            "symmetric_difference_pct_of_reference": m["sym_diff_pct"],
            "reference_only_pct": m["ref_only_pct"],
            "render_only_pct": m["render_only_pct"],
            "top_edge_error_pct_of_height": {
                "mean": m["top_edge_mean_pct_h"], "p95": m["top_edge_p95_pct_h"]},
            "bottom_edge_error_pct_of_height": {
                "mean": m["bottom_edge_mean_pct_h"], "p95": m["bottom_edge_p95_pct_h"]},
        },
        "previous_build": prev,
        "sweep": all_results,
        "caveat": (
            "This number measures SHAPE, not size: stretching both silhouettes into one box "
            "removes scale and aspect. A rear three-quarter view cannot score highly against "
            "a front three-quarter reference, and that is a limit of the reference, not "
            "evidence about the model."),
    }
    with open(os.path.join(HERE, "_qa_silhouette_metrics.json"), "w") as f:
        json.dump(doc, f, indent=1)
    print("wrote _qa_silhouette_metrics.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
