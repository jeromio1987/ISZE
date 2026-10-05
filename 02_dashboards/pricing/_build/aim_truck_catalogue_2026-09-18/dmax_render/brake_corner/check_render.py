"""Numeric checks on the final photographs.

I cannot see images in this environment, so this stands in for looking at them and
is written to catch the failures that eyeballing would: a blank or single-colour
frame, a subject that is clipped by the frame edge, a subject that is too small,
a transparent pass that is not actually transparent, and a lack of any tonal
variation (which would mean the lighting or the materials did not take).

  python check_render.py --shadow <png> --alpha <png> --out <json>
"""
from __future__ import annotations

import argparse
import json

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--shadow", required=True)
ap.add_argument("--alpha", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--edge", type=int, default=3, help="edge band width in px")
a = ap.parse_args()

doc = {}
for tag, path in (("shadow", a.shadow), ("alpha", a.alpha)):
    im = Image.open(path)
    arr = np.asarray(im)
    H, W = arr.shape[:2]
    rgb = arr[:, :, :3].astype(np.float64)
    al = arr[:, :, 3] if arr.shape[2] == 4 else np.full((H, W), 255)
    solid = al > 250
    cov = float(solid.mean())
    lum = rgb.mean(axis=2)
    lum_solid = lum[solid] if solid.any() else lum.ravel()
    # clipping: does the subject touch the frame edge?
    band = np.zeros((H, W), dtype=bool)
    band[: a.edge, :] = band[-a.edge:, :] = True
    band[:, : a.edge] = band[:, -a.edge:] = True
    clipped = int((solid & band).sum())
    # tonal variation across the subject: standard deviation of luminance
    doc[tag] = {
        "path": path,
        "size": [W, H],
        "alpha_min": int(al.min()),
        "alpha_max": int(al.max()),
        "solid_fraction": round(cov, 4),
        "transparent_fraction": round(float((al < 5).mean()), 4),
        "subject_touches_frame_edge_px": clipped,
        "lut_stddev_solid": round(float(lum_solid.std()), 2),
        "lut_mean_solid": round(float(lum_solid.mean()), 2),
        "distinct_colours_in_subject": int(len(np.unique(
            arr[:, :, :3][solid].reshape(-1, 3), axis=0))) if solid.any() else 0,
        "pct_solid_near_black": round(float((lum_solid < 3).mean() * 100), 2),
        "pct_solid_near_white": round(float((lum_solid > 252).mean() * 100), 2),
    }
    d = doc[tag]
    verdict = []
    if d["distinct_colours_in_subject"] < 2000:
        verdict.append("FAIL: subject has almost no colour variation (blank or flat-fill?)")
    if d["lut_stddev_solid"] < 3.0:
        verdict.append("FAIL: subject is flat (lighting or materials did not take)")
    if d["subject_touches_frame_edge_px"] > 0:
        verdict.append("FAIL: subject is clipped by the frame edge")
    if d["solid_fraction"] < 0.05:
        verdict.append("FAIL: subject covers less than 5% of the frame")
    if tag == "alpha" and d["transparent_fraction"] < 0.3:
        verdict.append("FAIL: the transparent pass is not mostly transparent")
    if tag == "shadow" and d["solid_fraction"] > 0.98:
        verdict.append("NOTE: the shadow pass is almost fully opaque")
    d["verdict"] = verdict or ["PASS"]
    print("%-7s %s" % (tag, path))
    print("   %dx%d  solid %.1f%%  transparent %.1f%%  edge-clipped %d px"
          % (W, H, 100 * d["solid_fraction"], 100 * d["transparent_fraction"], clipped))
    print("   subject luminance mean %.1f  stddev %.1f  distinct colours %d"
          % (d["lut_mean_solid"], d["lut_stddev_solid"], d["distinct_colours_in_subject"]))
    print("   near-black %.2f%%  near-white %.2f%%" % (d["pct_solid_near_black"],
                                                       d["pct_solid_near_white"]))
    print("   -> %s" % "; ".join(d["verdict"]))

doc["overall"] = ("PASS" if all(v.get("verdict") == ["PASS"]
                                 for v in (doc.get("shadow"), doc.get("alpha")))
                  else "REVIEW")
with open(a.out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1)
print("verdicts:", {k: doc[k]["verdict"] for k in ("shadow", "alpha")})
print("wrote", a.out)
print("overall:", doc["overall"])
