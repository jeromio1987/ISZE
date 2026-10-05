"""Check the callout geometry against the drawing, before looking at anything.

I cannot see images in this environment, so this stands in for looking at the page
and tests the things that would be visible: do two labels overlap, does a label sit
on top of the part it points at, do the leaders cross, and are the labels inside the
frame.  Ground truth for each part's picture extent is the solo ID render from the
build, so the test is against the geometry, not against another copy of the page.

  python check_callouts.py
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "_raw")

CALLOUTS = [
    {"id": "A", "caption": "Brake disc", "part": "disc",
     "box": (296, 64, 664, 214), "anchor": (536, 906)},
    {"id": "B", "caption": "Brake pads", "part": "pads",
     "box": (404, 1786, 816, 1942), "anchor": (826, 1040)},
    {"id": "C", "caption": "Brake caliper", "part": "caliper",
     "box": (824, 64, 1216, 214), "anchor": (1056, 690)},
    {"id": "D", "caption": "Road wheel", "part": "wheel",
     "box": (1116, 1786, 1496, 1942), "anchor": (1481, 1300)},
    {"id": "E", "caption": "Tyre", "part": "tyre",
     "box": (1972, 1786, 2392, 1942), "anchor": (2280, 1720)},
]

fails, notes = [], []
doc = {"callouts": CALLOUTS, "checks": {}}


def rect(b):
    x0, y0, x1, y1 = b
    return x0, y0, x1, y1


def overlap(a, b, pad=0):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return not (ax1 + pad <= bx0 or bx1 + pad <= ax0 or ay1 + pad <= by0 or by1 + pad <= ay0)


# ---- 1. label against label
pair = []
for i, c in enumerate(CALLOUTS):
    for d in CALLOUTS[i + 1:]:
        ov = overlap(rect(c["box"]), rect(d["box"]))
        pair.append({"a": c["id"], "b": d["id"], "overlap": ov})
        if ov:
            fails.append("labels %s and %s overlap" % (c["id"], d["id"]))
doc["checks"]["label_vs_label"] = pair
print("label against label:")
for p in pair:
    print("   %s-%s  %s" % (p["a"], p["b"], "OVERLAP" if p["overlap"] else "clear"))

# ---- 2. leaders against each other (segment intersection)
def seg_cross(p1, p2, p3, p4):
    def o(a, b, c):
        v = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else 2)

    def on(a, b, c):
        return (min(a[0], c[0]) <= b[0] <= max(a[0], c[0])
                and min(a[1], c[1]) <= b[1] <= max(a[1], c[1]))

    o1, o2, o3, o4 = o(p1, p2, p3), o(p1, p2, p4), o(p3, p4, p1), o(p3, p4, p2)
    if o1 != o2 and o3 != o4:
        return True
    return ((o1 == 0 and on(p1, p3, p2)) or (o2 == 0 and on(p1, p4, p2))
            or (o3 == 0 and on(p3, p1, p4)) or (o4 == 0 and on(p3, p2, p4)))


# the leader starts on the label edge nearest the anchor, exactly as the page draws it
def leader(c):
    x0, y0, x1, y1 = c["box"]
    ax, ay = c["anchor"]
    if ay > y1:
        sx, sy = (x0 + x1) / 2, y1
    elif ay < y0:
        sx, sy = (x0 + x1) / 2, y0
    else:
        sx, sy = (x1 if ax > x1 else x0), (y0 + y1) / 2
    return (sx, sy), (ax, ay)


cross = []
for i, c in enumerate(CALLOUTS):
    for d in CALLOUTS[i + 1:]:
        p1, p2 = leader(c)
        p3, p4 = leader(d)
        x = seg_cross(p1, p2, p3, p4)
        cross.append({"a": c["id"], "b": d["id"], "cross": x})
        if x:
            fails.append("leaders %s and %s cross" % (c["id"], d["id"]))
doc["checks"]["leader_vs_leader"] = cross
print("leader against leader:")
for p in cross:
    print("   %s-%s  %s" % (p["a"], p["b"], "CROSS" if p["cross"] else "clear"))

# ---- 3. leader must not pass through a label that is not its own
hit_label = []
for c in CALLOUTS:
    p1, p2 = leader(c)
    for d in CALLOUTS:
        if d["id"] == c["id"]:
            continue
        x0, y0, x1, y1 = d["box"]
        edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
        if any(seg_cross(p1, p2, e[0], e[1]) for e in edges):
            hit_label.append({"leader": c["id"], "through_label": d["id"]})
            fails.append("leader %s crosses label %s" % (c["id"], d["id"]))
doc["checks"]["leader_through_other_label"] = hit_label
print("leader through another label: %s"
      % (hit_label if hit_label else "none"))

# ---- 4. anchor must be on the part it names, and not on another part
missing = [p for p in CALLOUTS
           if not os.path.exists(os.path.join(RAW, "idpass_solo_%s_bc.png" % p["part"]))]
if missing:
    notes.append("solo ID renders missing for %s" % [m["part"] for m in missing])

if not missing:
    H = W = None
    for c in CALLOUTS:
        p = os.path.join(RAW, "idpass_solo_%s_bc.png" % c["part"])
        a = np.asarray(Image.open(p).convert("RGB"))
        H, W = a.shape[:2]
        m = a.max(axis=2) > 20
        ax, ay = c["anchor"]
        patch = m[max(0, ay - 6):ay + 7, max(0, ax - 6):ax + 7]
        on_self = bool(patch.any())
        others = []
        for d in CALLOUTS:
            if d["id"] == c["id"]:
                continue
            od = np.asarray(Image.open(
                os.path.join(RAW, "idpass_solo_%s_bc.png" % d["part"])).convert("RGB"))
            om = od.max(axis=2) > 20
            if om[max(0, ay - 6):ay + 7, max(0, ax - 6):ax + 7].any():
                others.append(d["id"])
        c["anchor_on_own_part"] = on_self
        c["anchor_also_on"] = others
        print("anchor %s at %s: on %s = %s ; also on %s"
              % (c["id"], (ax, ay), c["caption"], on_self, others or "nothing"))
        if not on_self:
            fails.append("anchor %s is not on its own part" % c["id"])
        if others:
            fails.append("anchor %s also lands on %s" % (c["id"], others))
    doc["checks"]["anchors_verified"] = True

# ---- 5. labels inside the frame, with a margin
fw, fh = W or 2800, H or 2000
inside = []
for c in CALLOUTS:
    x0, y0, x1, y1 = c["box"]
    ok = x0 > 12 and y0 > 12 and x1 < fw - 12 and y1 < fh - 12
    inside.append({"id": c["id"], "inside": ok})
    if not ok:
        fails.append("label %s is clipped by the frame edge" % c["id"])
doc["checks"]["labels_inside_frame"] = inside
print("labels inside the frame with a margin: %s"
      % all(i["inside"] for i in inside))

# ---- 6. how much of each label sits on top of the subject, i.e. would a reader lose
#         part of the drawing.  Some overlap is deliberate (a label in the empty
#         corner); the test is that no label sits on the part it points at.
occ = []
for c in CALLOUTS:
    p = os.path.join(RAW, "idpass_solo_%s_bc.png" % c["part"])
    if not os.path.exists(p):
        continue
    a = np.asarray(Image.open(p).convert("RGB"))
    m = a.max(axis=2) > 20
    x0, y0, x1, y1 = c["box"]
    cover = float(m[y0:y1, x0:x1].mean()) if m[y0:y1, x0:x1].size else 0.0
    occ.append({"id": c["id"], "own_part_under_label_pct": round(100 * cover, 2)})
    if cover > 0.02:
        fails.append("label %s covers %.1f%% of the part it points at"
                     % (c["id"], 100 * cover))
doc["checks"]["label_over_own_part"] = occ
print("label sitting on the part it points at:")
for o in occ:
    print("   %s  %.2f%%" % (o["id"], o["own_part_under_label_pct"]))

doc["failures"] = fails
doc["notes"] = notes
doc["verdict"] = "PASS" if not fails else "FAIL"
with open(os.path.join(RAW, "callout_check.json"), "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1)
print()
print("wrote", os.path.join(RAW, "callout_check.json"))
for n in notes:
    print("note:", n)
if fails:
    print("FAILURES:")
    for f in fails:
        print("  -", f)
else:
    print("no failures")
print("VERDICT:", doc["verdict"])
