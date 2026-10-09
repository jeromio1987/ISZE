# -*- coding: utf-8 -*-
"""
Pass 3 on the v2 kickback management deck, 2026-10-07.

Applies Jerome's slide-by-slide corrections:
 1. soften the 'retain' emphasis on the programme-details slide
 2. add other KPIs to the FY2026 performance slide (fill rate, days of stock
    against band, back orders against ceiling) from the KPI Master File + targets
 3. name the five distributors behind the EUR 678,464 replenishment card
 4. delete the SALES-TO-DEALER EVIDENCE slide (quantity-derived percentages)
 5. fix the clipping on the European logic slide
 6. rebuild the decision slide as a continuous-review cycle (kaizen)
 7. consolidate the iMotors slides from four to three
plus: renumber page markers, remove a units-derived percentage, scan for banned strings.
"""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import openpyxl
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
DECK = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
KPI = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\11_planning\KPI Master File august 2026.xlsx")
TGT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\11_planning\ISZE_DB_KPI_Targets_FY2627_v1.xlsx")

BG = RGBColor(0x26, 0x26, 0x26)
PANEL = RGBColor(0x30, 0x30, 0x30)
RED = RGBColor(0xE3, 0x06, 0x13)
INK = RGBColor(0xF2, 0xF2, 0xF2)
MUTED = RGBColor(0xBD, 0xBD, 0xBD)
GREY = RGBColor(0x4B, 0x4B, 0x4B)
FONT = "Aptos"


# --------------------------------------------------------------------------- #
# KPI computation (kept in the script so the printed figures are traceable)
# --------------------------------------------------------------------------- #
MONTH_COLS = None


def _kpi_rows(ws, header_row):
    """Return {distributor: {month_label: value}} for a block."""
    hdr = {}
    for c in range(2, 40):
        v = ws.cell(header_row, c).value
        if isinstance(v, str) and v.strip():
            hdr[c] = v.strip()
    out = {}
    r = header_row + 1
    while r <= ws.max_row:
        name = ws.cell(r, 1).value
        if not isinstance(name, str) or not name.strip():
            r += 1
            continue
        if name.strip().lower().startswith(("distributor",)):
            break
        row = {}
        for c, lbl in hdr.items():
            row[lbl] = ws.cell(r, c).value
        out[name.strip()] = row
        r += 1
    return out


def _latest(row, months):
    """Latest month, within the last 14 reported months, that carries a number.

    Two-year blocks are mostly 'N/D' (no report) once a distributor goes dark, so
    taking the strictly last numeric cell in the row would quote stale data. The
    14-month window is the reporting-gate period used in the targets workbook.
    """
    scan = months[-14:]
    for m in reversed(scan):
        v = row.get(m)
        if isinstance(v, (int, float)):
            return m, v
    return None, None


def compute_kpis():
    wb = openpyxl.load_workbook(KPI, data_only=True)
    ws = wb["Parts Handling"]
    # locate the block header rows
    rows = {}
    for r in range(1, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if isinstance(v, str):
            s = v.strip()
            for key in ("Days of Parts in Stock", "First Fill Rate",
                        "Back Order Lines", "Parts Sales DB to DLR in"):
                if s.startswith(key):
                    rows[key] = r + 2   # block label, blank line, header row
    mos = _kpi_rows(ws, rows["Days of Parts in Stock"])
    fill = _kpi_rows(ws, rows["First Fill Rate"])
    bo = _kpi_rows(ws, rows["Back Order Lines"])
    sales = _kpi_rows(ws, rows["Parts Sales DB to DLR in"])

    months = [ws.cell(rows["Days of Parts in Stock"], c).value for c in range(2, 40)]
    months = [m for m in months if isinstance(m, str) and m.strip()]
    months = [m.strip() for m in months]

    # supply-class bands from the targets workbook
    tb = openpyxl.load_workbook(TGT, data_only=True)["Targets FY26-27"]
    bands = {}
    for r in range(3, tb.max_row + 1):
        db = tb.cell(r, 1).value
        lo, hi = tb.cell(r, 8).value, tb.cell(r, 9).value
        if isinstance(db, str) and isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
            bands[db.strip()] = (float(lo), float(hi))

    # slide-9 distributors -> row names in the KPI file -> band keys
    mapping = {
        "IUK": ("IUK", "IUK"),
        "UTI": ("UTI", "UTI"),
        "UMI": ("UMI", "UMI"),
        "Germany (ISD)": ("ISD", "ISD"),
        "Benelux (IBX)": ("IBX (BENELUX)", "IBX (incl. Polska)"),
        "Portugal (Imotors)": ("Imotors", "Imotors"),
        "Sweden": ("Isuzu Sverige", "Isuzu Sverige"),
        "Norway (RSA)": ("RSA", "RSA"),
        "Ireland": ("Isuzu Ireland", "Isuzu Ireland"),
    }
    rec = {}
    for label, (krow, bkey) in mapping.items():
        fm, fv = _latest(fill.get(krow, {}), months)
        dm, dv = _latest(mos.get(krow, {}), months)
        bm, bv = _latest(bo.get(krow, {}), months)
        sm, sv = _latest(sales.get(krow, {}), months)
        band = bands.get(bkey)
        rec[label] = dict(fill=(fm, fv), mos=(dm, dv), bo=(bm, bv),
                          sales=(sm, sv), band=band)
    return rec, months


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def fill(shape, rgb):
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb
    shape.line.fill.background()
    shape.shadow.inherit = False


def say(shape, blocks, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """blocks = [ (text, size, colour, bold, space_before) ]"""
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.clear()
    for i, (txt, size, col, bold, sp_before) in enumerate(blocks):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if sp_before:
            p.space_before = Pt(sp_before)
        r = p.add_run()
        r.text = txt
        r.font.size = Pt(size)
        r.font.color.rgb = col
        r.font.bold = bold
        r.font.name = FONT


def set_one(shape, txt, size=None, col=None, bold=None):
    """Replace the text of a shape, keeping its first run's font where told to."""
    tf = shape.text_frame
    r = tf.paragraphs[0].runs[0]
    r.text = txt
    if size is not None:
        r.font.size = Pt(size)
    if col is not None:
        r.font.color.rgb = col
    if bold is not None:
        r.font.bold = bold
    for p in tf.paragraphs[1:]:
        for rr in p.runs:
            rr.text = ""


def find(slide, needle, nth=0):
    hits = [sh for sh in slide.shapes
            if sh.has_text_frame and needle in sh.text_frame.text]
    return hits[nth] if len(hits) > nth else None


def canvas(slide, x, y, w, h, rgb=None, shape=MSO_SHAPE.RECTANGLE):
    sh = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if rgb is None:
        sh.fill.background()
        sh.line.fill.background()
    else:
        fill(sh, rgb)
    sh.shadow.inherit = False
    return sh


def tbox(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    return tb


# --------------------------------------------------------------------------- #
def main():
    rec, months = compute_kpis()
    print("KPI read (latest reported month per distributor):")
    for k, v in rec.items():
        print("   %-20s fill=%s mos=%s band=%s bo=%s sales=%s" % (
            k, v["fill"], v["mos"], v["band"], v["bo"], v["sales"]))

    prs = Presentation(str(DECK))
    slides = list(prs.slides)
    print("slides at start:", len(slides))

    # ---------------- item 4 + item 7 : delete two slides -------------------
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    for physical in (13, 7):          # SALES-TO-DEALER EVIDENCE, then STOCK TIMING
        el = ids[physical - 1]
        prs.part.drop_rel(el.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"))
        sldIdLst.remove(el)
    slides = list(prs.slides)
    print("slides after deletion:", len(slides))
    assert len(slides) == 21, len(slides)

    # ---------------- renumber page markers --------------------------------
    for i, s in enumerate(slides, 1):
        if i == 1:
            continue
        m = None
        for sh in s.shapes:
            if not sh.has_text_frame:
                continue
            t = sh.text_frame.text.strip()
            if t.isdigit() and len(t) <= 2 and sh.left is not None and sh.left / 914400 > 11.5:
                m = sh
                break
        if m is not None:
            set_one(m, "%02d" % (i - 1))
    print("markers renumbered")

    # =========================== item 1: slide 5 ===========================
    s5 = slides[4]
    sh = find(s5, "incentive commitment")
    if sh:
        set_one(sh, "The FY2027 incentive commitment is EUR 393,000")
    sh = find(s5, "Financial cells")
    if sh:
        set_one(sh, "Source: budget_per_DB_reviewed_24042026.xlsx, "
                    "'Incentive FY27'. Financial cells as supplied.")
    sh = find(s5, "Eleven customers")
    if sh:
        set_one(sh, "Eleven customers. Rates and amounts as tabled; payment is "
                    "subject to annual target achievement and the required reporting.")
    print("item 1 done (slide 5)")

    # =========================== item 2: slide 8 ===========================
    s8 = slides[7]                     # FY2026 PERFORMANCE
    # --- KPI tiles in a new bottom band
    band = canvas(s8, 0.42, 5.99, 12.49, 0.92, PANEL)

    rep_fill = {k: v for k, v in rec.items() if isinstance(v["fill"][1], (int, float))}
    rep_mos = {k: v for k, v in rec.items() if isinstance(v["mos"][1], (int, float))}
    rep_bo = {k: v for k, v in rec.items() if isinstance(v["bo"][1], (int, float))}

    good_fill = [k for k, v in rep_fill.items() if v["fill"][1] >= 0.92]
    bad_fill = [k for k, v in rep_fill.items() if v["fill"][1] < 0.92]
    none_fill = [k for k in rec if k not in rep_fill]

    inside = [k for k, v in rep_mos.items() if v["band"] and v["band"][0] <= v["mos"][1] <= v["band"][1]]
    above = [k for k, v in rep_mos.items() if v["band"] and v["mos"][1] > v["band"][1]]
    below = [k for k, v in rep_mos.items() if v["band"] and v["mos"][1] < v["band"][0]]
    none_mos = [k for k in rec if k not in rep_mos]

    bo_above, bo_inside, bo_none, bo_unknown = [], [], [], []
    for k, v in rec.items():
        if not isinstance(v["bo"][1], (int, float)):
            bo_none.append(k)
            continue
        if isinstance(v["sales"][1], (int, float)) and v["sales"][1] > 0:
            ceiling = 15.0 * v["sales"][1] / 100000.0
            (bo_above if v["bo"][1] > ceiling else bo_inside).append(k)
        else:
            bo_unknown.append(k)

    def j(x):
        return ", ".join(x) if x else "none"

    tiles = [
        ("FILL RATE  ·  STANDARD 95%, FLOOR 92%",
         "%d of %d" % (len(good_fill), len(rep_fill)),
         "reporting distributors at or above the 92% floor. Below it: "
         + j(bad_fill) + ". No value on file: " + j(none_fill) + "."),
        ("DAYS OF STOCK  ·  AGAINST SUPPLY-CLASS BAND",
         "%d of %d" % (len(above), len(rep_mos)),
         "above their own band. Inside: " + j(inside) + ". Below: " + j(below)
         + ". No value on file: " + j(none_mos) + "."),
        ("BACK ORDERS  ·  CEILING 15 LINES PER EUR 100K",
         "%d of %d" % (len(bo_above), len(bo_above) + len(bo_inside)),
         "above the ceiling. Inside: " + j(bo_inside) + ". No value or no sales base on file: "
         + j(bo_none + bo_unknown) + "."),
    ]
    for n, (head, val, sub) in enumerate(tiles):
        x = 0.60 + n * 4.23
        acc = canvas(s8, x, 6.03, 0.04, 0.84, RED)
        tb = tbox(s8, x + 0.14, 6.03, 3.95, 0.84)
        say(tb, [(head, 7.4, MUTED, False, 0),
                 (val, 14.0, INK, True, 1),
                 (sub, 6.6, MUTED, False, 1)])

    # --- fold the old bottom strip into the source line, drop the strip
    strip = find(s8, "This comparison covers")
    note = "This comparison covers the nine distributors listed, not the full eleven-customer incentive programme."
    if strip is not None:
        note = strip.text_frame.text.strip()
        strip._element.getparent().remove(strip._element)
    src = find(s8, "Sources: FY2026 net billing")
    if src is not None:
        say(src, [("Sources: FY2026 net billing and 'Incentive FY27', fiscal year April 2025 - March 2026; "
                   "ITUK reviewed separately. Fill rate, days of stock and back orders from "
                   "KPI Master File august 2026.xlsx, 'Parts Handling', latest reported month per distributor; "
                   "supply-class bands and the 15-lines-per-EUR-100K ceiling from "
                   "ISZE_DB_KPI_Targets_FY2627_v1.xlsx. " + note, 6.2, MUTED, False, 0)])
        src.top = Inches(6.94)
        src.height = Inches(0.50)
    print("item 2 done (slide 8)")
    for h, v, sub in tiles:
        print("    tile:", h, "|", v, "|", sub)

    # =========================== item 3: slide 10 ==========================
    s10 = slides[9]                    # WIDER REVIEW
    lab = find(s10, "FIVE MARKETS")
    if lab:
        set_one(lab, "FIVE DISTRIBUTORS  |  REPLENISHMENT")
    card = find(s10, "Dealers bought the identified parts")
    if card:
        say(card, [("IUK, ITUK, Ireland, UTI and Greece. Dealers bought the identified parts "
                    "faster than the distributors reordered.", 8.5, MUTED, False, 0)])
    # remove the units-derived percentage introduced earlier
    head = find(s10, "The net build sat in brakes")
    if head:
        set_one(head, "The net build sat in brakes, body and electrical while the fastest-turning "
                      "maintenance family kept turning and sold on more than it bought.")
    body = find(s10, "Maintenance family kept turning")
    if body:
        say(body, [("Maintenance family kept turning: 14,662 billed, 15,007 sold on.", 8.5, MUTED, False, 0),
                   ("One brake part: 214 pieces, EUR 16,923.", 8.5, MUTED, False, 1)])
    src10 = find(s10, "Sources: headline EUR 225,744")
    if src10:
        say(src10, [("Sources: headline EUR 225,744 and 2,252 parts from "
                     "STOCK_CAMPAIGN_INSIGHTS_ALL_CUSTOMERS_20261007.md; family values from "
                     "portugal_family_stock_build.csv, whose 42 rows total EUR 225,364, so the family detail is "
                     "presented as its own value and not as a sum to the headline; part 8983767550 from "
                     "portugal_pn_stock_build.csv. The five distributors and the EUR 678,464 are the rows of "
                     "replenishment_exceptions_cy2025.csv carrying pipeline_signal 'leakage_high_sellthrough': "
                     "ITUK EUR 320,600, UTI EUR 157,983, IUK EUR 132,674, Ireland EUR 41,943, Greece EUR 25,264. "
                     "Sales to dealer is not end-customer sales.", 5.9, MUTED, False, 0)])
    print("item 3 done (slide 10)")

    # =========================== item 5: slide 19 ==========================
    s19 = slides[18]                   # THE EUROPEAN LOGIC
    fixes = [("our reference = 1.00", 3.00, 4.60, 1.20, 0.16, PP_ALIGN.RIGHT),
             ("full family", 7.31, 4.60, 1.20, 0.16, PP_ALIGN.RIGHT)]
    for txt, x, y, w, h, al in fixes:
        sh = find(s19, txt)
        if sh is not None:
            sh.left, sh.top, sh.width, sh.height = (Inches(x), Inches(y), Inches(w), Inches(h))
            sh.text_frame.paragraphs[0].alignment = al
            sh.text_frame.word_wrap = True
    cap = find(s19, "Kosha path")
    if cap is not None:
        cap.top = Inches(5.24)
        cap.height = Inches(0.18)
    for sh in s19.shapes:
        if sh.shape_type == 13 and sh.top is not None and 4.5 < sh.top / 914400 < 4.8:
            sh.top = Inches(4.62)
            sh.height = Inches(0.60)
    print("item 5 done (slide 19)")

    # =========================== item 6: slide 20 ==========================
    s20 = slides[19]                   # DECISION AND FOLLOW-UP
    KEEP_TEXT = ("no change proposed", "maintain the target", "decision requested")
    for sh in list(s20.shapes):
        t = sh.text_frame.text.strip().lower() if sh.has_text_frame else ""
        if any(t.startswith(k) for k in KEEP_TEXT):
            continue
        if sh.top is None:
            continue
        top = sh.top / 914400.0
        if top < 1.60:                 # header block
            continue
        if top > 7.0:                  # bottom note
            continue
        sh._element.getparent().remove(sh._element)

    cx, cy = 6.665, 4.55
    ring = canvas(s20, cx - 1.35, cy - 1.35, 2.70, 2.70, None, MSO_SHAPE.DONUT)
    ring.fill.solid()
    ring.fill.fore_color.rgb = GREY
    ring.line.fill.background()
    ring.shadow.inherit = False

    mid = tbox(s20, cx - 1.02, cy - 0.78, 2.04, 1.60)
    say(mid, [("The cycle feeds\nitself", 9.6, INK, True, 0),
              ("The plan is reset from the agreed monthly targets after every "
               "checkpoint.", 7.0, MUTED, False, 3)], anchor=MSO_ANCHOR.MIDDLE)

    nodes = [
        ("1", "Confirm the monthly plan\nfor each distributor", "ISZE / Japan"),
        ("2", "Check at month 6\nagainst the 10% tolerance", "ISZE / Japan"),
        ("3", "Check at month 9\nagainst the 10% tolerance", "ISZE / Japan"),
        ("4", "Review a separate\nsales-to-dealer element", "ISZE / Japan"),
        ("5", "Close the five reporting gaps;\nload ISD Feb-Jul 2026", "ISZE"),
    ]
    ang = [-90, -18, 54, 126, 198]
    Rn, bw, bh = 1.95, 2.20, 0.80
    for (num, txt, own), a in zip(nodes, ang):
        rad = math.radians(a)
        px = cx + Rn * math.cos(rad) - bw / 2
        py = cy + Rn * math.sin(rad) - bh / 2
        box = canvas(s20, px, py, bw, bh, PANEL, MSO_SHAPE.ROUNDED_RECTANGLE)
        canvas(s20, px, py, bw, 0.035, RED)
        tb = tbox(s20, px + 0.12, py + 0.13, bw - 0.24, bh - 0.26)
        say(tb, [(num + "  ·  " + own, 6.6, RED, True, 0),
                 (txt.replace("\n", " "), 7.6, INK, False, 1.4)])

    for a in (-54, 18, 90, 162, 234):
        rad = math.radians(a)
        ax, ay = cx + 1.58 * math.cos(rad), cy + 1.58 * math.sin(rad)
        arrow = canvas(s20, ax - 0.17, ay - 0.12, 0.34, 0.24, RED, MSO_SHAPE.RIGHT_ARROW)
        arrow.rotation = a + 90

    lcol = tbox(s20, 0.42, 1.90, 2.95, 3.60)
    say(lcol, [("A CONTINUOUS REVIEW CYCLE", 8.6, RED, True, 0),
               ("The five steps run as a loop rather than a one-off approval. Each "
                "checkpoint uses the agreed monthly plan, and the reporting gaps are "
                "closed before the next cycle begins.", 8.6, MUTED, False, 4),
               ("No change to the incentive rate or total.", 8.6, INK, True, 6)])
    rcol = tbox(s20, 9.90, 1.90, 3.00, 3.60)
    say(rcol, [("WHAT THE CYCLE PROTECTS", 8.6, RED, True, 0),
               ("Retain the incentive to support sales targets and secure the reporting.", 8.6, MUTED, False, 4),
               ("Use that reporting to manage stock risk and target commercial support.", 8.6, MUTED, False, 4),
               ("The evidence for the first cycle is in the notes to this slide.", 8.6, MUTED, False, 4)])
    print("item 6 done (slide 20)")

    prs.save(str(DECK))
    print("saved", DECK)

    # ---------------- verify structure -------------------------------------
    import zipfile
    z = zipfile.ZipFile(DECK)
    import re
    parts = sorted(n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n))
    print("slide parts after save:", len(parts))


if __name__ == "__main__":
    main()
