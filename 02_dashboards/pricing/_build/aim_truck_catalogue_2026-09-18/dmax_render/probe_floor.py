"""Where is the bed floor, really?

geometry_accuracy.py reports loadbox_floor_z = 0.874 by taking the median of the
topmost 6 cm of interior geometry.  That is a guess, not a measurement: it will
latch onto whatever the highest interior feature happens to be.  The floor of a
pickup box is the LARGEST horizontal surface inside the box, so measure it by
face area instead.

Also measures the cab beltline (bottom of the side glass) so the bed rail height
can be judged against it.

Run: blender --background --python probe_floor.py
"""
import bpy
import os
from collections import defaultdict
from mathutils import Matrix, Vector

HERE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build\aim_truck_catalogue_2026-09-18\dmax_render"
GLB = os.path.join(HERE, "_assets", "dmax_2021_objaverse.glb")
REAL_WB = 3.125

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
rim = []
for o in meshes:
    if any('Rims1' in m for m in mats(o)):
        for i, v in enumerate(o.data.vertices):
            if i % max(1, len(o.data.vertices) // 8000) == 0:
                rim.append(o.matrix_world @ v.co)
ys = sorted(p.y for p in rim)
gaps = sorted(((ys[i + 1] - ys[i], i) for i in range(len(ys) - 1)), reverse=True)
cut = ys[gaps[0][1]] + gaps[0][0] / 2.0
lo = [p for p in rim if p.y < cut]; hi = [p for p in rim if p.y >= cut]
fy = sum(p.y for p in lo) / len(lo); ry = sum(p.y for p in hi) / len(hi)
S = REAL_WB / abs(ry - fy)
M = Matrix.Translation((-PIVOT_X * S, -PIVOT_Y * S, -mn.z * S)) @ Matrix.Scale(S, 4)
for o in meshes:
    o.matrix_world = M @ o.matrix_world
bpy.context.view_layer.update()
print("FA %.4f RA %.4f  tail %.4f" % ((fy - PIVOT_Y) * S, (ry - PIVOT_Y) * S, mx.y * S - PIVOT_Y * S))

# ------------------------------------------------- horizontal area inside box
print("\n=== horizontal face AREA by z, face centre inside the box ===")
print("    (|x| < 0.62, y 1.25 .. 2.35  - clear of both side walls and the cab)")
area = defaultdict(float)
area_mat = defaultdict(lambda: defaultdict(float))
for o in meshes:
    me = o.data
    for p in me.polygons:
        n = (o.matrix_world.to_3x3() @ p.normal).normalized()
        if abs(n.z) < 0.90:
            continue
        c = o.matrix_world @ p.center
        if not (1.25 < c.y < 2.35) or abs(c.x) > 0.62 or c.z < 0.20:
            continue
        nm = o.material_slots[p.material_index].material.name if o.material_slots else "?"
        zb = round(c.z / 0.02) * 0.02
        area[zb] += p.area
        area_mat[zb][nm] += p.area
rows = sorted(area.items(), key=lambda kv: -kv[1])
print("  top 14 z bands by horizontal area:")
for z, a in rows[:14]:
    top = sorted(area_mat[z].items(), key=lambda kv: -kv[1])[:2]
    print("     z=%.2f  area %.4f m2   %s" % (
        z, a, ", ".join("%s(%.3f)" % (k[:22], v) for k, v in top)))
print("  all bands ascending:")
for z in sorted(area):
    if area[z] > 0.002:
        print("     z=%.2f  area %.4f m2" % (z, area[z]))

# ------------------------------------------------- beltline
print("\n=== BELTLINE: bottom of the cab side glass ===")
for o in meshes:
    if not any(m.endswith('_Windows') for m in mats(o)):
        continue
    vmap = {}
    for p in o.data.polygons:
        nm = o.material_slots[p.material_index].material.name if o.material_slots else "?"
        for vi in p.vertices:
            vmap[vi] = nm
    fl = []
    for i, v in enumerate(o.data.vertices):
        w = o.matrix_world @ v.co
        if abs(w.x) > 0.55 and -1.35 < w.y < 0.95:
            fl.append((w.y, w.z))
    if fl:
        zs = sorted(z for _, z in fl)
        print("  side glass: n=%d  z %.3f .. %.3f  (10th pct %.3f, 50th %.3f)" % (
            len(fl), zs[0], zs[-1], zs[int(0.10 * (len(zs) - 1))], zs[len(zs) // 2]))
        # the beltline is the lower edge at the MIDDLE of the door, not at the
        # wrapped-forward corner
        mid = sorted(z for y, z in fl if -0.90 < y < 0.60)
        if mid:
            print("  door mid-span glass: n=%d  z %.3f .. %.3f  -> beltline %.3f" % (
                len(mid), mid[0], mid[-1], mid[0]))

# ------------------------------------------------- what is at 0.85-0.90
print("\n=== what sits at z 0.82 .. 0.95 inside the box ===")
agg = defaultdict(list)
for o in meshes:
    vmap = {}
    for p in o.data.polygons:
        nm = o.material_slots[p.material_index].material.name if o.material_slots else "?"
        for vi in p.vertices:
            vmap[vi] = nm
    for i, v in enumerate(o.data.vertices):
        w = o.matrix_world @ v.co
        if 0.82 < w.z < 0.95 and 1.20 < w.y < 2.40 and abs(w.x) < 0.65:
            agg[vmap.get(i, "?")].append(w)
for k in sorted(agg, key=lambda k: -len(agg[k])):
    ps = agg[k]
    print("   %-32s n=%-5d y %.2f..%.2f  x %.2f..%.2f  z %.3f..%.3f" % (
        k[:32], len(ps), min(p.y for p in ps), max(p.y for p in ps),
        min(p.x for p in ps), max(p.x for p in ps),
        min(p.z for p in ps), max(p.z for p in ps)))

print("\n=== what sits at z 0.60 .. 0.80 inside the box (the real floor?) ===")
agg2 = defaultdict(list)
for o in meshes:
    vmap = {}
    for p in o.data.polygons:
        nm = o.material_slots[p.material_index].material.name if o.material_slots else "?"
        for vi in p.vertices:
            vmap[vi] = nm
    for i, v in enumerate(o.data.vertices):
        w = o.matrix_world @ v.co
        if 0.58 < w.z < 0.80 and 1.20 < w.y < 2.40 and abs(w.x) < 0.65:
            agg2[vmap.get(i, "?")].append(w)
for k in sorted(agg2, key=lambda k: -len(agg2[k])):
    ps = agg2[k]
    print("   %-32s n=%-5d y %.2f..%.2f  x %.2f..%.2f  z %.3f..%.3f" % (
        k[:32], len(ps), min(p.y for p in ps), max(p.y for p in ps),
        min(p.x for p in ps), max(p.x for p in ps),
        min(p.z for p in ps), max(p.z for p in ps)))

print("\nFLOOR PROBE DONE")
