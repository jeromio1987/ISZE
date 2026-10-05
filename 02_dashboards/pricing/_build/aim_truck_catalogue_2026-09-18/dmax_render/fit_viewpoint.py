"""Fit the camera angle by sweep, and score it against a real D-Max silhouette.

Reference: `01_data/90_INBOX/_truck_ref/cut/dmax_a.png` - an isolated 2021 D-Max
double cab on a flat light field, which segments exactly.  The press photo named
in the original brief is a 483x297 crop of a booklet page where the vehicle
merges with a dark setting and is clipped at the edge, so it cannot be segmented
to a number and is not used here.

Method
------
* segment the reference (flat background), fill holes, keep the largest blob
* sweep azimuth / elevation, render each at proxy resolution, segment from alpha
* stretch both silhouettes into one box - which removes scale and aspect, so the
  score measures OUTLINE, not size - and compute intersection over union,
  symmetric difference, and the mean and p95 error of the top and bottom edges as
  a percentage of vehicle height
* both orientations are tried, because the reference is viewed from the opposite
  flank to the render

The sweep covers front-three-quarter and rear-three-quarter azimuths, and goes up
to 22 degrees of elevation so the load box is visible over the bed rail.  A rear
three-quarter view cannot score well against a front three-quarter reference, and
that is reported rather than hidden.

Run: python fit_viewpoint.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
REF_CUT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_truck_ref\cut\dmax_a.png"
RAWDIR = os.path.join(HERE, "_sweep")
os.makedirs(RAWDIR, exist_ok=True)

# front three-quarter, plus two rear three-quarter azimuths for evidence
AZIMUTHS = [56, 64, 72, 80, 88, 250, 265]
ELEVATIONS = [10, 14, 18, 22]
RES = (1100, 475)
SAMPLES = 20
PAINT = "white"


def largest_component(mask: np.ndarray) -> np.ndarray:
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
    if not os.path.exists(REF_CUT):
        raise SystemExit("reference cutout not found: %s" % REF_CUT)
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


def main() -> int:
    ref, bg = ref_mask()
    print("reference: background level %.0f, vehicle %d px, bbox %dx%d"
          % (bg, int(ref.sum()), ref.shape[1], ref.shape[0]))

    results = []
    best = None
    for az in AZIMUTHS:
        for el in ELEVATIONS:
            tag = "sweep2_az%d_el%d" % (az, el)
            png = os.path.join(HERE, "_raw", "rgba_%s.png" % tag)
            if not os.path.exists(png):
                cmd = [BLENDER, "--background", "--python",
                       os.path.join(HERE, "build_dmax_render.py"), "--",
                       "--outdir", HERE, "--tag", tag, "--samples", str(SAMPLES),
                       "--resx", str(RES[0]), "--resy", str(RES[1]),
                       "--az", str(az), "--el", str(el), "--paint", PAINT,
                       "--details", "0"]
                log = open(os.path.join(RAWDIR, "%s.log" % tag), "w")
                subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
                log.close()
            if not os.path.exists(png):
                print("  az %3d el %2d  RENDER FAILED" % (az, el))
                continue
            ren = render_mask(png)
            m, r, n = score(ref, ren)
            m["az"], m["el"] = az, el
            m["view"] = "rear three-quarter" if az > 180 else "front three-quarter"
            results.append(m)
            print("  az %3d el %2d  %-19s IoU %.3f  sym-diff %5.1f%%  top %.1f%%H  bottom %.1f%%H"
                  % (az, el, m["view"], m["iou"], m["sym_diff_pct"],
                     m["top_edge_mean_pct_h"], m["bottom_edge_mean_pct_h"]))
            if best is None or m["iou"] > best[0]["iou"]:
                best = (m, r, n)

    if best is None:
        print("no comparison could be made")
        return 1
    m, r, n = best
    print("\nBEST MATCH: azimuth %d deg, elevation %d deg (%s)"
          % (m["az"], m["el"], m["view"]))
    print("  intersection over union       %.3f" % m["iou"])
    print("  symmetric difference          %.1f%% of the reference area" % m["sym_diff_pct"])
    print("  top edge error                %.1f%% of height (p95 %.1f%%)"
          % (m["top_edge_mean_pct_h"], m["top_edge_p95_pct_h"]))
    print("  bottom edge error             %.1f%% of height (p95 %.1f%%)"
          % (m["bottom_edge_mean_pct_h"], m["bottom_edge_p95_pct_h"]))

    H, W = r.shape
    vis = np.zeros((H, W, 3), np.uint8)
    vis[r & n] = [236, 236, 236]
    vis[r & ~n] = [40, 110, 235]
    vis[~r & n] = [225, 60, 40]
    Image.fromarray(vis).save(os.path.join(HERE, "_qa_silhouette_diff.png"))

    results.sort(key=lambda x: -x["iou"])
    with open(os.path.join(RAWDIR, "sweep_results.json"), "w") as f:
        json.dump(results, f, indent=1)
    print("\nwrote _sweep/sweep_results.json (%d angles)" % len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
