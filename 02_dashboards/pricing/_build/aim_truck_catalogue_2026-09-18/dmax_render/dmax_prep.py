"""Shared prep for the D-Max render: import, find the axles, scale, measure.

WHY THIS REPLACES THE OLD SCALING
---------------------------------
The previous build found the two axles by taking the single biggest gap in the
sorted y values of the rim cloud and averaging each side.  That is wrong on this
model, because it also carries wheel-material geometry BEHIND the rear axle (rim,
rim2 and tyre materials all appear around y = 172..192 units, at wheel height, at
the flanks).  The average of everything above that split is dragged rearward, so
the wheelbase came out at 130.1 units instead of 122.1, and because the wheelbase
sets the scale, EVERY metre in the render and in the QA tables came out 6.6% too
small.  That is the real reason the tail looked 15-19% short; the geometry was
never the problem.

The axles are now read from the BRAKE ROTOR discs, which exist only on road
wheels, and cross-checked against the free tyre diameter (265/65 R17 = 0.7766 m),
which is a second, independent measurement of metres per unit.

Run stand-alone:
    blender --background --python dmax_prep.py
"""
from __future__ import annotations

import json
import os

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
GLB_DEFAULT = os.path.join(HERE, "_assets", "dmax_2021_objaverse.glb")

REAL_WHEELBASE = 3.125          # Isuzu published, double cab
REAL_TYRE_DIA = 0.7766          # 265/65 R17 free diameter

SPEC = {
    "length_m": 5.265, "width_m": 1.870, "height_m": 1.785,
    "wheelbase_m": 3.125, "front_overhang_m": 0.905, "rear_overhang_m": 1.235,
    "track_m": 1.570, "loadbox_length_m": 1.495, "loadbox_width_m": 1.530,
    "loadbox_depth_m": 0.490, "ground_clearance_m": 0.227, "tyre_radius_m": 0.382,
}

ZONE_NAMES = ["front", "engine", "cab", "rear", "chassis", "elec"]


# --------------------------------------------------------------------------- #
# import
# --------------------------------------------------------------------------- #
def mats(o):
    return [s.material.name for s in o.material_slots if s.material]


def import_model(glb: str = GLB_DEFAULT):
    """Factory-reset, import the GLB, unparent, drop non-mesh objects."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.polygons) > 0]
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    for o in list(bpy.data.objects):
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    return meshes


def verts_of(meshes, want, step_target=40000):
    """World-space vertices of every mesh using a material whose name contains `want`."""
    out = []
    for o in meshes:
        if not any(want in m for m in mats(o)):
            continue
        vs = o.data.vertices
        step = max(1, len(vs) // step_target)
        for i in range(0, len(vs), step):
            out.append(o.matrix_world @ vs[i].co)
    return out


def world_bbox(meshes):
    mn = Vector((1e18,) * 3)
    mx = Vector((-1e18,) * 3)
    for o in meshes:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])
    return mn, mx


def _runs(sorted_vals, gap_min, min_len=20):
    if not sorted_vals:
        return []
    out, cur = [], [sorted_vals[0]]
    for v in sorted_vals[1:]:
        if v - cur[-1] > gap_min:
            out.append(cur); cur = [v]
        else:
            cur.append(v)
    out.append(cur)
    return [(min(r), max(r), len(r)) for r in out if len(r) >= min_len]


# --------------------------------------------------------------------------- #
# axles, scale
# --------------------------------------------------------------------------- #
def find_axles(meshes):
    """(front_y, rear_y, method) in raw model units."""
    tyres = sorted(p.y for p in verts_of(meshes, '_Tires'))
    span = (tyres[-1] - tyres[0]) if tyres else 0.0
    gap = span * 0.25

    for want, label in (('BrakeRotors', "brake rotors"), ('_Tires', "tyre discs")):
        discs = _runs(sorted(p.y for p in verts_of(meshes, want)), gap)
        if len(discs) >= 2:
            discs.sort(key=lambda d: -d[2])
            two = sorted(discs[:2], key=lambda d: d[0])
            return ((two[0][0] + two[0][1]) / 2.0,
                    (two[1][0] + two[1][1]) / 2.0, label)
    raise RuntimeError("could not find two axle discs")


def front_tyre_diameter_units(meshes):
    """Outer diameter of the front tyre, in raw units."""
    ys = sorted(p.y for p in verts_of(meshes, '_Tires', step_target=30000))
    if not ys:
        return None
    runs = _runs(ys, (ys[-1] - ys[0]) * 0.05, min_len=5)
    runs.sort(key=lambda r: -r[2])
    two = sorted(runs[:2], key=lambda r: r[0])
    return (two[0][1] - two[0][0]) if len(two) == 2 else None


def scale_to_metres(meshes, verbose=True):
    """Scale so the wheelbase is exactly REAL_WHEELBASE, ground at z=0."""
    mn0, mx0 = world_bbox(meshes)
    pivot_x = (mn0.x + mx0.x) / 2.0
    pivot_y = (mn0.y + mx0.y) / 2.0

    fy, ry, method = find_axles(meshes)
    wb_units = abs(ry - fy)
    S = REAL_WHEELBASE / wb_units

    dia_u = front_tyre_diameter_units(meshes)
    S_tyre = (REAL_TYRE_DIA / dia_u) if dia_u else None

    M = Matrix.Translation((-pivot_x * S, -pivot_y * S, 0.0)) @ Matrix.Scale(S, 4)
    for o in meshes:
        o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()

    mn, mx = world_bbox(meshes)
    drop = Matrix.Translation((0.0, 0.0, -mn.z))
    for o in meshes:
        o.matrix_world = drop @ o.matrix_world
    bpy.context.view_layer.update()
    mn, mx = world_bbox(meshes)
    size = mx - mn

    info = {
        "scale_m_per_unit": S,
        "axle_find_method": method,
        "units_wheelbase": wb_units,
        "front_axle_y": (fy - pivot_y) * S,
        "rear_axle_y": (ry - pivot_y) * S,
        "tyre_diameter_units": dia_u,
        "scale_from_tyre_diameter": S_tyre,
        "scale_methods_agree_pct": (100.0 * (S_tyre / S - 1.0)) if S_tyre else None,
        "model_size_m": {"length": size.y, "width_incl_mirrors": size.x, "height": size.z},
        "nose_y": mn.y, "tail_y": mx.y,
    }
    if verbose:
        print("axles from %s: front %.3f  rear %.3f  -> wheelbase %.3f units"
              % (method, fy, ry, wb_units))
        print("scale (wheelbase) 1 unit = %.6f m" % S)
        if S_tyre:
            print("scale (tyre dia)  1 unit = %.6f m   (agree %+.2f%%)"
                  % (S_tyre, info["scale_methods_agree_pct"]))
        print("model: L=%.3f  H=%.3f m   (spec 5.265 / 1.785 -> %+.1f%% / %+.1f%%)"
              % (size.y, size.z, 100 * (size.y / 5.265 - 1), 100 * (size.z / 1.785 - 1)))
    return info, mn, mx


# --------------------------------------------------------------------------- #
# world-space ray casting
# --------------------------------------------------------------------------- #
def build_bvh(meshes, verbose=True):
    """One world-space BVH over every triangle, plus a triangle->material map."""
    if verbose:
        print("building world BVH ...")
    verts, tris, names = [], [], []
    for o in meshes:
        mw = o.matrix_world
        base = len(verts)
        for v in o.data.vertices:
            verts.append(mw @ v.co)
        slots = [s.material.name if s.material else "?" for s in o.material_slots]
        for p in o.data.polygons:
            vi = [base + i for i in p.vertices]
            nm = slots[p.material_index] if slots else "?"
            for k in range(1, len(vi) - 1):
                tris.append((vi[0], vi[k], vi[k + 1]))
                names.append(nm)
    bvh = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)
    if verbose:
        print("  BVH: %d verts, %d triangles" % (len(verts), len(tris)))
    return bvh, names


def make_caster(bvh, names):
    """caster(origin, direction) -> (point, distance, material) or (None, None, None)."""
    def cast(origin, direction):
        loc, nor, idx, dist = bvh.ray_cast(Vector(origin), Vector(direction), 60.0)
        if loc is None:
            return None, None, None
        return loc, dist, names[idx]
    return cast


def drop_z(cast, x, y, z_from=2.4):
    """First downward hit at (x, y)."""
    loc, _, nm = cast((x, y, z_from), (0, 0, -1))
    return (loc.z, nm) if loc else (None, None)


def flank_x(cast, y, z, from_x=3.0):
    """First hit walking inboard from x=+3, i.e. the outboard surface at (y, z)."""
    loc, _, nm = cast((from_x, y, z), (-1, 0, 0))
    return (loc.x, nm) if loc else (None, None)


# --------------------------------------------------------------------------- #
# the load box, measured off the geometry
# --------------------------------------------------------------------------- #
def measure_box(meshes, info, cast, verbose=True):
    """Bed floor, rail, bulkhead and tailgate, all by ray casting.

    The load box is measured as a physical volume: the floor is the surface a
    down-ray meets inside the box, the rail is the top of the flank just inboard
    of the wall, and the inner length runs from the bulkhead face to the tailgate
    face, found as the two points where a centreline down-ray leaves the floor.
    """
    ra = info["rear_axle_y"]
    tail = info["tail_y"]

    # ---- floor and rail over the box region
    floor_z, rail_z, rear_top_z = [], [], []
    y = ra - 0.20
    while y <= tail - 0.20:
        zc, _ = drop_z(cast, 0.0, y)
        if zc is not None:
            floor_z.append(zc)
        for xs in (-0.76, 0.76):
            zs, nm = drop_z(cast, xs, y)
            if zs is not None:
                rail_z.append(zs)
        y += 0.02

    def median(v):
        if not v:
            return None
        v = sorted(v)
        return v[len(v) // 2]

    floor = median(floor_z)
    rail = median(rail_z)

    # ---- inner length: scan the centreline and find the floor run
    scan = []
    y = info["rear_axle_y"] - 0.60
    while y <= tail + 0.02:
        zc, nm = drop_z(cast, 0.0, y)
        scan.append((y, zc, nm))
        y += 0.01

    inner_front = inner_rear = None
    if floor is not None:
        on_floor = [s for s in scan if s[1] is not None and abs(s[1] - floor) < 0.06]
        if on_floor:
            inner_front = min(s[0] for s in on_floor)
            inner_rear = max(s[0] for s in on_floor)

    # ---- the tailgate top and the front wall top
    gate_z = None
    for y in (tail - 0.30, tail - 0.26, tail - 0.22, tail - 0.18, tail - 0.14):
        zc, nm = drop_z(cast, 0.0, y)
        if zc is not None and (floor is None or zc > floor + 0.10):
            gate_z = zc if gate_z is None else max(gate_z, zc)

    # ---- inner width: the bed floor is one flat surface spanning the box, so the
    #      floor's own x extent is the inner width.  (Casting in from outside the
    #      vehicle would only find the outer body panels, which is a different
    #      measurement - the model's bed sides are inset from the flank.)
    inner_w = None
    if floor is not None:
        half = 0.0
        for o in meshes:
            if not any(('BlackT' in m or 'UnderCarrier' in m) for m in mats(o)):
                continue
            mw = o.matrix_world
            slots = [s.material.name if s.material else "?" for s in o.material_slots]
            for p in o.data.polygons:
                n = (mw.to_3x3() @ p.normal).normalized()
                if abs(n.z) < 0.90:
                    continue
                c = mw @ p.center
                if abs(c.z - floor) > 0.05:
                    continue
                if not (info["rear_axle_y"] - 0.20 < c.y < tail - 0.15):
                    continue
                for vi in p.vertices:
                    half = max(half, abs((mw @ o.data.vertices[vi].co).x))
        if half > 0.1:
            inner_w = half * 2.0

    out = {
        "floor_z": floor,
        "rail_z": rail,
        "tailgate_top_z": gate_z,
        "box_inner_front_y": inner_front,
        "box_inner_rear_y": inner_rear,
        "box_inner_width_m": inner_w,
    }
    if inner_front is not None and inner_rear is not None:
        out["box_inner_length_m"] = inner_rear - inner_front
    if floor is not None and rail is not None:
        out["box_depth_m"] = rail - floor

    if verbose:
        print("load box (ray cast):")
        if floor is not None and rail is not None:
            print("   floor z        %.3f" % floor)
        if rail is not None:
            print("   rail  z        %.3f   -> depth %.3f m (spec %.3f)"
                  % (rail, (rail - floor) if floor else float('nan'), SPEC["loadbox_depth_m"]))
        if inner_w is not None:
            print("   inner width    %.3f m (spec %.3f)" % (inner_w, SPEC["loadbox_width_m"]))
        if inner_front is not None:
            print("   inner length   %.3f .. %.3f = %.3f m (spec %.3f)"
                  % (inner_front, inner_rear, inner_rear - inner_front,
                     SPEC["loadbox_length_m"]))
        if gate_z is not None:
            print("   tailgate top z %.3f" % gate_z)
    return out


def measure_front(meshes, info, cast, verbose=True):
    """Grille band, badge position, nose face - all from the geometry."""
    nose = info["nose_y"]
    # the nose face: walk forward from inside and record the last outboard hit
    grille_z = []
    for z in [0.70 + 0.01 * i for i in range(45)]:
        loc, _, nm = cast((0.0, nose + 0.30, z), (0, -1, 0))
        if loc is not None and 'Grille' in (nm or ""):
            grille_z.append(z)
    # highest forward-most point of the grille material
    badge_y = None
    for z in (0.86, 0.90, 0.94):
        loc, _, nm = cast((0.0, nose + 0.40, z), (0, -1, 0))
        if loc is not None:
            badge_y = loc.y if badge_y is None else min(badge_y, loc.y)
    out = {
        "grille_z_range": [min(grille_z), max(grille_z)] if grille_z else None,
        "nose_face_y": badge_y,
    }
    if verbose:
        print("front: grille z %s  nose face y %s"
              % (out["grille_z_range"], out["nose_face_y"]))
    return out


# --------------------------------------------------------------------------- #
# stand-alone
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    ms = import_model()
    info, mn, mx = scale_to_metres(ms)
    cast = make_caster(*build_bvh(ms))
    box = measure_box(ms, info, cast)
    front = measure_front(ms, info, cast)
    print("\n--- summary ---")
    print(json.dumps(info, indent=1))
    print(json.dumps(box, indent=1))
    print(json.dumps(front, indent=1))
    print("PREP DONE")
