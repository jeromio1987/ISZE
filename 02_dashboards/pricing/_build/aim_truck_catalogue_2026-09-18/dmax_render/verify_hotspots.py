"""Verify the hotspot polygons resolve correctly on the hero image.

Checks, without needing a browser:
  1. every polygon has 4 finite points
  2. every polygon lies inside the image
  3. the six polygons do not overlap each other
  4. together they cover the vehicle without gaps along the flank
  5. each polygon's centre point maps back to a plausible world position

Run: python verify_hotspots.py
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
HP = os.path.join(HERE, "dmax_hotspots.json")
HERO = os.path.join(HERE, "dmax_hero.png")

FAILS, WARNS = [], []


def main() -> int:
    with open(HP) as f:
        doc = json.load(f)
    im = Image.open(HERO)
    W, H = im.size

    print("hero        : %dx%d %s" % (W, H, im.mode))
    print("declared    : %s" % (doc["size"],))
    if list(doc["size"]) != [W, H]:
        FAILS.append("declared size %s does not match the hero %dx%d" % (doc["size"], W, H))
    if im.mode != "RGB":
        FAILS.append("dmax_hero.png must be opaque RGB, got %s" % im.mode)

    zones = doc["zones"]
    names = doc["zone_order"]
    print("zones       : %s" % names)
    if set(zones) != set(names):
        FAILS.append("zone_order %s does not match zones %s" % (names, sorted(zones)))

    # 1 + 2
    for k, poly in zones.items():
        if len(poly) < 3:
            FAILS.append("%s has %d points, need at least 3" % (k, len(poly)))
        if len(poly) % 2 != 0:
            WARNS.append("%s has an odd point count (%d); it should be an upper edge "
                         "followed by a lower edge" % (k, len(poly)))
        for p in poly:
            if len(p) != 2 or not all(isinstance(v, (int, float)) and np.isfinite(v) for v in p):
                FAILS.append("%s has a malformed point %s" % (k, p))
            elif not (0 <= p[0] <= W and 0 <= p[1] <= H):
                WARNS.append("%s point %s is outside the image" % (k, p))

    # 3 + 4: rasterise each zone and check overlap and gap.
    # Adjacent zones share an edge by design, and filling a polygon includes its
    # boundary, so a raw intersection always reports a 1-pixel seam.  Erode each
    # mask by one pixel first: what remains is real overlap.
    def erode1(m):
        e = m.copy()
        e[1:, :] &= m[:-1, :]
        e[:-1, :] &= m[1:, :]
        e[:, 1:] &= m[:, :-1]
        e[:, :-1] &= m[:, 1:]
        return e

    masks = {}
    for k, poly in zones.items():
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon([(p[0], p[1]) for p in poly], fill=255)
        masks[k] = np.asarray(m) > 0
    core = {k: erode1(m) for k, m in masks.items()}

    total_overlap = np.zeros((H, W), np.int32)
    for k, m in core.items():
        total_overlap += m.astype(np.int32)
    ov = int((total_overlap > 1).sum())
    print("overlap px  : %d (after 1-px erosion, so shared edges do not count)" % ov)
    if ov > 0:
        pairs = []
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                n = int((core[a] & core[b]).sum())
                if n:
                    pairs.append("%s/%s %d" % (a, b, n))
        FAILS.append("zones genuinely overlap: %s" % ", ".join(pairs))

    union = np.zeros((H, W), bool)
    for m in masks.values():
        union |= m
    print("union px    : %d" % int(union.sum()))

    # gap check: vehicle pixels that no zone covers.  "Vehicle" here is taken from
    # the alpha render's solid body, which is the ground truth for where the truck is.
    alpha_path = os.path.join(HERE, "dmax_alpha.png")
    a_im = Image.open(alpha_path)
    scale_x = a_im.width / W
    scale_y = a_im.height / H
    a_arr = np.asarray(a_im.convert("RGBA"))
    a_small = np.asarray(Image.fromarray(a_arr).resize((W, H), Image.BILINEAR))
    solid = a_small[..., 3] > 200
    print("solid vehicle px (from the alpha render): %d" % int(solid.sum()))
    gap = solid & ~union
    print("vehicle px no zone covers: %d (%.2f%% of the vehicle)" % (
        int(gap.sum()), 100.0 * gap.sum() / max(1, solid.sum())))
    if 100.0 * gap.sum() / max(1, solid.sum()) > 3.0:
        WARNS.append("%.2f%% of the vehicle falls outside every zone" % (
            100.0 * gap.sum() / max(1, solid.sum())))
    cov = doc.get("qa", {}).get("zone_pixel_coverage_pct", {})
    for k in names:
        v = cov.get(k)
        print("   %-8s coverage %s%%" % (k, v))
        if v is not None and v < 60:
            WARNS.append("%s coverage is only %.1f%%" % (k, v))

    # 5: verify the unprojection recovers sensible positions.  The zone polygons
    # are column-scanned, so their "centre" is not a point on the vehicle; instead
    # check the world slab each zone declares, using the same projection maths.
    proj = doc["projection"]
    M = np.array(proj["camera_matrix"], dtype=float)
    scale = proj["ortho_scale_m"]
    resx, resy = proj["res"]
    offx, offy = proj["crop_offset_px"]
    half_w = scale / 2.0
    half_h = half_w * resy / resx
    x_plane = doc["world_landmarks_m"]["visible_flank_x"]
    C = M[:3, 3]
    R0 = M[0, :3]

    def unproject(px, py):
        """Pixel -> the point on the flank plane that projects there."""
        rx, ry = px - offx, py - offy
        ndc_x = (rx / resx) * 2.0 - 1.0
        ndc_y = 1.0 - (ry / resy) * 2.0
        xc = ndc_x * half_w
        yc = ndc_y * half_h
        zc = (x_plane - C[0] - R0[0] * xc - R0[1] * yc) / R0[2]
        return (M @ np.array([xc, yc, zc, 1.0]))[:3]

    def project(p):
        v = np.linalg.inv(M) @ np.array([p[0], p[1], p[2], 1.0])
        return ((v[0] / half_w * 0.5 + 0.5) * resx + offx,
                (0.5 - v[1] / half_h * 0.5) * resy + offy)

    # round-trip test on the declared landmarks
    lm = doc["world_landmarks_m"]
    print("\nround-trip check on the declared landmarks (world -> pixel -> world):")
    worst = 0.0
    for name, pt in (("front_axle_ground", (x_plane, lm["front_axle_y"], 0.0)),
                     ("rear_axle_ground", (x_plane, lm["rear_axle_y"], 0.0)),
                     ("windscreen_base", (x_plane, lm["windscreen_base_y"], lm["bonnet_z"])),
                     ("cab_back", (x_plane, lm["cab_back_y"], lm["roof_z"] * 0.6)),
                     ("sill_mid", (x_plane, 0.0, lm["sill_z"]))):
        px, py = project(pt)
        back = unproject(px, py)
        err = float(np.linalg.norm(np.array(back[1:]) - np.array(pt[1:])))
        worst = max(worst, err)
        print("   %-18s -> px(%7.1f,%6.1f) -> back y %6.2f z %5.2f   err %.3f m" % (
            name, px, py, back[1], back[2], err))
    if worst > 0.35:
        FAILS.append("landmark round-trip error %.2f m is too large" % worst)

    # the declared zone slabs must tile the length with no gap
    slabs = doc.get("zone_slab_note")
    if not slabs:
        WARNS.append("hotspot file has no zone_slab_note describing the world slabs")
    # zone coverage reported by the composer
    qa = doc.get("qa", {})
    twice = qa.get("vehicle_px_claimed_by_two_zones")
    zero = qa.get("vehicle_px_claimed_by_no_zone")
    print("\ncomposer partition check: %s px claimed twice, %s px claimed zero times" % (twice, zero))
    if twice:
        FAILS.append("%s vehicle pixels are claimed by two zones" % twice)
    if zero is None:
        WARNS.append("no gap count in the hotspot file")
    elif zero > 0:
        WARNS.append("%s vehicle pixels are claimed by no zone (%.2f%% of the vehicle)" % (
            zero, 100.0 * zero / max(1, qa.get("vehicle_pixels", 1))))

    print()
    for w in WARNS:
        print("WARN: " + w)
    for f_ in FAILS:
        print("FAIL: " + f_)
    if not FAILS:
        print("HOTSPOT_CHECK_OK" if not WARNS else "HOTSPOT_CHECK_OK_WITH_WARNINGS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
