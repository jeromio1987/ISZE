"""Locate both wheel arches on the flank precisely.

The bed side panel is body paint; the arch is a cut-out in it through which the
dark tyre is visible.  So the arch is where the paint's LOWER edge on the flank
rises.  Doing this in 1 cm bands for both axles gives the arch centre and its
opening, and the front axle is the control: the method is right only if the front
arch lands on the front axle.

Run: blender --background --python probe_arch.py
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
print("FA %.4f   RA %.4f" % (FA_Y, RA_Y))

# tyre and rim centres exactly, per axle side
tyre = []
for o in meshes:
    if any(m.endswith('_Tires') for m in mats(o)):
        for i, v in enumerate(o.data.vertices):
            if i % max(1, len(o.data.vertices) // 6000) == 0:
                tyre.append(o.matrix_world @ v.co)
for name, y0, y1 in (("front", FA_Y - 0.6, FA_Y + 0.6), ("rear", RA_Y - 0.6, RA_Y + 0.6)):
    pts = [p for p in tyre if y0 < p.y < y1]
    if pts:
        print("%s tyre: y %.3f..%.3f (centre %.3f)  z %.3f..%.3f (centre %.3f)  |x| %.3f..%.3f" % (
            name, min(p.y for p in pts), max(p.y for p in pts),
            (min(p.y for p in pts) + max(p.y for p in pts)) / 2,
            min(p.z for p in pts), max(p.z for p in pts),
            (min(p.z for p in pts) + max(p.z for p in pts)) / 2,
            min(abs(p.x) for p in pts), max(abs(p.x) for p in pts)))

# ---- flank paint lower edge, 1 cm bands
print("\n=== paint lower edge on the outer flank, 1 cm bands ===")
STEP = 0.01
bins = defaultdict(list)
for o in meshes:
    if not any('Valencia' in m for m in mats(o)):
        continue
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        if abs(w.x) > 0.74:
            bins[int(w.y / STEP)].append(w.z)
lo_edge = {}
for k in sorted(bins):
    zs = sorted(bins[k])
    lo_edge[k] = zs[0]
for k in sorted(lo_edge):
    y = k * STEP
    if -2.10 < y < 2.60:
        print("  y %6.3f  lower paint edge %6.3f" % (y, lo_edge[k]))

# ---- arch detection: the run of columns where the lower edge is lifted
def arch(ylo, yhi, label):
    ks = [k for k in sorted(lo_edge) if ylo <= k * STEP <= yhi]
    if not ks:
        print("%s: no data" % label)
        return
    base = min(lo_edge[k] for k in ks)
    # "lifted" = at least 10 cm above the local floor of the panel
    lifted = [k for k in ks if lo_edge[k] > base + 0.10]
    if not lifted:
        print("%s: no arch found (base %.3f)" % (label, base))
        return
    # take the longest contiguous run
    runs, cur = [], [lifted[0]]
    for k in lifted[1:]:
        if k == cur[-1] + 1:
            cur.append(k)
        else:
            runs.append(cur); cur = [k]
    runs.append(cur)
    best = max(runs, key=len)
    y_a, y_b = best[0] * STEP, best[-1] * STEP
    apexk = max(best, key=lambda k: lo_edge[k])
    print("%s: opening y %.3f .. %.3f  (width %.3f, centre %.3f)  apex y %.3f at z %.3f" % (
        label, y_a, y_b, y_b - y_a, (y_a + y_b) / 2, apexk * STEP, lo_edge[apexk]))
    return y_a, y_b, (y_a + y_b) / 2

print()
fa = arch(-2.15, -0.90, "FRONT arch")
ra = arch(0.85, 2.10, "REAR  arch")
if fa:
    print("  front arch centre vs front axle: %+.3f m" % (fa[2] - FA_Y))
if ra:
    print("  rear  arch centre vs rear  axle: %+.3f m" % (ra[2] - RA_Y))

# ---- how much flat bed side exists ahead of and behind the rear arch
if ra:
    print("\n  cab back (paint drop) is at y = 0.881 (from measure_dmax.py)")
    print("  flat bed side ahead of the rear arch:  %.3f m" % (ra[0] - 0.881))
    print("  flat bed side behind the rear arch :  %.3f m" % (2.53 - ra[1]))

print("\nARCH PROBE DONE")
