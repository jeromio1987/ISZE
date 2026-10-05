"""Dump the structure of the D-Max GLB so the tail can be fixed without guessing.

Prints, per object and per material:
  * object name, vertex/polygon count, material slots
  * world bounding box in the SCALED metre frame used by build_dmax_render.py
  * for each material slot, the y and z extent of the vertices that use it

Run: blender --background --python inspect_dmax.py
"""
import bpy
import json
import os
from mathutils import Matrix, Vector

HERE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\aim_truck_catalogue_2026-09-18\dmax_render"
GLB = os.path.join(HERE, "_assets", "dmax_2021_objaverse.glb")
REAL_WB = 3.125

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

allobs = list(bpy.data.objects)
meshes = [o for o in allobs if o.type == 'MESH' and len(o.data.polygons) > 0]
print("objects total %d   drawable meshes %d" % (len(allobs), len(meshes)))
print("non-mesh:", [o.name for o in allobs if o.type != 'MESH'])


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

mn = Vector((1e18,) * 3)
mx = Vector((-1e18,) * 3)
for o in meshes:
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], p[i])
            mx[i] = max(mx[i], p[i])
PIVOT_X = (mn.x + mx.x) / 2.0
PIVOT_Y = (mn.y + mx.y) / 2.0

rim = []
for o in meshes:
    if any('Rims1' in m for m in mats(o)):
        vs = o.data.vertices
        for i in range(0, len(vs), max(1, len(vs) // 8000)):
            rim.append(o.matrix_world @ vs[i].co)
ys = sorted(p.y for p in rim)
gaps = sorted(((ys[i + 1] - ys[i], i) for i in range(len(ys) - 1)), reverse=True)
cut = ys[gaps[0][1]] + gaps[0][0] / 2.0
lo = [p for p in rim if p.y < cut]
hi = [p for p in rim if p.y >= cut]
fy = sum(p.y for p in lo) / len(lo)
ry = sum(p.y for p in hi) / len(hi)
S = REAL_WB / abs(ry - fy)
M = Matrix.Translation((-PIVOT_X * S, -PIVOT_Y * S, -mn.z * S)) @ Matrix.Scale(S, 4)
for o in meshes:
    o.matrix_world = M @ o.matrix_world
bpy.context.view_layer.update()

print("scale %.6f  front axle y %.4f  rear axle y %.4f" % (
    S, (fy - PIVOT_Y) * S, (ry - PIVOT_Y) * S))

# ---------------------------------------------------------------- object list
print("\n=== OBJECTS (sorted by tail y) ===")
rows = []
for o in meshes:
    vs = o.data.vertices
    step = max(1, len(vs) // 6000)
    xs, ysv, zs = [], [], []
    for i in range(0, len(vs), step):
        w = o.matrix_world @ vs[i].co
        xs.append(w.x); ysv.append(w.y); zs.append(w.z)
    if not ysv:
        continue
    rows.append({
        "name": o.name,
        "verts": len(vs), "polys": len(o.data.polygons),
        "mats": mats(o),
        "y": [min(ysv), max(ysv)], "x": [min(xs), max(xs)], "z": [min(zs), max(zs)],
    })
rows.sort(key=lambda r: -r["y"][1])
for r in rows:
    print("%-46s v%-7d p%-7d y[%7.3f %7.3f] z[%6.3f %6.3f] x[%6.3f %6.3f] %s" % (
        r["name"][:46], r["verts"], r["polys"], r["y"][0], r["y"][1],
        r["z"][0], r["z"][1], r["x"][0], r["x"][1], ",".join(m[:24] for m in r["mats"])))

# ------------------------------------------------------------- material spans
print("\n=== MATERIAL SPANS (y and z across all meshes using it) ===")
mat_span = {}
for o in meshes:
    vs = o.data.vertices
    step = max(1, len(vs) // 40000)
    # map vertex index -> set of material names via polygons
    vmat = {}
    for pi, p in enumerate(o.data.polygons):
        mname = None
        if o.material_slots:
            try:
                mname = o.material_slots[p.material_index].material.name
            except Exception:
                mname = None
        for vi in p.vertices:
            vmat[vi] = mname
    for i in range(0, len(vs), step):
        mname = vmat.get(i)
        if not mname:
            continue
        w = o.matrix_world @ vs[i].co
        d = mat_span.setdefault(mname, {"y": [1e18, -1e18], "z": [1e18, -1e18],
                                        "x": [1e18, -1e18], "n": 0})
        for k, v in (("y", w.y), ("z", w.z), ("x", w.x)):
            d[k][0] = min(d[k][0], v); d[k][1] = max(d[k][1], v)
        d["n"] += 1
for mname in sorted(mat_span, key=lambda k: -mat_span[k]["y"][1]):
    d = mat_span[mname]
    print("%-34s n%-7d y[%7.3f %7.3f] z[%6.3f %6.3f] x[%6.3f %6.3f]" % (
        mname[:34], d["n"], d["y"][0], d["y"][1], d["z"][0], d["z"][1], d["x"][0], d["x"][1]))

with open(os.path.join(HERE, "_raw", "inspect_objects.json"), "w") as f:
    json.dump({"scale": S, "objects": rows,
               "material_spans": {k: {"y": v["y"], "z": v["z"], "x": v["x"], "n": v["n"]}
                                  for k, v in mat_span.items()}}, f, indent=1)
print("\nwrote _raw/inspect_objects.json")
print("INSPECT DONE")
