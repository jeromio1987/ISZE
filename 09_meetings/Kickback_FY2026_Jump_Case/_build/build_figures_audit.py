"""FIGURES RETIRED - corrections audit for the kickback case deck.

Independent, separate deck. Does NOT touch ISZE_Kickback_FY2026_Year_End_Jump_Case.pptx.
Answers "which figures are not good": every figure retired during the 2026-10-07 session,
with what replaced it, why it was wrong, and the file + filter behind the correction.

Audience: internal (Jerome, and anyone who saw an earlier draft of the case deck).
Style: charcoal, matching the case deck exactly (bg 262626, panel 303030, border 6E6E6E,
red E30613, amber F5A000, grey B7B7B7, green 31A354, Aptos).

Helpers (txt / rect / hline / base / table) reuse the approach in build_kickback_jump_case.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = ROOT / "09_meetings" / "Kickback_FY2026_Jump_Case"
OUT = HERE / "ISZE_Kickback_Figures_Audit_20261007.pptx"

# ── palette ─────────────────────────────────────────────────────────────────
BG, PANEL, BORDER, ROW2 = "262626", "303030", "6E6E6E", "2B2B2B"
WHITE, MUTED, GRID = "F2F2F2", "BDBDBD", "4D4D4D"
RED, AMBER, GREY, GREEN = "E30613", "F5A000", "B7B7B7", "31A354"
FONT = "Aptos"


def rgb(h):
    return RGBColor.from_string(h)


prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
PAGE = [0]


def txt(slide, x, y, w, h, text, size=10, color=WHITE, bold=False,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text if isinstance(text, list) else [text]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = FONT
        r.font.color.rgb = rgb(color)
    return tb


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(0.75)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def hline(slide, x, y, w, color, width=0.75):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y),
                                   Inches(x + w), Inches(y))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    return c


def base(section, title, sub=None, source=None, number=True):
    PAGE[0] += 1
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(BG)
    txt(s, 0.42, 0.26, 6.0, 0.2, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 7, WHITE, True)
    txt(s, 0.42, 0.52, 8.0, 0.22, section.upper(), 8, RED, True)
    txt(s, 0.42, 0.78, 11.9, 0.6, title, 20 if len(title) <= 68 else 16, WHITE, True)
    y = 1.42
    if sub:
        txt(s, 0.42, y, 12.2, 0.4, sub, 10, MUTED)
        y += 0.46
    if source:
        txt(s, 0.42, 7.06, 12.5, 0.34, source, 7, MUTED)
    if number:
        txt(s, 12.3, 0.26, 0.7, 0.2, f"{PAGE[0]:02d}", 8, MUTED, True, PP_ALIGN.RIGHT)
    hline(s, 0.42, 1.30, 12.5, GRID)
    return s, y


def kpi(slide, x, y, w, value, label, accent=RED, vsize=20):
    rect(slide, x, y, w, 0.98, PANEL)
    rect(slide, x, y, 0.045, 0.98, accent)
    txt(slide, x + 0.18, y + 0.13, w - 0.3, 0.4, value, vsize, WHITE, True)
    txt(slide, x + 0.18, y + 0.58, w - 0.3, 0.36, label, 8.3, MUTED)


def table(slide, x, y, w, header, data, col_w, row_h=0.30, hdr_h=0.34, size=9.5):
    """Table with one textbox per cell. Cells may be a 3-tuple (text, colour, bold)."""
    n = len(header)
    rect(slide, x, y, w, hdr_h, PANEL)
    cx = x
    for i, h in enumerate(header):
        al = PP_ALIGN.LEFT if i == 0 else PP_ALIGN.LEFT
        txt(slide, cx + 0.10, y + 0.085, col_w[i] - 0.16, hdr_h, h, size - 0.5, MUTED, True, al)
        cx += col_w[i]
    yy = y + hdr_h
    for ri, row in enumerate(data):
        if ri % 2 == 1:
            rect(slide, x, yy, w, row_h, ROW2)
        cx = x
        for i, cell in enumerate(row):
            col, bold, val = WHITE, False, cell
            if isinstance(cell, tuple):
                if len(cell) == 3:
                    val, col, bold = cell
                else:
                    val, col = cell
            txt(slide, cx + 0.10, yy + 0.07, col_w[i] - 0.18, row_h, str(val),
                size, col, bold, PP_ALIGN.LEFT)
            cx += col_w[i]
        yy += row_h
    hline(slide, x, yy, w, GRID)
    return yy


def bullet_block(slide, x, y, w, items, size=9.2, gap=0.68, head_size=10):
    """items = list of (head, body, colour)."""
    yy = y
    for head, body, col in items:
        rect(slide, x, yy + 0.02, 0.035, 0.5, col)
        txt(slide, x + 0.16, yy, w - 0.16, 0.26, head, head_size, WHITE, True)
        txt(slide, x + 0.16, yy + 0.24, w - 0.16, 0.42, body, size, MUTED)
        yy += gap
    return yy


# ════════════════════════════════════════════════════════════════════════════
# 1  COVER
# ════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
s.background.fill.solid()
s.background.fill.fore_color.rgb = rgb(BG)
rect(s, 0, 0, 0.09, 7.5, RED)
txt(s, 0.85, 1.24, 11.5, 0.3, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 9.5, MUTED, True)
txt(s, 0.85, 1.74, 11.8, 1.6,
    ["Figures retired — corrections audit",
     "Which numbers from the kickback case are not good, and what replaced them"], 29, WHITE, True)
hline(s, 0.85, 3.46, 6.0, RED, 1.2)
txt(s, 0.85, 3.72, 11.8, 1.3,
    "This lists every figure the kickback case deck has carried or nearly carried that does not stand up, "
    "and the corrected number behind each one. It exists because the case goes to Japan / IML management "
    "and must not carry a number we cannot stand behind.", 11, MUTED)
txt(s, 0.85, 5.20, 11.8, 1.0,
    ["Twelve figures retired  ·  each with the file, the filter and the corrected value",
     "Internal note  ·  7 October 2026  ·  all figures in EUR"], 10, GREY)

# ════════════════════════════════════════════════════════════════════════════
# 2  HOW TO READ THIS
# ════════════════════════════════════════════════════════════════════════════
s, y = base("How to read this", "Three ways a figure went wrong here — invented, artefact, superseded",
            "Each row of the table says which one it is. Nothing is asserted without a source file and a filter behind it.")
spans = [
    ("Invented", "Stated without being computed.", "A count or a euro was written from a reading or an "
     "assumption, never drawn from the data. Caught by recomputing from the source file.", RED),
    ("Artefact", "A gap or a mix change mistaken for behaviour.", "The number is arithmetically right but "
     "describes the records, not the market: a hole in an extract, or a shift between two account codes.", AMBER),
    ("Superseded", "True when written, overtaken by events.", "The figure described the world at the time "
     "and no longer does. It is not wrong — it is out of date.", GREY),
]
by = y + 0.02
cx = 0.42
for head, subh, body, col in spans:
    rect(s, cx, by, 4.02, 2.55, PANEL)
    rect(s, cx, by, 4.02, 0.05, col)
    txt(s, cx + 0.24, by + 0.32, 3.6, 0.4, head, 17, col, True)
    txt(s, cx + 0.24, by + 0.90, 3.6, 0.6, subh, 10.5, WHITE, True)
    txt(s, cx + 0.24, by + 1.44, 3.6, 1.0, body, 8.8, MUTED)
    cx += 4.235
by += 2.75
rect(s, 0.42, by, 12.49, 1.34, ROW2)
txt(s, 0.66, by + 0.16, 12.1, 0.3, "What a correction here does and does not claim", 10.5, WHITE, True)
txt(s, 0.66, by + 0.52, 12.1, 0.8,
    "Every correction was re-derived from source; where the corrected figure is itself an estimate or a range, "
    "it is written as one. One item (the ISD resumption) is real but not verified from a file on disk, and is "
    "marked reported-not-verified on the table rather than asserted.", 8.8, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 3  THE TABLE — part 1 (items 1-6)
# ════════════════════════════════════════════════════════════════════════════
HDR = ["Figure used", "What is correct", "Why it was wrong"]
CW = [3.30, 4.45, 4.74]
ROWS1 = [
    [("Nine of ten distributors\nat or above plan", RED, True),
     ("Seven of nine. ITUK is intercompany and is excluded,\nso the denominator is 9.", WHITE, True),
     "Invented. Written from the plan table without computing it from billing."],
    [("Five of them by more\nthan 12%", RED, True),
     ("Four: IUK (+12.26%), ISD/Germany (+12.52%),\nNorway (+14.13%), Sweden (+12.30%).", WHITE, True),
     "Invented. Counted loosely; only those four plan increases exceed 12%."],
    [("ITUK February 2026\n= EUR 383,245", RED, True),
     ("EUR 346,195 — February billing EUR 861,719\nless the Apr-25–Jan-26 run rate EUR 515,524.", WHITE, True),
     "Invented. The source row's parts sum to EUR 798,761 against the\ncustomer's true Feb+Mar increase of EUR 771,238."],
    [("IBX order mix: '48% → 54% planned',\n'52% → 46% urgent', '67% Feb-Mar'", RED, True),
     ("Planned share 53.79% (FY2026) → 54.80% (FY2027 YTD)\n= +1.01 pp — and that is not real. Remove the gap\nand it falls 1.69 pp; with December too, 3.73 pp.", WHITE, True),
     "Artefact. IBX's order records stop 14 Apr 2025 and resume\n21 May 2025; the missing weeks were all-urgent, dragging\nthe baseline down and manufacturing the rise."],
    [("ISD 'minus 4.46 pp\nplanned decline'", RED, True),
     ("No change in ordering behaviour. It is the euro split\nbetween sold-to 2516 (planned in 17 of 20 months)\nand 601 (0.0% planned in all 20).", WHITE, True),
     "Artefact. Code 93 has zero rows anywhere. The blend is\narithmetically the always-planned code's share."],
    [("Cross-market stock-vs-fill\ncorrelation '+0.41'", RED, True),
     ("Latest-reading snapshot +0.386 (18 markets); average\nof the 25 monthly readings +0.248 (range −0.92 to +0.51).", WHITE, True),
     "Overstated. +0.42 is the single best month (Jul 2026, 9\nmarkets), quoted as the general relationship."],
]
s, y = base("The retired figures — 1 of 2", "Every figure withdrawn, with the correction and the reason")
table(s, 0.42, y + 0.08, 12.49, HDR, ROWS1, CW, row_h=0.80, hdr_h=0.34, size=8.3)
txt(s, 0.42, 6.62, 12.6, 0.3,
    "Sources — item 1-2: sales_fact.parquet billing by sold_to vs budget_per_DB_reviewed_24042026.xlsx, "
    "'Incentive FY27'. Item 3: sales_fact.parquet, sold-to 2575. Items 4-5: SOR_VOR_IMPROVEMENT_IBX_ISD_20261007.md, §9. "
    "Item 6: STOCK_FILL_VERIFICATION_20261007.md.", 7, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 4  THE TABLE — part 2 (items 7-12)
# ════════════════════════════════════════════════════════════════════════════
ROWS2 = [
    [("'0.6 points of fill'\nfrom extra stock", RED, True),
     ("+0.40 pp mean per-market on the ISZE book; +0.82 pp\nacross all markets (pooled +0.21 / +0.91).", WHITE, True),
     "Overstated. The direction (little gain from more stock)\nholds; the decimal is not reproducible as stated."],
    [("'IBX stopped reporting\nfill in April 2025'", RED, True),
     ("March 2025. Last fill of any kind 81.77% (Mar 2025);\nlast fill at or above 85% was February 2025 (87.45%).\nThe 48-day stock figure is April 2026.", WHITE, True),
     "Invented date. It made the stock and the fill reading\nlook as if they overlapped. They never did."],
    [("Target-file rationale\n'RAISE stock: 48d starves\n85% fill'", RED, True),
     ("The literal string is in the target file (IBX row,\nRationale). It pairs a 2026 stock reading with a fill\nreading from before April 2025 — never coexisted.", WHITE, True),
     "Unsupported pairing. The rationale as written cannot\nbe evidenced from the file it sits in."],
    [("'ITUK and Benelux both ran\nbehind plan and jumped';\nITUK = one rebate event", RED, True),
     ("Only ITUK ran behind and jumped; Benelux's rise was\ninstructed. February EUR 346,195 is a plan recovery,\nnot a price effect; March is largely a forward-buy.", WHITE, True),
     "Invented. Two distributors conflated, and a two-month\nmove attributed to a single cause."],
    [("'IBX places a stock order\nevery other week'", RED, True),
     ("Dropped. The sourced line is that Astara 'has shifted\ntoward holding more own stock and less VOR ordering'.", WHITE, True),
     "Invented. Traced to an Astara assertion our own minutes\ncontradict; the cadence claim is not in the minutes."],
    [("'ISD has not reported stock\nor fill for twenty months'", RED, True),
     ("True as history; no longer safe as written. ISD resumed\n2 Oct 2026 with Feb–Jul 2026 — reported, not verified\nfrom a file on disk. State as indicative, never fact.", AMBER, True),
     "Superseded. Overtaken by the resumed submission;\nthose months are not yet loaded or validated."],
]
s, y = base("The retired figures — 2 of 2", "Every figure withdrawn, with the correction and the reason")
table(s, 0.42, y + 0.08, 12.49, HDR, ROWS2, CW, row_h=0.80, hdr_h=0.34, size=8.3)
txt(s, 0.42, 6.62, 12.6, 0.3,
    "Sources — items 7-8: STOCK_FILL_VERIFICATION_20261007.md (IBX series, last 6 months). Item 9: "
    "ISZE_DB_KPI_Targets_FY2627_v1.xlsx, 'Targets FY26-27', IBX row. Item 10: sales_fact.parquet 2575; "
    "price_bp_weighted_compare_meta.json. Item 11: 12 Aug 2026 Astara WE minutes. Item 12: KPI Master File.", 7, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 5  DEEP DIVE — IBX ORDER MIX  (item 4)
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Retired — IBX order mix", "The one positive order-mix number was manufactured by a five-week hole in the records",
    source="Source: SOR_VOR_IMPROVEMENT_IBX_ISD_20261007.md §9, from order_headers_from_Order_Detail.csv — IBX sold-to 90, "
           "617 documents, planned = SOR+PRD, urgent = VOR+RUSH+SVOR, by order value. Billing side: sales_fact.parquet.")
kpi(s, 0.42, y + 0.05, 3.05, "{:+.2f} pp".format(1.01), "As the file stands — a rise (not real)", AMBER)
kpi(s, 3.60, y + 0.05, 3.05, "−1.69 pp", "With the five-week gap removed — a fall", RED)
kpi(s, 6.78, y + 0.05, 2.85, "−3.73 pp", "With the December timing too", RED)
kpi(s, 9.76, y + 0.05, 3.15, "+2.98 pp", "Only clean Jun–Aug window, on falling volume", GREEN)
rows = [
    ["IBX planned share, FY2026 → FY2027 YTD, as the file stands", "53.79% → 54.80%",
     ("+1.01 pp", AMBER, True), "Manufactured by the gap in the baseline"],
    ["IBX, gap months removed from the FY2026 baseline", "56.49% → 54.80%",
     ("−1.69 pp  (−EUR 15,040)", RED, True), "The sign flips: the planned share falls"],
    ["IBX, gap and Dec-25 timing removed", "58.53% → 54.80%",
     ("−3.73 pp  (−EUR 33,173)", RED, True), "Falls further once the timing is corrected"],
    ["IBX, only clean gap-free like-for-like (Jun–Aug)", "55.18% → 58.16%",
     ("+2.98 pp  (≈ +EUR 8,600)", GREEN, True), "On falling volume — inside the noise"],
]
yy = table(s, 0.42, y + 1.22, 12.49, ["Reading", "Planned share of order value", "Change", "What it means"], rows,
           [4.40, 2.75, 2.20, 3.14], row_h=0.42, size=8.6)
txt(s, 0.42, yy + 0.20, 12.6, 1.1,
    ["The filter: sold-to 90; planned = SOR+PRD; urgent = VOR+RUSH+SVOR, by order value. IBX's order records stop on "
     "14 April 2025 and resume on 21 May 2025; 555 documents worth EUR 2.62M for fifteen other customers sit in that "
     "same document range. Those missing weeks were all urgent.",
     "Read it as: stocking improved (the stock file is clean), but the direct order-mix evidence is not usable for FY2026. "
     "No slide should claim an IBX planned-versus-urgent improvement."], 8.8, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 6  DEEP DIVE — ITUK FEBRUARY  (item 3)
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Retired — the ITUK February figure", "EUR 383,245 was taken from a row that does not reconcile with the customer's own year",
    source="Source: sales_fact.parquet, sold-to 2575, monthly net sales value. Wrong figure from "
           "_order_insights_20261007/22_price_recon_attribution_split.csv, ITUK (2575) row.")
kpi(s, 0.42, y + 0.05, 3.05, "EUR 383,245", "The retired figure", RED)
kpi(s, 3.60, y + 0.05, 3.05, "EUR 346,195", "February billing less run rate", GREEN)
kpi(s, 6.78, y + 0.05, 2.85, "EUR 37,050", "Overstatement in the retired figure", AMBER)
kpi(s, 9.76, y + 0.05, 3.15, "EUR 861,719", "February 2026 billing, from source", WHITE)
rows = [
    ["ITUK run rate, Apr 2025 – Jan 2026 (10 months)", "EUR 515,524 per month", "Mean of ten monthly billings"],
    ["February 2026 billing", "EUR 861,719", "From sales_fact.parquet, sold-to 2575"],
    ["February excess over run rate (correct)", ("EUR 346,195", GREEN, True), "What the case deck now uses"],
    ["Split row, total of its three parts", ("EUR 798,761", RED, True), "Above ITUK's true Feb+Mar increase of EUR 771,238"],
]
yy = table(s, 0.42, y + 1.22, 12.49, ["ITUK, February 2026", "Value", "Where it comes from"], rows,
           [5.60, 3.30, 3.59], row_h=0.42, size=8.6)
txt(s, 0.42, yy + 0.22, 12.6, 1.2,
    ["The filter: sold-to 2575; run rate = mean of the ten monthly billings Apr 2025 to Jan 2026; February excess = "
     "February billing less that run rate.",
     "The retired EUR 383,245 came from the ITUK row of the price-reconciliation split file. That row's February "
     "component (EUR 383,245) and its three-part total (EUR 798,761) both exceed what billing supports: February "
     "recomputes to EUR 346,195 and February-plus-March to EUR 771,238. February is recomputed straight from billing."], 8.8, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 7  DEEP DIVE — STOCK VERSUS FILL  (items 6 + 7 + 8)
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Retired — the stock-versus-fill claim", "Three numbers from the same claim: the correlation, the fill gain, and a date that never existed",
    source="Source: STOCK_FILL_VERIFICATION_20261007.md, from KPI Master File august 2026.xlsx, sheet 'Parts Handling' — "
           "blocks 'Days of Parts in Stock' and 'First Fill Rate', paired on the same distributor and month. 304 paired "
           "distributor-months, 18 markets, Apr 2024 – Jul 2026.")
# small table of the three
rows = [
    ["The correlation across markets", "'+0.41'",
     ("+0.386 latest reading; +0.248 average month", AMBER, True),
     "One strongest month quoted as the general level"],
    ["Fill bought by extra stock", "'0.6 points'",
     ("+0.40 pp on the book; +0.82 pp all markets", AMBER, True),
     "The decimal is not reproducible as stated"],
    ["When IBX stopped reporting fill", "'April 2025'",
     ("March 2025 (last 85%+ fill: Feb 2025)", RED, True),
     "A one-month error that invented an overlap"],
]
yy = table(s, 0.42, y + 0.08, 12.49, ["Figure used", "As retired", "What is correct", "Why it was wrong"], rows,
           [3.60, 2.10, 4.30, 2.49], row_h=0.56, size=8.6)
# IBX series strip
txt(s, 0.42, yy + 0.22, 6.0, 0.3, "IBX: the fill readings stop before the stock readings begin", 10.5, WHITE, True)
ibx = [("Jun 24", "0.737"), ("Oct 24", "0.842"), ("Dec 24", "0.853"), ("Jan 25", "0.852"),
       ("Feb 25", "0.875"), ("Mar 25", "0.818"), ("Apr 25", "—"), ("Apr 26", "48 d"), ("Jul 26", "63 d")]
cx = 0.42
for lab, val in ibx:
    fill = "—" not in val and "d" not in val
    rect(s, cx, yy + 0.58, 1.30, 0.62, PANEL)
    rect(s, cx, yy + 0.58, 1.30, 0.045, GREEN if fill else AMBER)
    txt(s, cx + 0.10, yy + 0.68, 1.15, 0.24, val, 10.5, WHITE if fill else AMBER, True)
    txt(s, cx + 0.10, yy + 0.96, 1.15, 0.2, lab, 7.2, MUTED)
    cx += 1.365
txt(s, 0.42, yy + 1.34, 12.6, 1.0,
    ["Green = a reported fill rate; amber = a days-of-stock reading. The two series do not overlap: IBX's last fill "
     "was March 2025 (81.77%) and its first stock reading is April 2025. The '48 days' the target-file rationale "
     "pairs with '85% fill' is an April 2026 stock reading, twelve months after the last fill.",
     "Within a market over time — the number that actually answers the stocking question — the link is +0.085 all "
     "markets and +0.009 across the ISZE book. Raising a market's own stock has not lifted its fill."], 8.8, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 8  DEEP DIVE — TARGET-FILE RATIONALE  (items 8 + 9)
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Retired — the target-file rationale", "The rationale pairs a 2026 stock reading with a fill reading that stopped a year earlier",
    source="Source: ISZE_DB_KPI_Targets_FY2627_v1.xlsx, sheet 'Targets FY26-27', row 8 'IBX (incl. Polska)', "
           "column Y 'Rationale'. Read the cell; quoted exactly.")
rect(s, 0.42, y + 0.06, 12.49, 1.20, PANEL)
rect(s, 0.42, y + 0.06, 0.05, 1.20, RED)
txt(s, 0.68, y + 0.20, 12.1, 0.3, "The cell, verbatim", 10.5, WHITE, True)
txt(s, 0.68, y + 0.54, 12.1, 0.7,
    "“RAISE stock: 48d starves 85% fill. IMIT 845 = BE row only; PL/NL volumes unresolved in IMIT — verify. "
    "Parts = IBX 6.55M + PL 1.19M.”", 9.6, WHITE)
yy = y + 1.44
items = [
    ("The stock half is a 2026 reading.", "48 days of parts in stock is the April 2026 reading for IBX "
     "(its stock series runs 26 days in May 2025 to 63 days in July 2026).", AMBER),
    ("The fill half is from before April 2025.", "The last fill IBX reported at or above 85% was February 2025 "
     "(87.45%); its last fill of any kind was March 2025 (81.77%).", RED),
    ("There is no month where both existed.", "IBX stopped reporting fill the same month it began reporting stock. "
     "The gap is a clean handover, not an overlap — the two numbers never coexisted.", RED),
    ("So the rationale as written is unsupported.", "It is not a finding about IBX; it is two readings from "
     "different years placed in one sentence. Nothing in the target file evidences it.", GREY),
]
bullet_block(s, 0.42, yy, 12.6, items, size=9.0, gap=0.72)
txt(s, 0.42, 6.50, 12.6, 0.5,
    "What a file-backed rationale would need: either a month where IBX reported both stock and fill, or a market that "
    "demonstrably ran low stock and low fill together. The verification found four such paired months (IMF and KIMA) "
    "— neither is IBX.", 8.6, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 9  DEEP DIVE — THE PLAN COUNTS  (items 1 + 2)
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Retired — the plan counts", "Two counts in one sentence on the case deck's plan slide, both written without computing them",
    source="Source: sales_fact.parquet, billing by sold_to_sap, fiscal year Apr 2025 – Mar 2026, against "
           "budget_per_DB_reviewed_24042026.xlsx, sheet 'Incentive FY27'. ITUK (2575) excluded as intercompany.")
kpi(s, 0.42, y + 0.05, 3.05, "7 of 9", "At or above plan, FY2026 billing", GREEN)
kpi(s, 3.60, y + 0.05, 3.05, "4 of 9", "Plan increases above 12%", AMBER)
kpi(s, 6.78, y + 0.05, 2.85, "ITUK", "Excluded — intercompany", GREY)
kpi(s, 9.76, y + 0.05, 3.15, "9", "The correct denominator", WHITE)
rows = [
    ["IUK", "+11.99%", "+12.26%", ("above plan, above 12%", GREEN, True)],
    ["UTI", "+10.81%", "+5.87%", "above plan, plan rise under 12%"],
    ["UMI", "+13.53%", "+9.61%", "above plan, plan rise under 12%"],
    ["Germany (ISD)", "+5.50%", "+12.52%", ("plan rise above 12%", AMBER, True)],
    ["Benelux (IBX)", "−0.84%", "+3.37%", "behind plan"],
    ["Portugal", "+7.72%", "+7.99%", "above plan"],
    ["Sweden", "+10.31%", "+12.30%", ("above plan, plan rise above 12%", GREEN, True)],
    ["Norway", "+6.94%", "+14.13%", ("plan rise above 12%", AMBER, True)],
    ["Ireland", "−1.32%", "+9.21%", "behind plan"],
]
yy = table(s, 0.42, y + 1.22, 12.49,
           ["Distributor", "Billed FY2026 vs plan FY2026", "Plan increase FY26 → FY27", "Reading"], rows,
           [2.60, 3.30, 3.10, 3.49], row_h=0.315, size=8.6)
txt(s, 0.42, yy + 0.18, 12.6, 0.9,
    ["The count of distributors at or above plan is a billing-versus-plan calculation (left pair of number columns): "
     "seven of nine. ITUK is intercompany and is excluded, which is why the denominator is 9 and not 10.",
     "The 'more than 12%' count is a plan-increase figure (middle column): exactly four plan increases exceed 12% — "
     "IUK, ISD (Germany), Norway and Sweden. Both counts are recomputed from source, not read from the deck."], 8.6, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 10  WHICH CAME FROM ME
# ════════════════════════════════════════════════════════════════════════════
s, y = base("Where these came from", "Three of the retired figures originated with the assistant, not with the analysis",
            "Stated plainly: each was written without computing it, and each was caught by checking it against source.")
items = [
    ("The plan count — 'nine of ten'.", "Originated with the assistant. Written from the plan table without "
     "counting the billing; it is seven of nine, and ITUK is not a distributor.", RED),
    ("The 12% count — 'five of them'.", "Originated with the assistant. Counted roughly; only four plan "
     "increases exceed 12%, and they are IUK, ISD, Norway and Sweden.", RED),
    ("The ITUK February figure — EUR 383,245.", "Originated with the assistant. Taken from a reconciliation "
     "row that overstates February; the correct figure is EUR 346,195.", RED),
]
bullet_block(s, 0.42, y + 0.10, 12.6, items, size=9.6, gap=1.05, head_size=11)
rect(s, 0.42, y + 3.42, 12.49, 1.42, ROW2)
txt(s, 0.66, y + 3.56, 12.1, 0.3, "The pattern, and the fix", 11, WHITE, True)
txt(s, 0.66, y + 3.92, 12.1, 0.9,
    "All three share one failure: a number was written from a reading or an assumption rather than recomputed from "
    "the file. Each was caught only when it was recomputed against source, which is also what found the two artefact "
    "errors — the IBX records gap and the ISD code mix. The rule that follows: no figure goes on a slide unless the "
    "file, the filter and the row count behind it can be named at the moment it is written.", 9.0, MUTED)

# ════════════════════════════════════════════════════════════════════════════
# 11  WHAT REMAINS SOUND
# ════════════════════════════════════════════════════════════════════════════
s, y = base("What remains sound", "Five things the audit did not withdraw — each with the scope it was checked on, plus the one limit",
    source="Sources: budget_per_DB_reviewed_24042026.xlsx ('Incentive FY27'); KPI Master File august 2026.xlsx "
           "('Parts Handling'); price_bp_weighted_compare_meta.json; SOR_VOR_IMPROVEMENT_IBX_ISD_20261007.md (§4c); "
           "the FY2026 year-end review ('Kosha Gap & FY2027').")
rows = [
    ["The kickback total and its structure", "EUR 393,000 across eleven customers, 1.16–1.31% of each customer's plan",
     ("Verified", GREEN, True)],
    ["IBX stock rebuild (from the stock file)", "IBX only: 32 days (Jan 2026) → 63 days (Jul 2026), into its 60–75 day band",
     ("Verified", GREEN, True)],
    ["The 13 March 2026 price change", "+5.96% weighted across the whole ISZE book; step EUR 1,652,140.71",
     ("Verified", GREEN, True)],
    ["Derived order file against raw workbook", "IBX and ISD only: EUR 0.00 gap — IBX EUR 3,895,782.14, ISD EUR 4,522,260.63",
     ("Verified", GREEN, True)],
    ["The network plan ramp", "FY2026 EUR 29.19M → FY2027 EUR 31.82M (+9.0%); Kosha path to FY2031",
     ("Verified", GREEN, True)],
    ["The rest of the order file", "Not reconciled. The check above covers IBX and ISD only; no other customer was tested.",
     ("Limit", AMBER, True)],
]
yy = table(s, 0.42, y + 0.10, 12.49, ["What stands", "The figure, and its scope", "Status"], rows,
           [4.40, 6.50, 1.59], row_h=0.60, size=9.0)
txt(s, 0.42, yy + 0.28, 12.6, 1.5,
    ["These are the numbers the case can lean on, each with the scope it was checked on. The kickback total reads "
     "straight from the plan workbook; the IBX stock rebuild comes from the stock file, which carries no gap; the "
     "price change is dated, measured, and covers the whole book.",
     "The reconciliation of the derived order file against the raw workbook was run on IBX and Germany/ISD — those two "
     "customers, EUR 0.00 gap on both — and on no others. It must not be read as the whole order file reconciling.",
     "One caution carried over from the retired list: the FY2027 plan ramp is sound, but the monthly shape it is "
     "measured against must be confirmed per distributor before the 6- and 9-month checks are read on a pro-rata."], 8.6, MUTED)

prs.save(OUT)
print("written", OUT, f"({OUT.stat().st_size/1024:.0f} KB, {len(prs.slides._sldIdLst)} slides)")
