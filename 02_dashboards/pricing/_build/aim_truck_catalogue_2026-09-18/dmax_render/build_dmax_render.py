"""Build and render the Isuzu D-Max hero shot from the free Objaverse GLB.

Run:
  blender --background --python build_dmax_render.py -- --outdir <dir> --tag t1 \
          --samples 400 --resx 2400 --resy 988 --az 76 --el 12

What this does
--------------
* imports the CC-BY "2021 Isuzu D-Max" glTF (Sketchfab 5b4443c2..., mirrored on
  Objaverse; by David_Holiday, CC-BY 4.0)
* measures the axles from the brake-rotor discs and rescales to metres on the
  published 3.125 m wheelbase, cross-checked against the tyre diameter.
  (The previous version found the axles from the rim cloud by y-gap, which this
  model defeats - it carries extra wheel geometry behind the rear axle - and
  every metre was then 6.6% too small.  See dmax_prep.py.)
* reads the load box, the grille band and the plate recesses off the geometry by
  ray casting, and places the badge, plates and small details from those numbers
* replaces the flat SketchUp materials with automotive ones: basecoat + clearcoat
  paint with a procedural micro-flake and a faint panel wave, chrome, tinted
  glass, satin black plastic, rubber, alloy
* builds a studio: PolyHaven photo-studio HDRI + key / fill / top-strip / rim lights
* a shadow-catcher floor gives a soft contact shadow while the film stays
  transparent, so the same render serves as the background-free PNG
* renders RGBA and dumps the orthographic camera so zone hotspots can be
  projected from world metres straight into hero pixels

Nothing here needs an account or a key.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmax_prep as prep                                            # noqa: E402

# --------------------------------------------------------------------------- #
# arguments after the "--"
# --------------------------------------------------------------------------- #
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []


def arg(name, default=None):
    if name in argv:
        return argv[argv.index(name) + 1]
    return default


HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = arg("--outdir", HERE)
TAG = arg("--tag", "test")
SAMPLES = int(arg("--samples", "400"))
RESX = int(arg("--resx", "2400"))
RESY = int(arg("--resy", "988"))
AZ = float(arg("--az", "76"))       # 0 = straight ahead of the truck, 90 = pure side
EL = float(arg("--el", "12"))       # degrees above the horizon
GLB = arg("--glb", os.path.join(HERE, "_assets", "dmax_2021_objaverse.glb"))
PAINT_ARG = arg("--paint", "white")     # white | orange | silver | blue | grey | "r,g,b"
MARGIN = float(arg("--margin", "1.045"))
DETAILS = arg("--details", "1") == "1"

os.makedirs(OUTDIR, exist_ok=True)
RAW = os.path.join(OUTDIR, "_raw")
os.makedirs(RAW, exist_ok=True)

T0 = time.perf_counter()
print("=== build_dmax_render ===")
print("glb     :", GLB)
print("outdir  :", OUTDIR)
print("tag     :", TAG, "samples", SAMPLES, "res", RESX, RESY, "az", AZ, "el", EL)

# --------------------------------------------------------------------------- #
# 1. import, find the axles, scale to metres
# --------------------------------------------------------------------------- #
drawable = prep.import_model(GLB)
print("drawable meshes: %d" % len(drawable))
INFO, DMN, DMX = prep.scale_to_metres(drawable)
SIZE = DMX - DMN
FRONT_AXLE_Y = INFO["front_axle_y"]
REAR_AXLE_Y = INFO["rear_axle_y"]
NOSE_Y, TAIL_Y = INFO["nose_y"], INFO["tail_y"]
LEGACY_SCALE = 0.024016970978185472      # what the previous build used, for the report

# wheel radius from the tyre meshes: half their vertical extent
_tz = [p.z for p in prep.verts_of(drawable, '_Tires', step_target=4000)]
WHEEL_R = (max(_tz) - min(_tz)) / 2.0 if _tz else 0.0
print("front axle y=%.3f  rear axle y=%.3f  tyre r=%.3f m"
      % (FRONT_AXLE_Y, REAR_AXLE_Y, WHEEL_R))

# a world BVH so the details can be placed on measured surfaces.  Only needed
# when details are being built, and it costs ~8 s on 882k triangles, so the
# camera sweep (--details 0) skips it.
if DETAILS:
    CAST = prep.make_caster(*prep.build_bvh(drawable))
    BOX = prep.measure_box(drawable, INFO, CAST)
    FRONT = prep.measure_front(drawable, INFO, CAST)
else:
    CAST = None
    BOX = {}
    FRONT = {}
    print("details off: skipping the BVH and the detail measurements")
SCENE_MEASURED = {
    "box": BOX, "front": FRONT,
    "legacy_scale_m_per_unit": LEGACY_SCALE,
    "scale_correction_pct": 100.0 * (INFO["scale_m_per_unit"] / LEGACY_SCALE - 1.0),
}
print("scale correction vs the previous build: %+.2f%%"
      % SCENE_MEASURED["scale_correction_pct"])

# --------------------------------------------------------------------------- #
# 2. materials.  The SketchUp export arrived as flat untextured shades, so each
#    part is given the values the real part has: this is most of what separates a
#    toy render from a photograph.
# --------------------------------------------------------------------------- #
PAINTS = {
    # linear-space base colours (Blender is linear; these are not sRGB hex)
    "white":  (0.760, 0.772, 0.780, 1.0),   # Splash White pearl
    "silver": (0.400, 0.412, 0.425, 1.0),   # Mercury Silver metallic
    "orange": (0.720, 0.175, 0.045, 1.0),   # Valencia Orange, the model's own Isuzu colour
    "blue":   (0.020, 0.070, 0.210, 1.0),   # Biarritz Blue
    "grey":   (0.100, 0.104, 0.110, 1.0),   # Islay Gray
}
if PAINT_ARG in PAINTS:
    PAINT = PAINTS[PAINT_ARG]
    PAINT_METAL = 0.30 if PAINT_ARG in ("silver", "orange", "blue", "grey") else 0.10
    PAINT_ROUGH = 0.30 if PAINT_ARG in ("silver", "grey") else 0.26
else:
    _r, _g, _b = (float(x) for x in PAINT_ARG.split(","))
    PAINT = (_r, _g, _b, 1.0)
    PAINT_METAL, PAINT_ROUGH = 0.25, 0.28
GLASS = (0.013, 0.016, 0.020, 1.0)     # dark tint; kept opaque so the PNG alpha stays solid
LAMP_GLASS = (0.05, 0.05, 0.055, 1.0)
PEARL = PAINT_ARG in ("white", "silver", "blue")
print("paint: %s  metal %.2f rough %.2f  (pearl/flake %s)"
      % (PAINT_ARG, PAINT_METAL, PAINT_ROUGH, PEARL))


def pset(bsdf, name, value):
    if name in bsdf.inputs:
        bsdf.inputs[name].default_value = value


def nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    bs = next((x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if bs is None:
        bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = next((x for x in nt.nodes if x.type == 'OUTPUT_MATERIAL'), None)
        if out is None:
            out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(bs.outputs[0], out.inputs[0])
    return nt, bs


def add_msurface(nt, bs, *, flake=0.0, wave=0.0, flake_scale=420.0, wave_scale=7.0,
                 tint=0.0):
    """A layered automotive surface: a paint wave plus metal flake.

    Both are procedural, because the model carries no texture atlas.  They are
    deliberately subtle: the flake is a bump on the coat normal (which is what
    makes metallic paint sparkle at the highlight), and the wave is a very shallow
    normal tilt across whole panels, which is what orange peel actually is.

    The BSDF's Normal socket is only connected when at least one layer is asked
    for, so unaffected materials stay untouched.
    """
    nodes_in = [n for n in nt.nodes if n.type in
                ('TEX_NOISE', 'BUMP', 'TEX_COORD', 'MAPPING', 'MIX_RGB', 'VALTORGB')]
    for n in nodes_in:
        nt.nodes.remove(n)
    prev = None
    tc = None
    if flake or wave or tint:
        tc = nt.nodes.new('ShaderNodeTexCoord')
    # ---- panel wave (orange peel): very low frequency, very low strength
    if wave:
        n_wave = nt.nodes.new('ShaderNodeTexNoise')
        n_wave.inputs['Scale'].default_value = wave_scale
        n_wave.inputs['Detail'].default_value = 3.0
        n_wave.inputs['Roughness'].default_value = 0.55
        nt.links.new(tc.outputs['Object'], n_wave.inputs['Vector'])
        b_wave = nt.nodes.new('ShaderNodeBump')
        b_wave.inputs['Strength'].default_value = wave
        b_wave.inputs['Distance'].default_value = 0.012
        nt.links.new(n_wave.outputs['Fac'], b_wave.inputs['Height'])
        prev = b_wave
    # ---- metal flake: high frequency, shallow, on top of the wave
    if flake:
        n_flake = nt.nodes.new('ShaderNodeTexNoise')
        n_flake.inputs['Scale'].default_value = flake_scale
        n_flake.inputs['Detail'].default_value = 6.0
        n_flake.inputs['Roughness'].default_value = 0.72
        nt.links.new(tc.outputs['Object'], n_flake.inputs['Vector'])
        b_flake = nt.nodes.new('ShaderNodeBump')
        b_flake.inputs['Strength'].default_value = flake
        b_flake.inputs['Distance'].default_value = 0.0016
        nt.links.new(n_flake.outputs['Fac'], b_flake.inputs['Height'])
        if prev is not None:
            nt.links.new(prev.outputs['Normal'], b_flake.inputs['Normal'])
        prev = b_flake
    # ---- a faint large-scale base-colour variation, so the panels are not uniform
    if tint:
        n_tint = nt.nodes.new('ShaderNodeTexNoise')
        n_tint.inputs['Scale'].default_value = 3.2
        n_tint.inputs['Detail'].default_value = 2.0
        nt.links.new(tc.outputs['Object'], n_tint.inputs['Vector'])
        # a noise Fac is grey; scale it down so the tint is only a few percent
        m = nt.nodes.new('ShaderNodeMixRGB')
        m.blend_type = 'MULTIPLY'
        m.inputs['Fac'].default_value = 1.0
        m.inputs['Color1'].default_value = tuple(PAINT)
        m.inputs['Color2'].default_value = (1.0 - tint, 1.0 - tint, 1.0 - tint, 1.0)
        nt.links.new(n_tint.outputs['Fac'], m.inputs['Color2'])
        # keep the mean where it was: mix the tinted colour back over the flat one
        mix = nt.nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MIX'
        mix.inputs['Fac'].default_value = 0.5
        mix.inputs['Color1'].default_value = tuple(PAINT)
        nt.links.new(m.outputs['Color'], mix.inputs['Color2'])
        nt.links.new(mix.outputs['Color'], bs.inputs['Base Color'])
    if prev is not None:
        sock = 'Coat Normal' if 'Coat Normal' in bs.inputs else 'Normal'
        nt.links.new(prev.outputs['Normal'], bs.inputs[sock])
    return prev


def restyle(mat):
    """Give one imported material physically sensible values."""
    n = mat.name
    nt, bs = nodes(mat)
    pset(bs, 'Metallic', 0.0)
    pset(bs, 'Roughness', 0.5)
    pset(bs, 'IOR', 1.45)
    pset(bs, 'Coat Weight', 0.0)
    pset(bs, 'Coat Roughness', 0.03)
    pset(bs, 'Transmission Weight', 0.0)
    pset(bs, 'Alpha', 1.0)
    pset(bs, 'Emission Strength', 0.0)
    bs.inputs['Base Color'].default_value = (0.5, 0.5, 0.5, 1.0)

    if 'Valencia' in n:
        # automotive basecoat + clearcoat.  The coat is what makes the highlight
        # read as paint rather than plastic.
        bs.inputs['Base Color'].default_value = PAINT
        pset(bs, 'Metallic', PAINT_METAL)
        pset(bs, 'Roughness', PAINT_ROUGH)
        pset(bs, 'Coat Weight', 1.0)
        pset(bs, 'Coat Roughness', 0.02)
        pset(bs, 'Specular IOR Level', 0.5)
        add_msurface(nt, bs,
                     flake=0.020 if PEARL else 0.012,
                     wave=0.055, flake_scale=520.0, wave_scale=6.0,
                     tint=0.05 if PEARL else 0.03)
    elif 'ChromeTrims' in n:
        # brushed, not mirror: a faint directional roughness so the highlight
        # smears in one direction the way real brightwork does
        bs.inputs['Base Color'].default_value = (0.925, 0.935, 0.945, 1.0)
        pset(bs, 'Metallic', 1.0)
        pset(bs, 'Roughness', 0.085)
        add_msurface(nt, bs, flake=0.0, wave=0.0, tint=0.0)
    elif n.endswith('_Windows') or 'Windows' == n.split('_')[-1]:
        bs.inputs['Base Color'].default_value = GLASS
        pset(bs, 'Metallic', 0.0)
        pset(bs, 'Roughness', 0.012)
        pset(bs, 'IOR', 1.52)
        pset(bs, 'Coat Weight', 1.0)
        pset(bs, 'Coat Roughness', 0.008)
        add_msurface(nt, bs, flake=0.0, wave=0.012, wave_scale=14.0)
    elif 'WindowsTrims' in n:
        bs.inputs['Base Color'].default_value = (0.018, 0.018, 0.020, 1.0)
        pset(bs, 'Roughness', 0.28)
    elif 'HeadLightsGlass' in n:
        bs.inputs['Base Color'].default_value = LAMP_GLASS
        pset(bs, 'Roughness', 0.015)
        pset(bs, 'Coat Weight', 1.0)
        pset(bs, 'Coat Roughness', 0.008)
    elif 'HeadLightsBase' in n:
        bs.inputs['Base Color'].default_value = (0.010, 0.010, 0.012, 1.0)
        pset(bs, 'Roughness', 0.16)
    elif 'BrakeLightsGlass' in n:
        bs.inputs['Base Color'].default_value = (0.085, 0.006, 0.006, 1.0)
        pset(bs, 'Roughness', 0.04)
        pset(bs, 'Coat Weight', 1.0)
    elif n.startswith('2021_Isuzu_Dmax_BrakeLights'):
        bs.inputs['Base Color'].default_value = (0.30, 0.012, 0.010, 1.0)
        pset(bs, 'Roughness', 0.10)
        pset(bs, 'Emission Color', (0.60, 0.030, 0.020, 1.0))
        pset(bs, 'Emission Strength', 0.30)   # tail lamps just awake, as in a press shot
    elif 'DRLs' in n and 'Signal' not in n:
        bs.inputs['Base Color'].default_value = (0.85, 0.87, 0.90, 1.0)
        pset(bs, 'Roughness', 0.05)
        pset(bs, 'Emission Color', (0.85, 0.90, 1.00, 1.0))
        pset(bs, 'Emission Strength', 1.5)    # daytime running lamps on
    elif 'SignalLights' in n:
        bs.inputs['Base Color'].default_value = (0.75, 0.28, 0.02, 1.0)
        pset(bs, 'Roughness', 0.07)
    elif n.endswith('_Tires'):
        bs.inputs['Base Color'].default_value = (0.015, 0.015, 0.016, 1.0)
        pset(bs, 'Roughness', 0.78)
        # a faint mould/release texture so the rubber is not a perfect black mirror
        add_msurface(nt, bs, flake=0.030, wave=0.0, flake_scale=90.0)
    elif 'Rims1' in n:
        bs.inputs['Base Color'].default_value = (0.70, 0.712, 0.728, 1.0)
        pset(bs, 'Metallic', 1.0)
        pset(bs, 'Roughness', 0.20)
        add_msurface(nt, bs, flake=0.010, wave=0.0, flake_scale=260.0)
    elif 'Rims2' in n:
        bs.inputs['Base Color'].default_value = (0.045, 0.045, 0.050, 1.0)
        pset(bs, 'Roughness', 0.32)
    elif 'BrakeRotors1' in n:
        bs.inputs['Base Color'].default_value = (0.50, 0.51, 0.52, 1.0)
        pset(bs, 'Metallic', 1.0)
        pset(bs, 'Roughness', 0.42)
        add_msurface(nt, bs, flake=0.024, wave=0.0, flake_scale=170.0)
    elif 'BrakeRotors' in n or 'BrakePads' in n:
        bs.inputs['Base Color'].default_value = (0.042, 0.042, 0.045, 1.0)
        pset(bs, 'Roughness', 0.68)
    elif 'Calipers' in n:
        bs.inputs['Base Color'].default_value = (0.090, 0.090, 0.095, 1.0)
        pset(bs, 'Metallic', 0.6)
        pset(bs, 'Roughness', 0.40)
    elif 'Mirrors' in n:
        bs.inputs['Base Color'].default_value = (0.028, 0.028, 0.031, 1.0)
        pset(bs, 'Roughness', 0.34)
    elif 'BlackTrims' in n or 'Grille' in n or 'UnderCarrier' in n:
        # the arch liners, the bed liner, the bumper plastics and the grille all
        # live on this material, so it sets the darkest surfaces on the vehicle.
        # Kept a little rougher and darker than before so the wheel wells read as
        # deep shadow rather than as grey plastic.
        bs.inputs['Base Color'].default_value = (0.020, 0.020, 0.022, 1.0)
        pset(bs, 'Roughness', 0.52)
        add_msurface(nt, bs, flake=0.035, wave=0.0, flake_scale=60.0)
    elif 'Default_Material' in n:
        bs.inputs['Base Color'].default_value = (0.040, 0.040, 0.043, 1.0)
        pset(bs, 'Roughness', 0.62)
    elif 'Sticker' in n:
        bs.inputs['Base Color'].default_value = (0.60, 0.61, 0.62, 1.0)
        pset(bs, 'Metallic', 0.9)
        pset(bs, 'Roughness', 0.12)


for mat in bpy.data.materials:
    restyle(mat)
print("materials restyled:", len(bpy.data.materials))


def new_material(name, base, metallic=0.0, rough=0.4, coat=0.0, coat_rough=0.03,
                 emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, bs = nodes(m)
    bs.inputs['Base Color'].default_value = tuple(base) + (1.0,)
    pset(bs, 'Metallic', metallic)
    pset(bs, 'Roughness', rough)
    pset(bs, 'Coat Weight', coat)
    pset(bs, 'Coat Roughness', coat_rough)
    if emission:
        pset(bs, 'Emission Color', tuple(emission) + (1.0,))
        pset(bs, 'Emission Strength', emission_strength)
    return m


MAT_BADGE = new_material("DMAX_badge_chrome", (0.885, 0.895, 0.905),
                         metallic=1.0, rough=0.055)
MAT_PLATE_FACE = new_material("DMAX_plate_face", (0.845, 0.845, 0.838),
                              metallic=0.0, rough=0.42, coat=0.25, coat_rough=0.06)
MAT_PLATE_FRAME = new_material("DMAX_plate_frame", (0.020, 0.020, 0.022),
                               metallic=0.0, rough=0.55)
MAT_RUBBER = new_material("DMAX_wiper_rubber", (0.020, 0.020, 0.021),
                          metallic=0.0, rough=0.72)
MAT_SATIN = new_material("DMAX_satin_black", (0.022, 0.022, 0.024),
                         metallic=0.0, rough=0.38)
MAT_GRILLE_DARK = new_material("DMAX_grille_dark", (0.0165, 0.0165, 0.018),
                               metallic=0.0, rough=0.44)
MAT_PAINT = bpy.data.materials.get('2021_Isuzu_Dmax_Valencia_Orange')

# --------------------------------------------------------------------------- #
# 3. detail geometry, placed from the measured anchors
# --------------------------------------------------------------------------- #
ADDED = []


def _link(ob):
    if ob.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(ob)
    ADDED.append(ob)
    return ob


def box(name, centre, size, mat, rot=None, bevel=0.0):
    """An axis-aligned box (optionally rotated) as a simple primitive."""
    sx, sy, sz = size
    me = bpy.data.meshes.new(name)
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    vs = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
          (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    fs = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
          (2, 6, 7, 3), (3, 7, 4, 0)]
    me.from_pydata(vs, [], fs)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = Vector(centre)
    if rot:
        ob.rotation_euler = rot
    me.materials.append(mat)
    return _link(ob)


def disc(name, centre, radius, depth, mat, rot=None, verts=48, hollow=None):
    """A shallow cylinder, i.e. a disc with thickness."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=centre)
    ob = bpy.context.active_object
    ob.name = name
    if rot:
        ob.rotation_euler = rot
    ob.data.materials.append(mat)
    return _link(ob)


def wordmark(text, size, extrude, mat, centre, rot=(math.radians(90), 0.0, 0.0),
             spacing=1.0):
    """Real extruded letterforms, converted to mesh."""
    bpy.ops.object.text_add()
    ob = bpy.context.active_object
    ob.name = "badge_%s" % text
    ob.data.body = text
    ob.data.size = size
    ob.data.extrude = extrude
    ob.data.align_x = 'CENTER'
    ob.data.align_y = 'CENTER'
    ob.data.space_character = spacing
    ob.rotation_euler = rot
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.active_object
    ob.location = Vector(centre)
    ob.data.materials.append(mat)
    return _link(ob)


def surface_y(x, z, default):
    """The forward-most surface at (x, z) - used to sit details on the nose.

    Cast from behind the nose going forward is wrong (it hits interior first), so
    cast from OUTSIDE the vehicle inwards: the first hit is the front face.
    """
    loc, _, _ = CAST((x, NOSE_Y - 0.5, z), (0, 1, 0))
    return loc.y if loc else default


def surface_y_rear(x, z, default):
    """The rearmost surface at (x, z) - the outer face of the tailgate."""
    loc, _, _ = CAST((x, TAIL_Y + 0.5, z), (0, -1, 0))
    return loc.y if loc else default


def surface_z_on_bonnet(x, y, default):
    """The bonnet / cowl surface height at (x, y), found from above."""
    loc, _, _ = CAST((x, y, 2.2), (0, 0, -1))
    return loc.z if loc else default


if DETAILS:
    # ---- ISUZU wordmark on the grille.  The model's badge is a material split on
    #      the grille face, so it is smooth: real extruded letters give it an edge
    #      to catch the light, which is what makes a badge read at all.
    #
    #      Rectangular allocation plate behind it: the model puts the badge inside
    #      a moulded recess whose left and right thirds are raised, so a wide flat
    #      face over the whole bar would sit proud of that step.  A recess-filling
    #      plate makes the letters sit on a flat, correctly-shaded background and
    #      keeps the grille's own step visible at its edge.
    gz = FRONT.get("grille_z_range") or [0.70, 1.08]
    badge_z = gz[0] + (gz[1] - gz[0]) * 0.80
    badge_y = surface_y(0.0, badge_z, NOSE_Y + 0.02)
    # find the width of the raised centre section by stepping outwards
    hw = 0.06
    for x in [0.02 * i for i in range(1, 18)]:
        yx = surface_y(x, badge_z, badge_y)
        if abs(yx - badge_y) > 0.012:
            break
        hw = x
    plate_w = min(0.34, hw * 2.0 + 0.03)
    # dark backing plate, so the chrome letters have something to read against -
    # on the real truck the wordmark sits on the dark grille, not on brightwork
    box("badge_plate", (0.0, badge_y - 0.0055, badge_z), (plate_w, 0.011, 0.062),
        MAT_GRILLE_DARK)
    wordmark("ISUZU", 0.086, 0.009, MAT_BADGE,
             (0.0, badge_y - 0.014, badge_z), spacing=1.14)
    print("badge: ISUZU wordmark on a %.3f m plate at y=%.3f z=%.3f"
          % (plate_w, badge_y - 0.014, badge_z))

    # ---- number plates.  Deliberately blank: no registration number is invented,
    #      and no distributor branding goes on them.
    for tag, yface, zc, sy in (
            ("front", surface_y(0.0, 0.548, NOSE_Y + 0.02), 0.548, -1),
            ("rear", surface_y_rear(0.0, 0.615, TAIL_Y - 0.02), 0.615, +1)):
        pw, ph, pt = 0.470, 0.104, 0.012
        box("plate_%s_frame" % tag, (0.0, yface - sy * (pt / 2.0), zc),
            (pw + 0.018, pt, ph + 0.016), MAT_PLATE_FRAME)
        box("plate_%s_face" % tag, (0.0, yface - sy * (pt - 0.0035), zc),
            (pw, pt * 0.5, ph), MAT_PLATE_FACE)
        print("plate %-5s face y=%.3f z=%.3f  %.0f x %.0f mm" % (tag, yface, zc,
                                                                 pw * 1000, ph * 1000))

    # ---- door handles: four, just under the beltline, front and rear doors each side
    glass_z = []
    for o in drawable:
        if not any(m.endswith('_Windows') for m in prep.mats(o)):
            continue
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            if abs(w.x) > 0.45 and -1.10 < w.y < 0.80:
                glass_z.append(w.z)
    belt_z = min(glass_z) if glass_z else 1.262
    handle_z = belt_z - 0.085
    for xf in (-1, +1):
        for yc in (-0.05, 0.66):
            xs = CAST((3.0 * xf, yc, handle_z), (-xf, 0, 0))[0]
            xface = xs.x if xs is not None else xf * 0.86
            box("handle_%s_%.2f" % ("L" if xf < 0 else "R", yc),
                (xface + xf * 0.009, yc, handle_z), (0.022, 0.165, 0.028), MAT_BADGE)
    print("door handles at beltline z=%.3f, handle z=%.3f" % (belt_z, handle_z))

    # ---- windscreen wipers: two thin blades lying on the cowl, angled as on the
    #      real truck.  Sunk very slightly so they sit in the surface, not on it.
    cowl_z = surface_z_on_bonnet(0.0, -1.30, 1.30)
    for xc, ln, ang in ((-0.36, 0.60, 8.0), (0.18, 0.50, -6.0)):
        zc = surface_z_on_bonnet(xc, -1.30, cowl_z)
        box("wiper_%.2f" % xc, (xc, -1.30, zc - 0.002),
            (0.013, ln, 0.010), MAT_RUBBER,
            rot=(0.0, 0.0, math.radians(ang)))
    print("wipers on the cowl at z=%.3f, y=-1.30" % cowl_z)

    # ---- fuel filler doors, one each side, just behind the cab
    for xf in (-1, +1):
        xs = CAST((3.0 * xf, 1.02, 1.02), (-xf, 0, 0))[0]
        xface = xs.x if xs is not None else xf * 0.86
        disc("fuel_%s" % ("L" if xf < 0 else "R"),
             (xface + xf * 0.0015, 1.02, 1.02), 0.052, 0.004,
             MAT_PAINT if MAT_PAINT else MAT_SATIN,
             rot=(0.0, math.radians(90), 0.0))
    print("fuel filler discs at y=1.02 z=1.02")

    print("detail objects added: %d" % len(ADDED))
else:
    print("details disabled")

# --------------------------------------------------------------------------- #
# 4. shading: SketchUp geometry arrives faceted.  Smooth it with an angle
#    threshold so panels curve but hard edges and panel gaps stay crisp.
# --------------------------------------------------------------------------- #
bpy.ops.object.select_all(action='DESELECT')
for o in drawable:
    o.select_set(True)
bpy.context.view_layer.objects.active = drawable[0]
try:
    bpy.ops.object.shade_auto_smooth(angle=math.radians(31.0))
    print("shade_auto_smooth applied (31 deg)")
except Exception as exc:                                     # older operator name
    print("shade_auto_smooth unavailable (%s); using shade_smooth" % exc)
    bpy.ops.object.shade_smooth()
    for o in drawable:
        o.data.use_auto_smooth = True
        o.data.auto_smooth_angle = math.radians(31.0)

# the added details want their own smoothing: the extruded letters are already
# faceted enough, the boxes must stay flat
for o in ADDED:
    for p in o.data.polygons:
        p.use_smooth = False

# --------------------------------------------------------------------------- #
# 5. studio
# --------------------------------------------------------------------------- #
scene = bpy.context.scene
world = bpy.data.worlds.new("studio")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
wnt.nodes.clear()
wout = wnt.nodes.new('ShaderNodeOutputWorld')
wbg = wnt.nodes.new('ShaderNodeBackground')
HDRI = os.path.join(HERE, "_assets", "photo_studio_01_2k.hdr")
if os.path.exists(HDRI):
    tenv = wnt.nodes.new('ShaderNodeTexEnvironment')
    tenv.image = bpy.data.images.load(HDRI, check_existing=True)
    wnt.links.new(tenv.outputs['Color'], wbg.inputs['Color'])
    wbg.inputs['Strength'].default_value = 0.50
    print("world: HDRI", os.path.basename(HDRI))
else:
    wbg.inputs['Color'].default_value = (0.5, 0.5, 0.52, 1.0)
    wbg.inputs['Strength'].default_value = 0.6
    print("world: flat grey (HDRI missing)")
wnt.links.new(wbg.outputs[0], wout.inputs[0])

scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for dt in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = dt
            prefs.get_devices()
            if any(d.type == dt for d in prefs.devices):
                print("cycles compute:", dt)
                break
        except Exception:
            continue
    for d in prefs.devices:
        d.use = True
except Exception as exc:
    print("could not set compute device:", exc)

scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.008
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
scene.cycles.max_bounces = 14
scene.cycles.diffuse_bounces = 5
scene.cycles.glossy_bounces = 8
scene.cycles.transmission_bounces = 8
scene.cycles.transparent_max_bounces = 10
scene.cycles.use_light_tree = True
scene.render.film_transparent = True
scene.render.resolution_x = RESX
scene.render.resolution_y = RESY
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '16'
# 16-bit PNGs are linear by spec.  The view transform stays as the accepted
# build had it: AgX with the Punchy look, applied here in Blender.  Changing it
# was tried and made the paint read hazier, so it is left alone.
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Punchy'
scene.view_settings.exposure = 0.0

# ---- lights ---------------------------------------------------------------
L = SIZE.y          # ~5 m, so light distances scale with the vehicle


def area_light(name, loc, aim, size_x, size_y, power, shape='RECTANGLE', spread=math.pi,
               color=(1, 1, 1)):
    d = bpy.data.lights.new(name, 'AREA')
    d.shape = shape
    d.size = size_x
    if shape == 'RECTANGLE':
        d.size_y = size_y
    d.energy = power
    d.color = color
    d.spread = spread
    ob = bpy.data.objects.new(name, d)
    scene.collection.objects.link(ob)
    ob.location = Vector(loc)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y')
    return ob


# key: big softbox, high on the front-left of the truck, the shape that draws the
# long highlight down the shoulder line
KEY = area_light("KEY", (-3.6 * L / 5.0, -3.3, 3.3 * L / 5.0), (0, 0, 0.75), 4.6, 3.2, 2400)
# fill: wide and dim, opposite side, keeps the shadow side readable
FILL = area_light("FILL", (4.6 * L / 5.0, -1.9, 1.5 * L / 5.0), (0, 0, 0.7), 4.4, 3.4, 700)
# top strip: long thin softbox straight overhead, the classic car-shot ceiling light
TOP = area_light("TOP", (-0.4, 0.6, 3.5 * L / 5.0), (0, 0, 0.7), 1.1, 6.5, 1500)
# rim: narrow strip behind and above, separates the roof and bed rail from the wall
RIM = area_light("RIM", (-1.4, 3.9, 2.5 * L / 5.0), (0, 0.3, 0.8), 0.7, 4.0, 1100)
print("lights: KEY FILL TOP RIM")

# ---- shadow catcher floor -------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "FLOOR_shadowcatcher"
mat = bpy.data.materials.new("floor_shadow")
mat.use_nodes = True
_b = next(x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
_b.inputs['Base Color'].default_value = (0.55, 0.55, 0.56, 1.0)
_b.inputs['Roughness'].default_value = 0.60
floor.data.materials.append(mat)
floor.is_shadow_catcher = True

# --------------------------------------------------------------------------- #
# 6. camera.  Orthographic, so the render is a measured projection and the zone
#    hotspots can be computed exactly instead of eyeballed.
# --------------------------------------------------------------------------- #
cam_data = bpy.data.cameras.new("HERO_CAM")
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new("HERO_CAM", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

TARGET = Vector((0.0, 0.0, SIZE.z * 0.46))
az_r = math.radians(AZ)
el_r = math.radians(EL)
DIST = 16.0
cam.location = TARGET + Vector((math.sin(az_r) * math.cos(el_r) * DIST,
                                -math.cos(az_r) * math.cos(el_r) * DIST,
                                math.sin(el_r) * DIST))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (TARGET - cam.location).to_track_quat('-Z', 'Y')


def fit_ortho(cam, objs, resx, resy, margin):
    """Frame the vehicle: project every mesh corner through the camera and fit."""
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
    # ortho_scale spans the wider axis; the height available is scale*aspect
    need = max(u * 2.0 / 0.98, (v * 2.0) / (0.98 * aspect))
    cam_data.ortho_scale = need * margin
    return cam_data.ortho_scale


FRAMING_MATS = ('Valencia', 'Grille', 'Windows', 'Tires', 'BrakeLights', 'DRLs',
                'HeadLights', 'BlackTrims', 'ChromeTrims', 'Mirrors', 'Rims')
framing = [o for o in drawable
           if any(any(f in s.material.name for f in FRAMING_MATS)
                  for s in o.material_slots if s.material)] or drawable
scale_used = fit_ortho(cam, framing, RESX, RESY, MARGIN)
print("ortho_scale: %.4f" % scale_used)
print("camera loc : %.3f %.3f %.3f" % tuple(cam.location))
print("camera aim : %.3f %.3f %.3f" % tuple(TARGET))

# --------------------------------------------------------------------------- #
# 7. world-space landmarks, for the hotspot projection
# --------------------------------------------------------------------------- #
def project(p):
    """world metres -> hero pixel (x, y), top-left origin."""
    pc = cam.matrix_world.inverted() @ Vector(p)
    half_w = cam.data.ortho_scale / 2.0
    half_h = half_w * RESY / RESX
    px = (pc.x / half_w * 0.5 + 0.5) * RESX
    py = (0.5 - pc.y / half_h * 0.5) * RESY
    return (round(px, 1), round(py, 1))


def band_bounds(pred, ylo, yhi):
    """World-space z range of the meshes matching pred, inside a y window."""
    zs = []
    for o in drawable:
        names = prep.mats(o)
        if not any(pred(n) for n in names):
            continue
        vs = o.data.vertices
        step = max(1, len(vs) // 4000)
        for i in range(0, len(vs), step):
            w = o.matrix_world @ vs[i].co
            if ylo <= w.y <= yhi:
                zs.append(w.z)
    return (min(zs), max(zs)) if zs else None


BONNET_TOP = band_bounds(lambda n: 'Valencia' in n, FRONT_AXLE_Y - 0.1,
                         FRONT_AXLE_Y + 0.35)
BED_TOP = band_bounds(lambda n: 'Valencia' in n, REAR_AXLE_Y + 0.15,
                      REAR_AXLE_Y + 0.60)
TAILLAMP = band_bounds(lambda n: 'BrakeLights' in n, TAIL_Y - 1.3, TAIL_Y + 0.5)
HEADLAMP = band_bounds(lambda n: 'HeadLights' in n, NOSE_Y - 0.5, NOSE_Y + 1.1)
WIN = band_bounds(lambda n: n.endswith('_Windows'), NOSE_Y, TAIL_Y)
print("bonnet z %s  bed rail z %s  headlamp z %s  taillamp z %s"
      % (BONNET_TOP, BED_TOP, HEADLAMP, TAILLAMP))

# body width excluding the mirrors: painted flank plus the arch flares
_paint_x = []
for _o in drawable:
    _n = prep.mats(_o)
    if not any(('Valencia' in x or 'BlackTrims' in x) for x in _n):
        continue
    for _c in _o.bound_box:
        _paint_x.append((_o.matrix_world @ Vector(_c)).x)
body_width = (max(_paint_x) - min(_paint_x)) if _paint_x else None
print("body width excl mirrors: %.3f m (overall incl mirrors %.3f m)"
      % (body_width or float('nan'), SIZE.x))

# --------------------------------------------------------------------------- #
# 8. render
# --------------------------------------------------------------------------- #
out_png = os.path.join(RAW, "rgba_%s.png" % TAG)
scene.render.filepath = out_png
print("rendering ->", out_png)
_rs = time.perf_counter()
bpy.ops.render.render(write_still=True)
render_seconds = time.perf_counter() - _rs
print("render finished in %.1f s" % render_seconds)

# Second pass with the shadow catcher hidden.  The floor is what puts the contact
# shadow into the alpha channel, but it also fogs the whole background with a faint
# veil (the HDRI lights the floor, and a shadow catcher still returns that light as
# partial alpha).  That veil is fine under the hero, which has a studio background
# to lay it on, but it is wrong for a compositing PNG: a transparent background must
# really be transparent.  So the shadow-carrying pass drives the hero, and this
# floor-free pass drives dmax_alpha.png.
clean_png = os.path.join(RAW, "rgba_%s_nofoor.png" % TAG)
floor.hide_render = True
scene.render.filepath = clean_png
print("rendering (no floor) ->", clean_png)
_cs = time.perf_counter()
bpy.ops.render.render(write_still=True)
clean_seconds = time.perf_counter() - _cs
floor.hide_render = False
print("clean render finished in %.1f s" % clean_seconds)

# --------------------------------------------------------------------------- #
# 9. emit the camera + measurements for the composing and hotspot steps
# --------------------------------------------------------------------------- #
probe = []
for label, p in (("nose_ground", (0.0, NOSE_Y, 0.0)),
                 ("nose_top", (0.0, NOSE_Y, SIZE.z)),
                 ("tail_ground", (0.0, TAIL_Y, 0.0)),
                 ("tail_top", (0.0, TAIL_Y, SIZE.z)),
                 ("front_axle_ground", (0.0, FRONT_AXLE_Y, 0.0)),
                 ("rear_axle_ground", (0.0, REAR_AXLE_Y, 0.0)),
                 ("body_left", (-SIZE.x / 2, NOSE_Y, SIZE.z * 0.5)),
                 ("body_right", (SIZE.x / 2, NOSE_Y, SIZE.z * 0.5)),
                 ("bonnet_front", (SIZE.x / 2, NOSE_Y + 0.62, 1.15)),
                 ("bed_rail_front", (SIZE.x / 2, TAIL_Y - 0.35, 1.25)),
                 ("roof_mid", (0.0, 0.0, 1.65)),
                 ("sill_mid", (SIZE.x / 2, 0.0, 0.30))):
    probe.append({"name": label, "world": list(p), "px": project(p)})

report = {
    "tag": TAG, "res": [RESX, RESY], "az_deg": AZ, "el_deg": EL,
    "samples": SAMPLES, "ortho_scale": scale_used,
    "camera_location": list(cam.location), "camera_aim": list(TARGET),
    "camera_matrix": [list(r) for r in cam.matrix_world],
    "clean_render_png": clean_png if os.path.exists(clean_png) else None,
    "render_seconds": render_seconds, "clean_render_seconds": clean_seconds,
    "scale_m_per_unit": INFO["scale_m_per_unit"],
    "units_wheelbase": INFO["units_wheelbase"],
    "axle_find_method": INFO["axle_find_method"],
    "scale_from_tyre_diameter": INFO["scale_from_tyre_diameter"],
    "scale_methods_agree_pct": INFO["scale_methods_agree_pct"],
    "legacy_scale_m_per_unit": LEGACY_SCALE,
    "scale_correction_pct": SCENE_MEASURED["scale_correction_pct"],
    "model_size_m": {"length": SIZE.y, "width_incl_mirrors": SIZE.x, "height": SIZE.z},
    "body_width_m": body_width,
    "unit": "m",
    "real_spec_m": prep.SPEC,
    "front_axle_y": FRONT_AXLE_Y, "rear_axle_y": REAR_AXLE_Y, "wheel_radius_m": WHEEL_R,
    "y_nose": NOSE_Y, "y_tail": TAIL_Y, "x_side": (body_width or 1.9) / 2.0,
    "box_measured": BOX,
    "front_measured": FRONT,
    "measured": {"bonnet_top_z": BONNET_TOP, "bed_rail_z": BED_TOP,
                 "headlamp_z": HEADLAMP, "taillamp_z": TAILLAMP, "windows_z": WIN},
    "details_added": [o.name for o in ADDED],
    "probe": probe,
}
with open(os.path.join(RAW, "cam_%s.json" % TAG), "w") as f:
    json.dump(report, f, indent=1)
print("wrote", os.path.join(RAW, "cam_%s.json" % TAG))
print("total build time %.1f s" % (time.perf_counter() - T0))
print("=== DONE %s ===" % TAG)
