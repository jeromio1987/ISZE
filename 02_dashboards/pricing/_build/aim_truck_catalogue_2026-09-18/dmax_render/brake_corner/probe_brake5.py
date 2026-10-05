"""Probe 5b: full geometry of the front-right brake corner, per part group.

Both rotor materials appear at every corner, so each material name is treated as
one part group and described properly: every connected island, its lateral (x)
band and its radial band about the fitted wheel centre.  The centroid written
here is the vertex centroid of the group, which is where a callout leader should
point.

Run:
  blender --background --python probe_brake5.py -- --outdir _raw
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
FA = INFO["front_axle_y"]
WC = {"y": -1.7415, "z": 0.3929}      # front-right wheel centre, fitted in probe 3

# part group -> the material names that make it up
GROUPS = [
    ("tyre",      ["2021_Isuzu_Dmax_Tires"]),
    ("wheel",     ["2021_Isuzu_Dmax_Rims1", "2021_Isuzu_Dmax_Rims2"]),
    ("disc_face", ["2021_Isuzu_Dmax_BrakeRotors"]),
    ("disc_ring", ["2021_Isuzu_Dmax_BrakeRotors1"]),
    ("pads",      ["2021_Isuzu_Dmax_BrakePads"]),
    ("caliper",   ["2021_Isuzu_Dmax_Calipers"]),
    ("liner",     ["2021_Isuzu_Dmax_BlackTrims"]),
    ("under",     ["2021_Isuzu_Dmax_UnderCarrier"]),
]


def islands(mesh, minn=25):
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
    g = {}
    for i in range(n):
        g.setdefault(find(i), []).append(i)
    return [v for v in sorted(g.values(), key=len, reverse=True) if len(v) >= minn]


def pct(v, q):
    s = sorted(v)
    return s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]


out = {"front_axle_y": FA, "wheel_centre": WC, "parts": {}}

for label, matnames in GROUPS:
    objs = [o for o in drawable
            if any(m in matnames for m in prep.mats(o))]
    pts, isl_recs = [], []
    for o in objs:
        mw = o.matrix_world
        for isl in islands(o.data):
            world = [mw @ o.data.vertices[i].co for i in isl]
            cy = sum(p.y for p in world) / len(world)
            cx = sum(p.x for p in world) / len(world)
            if abs(cy - FA) > 0.62 or cx < 0.18:
                continue
            pts.extend(world)
            xs = [p.x * 1000 for p in world]
            rs = [math.hypot(p.y - WC["y"], p.z - WC["z"]) * 1000 for p in world]
            isl_recs.append({
                "object": o.name, "n": len(world),
                "x_mm": [round(min(xs), 1), round(max(xs), 1)],
                "r_mm": [round(min(rs), 1), round(max(rs), 1)],
                "centroid": [round(sum(p.x for p in world) / len(world), 5),
                             round(sum(p.y for p in world) / len(world), 5),
                             round(sum(p.z for p in world) / len(world), 5)],
            })
    if not pts:
        print("!! no geometry for %s" % label)
        continue
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    rs = [math.hypot(p.y - WC["y"], p.z - WC["z"]) for p in pts]
    cen = Vector((sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)))
    rec = {
        "materials": matnames,
        "n_verts": len(pts),
        "x_mm": [round(min(xs) * 1000, 1), round(max(xs) * 1000, 1)],
        "x_p05_p95_mm": [round(pct(xs, 0.05) * 1000, 1), round(pct(xs, 0.95) * 1000, 1)],
        "radius_mm": [round(min(rs) * 1000, 1), round(max(rs) * 1000, 1)],
        "radius_p05_p95_mm": [round(pct(rs, 0.05) * 1000, 1), round(pct(rs, 0.95) * 1000, 1)],
        "y": [round(min(ys), 4), round(max(ys), 4)],
        "z": [round(min(zs), 4), round(max(zs), 4)],
        "centroid": [round(v, 5) for v in cen],
        "islands": sorted(isl_recs, key=lambda r: -r["n"]),
    }
    out["parts"][label] = rec
    print("\n=== %-10s verts %6d   islands %d" % (label, rec["n_verts"], len(isl_recs)))
    print("   x %7.1f .. %7.1f mm  (p05-p95 %7.1f .. %7.1f)"
          % (rec["x_mm"][0], rec["x_mm"][1], rec["x_p05_p95_mm"][0], rec["x_p05_p95_mm"][1]))
    print("   r %7.1f .. %7.1f mm  (p05-p95 %7.1f .. %7.1f)"
          % (rec["radius_mm"][0], rec["radius_mm"][1],
             rec["radius_p05_p95_mm"][0], rec["radius_p05_p95_mm"][1]))
    print("   centroid x=%.4f y=%.4f z=%.4f" % tuple(rec["centroid"]))
    for r in rec["islands"][:6]:
        print("      n=%5d  x %7.1f..%7.1f  r %6.1f..%6.1f  %s"
              % (r["n"], r["x_mm"][0], r["x_mm"][1], r["r_mm"][0], r["r_mm"][1], r["object"]))

with open(os.path.join(OUTDIR, "corner_geometry.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("\nwrote", os.path.join(OUTDIR, "corner_geometry.json"))
print("=== PROBE5 DONE ===")
