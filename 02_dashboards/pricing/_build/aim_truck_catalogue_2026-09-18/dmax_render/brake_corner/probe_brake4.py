"""Probe 4: split each brake-related material into physical islands at one corner.

Both rotor materials appear at both axles and both sides, so the front/rear
premise does not hold.  This probe splits each material's geometry into connected
islands (separate physical pieces) at the front-right and rear-right corners and
reports each island's lateral (x) placement and radius about the wheel centre.
That is what tells a disc from a hub from a shield from a pad.

Run:
  blender --background --python probe_brake4.py -- --outdir _raw
"""
from __future__ import annotations

import json
import math
import os
import sys

import bpy
from mathutils import Vector, kdtree

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

# wheel centre from the front-right tyre (fixed from probe 3)
WC = {"y": -1.7415, "z": 0.3929}

WANT = ("BrakeRotors1", "BrakeRotors", "Calipers", "BrakePads", "Rims1", "Rims2",
        "Tires", "UnderCarrier")

out = {"front_axle_y": FA, "rear_axle_y": RA, "wheel_centre_front_right": WC,
       "corners": {}}


def islands(mesh):
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
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)


for corner_name, ay, sgn in (("front_right", FA, +1), ("rear_right", RA, +1)):
    out["corners"][corner_name] = {}
    print("\n================ %s  (axle y=%+.3f, right side) ================" % (corner_name, ay))
    for o in drawable:
        mats = prep.mats(o)
        key = next((w for w in WANT if any(w in m for m in mats)), None)
        if key is None:
            continue
        mw = o.matrix_world
        world = [mw @ v.co for v in o.data.vertices]
        near = [i for i, p in enumerate(world)
                if abs(p.y - ay) < 0.62 and (p.x * sgn) > 0.18]
        if len(near) < 12:
            continue
        near_set = set(near)
        recs = []
        for isl in islands(o.data):
            sel = [i for i in isl if i in near_set]
            if len(sel) < 8:
                continue
            pts = [world[i] for i in sel]
            rs = [math.hypot(p.y - WC["y"], p.z - WC["z"]) * 1000 for p in pts]
            xs = [p.x * 1000 for p in pts]
            ys = [p.y for p in pts]
            zs = [p.z for p in pts]
            recs.append({
                "n_verts": len(sel),
                "x_mm": [round(min(xs), 1), round(max(xs), 1)],
                "x_thickness_mm": round(max(xs) - min(xs), 1),
                "radius_mm": [round(min(rs), 1), round(max(rs), 1)],
                "radius_span_mm": round(max(rs) - min(rs), 1),
                "y": [round(min(ys), 4), round(max(ys), 4)],
                "z": [round(min(zs), 4), round(max(zs), 4)],
            })
        recs.sort(key=lambda r: -r["n_verts"])
        out["corners"][corner_name][key] = {"materials": mats, "object": o.name,
                                            "islands": recs[:5]}
        print("%-14s %-14s  %d islands near corner" % (key, o.name, len(recs)))
        for r in recs[:5]:
            print("    n=%5d  x %7.1f..%7.1f (%5.1f mm thick)  r %6.1f..%6.1f mm"
                  % (r["n_verts"], r["x_mm"][0], r["x_mm"][1], r["x_thickness_mm"],
                     r["radius_mm"][0], r["radius_mm"][1]))

with open(os.path.join(OUTDIR, "probe_brake4.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("\nwrote", os.path.join(OUTDIR, "probe_brake4.json"))
print("=== PROBE4 DONE ===")
