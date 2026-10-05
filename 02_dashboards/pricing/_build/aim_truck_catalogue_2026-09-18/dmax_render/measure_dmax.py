"""Measure the D-Max silhouette off the model itself and find the real landmarks.

Scans the vehicle's top-of-body height as a function of length, which reveals the
bonnet line, windscreen rake, roof, cab back and bed rail as actual inflections
rather than guesses.  Writes _assets/landmarks.json, consumed by build_dmax_render.py.

Run: blender --background --python measure_dmax.py
"""
import bpy, os, json, math, statistics
from mathutils import Matrix, Vector

HERE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\aim_truck_catalogue_2026-09-18\dmax_render"
GLB = os.path.join(HERE, "_assets", "dmax_2021_objaverse.glb")
REAL_WHEELBASE = 3.125

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.polygons) > 0]


def mats(o):
    return [s.material.name for s in o.material_slots if s.material]


bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)

mn = Vector((1e18,) * 3); mx = Vector((-1e18,) * 3)
for o in meshes:
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], p[i]); mx[i] = max(mx[i], p[i])
PIVOT_X = (mn.x + mx.x) / 2.0
PIVOT_Y = (mn.y + mx.y) / 2.0

# scale from the rims, as in the main build
pts = []
for o in meshes:
    if any('Rims1' in m for m in mats(o)):
        vs = o.data.vertices
        for i in range(0, len(vs), max(1, len(vs) // 8000)):
            pts.append(o.matrix_world @ vs[i].co)
ys = sorted(p.y for p in pts)
gaps = sorted(((ys[i + 1] - ys[i], i) for i in range(len(ys) - 1)), reverse=True)
cut = ys[gaps[0][1]] + gaps[0][0] / 2.0
lo = [p for p in pts if p.y < cut]; hi = [p for p in pts if p.y >= cut]
fy = sum(p.y for p in lo) / len(lo); ry = sum(p.y for p in hi) / len(hi)
S = REAL_WHEELBASE / abs(ry - fy)
M = Matrix.Translation((-PIVOT_X * S, -PIVOT_Y * S, -mn.z * S)) @ Matrix.Scale(S, 4)
for o in meshes:
    o.matrix_world = M @ o.matrix_world
bpy.context.view_layer.update()

mn2 = Vector((1e18,) * 3); mx2 = Vector((-1e18,) * 3)
for o in meshes:
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c)
        for i in range(3):
            mn2[i] = min(mn2[i], p[i]); mx2[i] = max(mx2[i], p[i])
print("model metres: L=%.3f W=%.3f H=%.3f" % (mx2.y - mn2.y, mx2.x - mn2.x, mx2.z - mn2.z))
print("front axle y=%.3f rear axle y=%.3f" % ((fy - PIVOT_Y) * S, (ry - PIVOT_Y) * S))
FA_Y = (fy - PIVOT_Y) * S

# tyre radius, for reporting: half the tyre's vertical extent
tz = []
for o in meshes:
    if any(m.endswith('_Tires') for m in mats(o)):
        vs = o.data.vertices
        for i in range(0, len(vs), max(1, len(vs) // 4000)):
            tz.append((o.matrix_world @ vs[i].co).z)
TYRE_R = (max(tz) - min(tz)) / 2.0 if tz else 0.0
print("tyre radius from model: %.3f m (published 255/65 R17 ~ 0.382 m)" % TYRE_R)

# ---- silhouette from the PAINTED panels only ------------------------------
# Black plastic (roof rails, arch flares) sits proud of the panels, so including
# it corrupts the top-line.  Paint alone gives the shape a reader recognises.
PAINT = lambda o: any('Valencia' in m for m in mats(o))
GLASS = lambda o: any(m.endswith('_Windows') for m in mats(o))

NB = 400
y0, y1 = mn2.y, mx2.y
ptop = [None] * NB
pbot = [None] * NB
gtop = [None] * NB
for o in meshes:
    is_p = PAINT(o); is_g = GLASS(o)
    if not (is_p or is_g):
        continue
    vs = o.data.vertices
    step = max(1, len(vs) // 80000)
    for i in range(0, len(vs), step):
        w = o.matrix_world @ vs[i].co
        k = max(0, min(NB - 1, int((w.y - y0) / (y1 - y0) * (NB - 1))))
        if is_g:
            if gtop[k] is None or w.z > gtop[k]:
                gtop[k] = w.z
        else:
            if ptop[k] is None or w.z > ptop[k]:
                ptop[k] = w.z
            if pbot[k] is None or w.z < pbot[k]:
                pbot[k] = w.z

prof = [{"y": round(y0 + (k + 0.5) * (y1 - y0) / NB, 4),
         "paint_top": round(ptop[k], 4) if ptop[k] is not None else None,
         "paint_bot": round(pbot[k], 4) if pbot[k] is not None else None,
         "glass_top": round(gtop[k], 4) if gtop[k] is not None else None}
        for k in range(NB)]

print("\n    y     paint_top  paint_bot  glass_top")
for k in range(0, NB, 8):
    p = prof[k]
    f = lambda v: ("%8.3f" % v) if v is not None else "     -  "
    print("%7.3f  %s  %s  %s" % (p["y"], f(p["paint_top"]), f(p["paint_bot"]), f(p["glass_top"])))

# ---- landmarks, read off the paint profile --------------------------------
valid = [p for p in prof if p["paint_top"] is not None]
roof_z = max(p["paint_top"] for p in valid)
# the roof is the contiguous run within 4 cm of the highest point
roof_pts = [p for p in valid if p["paint_top"] > roof_z - 0.04]
roof_y0 = min(p["y"] for p in roof_pts); roof_y1 = max(p["y"] for p in roof_pts)

# windscreen base: the cowl, i.e. where the bonnet stops rising and the screen
# begins.  Take the bonnet plateau just behind the front axle, then the first
# point further back that clears it by 8 cm.
ax_zone = [p for p in valid if (FA_Y - 0.10) < p["y"] < (FA_Y + 0.50)]
bonnet_z = max(p["paint_top"] for p in ax_zone) if ax_zone else None
ws_base_y = roof_y0 - 0.55
if bonnet_z is not None:
    cands = [p["y"] for p in valid if p["y"] > FA_Y + 0.30 and p["paint_top"] > bonnet_z + 0.08]
    if cands:
        ws_base_y = min(cands)

# cab back and bed rail: behind the roof the paint drops to the bed rail
behind = [p for p in valid if p["y"] > roof_y1 + 0.03]
bed_rail_z = max(p["paint_top"] for p in behind) if behind else None
if behind:
    # the rail is the flat run over the box, so take the median of the back half
    hi_y = max(x["y"] for x in behind)
    tail_half = [p["paint_top"] for p in behind if p["y"] > (roof_y1 + hi_y) / 2]
    bed_rail_z = float(statistics.median(tail_half)) if tail_half else bed_rail_z
    bed_pts = [p for p in behind if abs(p["paint_top"] - bed_rail_z) < 0.05]
    bed_y0 = min(p["y"] for p in bed_pts) if bed_pts else None
    bed_y1 = max(p["y"] for p in bed_pts) if bed_pts else None
    # the cab ends where the paint first drops to the rail
    cab_back_y = next((p["y"] for p in behind if p["paint_top"] < bed_rail_z + 0.05), roof_y1)
else:
    bed_y0 = bed_y1 = cab_back_y = None

gs = [p for p in prof if p["glass_top"] is not None]
glass_y0 = min(p["y"] for p in gs) if gs else None
glass_y1 = max(p["y"] for p in gs) if gs else None
glass_max_z = max(p["glass_top"] for p in gs) if gs else None
glass_min_z = min(p["glass_top"] for p in gs) if gs else None
mids = [p for p in valid if y0 + 1.0 < p["y"] < y1 - 1.0 and p["paint_bot"] is not None]
sill_z = min(p["paint_bot"] for p in mids) if mids else None
lastp = [p for p in valid if p["y"] > y1 - 0.30]
tail_top_z = max(p["paint_top"] for p in lastp) if lastp else None

lm = {
    "model_size_m": {"length": round(mx2.y - mn2.y, 4), "width": round(mx2.x - mn2.x, 4),
                     "height": round(mx2.z - mn2.z, 4)},
    "scale_m_per_unit": S, "units_wheelbase": abs(ry - fy),
    "front_axle_y": round((fy - PIVOT_Y) * S, 4), "rear_axle_y": round((ry - PIVOT_Y) * S, 4),
    "tyre_radius_m": round(TYRE_R, 4),
    "nose_y": round(y0, 4), "tail_y": round(y1, 4),
    "roof_z": round(roof_z, 4),
    "roof_y": [round(roof_y0, 4), round(roof_y1, 4)],
    "bed_rail_z": round(bed_rail_z, 4) if bed_rail_z else None,
    "bed_rail_y": [round(bed_y0, 4), round(bed_y1, 4)] if bed_y0 else None,
    "bonnet_z": round(bonnet_z, 4) if bonnet_z else None,
    "windscreen_base_y": round(ws_base_y, 4),
    "cab_back_y": round(cab_back_y, 4) if cab_back_y else None,
    "glass_y": [round(glass_y0, 4), round(glass_y1, 4)] if glass_y0 else None,
    "glass_z": [round(glass_min_z, 4), round(glass_max_z, 4)] if glass_min_z else None,
    "sill_z": round(sill_z, 4) if sill_z else None,
    "tail_top_z": round(tail_top_z, 4) if tail_top_z else None,
    "profile": prof,
}
with open(os.path.join(HERE, "_assets", "landmarks.json"), "w") as f:
    json.dump(lm, f, indent=1)
print("\n--- landmarks ---")
for k, v in lm.items():
    if k != "profile":
        print("  %-20s %s" % (k, v))
print("MEASURE DONE")
