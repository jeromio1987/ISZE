"""Definitive bed-floor / rail / beltline measurement, by ray casting (world BVH).

bpy object.ray_cast takes object-space coordinates and the imported SketchUp
meshes carry a transform, so the first attempt hit nothing.  This builds one
world-space BVH over every triangle and casts against that.

A downward ray from inside the box hits the bed floor; a ray at the box side hits
the rail; a ray at the door hits the beltline.  Those three numbers decide whether
the tail can be corrected and in which direction.

Run: blender --background --python probe_raycast.py
"""
import bpy
import os
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

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
FA_Y = (fy - PIVOT_Y) * S
RA_Y = (ry - PIVOT_Y) * S
NOSE = mn.y * S - PIVOT_Y * S
TAIL = mx.y * S - PIVOT_Y * S
print("FA %.3f  RA %.3f  nose %.3f  tail %.3f  (length %.3f)  z_top %.3f" % (
    FA_Y, RA_Y, NOSE, TAIL, TAIL - NOSE, mx.z * S - mn.z * S))

# ------------------------------------------------------------------ world BVH
print("\nbuilding world BVH ...")
verts = []
tris = []
mat_of_tri = []
for o in meshes:
    mw = o.matrix_world
    base = len(verts)
    for v in o.data.vertices:
        verts.append(mw @ v.co)
    slotnames = [s.material.name if s.material else "?" for s in o.material_slots]
    for p in o.data.polygons:
        vi = [base + i for i in p.vertices]
        nm = slotnames[p.material_index] if slotnames else "?"
        for k in range(1, len(vi) - 1):
            tris.append((vi[0], vi[k], vi[k + 1]))
            mat_of_tri.append(nm)
print("  %d verts, %d triangles" % (len(verts), len(tris)))
bvh = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)
print("  BVH built")


def cast(origin, direction, label):
    loc, nor, idx, dist = bvh.ray_cast(Vector(origin), Vector(direction), 60.0)
    if loc is None:
        print("  %-44s NO HIT" % label)
        return None
    nm = mat_of_tri[idx]
    print("  %-44s z=%.3f  (y=%+.3f x=%+.3f)  %s" % (label, loc.z, loc.y, loc.x, nm[:28]))
    return loc.z


print("\n=== downward rays from z=2.4, inside the box (THE BED FLOOR) ===")
for y in (1.30, 1.45, 1.60, 1.75, 1.90, 2.05, 2.20, 2.35, 2.45):
    row = []
    for x in (-0.45, 0.0, 0.45):
        loc, nor, idx, dist = bvh.ray_cast(Vector((x, y, 2.4)), Vector((0, 0, -1)), 60.0)
        row.append("%s" % ("%.3f" % loc.z if loc else "  -  "))
    print("   y=%.2f   x-0.45 %s   x0.00 %s   x+0.45 %s" % (y, row[0], row[1], row[2]))

print("\n=== downward rays onto the bed RAIL ===")
for y in (1.10, 1.40, 1.70, 2.00, 2.30, 2.45):
    for x in (-0.82, 0.82):
        cast((x, y, 2.4), (0, 0, -1), "rail at y=%.2f x=%+.2f" % (y, x))

print("\n=== sanity: roof and bonnet ===")
cast((0.0, -0.10, 3.0), (0, 0, -1), "roof centre")
cast((0.0, -1.90, 3.0), (0, 0, -1), "bonnet")
cast((0.30, -0.30, 3.0), (0, 0, -1), "roof off-centre")

print("\n=== sideways rays from x=+3 towards the flank (door / beltline) ===")
for y in (-1.00, -0.60, -0.30, 0.10, 0.40):
    res = []
    for z in (1.05, 1.12, 1.18, 1.24, 1.30):
        loc, nor, idx, dist = bvh.ray_cast(Vector((3.0, y, z)), Vector((-1, 0, 0)), 60.0)
        res.append("%.2f:%s" % (z, ("%.3f" % abs(loc.x)) if loc else " - "))
    print("   y=%+.2f   %s" % (y, "  ".join(res)))

print("\n=== sideways rays at the BED side ===")
for y in (1.10, 1.50, 1.90, 2.20, 2.40):
    res = []
    for z in (0.65, 0.80, 0.95, 1.10, 1.20, 1.26):
        loc, nor, idx, dist = bvh.ray_cast(Vector((3.0, y, z)), Vector((-1, 0, 0)), 60.0)
        res.append("%.2f:%s" % (z, ("%.3f" % abs(loc.x)) if loc else " - "))
    print("   y=%+.2f   %s" % (y, "  ".join(res)))

print("\n=== tailgate: rearward rays from y=+6 ===")
for z in (0.50, 0.62, 0.72, 0.85, 1.00, 1.10, 1.18, 1.24, 1.30):
    for x in (-0.60, 0.0, 0.60):
        cast((x, 6.0, z), (0, -1, 0), "tail z=%.2f x=%+.2f" % (z, x))

print("\n=== nose: forward rays ===")
for z in (0.85, 0.95, 1.05, 1.15):
    cast((0.0, -6.0, z), (0, 1, 0), "nose z=%.2f" % z)

print("\n=== front grille face: what is at the very front, centre ===")
for x in (-0.28, 0.0, 0.28):
    cast((x, -6.0, 0.93), (0, 1, 0), "grille z=0.93 x=%+.2f" % x)

print("\n=== bonnet / cab: forward rays at the cab roof front ===")
cast((0.0, -1.20, 1.70), (0, 1, 0), "roof front over windscreen")

print("\nRAYCAST PROBE DONE")
