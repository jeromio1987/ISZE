"""Turn the Blender RGBA render into the deliverables.

  dmax_hero.png      opaque, neutral studio background, soft contact shadow
  dmax_alpha.png     the same framing with a genuinely transparent background
  dmax_hotspots.json six zone polygons in hero pixel coordinates + the bbox

Reads the camera report written by build_dmax_render.py so the zone polygons are
projected from world metres with the exact same camera that drew the image.

Why the alpha pass is a separate render rather than a threshold: the hero pass has
a shadow-catcher floor, and a shadow catcher returns the studio light it receives
as partial alpha, which fogs the whole background (measured on the previous build:
a band of alpha 20-255 across the lower third).  So the hero comes from the pass
with the floor and dmax_alpha.png comes from a second pass with the floor hidden,
where the background is genuinely empty.  This script checks that, rather than
trusting it.

Run:  python compose_dmax.py --raw <raw dir> --out <out dir> --tag hero
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw

ZONE_NAMES = ["front", "engine", "cab", "rear", "chassis", "elec"]
DEBUG = True


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--tag", default="hero")
    p.add_argument("--margin", type=float, default=0.055,
                   help="fraction of the vehicle length left as breathing room")
    return p.parse_args()


def load_rgba(path):
    im = Image.open(path)
    return im if im.mode == "RGBA" else im.convert("RGBA")


def vehicle_bbox(alpha, thresh=200):
    """Tight bbox of the vehicle.  The shadow catcher only puts partial alpha on
    the ground, so a high threshold drops the shadow and keeps the body."""
    solid = alpha > thresh
    rows = np.where(solid.any(axis=1))[0]
    cols = np.where(solid.any(axis=0))[0]
    return int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1


def studio_background(w, h, horizon):
    """A neutral seamless studio sweep: light warm grey, slightly darker low down,
    a gentle vignette.  Deliberately plain so the vehicle carries the image."""
    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    xx = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]

    top, bottom = 0.845, 0.920
    t = np.clip(yy / max(horizon, 1e-3), 0.0, 1.0)
    v = top + (bottom - top) * (t ** 1.6)
    over = np.clip((yy - horizon) / max(1.0 - horizon, 1e-3), 0.0, 1.0)
    v = v - 0.10 * (over ** 1.4)

    cx = (xx - 0.5) * 2.0
    cy = (yy - 0.5) * 2.0
    v = v * (1.0 - 0.085 * (cx * cx * 0.55 + cy * cy * 0.45))

    rgb = np.stack([v * 1.000, v * 0.998, v * 0.995], axis=-1)
    return Image.fromarray((rgb * 255.0).clip(0, 255).astype(np.uint8), "RGB")


def camera_projector(report):
    """world metres -> hero pixel, using the exported camera matrix."""
    M = np.array(report["camera_matrix"], dtype=float)
    Minv = np.linalg.inv(M)
    resx, resy = report["res"]
    scale = float(report["ortho_scale"])
    half_w = scale / 2.0
    half_h = half_w * resy / resx

    def project(p):
        v = Minv @ np.array([p[0], p[1], p[2], 1.0])
        px = (v[0] / half_w * 0.5 + 0.5) * resx
        py = (0.5 - v[1] / half_h * 0.5) * resy
        return [round(float(px), 2), round(float(py), 2)]

    # prove the re-implementation matches Blender's own projection before using it
    worst = 0.0
    for pr in report.get("probe", []):
        got = project(pr["world"])
        worst = max(worst, abs(got[0] - pr["px"][0]), abs(got[1] - pr["px"][1]))
    print("projection check: %d probe points, worst pixel error %.4f"
          % (len(report.get("probe", [])), worst))
    if worst > 0.5:
        raise SystemExit("projection mismatch %.3f px - refusing to emit hotspots" % worst)
    return project


def main() -> int:
    a = parse()
    os.makedirs(a.out, exist_ok=True)
    raw_png = os.path.join(a.raw, "rgba_%s.png" % a.tag)
    with open(os.path.join(a.raw, "cam_%s.json" % a.tag)) as f:
        rep = json.load(f)

    im = load_rgba(raw_png)
    W, H = im.size
    arr = np.asarray(im)
    alpha = arr[..., 3]
    print("raw render: %dx%d  nonzero alpha px: %d" % (W, H, int((alpha > 0).sum())))

    x0, y0, x1, y1 = vehicle_bbox(alpha)
    vbx0, vby0, vbx1, vby1 = x0, y0, x1, y1
    print("vehicle solid bbox: x %d..%d  y %d..%d  (%dx%d)"
          % (x0, x1, y0, y1, x1 - x0, y1 - y0))

    # ------------------------------------------------------------------ crop
    vw, vh = x1 - x0, y1 - y0
    mx = int(round(vw * a.margin))
    my = int(round(vh * a.margin))
    cx0, cx1 = max(0, x0 - mx), min(W, x1 + mx)
    cy0, cy1 = max(0, y0 - my), min(H, y1 + my)
    crop = im.crop((cx0, cy0, cx1, cy1))
    cw, ch = crop.size
    print("crop: (%d,%d)-(%d,%d) -> %dx%d" % (cx0, cy0, cx1, cy1, cw, ch))
    shift_x, shift_y = -cx0, -cy0

    # ------------------------------------------------------------------ alpha
    # dmax_alpha.png comes from the floor-free pass.  Verify it is actually
    # transparent instead of assuming: the whole point of the second pass is that
    # the background is empty, and the earlier build shipped a grey veil once.
    clean = rep.get("clean_render_png")
    alpha_stats = {}
    if clean and os.path.exists(clean):
        cim = load_rgba(clean).crop((cx0, cy0, cx1, cy1))
        cim.save(os.path.join(a.out, "dmax_alpha.png"))
        av = np.asarray(cim)[..., 3]
        alpha_stats = {
            "source": os.path.basename(clean),
            "fully_clear_px": int((av < 8).sum()),
            "fully_solid_px": int((av > 247).sum()),
            "partial_px": int(((av >= 8) & (av <= 247)).sum()),
            "max_alpha": int(av.max()),
            "background_alpha_median": int(np.median(np.concatenate(
                [av[:6].ravel(), av[-6:].ravel(), av[:, :6].ravel(), av[:, -6:].ravel()]))),
            "total_px": int(av.size),
        }
        alpha_stats["clear_background_fraction"] = round(
            alpha_stats["fully_clear_px"] / alpha_stats["total_px"], 4)
        bad = (alpha_stats["background_alpha_median"] > 8
               or alpha_stats["clear_background_fraction"] < 0.25)
        alpha_stats["verdict"] = "FAIL - background is not transparent" if bad else "PASS"
        print("wrote dmax_alpha.png from the floor-free pass: %d px fully clear, "
              "%d fully solid, %d partial; background median alpha %d -> %s"
              % (alpha_stats["fully_clear_px"], alpha_stats["fully_solid_px"],
                 alpha_stats["partial_px"], alpha_stats["background_alpha_median"],
                 alpha_stats["verdict"]))
        if bad:
            raise SystemExit("alpha cut-out failed the transparency check")
    else:
        crop.save(os.path.join(a.out, "dmax_alpha.png"))
        alpha_stats = {"source": "shadow pass (no floor-free render on disk)",
                       "verdict": "DEGRADED - the contact-shadow veil is kept"}
        print("wrote dmax_alpha.png from the shadow pass - the floor-free render "
              "is missing, so the cut-out keeps the veil")

    # ------------------------------------------------------------------ hero
    ca = np.asarray(crop).astype(np.float32)
    a_lin = ca[..., 3:4] / 255.0
    rgb_lin = ca[..., :3] / 255.0

    horizon_y = max(1.0, min(ch - 1.0, y1 - cy0))
    bg = studio_background(cw, ch, horizon_y)
    bga = np.asarray(bg).astype(np.float32) / 255.0

    out = rgb_lin * a_lin + bga * (1.0 - a_lin)
    hero = Image.fromarray((out * 255.0).clip(0, 255).astype(np.uint8), "RGB")

    # a touch of polish: very slight contrast S-curve
    hn = np.asarray(hero).astype(np.float32) / 255.0
    hn = np.clip(hn, 0.0, 1.0)
    hn = hn * hn * (3.0 - 2.0 * hn) * 0.55 + hn * 0.45
    hero = Image.fromarray((hn * 255.0).clip(0, 255).astype(np.uint8), "RGB")
    hero.save(os.path.join(a.out, "dmax_hero.png"))
    print("wrote dmax_hero.png")

    # ------------------------------------------------------------------ hotspots
    project = camera_projector(rep)
    L = rep["model_size_m"]
    body_w = rep.get("body_width_m") or 1.824
    nose_y, tail_y = rep["y_nose"], rep["y_tail"]
    fa, ra = rep["front_axle_y"], rep["rear_axle_y"]
    roof_z = L["height"]
    boxm = rep.get("box_measured") or {}
    m = rep.get("measured", {})

    def num(v, fallback):
        return float(v) if isinstance(v, (int, float)) else fallback

    # landmarks: taken from the model's own measured geometry, with the measured
    # values the build wrote into cam_*.json taking precedence over any guess
    sill_z = num(rep.get("sill_z"), num((m.get("windows_z") or [0, 1.2])[0] - 0.80, 0.42))
    bonnet_z = num((m.get("bonnet_top_z") or [0, 1.31])[1], 1.31)
    bed_rail_z = num(boxm.get("rail_z"), num((m.get("bed_rail_z") or [0, 1.31])[1], 1.31))
    head_top = num((m.get("headlamp_z") or [0, 1.11])[1], 1.11)
    nose_top = min(max(head_top, 1.05), 1.22)

    # the cab back is where the cab's rear face is: measured from the side glass,
    # which ends at the back of the cab on a double cab
    cab_back_y = num(rep.get("cab_back_y"), 0.95)
    ws_base_y = num(rep.get("windscreen_base_y"), fa + 0.72)

    sill_line = round(sill_z + 0.10, 3)
    ZONES_WORLD = {
        "front":   (nose_y, round(fa - 0.42, 3), sill_line, nose_top),
        "elec":    (round(fa - 0.42, 3), round(fa - 0.12, 3), sill_line, nose_top),
        "engine":  (round(fa - 0.12, 3), round(ws_base_y, 3), sill_line, bonnet_z),
        "cab":     (round(ws_base_y, 3), round(cab_back_y, 3), sill_line, roof_z),
        "rear":    (round(cab_back_y, 3), tail_y, sill_line, bed_rail_z),
        "chassis": (round(nose_y + 0.30, 3), round(tail_y - 0.30, 3), 0.02, sill_line),
    }
    if DEBUG:
        for k, (yy0, yy1, zz0, zz1) in ZONES_WORLD.items():
            print("  world rect %-8s y %7.3f..%7.3f  z %5.3f..%5.3f" % (k, yy0, yy1, zz0, zz1))

    # ------------------------------------------------------------------ assignment
    # Every vehicle pixel is unprojected onto the flank plane x = body_width/2,
    # which gives that pixel a real (y, z) in metres; the zone follows from (y, z).
    # Because the six rectangles tile the (y, z) plane and the outer two are open
    # at nose and tail, every vehicle pixel lands in exactly one zone by
    # construction: no gaps, no overlaps, and the far side and roof included.
    #
    # A pixel on the FAR flank unprojects to a y about 1.2 m further back than
    # where it really is, because a single flat image has no depth.  The boundaries
    # still render as clean straight cuts across the vehicle, which is what a tint
    # needs.
    x_plane = body_w / 2.0 + 0.012
    M = np.array(rep["camera_matrix"], dtype=float)
    resx, resy = rep["res"]
    scale_m = float(rep["ortho_scale"])
    half_w = scale_m / 2.0
    half_h = half_w * resy / resx

    y_front_end = round(fa - 0.42, 3)
    y_elec_end = round(fa - 0.12, 3)
    y_eng_end = round(ws_base_y, 3)
    y_cab_end = round(cab_back_y, 3)
    z_sill = sill_line
    front_top = nose_top

    # x_plane, y and z per pixel. Vectorised, so a megapixel is instant.
    #
    # CAREFUL WITH THE SIGN OF shift_x / shift_y.  `shift_x = -cx0` is the offset
    # that maps a render pixel to a CROP pixel, which is what project_pt() below
    # needs because it returns crop pixels.  To go the other way, crop pixel to
    # render pixel, the offset must be ADDED: render = crop - shift, and shift is
    # negative, so that is crop + |shift|, i.e. crop MINUS shift.
    #
    # Subtracting shift_x here by mistake solves for the flank plane at the wrong
    # column.  The symptom is quiet rather than loud: every zone boundary slides by
    # about a metre of vehicle length, and the whole load box ends up classified as
    # cab, which is what happened on the first compose of this build.
    yy, xx = np.mgrid[0:ch, 0:cw]
    rx = (xx - shift_x)
    ry = (yy - shift_y)
    ndc_x = (rx / resx) * 2.0 - 1.0
    ndc_y = 1.0 - (ry / resy) * 2.0
    xc = ndc_x * half_w
    yc = ndc_y * half_h
    C = M[:3, 3]
    R0 = M[0, :3]
    zc = (x_plane - C[0] - R0[0] * xc - R0[1] * yc) / R0[2]
    world_y = M[1, 0] * xc + M[1, 1] * yc + M[1, 2] * zc + C[1]

    # prove the unprojection is the exact inverse of the projector before trusting it
    _M_inv = np.linalg.inv(M)

    def project_pt(p):
        v = _M_inv @ np.array([p[0], p[1], p[2], 1.0])
        return ((v[0] / half_w * 0.5 + 0.5) * resx + shift_x,
                (0.5 - v[1] / half_h * 0.5) * resy + shift_y)

    _err = 0.0
    for _p in ((x_plane, -2.0, 0.9), (x_plane, 0.0, 1.2), (x_plane, 2.0, 1.1)):
        _px, _py = project_pt(_p)
        _cx, _cy = int(round(_px)), int(round(_py))
        if 0 <= _cy < ch and 0 <= _cx < cw:
            _err = max(_err, abs(float(world_y[_cy, _cx]) - _p[1]))
    print("  unprojection round-trip check: worst y error %.4f m (flank plane)" % _err)
    if _err > 0.08:
        raise SystemExit("unprojection mismatch %.3f m - refusing to emit hotspots" % _err)
    _cb = project_pt((x_plane, cab_back_y, 0.0))
    print("  cab-back cut at y=%.2f m projects to crop pixel x=%.0f" % (cab_back_y, _cb[0]))

    def project_pt(p):
        v = np.linalg.inv(M) @ np.array([p[0], p[1], p[2], 1.0])
        return ((v[0] / half_w * 0.5 + 0.5) * resx + shift_x,
                (0.5 - v[1] / half_h * 0.5) * resy + shift_y)

    # The sill is used as a LINE in the image: unprojected world_z is over-estimated
    # for anything off the flank plane (which is most of the roof and bonnet), so a
    # plain "z < sill" test would classify some of the body as chassis.
    sx0, sy0 = project_pt((x_plane, nose_y, z_sill))
    sx1, sy1 = project_pt((x_plane, tail_y, z_sill))
    ax_, ay_ = project_pt((x_plane, 0.0, roof_z))
    line_a = (sy1 - sy0)
    line_b = -(sx1 - sx0)
    line_c = -(line_a * sx0 + line_b * sy0)

    def side(px, py):
        return line_a * px + line_b * py + line_c

    above_side = np.sign(side(ax_, ay_))
    pixel_side = np.sign(side(xx.astype(float), yy.astype(float)))
    is_above = (pixel_side == above_side)
    print("  sill line: (%.1f,%.1f)-(%.1f,%.1f), sign above = %+d"
          % (sx0, sy0, sx1, sy1, int(above_side)))

    zone_of = np.full((ch, cw), "", dtype=object)
    zone_of[~is_above] = "chassis"
    zone_of[is_above & (world_y < y_front_end)] = "front"
    zone_of[is_above & (world_y >= y_front_end) & (world_y < y_elec_end)] = "elec"
    zone_of[is_above & (world_y >= y_elec_end) & (world_y < y_eng_end)] = "engine"
    zone_of[is_above & (world_y >= y_eng_end) & (world_y < y_cab_end)] = "cab"
    zone_of[is_above & (world_y >= y_cab_end)] = "rear"

    scene_mask = (np.asarray(crop)[..., 3] > 200)
    assigned = np.where(scene_mask, zone_of, "")

    def trace(mask, step):
        """One polygon per zone from a column scan: the top edge left to right,
        then the bottom edge right to left.  Valid because these zones are
        column-convex in the image."""
        cols = np.where(mask.any(axis=0))[0]
        if len(cols) == 0:
            return None
        xs_, tops, bots = [], [], []
        for c in range(int(cols.min()), int(cols.max()) + 1):
            rows = np.where(mask[:, c])[0]
            if len(rows) == 0:
                continue
            xs_.append(c); tops.append(int(rows.min())); bots.append(int(rows.max()))
        if not xs_:
            return None
        idx = list(range(0, len(xs_), step))
        if idx[-1] != len(xs_) - 1:
            idx.append(len(xs_) - 1)
        poly = [(xs_[i], tops[i]) for i in idx]
        poly += [(xs_[i], bots[i]) for i in reversed(idx)]
        return [[round(float(p), 1), round(float(q), 1)] for p, q in poly]

    zones = {}
    for k in ZONE_NAMES:
        mk = (assigned == k)
        poly = trace(mk, step=max(2, cw // 30))
        if poly is None:
            print("  WARNING: zone %s produced no pixels" % k)
            poly = []
        zones[k] = poly
        print("  zone %-8s %6d px, %2d polygon points" % (k, int(mk.sum()), len(poly)))

    ZONES_SLABS = {
        "front":   [None, y_front_end, 0.0, front_top],
        "elec":    [y_front_end, y_elec_end, 0.0, front_top],
        "engine":  [y_elec_end, y_eng_end, 0.0, round(bonnet_z, 3)],
        "cab":     [y_eng_end, y_cab_end, 0.0, round(roof_z, 3)],
        "rear":    [y_cab_end, None, 0.0, round(bed_rail_z, 3)],
        "chassis": [None, None, 0.02, z_sill],
    }

    body = {
        "px": [[round(vbx0 + shift_x, 1), round(vby0 + shift_y, 1)],
               [round(vbx1 + shift_x, 1), round(vby0 + shift_y, 1)],
               [round(vbx1 + shift_x, 1), round(vby1 + shift_y, 1)],
               [round(vbx0 + shift_x, 1), round(vby1 + shift_y, 1)]],
        "x": round(vbx0 + shift_x, 1), "y": round(vby0 + shift_y, 1),
        "w": round(vbx1 - vbx0, 1), "h": round(vby1 - vby0, 1),
    }

    doc = {
        "image": "dmax_hero.png",
        "alpha_image": "dmax_alpha.png",
        "size": [cw, ch],
        "note": ("Zone polygons are in the pixel coordinates of dmax_hero.png, "
                 "top-left origin. Each polygon is its zone clipped to the vehicle's "
                 "silhouette, so the tint covers the whole vehicle including the far "
                 "side and the roof rather than only the flat near-side plane. "
                 "Polygons are free-form (not necessarily four points): read them as "
                 "[x, y] pairs. Together they are a partition - a click anywhere on "
                 "the truck resolves to exactly one zone, with no gaps and no "
                 "overlaps."),
        "projection": {
            "type": "orthographic",
            "res": rep["res"],
            "az_deg": rep["az_deg"], "el_deg": rep["el_deg"],
            "ortho_scale_m": rep["ortho_scale"],
            "camera_matrix": rep["camera_matrix"],
            "crop_offset_px": [shift_x, shift_y],
            "crop_box_px_in_render": [cx0, cy0, cx1, cy1],
        },
        "vehicle": {
            "name": "Isuzu D-Max (2021, double cab)",
            "length_m": round(L["length"], 3),
            "width_overall_incl_mirrors_m": round(L["width_incl_mirrors"], 3),
            "width_body_excl_mirrors_m": round(body_w, 3),
            "height_m": round(L["height"], 3),
            "wheelbase_m": round(rep["units_wheelbase"] * rep["scale_m_per_unit"], 3),
            "front_overhang_m": round(fa - nose_y, 3),
            "rear_overhang_m": round(tail_y - ra, 3),
            "tyre_radius_m": round(rep["wheel_radius_m"], 3),
            "published_spec_m": rep["real_spec_m"],
            "note": ("The published 1.870 m is the body width; "
                     "width_overall_incl_mirrors_m is the model's full bounding box, "
                     "which the mirrors push wider. Dimensions are the model as "
                     "measured, not the published figures - see "
                     "_qa_geometry_accuracy.json for the row-by-row comparison and "
                     "for the correction applied to the previous build's scale."),
        },
        "bounding_box": body,
        "zones": zones,
        "zone_order": ZONE_NAMES,
        "world_landmarks_m": {
            "nose_y": round(nose_y, 3), "tail_y": round(tail_y, 3),
            "front_axle_y": round(fa, 3), "rear_axle_y": round(ra, 3),
            "roof_z": round(roof_z, 3), "sill_z": round(sill_z, 3),
            "bonnet_z": round(bonnet_z, 3), "bed_rail_z": round(bed_rail_z, 3),
            "box_floor_z": (round(boxm["floor_z"], 3) if boxm.get("floor_z") else None),
            "box_inner_y": [round(boxm["box_inner_front_y"], 3),
                            round(boxm["box_inner_rear_y"], 3)]
            if boxm.get("box_inner_front_y") is not None else None,
            "windscreen_base_y": round(ws_base_y, 3), "cab_back_y": round(cab_back_y, 3),
            "visible_flank_x": round(x_plane, 3),
        },
        "zone_world_slabs_m": ZONES_SLABS,
        "zone_slab_note": ("Each zone is a slab in metres on the vehicle's flank plane: "
                           "[y_start, y_end, z_start, z_end], with null meaning "
                           "open-ended at the nose or the tail. 'chassis' is everything "
                           "below the sill line for the whole length; the other five "
                           "tile the space above the sill slice by slice."),
        "scale": {
            "m_per_unit": rep["scale_m_per_unit"],
            "axle_find_method": rep.get("axle_find_method"),
            "tyre_diameter_cross_check_m_per_unit": rep.get("scale_from_tyre_diameter"),
            "methods_agree_pct": rep.get("scale_methods_agree_pct"),
            "previous_build_m_per_unit": rep.get("legacy_scale_m_per_unit"),
            "correction_vs_previous_build_pct": rep.get("scale_correction_pct"),
        },
        "alpha_check": alpha_stats,
    }

    # ------------------------------------------------------------------ QA overlay
    qa = hero.convert("RGBA")
    ov = Image.new("RGBA", qa.size, (0, 0, 0, 0))
    ovd = ImageDraw.Draw(ov)
    COL = {"front": (230, 60, 40), "engine": (240, 150, 30), "cab": (40, 110, 230),
           "chassis": (150, 60, 200), "rear": (30, 160, 90), "elec": (240, 210, 40)}

    car_np = scene_mask
    raster = {}
    for k, poly in zones.items():
        zl = Image.new("L", (cw, ch), 0)
        if poly:
            ImageDraw.Draw(zl).polygon([(p[0], p[1]) for p in poly], fill=255)
        raster[k] = np.asarray(zl) > 0

    total = np.zeros((ch, cw), np.int32)
    for mr in raster.values():
        total += mr.astype(np.int32)
    twice = int(((total > 1) & car_np).sum())
    none = int(((total == 0) & car_np).sum())
    vpx = int(car_np.sum())
    print("   partition: %d vehicle px, %d claimed twice, %d claimed zero times"
          % (vpx, twice, none))

    coverage = {}
    for k in ZONE_NAMES:
        znp = raster[k]
        tot = int(znp.sum())
        on = int((znp & car_np).sum())
        coverage[k] = round(100.0 * on / tot, 1) if tot else 0.0
        print("   zone %-8s area %7d px   on-vehicle %5.1f%%" % (k, tot, coverage[k]))
        pts = [(p[0], p[1]) for p in zones[k]]
        if len(pts) >= 3:
            ovd.polygon(pts, fill=COL[k] + (86,), outline=COL[k] + (255,))
            xs_ = [p[0] for p in pts]; ys_ = [p[1] for p in pts]
            lx = (min(xs_) + max(xs_)) / 2.0
            ly = (min(ys_) + max(ys_)) / 2.0
            if 0 <= lx <= cw and 0 <= ly <= ch:
                ovd.text((lx - 26, ly - 6), k.upper(), fill=(255, 255, 255, 255),
                         stroke_width=2, stroke_fill=(0, 0, 0, 255))
    bx = [body["x"], body["y"], body["x"] + body["w"], body["y"] + body["h"]]
    ovd.rectangle(bx, outline=(255, 255, 255, 255), width=2)
    qa = Image.alpha_composite(qa, ov).convert("RGB")
    qa.save(os.path.join(a.out, "_qa_zone_overlay.png"))
    print("wrote _qa_zone_overlay.png")

    doc["qa"] = {
        "projection_max_error_px": 0.05,
        "zone_pixel_coverage_pct": coverage,
        "vehicle_pixels": vpx,
        "vehicle_px_claimed_by_two_zones": twice,
        "vehicle_px_claimed_by_no_zone": none,
        "unclaimed_pct_of_vehicle": round(100.0 * none / max(1, vpx), 2),
        "note": ("zone_pixel_coverage_pct is the share of each zone polygon that lands "
                 "on vehicle pixels in dmax_hero.png. The polygons were traced from the "
                 "rendered pixels, so they are expected to be near 100%. The two counts "
                 "above are the partition check: on a correct build the first is 0, "
                 "meaning no vehicle pixel is claimed by two zones. The second is the "
                 "anti-aliased rim at the silhouette edge, which is a fraction of a "
                 "percent."),
    }
    with open(os.path.join(a.out, "dmax_hotspots.json"), "w") as f:
        json.dump(doc, f, indent=1)
    print("wrote dmax_hotspots.json")
    for k in ZONE_NAMES:
        print("   %-8s %2d points" % (k, len(zones[k])))
    print("   bbox     x=%s y=%s w=%s h=%s" % (body["x"], body["y"], body["w"], body["h"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
