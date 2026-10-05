"""Map the wheel-arch openings, and the bed rail, by material hit.

For a grid over each wheel, cast a ray from outboard (x=+3) towards the flank and
record the material of the FIRST hit.  If that is tyre / rim / brake, the ray went
through the arch opening; if it is paint or black trim, it hit sheet metal.  That
gives the true opening outline without guessing at edges.

Same trick vertically for the bed rail: down-rays inboard of the flare, where the
rail surface actually is.

Run: blender --background --python probe_arch2.py
"""
import bpy
import json
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
print("FA %.3f RA %.3f" % (FA_Y, RA_Y))

verts, tris, mat_of_tri = [], [], []
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
bvh = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)
print("BVH: %d tris" % len(tris))

OPEN_MATS = ('Tires', 'Rims1', 'Rims2', 'BrakeRotor', 'Calipers', 'BrakePad', 'UnderCarrier')


def hit(x, y, z):
    loc, nor, idx, dist = bvh.ray_cast(Vector((x, y, z)), Vector((-1, 0, 0)), 60.0)
    if loc is None:
        return None, None
    return loc, mat_of_tri[idx]


def opening(cy, label, yhalf=0.75):
    """For each y, the highest z whose outboard ray still lands on wheel/underside."""
    print("\n=== %s: arch opening (top edge of the cut-out) ===" % label)
    step = 0.01
    rows = []
    k = int(-yhalf / step)
    while k * step <= yhalf:
        y = cy + k * step
        top = None
        z = 0.20
        while z < 1.30:
            loc, nm = hit(3.0, y, z)
            if loc is not None and any(o in nm for o in OPEN_MATS):
                top = z
            z += 0.01
        if top is not None:
            rows.append((y, top))
        k += 1
    if not rows:
        print("   no opening found")
        return
    ys_ = [r[0] for r in rows]
    apexy, apexz = max(rows, key=lambda r: r[1])
    print("   opening spans y %.3f .. %.3f  (width %.3f, centre %.3f)" % (
        min(ys_), max(ys_), max(ys_) - min(ys_), (min(ys_) + max(ys_)) / 2))
    print("   apex at y %.3f, z %.3f  ->  radius %.3f from the axle centre z 0.368"
          % (apexy, apexz, apexz - 0.368))
    # print the outline coarsely
    print("   outline (y, top-of-opening z):")
    for y, t in rows[::4]:
        print("      %6.3f  %6.3f" % (y, t))
    return rows


opening(FA_Y, "FRONT wheel")
opening(RA_Y, "REAR wheel")

print("\n=== lateral: how far out does the opening extend? (ray along +x from the centreline) ===")
for label, cy in (("front", FA_Y), ("rear", RA_Y)):
    for z in (0.368, 0.50, 0.70):
        # ray from x=0 outward at the axle height: what do we hit last?
        lastnm = None
        xx = 0.0
        while xx < 1.10:
            loc, nm = hit(-0.001, cy, z)  # start just off centre, cast to +x
            break
        print("   %s z=%.3f  (see next block)" % (label, z))

# outward ray from inside the box, at each wheel, to find the outermost sheet
print("\n=== outward (towards +x) from the vehicle centreline at the axle ===")
for label, cy in (("front", FA_Y), ("rear", RA_Y)):
    for z in (0.368, 0.55, 0.75, 0.95):
        loc, nor, idx, dist = bvh.ray_cast(Vector((0.0, cy, z)), Vector((1, 0, 0)), 60.0)
        nm = mat_of_tri[idx] if loc else "-"
        # now the reverse: from far +x inward, first hit
        loc2, nor2, idx2, d2 = bvh.ray_cast(Vector((3.0, cy, z)), Vector((-1, 0, 0)), 60.0)
        nm2 = mat_of_tri[idx2] if loc2 else "-"
        print("   %-5s z=%.3f  outward-from-centre first hit x=%-7s(%s)   inward-from-outside first hit x=%-7s(%s)" % (
            label, z,
            ("%.3f" % loc.x) if loc else "-", nm[:22],
            ("%.3f" % loc2.x) if loc2 else "-", nm2[:22]))

print("\n=== BED RAIL: down-rays at several x, inside and outside the flare ===")
for x in (0.50, 0.60, 0.68, 0.74, 0.78, 0.82, 0.86, 0.90):
    res = []
    for y in (0.95, 1.20, 1.50, 1.80, 2.10, 2.30, 2.45):
        loc, nor, idx, dist = bvh.ray_cast(Vector((x, y, 2.2)), Vector((0, 0, -1)), 60.0)
        res.append("%.2f:%s" % (y, ("%.3f" % loc.z) if loc else "  - "))
    print("   x=%+.2f   %s" % (x, "  ".join(res)))

print("\n=== BED FLOOR: down-rays to confirm, at the centre line ===")
for y in (1.30, 1.60, 1.90, 2.20, 2.36, 2.42):
    loc, nor, idx, dist = bvh.ray_cast(Vector((0.0, y, 2.2)), Vector((0, 0, -1)), 60.0)
    print("   y=%.2f  floor z=%s  (%s)" % (y, ("%.4f" % loc.z) if loc else "-",
                                          mat_of_tri[idx][:26] if loc else "-"))

print("\n=== TAILGATE TOP: down-rays just behind the box ===")
for y in (2.40, 2.46, 2.50, 2.52):
    loc, nor, idx, dist = bvh.ray_cast(Vector((0.0, y, 2.2)), Vector((0, 0, -1)), 60.0)
    print("   y=%.2f  z=%s  (%s)" % (y, ("%.4f" % loc.z) if loc else "-",
                                    mat_of_tri[idx][:26] if loc else "-"))

print("\nARCH2 PROBE DONE")
