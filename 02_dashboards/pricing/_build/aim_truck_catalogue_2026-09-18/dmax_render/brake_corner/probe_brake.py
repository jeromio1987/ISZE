"""Probe: which brake rotor mesh is the front axle, and how are the parts laid out?

Run:
  blender --background --python probe_brake.py -- --outdir <dir>

Prints, for every brake / wheel related material, the world-space bounding box and
the object-space structure (how many disconnected islands), so the front/rear
question is settled from geometry rather than guessed.  Writes probe_brake.json.
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

WANT = ("BrakeRotors", "BrakeRotors1", "Calipers", "BrakePads",
        "Rims1", "Rims2", "Tires", "UnderCarrier", "BlackTrims")

drawable = prep.import_model(GLB)
print("meshes: %d" % len(drawable))
INFO, DMN, DMX = prep.scale_to_metres(drawable)
SIZE = DMX - DMN
FA, RA = INFO["front_axle_y"], INFO["rear_axle_y"]
print("front axle y=%+.3f  rear axle y=%+.3f  nose y=%+.3f  tail y=%+.3f"
      % (FA, RA, INFO["nose_y"], INFO["tail_y"]))
print("model L=%.3f W=%.3f H=%.3f" % (SIZE.y, SIZE.x, SIZE.z))
print("scale %.6f m/unit  (axles from %s)" % (INFO["scale_m_per_unit"], INFO["axle_find_method"]))

out = {"axles": {"front_y": FA, "rear_y": RA,
                 "nose_y": INFO["nose_y"], "tail_y": INFO["tail_y"]},
       "scale_m_per_unit": INFO["scale_m_per_unit"],
       "parts": {}}

for o in drawable:
    mats = prep.mats(o)
    key = next((w for w in WANT if any(w == m.split("_")[-1] or w in m for m in mats)), None)
    if key is None:
        continue
    mw = o.matrix_world
    vs = [mw @ v.co for v in o.data.vertices]
    if not vs:
        continue
    xs = sorted(p.x for p in vs)
    ys = sorted(p.y for p in vs)
    zs = sorted(p.z for p in vs)
    # split the y cloud into runs to see how many separate wheel groups there are
    runs = []
    cur = [ys[0]]
    span = max(1e-6, ys[-1] - ys[0])
    for v in ys[1:]:
        if v - cur[-1] > span * 0.08:
            runs.append((cur[0], cur[-1], len(cur)))
            cur = [v]
        else:
            cur.append(v)
    runs.append((cur[0], cur[-1], len(cur)))
    runs = [r for r in runs if r[2] > 20]
    # side split by x sign at each y run
    sides = {}
    for lo, hi, n in runs:
        sel = [p for p in vs if lo <= p.y <= hi]
        left = [p for p in sel if p.x < 0]
        right = [p for p in sel if p.x > 0]
        sides["%.3f..%.3f" % (lo, hi)] = {
            "n": n, "left_n": len(left), "right_n": len(right),
            "x_min": min(p.x for p in sel), "x_max": max(p.x for p in sel),
            "x_abs_mean": sum(abs(p.x) for p in sel) / len(sel),
        }
    rec = {
        "objects": [o.name for o in drawable if prep.mats(o) == mats],
        "materials": mats,
        "n_verts": len(vs),
        "x": [xs[0], xs[-1]],
        "y": [ys[0], ys[-1]],
        "z": [zs[0], zs[-1]],
        "y_centre": (ys[0] + ys[-1]) / 2.0,
        "y_runs": [[round(a, 4), round(b, 4), n] for a, b, n in runs],
        "runs_detail": sides,
    }
    # which run is closer to the front axle
    if runs:
        rec["y_run_centre_nearest_front_axle"] = min(
            ((a + b) / 2.0 for a, b, _ in runs), key=lambda c: abs(c - FA))
        rec["y_run_centre_nearest_rear_axle"] = min(
            ((a + b) / 2.0 for a, b, _ in runs), key=lambda c: abs(c - RA))
    out["parts"].setdefault(key, []).append(rec)
    print("\n%-16s mats=%s  verts=%d" % (key, mats, len(vs)))
    print("   x %+.3f..%+.3f   y %+.3f..%+.3f  (centre %+.3f)   z %+.3f..%+.3f"
          % (xs[0], xs[-1], ys[0], ys[-1], (ys[0] + ys[-1]) / 2.0, zs[0], zs[-1]))
    for a, b, n in runs:
        d = sides["%.3f..%.3f" % (a, b)]
        print("   y-run %+.3f..%+.3f  n=%5d  left=%5d right=%5d  |x| %.3f..%.3f"
              % (a, b, n, d["left_n"], d["right_n"], d["x_abs_mean"],
                 max(abs(d["x_min"]), abs(d["x_max"]))))

with open(os.path.join(OUTDIR, "probe_brake.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("\nwrote", os.path.join(OUTDIR, "probe_brake.json"))
print("=== PROBE DONE ===")
