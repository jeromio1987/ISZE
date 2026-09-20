"""Find the two axles definitively.

build_dmax_render.py has always found the axles by taking the biggest gap in the
sorted y values of the 'Rims1' mesh and splitting there.  If the model also
carries a SPARE wheel rim (which the earlier probes suggest: Rims1 reaches y=2.08
while a rim cluster should be about 0.38 m wide), that split is wrong, and every
metre in the whole render is then scaled by the wrong factor.

This clusters the rim and tyre geometry properly and reports each wheel centre,
the true wheelbase, and whether a spare exists.

Run: blender --background --python probe_axle.py
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

# work in RAW units here - no scaling yet, that is what we are testing
mn = Vector((1e18,) * 3); mx = Vector((-1e18,) * 3)
for o in meshes:
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], p[i]); mx[i] = max(mx[i], p[i])
print("raw bbox  x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f" % (
    mn.x, mx.x, mn.y, mx.y, mn.z, mx.z))
print("raw length %.3f units, width %.3f, height %.3f" % (
    mx.y - mn.y, mx.x - mn.x, mx.z - mn.z))

for want in ('Rims1', 'Rims2', '_Tires', 'BrakeRotors', 'Calipers'):
    pts = []
    for o in meshes:
        if not any(want in m for m in mats(o)):
            continue
        for v in o.data.vertices:
            pts.append(o.matrix_world @ v.co)
    if not pts:
        continue
    print("\n=== %s : %d verts, y %.3f..%.3f ===" % (want, len(pts),
                                                     min(p.y for p in pts), max(p.y for p in pts)))
    # y histogram in 0.05 unit buckets is too coarse for 0.024 m units; use 2 units
    h = defaultdict(int)
    for p in pts:
        h[int(p.y / 2.0) * 2] += 1
    ks = sorted(h)
    dense = [(k, h[k]) for k in ks if h[k] > 0]
    print("   y histogram (2-unit buckets, only non-empty):")
    line = []
    for k, n in dense:
        line.append("%d:%d" % (k, n))
        if len(line) == 12:
            print("     " + "  ".join(line)); line = []
    if line:
        print("     " + "  ".join(line))

# ---------------------------------------------------------------- tyre clusters
print("\n=== TIRE vertex clusters by y (1-unit buckets), with x and z spread ===")
pts = []
for o in meshes:
    if not any(m.endswith('_Tires') for m in mats(o)):
        continue
    for v in o.data.vertices:
        pts.append(o.matrix_world @ v.co)
buckets = defaultdict(list)
for p in pts:
    buckets[int(p.y / 4.0) * 4].append(p)
for k in sorted(buckets):
    ps = buckets[k]
    xs = [abs(p.x) for p in ps]
    print("   y %5d..%5d  n=%-6d  |x| %.2f..%.2f   z %.3f..%.3f" % (
        k, k + 4, len(ps), min(xs), max(xs),
        min(p.z for p in ps), max(p.z for p in ps)))

print("\n=== RIMS1 clusters by y (2-unit buckets) ===")
pts = []
for o in meshes:
    if not any('Rims1' in m for m in mats(o)):
        continue
    for v in o.data.vertices:
        pts.append(o.matrix_world @ v.co)
buckets = defaultdict(list)
for p in pts:
    buckets[int(p.y / 2.0) * 2].append(p)
run = []
prev = None
for k in sorted(buckets):
    ps = buckets[k]
    xs = [abs(p.x) for p in ps]
    print("   y %5d..%5d  n=%-6d  |x| %.2f..%.2f  z %.3f..%.3f" % (
        k, k + 2, len(ps), min(xs), max(xs),
        min(p.z for p in ps), max(p.z for p in ps)))

# --------------------------------------------- proper clustering of a circular wheel
print("\n=== proper wheel clustering: rim vertices grouped by (y,z) proximity ===")
rim_pts = []
for o in meshes:
    if not any('Rims1' in m for m in mats(o)):
        continue
    for v in o.data.vertices:
        rim_pts.append(o.matrix_world @ v.co)


def cluster(pts, ytol, ztol):
    """Single-link clustering on (y,z) with generous tolerances."""
    groups = []
    for p in sorted(pts, key=lambda q: q.y):
        for g in groups:
            if abs(p.y - g["ys"][-1]) <= ytol and g["zlo"] - ztol <= p.z <= g["zhi"] + ztol:
                g["ys"].append(p.y)
                g["zlo"] = min(g["zlo"], p.z); g["zhi"] = max(g["zhi"], p.z)
                g["pts"].append(p)
                break
        else:
            groups.append({"ys": [p.y], "zlo": p.z, "zhi": p.z, "pts": [p]})
    return groups


# sort/gap split on y is enough because rims are far apart in y
ys = sorted(p.y for p in rim_pts)
gaps = []
for i in range(len(ys) - 1):
    gaps.append((ys[i + 1] - ys[i], ys[i], ys[i + 1]))
gaps.sort(reverse=True)
print("   the 6 largest y gaps in the rim cloud:")
for g, a, b in gaps[:6]:
    print("      gap %.3f units  between y %.3f and %.3f" % (g, a, b))

# cluster by any gap greater than 3 units
cuts = sorted([a for g, a, b in gaps if g > 3.0])
print("   cut points (gaps > 3 units): %s" % ["%.2f" % c for c in cuts])
groups = []
cur = [ys[0]]
for i in range(len(ys) - 1):
    if ys[i + 1] - ys[i] > 3.0:
        groups.append(cur); cur = [ys[i + 1]]
    else:
        cur.append(ys[i + 1])
groups.append(cur)

# now, per y-cluster, split by x sign so a full-wheel cluster reports both sides
print("\n   rim y-clusters and their centres:")
centres = []
for g in groups:
    if len(g) < 50:
        continue
    lo, hi = min(g), max(g)
    sub = [p for p in rim_pts if lo <= p.y <= hi]
    # per-side centre
    leftc = [p.y for p in sub if p.x < -0.05]
    rightc = [p.y for p in sub if p.x > 0.05]
    mid = [p for p in sub if abs(p.x) <= 0.05]
    zc = sum(p.z for p in sub) / len(sub)
    print("      y %.2f..%.2f  n=%-6d  centre y %.3f   z centre %.3f   (|x|<0.05: %d verts)"
          % (lo, hi, len(sub), (lo + hi) / 2.0, zc, len(mid)))
    if leftc:
        print("          left side centre y %.3f (n=%d)   right side centre y %.3f (n=%d)"
              % (sum(leftc) / len(leftc), len(leftc),
                 (sum(rightc) / len(rightc)) if rightc else float("nan"), len(rightc)))
    centres.append(((lo + hi) / 2.0, zc, len(sub)))

if len(centres) >= 2:
    centres.sort()
    print("\n   >>> %d rim clusters found" % len(centres))
    # the two big ones closest to the ends are the road wheels
    big = sorted(centres, key=lambda c: -c[2])[:2]
    big.sort()
    wb = big[1][0] - big[0][0]
    print("   >>> two largest clusters: y %.3f and y %.3f" % (big[0][0], big[1][0]))
    print("   >>> WHEELBASE from rim clusters = %.3f units" % wb)
    print("   >>> scale to 3.125 m would be %.6f m/unit" % (REAL_WB / wb))
    print("   (the old code's split gave 130.116 units, scale 0.024017)")
    print("   >>> would change the scale by %.2f%%" % (
        100.0 * ((REAL_WB / wb) / 0.024016970978185472 - 1.0)))

print("\nAXLE PROBE DONE")
