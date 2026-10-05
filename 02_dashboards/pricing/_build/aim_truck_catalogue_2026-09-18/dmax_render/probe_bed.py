"""Probe the D-Max bed / tail geometry so the tail fix can be targeted.

Answers, in the scaled metre frame used by build_dmax_render.py:
  * where the bed floor really is (z histogram inside the box)
  * where the bed rail is, and its front/back extent
  * where the rear wheel arch cutout is (min z of the bed side vs y)
  * how tall the tail lamp cluster is and where it sits
  * what the front chrome piece (candidate badge) looks like
  * where the number-plate surfaces are

Run: blender --background --python probe_bed.py
"""
import bpy
import json
import os
import statistics
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

# gather vertices per material with material-name resolution through polygons
vmat = {}
for o in meshes:
    vmap = {}
    for p in o.data.polygons:
        nm = None
        if o.material_slots:
            try:
                nm = o.material_slots[p.material_index].material.name
            except Exception:
                nm = None
        for vi in p.vertices:
            vmap[vi] = nm
    vs = o.data.vertices
    for i, v in enumerate(vs):
        nm = vmap.get(i)
        if nm:
            vmat.setdefault(nm, []).append(o.matrix_world @ v.co)

def span(pts):
    if not pts:
        return None
    return (min(p.y for p in pts), max(p.y for p in pts),
            min(p.z for p in pts), max(p.z for p in pts),
            min(p.x for p in pts), max(p.x for p in pts))

print("\n=== BED FLOOR: z histogram of interior points behind the cab ===")
# cab back is where the paint profile drops; measure it here directly:
# take the Valencia top profile
val = vmat.get('2021_Isuzu_Dmax_Valencia_Orange', [])
NB = 260
y0, y1 = -2.54, 2.54
bins = [[] for _ in range(NB)]
for p in val:
    k = max(0, min(NB - 1, int((p.y - y0) / (y1 - y0) * (NB - 1))))
    bins[k].append(p.z)
top = [(y0 + (k + .5) * (y1 - y0) / NB, max(bins[k]) if bins[k] else None)
       for k in range(NB)]
print("y, valencia top z (every 6th):")
for k in range(0, NB, 6):
    print("  %7.3f  %s" % (top[k][0], ("%.3f" % top[k][1]) if top[k][1] is not None else "-"))

print("\n=== interior z histogram, y in [1.05, 2.20] (inside the box) ===")
inner = []
for nm, pts in vmat.items():
    for p in pts:
        if 1.05 < p.y < 2.20 and abs(p.x) < 0.42 and p.z > 0.20:
            inner.append((p.z, nm))
inner.sort()
zs = [z for z, _ in inner]
print("count %d  z range %.3f .. %.3f" % (len(zs), zs[0], zs[-1]))
# histogram in 5 cm buckets, with the dominant material named
from collections import defaultdict
buck = defaultdict(list)
for z, nm in inner:
    buck[round(z / 0.05) * 0.05].append(nm)
for z in sorted(buck)[-26:]:
    names = defaultdict(int)
    for nm in buck[z]:
        names[nm] += 1
    top3 = sorted(names.items(), key=lambda kv: -kv[1])[:2]
    print("   z=%.2f  n=%-6d %s" % (z, len(buck[z]), ", ".join("%s(%d)" % (a[:22], b) for a, b in top3)))

print("\n=== BED SIDE: min z of white paint vs y (shows the wheel arch cutout) ===")
NB2 = 150
yb0, yb1 = 0.85, 2.55
b2 = [[] for _ in range(NB2)]
for p in val:
    if yb0 <= p.y <= yb1 and abs(p.x) > 0.70:
        k = max(0, min(NB2 - 1, int((p.y - yb0) / (yb1 - yb0) * (NB2 - 1))))
        b2[k].append(p.z)
for k in range(NB2):
    if b2[k]:
        print("  y %6.3f  flank z %6.3f .. %6.3f   n %d" % (
            yb0 + (k + .5) * (yb1 - yb0) / NB2, min(b2[k]), max(b2[k]), len(b2[k])))

print("\n=== TAIL LAMP ===")
for nm in ('2021_Isuzu_Dmax_BrakeLightsGlass', '2021_Isuzu_Dmax_BrakeLightsBase',
           '2021_Isuzu_Dmax_BrakeLightsBase1', '2021_Isuzu_Dmax_BrakeLights1'):
    pts = [p for p in vmat.get(nm, []) if p.y > 1.9]
    print("  %-36s %s" % (nm, span(pts)))

print("\n=== FRONT CHROME / GRILLE / BADGE ===")
for nm in ('2021_Isuzu_Dmax_ChromeTrims', '2021_Isuzu_Dmax_Grille1', '2021_Isuzu_Dmax_Grille2',
           'material', '2021_Isuzu_Dmax_Default_Material'):
    pts = vmat.get(nm, [])
    if nm == '2021_Isuzu_Dmax_ChromeTrims':
        pts = [p for p in pts if p.y < -2.30]
    print("  %-36s n=%-6d %s" % (nm, len(pts), span(pts)))

print("\n  front chrome z bands (x-width per 3 cm z slice, y<-2.30):")
fr = [p for p in vmat.get('2021_Isuzu_Dmax_ChromeTrims', []) if p.y < -2.30]
zb = defaultdict(list)
for p in fr:
    zb[round(p.z / 0.03) * 0.03].append(p.x)
for z in sorted(zb):
    xs = zb[z]
    print("     z=%.2f  n=%-5d x %.3f .. %.3f" % (z, len(xs), min(xs), max(xs)))

print("\n=== NUMBER PLATES ('material') ===")
pts = vmat.get('material', [])
front = [p for p in pts if p.y < 0]
rear = [p for p in pts if p.y > 0]
print("  front plate  n=%d %s" % (len(front), span(front)))
print("  rear  plate  n=%d %s" % (len(rear), span(rear)))

print("\n=== THINGS THAT MAY OR MAY NOT EXIST ===")
for nm in sorted(vmat):
    print("  %-40s n=%d" % (nm, len(vmat[nm])))

with open(os.path.join(HERE, "_raw", "probe_bed.json"), "w") as f:
    json.dump({"scale": S, "front_axle_y": FA_Y, "rear_axle_y": RA_Y,
               "valencia_top": [[round(a, 4), (round(b, 4) if b else None)] for a, b in top]},
              f, indent=1)
print("\nPROBE DONE")
