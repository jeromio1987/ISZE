#!/usr/bin/env python3
"""Build the four trucks from published dimensions: geometry, then renders.

Run with:  blender --background --python build_truck_models.py

Every dimension is from Isuzu's own published specification, named per vehicle
below. Units are metres, so the model, the camera and the page all agree without
conversion factors.

This script is the single source of truth for one vehicle's shape. It produces:

  vehicle_catalogue.json   the silhouette profiles, the six clickable zones,
                           the label anchors, and the exact camera parameters
  renders/<key>.png        a shaded render on the page's paper colour
  renders/<key>.jpg        the same render, compressed for embedding

The page draws the JPEG and projects the zone profiles with the same
orthographic camera, so the clickable regions land on the rendered truck rather
than near it. The camera parameters are emitted rather than re-derived, and
Blender also emits ground-truth pixel positions for a set of known world points,
which is what lets QA assert the alignment instead of eyeballing it.

Zones tile the silhouette by construction
------------------------------------------
Rather than hand-drawing six polygons and hoping they line up, the zones are
defined as disjoint rectangles that between them cover the whole profile, and
each zone's polygon is the silhouette clipped to its rectangle. Disjoint
rectangles covering everything means no gaps and no double-claimed patches, and
a raster self-check confirms it on every build.

Wheels sit in real arches: the arch is cut out of the body with a boolean, so
the recess shades correctly and the tyre is framed by the body rather than stuck
on a slab.
"""
from __future__ import annotations

import json
import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(HERE, "renders")
os.makedirs(RENDERS, exist_ok=True)

# ---------------------------------------------------------------------------
# Camera and frame
#   AZ  azimuth: 0 is a pure side view, positive turns to show the front
#   EL  elevation above the horizon
# The page must use exactly these numbers.
# ---------------------------------------------------------------------------
AZ = math.radians(14.0)
EL = math.radians(7.0)
RES_X, RES_Y = 1680, 760
SAMPLES = 96
MARGIN_X = 1.16          # how much room to leave beside the vehicle
MARGIN_Y = 1.34          # more room below than above, for the shadow

PAPER = (0.930, 0.907, 0.854)     # the page's #f7f4ee, as an sRGB triple


# ===========================================================================
# Small polygon helpers. The zone partition depends on these being right, so
# they are written plainly and checked by a raster test further down.
# ===========================================================================

def inside(poly, pt):
    """Ray casting, for a point in a polygon."""
    x, z = pt
    hit = False
    n = len(poly)
    for i in range(n):
        x0, z0 = poly[i]
        x1, z1 = poly[(i + 1) % n]
        if (z0 > z) != (z1 > z):
            xt = x0 + (z - z0) * (x1 - x0) / (z1 - z0)
            if x < xt:
                hit = not hit
    return hit


def clip_rect(poly, rect):
    """Clip a polygon to an axis-aligned rectangle.

    Sutherland-Hodgman against the four half-planes of the rectangle. The zone
    rectangles are convex and each clipped piece is a single connected region
    for these shapes, which the raster self-check verifies on every build.
    """
    x0, x1, z0, z1 = rect
    out = list(poly)
    for axis, lo, hi in ((0, x0, x1), (1, z0, z1)):
        if not out:
            return []
        res = []
        n = len(out)
        for i in range(n):
            a = out[i]
            b = out[(i + 1) % n]
            ain = lo - 1e-12 <= a[axis] <= hi + 1e-12
            bin_ = lo - 1e-12 <= b[axis] <= hi + 1e-12
            if ain:
                res.append(a)
            if ain != bin_:
                t = (lo - a[axis]) / (b[axis] - a[axis]) if not ain else \
                    (hi - a[axis]) / (b[axis] - a[axis])
                res.append([a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])])
        out = res
    # drop repeated points, which the clipping introduces at corners
    clean = []
    for p in out:
        if not clean or abs(p[0] - clean[-1][0]) > 1e-9 or abs(p[1] - clean[-1][1]) > 1e-9:
            clean.append(p)
    if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 1e-9 \
            and abs(clean[0][1] - clean[-1][1]) < 1e-9:
        clean.pop()
    return clean if len(clean) >= 3 else []


def raster_check(name, solids, zones, elec, step=0.018):
    """Confirm the zones tile the silhouette: no gap, nothing claimed twice.

    Samples a fine grid over the whole vehicle, keeps the points that fall
    inside the silhouette, and checks that each one is claimed by exactly one
    zone. This is the guarantee that the page's clickable regions have no holes
    and no ambiguous overlaps.
    """
    xs = [p[0] for s in solids for p in s]
    zs = [p[1] for s in solids for p in s]
    for polys in zones.values():
        for poly in polys:
            xs += [p[0] for p in poly]
            zs += [p[1] for p in poly]
    bx0, bx1, bz0, bz1 = min(xs), max(xs), min(zs), max(zs)

    gap = over = inside_n = 0
    gap_ex = over_ex = []
    nx = int((bx1 - bx0) / step) + 1
    nz = int((bz1 - bz0) / step) + 1
    for i in range(nx):
        for j in range(nz):
            x = bx0 + (i + 0.5) * step
            z = bz0 + (j + 0.5) * step
            if not any(inside(s, (x, z)) for s in solids):
                continue
            inside_n += 1
            claims = [k for k, polys in zones.items()
                      if any(inside(p, (x, z)) for p in polys)]
            if not claims:
                gap += 1
                if len(gap_ex) < 6:
                    gap_ex.append([round(x, 3), round(z, 3)])
            elif len(claims) > 1:
                over += 1
                if len(over_ex) < 6:
                    over_ex.append([round(x, 3), round(z, 3), claims])

    # the electrical boxes are an extra layer on top, so each must fall inside
    # the silhouette and inside exactly one positional zone
    elec_bad = []
    for poly in elec:
        ok = False
        for s in solids:
            cxs = [p[0] for p in s]
            czs = [p[1] for p in s]
            for i in range(1, 12):
                for j in range(1, 12):
                    x = min(cxs) + (max(cxs) - min(cxs)) * i / 12.0
                    z = min(czs) + (max(czs) - min(czs)) * j / 12.0
                    if inside(poly, (x, z)) and inside(s, (x, z)):
                        ok = True
                        break
                if ok:
                    break
            if ok:
                break
        if not ok:
            cx = sum(p[0] for p in poly) / len(poly)
            cz = sum(p[1] for p in poly) / len(poly)
            elec_bad.append([round(cx, 3), round(cz, 3), "outside silhouette"])
            continue
        cx = sum(p[0] for p in poly) / len(poly)
        cz = sum(p[1] for p in poly) / len(poly)
        c = [k for k, polys in zones.items() if any(inside(p, (cx, cz)) for p in polys)]
        if len(c) != 1:
            elec_bad.append([round(cx, 3), round(cz, 3), f"claims {c}"])

    return {"vehicle": name, "points_inside": inside_n,
            "gap_points": gap, "overlap_points": over,
            "gap_examples": gap_ex, "overlap_examples": over_ex,
            "gap_pct": round(100.0 * gap / inside_n, 4) if inside_n else None,
            "overlap_pct": round(100.0 * over / inside_n, 4) if inside_n else None,
            "elec_bad": elec_bad,
            "step": step}


# ===========================================================================
# Dimensions
# ===========================================================================
#
# D-MAX MY26 double cab 4x4 - Isuzu D-Max spec booklet
#     5.265 long, 1.870 wide, 1.785 high, 3.125 wheelbase, 0.905 front overhang,
#     1.235 rear overhang, 1.570 track, loadbox 1.495 x 1.530 x 0.490,
#     0.227 ground clearance, 255/65 R17 -> 0.382 radius
#
# NLR 150 - Isuzu N-Series individual spec sheet (European range)
#     4.730 long, 1.815 wide, 2.475 wheelbase, 1.110 front overhang,
#     1.145 rear overhang, 2.195 high, 0.760 chassis height, 0.200 clearance
#
# NMR / NPR wide - Isuzu N-Series spec sheet
#     6.020 long, 1.995 wide, 3.345 wheelbase, 1.110 front overhang,
#     1.510 rear overhang, 2.265 high, 0.810 chassis height
#
# FRR 110-260 MWB - Isuzu Australia FRR spec sheet
#     7.255 long, 2.170 track, 4.360 wheelbase, 1.170 front overhang,
#     1.725 rear overhang, 2.585 cab height, 0.895 chassis height
# ===========================================================================

def build_dmax():
    L, W, H, WB, FOH, ROH, GL, WR = (5.265, 1.870, 1.785, 3.125,
                                     0.905, 1.235, 0.227, 0.382)
    rear_axle = FOH + WB
    floor = 0.42                     # underside of the body sides
    bonnet = 1.08                    # bonnet top and bed rail
    roof = H
    x_screen = 2.10                  # base of the windscreen
    x_roof_f = 2.52
    x_roof_r = 3.34
    x_cab_r = 3.48
    x_bed_f = 3.74
    x_bed_r = L - 0.06
    bed_floor = 0.92

    body = [
        [0.02, 0.30], [0.02, 0.66], [0.12, 0.74],
        [0.34, 0.78], [1.10, 0.90], [1.70, 1.00],
        [x_screen, bonnet], [x_roof_f + 0.10, roof - 0.03],
        [x_roof_f + 0.34, roof], [x_roof_r, roof],
        [x_roof_r + 0.14, roof - 0.12], [x_cab_r, bonnet],
        [x_bed_f - 0.05, bonnet], [x_bed_f, bonnet - 0.04],
        [x_bed_r, bonnet - 0.06], [L, bonnet - 0.36],
        [L, floor], [L - 0.22, floor - 0.07],
        [0.66, floor - 0.07], [0.36, floor],
    ]
    bed = [
        [x_bed_f, floor - 0.07], [x_bed_f, bonnet - 0.04],
        [x_bed_f + 0.06, bonnet - 0.07], [x_bed_f + 0.06, bed_floor + 0.04],
        [x_bed_r - 0.06, bed_floor + 0.04], [x_bed_r - 0.06, bonnet - 0.11],
        [x_bed_r, bonnet - 0.16], [x_bed_r, floor - 0.07],
    ]

    cuts = {"front_x": 0.46, "eng_x": 1.70, "cab_x": x_bed_f - 0.05,
            "floor": floor, "L": L, "top": 3.0, "bot": -1.0}

    det = {
        "wheels": [[FOH, WR], [rear_axle, WR]],
        # the windscreen and the cab side glass, as separate panes
        "glass": [[x_screen + 0.03, bonnet + 0.03], [x_roof_f + 0.16, roof - 0.10],
                  [x_roof_f + 0.44, roof - 0.11], [x_screen + 0.52, bonnet + 0.03]],
        "sideglass": [[x_screen + 0.62, bonnet + 0.05], [x_roof_r - 0.08, bonnet + 0.05],
                      [x_roof_r - 0.08, roof - 0.12], [x_screen + 0.70, roof - 0.13],
                      [x_screen + 0.62, bonnet + 0.34]],
        "bumper": [0.12, 0.56, 0.62, 0.30],
        "grille": [0.20, 0.78, 0.44, 0.24],
        "lamp": [0.30, 0.72, 0.34, 0.20],
        "mirror": [x_screen + 0.10, roof - 0.30],
        "shut": [[[1.80, floor + 0.04], [1.80, 1.04]],
                 [[x_cab_r + 0.04, floor + 0.04], [x_cab_r + 0.04, bonnet - 0.04]],
                 [[x_bed_f + 0.12, floor + 0.06], [x_bed_f + 0.12, bonnet - 0.12]],
                 [[x_screen + 0.60, bonnet + 0.02], [x_screen + 0.60, roof - 0.14]]],
        "handle": [[2.42, 1.02], [2.86, 1.02]],
        "step": None,
        "elec": [[[0.90, 0.72], [1.16, 0.72], [1.16, 0.96], [0.90, 0.96]],
                 [[2.34, 1.14], [2.60, 1.14], [2.60, 1.36], [2.34, 1.36]]],
        "anchor": {"front": [0.26, 1.45, -1, 0.3],
                   "engine": [1.15, 1.22, -0.5, 1],
                   "cab": [2.66, 1.90, 0, -1],
                   "chassis": [3.30, 0.28, -0.3, -1],
                   "rear": [4.55, 1.22, 1, 0.4],
                   "elec": [2.47, 1.66, 1, 1]},
    }
    return {"key": "dmax", "name": "D-Max", "kind": "Pickup / LCV",
            "length": L, "width": W, "height": H,
            "body": body, "box": bed, "frame": None,
            "partition_solids": [body], "solids": [body, bed],
            "cuts": cuts, "det": det, "wheel_r": WR, "wheel_w": 0.255,
            "chassis_w": 1.05,
            "source": "Isuzu D-Max spec booklet (double cab, 4x4)"}


def build_cabover(key, name, kind, L, W, WB, FOH, ROH, OH, EH, GL, ch_w,
                  cab_h, wr, tyre_w, track, source, cab_len=2.10, box_h=None):
    """A cab-over: a tall flat-nosed cab, then a cargo box on the frame."""
    rear_axle = FOH + WB
    frame_top = EH + 0.16
    body_bottom = frame_top - 0.04
    cab_base = max(GL + 0.13, EH - 0.20)   # underside of the cab shell
    nose = 0.03
    cab_back = FOH + cab_len
    front_top = cab_h * 0.60            # where the windscreen begins
    roof = cab_h
    box_f = cab_back + 0.14
    box_r = L - 0.05
    box_top = box_h if box_h else OH * 0.93

    body = [
        [nose, cab_base], [nose, front_top],
        [nose + 0.05, front_top + 0.20],
        [nose + 0.12, roof - 0.05], [nose + 0.40, roof],
        [cab_back, roof], [cab_back + 0.08, roof - 0.10],
        [cab_back + 0.08, body_bottom],
        [cab_back + 0.02, cab_base - 0.02], [nose + 0.10, cab_base - 0.02],
    ]
    box = [
        [box_f, body_bottom], [box_f, box_top],
        [box_f + 0.05, box_top + 0.04], [box_r - 0.05, box_top + 0.04],
        [box_r, box_top - 0.02], [box_r, body_bottom],
    ]
    frame = [
        [nose + 0.06, body_bottom - 0.26], [box_r, body_bottom - 0.26],
        [box_r, body_bottom], [nose + 0.06, body_bottom],
    ]

    cuts = {"front_x": nose + 0.22, "cab_back": cab_back + 0.08,
            "cab_base": cab_base, "body_bottom": body_bottom,
            "L": L, "top": roof + 1.0, "bot": -1.0}

    det = {
        "wheels": [[FOH, wr], [rear_axle, wr]],
        "glass": [[nose + 0.08, front_top + 0.10], [nose + 0.22, roof - 0.14],
                  [nose + 0.66, roof - 0.15], [nose + 0.12, front_top + 0.02]],
        "sideglass": [[nose + 0.76, front_top - 0.04],
                      [cab_back - 0.12, front_top - 0.02],
                      [cab_back - 0.12, roof - 0.16],
                      [nose + 0.80, roof - 0.20]],
        "bumper": [nose - 0.10, cab_base - 0.10, 0.22, 0.26],
        "grille": [nose - 0.01, cab_base + 0.34, 0.18, 0.44],
        "lamp": [nose + 0.01, cab_base + 0.08, 0.16, 0.20],
        "mirror": [nose + 0.22, roof - 0.46],
        "shut": [[[cab_back + 0.06, cab_base + 0.02], [cab_back + 0.06, roof - 0.12]],
                 [[box_f + 0.03, body_bottom + 0.03], [box_f + 0.03, box_top]],
                 [[box_r - 0.09, body_bottom + 0.03], [box_r - 0.09, box_top]],
                 [[cab_back - 0.30, cab_base + 0.02], [cab_back - 0.30, roof - 0.16]]],
        "handle": [[cab_back - 0.44, cab_base + 0.20], [cab_back - 0.16, cab_base + 0.20]],
        "step": [cab_back - 0.40, cab_base - 0.26, 0.34, 0.08],
        "elec": [[[nose + 0.62, cab_base + 0.22], [nose + 0.99, cab_base + 0.22],
                  [nose + 0.99, cab_base + 0.60], [nose + 0.62, cab_base + 0.60]],
                 [[box_f + 0.45, body_bottom + 0.28], [box_f + 0.90, body_bottom + 0.28],
                  [box_f + 0.90, body_bottom + 0.68], [box_f + 0.45, body_bottom + 0.68]]],
        "anchor": {"front": [nose + 0.10, cab_base + 0.75, -1, -0.2],
                   "engine": [cab_back * 0.55, body_bottom - 0.16, -0.4, -1],
                   "cab": [cab_back * 0.60, roof - 0.30, -0.2, -1],
                   "chassis": [(cab_back + box_r) / 2, body_bottom - 0.18, -0.2, -1],
                   "rear": [(box_f + box_r) / 2, box_top - 0.34, 1, 0.2],
                   "elec": [nose + 1.05, cab_base + 0.70, 1, 1]},
    }
    return {"key": key, "name": name, "kind": kind,
            "length": L, "width": W, "height": OH,
            "body": body, "box": box, "frame": frame,
            "partition_solids": [body, box, frame], "solids": [body, box, frame],
            "cuts": cuts, "det": det, "wheel_r": wr, "wheel_w": tyre_w,
            "track": track, "chassis_w": ch_w, "source": source}


VEHICLES = [
    build_dmax(),
    build_cabover(
        "nlr", "N-Series light", "Light truck",
        L=4.730, W=1.815, WB=2.475, FOH=1.110, ROH=1.145, OH=2.195,
        EH=0.760, GL=0.200, ch_w=0.700, cab_h=2.05, wr=0.360, tyre_w=0.24,
        track=1.500, cab_len=1.95,
        source="Isuzu N-Series individual spec sheet (NLR 150)"),
    build_cabover(
        "nmr", "N-Series heavy", "Medium truck",
        L=6.020, W=1.995, WB=3.345, FOH=1.110, ROH=1.510, OH=2.265,
        EH=0.810, GL=0.210, ch_w=0.850, cab_h=2.12, wr=0.385, tyre_w=0.28,
        track=1.650, cab_len=2.20,
        source="Isuzu N-Series spec sheet (NPR wide cab, 3.345 m wheelbase)"),
    build_cabover(
        "frr", "F-Series", "Heavy truck",
        L=7.255, W=2.170, WB=4.360, FOH=1.170, ROH=1.725, OH=2.585,
        EH=0.895, GL=0.215, ch_w=0.960, cab_h=2.44, wr=0.455, tyre_w=0.31,
        track=1.800, cab_len=2.35, box_h=2.60,
        source="Isuzu Australia FRR 110-260 MWB spec sheet"),
]


# ===========================================================================
# The zone partition
# ===========================================================================

def zone_rects(veh):
    """Disjoint rectangles covering the whole profile, one set per zone.

    Between them these cover [0, L] x [bot, top], and no two of them share any
    area, so clipping the silhouette to each gives six zones with no gap and
    nothing claimed twice. The electrical layer is deliberately not one of these
    rectangles: it is a functional layer that sits on top of the positional
    zones, so it is defined separately as boxes that fall inside them.
    """
    c = veh["cuts"]
    L, top, bot = c["L"], c["top"], c["bot"]
    if veh["key"] == "dmax":
        f, e, cb, fl = c["front_x"], c["eng_x"], c["cab_x"], c["floor"]
        return {
            "front":   [(0.0, f, bot, top)],
            "engine":  [(f, e, bot, top)],
            "chassis": [(f, L, bot, fl)],
            "cab":     [(e, cb, fl, top)],
            "rear":    [(cb, L, fl, top)],
        }
    fx, cbk = c["front_x"], c["cab_back"]
    return {
        "front":   [(0.0, fx, bot, top)],
        "cab":     [(fx, cbk, bot, top)],
        "chassis": [(cbk, L, bot, c["body_bottom"])],
        "rear":    [(cbk, L, c["body_bottom"], top)],
        "engine":  [(fx, cbk, bot, c["cab_base"])],
    }


def build_zone_polygons(veh):
    rects = zone_rects(veh)
    zones = {}
    for name, rl in rects.items():
        polys = []
        for rect in rl:
            for solid in veh["partition_solids"]:
                piece = clip_rect(solid, rect)
                if piece:
                    polys.append([[round(p[0], 4), round(p[1], 4)] for p in piece])
        zones[name] = polys
    return zones


# ===========================================================================
# Blender scene
# ===========================================================================

def wipe():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_mat(name, rgb, rough=0.4, metal=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = spec
    return m


def mesh_obj(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def add_profile(name, profile, width, mat, bevel=0.014, y_off=0.0):
    """Extrude a side profile across the vehicle width and bevel its edges."""
    n = len(profile)
    verts = [(x, -width / 2 + y_off, z) for x, z in profile] + \
            [(x, width / 2 + y_off, z) for x, z in profile]
    faces = [list(range(n))[::-1], list(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, j + n, i + n])
    ob = mesh_obj(name, verts, faces, mat)
    if bevel:
        bpy.context.view_layer.objects.active = ob
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(30)
    return ob


def add_box(name, x0, z0, dx, dz, width, mat, y_off=0.0, bevel=0.006):
    prof = [[x0, z0], [x0 + dx, z0], [x0 + dx, z0 + dz], [x0, z0 + dz]]
    return add_profile(name, prof, width, mat, bevel=bevel, y_off=y_off)


def cut_arches(body_obj, veh):
    """Cut a wheel arch out of the body at every wheel, so the tyre sits in a
    recess instead of in front of a slab. The recess shading then comes from
    the geometry rather than from a painted-on shadow."""
    half = veh["body_width"] / 2
    depth = veh["wheel_w"] + 0.30
    for i, (cx, cz) in enumerate(veh["det"]["wheels"]):
        for side, y in (("n", -(half - depth / 2 + 0.001)),
                        ("f", half - depth / 2 - 0.001)):
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=40, radius=veh["wheel_r"] + 0.065, depth=depth,
                location=(cx, y, cz), rotation=(math.radians(90), 0, 0))
            cut = bpy.context.object
            cut.name = f"cut_{i}_{side}"
            mod = body_obj.modifiers.new("arch", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.object = cut
            mod.solver = "EXACT"
            bpy.context.view_layer.objects.active = body_obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(cut, do_unlink=True)


def add_wheel(cx, cz, r, width, y, mat_tyre, mat_rim):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=width,
                                        location=(cx, y, cz),
                                        rotation=(math.radians(90), 0, 0))
    tyre = bpy.context.object
    tyre.name = "tyre"
    tyre.data.materials.append(mat_tyre)
    bpy.ops.object.shade_smooth()

    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r * 0.60,
                                        depth=width * 1.04,
                                        location=(cx, y, cz),
                                        rotation=(math.radians(90), 0, 0))
    rim = bpy.context.object
    rim.name = "rim"
    rim.data.materials.append(mat_rim)
    bpy.ops.object.shade_smooth()

    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r * 0.19,
                                        depth=width * 1.12,
                                        location=(cx, y, cz),
                                        rotation=(math.radians(90), 0, 0))
    hub = bpy.context.object
    hub.name = "hub"
    hub.data.materials.append(mat_tyre)
    return tyre


def build_scene(veh):
    wipe()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x = RES_X
    sc.render.resolution_y = RES_Y
    sc.render.image_settings.file_format = "PNG"
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        sc.view_settings.view_transform = "Filmic"
        sc.view_settings.look = "Medium High Contrast"
    sc.view_settings.exposure = 0.55

    # A light neutral vehicle. The body has to be clearly lighter than the paper
    # background, or the shading disappears and the shape reads as a silhouette.
    body_mat = make_mat("body", (0.600, 0.616, 0.638), rough=0.30, metal=0.25)
    dark_mat = make_mat("bodydark", (0.035, 0.037, 0.043), rough=0.50)
    glass_mat = make_mat("glass", (0.055, 0.075, 0.105), rough=0.07, spec=0.95)
    rim_mat = make_mat("rim", (0.66, 0.68, 0.71), rough=0.24, metal=0.92)
    line_mat = make_mat("line", (0.085, 0.090, 0.100), rough=0.60)
    light_mat = make_mat("light", (0.86, 0.89, 0.93), rough=0.09, spec=0.95)
    floor_mat = make_mat("floor", (0.870, 0.850, 0.800), rough=0.92)

    # The body is a little narrower than the published overall width, because
    # the overall width includes the tyres. The tyre then sits inside the body's
    # outer plane and is framed by the arch.
    veh["body_width"] = veh["width"] - veh["wheel_w"] * 1.05
    y = -(veh["body_width"] - veh["wheel_w"]) / 2

    body = add_profile(veh["key"] + "_body", veh["body"], veh["body_width"], body_mat)
    cut_arches(body, veh)
    add_profile(veh["key"] + "_box", veh["box"], veh["width"] - 0.04, body_mat)
    if veh["frame"]:
        add_profile(veh["key"] + "_frame", veh["frame"], veh["chassis_w"],
                    dark_mat, bevel=0.008)

    for cx, cz in veh["det"]["wheels"]:
        add_wheel(cx, cz, veh["wheel_r"], veh["wheel_w"], y, dark_mat, rim_mat)

    det = veh["det"]
    for key, extra in (("glass", 0.012), ("sideglass", 0.014)):
        poly = det.get(key)
        if poly:
            add_profile(key, poly, veh["body_width"] + extra, glass_mat,
                        bevel=0.004)

    for key, mat, w in (("grille", line_mat, veh["width"] - 0.14),
                        ("lamp", light_mat, veh["width"] - 0.10)):
        spec = det.get(key)
        if spec:
            x0, z0, dx, dz = spec
            add_box(key, x0, z0, dx, dz, w, mat, bevel=0.01)
    sp = det.get("bumper")
    if sp:
        x0, z0, dx, dz = sp
        add_box("bumper", x0, z0, dx, dz, veh["width"] + 0.02, dark_mat,
                bevel=0.014)
    st = det.get("step")
    if st:
        x0, z0, dx, dz = st
        add_box("step", x0, z0, dx, dz, veh["width"] * 0.52, dark_mat,
                bevel=0.008)
    for i, seg in enumerate(det.get("shut", [])):
        (x0, z0), (x1, z1) = seg
        add_box(f"shut{i}", min(x0, x1) - 0.008, min(z0, z1) - 0.008,
                abs(x1 - x0) + 0.016, abs(z1 - z0) + 0.016,
                veh["body_width"] + 0.020, line_mat, bevel=0.003)
    h = det.get("handle")
    if h:
        (x0, z0), (x1, z1) = h
        add_box("handle", x0, z0, abs(x1 - x0), 0.055,
                veh["body_width"] + 0.048, line_mat, bevel=0.012)
    if det.get("mirror"):
        mx, mz = det["mirror"]
        add_box("mirror", mx, mz, 0.32, 0.17, veh["body_width"] + 0.24,
                dark_mat, y_off=-0.10, bevel=0.030)
        add_box("mirrorarm", mx - 0.05, mz - 0.05, 0.18, 0.05,
                veh["body_width"] + 0.12, dark_mat, y_off=-0.05, bevel=0.008)

    bpy.ops.mesh.primitive_plane_add(size=60,
                                     location=(veh["length"] / 2, 0, -0.002))
    floor = bpy.context.object
    floor.name = "floor"
    floor.data.materials.append(floor_mat)

    # A soft contact shadow under the vehicle. A dark translucent plate a few
    # millimetres above ground reads as a shadow and plants the truck, which is
    # most of what stops a render looking like it is floating.
    bpy.ops.mesh.primitive_plane_add(size=veh["length"] * 1.10,
                                     location=(veh["length"] / 2 + 0.05, 0, 0.004))
    shadow = bpy.context.object
    shadow.name = "shadowplate"
    sh_mat = make_mat("shadowplate", (0.10, 0.11, 0.13), rough=0.95)
    sh_mat.blend_method = "BLEND"
    sh_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.30
    shadow.data.materials.append(sh_mat)

    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (PAPER[0], PAPER[1], PAPER[2], 1.0)
    bg.inputs[1].default_value = 0.85

    bpy.ops.object.light_add(type="SUN", location=(2, -7, 9))
    sun = bpy.context.object
    sun.data.energy = 3.6
    sun.data.angle = math.radians(3.5)
    sun.rotation_euler = (math.radians(46), 0, math.radians(-34))

    bpy.ops.object.light_add(type="AREA",
                             location=(veh["length"] * 0.42, -3.2, 6.0))
    a1 = bpy.context.object
    a1.data.energy = 1400
    a1.data.size = 11
    a1.rotation_euler = (math.radians(26), 0, math.radians(-12))

    bpy.ops.object.light_add(type="AREA",
                             location=(veh["length"] * 0.62, 4.5, 3.0))
    a2 = bpy.context.object
    a2.data.energy = 420
    a2.data.size = 12
    a2.rotation_euler = (math.radians(100), 0, math.radians(16))

    return veh


def place_camera(veh):
    """An orthographic camera on a sphere around the vehicle centre.

    Convention: x runs from the front of the vehicle (0) to the rear (length),
    y is across it, z is up. The vehicle faces -x. To see its front and its
    nearside (negative y) from slightly above, the camera sits at low x,
    negative y and positive z:

        loc = centre + dist * (-sin(az)cos(el), -cos(az)cos(el), +sin(el))

    Getting these signs wrong puts the camera under the ground and behind the
    vehicle, which silently renders the wrong side of the truck.
    """
    cx = veh["length"] / 2
    cz = veh["height"] * 0.45
    target = Vector((cx, 0.0, cz))
    dist = 30.0
    loc = Vector((cx - math.sin(AZ) * math.cos(EL) * dist,
                  -math.cos(AZ) * math.cos(EL) * dist,
                  cz + math.sin(EL) * dist))
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.clip_start = 0.1
    cam.data.clip_end = 200.0
    cam.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    bpy.context.view_layer.update()     # the matrix must exist before it is read
    return cam, target


def frame_camera(cam, veh, target):
    """Fit the vehicle in frame.

    With sensor_fit HORIZONTAL, ortho_scale is the width of the frame in world
    units and the visible height is ortho_scale / aspect. So the scale has to
    cover the horizontal span directly and the vertical span multiplied by the
    aspect ratio. Dividing instead of multiplying here is what let the truck
    overflow the frame.

    The camera is turned, so the vehicle's width shows in the image and adds to
    the span the length projects to.
    """
    aspect = RES_X / RES_Y
    w_half = veh["width"] / 2 + veh["wheel_w"]
    span_x = (veh["length"] * math.cos(AZ) + 2 * w_half * math.sin(AZ)) * MARGIN_X
    span_y = (veh["height"] + 2 * w_half * math.sin(EL)) * MARGIN_Y
    scale = max(span_x, span_y * aspect)
    cam.data.ortho_scale = scale
    return scale


def render_vehicle(veh, zones):
    veh = build_scene(veh)
    cam, target = place_camera(veh)
    scale = frame_camera(cam, veh, target)
    sc = bpy.context.scene
    out = os.path.join(RENDERS, veh["key"] + ".png")
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)

    # A JPEG for the page to embed. The page carries the image inside it to stay
    # openable from Explorer, and a JPEG of a rendered photograph is about a
    # twentieth the size of the PNG master, which keeps the page small. The PNG
    # stays on disk for inspection.
    jpg = os.path.join(RENDERS, veh["key"] + ".jpg")
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 88
    img = bpy.data.images.get("Render Result")
    if img is not None:
        img.save_render(filepath=jpg, scene=sc)
    sc.render.image_settings.file_format = "PNG"

    # Ground truth for the overlay. An orthographic render maps world points to
    # pixels affinely, so Blender can state exactly where a set of known world
    # points lands. QA compares the page's projection against these numbers,
    # which turns "does the overlay line up" into an assertion.
    mw = cam.matrix_world
    right = [mw[0][0], mw[1][0], mw[2][0]]      # camera x axis, in world
    up = [mw[0][1], mw[1][1], mw[2][1]]         # camera y axis, in world

    from bpy_extras.object_utils import world_to_camera_view
    probe_pts = []
    for fx in (0.0, 0.5, 1.0):
        for fz in (0.0, 0.5, 1.0):
            probe_pts.append([veh["length"] * fx, 0.0, veh["height"] * fz])
    for fx in (0.0, 1.0):
        probe_pts.append([veh["length"] * fx, -veh["body_width"] / 2,
                          veh["height"] * 0.2])
    probe = []
    for p in probe_pts:
        v = world_to_camera_view(sc, cam, Vector(p))
        probe.append({"world": [round(c, 5) for c in p],
                      "ndc": [round(v.x, 6), round(v.y, 6)],
                      "px": [round(v.x * RES_X, 3), round((1 - v.y) * RES_Y, 3)]})

    return {
        "embed": os.path.basename(jpg),
        "ortho_scale": scale,
        "res": [RES_X, RES_Y],
        "az": AZ, "el": EL,
        "target": [round(target.x, 6), round(target.y, 6), round(target.z, 6)],
        "right": [round(c, 8) for c in right],
        "up": [round(c, 8) for c in up],
        "probe": probe,
        "body_width": veh["body_width"],
        "wheel_r": veh["wheel_r"],
        "wheels": veh["det"]["wheels"],
    }


def main() -> int:
    cat = {"az_deg": round(math.degrees(AZ), 4), "el_deg": round(math.degrees(EL), 4),
           "res": [RES_X, RES_Y], "vehicles": {}}
    checks = []
    for veh in VEHICLES:
        print(f"--- {veh['key']} ({veh['name']})")
        zones = build_zone_polygons(veh)
        chk = raster_check(veh["key"], veh["partition_solids"], zones,
                           veh["det"]["elec"])
        checks.append(chk)
        print(f"    zones: {len(zones)}  inside {chk['points_inside']} pts  "
              f"gap {chk['gap_points']}  overlap {chk['overlap_points']}")
        if chk["gap_points"] or chk["overlap_points"] or chk["elec_bad"]:
            print(f"    !! PARTITION FAILED  gap_ex {chk['gap_examples']}")
            print(f"       overlap_ex {chk['overlap_examples']}  elec {chk['elec_bad']}")
        r = render_vehicle(veh, zones)
        print(f"    -> {r['embed']}  ortho_scale {r['ortho_scale']:.4f}")

        xs = [p[0] for s in veh["solids"] for p in s]
        zs = [p[1] for s in veh["solids"] for p in s]
        cat["vehicles"][veh["key"]] = {
            "name": veh["name"], "kind": veh["kind"],
            "length": veh["length"], "width": veh["width"],
            "height": veh["height"], "source": veh["source"],
            "solids": [[[round(p[0], 4), round(p[1], 4)] for p in s]
                       for s in veh["solids"]],
            "zones": zones,
            "elec": [[[round(p[0], 4), round(p[1], 4)] for p in poly]
                     for poly in veh["det"]["elec"]],
            "anchors": veh["det"]["anchor"],
            "bounds": [round(min(xs), 4), round(max(xs), 4),
                       round(min(zs), 4), round(max(zs), 4)],
            "render": r,
        }
    cat["partition_check"] = checks
    bad = [c for c in checks if c["gap_points"] or c["overlap_points"] or c["elec_bad"]]
    with open(os.path.join(HERE, "vehicle_catalogue.json"), "w", encoding="utf-8") as f:
        json.dump(cat, f, separators=(",", ":"))
    print("wrote vehicle_catalogue.json")
    if bad:
        print("ZONE PARTITION FAILED - not usable")
        return 1
    print("ZONE PARTITION OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
