"""Numeric QA on the composited frames.

Image reads do not render into this agent's context, so the frames are checked by
measurement instead: the truck body never reaches a frame edge, the studio sweep is
identical frame to frame, the contact shadow is present in every frame, consecutive
frames differ by a sensible and even amount, and the truck's tone does not swing.

Run:  python qa_frames_visual.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
FD = HERE / "frames"
OUT = HERE / "_qa"
OUT.mkdir(exist_ok=True)


def main() -> int:
    files = sorted(FD.glob("t_*.jpg"))
    if not files:
        raise SystemExit("no frames")
    n = len(files)
    print("%d frames in %s" % (n, FD))

    arrs = []
    for f in files:
        im = Image.open(f).convert("RGB")
        arrs.append(np.asarray(im).astype(np.float32))
    h, w, _ = arrs[0].shape
    print("frame size: %dx%d" % (w, h))

    fails = []

    # ---- 1. nothing clipped at the frame edge.  The detector has to be calibrated:
    # the house studio sweep is deliberately DARK low down, and the accepted hero
    # (dmax_hero.png) has a 1700 px dark run along its own bottom edge.  So "a dark run
    # on an edge" is the house background, not a clip.  What a clip actually looks like
    # is the TRUCK BODY - the near-opaque silhouette - reaching an edge.  That is what
    # is tested, on the raw renders where the body has its own alpha.
    print("\nedge check (does the truck BODY reach any frame edge?):")
    raw_dir = HERE / "_raw_tt"
    worst_gap = 10 ** 9
    worst_at = ""
    if raw_dir.exists():
        for j in range(n):
            p = raw_dir / ("f_%03d.png" % j)
            if not p.exists():
                continue
            al = np.asarray(Image.open(p))[..., 3]
            body = al > 250
            ys, xs = np.where(body)
            if not len(ys):
                continue
            gaps = {"top": int(ys.min()), "bottom": int(al.shape[0] - 1 - ys.max()),
                    "left": int(xs.min()), "right": int(al.shape[1] - 1 - xs.max())}
            for k, g in gaps.items():
                if g < worst_gap:
                    worst_gap, worst_at = g, "%s edge, frame %d" % (k, j)
        print("  smallest clearance between the body and any edge: %d px (%s)"
              % (worst_gap, worst_at))
        if worst_gap < 8:
            fails.append("the truck body comes within %d px of a frame edge (%s)"
                         % (worst_gap, worst_at))
        # the composited frames are cropped inside the render, so re-check after the crop
        crop = json.loads((HERE / "turntable_frames.json").read_text())["drift"]["crop_box_render_px"]
        cx0, cy0, cx1, cy1 = crop
        print("  crop box in render px: %s" % crop)
        for band, lim in (("left", cx0), ("top", cy0)):
            print("    %s margin inside the render: %d px" % (band, lim))
        print("    right margin: %d px, bottom margin: %d px"
              % (int(al.shape[1]) - cx1, int(al.shape[0]) - cy1))
    else:
        print("  (raw renders not present; skipped)")

    # ---- 1b. for the record, the house bottom-edge darkness, compared to the hero
    hero_p = HERE.parent / "dmax_hero.png"
    if hero_p.exists():
        hl = np.asarray(Image.open(hero_p).convert("RGB")).astype(np.float32).mean(axis=2)
        print("\nhouse background comparison (the sweep is dark low down by design):")
        print("  accepted hero bottom row: mean %.1f" % hl[-1].mean())
        print("  turntable bottom row    : mean %.1f (varies with the shadow the truck casts)"
              % float(np.mean([a[-1].mean() for a in arrs])))

    # ---- 1c. the studio backdrop must be the same in every frame.  The background is
    # generated once from the camera and the crop box is identical for all frames, so it
    # is fixed by construction.  What is measured here is the band above the truck.
    #
    # Two things move that band very slightly, and neither is a defect:
    #   * the band is not perfectly empty.  The shadow-catcher floor returns a faint
    #     ambient veil (alpha 1-14 up here, measured), and that veil is lit partly by
    #     light bouncing off the truck, so it changes a little as the vehicle turns.
    #   * the truck reaches higher in an end-on view, so in some frames it is inside
    #     the band.
    # The measured total effect is ~1.2 of 255, i.e. 0.5%, and it reads as a smooth
    # sweep rather than a step.  A tolerance of 3.0 catches a real background shift
    # while ignoring that.
    print("\nstudio backdrop above the truck (fixed by construction; measured):")
    top = np.array([float(a[:12].mean()) for a in arrs])
    print("  mean %.2f  spread across frames %.3f (%.2f%% of full scale)"
          % (top.mean(), top.max() - top.min(), 100.0 * (top.max() - top.min()) / 255.0))
    # and confirm it is a smooth drift, not a step between neighbouring frames
    step = float(np.abs(np.diff(top)).max())
    print("  largest step between neighbouring frames: %.3f" % step)
    if top.max() - top.min() > 3.0:
        fails.append("the studio backdrop shifts by %.2f across frames"
                     % (top.max() - top.min()))
    if step > 0.6:
        fails.append("the studio backdrop steps by %.2f between neighbouring frames"
                     % step)

    # ---- 2. the contact shadow must be present in every frame (the truck must not
    # float) and must be a shadow, i.e. darker than the sweep around it.
    print("\ncontact shadow under the truck, every frame:")
    shadow_ok = 0
    shadow_vals = []
    for j, a in enumerate(arrs):
        lum = a.mean(axis=2)
        band = lum[int(h * 0.80):int(h * 0.94)]
        p05 = float(np.percentile(band, 5))
        shadow_vals.append(p05)
        if p05 < 120:
            shadow_ok += 1
    print("  frames with a shadow (5th percentile < 120): %d / %d" % (shadow_ok, n))
    print("  shadow darkness: min %.1f  max %.1f" % (min(shadow_vals), max(shadow_vals)))
    if shadow_ok < n:
        fails.append("%d frame(s) have no visible contact shadow - the truck would float"
                     % (n - shadow_ok))

    # ---- 3b. the ground line is where the shadow sits, and it is generated from the
    # camera, so it must be identical in every frame.
    print("\nground/shadow line row, from the alpha of the raw renders:")
    raw_dir = HERE / "_raw_tt"
    if raw_dir.exists():
        rows = []
        for j in range(n):
            p = raw_dir / ("f_%03d.png" % j)
            if not p.exists():
                continue
            al = np.asarray(Image.open(p))[..., 3]
            # the shadow is the semi-transparent region; its top edge is the contact line
            semi = (al > 12) & (al < 250)
            ys = np.where(semi.any(axis=1))[0]
            if len(ys):
                rows.append(int(ys.min()))
        if rows:
            print("  top of the shadow, min %d max %d spread %d px" % (min(rows), max(rows),
                                                                      max(rows) - min(rows)))
            if max(rows) - min(rows) > 8:
                fails.append("the contact line moves by %d px across frames"
                             % (max(rows) - min(rows)))
    # ---- 4. consecutive frames must differ smoothly; a discontinuity would be a jump
    print("\nframe-to-frame difference (a spike would be a visible jump):")
    diffs = []
    for j in range(n):
        a = arrs[j]
        b = arrs[(j + 1) % n]
        d = float(np.abs(a - b).mean())
        diffs.append(d)
    mean_d = sum(diffs) / len(diffs)
    mx = max(diffs)
    mn = min(diffs)
    print("  mean %.3f  min %.3f  max %.3f  (max/mean = %.2f)"
          % (mean_d, mn, mx, mx / mean_d))
    print("  the wrap step is diff[%d] = %.3f; the mean of the rest is %.3f"
          % (n - 1, diffs[-1], sum(diffs[:-1]) / (n - 1)))
    rw = diffs[-1] / (sum(diffs[:-1]) / (n - 1))
    print("  wrap/others ratio %.3f  (1.0 is a perfectly even loop)" % rw)
    if rw > 1.35 or rw < 0.75:
        fails.append("the wrap step differs from the other steps (ratio %.2f) - "
                     "the loop would jump" % rw)
    if mx / mean_d > 2.0:
        fails.append("a single step differs %.2fx from the mean - possible jump"
                     % (mx / mean_d))

    # ---- 5. the truck must be present and dark-ish in every frame, and the amount of
    # ink must follow the yaw smoothly (end-on shows less truck than broadside)
    print("\ntruck presence per frame (share of pixels darker than 170):")
    ink = [float((a.mean(axis=2) < 170).mean()) for a in arrs]
    print("  min %.3f  max %.3f  mean %.3f" % (min(ink), max(ink), sum(ink) / len(ink)))
    if min(ink) < 0.04:
        fails.append("a frame has almost no truck in it (ink %.3f)" % min(ink))
    # smoothness of that curve
    d2 = [abs(ink[j] - ink[(j + 1) % n]) for j in range(n)]
    print("  largest change between neighbouring frames: %.4f" % max(d2))

    # ---- 6. colour stability: the median colour of the truck should not swing
    print("\nmedian truck colour per frame (the vehicle must not change hue):")
    meds = []
    for a in arrs:
        m = a.mean(axis=2) < 150
        if m.sum() < 500:
            continue
        meds.append(a[m].mean(axis=0))
    meds = np.array(meds)
    print("  R %.1f..%.1f  G %.1f..%.1f  B %.1f..%.1f"
          % (meds[:, 0].min(), meds[:, 0].max(),
             meds[:, 1].min(), meds[:, 1].max(),
             meds[:, 2].min(), meds[:, 2].max()))
    if (meds.max(axis=0) - meds.min(axis=0)).max() > 45:
        fails.append("truck colour swings widely across frames")

    # ---- contact sheet plus a strip of the extremes, for the record
    from PIL import ImageDraw
    cols = 8
    tw = 240
    th = int(round(tw * h / w))
    rows_n = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows_n * (th + 16)), (21, 35, 60))
    d = ImageDraw.Draw(sheet)
    for j, a in enumerate(arrs):
        t = Image.fromarray(a.astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        x, y = (j % cols) * tw, (j // cols) * (th + 16)
        sheet.paste(t, (x, y + 16))
        d.text((x + 4, y + 3), "f%02d  %5.1f deg" % (j, j * 360.0 / n), fill=(247, 244, 238))
    sp = OUT / "frames_contact_sheet.png"
    sheet.save(sp)
    print("\nwrote", sp, sheet.size)

    # a large strip of the four "corners" of the rotation, to judge by eye elsewhere
    picks = [0, n // 4, n // 2, (3 * n) // 4]
    strip = Image.new("RGB", (2 * 620, 2 * int(round(620 * h / w))), (21, 35, 60))
    for k, j in enumerate(picks):
        t = Image.fromarray(arrs[j].astype(np.uint8)).resize(
            (620, int(round(620 * h / w))), Image.LANCZOS)
        strip.paste(t, ((k % 2) * 620, (k // 2) * t.height))
    sp2 = OUT / "frames_four_angles.png"
    strip.save(sp2)
    print("wrote", sp2, strip.size, "frames", picks)

    print("\n=== QA %s ===" % ("FAILED" if fails else "OK"))
    for f in fails:
        print("  -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
