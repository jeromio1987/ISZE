"""Build the QA contact sheet: real D-Max imagery vs this render, with the numbers.

Three panels:
  1. Isuzu's own imagery beside the render at the same size, so the "does it look
     like a real D-Max" question is answered by eye.
  2. The measured silhouette comparison at the HERO angle: the real cutout, the
     difference, and this render.
  3. The measured dimensions against Isuzu's published specification, with the
     before/after column for the tail rows the brief called out.

Run: python make_qa_sheet.py
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REFDIR = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_truck_ref"
CUTOUT = os.path.join(REFDIR, "cut", "dmax_a.png")       # clean isolated D-Max double cab
HERO = os.path.join(HERE, "dmax_hero.png")

NAVY = (21, 35, 60)
PAPER = (247, 244, 238)
INK = (34, 34, 34)
TERRA = (192, 85, 45)
GREEN = (30, 107, 79)
GREY = (110, 116, 126)


def font(size, bold=False):
    for name in (("seguisb.ttf" if bold else "segoeui.ttf"),
                 ("arialbd.ttf" if bold else "arial.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def fit(im, box_w, box_h):
    r = min(box_w / im.width, box_h / im.height)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)


def silhouette_pair():
    """Recover the normalised reference and render silhouettes at the hero angle."""
    try:
        import measure_silhouette_mismatch as sil
        with open(os.path.join(HERE, "_qa_silhouette_metrics.json")) as f:
            doc = json.load(f)
        m = doc["hero_angle"]
        az, el = int(round(m["azimuth_deg"])), int(round(m["elevation_deg"]))
        png = os.path.join(HERE, "_raw", "rgba_hero_meas_az%d_el%d.png" % (az, el))
        if not os.path.exists(png):
            return None
        ref = sil.ref_mask()[0]
        ren = sil.render_mask(png)
        if m.get("orientation") == "mirrored":
            ren = ren[:, ::-1].copy()

        def body(x):
            rows = x.sum(1)
            peak = int(np.argmax(rows))
            keep = np.where(rows > 0.25 * rows[peak])[0]
            return x[keep.min():keep.max() + 1]

        return body(ref), body(ren)
    except Exception as exc:                                   # never fail the sheet
        print("silhouette panel skipped:", exc)
        return None


def mask_image(m, w, h):
    return Image.fromarray((m * 255).astype(np.uint8)).convert("L").resize((w, h), Image.LANCZOS)


def overlay_image(ref, ren, w, h):
    a = np.asarray(mask_image(ref, w, h)) > 127
    b = np.asarray(mask_image(ren, w, h)) > 127
    vis = np.zeros((h, w, 3), np.uint8)
    vis[:, :] = (250, 250, 252)
    vis[a & b] = (150, 156, 166)
    vis[a & ~b] = (40, 110, 235)
    vis[~a & b] = (225, 60, 40)
    return Image.fromarray(vis)


def wrap(draw, text, fnt, max_w):
    """Wrap a note to the sheet width, returning the lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main() -> int:
    with open(os.path.join(HERE, "_qa_geometry_accuracy.json")) as f:
        acc = json.load(f)
    rows = acc["after"]["comparison"]
    tail = {r["dimension"]: r for r in acc.get("tail_before_after", [])}

    try:
        with open(os.path.join(HERE, "_qa_silhouette_metrics.json")) as f:
            silm = json.load(f)["hero_angle"]
    except Exception:
        silm = None

    W = 1860
    pad = 40
    gap = 30
    col_w = (W - 2 * pad - gap) // 2
    img_h = 330
    row_h = 28
    # five columns: dimension | what it means | model | spec | delta | before
    table_h = 40 + row_h * (len(rows) + 1)
    sil_h = 190

    scale_note = ("The model is scaled on the published 3.125 m wheelbase. The previous build "
                  "read the wheelbase as the largest gap in the rim cloud, which this model "
                  "defeats because it carries extra wheel geometry behind the rear axle. That "
                  "made every dimension %.1f%% too small - including the tail rows. Correcting "
                  "the scale, and measuring the load box by ray casting instead of by a height "
                  "histogram, is what moved the tail." % abs(acc["scale_correction_pct"]))

    notes = [
        scale_note,
        "BEFORE is the previous method, recomputed by the same script so the two columns are "
        "directly comparable rather than copied from an earlier report.",
        "Red rows differ from Isuzu's published figure by more than 5%. The wheelbase agrees by "
        "construction, so every other row is a genuine test.",
        "Box depth now reads %.2f m against a published %.2f m. The model measures a 3 cm higher "
        "rail and a 5 cm lower floor than the published figures imply, so the scale anchor "
        "explains most but not all of it and the residual is stated rather than hidden."
        % (acc["after"]["model_all_measures_m"]["loadbox_depth_m"],
           acc["spec"]["loadbox_depth_m"]),
    ]
    if silm:
        notes.append(
            "Silhouette at the hero camera angle (azimuth %d deg, elevation %d deg): "
            "intersection-over-union %.3f, symmetric difference %.1f%% of the reference area. "
            "Top-edge error %.1f%% of vehicle height, bottom-edge error %.1f%%."
            % (silm["azimuth_deg"], silm["elevation_deg"],
               silm["intersection_over_union"],
               silm["symmetric_difference_pct_of_reference"],
               silm["top_edge_error_pct_of_height"]["mean"],
               silm["bottom_edge_error_pct_of_height"]["mean"]))

    head_h = 132
    sec_a_head = 34
    cap_h = 26
    sec_b_head = 34
    sec_c_head = 34
    note_font = font(14)
    # measure the wrapped notes on a scratch drawable at the full sheet width, so
    # the footer box is sized from the real wrapped line count and nothing is cut
    _scratch = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    note_lines = []
    for n in notes:
        note_lines.extend(wrap(_scratch, n, note_font, W - 2 * pad))
        note_lines.append("")
    note_lines = note_lines[:-1]
    foot_h = 24 * len(note_lines) + 34
    H = head_h + sec_a_head + img_h + cap_h + sec_b_head + sil_h + cap_h \
        + sec_c_head + table_h + foot_h

    sheet = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(sheet)

    d.rectangle([0, 0, W, head_h - 26], fill=NAVY)
    d.text((pad, 24), "ISUZU D-MAX 2021 - RENDER ACCURACY", font=font(34, True), fill=PAPER)
    d.text((pad, 70), "Free Objaverse / CC-BY model, Cycles render, 2600 x 1120, 400 samples. "
                      "Compared against Isuzu's own photography and the published dimensions.",
           font=font(16), fill=(200, 210, 225))

    # ---- section A: real imagery beside the render
    y = head_h
    d.text((pad, y), "ISUZU'S OWN IMAGERY  (real D-Max, the reference)",
           font=font(17, True), fill=TERRA)
    d.text((pad + col_w + gap, y), "THIS RENDER  (free model, no textures)",
           font=font(17, True), fill=TERRA)
    y += sec_a_head

    ax, bx = pad, pad + col_w + gap
    cut = fit(Image.open(CUTOUT).convert("RGB"), col_w, img_h)
    sheet.paste(cut, (ax + (col_w - cut.width) // 2, y + (img_h - cut.height) // 2))
    hero = fit(Image.open(HERO).convert("RGB"), col_w, img_h)
    sheet.paste(hero, (bx + (col_w - hero.width) // 2, y + (img_h - hero.height) // 2))
    y += img_h + 4
    d.text((ax, y), "Isolated 2021 D-Max double cab, same body style as the render",
           font=font(13), fill=GREY)
    d.text((bx, y), "dmax_hero.png - hero angle azimuth %d, elevation %d"
           % (silm["azimuth_deg"] if silm else 0, silm["elevation_deg"] if silm else 0),
           font=font(13), fill=GREY)
    y += cap_h

    # ---- section B: the measured silhouette comparison
    d.text((pad, y), "MEASURED SILHOUETTE AT THE HERO CAMERA ANGLE",
           font=font(17, True), fill=TERRA)
    y += sec_b_head
    pair = silhouette_pair()
    if pair:
        ref, ren = pair
        third = (W - 2 * pad - 2 * gap) // 3
        rh = min(int(third * ref.shape[0] / ref.shape[1]), sil_h)
        w1 = int(rh * ref.shape[1] / ref.shape[0])
        w2 = int(rh * ren.shape[1] / ren.shape[0])
        ov = overlay_image(ref, ren, w1, rh)
        for i, (im, cap) in enumerate([
                (mask_image(ref, w1, rh).convert("RGB"), "real D-Max silhouette"),
                (ov, "blue = real only, red = render only"),
                (mask_image(ren, w2, rh).convert("RGB"), "this render, same scale")]):
            x = pad + i * (third + gap) + (third - im.width) // 2
            box = Image.new("RGB", (im.width, im.height), (250, 250, 252))
            box.paste(im, (0, 0))
            sheet.paste(box, (x, y))
            d.text((pad + i * (third + gap), y + rh + 6), cap, font=font(13), fill=GREY)
        y += rh + cap_h
    else:
        d.text((pad, y), "silhouette panel unavailable", font=font(15), fill=GREY)
        y += cap_h

    # ---- section C: the geometry table, after with the before column
    d.text((pad, y), "MEASURED AGAINST ISUZU'S PUBLISHED SPECIFICATION  (after vs before)",
           font=font(17, True), fill=TERRA)
    y += sec_c_head
    cols = [pad, pad + 330, pad + 640, pad + 780, pad + 920, pad + 1090, pad + 1290]
    d.rectangle([pad - 10, y - 4, W - pad + 10, y + row_h - 2], fill=(228, 232, 238))
    for x, t in zip(cols, ["dimension", "what it means", "model (m)", "spec (m)", "after",
                           "before", "before delta"]):
        d.text((x, y + 3), t, font=font(14, True), fill=NAVY)
    y += row_h
    for i, r in enumerate(rows):
        t = tail.get(r["dimension"], {})
        bg = (250, 250, 252) if i % 2 == 0 else PAPER
        d.rectangle([pad - 10, y - 4, W - pad + 10, y + row_h - 4], fill=bg)
        col = TERRA if r.get("over_5pct") else INK
        d.text((cols[0], y + 3), r["dimension"], font=font(14), fill=col)
        d.text((cols[1], y + 3), r["means"], font=font(14), fill=(90, 96, 105))
        d.text((cols[2], y + 3), "%.3f" % r["model_m"], font=font(14), fill=INK)
        d.text((cols[3], y + 3), "%.3f" % r["spec_m"], font=font(14), fill=INK)
        d.text((cols[4], y + 3), "%+.1f%%" % r["delta_pct"], font=font(14, True), fill=col)
        if t.get("before_m") is not None:
            d.text((cols[5], y + 3), "%.3f" % t["before_m"], font=font(14), fill=(120, 124, 132))
            bcol = TERRA if abs(t["before_delta_pct"]) > 5 else GREEN
            d.text((cols[6], y + 3), "%+.1f%%" % t["before_delta_pct"],
                   font=font(14, True), fill=bcol)
        else:
            d.text((cols[5], y + 3), "-", font=font(14), fill=(160, 164, 170))
        y += row_h

    # ---- notes
    y += 12
    d.rectangle([pad - 10, y, W - pad + 10, y + 4], fill=NAVY)
    y += 18
    for ln in note_lines:
        if ln:
            d.text((pad, y), ln, font=note_font, fill=(70, 76, 86))
        y += 24

    out = os.path.join(HERE, "_qa_accuracy_sheet.png")
    sheet.save(out)
    print("wrote", out, sheet.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
