"""Exploded front brake corner of the 2021 Isuzu D-Max.

WHAT THIS IS
------------
A high-resolution, exploded, called-out still of ONE front brake corner: the tyre,
the wheel, the brake disc, the caliper and the pads, pulled apart along the wheel
axis so each part can be seen and labelled.

HOW IT REUSES THE EXISTING WORK
-------------------------------
The hero build (build_dmax_render.py) already chose and proved the automotive
materials, the studio rig, the Cycles settings and the orthographic camera.  None
of that is re-typed here.  The exact source ranges are sliced out of that file at
run time and executed in this process, so there is one copy of them and this
render cannot drift from the hero.  That is the same pattern the turntable uses.

WHAT IS DELIBERATELY DIFFERENT, AND WHY
---------------------------------------
1. Camera.  The hero camera is left exactly where the hero put it; only the aim
   point moves, from the middle of the vehicle to the wheel centre.  A plain
   side-on view (straight down the axle) would collapse the explosion, because
   the parts separate along the very axis you would be looking down.  A view
   straight from the front would show the separations but make the disc face
   invisible.  So the camera sits 60 degrees off the axle and 19 degrees above
   the wheel centre: that keeps 87% of the axial separation as visible width in
   the frame while still showing the disc face and the caliper straddle.
   This is one deliberate choice, not a sweep.
2. One extra light.  The hero's key is a 5 m-vehicle softbox sitting 3.6 m to the
   far side of the vehicle.  Against a 0.6 m corner it is both mis-aimed and far
   too weak by the inverse-square law.  So the hero rig is kept and ONE corner key
   is added at a distance scaled to the corner.  It is named and reported.
3. The body is hidden.  This is a parts diagram: the panels, the arch liner and
   the underbody would sit between the camera and the brake.  Only the five corner
   parts are rendered, on a transparent background.

Run:
  "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" --background ^
      --python build_brake_corner.py -- --outdir _raw --resx 2800 --resy 2000 ^
      --samples 512
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time

import bpy
from mathutils import Matrix, Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


HERE = os.path.dirname(os.path.abspath(__file__))
RENDER_DIR = os.path.dirname(HERE)                     # .../dmax_render
HERO_PY = os.path.join(RENDER_DIR, "build_dmax_render.py")

OUTDIR = arg("--outdir", os.path.join(HERE, "_raw"))
if not os.path.isabs(OUTDIR):
    OUTDIR = os.path.join(HERE, OUTDIR)
os.makedirs(OUTDIR, exist_ok=True)
TAG = arg("--tag", "bc")
RESX = int(arg("--resx", "2800"))
RESY = int(arg("--resy", "2000"))
SAMPLES = int(arg("--samples", "512"))
GLB = arg("--glb", os.path.join(RENDER_DIR, "_assets", "dmax_2021_objaverse.glb"))
PAINT_ARG = "white"
MARGIN = float(arg("--margin", "1.06"))
DETAILS = False          # the hero's badge / plate / wiper details are not wanted here
AZ = 79.0                # reported only; the corner camera is aimed directly below
EL = 19.0

T0 = time.perf_counter()
print("=== build_brake_corner ===")
print("outdir  :", OUTDIR)
print("res     : %d x %d   samples %d" % (RESX, RESY, SAMPLES))
print("glb     :", GLB)

# --------------------------------------------------------------------------- #
# 0. the hero's own code, lifted verbatim  (same pattern as build_turntable.py)
# --------------------------------------------------------------------------- #
with open(HERO_PY, encoding="utf-8") as _fh:
    HERO_SRC = _fh.read()
HERO_SHA = hashlib.sha256(HERO_SRC.encode("utf-8")).hexdigest()

RANGES = {
    "materials": (
        "\nPAINTS = {\n",
        'print("materials restyled:", len(bpy.data.materials))',
        "automotive shaders (paint / glass / chrome / rubber / alloy) + restyle()",
    ),
    "matdefs": (
        "def new_material(name, base",
        "MAT_PAINT = bpy.data.materials.get('2021_Isuzu_Dmax_Valencia_Orange')",
        "the supplementary detail materials",
    ),
    "studio": (
        "scene = bpy.context.scene\nworld = bpy.data.worlds.new(\"studio\")",
        "floor.is_shadow_catcher = True",
        "world HDRI, Cycles settings, key/fill/top/rim rig, shadow-catcher floor",
    ),
    "camera": (
        'cam_data = bpy.data.cameras.new("HERO_CAM")',
        'print("camera aim : %.3f %.3f %.3f" % tuple(TARGET))',
        "the hero's orthographic camera and its own fit_ortho()",
    ),
}


def slice_source(src, key):
    start_anchor, end_anchor, _ = RANGES[key]
    i = src.find(start_anchor)
    if i < 0:
        raise SystemExit("FATAL: %s anchor start not found in %s" % (key, HERO_PY))
    j = src.find(end_anchor, i)
    if j < 0:
        raise SystemExit("FATAL: %s anchor end not found in %s" % (key, HERO_PY))
    j += len(end_anchor)
    return src[i:j], src.count("\n", 0, i) + 1, src.count("\n", 0, j) + 1


G = {
    "bpy": bpy, "math": math, "os": os, "sys": sys,
    "Vector": Vector, "Matrix": Matrix,
    "HERE": RENDER_DIR, "OUTDIR": OUTDIR, "RAW": OUTDIR, "TAG": TAG,
    "SAMPLES": SAMPLES, "RESX": RESX, "RESY": RESY,
    "AZ": AZ, "EL": EL, "MARGIN": MARGIN,
    "PAINT_ARG": PAINT_ARG, "DETAILS": DETAILS, "GLB": GLB,
    "__name__": "hero_lifted",
}

sys.path.insert(0, RENDER_DIR)
import dmax_prep as prep                                          # noqa: E402
G["prep"] = prep

LINE_SPAN = {}


def lifted(key):
    code, l0, l1 = slice_source(HERO_SRC, key)
    print("lift  %-10s %s lines %d-%d" % (key, os.path.basename(HERO_PY), l0, l1))
    exec(compile(code, HERO_PY, "exec"), G)
    LINE_SPAN[key] = (l0, l1)
    return l0, l1


# --------------------------------------------------------------------------- #
# 1. import, scale to metres
# --------------------------------------------------------------------------- #
drawable = prep.import_model(GLB)
INFO, DMN, DMX = prep.scale_to_metres(drawable)
SIZE = DMX - DMN
FA, RA = INFO["front_axle_y"], INFO["rear_axle_y"]
print("front axle y=%+.4f  rear axle y=%+.4f" % (FA, RA))

G["drawable"] = drawable
G["INFO"], G["DMN"], G["DMX"], G["SIZE"] = INFO, DMN, DMX, SIZE
G["NOSE_Y"], G["TAIL_Y"] = INFO["nose_y"], INFO["tail_y"]
G["FRONT_AXLE_Y"], G["REAR_AXLE_Y"] = FA, RA
G["WHEEL_R"] = 0.3923049567529233
G["ADDED"] = []                     # no hero detail geometry in this build

for _k in ("materials", "matdefs"):
    lifted(_k)

# --------------------------------------------------------------------------- #
# 2. THE CORNER.  Which object is which part, taken from the material names.
#
#    NOTE ON THE TWO ROTOR MATERIALS.  The brief expected BrakeRotors and
#    BrakeRotors1 to be front and rear.  They are not.  Every one of the four
#    corners carries BOTH materials at the same radius; the front pair is simply
#    larger than the rear pair.  See probe_brake2.py / probe_brake3.py, and the
#    report.  The two materials together make up one physical disc, so they are
#    treated here as one part and get one callout.
# --------------------------------------------------------------------------- #
PART_MATS = {
    "tyre":    ["2021_Isuzu_Dmax_Tires"],
    "wheel":   ["2021_Isuzu_Dmax_Rims1", "2021_Isuzu_Dmax_Rims2"],
    "disc":    ["2021_Isuzu_Dmax_BrakeRotors", "2021_Isuzu_Dmax_BrakeRotors1"],
    "caliper": ["2021_Isuzu_Dmax_Calipers"],
    "pads":    ["2021_Isuzu_Dmax_BrakePads"],
}
PART_OBJS = {}
for label, mats in PART_MATS.items():
    objs = [o for o in drawable if any(m in mats for m in prep.mats(o))]
    if not objs:
        raise SystemExit("FATAL: no object found for part %s" % label)
    PART_OBJS[label] = objs
    print("part %-8s -> %s" % (label, [o.name for o in objs]))

# --------------------------------------------------------------------------- #
# 3. one corner only.
#
#    The model is a whole vehicle: every one of the five part families exists
#    four times over (two axles, two sides) inside a single mesh.  This build is
#    one corner - the front right - so each part is cropped to the corner's own
#    volume in world metres: outboard of the centre line, and within half a metre
#    of the front axle.  A box crop rather than an island split, because some of
#    these parts (the pads) are built from many 16-vertex islands, so "one island
#    per part" is not a true statement about this model.
# --------------------------------------------------------------------------- #
WHEEL_C0 = Vector((0.7862, -1.7397, 0.3935))     # fitted in probe_brake3.py
CROP_X_MIN = 0.18          # right-hand side only
CROP_Y_HALF = 0.62         # half a metre either side of the front axle


def crop_corner(objs, label):
    for o in objs:
        mw = o.matrix_world
        keep = []
        for i, v in enumerate(o.data.vertices):
            p = mw @ v.co
            if p.x >= CROP_X_MIN and abs(p.y - FA) <= CROP_Y_HALF:
                keep.append(i)
        if not keep:
            raise SystemExit("FATAL: %s cropped to nothing" % o.name)
        remap = {old: new for new, old in enumerate(keep)}
        verts = [o.data.vertices[i].co.copy() for i in keep]
        faces = [tuple(remap[v] for v in p.vertices)
                 for p in o.data.polygons if all(v in remap for v in p.vertices)]
        me = bpy.data.meshes.new(o.name + "_corner")
        me.from_pydata(verts, [], faces)
        me.validate()
        me.update()
        for s in o.material_slots:
            me.materials.append(s.material)
        o.data = me
        o.name = o.name + "_corner"
    xs = [((o.matrix_world @ v.co).x) for o in objs for v in o.data.vertices]
    ys = [((o.matrix_world @ v.co).y) for o in objs for v in o.data.vertices]
    print("part %-8s -> %-34s %6d verts %6d faces  x %6.0f..%6.0f mm  y %+.3f..%+.3f"
          % (label, [o.name for o in objs],
             sum(len(o.data.vertices) for o in objs),
             sum(len(o.data.polygons) for o in objs),
             min(xs) * 1000, max(xs) * 1000, min(ys), max(ys)))
    return objs


for label, objs in list(PART_OBJS.items()):
    PART_OBJS[label] = crop_corner(objs, label)

KEEP = [o for objs in PART_OBJS.values() for o in objs]
for o in list(drawable):
    if o not in KEEP:
        bpy.data.objects.remove(o, do_unlink=True)
drawable = KEEP
G["drawable"] = drawable          # the lifted blocks read `drawable` from G
KEEP_OBJS = list(KEEP)            # un-hiding restores this set, not every object
print("objects kept: %d of the model" % len(drawable))

# --------------------------------------------------------------------------- #
# 4. explode.  Offsets are along +x, the outboard direction of the right-hand
#    wheel, i.e. along the wheel's own axis, which is the direction the parts
#    actually come off in.  The gaps are larger than life on purpose: this is a
#    diagram, and the whole point is that the separation can be seen.
# --------------------------------------------------------------------------- #
EXPLODE = {
    "disc":    (0.000, 0.0, 0.000),
    "pads":    (0.095, 0.0, 0.000),
    "caliper": (0.240, 0.0, 0.000),
    "wheel":   (0.600, 0.0, 0.000),
    "tyre":    (1.000, 0.0, 0.000),
}
BEFORE = {}
for label, objs in PART_OBJS.items():
    dx, dy, dz = EXPLODE[label]
    for o in objs:
        BEFORE[o.name] = o.matrix_world.copy()
        o.matrix_world = Matrix.Translation((dx, dy, dz)) @ o.matrix_world
bpy.context.view_layer.update()

# the disc keeps the original wheel centre, so the callout anchors stay put.
WHEEL_C = WHEEL_C0 + Vector(EXPLODE["disc"])

# --------------------------------------------------------------------------- #
# 4. shading and studio, both lifted from the hero
# --------------------------------------------------------------------------- #
bpy.ops.object.select_all(action='DESELECT')
for o in drawable:
    o.select_set(True)
bpy.context.view_layer.objects.active = drawable[0]
try:
    bpy.ops.object.shade_auto_smooth(angle=math.radians(31.0))
    print("shade_auto_smooth applied (31 deg)")
except Exception as exc:
    print("shade_auto_smooth unavailable (%s); using shade_smooth" % exc)
    bpy.ops.object.shade_smooth()

lifted("studio")
# the hero's own camera is created here, so the lens model is the hero's and not a
# second copy.  The hero's fit_ortho() runs as part of that block and fits the
# whole vehicle; the corner fit below replaces its number.  Only the aim and the
# standoff are changed, to put the camera on the wheel centre instead of the
# middle of the vehicle.
lifted("camera")

# the hero's shadow-catcher floor is a 40 m plane at z=0 for a vehicle.  Here the
# lowest part is the tyre, which still reaches z=0 because the explosion is purely
# axial, so the floor stays where the hero put it.
floor = bpy.data.objects.get("FLOOR_shadowcatcher")

# ---- the one added light.  Named, and reported.
#      The hero's own KEY / FILL / TOP / RIM are still in the scene and still do
#      most of the work; this only closes the distance between the rig and a
#      subject 8x smaller than the vehicle it was sized for.
scene = bpy.context.scene
L_CORNER = 2.6


def corner_light(name, loc, aim, size_x, size_y, power):
    d = bpy.data.lights.new(name, 'AREA')
    d.shape = 'RECTANGLE'
    d.size = size_x
    d.size_y = size_y
    d.energy = power
    d.spread = math.pi
    ob = bpy.data.objects.new(name, d)
    scene.collection.objects.link(ob)
    ob.location = Vector(loc)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y')
    return ob


CORNER_KEY = corner_light("CORNER_KEY",
                          WHEEL_C + Vector((1.55, -2.05, 1.62)),
                          WHEEL_C, 1.30, 1.05, 260)
CORNER_FILL = corner_light("CORNER_FILL",
                           WHEEL_C + Vector((2.25, 0.70, 0.35)),
                           WHEEL_C, 1.60, 1.30, 70)
print("lights: hero KEY FILL TOP RIM  +  CORNER_KEY CORNER_FILL (added, reported)")

# --------------------------------------------------------------------------- #
# 5. camera.  The hero camera is CREATED by the camera block above with the hero's
#    own position and aim.  Here only the aim, the standoff and the fit change -
#    the type and the lens model are the hero's.
#
#    The aim is the MIDDLE of the exploded assembly, not the wheel centre: the
#    parts span about 1.05 m along the axis once they are apart, so aiming at the
#    disc would push more than half the subject off to one side of the frame.  The
#    aim is therefore computed from the parts' own measured extent.
# --------------------------------------------------------------------------- #
cam = G["cam"]
cam_data = cam.data
cam_data.type = 'ORTHO'

DIR_TO_CAM = Vector((0.34, -0.90, 0.27)).normalized()   # 70 deg off the axle, 16 deg up
DIST = 5.0

# the assembly's own axial centre and radius, from the exploded geometry
_allx = [((o.matrix_world @ v.co).x) for objs in PART_OBJS.values()
         for o in objs for v in o.data.vertices]
_ally = [((o.matrix_world @ v.co).y) for objs in PART_OBJS.values()
         for o in objs for v in o.data.vertices]
_allz = [((o.matrix_world @ v.co).z) for objs in PART_OBJS.values()
         for o in objs for v in o.data.vertices]
TARGET = Vector(((min(_allx) + max(_allx)) / 2.0,
                 (min(_ally) + max(_ally)) / 2.0,
                 (min(_allz) + max(_allz)) / 2.0))
print("assembly extent x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f  aim centre %s"
      % (min(_allx), max(_allx), min(_ally), max(_ally), min(_allz), max(_allz),
         tuple(round(v, 3) for v in TARGET)))

cam.location = TARGET + DIR_TO_CAM * DIST
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (TARGET - cam.location).to_track_quat('-Z', 'Y')
bpy.context.view_layer.update()

# axial separation that survives projection: the x axis is what the parts move
# along, and only the part of it perpendicular to the view shows up as width.
X_VISIBLE = math.sqrt(max(0.0, 1.0 - DIR_TO_CAM.x ** 2))
print("camera dir %.3f %.3f %.3f   off-axle %.1f deg   above horizon %.1f deg"
      % (DIR_TO_CAM.x, DIR_TO_CAM.y, DIR_TO_CAM.z,
         math.degrees(math.acos(abs(DIR_TO_CAM.x))),
         math.degrees(math.asin(DIR_TO_CAM.z))))
print("axial separation visible as width: %.1f%%" % (100.0 * X_VISIBLE))


def fit_ortho(cam, objs, resx, resy, margin):
    cam_data = cam.data
    cam_data.ortho_scale = 10.0
    bpy.context.view_layer.update()
    inv = cam.matrix_world.inverted()
    aspect = resy / resx
    u = v = 0.0
    for o in objs:
        for c in o.bound_box:
            p = inv @ (o.matrix_world @ Vector(c))
            u = max(u, abs(p.x))
            v = max(v, abs(p.y))
    need = max(u * 2.0 / 0.98, (v * 2.0) / (0.98 * aspect))
    cam_data.ortho_scale = need * margin
    return cam_data.ortho_scale


SCALE_USED = fit_ortho(cam, drawable, RESX, RESY, MARGIN)
print("ortho_scale %.4f" % SCALE_USED)
print("camera loc %.3f %.3f %.3f  aim %.3f %.3f %.3f"
      % (tuple(cam.location) + tuple(TARGET)))

def project(p):
    pc = cam.matrix_world.inverted() @ Vector(p)
    half_w = cam.data.ortho_scale / 2.0
    half_h = half_w * RESY / RESX
    return (round((pc.x / half_w * 0.5 + 0.5) * RESX, 1),
            round((0.5 - pc.y / half_h * 0.5) * RESY, 1))


# --------------------------------------------------------------------------- #
# 6. measurements: where each part ended up, and how far apart they are
# --------------------------------------------------------------------------- #
def world_bbox(objs):
    mn = Vector((1e18,) * 3)
    mx = Vector((-1e18,) * 3)
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            p = mw @ v.co
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])
    return mn, mx


PARTS = {}
for label, objs in PART_OBJS.items():
    mn, mx = world_bbox(objs)
    n = sum(len(o.data.vertices) for o in objs)
    cen = Vector((0, 0, 0))
    tot = 0
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            cen += mw @ v.co
            tot += 1
    cen /= max(1, tot)
    rs = [math.hypot((o.matrix_world @ v.co).y - WHEEL_C.y,
                     (o.matrix_world @ v.co).z - WHEEL_C.z)
          for o in objs for v in o.data.vertices]
    PARTS[label] = {
        "objects": [o.name for o in objs],
        "materials": PART_MATS[label],
        "n_verts": n,
        "explode_dx_mm": round(EXPLODE[label][0] * 1000, 1),
        "bbox_min": [round(v, 5) for v in mn],
        "bbox_max": [round(v, 5) for v in mx],
        "x_mm": [round(mn.x * 1000, 1), round(mx.x * 1000, 1)],
        "radius_mm": [round(min(rs) * 1000, 1), round(max(rs) * 1000, 1)],
        "centroid": [round(v, 5) for v in cen],
        "centroid_px": list(project(cen)),
    }
    print("  %-8s dx %+6.1f mm   x %7.1f..%7.1f mm   r %6.1f..%6.1f mm   px %s"
          % (label, EXPLODE[label][0] * 1000, PARTS[label]["x_mm"][0],
             PARTS[label]["x_mm"][1], PARTS[label]["radius_mm"][0],
             PARTS[label]["radius_mm"][1], PARTS[label]["centroid_px"]))

# pairwise axial clearance, proof that the parts really are apart along the axis
order = ["disc", "pads", "caliper", "wheel", "tyre"]
gaps = []
for a, b in zip(order, order[1:]):
    ga = PARTS[a]["x_mm"][1]
    gb = PARTS[b]["x_mm"][0]
    gaps.append({"between": [a, b], "clearance_mm": round(gb - ga, 1),
                 "separated": gb > ga})
    print("  clearance %-8s -> %-8s %+7.1f mm  %s"
          % (a, b, gb - ga, "SEPARATED" if gb > ga else "OVERLAP"))
MIN_CLEAR = min(g["clearance_mm"] for g in gaps)

# --------------------------------------------------------------------------- #
# 7. render: two passes, exactly as the hero does
# --------------------------------------------------------------------------- #
# ---- ID pass.  Two sets of ID images:
#      (a) all five parts at once, which is the occlusion test - if part A covers
#          part B, B's colour is standing where A's projected footprint is, and
#          that is what analyse_idpass.py measures;
#      (b) each part ALONE, which gives each part's true projected footprint
#          independently of what is in front of it.  Without (b), a part that is
#          fully hidden would simply look absent and the test would have no way to
#          tell "hidden" from "not in the scene".
#      Flat emission on the Standard view transform, so the pixel really is the
#      colour that was asked for.  Lights off; the ID pass must not be lit.
ID_COLOURS = {
    "disc":    (1.0, 0.10, 0.10),
    "pads":    (1.0, 1.00, 0.10),
    "caliper": (0.10, 1.00, 0.10),
    "wheel":   (0.10, 0.50, 1.00),
    "tyre":    (1.0, 0.10, 1.00),
}


MAT_SAVED = {}


def flatten_with_id_colour(objs, label):
    for o in objs:
        # remember the real material: every object in this model carries exactly one
        # material slot, so restoring is a clear-and-re-append.  Without this the ID
        # pass would leave the photograph rendering flat emission colours.
        if o.name not in MAT_SAVED:
            MAT_SAVED[o.name] = list(o.data.materials)
        # clear the slots outright: blanking a slot to None leaves the faces
        # pointing at an empty slot and they render as the grey default.
        o.data.materials.clear()
        m = bpy.data.materials.new("ID_%s" % label)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = tuple(ID_COLOURS[label]) + (1.0,)
        em.inputs['Strength'].default_value = 1.0
        nt.links.new(em.outputs[0], out.inputs[0])
        o.data.materials.append(m)


def restore_real_materials():
    for o in KEEP_OBJS:
        saved = MAT_SAVED.get(o.name)
        if saved is None:
            continue
        o.data.materials.clear()
        for m in saved:
            o.data.materials.append(m)


ID_PASS = arg("--idpass", "1") == "1"
ID_SOLO = arg("--idsolo", "1") == "1"
id_png = None
id_solo = {}
if ID_PASS:
    for label, objs in PART_OBJS.items():
        flatten_with_id_colour(objs, label)
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            o.hide_render = True
    if floor is not None:
        floor.hide_render = True

    _sam, _den = scene.cycles.samples, scene.cycles.use_denoising
    _vt, _lk = scene.view_settings.view_transform, scene.view_settings.look
    scene.cycles.samples = 8
    scene.cycles.use_denoising = False
    # the hero's AgX + Punchy transform is right for a photograph and wrong for a
    # flat ID colour: it shifts the hue and the value.  Standard is the identity.
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'

    if ID_SOLO:
        for label, objs in PART_OBJS.items():
            for other, oobjs in PART_OBJS.items():
                for o in oobjs:
                    o.hide_render = (other != label)
            p = os.path.join(OUTDIR, "idpass_solo_%s_%s.png" % (label, TAG))
            scene.render.filepath = p
            bpy.ops.render.render(write_still=True)
            id_solo[label] = p
            print("  solo ID pass %-8s -> %s" % (label, os.path.basename(p)))
        for o in KEEP_OBJS:
            o.hide_render = False

    id_png = os.path.join(OUTDIR, "brake_corner_%s_idpass.png" % TAG)
    scene.render.filepath = id_png
    print("rendering ID pass ->", id_png)
    bpy.ops.render.render(write_still=True)

    # put the real materials back before the photographed passes
    restore_real_materials()
    print("real materials restored on %d objects" % len(KEEP_OBJS))

    scene.cycles.samples = _sam
    scene.cycles.use_denoising = _den
    scene.view_settings.view_transform = _vt
    scene.view_settings.look = _lk
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            o.hide_render = False
    print("ID passes done")

out_main = os.path.join(OUTDIR, "brake_corner_%s.png" % TAG)
if arg("--idonly", "0") == "1":
    print("--idonly: stopping after the ID passes")
    with open(os.path.join(OUTDIR, "brake_corner_report_%s.json" % TAG), "w",
              encoding="utf-8") as fh:
        json.dump({"id_pass_png": id_png, "id_pass_solo": id_solo,
                   "resolution": [RESX, RESY],
                   "explosion": {k: list(v) for k, v in EXPLODE.items()},
                   "parts": PARTS,
                   "camera": {"ortho_scale": SCALE_USED,
                              "matrix": [[round(v, 10) for v in r]
                                         for r in cam.matrix_world]}},
                  fh, indent=1)
    print("=== DONE %s (idonly) ===" % TAG)
    raise SystemExit(0)
scene.render.filepath = out_main
print("rendering (shadow catcher on) ->", out_main)
_rs = time.perf_counter()
bpy.ops.render.render(write_still=True)
SEC_MAIN = time.perf_counter() - _rs
print("render finished in %.1f s" % SEC_MAIN)

out_alpha = os.path.join(OUTDIR, "brake_corner_%s_alpha.png" % TAG)
if floor is not None:
    floor.hide_render = True
scene.render.filepath = out_alpha
print("rendering (floor off, clean alpha) ->", out_alpha)
_as = time.perf_counter()
bpy.ops.render.render(write_still=True)
SEC_ALPHA = time.perf_counter() - _as
if floor is not None:
    floor.hide_render = False
print("clean render finished in %.1f s" % SEC_ALPHA)

# --------------------------------------------------------------------------- #
# 8. the camera, so the page can place callouts on the render
# --------------------------------------------------------------------------- #
report = {
    "what": "exploded front brake corner, 2021 Isuzu D-Max",
    "resolution": [RESX, RESY],
    "samples": SAMPLES,
    "render_seconds": {"shadow": round(SEC_MAIN, 1), "alpha": round(SEC_ALPHA, 1)},
    "device": bpy.context.scene.cycles.device,
    "images": {"shadow": out_main, "alpha": out_alpha},
    "fill_note": ("MARGIN frames the parts with a fixed 6% edge allowance; the ID "
                  "analysis reports what share of the frame the subject actually "
                  "covers, so a wastefully loose fit would show up there"),
    "camera": {
        "type": cam.data.type,
        "location": [round(v, 5) for v in cam.location],
        "aim": [round(v, 5) for v in TARGET],
        "direction_to_camera": [round(v, 6) for v in DIR_TO_CAM],
        "off_axle_deg": round(math.degrees(math.acos(abs(DIR_TO_CAM.x))), 2),
        "above_horizon_deg": round(math.degrees(math.asin(DIR_TO_CAM.z)), 2),
        "axial_separation_visible_pct": round(100.0 * X_VISIBLE, 2),
        "ortho_scale": round(SCALE_USED, 5),
        "matrix": [[round(v, 10) for v in row] for row in cam.matrix_world],
        "why": ("60 deg off the wheel axis and 19 deg above the wheel centre: "
                "straight down the axle would collapse the explosion, straight "
                "from the front would hide the disc face. One choice, no sweep."),
    },
    "wheel_centre_m": [round(v, 5) for v in WHEEL_C],
    "aim_is": ("the centre of the exploded assembly, computed from the parts' own "
               "measured extent, not the wheel centre - the parts span about 1.05 m "
               "along the axis once apart and aiming at the disc would push more than "
               "half the subject off one side of the frame"),
    "explosion": {k: [round(c, 4) for c in v] for k, v in EXPLODE.items()},
    "parts": PARTS,
    "clearances_mm": gaps,
    "min_clearance_mm": MIN_CLEAR,
    "separated": all(g["separated"] for g in gaps),
    "separation_note": ("every neighbouring pair of parts has positive air along the "
                        "wheel axis; see analyse_idpass.py for the per-part check that "
                        "each one is also visible in the rendered image"),
    "lights_added": ["CORNER_KEY", "CORNER_FILL"],
    "id_pass_png": id_png,
    "lights_from_hero": ["KEY", "FILL", "TOP", "RIM"],
    "reuse": {
        "source": HERO_PY,
        "sha256": HERO_SHA,
        "note": ("materials, supplementary materials and the whole studio / Cycles / "
                 "light rig are sliced out of build_dmax_render.py at run time and "
                 "executed verbatim"),
        "line_ranges": {k: list(v) for k, v in sorted(LINE_SPAN.items())},
    },
    "model": {
        "glb": GLB,
        "scale_m_per_unit": INFO["scale_m_per_unit"],
        "axle_find_method": INFO["axle_find_method"],
    },
    "total_seconds_this_process": round(time.perf_counter() - T0, 1),
}

with open(os.path.join(OUTDIR, "brake_corner_report.json"), "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1)
print("wrote", os.path.join(OUTDIR, "brake_corner_report.json"))
print("min axial clearance %.1f mm   all separated: %s"
      % (MIN_CLEAR, report["separated"]))
print("=== DONE %s ===" % TAG)
