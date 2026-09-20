"""Second probe: the bed floor, the tailgate, the badge, and the small details.

Run: blender --background --python probe_detail.py
"""
import bpy
import json
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

mn = Vector((1e18,) * 3)
mx = Vector((-1e18,) * 3)
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
        vs = o.data.vertices
        for i in range(0, len(vs), max(1, len(vs) // 8000)):
            rim.append(o.matrix_world @ vs[i].co)
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
print("scale %.6f  FA %.4f  RA %.4f" % (S, FA_Y, RA_Y))

# ------------------------------------------------ horizontal faces = the floor
print("\n=== near-horizontal downward/upward faces in the bed region (y 0.9..2.6) ===")
zc = defaultdict(int)
zc_by_mat = defaultdict(lambda: defaultdict(int))
for o in meshes:
    me = o.data
    for p in me.polygons:
        n = (o.matrix_world.to_3x3() @ p.normal).normalized()
        if abs(n.z) < 0.85:
            continue
        c = o.matrix_world @ p.center
        if not (0.9 < c.y < 2.6):
            continue
        if abs(c.x) > 0.75:
            continue
        if not (0.10 < c.z < 1.35):
            continue
        nm = o.material_slots[p.material_index].material.name if o.material_slots else "?"
        zc[round(c.z, 2)] += 1
        zc_by_mat[round(c.z, 2)][nm] += 1
for z in sorted(zc):
    top = sorted(zc_by_mat[z].items(), key=lambda kv: -kv[1])[:2]
    print("   z=%.2f  faces=%-5d  %s" % (z, zc[z], ", ".join("%s(%d)" % (a[:24], b) for a, b in top)))

# ------------------------------------------------ what is in the bed interior
print("\n=== ALL geometry inside the box, by 5cm z band (|x|<0.60, y 1.10..2.30) ===")
band = defaultdict(lambda: defaultdict(int))
zmax = defaultdict(float)
for o in meshes:
    nm = o.material_slots[0].material.name if o.material_slots else "?"
    vmap = {}
    for p in o.data.polygons:
        m_ = o.material_slots[p.material_index].material.name if o.material_slots else "?"
        for vi in p.vertices:
            vmap[vi] = m_
    for i, v in enumerate(o.data.vertices):
        w = o.matrix_world @ v.co
        if not (1.10 < w.y < 2.30):
            continue
        if abs(w.x) > 0.60:
            continue
        m_ = vmap.get(i, nm)
        band[round(w.z / 0.05) * 0.05][m_] += 1
for z in sorted(band):
    if z < 0.15 or z > 1.30:
        continue
    tot = sum(band[z].values())
    top = sorted(band[z].items(), key=lambda kv: -kv[1])[:3]
    print("   z=%.2f  n=%-6d %s" % (z, tot, ", ".join("%s(%d)" % (a[:24], b) for a, b in top)))

# ------------------------------------------------ the tailgate
print("\n=== TAILGATE: geometry in the rear-facing plane y>2.30 ===")
for o in meshes:
    vmap = {}
    for p in o.data.polygons:
        m_ = o.material_slots[p.material_index].material.name if o.material_slots else "?"
        for vi in p.vertices:
            vmap[vi] = m_
    pts = defaultdict(list)
    for i, v in enumerate(o.data.vertices):
        w = o.matrix_world @ v.co
        if w.y > 2.30:
            pts[vmap.get(i, "?")].append(w)
    for m_, ps in pts.items():
        print("   %-34s n=%-6d y %.3f..%.3f  z %.3f..%.3f  x %.3f..%.3f" % (
            m_[:34], len(ps), min(p.y for p in ps), max(p.y for p in ps),
            min(p.z for p in ps), max(p.z for p in ps),
            min(p.x for p in ps), max(p.x for p in ps)))

# ------------------------------------------------ the front badge
print("\n=== FRONT: vertices with y < -2.36 (the nose face), by material ===")
for o in meshes:
    vmap = {}
    for p in o.data.polygons:
        m_ = o.material_slots[p.material_index].material.name if o.material_slots else "?"
        for vi in p.vertices:
            vmap[vi] = m_
    pts = defaultdict(list)
    for i, v in enumerate(o.data.vertices):
        w = o.matrix_world @ v.co
        if w.y < -2.36:
            pts[vmap.get(i, "?")].append(w)
    for m_, ps in pts.items():
        print("   %-34s n=%-6d y %.3f..%.3f  z %.3f..%.3f  x %.3f..%.3f" % (
            m_[:34], len(ps), min(p.y for p in ps), max(p.y for p in ps),
            min(p.z for p in ps), max(p.z for p in ps),
            min(p.x for p in ps), max(p.x for p in ps)))

print("\n=== FRONT: compact clusters in the grille face y<-2.40, z 0.80..1.05 ===")
cl = defaultdict(list)
for o in meshes:
    vmap = {}
    for p in o.data.polygons:
        m_ = o.material_slots[p.material_index].material.name if o.material_slots else "?"
        for vi in p.vertices:
            vmap[vi] = m_
    for i, v in enumerate(o.data.vertices):
        w = o.matrix_world @ v.co
        if w.y < -2.40 and 0.78 < w.z < 1.06 and abs(w.x) < 0.30:
            cl[vmap.get(i, "?")].append(w)
for m_ in sorted(cl, key=lambda k: -len(cl[k])):
    ps = cl[m_]
    print("   %-34s n=%-6d y %.4f..%.4f  z %.4f..%.4f  x %.4f..%.4f" % (
        m_[:34], len(ps), min(p.y for p in ps), max(p.y for p in ps),
        min(p.z for p in ps), max(p.z for p in ps),
        min(p.x for p in ps), max(p.x for p in ps)))

# ------------------------------------------------ small details to look for
print("\n=== DOOR-HANDLE / WIPER / FUEL-FILLER candidates ===")
for want, ylo, yhi, zlo, zhi, xmin in (
        ("door handle (cab flank, mid height)", -1.20, 0.85, 0.95, 1.30, 0.70),
        ("windscreen wiper (cowl band)", -1.15, -0.95, 1.20, 1.35, 0.00),
        ("fuel filler (rear left flank)", 0.30, 1.30, 0.90, 1.20, 0.78)):
    agg = defaultdict(list)
    for o in meshes:
        vmap = {}
        for p in o.data.polygons:
            m_ = o.material_slots[p.material_index].material.name if o.material_slots else "?"
            for vi in p.vertices:
                vmap[vi] = m_
        for i, v in enumerate(o.data.vertices):
            w = o.matrix_world @ v.co
            if ylo < w.y < yhi and zlo < w.z < zhi and abs(w.x) > xmin:
                agg[vmap.get(i, "?")].append(w)
    print("  -- %s --" % want)
    for m_ in sorted(agg, key=lambda k: -len(agg[k]))[:4]:
        ps = agg[m_]
        print("     %-32s n=%-5d y %.2f..%.2f z %.2f..%.2f |x| %.2f..%.2f" % (
            m_[:32], len(ps), min(p.y for p in ps), max(p.y for p in ps),
            min(p.z for p in ps), max(p.z for p in ps),
            min(abs(p.x) for p in ps), max(abs(p.x) for p in ps)))

# ------------------------------------------------ wheel-arch extent on the bed side
print("\n=== rear arch: bottom edge of the bed side panel vs y (2.5cm bands) ===")
bins = defaultdict(list)
for o in meshes:
    if not any('Valencia' in m for m in mats(o)):
        continue
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        if 1.00 < w.y < 2.70 and abs(w.x) > 0.72:
            bins[round(w.y / 0.025) * 0.025].append(w.z)
for y in sorted(bins):
    zs = sorted(bins[y])
    print("   y=%.3f  bottom %.3f  top %.3f  n=%d" % (y, zs[0], zs[-1], len(zs)))

print("\nPROBE2 DONE")
