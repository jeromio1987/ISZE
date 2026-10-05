"""Probe 3: what are BrakeRotors vs BrakeRotors1, at the front-right corner?

Both appear at both axles, so neither is "the front one".  A brake corner stacks
plates along the axle (the x axis).  So for one corner, bucket the vertices by
lateral position x and by radius about the axle centre.  A vented disc shows as a
narrow lateral spike; a hub or dust shield shows as a wider lateral band at a
different x.  Also fits the true wheel centre from the tyre so the radius is not
distorted by a guessed centre.

Run:
  blender --background --python probe_brake3.py -- --outdir _raw
"""
from __future__ import annotations

import json
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


HERE = os.path.dirname(os.path.abspath(__file__))
RENDER_DIR = os.path.dirname(HERE)
OUTDIR = arg("--outdir", HERE)
if not os.path.isabs(OUTDIR):
    OUTDIR = os.path.join(HERE, OUTDIR)
os.makedirs(OUTDIR, exist_ok=True)
GLB = arg("--glb", os.path.join(RENDER_DIR, "_assets", "dmax_2021_objaverse.glb"))

sys.path.insert(0, RENDER_DIR)
import dmax_prep as prep                                          # noqa: E402

drawable = prep.import_model(GLB)
INFO, DMN, DMX = prep.scale_to_metres(drawable)
FA, RA = INFO["front_axle_y"], INFO["rear_axle_y"]

# ---- fit the true wheel centre (y, z) from the front-right tyre ring, by least
#      squares on the tyre's own cross-section, so radius is not measured from a
#      guessed centre.
for o in drawable:
    if not any('_Tires' in m for m in prep.mats(o)):
        continue
    mw = o.matrix_world
    pts = [mw @ v.co for v in o.data.vertices]
    ring = [p for p in pts if p.y < FA + 0.55 and p.x > 0.2]
    if len(ring) < 100:
        continue
    # annulus centres: solve for (cy, cz) minimising variance of hypot
    cy = sum(p.y for p in ring) / len(ring)
    cz = sum(p.z for p in ring) / len(ring)
    for _ in range(60):
        rs = [math.hypot(p.y - cy, p.z - cz) for p in ring]
        rbar = sum(rs) / len(rs)
        # gradient step on the residual
        gy = sum(-(r - rbar) * (p.y - cy) / max(r, 1e-9) for r, p in zip(rs, ring))
        gz = sum(-(r - rbar) * (p.z - cz) / max(r, 1e-9) for r, p in zip(rs, ring))
        n = len(ring)
        cy -= 0.35 * gy / n
        cz -= 0.35 * gz / n
    rs = sorted(math.hypot(p.y - cy, p.z - cz) for p in ring)
    print("tyre ring fit: centre y=%.4f z=%.4f   r %.1f .. %.1f mm"
          % (cy, cz, rs[0] * 1000, rs[-1] * 1000))
    WHEEL = {"cy": cy, "cz": cz, "r_min": rs[0], "r_max": rs[-1],
             "r_p05": rs[len(rs) // 20], "r_p95": rs[-len(rs) // 20]}
    break

out = {"front_axle_y": FA, "rear_axle_y": RA, "wheel_centre": WHEEL, "corner": {}}

WANT = ("BrakeRotors1", "BrakeRotors", "Calipers", "BrakePads", "Rims1", "Rims2")
for o in drawable:
    mats = prep.mats(o)
    key = next((w for w in WANT if any(w in m for m in mats)), None)
    if key is None:
        continue
    mw = o.matrix_world
    pts = [mw @ v.co for v in o.data.vertices]
    sel = [p for p in pts if abs(p.y - FA) < 0.60 and p.x > 0.2]
    if len(sel) < 12:
        continue
    # radial histogram, 20 mm bins, 0..320 mm
    bins = [0] * 16
    for p in sel:
        r = math.hypot(p.y - WHEEL["cy"], p.z - WHEEL["cz"])
        k = int(r / 0.020)
        if 0 <= k < 16:
            bins[k] += 1
    # lateral histogram, 5 mm bins over the observed x range
    xlo = min(p.x for p in sel)
    xhi = max(p.x for p in sel)
    nb = max(1, int((xhi - xlo) / 0.005) + 1)
    lat = [0] * nb
    for p in sel:
        k = int((p.x - xlo) / 0.005)
        lat[min(k, nb - 1)] += 1
    rec = {
        "materials": mats,
        "n": len(sel),
        "object": o.name,
        "x_range": [round(xlo, 4), round(xhi, 4)],
        "radial_hist_20mm": bins,
        "lateral_bins_5mm": [
            [round(xlo + i * 0.005, 4), lat[i]] for i in range(nb) if lat[i] > 0],
    }
    out["corner"].setdefault(key, []).append(rec)
    print("\n%-13s %-14s n=%5d   x %.3f .. %.3f  (%.0f mm wide)"
          % (key, o.name, len(sel), xlo, xhi, (xhi - xlo) * 1000))
    print("   radial 0..320mm in 20mm bins :", bins)
    comp = [b for b in rec["lateral_bins_5mm"] if b[1] > max(30, len(sel) // 400)]
    print("   lateral bands (>1%% of verts)  :",
          ", ".join("%.0fmm x%d" % (b[0] * 1000, b[1]) for b in comp))

with open(os.path.join(OUTDIR, "probe_brake3.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("\nwrote", os.path.join(OUTDIR, "probe_brake3.json"))
print("=== PROBE3 DONE ===")
