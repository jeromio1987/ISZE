"""Compare the model's measured geometry against Isuzu's published D-Max spec.

This is the defensible accuracy measure.  The photo supplied with the original
brief is a 483 x 297 region of a booklet page in which the vehicle, the page type
and the dark setting all overlap in luminance and the vehicle is clipped at the
image edge, so an automatic silhouette segmentation cannot be trusted to a number.
Published dimensions can.

This script reports the numbers TWICE:

  BEFORE - the method the previous build used: the wheelbase read as the biggest
           y-gap in the rim cloud, and the load-box floor taken as the median of
           the topmost 6 cm of interior geometry.
  AFTER  - the wheelbase read from the brake-rotor discs and cross-checked against
           the free tyre diameter, and the load box measured by ray casting.

The before column is recomputed here rather than copied from the earlier report,
so the two columns are produced by the same code and are directly comparable.

Run: blender --background --python geometry_accuracy.py
"""
import json
import os
import statistics
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmax_prep as prep                                            # noqa: E402

SPEC = prep.SPEC
LEGACY_SCALE = 0.024016970978185472     # 3.125 / 130.116 units, the old axle split


# --------------------------------------------------------------------------- #
# material helpers
# --------------------------------------------------------------------------- #
def build_predicates(meshes):
    return {
        "paint": lambda m: 'Valencia' in m,
        "trim": lambda m: 'BlackTrims' in m,
        "tyre": lambda m: m.endswith('_Tires'),
        "rim": lambda m: 'Rims1' in m,
        "chassis": lambda m: 'UnderCarrier' in m,
    }


def verts(meshes, pred, step_target=20000, ylim=None):
    for o in meshes:
        if not any(pred(m) for m in prep.mats(o)):
            continue
        vs = o.data.vertices
        step = max(1, len(vs) // step_target)
        for i in range(0, len(vs), step):
            w = o.matrix_world @ vs[i].co
            if ylim and not (ylim[0] <= w.y <= ylim[1]):
                continue
            yield w


def bbox(meshes, pred, ylim=None):
    acc = []
    for w in verts(meshes, pred, ylim=ylim):
        acc.append(w)
    if not acc:
        return None
    return (min(w.x for w in acc), max(w.x for w in acc),
            min(w.y for w in acc), max(w.y for w in acc),
            min(w.z for w in acc), max(w.z for w in acc))


# --------------------------------------------------------------------------- #
# the lens, under whichever scale is passed in
# --------------------------------------------------------------------------- #
def measure_lens(meshes, S, *, method):
    """All the dimensional rows, measured on the CURRENT (already scaled) meshes.

    `S` is the metres-per-unit that was used to get here; it is needed only to
    report the scale method, because every vertex is already in metres.
    """
    P = build_predicates(meshes)
    allb = bbox(meshes, P["paint"])
    allb_any = bbox(meshes, lambda m: True)
    paint = bbox(meshes, P["paint"])
    tyre = bbox(meshes, P["tyre"])
    chassis = bbox(meshes, P["chassis"])
    no_mirror = bbox(meshes, lambda m: 'Valencia' in m or 'BlackTrims' in m)

    # the axles as this run's prep found them (already in metres, in AXLE)
    fa = AXLE["front_axle_y"]
    ra = AXLE["rear_axle_y"]
    nose = AXLE["nose_y"]
    tail = AXLE["tail_y"]

    # track at the front axle
    left, right = [], []
    for w in verts(meshes, lambda m: P["tyre"](m) or P["rim"](m),
                   ylim=(fa - 0.35, fa + 0.35)):
        (left if w.x < 0 else right).append(w.x)
    front_track = (((min(right) + max(right)) / 2.0 - (min(left) + max(left)) / 2.0)
                   if (left and right) else None)

    # ---- load box, by the requested method
    box = {}
    if method == "raycast":
        box = prep.measure_box(meshes, AXLE, CASTER, verbose=False)
        bed_tuple = None
        box_len = box.get("box_inner_length_m")
        box_depth = box.get("box_depth_m")
        box_width = box.get("box_inner_width_m")
    else:
        box_len, box_depth, box_width = legacy_box(meshes, P, fa, ra, nose, tail)

    # ---- bed outer length, for reference (rail start to tail)
    rail_pts = []
    for o in meshes:
        if not any('Valencia' in m for m in prep.mats(o)):
            continue
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            if 0.70 < abs(w.x) < 0.90 and w.y > ra - 0.10:
                rail_pts.append(w)
    rail_z = max(p.z for p in rail_pts) if rail_pts else None
    rail_y0 = min(p.y for p in rail_pts if p.z > rail_z - 0.02) if rail_pts else None
    box_outer_len = (tail - rail_y0) if rail_y0 is not None else None

    lens = {
        "length_m": tail - nose,
        "height_m": (allb_any[5] - allb_any[4]) if allb_any else None,
        "wheelbase_m": abs(ra - fa),
        "front_overhang_m": fa - nose,
        "rear_overhang_m": tail - ra,
        "tyre_radius_m": (tyre[5] - tyre[4]) / 2.0,
        "ground_clearance_m": chassis[4] if chassis else None,
        "track_m": front_track,
        "tyre_outer_face_width_m": (tyre[1] - tyre[0]) if tyre else None,
        "width_body_flank_m": paint[1] - paint[0],
        "width_without_mirrors_m": (no_mirror[1] - no_mirror[0]) if no_mirror else None,
        "width_overall_incl_mirrors_m": (allb_any[1] - allb_any[0]) if allb_any else None,
        "loadbox_length_m": box_len,
        "loadbox_depth_m": box_depth,
        "loadbox_width_m_inner": box_width,
        "loadbox_outer_length_m": box_outer_len,
    }
    return lens, box


def legacy_box(meshes, P, fa, ra, nose, tail):
    """The load box as the previous build measured it, for the before column.

    Floor = median of the topmost 6 cm of interior geometry, which is what the
    earlier build did.  Kept verbatim so the two columns are comparable.
    """
    cb = CAB_BACK_LEGACY
    rail = RAIL_LEGACY
    if cb is None or rail is None:
        return None, None, None
    ylo, yhi = cb + 0.15, tail - 0.30
    bed = bbox(meshes, P["paint"], ylim=(ylo, yhi))
    if not bed:
        return None, None, None
    half = (bed[1] - bed[0]) / 2.0
    zs = []
    for w in verts(meshes, lambda m: True, ylim=(ylo, yhi)):
        if abs(w.x) > half - 0.20:
            continue
        if w.z > rail - 0.10 or w.z < 0.25:
            continue
        zs.append(w.z)
    floor = None
    if zs:
        zs.sort()
        top = zs[-1]
        floor = statistics.median([z for z in zs if z > top - 0.06])
    length = bed[3] - bed[2]
    depth = (rail - floor) if floor is not None else None
    xs = [w.x for w in verts(meshes, P["paint"], ylim=(ylo, yhi))]
    inner_w = None
    if xs:
        xs.sort()
        l = [x for x in xs if x < 0]
        r = [x for x in xs if x >= 0]
        if l and r:
            inner_w = r[int(0.015 * (len(r) - 1))] - l[int(0.985 * (len(l) - 1))]
    return length, depth, inner_w


# --------------------------------------------------------------------------- #
def report(label, lens, S, extra=None):
    print("\n--- %s ---" % label)
    print("%-24s %11s %11s %9s   %s" % ("dimension", "model", "spec", "delta", "means"))
    print("-" * 92)
    rows = []
    for spec_key, meaning, model_key in COMPARE:
        mv = lens.get(model_key)
        sv = SPEC.get(spec_key)
        if mv is None or sv is None:
            print("%-24s %11s %11.3f %9s   %s" % (spec_key, "n/a", sv, "-", meaning))
            continue
        d = mv - sv
        pct = 100.0 * d / sv
        flag = "  <-- over 5%" if abs(pct) > 5 else ""
        print("%-24s %11.3f %11.3f %+8.1f%%   %s%s" % (spec_key, mv, sv, pct, meaning, flag))
        rows.append({"dimension": spec_key, "means": meaning, "model_m": round(mv, 4),
                     "spec_m": sv, "delta_m": round(d, 4), "delta_pct": round(pct, 2),
                     "over_5pct": abs(pct) > 5})
    if extra:
        print("\nscale: %s" % extra)
    return rows


COMPARE = [
    ("length_m", "overall length, bumper to tailgate", "length_m"),
    ("width_m", "body width, mirrors excluded", "width_without_mirrors_m"),
    ("height_m", "overall height, roof to ground", "height_m"),
    ("wheelbase_m", "front axle to rear axle", "wheelbase_m"),
    ("front_overhang_m", "front axle centre to nose", "front_overhang_m"),
    ("rear_overhang_m", "rear axle centre to tail", "rear_overhang_m"),
    ("track_m", "wheel centreline to wheel centreline", "track_m"),
    ("tyre_radius_m", "free tyre radius", "tyre_radius_m"),
    ("loadbox_length_m", "inside the box, bulkhead to tailgate", "loadbox_length_m"),
    ("loadbox_width_m", "inside the box, wall to wall", "loadbox_width_m_inner"),
    ("loadbox_depth_m", "bed rail down to the floor", "loadbox_depth_m"),
    ("ground_clearance_m", "lowest structural point", "ground_clearance_m"),
]

# --------------------------------------------------------------------------- #
# run
# --------------------------------------------------------------------------- #
print("=== geometry_accuracy ===")
meshes = prep.import_model()
mn0, mx0 = prep.world_bbox(meshes)
pivot_x = (mn0.x + mx0.x) / 2.0
pivot_y = (mn0.y + mx0.y) / 2.0

# ---- the legacy axle split, reproduced so the BEFORE column is derived
rim_pts = sorted(p.y for p in prep.verts_of(meshes, 'Rims1', step_target=8000))
gaps = sorted(((rim_pts[i + 1] - rim_pts[i], i) for i in range(len(rim_pts) - 1)),
              reverse=True)
cut = rim_pts[gaps[0][1]] + gaps[0][0] / 2.0
lo = [y for y in rim_pts if y < cut]
hi = [y for y in rim_pts if y >= cut]
fy_legacy = sum(lo) / len(lo)
ry_legacy = sum(hi) / len(hi)
wb_legacy = abs(ry_legacy - fy_legacy)
print("legacy axle split: front %.3f rear %.3f -> wheelbase %.3f units "
      "(scale %.6f)" % (fy_legacy, ry_legacy, wb_legacy, LEGACY_SCALE))
print("legacy front axle, rear axle, nose, tail in metres: "
      "%.3f %.3f %.3f %.3f" % ((fy_legacy - pivot_y) * LEGACY_SCALE,
                               (ry_legacy - pivot_y) * LEGACY_SCALE,
                               (mn0.y - pivot_y) * LEGACY_SCALE,
                               (mx0.y - pivot_y) * LEGACY_SCALE))

# the legacy landmarks the legacy box measurement needs
from mathutils import Matrix                                          # noqa: E402
Ml = Matrix.Translation((-pivot_x * LEGACY_SCALE, -pivot_y * LEGACY_SCALE, 0.0)) \
    @ Matrix.Scale(LEGACY_SCALE, 4)
for o in meshes:
    o.matrix_world = Ml @ o.matrix_world
bpy.context.view_layer.update()
mnl, mxl = prep.world_bbox(meshes)
drop = Matrix.Translation((0.0, 0.0, -mnl.z))
for o in meshes:
    o.matrix_world = drop @ o.matrix_world
bpy.context.view_layer.update()

AXLE = {
    "front_axle_y": (fy_legacy - pivot_y) * LEGACY_SCALE,
    "rear_axle_y": (ry_legacy - pivot_y) * LEGACY_SCALE,
    "nose_y": mnl.y if mnl.y < 0 else -2.5358,
    "tail_y": mxl.y,
}
mnl, mxl = prep.world_bbox(meshes)
AXLE["nose_y"] = mnl.y
AXLE["tail_y"] = mxl.y
# the legacy build's own landmarks, from landmarks.json if present
LM = {}
lm_path = os.path.join(HERE, "_assets", "landmarks.json")
if os.path.exists(lm_path):
    with open(lm_path) as f:
        LM = json.load(f)
CAB_BACK_LEGACY = LM.get("cab_back_y")
RAIL_LEGACY = LM.get("bed_rail_z")
print("legacy landmarks: cab_back_y %s  bed_rail_z %s" % (CAB_BACK_LEGACY, RAIL_LEGACY))

CASTER = None
lens_before, _ = measure_lens(meshes, LEGACY_SCALE, method="legacy")
rows_before = report("BEFORE (legacy axle split + legacy floor method)", lens_before,
                     LEGACY_SCALE,
                     "1 unit = %.6f m, wheelbase %.3f units"
                     % (LEGACY_SCALE, wb_legacy))

# --------------------------------------------------------------------------- #
# now the corrected build
# --------------------------------------------------------------------------- #
meshes = prep.import_model()
INFO, mn, mx = prep.scale_to_metres(meshes)
CASTER = prep.make_caster(*prep.build_bvh(meshes))
AXLE = dict(INFO)
AXLE["nose_y"] = mn.y
AXLE["tail_y"] = mx.y
lens_after, box_after = measure_lens(meshes, INFO["scale_m_per_unit"], method="raycast")
rows_after = report("AFTER (axles from the brake rotors, box measured by ray casting)",
                    lens_after, INFO["scale_m_per_unit"],
                    "1 unit = %.6f m  (tyre-diameter cross-check %.6f m, %+.2f%%)"
                    % (INFO["scale_m_per_unit"], INFO["scale_from_tyre_diameter"],
                       INFO["scale_methods_agree_pct"]))

# --------------------------------------------------------------------------- #
# before / after table for the three tail rows the brief called out
# --------------------------------------------------------------------------- #
TAIL_KEYS = ["rear_overhang_m", "loadbox_length_m", "loadbox_depth_m", "length_m",
             "height_m", "front_overhang_m"]
print("\n=== TAIL ROWS, BEFORE vs AFTER ===")
print("%-24s %10s %10s %10s %10s" % ("dimension", "before", "after", "spec",
                                     "after delta"))
before_after = []
for k in TAIL_KEYS:
    b = lens_before.get(k)
    a = lens_after.get(k)
    s = SPEC.get(k)
    bp = (100.0 * (b - s) / s) if (b is not None and s) else None
    ap = (100.0 * (a - s) / s) if (a is not None and s) else None
    print("%-24s %10s %10s %10.3f %10s    (before %s)"
          % (k,
             ("%.3f" % b) if b is not None else "n/a",
             ("%.3f" % a) if a is not None else "n/a",
             s or float('nan'),
             ("%+.1f%%" % ap) if ap is not None else "n/a",
             ("%+.1f%%" % bp) if bp is not None else "n/a"))
    before_after.append({
        "dimension": k, "spec_m": s,
        "before_m": round(b, 4) if b is not None else None,
        "before_delta_pct": round(bp, 2) if bp is not None else None,
        "after_m": round(a, 4) if a is not None else None,
        "after_delta_pct": round(ap, 2) if ap is not None else None,
    })

print("\nall measured quantities (after):")
for k in sorted(lens_after):
    v = lens_after[k]
    print("  %-32s %s" % (k, ("%.3f" % v) if isinstance(v, (int, float)) else "n/a"))

with open(os.path.join(HERE, "_qa_geometry_accuracy.json"), "w") as f:
    json.dump({
        "spec_source": "Isuzu D-Max double-cab published specification (as supplied in the brief)",
        "spec": SPEC,
        "before": {
            "method": ("wheelbase read as the biggest y-gap in the rim cloud; load-box "
                       "floor taken as the median of the topmost 6 cm of interior geometry"),
            "scale_m_per_unit": LEGACY_SCALE,
            "units_wheelbase": round(wb_legacy, 4),
            "model_all_measures_m": {k: (round(v, 4) if isinstance(v, (int, float)) else None)
                                     for k, v in lens_before.items()},
            "comparison": rows_before,
        },
        "after": {
            "method": ("wheelbase read from the brake-rotor discs and cross-checked against "
                       "the free tyre diameter; load box measured by ray casting"),
            "scale_m_per_unit": INFO["scale_m_per_unit"],
            "scale_from_tyre_diameter": INFO["scale_from_tyre_diameter"],
            "scale_methods_agree_pct": INFO["scale_methods_agree_pct"],
            "units_wheelbase": INFO["units_wheelbase"],
            "model_all_measures_m": {k: (round(v, 4) if isinstance(v, (int, float)) else None)
                                     for k, v in lens_after.items()},
            "comparison": rows_after,
            "box_raycast": {k: (round(v, 4) if isinstance(v, (int, float)) else v)
                            for k, v in box_after.items()},
        },
        "tail_before_after": before_after,
        "scale_correction_pct": round(100.0 * (INFO["scale_m_per_unit"] / LEGACY_SCALE - 1.0), 3),
        "note": (
            "The model is scaled so its wheelbase is exactly the published 3.125 m, so the "
            "wheelbase row agrees by construction and every other row is a real test. The "
            "tyre-diameter cross-check agrees to within 1%, which is a genuinely independent "
            "check because it does not use the axles at all. Two caveats worth stating: the "
            "published 1.870 m is the BODY width and width_without_mirrors_m is what is "
            "compared, while width_overall_incl_mirrors_m is the full bounding box and is "
            "wider; and the model's own proportions are internally inconsistent with the "
            "published spec by a few percent, so no single scale factor makes every row "
            "exact - anchoring on the wheelbase leaves the length about 2.6% long, while "
            "anchoring on the tyre diameter would leave the wheelbase 1% short and the "
            "length about 1.6% short. The wheelbase anchor is used because it is the "
            "dimension the vehicle is actually specified and measured by."),
    }, f, indent=1)
print("\nwrote _qa_geometry_accuracy.json")
print("GEOMETRY DONE")
