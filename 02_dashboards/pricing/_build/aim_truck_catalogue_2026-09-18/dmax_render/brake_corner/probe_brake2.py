"""Probe 2: settle what BrakeRotors vs BrakeRotors1 actually are, from radius.

Both rotor materials appear at both axles, so "front vs rear" is not a y split.
The disc plane of a wheel is the y-z plane (the axle runs along x).  So for each
material and each axle, measure the radius about the axle centre, the radial
thickness, the lateral (x) placement and the number of disconnected islands.
That distinguishes a friction ring from a hub from a shield without guessing.

Run:
  blender --background --python probe_brake2.py -- --outdir _raw
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

WANT = ("BrakeRotors1", "BrakeRotors", "Calipers", "BrakePads", "Rims1", "Rims2",
        "Tires")

drawable = prep.import_model(GLB)
INFO, DMN, DMX = prep.scale_to_metres(drawable)
FA, RA = INFO["front_axle_y"], INFO["rear_axle_y"]

# wheel centre height: half the tyre height on the front axle
_tz = [p.z for p in prep.verts_of(drawable, '_Tires', step_target=4000)]
ZC = (max(_tz) + min(_tz)) / 2.0
print("front axle y=%+.4f  rear axle y=%+.4f  wheel centre z=%.4f" % (FA, RA, ZC))

out = {"front_axle_y": FA, "rear_axle_y": RA, "wheel_centre_z": ZC, "parts": {}}


def islands_of(mesh):
    """Count disconnected vertex islands by union-find over edges."""
    n = len(mesh.vertices)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for e in mesh.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    roots = {}
    for i in range(n):
        roots.setdefault(find(i), 0)
        roots[find(i)] += 1
    return sorted(roots.values(), reverse=True)


for o in drawable:
    mats = prep.mats(o)
    key = next((w for w in WANT if any(w in m for m in mats)), None)
    if key is None:
        continue
    mw = o.matrix_world
    mw3 = mw.to_3x3()
    for ax_name, ay in (("front", FA), ("rear", RA)):
        for side_name, sgn in (("L", -1), ("R", +1)):
            pts = [mw @ v.co for v in o.data.vertices]
            sel = [p for p in pts if abs(p.y - ay) < 0.55 and (p.x * sgn) > 0.2]
            if len(sel) < 12:
                continue
            r = [math.hypot(p.y - ay, p.z - ZC) for p in sel]
            xs = [p.x for p in sel]
            r_lo, r_hi = min(r), max(r)
            rec = {
                "material": mats,
                "n_verts_in_corner": len(sel),
                "radius_min_m": round(r_lo, 4),
                "radius_max_m": round(r_hi, 4),
                "radius_span_mm": round((r_hi - r_lo) * 1000, 1),
                "radius_mean_mm": round(1000 * sum(r) / len(r), 1),
                "x_min": round(min(xs), 4), "x_max": round(max(xs), 4),
                "x_span_mm": round((max(xs) - min(xs)) * 1000, 1),
                "x_abs_mean": round(sum(abs(v) for v in xs) / len(xs), 4),
                "y_lo": round(min(p.y for p in sel), 4),
                "y_hi": round(max(p.y for p in sel), 4),
                "z_lo": round(min(p.z for p in sel), 4),
                "z_hi": round(max(p.z for p in sel), 4),
            }
            # object-space islands, only when the object is single-sided
            if sgn > 0 and ax_name == "front":
                rec["islands_whole_object"] = islands_of(o.data)[:6]
            out["parts"].setdefault("%s_%s" % (key, o.name), {})["%s_%s" % (ax_name, side_name)] = rec
            print("%-14s %-28s %s/%s  n=%5d  r %5.1f..%5.1f mm (span %5.1f)  "
                  "x %.3f..%.3f (span %4.0f mm)  y %+.3f..%+.3f"
                  % (key, o.name, ax_name, side_name, len(sel), r_lo * 1000, r_hi * 1000,
                     (r_hi - r_lo) * 1000, min(xs), max(xs), (max(xs) - min(xs)) * 1000,
                     min(p.y for p in sel), max(p.y for p in sel)))
    print()

with open(os.path.join(OUTDIR, "probe_brake2.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("wrote", os.path.join(OUTDIR, "probe_brake2.json"))
print("=== PROBE2 DONE ===")
