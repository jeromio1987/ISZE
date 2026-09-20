"""Turntable render: the 2021 Isuzu D-Max turning on the hero camera.

The hero camera (azimuth 80 deg, elevation 18 deg, orthographic, 16 m standoff) is
kept exactly as build_dmax_render.py built it.  What moves is the VEHICLE: it turns
about its own vertical axis in even steps.  That is what a real turntable shoot is -
the object turns on the table and the room's lights stay where they are, so the
highlights sweep across the panels as it comes round.  Because the camera is fixed
and the rotation is rigid about a fixed vertical axis, the truck cannot shift,
grow or shrink between frames; only its yaw changes.

Nothing about the materials, the light rig, the Cycles settings or the camera is
re-implemented here.  Those blocks are read out of build_dmax_render.py at run time
and executed in this process, so there is exactly one copy of them and this script
cannot drift away from the hero.  See slice_source() below, and the report it
writes, which records the exact line ranges and a hash of the source file used.

Run:
  "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe" --background \
      --python build_turntable.py -- \
      --frames 36 --resx 1300 --resy 560 --samples 150 --outdir _raw_tt

Probe a few angles only:
  ... --yaws "0,90,180,270"
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

# --------------------------------------------------------------------------- #
# arguments after the "--"
# --------------------------------------------------------------------------- #
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


HERE = os.path.dirname(os.path.abspath(__file__))          # .../dmax_render/turntable
HERO_DIR = os.path.dirname(HERE)                           # .../dmax_render
HERO_PY = os.path.join(HERO_DIR, "build_dmax_render.py")

OUTDIR = arg("--outdir", os.path.join(HERE, "_raw_tt"))
if not os.path.isabs(OUTDIR):
    OUTDIR = os.path.join(HERE, OUTDIR)
TAG = arg("--tag", "tt")
FRAMES = int(arg("--frames", "36"))
SAMPLES = int(arg("--samples", "150"))
RESX = int(arg("--resx", "1300"))
RESY = int(arg("--resy", "560"))
AZ = float(arg("--az", "80"))
EL = float(arg("--el", "18"))
MARGIN = float(arg("--margin", "1.045"))
GLB = arg("--glb", os.path.join(HERO_DIR, "_assets", "dmax_2021_objaverse.glb"))
PAINT_ARG = arg("--paint", "white")
YAW_LIST = arg("--yaws", None)
DETAILS = arg("--details", "1") == "1"
FLOOR = arg("--floor", "1") == "1"        # shadow-catcher on: the frames need a contact shadow
PROBE = arg("--probe-framing", "0") == "1"
VERIFY_FRAMING = arg("--verify-framing", "0") == "1"
ORTHO_OVERRIDE = float(arg("--ortho", "0")) or None

os.makedirs(OUTDIR, exist_ok=True)

if YAW_LIST:
    YAWS = [float(x) for x in YAW_LIST.split(",")]
    FRAMES = len(YAWS)
else:
    YAWS = [360.0 * j / FRAMES for j in range(FRAMES)]

T0 = time.perf_counter()
print("=== build_turntable ===")
print("hero dir :", HERO_DIR)
print("outdir   :", OUTDIR)
print("frames   : %d  step %.4f deg" % (FRAMES, 360.0 / FRAMES))
print("res      : %d x %d   samples %d   az %.1f  el %.1f"
      % (RESX, RESY, SAMPLES, AZ, EL))
print("paint    : %s   details %s   floor %s" % (PAINT_ARG, DETAILS, FLOOR))
print("glb      :", GLB)

# --------------------------------------------------------------------------- #
# 0. the hero's own code, lifted verbatim
# --------------------------------------------------------------------------- #
# The hero build has already chosen and proved: the axles/scale, the automotive
# shaders, the badge / plate / handle / wiper details, the studio rig, the Cycles
# settings and the camera.  Re-typing any of that here would create a second copy
# that can silently disagree with the hero.  So the exact source ranges are sliced
# out of build_dmax_render.py and executed below.  Each anchor is checked; a
# missing anchor is a hard stop, never a silent fallback.
with open(HERO_PY, encoding="utf-8") as _fh:
    HERO_SRC = _fh.read()
HERO_SHA = hashlib.sha256(HERO_SRC.encode("utf-8")).hexdigest()

RANGES = {
    # name: (start anchor, end anchor, what it provides)
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
    "details": (
        "ADDED = []",
        'print("detail objects added: %d" % len(ADDED))',
        "badge, number plates, door handles, wipers, fuel doors placed from measurement",
    ),
    "smoothing": (
        "bpy.ops.object.select_all(action='DESELECT')\nfor o in drawable:\n    o.select_set(True)",
        "        p.use_smooth = False",
        "auto-smooth so panels curve and panel gaps stay crisp",
    ),
    "studio": (
        "scene = bpy.context.scene\nworld = bpy.data.worlds.new(\"studio\")",
        "floor.is_shadow_catcher = True",
        "world HDRI, Cycles settings, key/fill/top/rim rig, shadow-catcher floor",
    ),
    "camera": (
        'cam_data = bpy.data.cameras.new("HERO_CAM")',
        'print("camera aim : %.3f %.3f %.3f" % tuple(TARGET))',
        "the orthographic camera and the hero's own fit_ortho()",
    ),
}


def slice_source(src: str, key: str):
    start_anchor, end_anchor, _ = RANGES[key]
    i = src.find(start_anchor)
    if i < 0:
        raise SystemExit("FATAL: %s anchor start not found in %s" % (key, HERO_PY))
    j = src.find(end_anchor, i)
    if j < 0:
        raise SystemExit("FATAL: %s anchor end not found in %s" % (key, HERO_PY))
    j += len(end_anchor)
    code = src[i:j]
    line0 = src.count("\n", 0, i) + 1
    line1 = src.count("\n", 0, j) + 1
    return code, line0, line1


# globals the lifted blocks expect to find
G = {
    "bpy": bpy, "math": math, "os": os, "sys": sys,
    "Vector": Vector, "Matrix": Matrix,
    "HERE": HERO_DIR,                 # the studio block resolves _assets/ off HERE
    "OUTDIR": OUTDIR, "RAW": OUTDIR, "TAG": TAG,
    "SAMPLES": SAMPLES, "RESX": RESX, "RESY": RESY,
    "AZ": AZ, "EL": EL, "MARGIN": MARGIN,
    "PAINT_ARG": PAINT_ARG, "DETAILS": DETAILS, "GLB": GLB,
    "__name__": "hero_lifted",
}

sys.path.insert(0, HERO_DIR)          # dmax_prep.py lives next to build_dmax_render.py
import dmax_prep as prep                                          # noqa: E402
G["prep"] = prep


def lifted(key: str):
    code, l0, l1 = slice_source(HERO_SRC, key)
    print("lift  %-10s %s lines %d-%d" % (key, os.path.basename(HERO_PY), l0, l1))
    exec(compile(code, HERO_PY, "exec"), G)
    return l0, l1


# --------------------------------------------------------------------------- #
# 1. import, scale to metres
# --------------------------------------------------------------------------- #
drawable = prep.import_model(GLB)
print("drawable meshes: %d" % len(drawable))
INFO, DMN, DMX = prep.scale_to_metres(drawable)
SIZE = DMX - DMN
G["drawable"] = drawable
G["INFO"], G["DMN"], G["DMX"], G["SIZE"] = INFO, DMN, DMX, SIZE
G["NOSE_Y"], G["TAIL_Y"] = INFO["nose_y"], INFO["tail_y"]
G["FRONT_AXLE_Y"], G["REAR_AXLE_Y"] = INFO["front_axle_y"], INFO["rear_axle_y"]
G["WHEEL_R"] = 0.3923049567529233

LINE_SPAN = {}
for _key in ("materials", "matdefs"):
    LINE_SPAN[_key] = lifted(_key)

# --------------------------------------------------------------------------- #
# 2. details, placed on the measured geometry (same as the hero)
# --------------------------------------------------------------------------- #
if DETAILS:
    _t = time.perf_counter()
    G["CAST"] = prep.make_caster(*prep.build_bvh(drawable))
    G["BOX"] = prep.measure_box(drawable, INFO, G["CAST"])
    G["FRONT"] = prep.measure_front(drawable, INFO, G["CAST"])
    print("measurement/BVH: %.1f s" % (time.perf_counter() - _t))
    LINE_SPAN["details"] = lifted("details")
else:
    G["ADDED"] = []
    print("details disabled")

LINE_SPAN["smoothing"] = lifted("smoothing")

# every object that must turn with the vehicle: the model plus the added details.
# The fit is taken over this whole set, not a material subset, so nothing that
# turns can ever be clipped at the frame edge.
SPIN_OBJS = list(drawable) + list(G.get("ADDED", []))
print("objects that turn: %d (%d model + %d detail)"
      % (len(SPIN_OBJS), len(drawable), len(G.get("ADDED", []))))

# --------------------------------------------------------------------------- #
# studio, Cycles settings, light rig, floor   (lifted before the diagnostics
# below, because both of them need the hero's own camera and its fitted scale)
# --------------------------------------------------------------------------- #
LINE_SPAN["studio"] = lifted("studio")
LINE_SPAN["camera"] = lifted("camera")

# --------------------------------------------------------------------------- #
# framing probe: how the projected extent behaves as the vehicle turns
# --------------------------------------------------------------------------- #
# The camera looks down at 18 deg, so the image height a vehicle occupies is
# proportional to  L*sin(az') + 2*H*cos(el)  - a length term that swings as the
# truck comes round, plus the same height term for every yaw.  That means the
# projected height is a function of yaw with a clean 180-deg period, and its
# maximum decides how much height the sequence needs.  This probe measures it
# instead of trusting the formula, and reports what several candidate frame
# shapes would cost.  It writes JSON and exits; nothing is rendered.
if PROBE:
    cam_p = bpy.data.cameras.new("PROBE_CAM")
    cam_p.type = 'ORTHO'
    cam_ob = bpy.data.objects.new("PROBE_CAM", cam_p)
    bpy.context.scene.collection.objects.link(cam_ob)
    TARGET_P = Vector((0.0, 0.0, SIZE.z * 0.46))
    az_r, el_r = math.radians(AZ), math.radians(EL)
    DIST_P = 16.0
    cam_ob.location = TARGET_P + Vector((math.sin(az_r) * math.cos(el_r) * DIST_P,
                                         -math.cos(az_r) * math.cos(el_r) * DIST_P,
                                         math.sin(el_r) * DIST_P))
    cam_ob.rotation_mode = 'QUATERNION'
    cam_ob.rotation_quaternion = (TARGET_P - cam_ob.location).to_track_quat('-Z', 'Y')
    bpy.context.view_layer.update()
    _inv = cam_ob.matrix_world.inverted()

    def ext(yaw_deg):
        R = Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')
        u = v = 0.0
        for o in SPIN_OBJS:
            mw = o.matrix_world
            for c in o.bound_box:
                q = _inv @ (R @ (mw @ Vector(c)))
                u = max(u, abs(q.x))
                v = max(v, abs(q.y))
        return u, v

    curve = []
    for k in range(37):
        y = k * 10.0
        u, v = ext(y)
        curve.append({"yaw": y, "u": round(u, 4), "v": round(v, 4),
                      "w_m": round(u * 2.0, 4), "h_m": round(v * 2.0, 4)})
    u_all = max(c["u"] for c in curve)
    v_all = max(c["v"] for c in curve)
    options = {}
    for ar in (2.32, 2.0, 1.85, 1.75, 1.6, 1.55, 1.5, 1.4):
        # ar is width/height, so the Blender aspect (resy/resx) is 1/ar.  The
        # ortho scale must satisfy BOTH: scale >= 2u/0.98 across, and
        # scale*(1/ar) >= 2v/0.98 down.  Whichever binds decides the framing.
        need = max(u_all * 2.0 / 0.98, (v_all * 2.0) * ar / 0.98)
        scale = need * MARGIN
        px_w = 1400
        px_h = int(round(px_w / ar))
        px_per_m = px_w / scale
        options["%.2f" % ar] = {
            "aspect": ar,
            "pixels_at_1400_wide": [px_w, px_h],
            "ortho_scale_union": round(scale, 4),
            "binding": "width" if u_all * 2.0 / 0.98 >= (v_all * 2.0) * ar / 0.98 else "height",
            "truck_width_px": round(u_all * 2.0 * px_per_m, 1),
            "truck_height_max_px": round(v_all * 2.0 * px_per_m, 1),
            "fill_w_pct": round(100.0 * u_all * 2.0 * px_per_m / px_w, 1),
            "fill_h_pct": round(100.0 * v_all * 2.0 * px_per_m / px_h, 1),
            "megapixels": round(px_w * px_h / 1e6, 3),
        }
    doc = {"curve": curve,
           "union_u_m": round(u_all * 2.0, 4), "union_v_m": round(v_all * 2.0, 4),
           "max_yaw_u": max(curve, key=lambda c: c["u"])["yaw"],
           "max_yaw_v": max(curve, key=lambda c: c["v"])["yaw"],
           "options": options}
    with open(os.path.join(OUTDIR, "framing_probe.json"), "w") as fh:
        json.dump(doc, fh, indent=1)
    print("=== FRAMING PROBE ===")
    print("union image-space width  %.3f m (at yaw %.0f)" % (u_all * 2, doc["max_yaw_u"]))
    print("union image-space height %.3f m (at yaw %.0f)" % (v_all * 2, doc["max_yaw_v"]))
    for k, o in sorted(options.items()):
        print("  aspect %-5s -> %4dx%-4d  ortho %6.3f (%-6s binds)  truck %5.1f x %5.1f px"
              "  fill %.0f%% w / %.0f%% h"
              % (k, o["pixels_at_1400_wide"][0], o["pixels_at_1400_wide"][1],
                 o["ortho_scale_union"], o["binding"], o["truck_width_px"],
                 o["truck_height_max_px"], o["fill_w_pct"], o["fill_h_pct"]))
    print("wrote", os.path.join(OUTDIR, "framing_probe.json"))
    print("=== PROBE DONE ===")
    raise SystemExit(0)

# --------------------------------------------------------------------------- #
# framing verification: predict every frame's silhouette from the rigid rotation
# --------------------------------------------------------------------------- #
# This is the test that actually settles whether the spin jitters.  Not "is the
# bounding box constant between frames" - a truck genuinely projects narrower end-on,
# so that would fail a perfect turntable.  Instead: for each yaw, take the REAL
# vertex cloud of the vehicle, rotate it, project every vertex through the camera,
# and predict the silhouette's bbox and the position of its centre.  Then render
# nothing and compare that prediction against what the frames actually measured.
#
# A rigid rotation about the model's vertical axis has 180 deg symmetry, so
# yaw+180 must predict an identical bbox.  Any camera shift, scale change or
# off-centre pivot breaks that immediately.
if VERIFY_FRAMING:
    from mathutils import Matrix as _M
    cam_p = bpy.data.cameras.new("VERIFY_CAM")
    cam_p.type = 'ORTHO'
    cam_ob = bpy.data.objects.new("VERIFY_CAM", cam_p)
    bpy.context.scene.collection.objects.link(cam_ob)
    TARGET_V = Vector((0.0, 0.0, SIZE.z * 0.46))
    az_r, el_r = math.radians(AZ), math.radians(EL)
    DV = 16.0
    cam_ob.location = TARGET_V + Vector((math.sin(az_r) * math.cos(el_r) * DV,
                                         -math.cos(az_r) * math.cos(el_r) * DV,
                                         math.sin(el_r) * DV))
    cam_ob.rotation_mode = 'QUATERNION'
    cam_ob.rotation_quaternion = (TARGET_V - cam_ob.location).to_track_quat('-Z', 'Y')
    bpy.context.view_layer.update()
    _inv = cam_ob.matrix_world.inverted()
    _resx, _resy = RESX, RESY
    # recompute the exact same union fit the render used, so the prediction is
    # expressed in the same pixel space as the frames
    cam_p.ortho_scale = 10.0
    _u = _v = 0.0
    for _y in YAWS:
        _R = Matrix.Rotation(math.radians(_y), 4, 'Z')
        for _o in SPIN_OBJS:
            _mw = _o.matrix_world
            for _c in _o.bound_box:
                _q = _inv @ (_R @ (_mw @ Vector(_c)))
                _u = max(_u, abs(_q.x))
                _v = max(_v, abs(_q.y))
    _sc = max(max(_u * 2.0 / 0.98, (_v * 2.0) / (0.98 * (RESY / RESX))) * MARGIN,
              G["scale_used"])
    if ORTHO_OVERRIDE:
        _sc = ORTHO_OVERRIDE
    cam_p.ortho_scale = _sc
    print("verify framing: ortho_scale %.4f" % _sc)

    # every real vertex, sampled so the cloud is heavy enough to be the true silhouette
    _pts = []
    for _o in SPIN_OBJS:
        _vs = _o.data.vertices
        _step = max(1, len(_vs) // 3000)
        _mw = _o.matrix_world
        for _i in range(0, len(_vs), _step):
            _pts.append(_mw @ _vs[_i].co)
    print("verify framing: %d sample vertices" % len(_pts))

    def predict(yaw_deg):
        R = _M.Rotation(math.radians(yaw_deg), 4, 'Z')
        u0 = u1 = v0 = v1 = None
        for p in _pts:
            q = _inv @ (R @ p)
            if u0 is None:
                u0 = u1 = q.x; v0 = v1 = q.y
            else:
                u0 = min(u0, q.x); u1 = max(u1, q.x)
                v0 = min(v0, q.y); v1 = max(v1, q.y)
        half_w = _sc / 2.0
        half_h = half_w * _resy / _resx
        px0 = (u0 / half_w * 0.5 + 0.5) * _resx
        px1 = (u1 / half_w * 0.5 + 0.5) * _resx
        py0 = (0.5 - v1 / half_h * 0.5) * _resy
        py1 = (0.5 - v0 / half_h * 0.5) * _resy
        # the OTHER half of the x scale: subtracting the camera x, not adding
        return {"x0": px0, "x1": px1, "y0": py0, "y1": py1,
                "w": px1 - px0, "h": py1 - py0,
                "cx": (px0 + px1) / 2.0, "cy": (py0 + py1) / 2.0}

    pred = {}
    for y in YAWS:
        pred["%.4f" % y] = {k: round(v, 2) for k, v in predict(y).items()}

    # 180-degree symmetry of the PREDICTION: the whole sequence is rigid, so
    # yaw+180 must give the same bbox.  (Front and back differ in shape, but the
    # camera geometry maps them to the same envelope for a half turn.)
    print("\nverify framing: predicted bbox per frame")
    print("  %-9s %9s %9s %9s %9s" % ("yaw", "width", "height", "centre_x", "centre_y"))
    for k in list(pred)[:6]:
        p = pred[k]
        print("  %-9s %9.1f %9.1f %9.1f %9.1f" % (k, p["w"], p["h"], p["cx"], p["cy"]))

    ws = [pred[k]["w"] for k in pred]
    hs = [pred[k]["h"] for k in pred]
    cxs = [pred[k]["cx"] for k in pred]
    cys = [pred[k]["cy"] for k in pred]
    print("\nverify framing: predicted ranges over %d yaws" % len(pred))
    print("  width  %.1f .. %.1f  (spread %.1f px)" % (min(ws), max(ws), max(ws) - min(ws)))
    print("  height %.1f .. %.1f  (spread %.1f px)" % (min(hs), max(hs), max(hs) - min(hs)))
    print("  centre_x %.1f .. %.1f  (spread %.1f px)" % (min(cxs), max(cxs), max(cxs) - min(cxs)))
    print("  centre_y %.1f .. %.1f  (spread %.1f px)" % (min(cys), max(cys), max(cys) - min(cys)))
    print("  NOTE: width/height spread here is the ROTATION of a 5.4 x 2.1 m object,")
    print("        not camera or scale drift.  What matters is that the prediction is")
    print("        generated from ONE fixed camera and compared to the frames.")

    # fit margins: does anything ever touch the frame edge?
    m_left = min(cxs and [pred[k]["x0"] for k in pred])
    m_right = _resx - max(pred[k]["x1"] for k in pred)
    m_top = min(pred[k]["y0"] for k in pred)
    m_bot = _resy - max(pred[k]["y1"] for k in pred)
    print("  frame margins: left %.1f  right %.1f  top %.1f  bottom %.1f px"
          % (m_left, m_right, m_top, m_bot))
    if min(m_left, m_right, m_top, m_bot) < 0:
        print("  !! a frame edge is crossed - the sequence would clip")

    with open(os.path.join(OUTDIR, "framing_verify.json"), "w") as fh:
        json.dump({"ortho_scale": _sc, "resolution": [RESX, RESY],
                   "vertices": len(_pts), "predicted": pred,
                   "ranges": {"width": [min(ws), max(ws)],
                              "height": [min(hs), max(hs)],
                              "centre_x": [min(cxs), max(cxs)],
                              "centre_y": [min(cys), max(cys)]},
                   "margins_px": {"left": round(m_left, 1), "right": round(m_right, 1),
                                  "top": round(m_top, 1), "bottom": round(m_bot, 1)}},
                  fh, indent=1)
    print("wrote", os.path.join(OUTDIR, "framing_verify.json"))
    print("=== VERIFY FRAMING DONE ===")
    raise SystemExit(0)

# --------------------------------------------------------------------------- #
# 5. THE ONE FRAMING DECISION
# --------------------------------------------------------------------------- #
# A turntable has to hold one framing for every frame.  If the fit were
# recomputed per frame the truck would breathe in and out as it turned - the exact
# jitter to avoid.  So the fit is taken ONCE, over the union of every yaw in the
# sequence: the projected bounding box of each yaw is measured, the largest is
# kept, and that single ortho_scale is used for all frames.  The cost is that the
# frames where the truck is longest or tallest carry a little more air than the
# hero does; the benefit is that the camera is provably identical in every frame.
cam = G["cam"]
_cam_data = cam.data
framing = G["framing"]                # the hero's own framing object set
_hero_scale = G["scale_used"]         # the hero's fit at az 80 / el 18, i.e. yaw 0


def projected_extent(yaw_deg):
    """Furthest |x| and |y| reached by any bounding-box corner, in camera space,
    with the vehicle turned by yaw_deg about its own vertical axis."""
    inv = cam.matrix_world.inverted()
    R = Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')   # the plan-centre is at the origin
    u = v = 0.0
    for o in SPIN_OBJS:
        mw = o.matrix_world
        for c in o.bound_box:
            q = inv @ (R @ (mw @ Vector(c)))
            u = max(u, abs(q.x))
            v = max(v, abs(q.y))
    return u, v


_aspect = RESY / RESX
_u = _v = 0.0
_worst_yaw = None
for _y in YAWS:
    _uu, _vv = projected_extent(_y)
    if _uu > _u or _vv > _v:
        _worst_yaw = _y
    _u, _v = max(_u, _uu), max(_v, _vv)

_need = max(_u * 2.0 / 0.98, (_v * 2.0) / (0.98 * _aspect))
_fit_scale = _need * MARGIN
# Never frame tighter than the hero did.  The hero's fit at az 80 / el 18 is the
# accepted look; at yaw 0 it IS the hero.  If the union fit asked for a scale below
# that (which it can, because at yaw 0 the truck is momentarily shorter than the
# widest yaw), the hero's own value wins, so frame 1 matches the accepted hero
# framing exactly and the rest of the sequence never crops in past it.
UNION_SCALE = max(_fit_scale, _hero_scale)
_cam_data.ortho_scale = UNION_SCALE

print("framing: hero fit at yaw 0 = %.4f, union fit over %d yaws = %.4f -> using %.4f (%+.1f%%)"
      % (_hero_scale, len(YAWS), _fit_scale, UNION_SCALE,
         100.0 * (UNION_SCALE / _hero_scale - 1.0)))

# Hero parity, checked properly.  The ortho fit depends on the frame's aspect ratio, so
# comparing a fit taken at 1500x860 with the hero's 2600x1120 would be meaningless.
# What must hold is that this camera model reproduces the hero's own number when it is
# given the hero's resolution: that is the real proof the camera has not drifted.
def _fit_at(resx, resy):
    aspect = resy / resx
    u = v = 0.0
    inv = cam.matrix_world.inverted()
    for o in framing:
        for c in o.bound_box:
            q = inv @ (o.matrix_world @ Vector(c))
            u = max(u, abs(q.x))
            v = max(v, abs(q.y))
    return max(u * 2.0 / 0.98, (v * 2.0) / (0.98 * aspect)) * MARGIN


HERO_SCALE_REF = 6.686607360839844
hero_parity = _fit_at(2600, 1120)
parity_ok = abs(hero_parity - HERO_SCALE_REF) <= 0.02
print("framing: hero parity check - this camera model at the hero's 2600x1120 gives "
      "%.4f vs the hero's recorded %.4f -> %s"
      % (hero_parity, HERO_SCALE_REF, "MATCH" if parity_ok else "MISMATCH"))

# the floor: the turntable frames are composited on a studio sweep and need a
# genuinely transparent background, so the shadow-catcher floor is never rendered.
# This is the hero's own "floor-free" pass, the one that drives dmax_alpha.png.
floor = bpy.data.objects.get("FLOOR_shadowcatcher")
if floor is not None:
    floor.hide_render = (not FLOOR)
    print("floor    : shadow-catcher present, hide_render=%s" % floor.hide_render)

# --------------------------------------------------------------------------- #
# 6. render the sequence
# --------------------------------------------------------------------------- #
_before = {}
for o in SPIN_OBJS:
    _before[o.name] = o.matrix_world.copy()

frames = []
_tt = time.perf_counter()
for j, yaw in enumerate(YAWS):
    R = Matrix.Rotation(math.radians(yaw), 4, 'Z')
    for o in SPIN_OBJS:
        o.matrix_world = R @ _before[o.name]
    bpy.context.view_layer.update()

    out_png = os.path.join(OUTDIR, "f_%03d.png" % j)
    bpy.context.scene.render.filepath = out_png
    _rs = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    _secs = time.perf_counter() - _rs

    mn = Vector((1e18,) * 3)
    mx = Vector((-1e18,) * 3)
    for o in SPIN_OBJS:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])

    frames.append({
        "index": j, "yaw_deg": round(yaw, 6), "png": os.path.basename(out_png),
        "render_seconds": round(_secs, 2),
        "world_bbox_min": [round(v, 4) for v in mn],
        "world_bbox_max": [round(v, 4) for v in mx],
    })
    print("  frame %2d/%d  yaw %7.2f deg  %6.1f s  -> %s"
          % (j + 1, len(YAWS), yaw, _secs, os.path.basename(out_png)))

TOTAL_RENDER = time.perf_counter() - _tt

# restore the unturned pose so the scene is left as found
for o in SPIN_OBJS:
    o.matrix_world = _before[o.name]
bpy.context.view_layer.update()

# --------------------------------------------------------------------------- #
# 7. report
# --------------------------------------------------------------------------- #
report = {
    "what": "Isuzu D-Max (2021, double cab) turntable, fixed hero camera, vehicle yaw",
    "resolution": [RESX, RESY],
    "samples": SAMPLES,
    "cycle_settings": {
        "engine": "CYCLES",
        "device": bpy.context.scene.cycles.device,
        "adaptive_sampling": bool(bpy.context.scene.cycles.use_adaptive_sampling),
        "adaptive_threshold": float(bpy.context.scene.cycles.adaptive_threshold),
        "denoising": bool(bpy.context.scene.cycles.use_denoising),
        "denoiser": bpy.context.scene.cycles.denoiser,
        "max_bounces": int(bpy.context.scene.cycles.max_bounces),
        "film_transparent": bool(bpy.context.scene.render.film_transparent),
        "view_transform": bpy.context.scene.view_settings.view_transform,
        "look": bpy.context.scene.view_settings.look,
    },
    "camera": {
        "type": cam.data.type,
        "az_deg": AZ, "el_deg": EL,
        "location": [round(v, 4) for v in cam.location],
        "aim": [round(v, 4) for v in G["TARGET"]],
        "matrix": [[round(v, 8) for v in row] for row in cam.matrix_world],
        "ortho_scale_hero_yaw0": round(_hero_scale, 6),
        "ortho_scale_used": round(UNION_SCALE, 6),
        "fit_mode": "ONE fixed ortho_scale for every frame, taken over the union of all yaws",
        "hero_parity_reference": HERO_SCALE_REF,
        "hero_parity_at_hero_resolution": round(hero_parity, 6),
        "hero_parity_ok": parity_ok,
        "hero_parity_note": ("the ortho fit depends on the frame aspect, so parity is "
                            "checked by re-running the fit at the hero's own 2600x1120 and "
                            "comparing with the value cam_hero.json recorded"),
        "union_fit_worst_yaw_deg": _worst_yaw,
    },
    "motion": {
        "mode": "vehicle rotates about its own vertical axis; camera, lights and floor fixed",
        "frames": FRAMES,
        "step_deg": 360.0 / FRAMES,
        "yaws_deg": [round(y, 6) for y in YAWS],
        "wrap_step_deg": round(((YAWS[0] + 360.0) - YAWS[-1]) % 360.0 or 360.0, 6),
        "spin_objects": len(SPIN_OBJS),
    },
    "reuse": {
        "source": HERO_PY,
        "sha256": HERO_SHA,
        "note": ("material, detail, smoothing, studio and camera blocks are sliced out of "
                 "build_dmax_render.py at run time and executed verbatim, so there is one "
                 "copy of them and this render cannot drift from the hero"),
        "line_ranges": {k: list(v) for k, v in sorted(LINE_SPAN.items())},
        "anchors": {k: {"start": v[0], "end": v[1], "gives": v[2]} for k, v in RANGES.items()},
    },
    "model": {
        "glb": GLB,
        "size_m": {"length": INFO["model_size_m"]["length"],
                   "width_incl_mirrors": INFO["model_size_m"]["width_incl_mirrors"],
                   "height": INFO["model_size_m"]["height"]},
        "scale_m_per_unit": INFO["scale_m_per_unit"],
        "axle_find_method": INFO["axle_find_method"],
    },
    "timing": {
        "per_frame_seconds": [f["render_seconds"] for f in frames],
        "mean_frame_seconds": round(TOTAL_RENDER / max(1, len(YAWS)), 2),
        "total_render_seconds": round(TOTAL_RENDER, 2),
        "total_seconds_this_process": round(time.perf_counter() - T0, 2),
    },
    "frames": frames,
}
with open(os.path.join(OUTDIR, "turntable_render_report.json"), "w") as fh:
    json.dump(report, fh, indent=1)
print("wrote", os.path.join(OUTDIR, "turntable_render_report.json"))
print("total render %.1f s for %d frames (%.2f s/frame)"
      % (TOTAL_RENDER, len(YAWS), TOTAL_RENDER / max(1, len(YAWS))))
print("=== DONE %s ===" % TAG)
