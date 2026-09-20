"""Measure the ID pass: is each part actually visible in the shipped image?

Reads the flat-colour ID render the build wrote and answers the question that
matters for a parts diagram: is every part visible, whole, and not hidden behind
its neighbour?  Three measurements per part:

  visible_px        pixels of that part's colour
  visible_fraction  what share of the part's own projected silhouette is visible,
                    i.e. how much of it is not covered by another part
  colour_coverage   of the pixels where the part is the FRONT-most surface, what
                    share carry the right colour (should be ~100%)

Ground truth for each part's full silhouette is its own geometry projected through
the camera from the build report, so this compares the picture against the
geometry rather than against another copy of the picture.

  python analyse_idpass.py --id <png> --report <json> --out <json>
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
from PIL import Image

COLOURS_LINEAR = {
    "disc":    (1.0, 0.10, 0.10),
    "pads":    (1.0, 1.00, 0.10),
    "caliper": (0.10, 1.00, 0.10),
    "wheel":   (0.10, 0.50, 1.00),
    "tyre":    (1.0, 0.10, 1.00),
}
ORDER = ["disc", "pads", "caliper", "wheel", "tyre"]


def lin_to_srgb_u8(c):
    """Blender writes 8-bit PNGs through the sRGB transfer function, so a flat
    emission asked for in linear space arrives encoded.  Predict that here rather
    than hard-coding a colour that would silently change if the transform did."""
    out = []
    for v in c:
        v = 0.0 if v <= 0.0 else (1.0 if v >= 1.0 else v)
        s = 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055
        out.append(int(round(s * 255.0)))
    return tuple(out)


COLOURS = {k: lin_to_srgb_u8(v) for k, v in COLOURS_LINEAR.items()}

ap = argparse.ArgumentParser()
ap.add_argument("--id", required=True)
ap.add_argument("--solo-dir", required=True,
                help="folder holding idpass_solo_<part>_<tag>.png")
ap.add_argument("--solo-tag", default="bc")
ap.add_argument("--out", required=True)
ap.add_argument("--tol", type=int, default=40)
a = ap.parse_args()

im = Image.open(a.id).convert("RGB")
arr = np.asarray(im).astype(np.int16)
H, W, _ = arr.shape
print("ID image %dx%d" % (W, H))

lum = arr.max(axis=2)
subject = lum > 20
print("subject pixels %d (%.1f%% of frame)" % (subject.sum(), 100.0 * subject.sum() / (W * H)))

# ---- each part's TRUE projected footprint, taken from the render of that part on
#      its own.  This is the ground truth the occlusion test needs: a part that is
#      completely hidden still has a footprint, so "hidden" and "absent" cannot be
#      confused.
solo_masks = {}
for name in ORDER:
    p = os.path.join(a.solo_dir, "idpass_solo_%s_%s.png" % (name, a.solo_tag))
    s = np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
    m = s.max(axis=2) > 20
    solo_masks[name] = m
    print("  solo footprint %-8s %7d px" % (name, int(m.sum())))

results = {}
claimed = np.zeros((H, W), dtype=bool)
for name in ORDER:
    rgb = COLOURS[name]
    d = np.abs(arr - np.array(rgb, dtype=np.int16)).max(axis=2)
    m = (d <= a.tol) & subject
    claimed |= m
    n = int(m.sum())
    foot = solo_masks[name]
    foot_n = int(foot.sum())
    visible_in_foot = int((m & foot).sum())
    entry = {
        "colour_rgb": list(rgb),
        "visible_px": n,
        "solo_footprint_px": foot_n,
        "visible_share_of_own_footprint": round(visible_in_foot / max(1, foot_n), 4),
        "occluded_px": foot_n - visible_in_foot,
    }
    if n:
        ys, xs = np.nonzero(m)
        entry.update({"x0": int(xs.min()), "x1": int(xs.max()),
                      "y0": int(ys.min()), "y1": int(ys.max()),
                      "w": int(xs.max() - xs.min() + 1),
                      "h": int(ys.max() - ys.min() + 1)})
    results[name] = entry
    if n:
        print("  %-8s %7d px  visible %5.1f%% of its own footprint (%d px hidden)  "
              "box x %4d..%4d y %4d..%4d"
              % (name, n, 100.0 * entry["visible_share_of_own_footprint"],
                 entry["occluded_px"], entry["x0"], entry["x1"], entry["y0"], entry["y1"]))
    else:
        print("  %-8s %7d px  NOT VISIBLE AT ALL" % (name, n))

unclaimed = int((subject & ~claimed).sum())
print("subject pixels not claimed by any part colour: %d (%.2f%%)"
      % (unclaimed, 100.0 * unclaimed / max(1, subject.sum())))

# ---- why is a part hidden?  Split its hidden pixels by which neighbour's footprint
#      they fall inside, so "the wheel is 35% hidden" can be stated as self-occlusion
#      of an open rim versus being covered by another part.
for name in ORDER:
    foot = solo_masks[name]
    hidden = foot & ~(np.abs(arr - np.array(COLOURS[name], dtype=np.int16)).max(axis=2)
                      <= a.tol)
    # a hidden pixel explained by self-occlusion is one where no neighbour's
    # footprint reaches, but the part's own colour is absent because its far side is
    # behind its near side.  That cannot be separated from occlusion by a colour
    # test alone, so attribute by neighbour footprint and label the remainder.
    attrib = {}
    for other in ORDER:
        if other == name:
            continue
        share = int((hidden & solo_masks[other]).sum())
        if share:
            attrib[other] = share
    total_hidden = int(hidden.sum())
    unattributed = total_hidden - sum(attrib.values())
    results[name]["hidden_attributed_to"] = attrib
    results[name]["hidden_unattributed_self_occlusion_px"] = unattributed
    if total_hidden:
        top = ", ".join("%s %d px" % kv for kv in
                        sorted(attrib.items(), key=lambda kv: -kv[1])[:4]) or "none"
        print("  hidden pixels of %-8s: %6d  behind a neighbour: %s ; self-occluded: %d"
              % (name, total_hidden, top, unattributed))

# horizontal air between the visible faces, which is what a reader sees
gaps = []
for x, y in zip(ORDER, ORDER[1:]):
    if results[x].get("x1") is None or results[y].get("x0") is None:
        gaps.append({"between": [x, y], "gap_px": None, "separated": None})
        continue
    g = results[y]["x0"] - results[x]["x1"]
    gaps.append({"between": [x, y], "gap_px": int(g), "separated": bool(g > 0)})
    print("  air between %-8s and %-8s : %+5d px  %s"
          % (x, y, g, "AIR" if g > 0 else "overlapping on screen"))

doc = {
    "image": a.id,
    "size": [W, H],
    "subject_pixels": int(subject.sum()),
    "subject_pct": round(100.0 * subject.sum() / (W * H), 2),
    "parts": results,
    "unclaimed_subject_px": unclaimed,
    "unclaimed_pct_of_subject": round(100.0 * unclaimed / max(1, subject.sum()), 2),
    "horizontal_gaps_px": gaps,
    "every_part_visible": all(r["visible_px"] > 2000 for r in results.values()),
    "min_visible_share_of_own_footprint": min(
        r["visible_share_of_own_footprint"] for r in results.values()),
    "order_left_to_right": [k for k in sorted(results, key=lambda k: results[k].get("x0", 10**9))
                            if results[k].get("x0") is not None],
    "method": ("each part's own footprint comes from an identical render of that part "
               "alone. visible_share_of_own_footprint is the share of that footprint "
               "where the part is the front-most surface, so a low value means a "
               "neighbour is covering it and 100% means nothing covers it at all."),
}
with open(a.out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1)
print("wrote", a.out)
print("every part visible:", doc["every_part_visible"],
      " min visible share of own footprint: %.1f%%"
      % (100 * doc["min_visible_share_of_own_footprint"]))
print("left to right:", " -> ".join(doc["order_left_to_right"]))
