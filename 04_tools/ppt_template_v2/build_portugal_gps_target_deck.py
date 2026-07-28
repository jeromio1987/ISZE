"""
Portugal Sales Meeting deck — I-Motors, 29 July 2026.
Full agenda per Masumi Hayakawa's email (23-07-2026): Q1 Sales Review, GPS,
PMS, SPA, R&M, genuine parts share / FY2027 target, data request.

Sources:
  - Q1 FY27 Portugal actuals: accounting/PowerBI Q1 FY2027 report, provided
    directly by Jerome 2026-07-28 (screenshot) — Sales amount EUR140K/151K/153K
    (Apr/May/Jun), Budget EUR148K/141K/163K, prior year EUR116K/140K/169K.
    Supersedes an earlier cut from q1fy2027_billing_tagged.csv (GPS-signed
    basis, net_value_gps_signed), which totalled EUR404,830 vs PowerBI's
    EUR445K Sales amount — a real basis gap (~9%), not yet reconciled; use
    PowerBI as authoritative per Jerome. That earlier cut's prior-year number
    (from 01_data\\00_derived\\cy2025_raw.csv) matched PowerBI closely
    (EUR425,276 vs EUR425K), so the gap is specific to the 2026 side.
  - GPS: 01_data\\00_derived\\gps_master.csv, row 'Imotors' — net_FY2025 /
    max_spend, where max_spend = uio_2025(8,019) x flat rate(EUR250/unit for
    EVERY vehicle, trucks included) = EUR2,004,750 -> 74.0%. That flat rate is
    the LCV/D-Max rate applied network-wide regardless of vehicle class - not
    the segmented N35/N75+/F-series/LCV pricing this deck uses elsewhere.
    Recomputed on the same actual (net_FY2025 EUR1,483,250) against a properly
    segmented Max Spend (this deck's own CY2025 figure, EUR2,343,140) -> 63.3%.
    Note: gps_master.csv's own column is literally named 'gps_pct_FY2025'
    (fiscal Apr'24-Mar'25), not calendar 2025 - flagging this date-basis
    question openly rather than asserting either label with confidence.
  - PMS: 01_data\\00_derived\\pms_capture_by_db_year.csv, distributor_code==
    'PORTUGAL', year==2025, line_type=='total' - queried directly 2026-07-28,
    the same day this file was last regenerated. Supersedes the PMS brief
    (01_data\\00_derived\\pms_briefs\\PORTUGAL_pms_capture.md, stale since
    2026-06-13) used in the previous version of this deck - several category
    rates differ by roughly 2x between the two; the fresher, same-day-sourced
    numbers are used here.
  - Fleet/target: Matriculas Isuzu SAP.xlsx (real registrations) cohort-decayed
    on the IMIT survival curve; ISZE_GPS_Extended_Target_FY27_V3.1.xlsx (FY26
    actuals, target formula); prism\\data\\gps_model_targets.csv (per-segment
    rates incl. N35 Grafter split, corrected 2026-07-28 16:33 WEDT).
  - SPA / R&M: no PN list exists for SPA. R&M has no ISZE-side definition on
    record; per Jerome's direction this is rebuilt as discussion questions for
    the room (LCV market/fleet, P700 R&M rollout, tender linkage), not as a
    status slide, and does not name any internal colleague.
  See memory project_uio_v20.md for full derivation history.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import isze_chart_theme as ct
import isze_deck_builder as db
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

ct.FONT_FAMILY = "Calibri"

CHART_DIR = os.path.join(HERE, "charts_out", "portugal_gps_target")
os.makedirs(CHART_DIR, exist_ok=True)


def cp(name):
    return os.path.join(CHART_DIR, name)


RED = RGBColor(0xCC, 0x0E, 0x1E)
RED_LIGHT = RGBColor(0xDC, 0x60, 0x6E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x5A, 0x5A, 0x5A)
GRAY_BG = RGBColor(0xEC, 0xEC, 0xEC)


def styled_table(slide, rows_data, left, top, width, height, col_widths, bold_last_row=True):
    n_rows, n_cols = len(rows_data), len(rows_data[0])
    tbl = slide.shapes.add_table(n_rows, n_cols, left, top, width, height).table
    for c, w in enumerate(col_widths):
        tbl.columns[c].width = w
    for r in range(n_rows):
        for c in range(n_cols):
            cell = tbl.cell(r, c)
            cell.text = rows_data[r][c] if rows_data[r][c] else " "
            para = cell.text_frame.paragraphs[0]
            if not para.runs:
                para.add_run().text = ""
            run = para.runs[0]
            run.font.size = Pt(12.5)
            run.font.name = "Calibri"
            para.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.RIGHT
            cell.vertical_anchor = 3
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            is_last = bold_last_row and r == n_rows - 1
            if r == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = RED
                run.font.bold = True; run.font.color.rgb = WHITE
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = GRAY_BG if is_last else (WHITE if r % 2 == 1 else GRAY_BG)
                run.font.bold = is_last
                run.font.color.rgb = RED if is_last else BLACK
    return tbl


def rounded_rect(slide, left, top, width, height, fill_color):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    try:
        shp.adjustments[0] = 0.06
    except Exception:
        pass
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def badge(slide, cx_left, cy_top, diameter, letter, bg=RED):
    oval = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx_left, cy_top, diameter, diameter)
    oval.fill.solid(); oval.fill.fore_color.rgb = bg
    oval.line.fill.background()
    oval.shadow.inherit = False
    tf = oval.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = letter
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = WHITE
    r.font.name = "Calibri"
    return oval


def card(slide, left, top, width, height, badge_letter, header, lines, badge_color=RED):
    rounded_rect(slide, left, top, width, height, GRAY_BG)
    d = Inches(0.5)
    badge(slide, left + Inches(0.22), top + Inches(0.22), d, badge_letter, bg=badge_color)
    db.txt(slide, header, left + Inches(0.9), top + Inches(0.22), width - Inches(1.1), Inches(0.45),
           size=15, bold=True, color=BLACK)
    db.bullet_list(slide, lines, left + Inches(0.32), top + Inches(0.85),
                    width - Inches(0.6), height - Inches(1.0), size=12.5, line_spacing=1.15)


# ============================================================================
# Charts
# ============================================================================
ct.bar_chart(
    ["Apr", "May", "Jun"],
    {"2026 (EUR K)": [140, 151, 153], "2025 (EUR K)": [116, 140, 169]},
    cp("q1_portugal_monthly.png"),
    title="Portugal Q1 — Sales Amount, Apr-Jun 2025 vs 2026 (EUR K)",
    ylabel="EUR K",
    value_fmt="{:,.0f}",
    figsize=(10.2, 4.3),
)

def diverging_bar_chart(categories, values, filename, title=None, figsize=(10.2, 4.3)):
    import matplotlib.pyplot as plt
    import numpy as np
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    fig.patch.set_facecolor(ct.WHITE)
    ax.set_facecolor(ct.WHITE)
    for spine in ("top", "right", "left", "bottom"):
        ax.spines[spine].set_visible(False)
    ax.axhline(0, color=ct.GRAY_LIGHT, linewidth=1, zorder=2)
    ax.tick_params(axis="x", colors=ct.GRAY, labelsize=11, length=0)
    ax.tick_params(axis="y", colors=ct.GRAY, labelsize=10, length=0)
    ax.yaxis.grid(True, color=ct.GRAY_BG, linewidth=1.2, zorder=0)
    ax.set_axisbelow(True)
    x = np.arange(len(categories))
    colors = [ct.RED if v < 0 else ct.CHARCOAL for v in values]
    bars = ax.bar(x, values, color=colors, width=0.6, zorder=3)
    for b, v in zip(bars, values):
        va = "top" if v < 0 else "bottom"
        offset = -4 if v < 0 else 4
        ax.annotate(f"{v:+,.0f}", (b.get_x() + b.get_width() / 2, v),
                    xytext=(0, offset), textcoords="offset points",
                    ha="center", va=va, fontsize=9.5, color=ct.CHARCOAL, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11, color=ct.CHARCOAL)
    ymax = max(values) * 1.3
    ymin = min(values) * 1.3
    ax.set_ylim(ymin, ymax)
    if title:
        ax.set_title(title, fontsize=13, color=ct.CHARCOAL, loc="left", fontweight="bold", pad=12)
    fig.tight_layout(pad=0.6)
    fig.savefig(filename, dpi=200, facecolor=ct.WHITE)
    plt.close(fig)

diverging_bar_chart(
    ["Brake\nparts", "Clutch\nparts", "Starter/\nalternator", "Filters", "Transmission", "Electrical\nsensors"],
    [-34215, -8491, -5509, 12942, 18947, 22580],
    cp("h1_category_movers.png"),
    title="Portugal H1 2026 vs H1 2025 — biggest category moves (EUR)",
)

ct.bar_chart(
    ["Oil\nFilter", "Fuel\nFilter", "Air\nFilter", "Urea\nFilter", "Blower\nFilter"],
    {"Portugal capture % CY2025": [52.1, 44.9, 62.7, 1.1, 24.2]},
    cp("pms_portugal_filters.png"),
    title="Portugal — Filter Capture Rate by Category, CY2025 (%)",
    ylabel="%",
    value_fmt="{:,.1f}",
    figsize=(10.2, 4.3),
)

YEARS = ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]
TRUCKS = [1586.9, 1701.2, 1949.1, 2187.0, 2464.4, 2661.3, 2666.6, 2940.9]
PICKUPS = [3148.0, 3140.8, 3183.7, 3287.9, 3635.0, 4281.2, 4568.8, 4968.0]

ct.trend_line(
    YEARS,
    {"Pickups": PICKUPS, "Trucks": TRUCKS},
    cp("uio_trend.png"),
    title="Portugal fleet, built from your own registration records — 4,735 (2019) to 7,909 (2026)",
    value_fmt="{:,.0f}",
)

# ============================================================================
# Assemble deck
# ============================================================================
prs = db.new_presentation()

db.build_cover(
    prs,
    title="Portugal Sales Review\n& FY2027 Target",
    subtitle="I-Motors  ·  29 July 2026",
    eyebrow="ISZE  ·  PORTUGAL  ·  I-MOTORS",
)

# ---- Slide 2: Agenda --------------------------------------------------------
s = db.build_content(prs, "Agenda", eyebrow="I-Motors Meeting", page_no=2)
db.bullet_list(
    s,
    [
        "Q1 FY2027 Sales Review",
        "Parts Performance — H1 category movers",
        "Parts Performance — Brakes",
        "Parts Performance — Clutch",
        "Parts Performance — New Business",
        "GPS Capture",
        "PMS Coverage",
        "Fleet & FY2027 Target",
        "SPA — status",
        "R&M — market discussion",
        "Data request: Sales-to-Dealer, from 01/01/2025",
        "Next steps",
    ],
    Inches(0.32), Inches(1.35), Inches(11.5), Inches(4.5), size=16,
)

# ---- Slide 3: Q1 Sales Review, with YoY -------------------------------------
db.build_two_col(
    prs,
    title="Q1 FY2027: EUR 445K, +5% YoY — EUR 452K budget, -2%",
    chart_path=cp("q1_portugal_monthly.png"),
    eyebrow="Q1 FY2027 Sales Review (Apr-Jun 2026)",
    page_no=3,
    takeaways=[
        "Sales EUR 445K vs Budget EUR 452K — -2%, essentially on plan.",
        "vs prior year EUR 425K — +5% growth.",
        "By month vs budget: Apr -5%, May +8%, Jun -6% — May ahead, April and June a touch behind.",
        "By month vs last year: Apr +21%, May +8%, Jun -9% — strong start, softer close to the quarter.",
    ],
)

# ---- Slide 4: Parts performance — H1 category movers -------------------------
db.build_two_col(
    prs,
    title="Parts performance: strong growth, two categories to watch",
    chart_path=cp("h1_category_movers.png"),
    eyebrow="Parts Performance (H1 2026 vs H1 2025)",
    page_no=4,
    takeaways=[
        "H1 2026 EUR 935K vs H1 2025 EUR 815K overall — the +15% is broad-based: electrical sensors, transmission, steering and filters are all up 25-50%.",
        "Two categories moved the other way: brake parts (-33%) and clutch parts (-20%).",
        "Neither drop shows up as a shift to our own value-tier range — it's not a trade-down we can see on our side.",
        "We'd like to understand what's behind it from your side — availability, fitment, local competition — happy to go through specifics together.",
    ],
)

# ---- Slide 5: Brake parts detail ---------------------------------------------
s = db.build_content(prs, "Brake parts: -33%, and it's not a value-tier switch", eyebrow="Parts Performance — Brakes", page_no=5)
db.bullet_list(
    s,
    [
        "EUR 102,894 (H1'25) -> EUR 68,680 (H1'26), down EUR 34,215.",
        "Biggest single line: PAD KIT, CALIPER/DISC BRK FRT, EUR 17,342 -> EUR 0. Two more brake pad lines also dropped to exactly zero.",
        "Checked on our side: none of this shows up as a shift to our own value-tier (BVP) range — the volume simply isn't landing with us, either way.",
    ],
    Inches(0.32), Inches(1.35), Inches(11.5), Inches(2.3), size=15,
)
db.txt(s, "Questions for us to work through together", Inches(0.32), Inches(3.85), Inches(9.4), Inches(0.3), size=13, bold=True, color=RED)
db.bullet_list(
    s,
    [
        "Has anything changed in how you source brake pads recently?",
        "Any fitment or catalog issues you've run into on specific part numbers?",
        "Is this a deliberate move, or more of a service/availability gap on our end?",
    ],
    Inches(0.32), Inches(4.2), Inches(11.5), Inches(2.0), size=15,
)

# ---- Slide 6: Clutch parts detail --------------------------------------------
s = db.build_content(prs, "Clutch parts: -20%, worth a closer look together", eyebrow="Parts Performance — Clutch", page_no=6)
db.bullet_list(
    s,
    [
        "EUR 41,807 (H1'25) -> EUR 33,316 (H1'26), down EUR 8,491.",
        "Same check as brakes: no shift to our value-tier (BVP) range on the clutch side either.",
    ],
    Inches(0.32), Inches(1.35), Inches(11.5), Inches(1.6), size=15,
)
db.txt(s, "Questions for us to work through together", Inches(0.32), Inches(3.15), Inches(9.4), Inches(0.3), size=13, bold=True, color=RED)
db.bullet_list(
    s,
    [
        "Is clutch pricing specifically a barrier against local competition for you?",
        "What would make the biggest difference to keep this business with us?",
        "Worth a joint look at the 2-3 part numbers with the biggest gap?",
    ],
    Inches(0.32), Inches(3.5), Inches(11.5), Inches(2.0), size=15,
)

# ---- Slide 7: New business ----------------------------------------------------
s = db.build_content(prs, "New in 2025: five part numbers with real, sustained demand", eyebrow="Parts Performance — New Business", page_no=7)
styled_table(
    s,
    [
        ["Part", "Description", "First seen", "H1 2026"],
        ["7552933240 / 7552933280 / 7552887860", "METER COMPL; CLUSTER", "Aug-Dec 2025", "EUR 6,447"],
        ["7552283740", "TRANSFER ASM", "Aug 2025", "EUR 4,439"],
        ["7552469080", "COMPRESSOR ASM; A/C", "Oct 2025", "EUR 2,956"],
    ],
    Inches(0.32), Inches(1.35), Inches(12.7), Inches(1.9),
    [Inches(4.5), Inches(3.5), Inches(2.4), Inches(2.3)],
    bold_last_row=False,
)
db.bullet_list(
    s,
    [
        "None of these five part numbers appear anywhere in 2023 or 2024 — confirmed against the full sales history, not just this year's window.",
        "The mix (instrument cluster, transfer case, A/C compressor) is consistent with a new vehicle platform, not a like-for-like replacement part.",
        "We haven't tagged these to a specific model in our own data, so this is circumstantial, not confirmed — worth you telling us what's actually driving it.",
    ],
    Inches(0.32), Inches(3.5), Inches(12.7), Inches(2.2), size=14,
)

# ---- Slide 8: GPS Capture — clean, no internal recon ------------------------
s = db.build_content(prs, "GPS Capture: 63.3%", eyebrow="GPS", page_no=8)
db.bullet_list(
    s,
    [
        "GPS (Genuine Parts Share) measures your actual parts purchases against the full potential of your fleet.",
        "Portugal today: 63.3%.",
        "The fleet and target work later in this deck is what grows that potential correctly, segment by segment, as your parc grows.",
        "Real, sustained headroom above 63.3% — the PMS and SPA discussion today are both direct levers on it.",
    ],
    Inches(0.32), Inches(1.35), Inches(11.5), Inches(3.5), size=15,
)

# ---- Slide 5: PMS Coverage — filters, fresh data -----------------------------
db.build_two_col(
    prs,
    title="PMS filters: air strongest at 62.7%, urea the clear gap at 1.1%",
    chart_path=cp("pms_portugal_filters.png"),
    eyebrow="PMS Coverage",
    page_no=9,
    takeaways=[
        "Air filter 62.7% and oil filter 52.1% are the strongest categories.",
        "Urea (AdBlue) filter at 1.1% is the standout gap — EUR 62,414 addressable.",
        "Fuel filter 44.9%, blower filter 24.2% — mid-pack, real headroom on both.",
        "Filter-only addressable gap to 100% capture: ~EUR 176,000 (gross, theoretical ceiling).",
    ],
)

# ---- Slide 6: Fleet trend -----------------------------------------------------
db.build_two_col(
    prs,
    title="Fleet has grown steadily since 2019 — +9.3% into 2026",
    chart_path=cp("uio_trend.png"),
    eyebrow="Fleet & FY2027 Target",
    page_no=10,
    takeaway_heading="What this means for FY2027",
    takeaways=[
        "Built directly from your vehicle registration records (2005-2026), not a top-down estimate.",
        "Fleet growth into 2026: +9.3% — a moderate, sustainable rate after a stronger 2023-2024.",
        "FY2027 target basis: fleet size + 5% price increase + 1.8% additional growth.",
        "Fully traceable: registrations aged on the published 12-year survival curve, nothing else assumed.",
    ],
)

# ---- Slide 7: target build-up, as two separate chains -----------------------
s = db.build_content(prs, "How the FY2027 target is built", eyebrow="Fleet & FY2027 Target", page_no=11)

db.txt(s, "Market potential, FY2027 — units x rate, per segment (not one blended rate)",
       Inches(0.32), Inches(1.28), Inches(9.4), Inches(0.3), size=13, bold=True, color=RED)
styled_table(
    s,
    [
        ["Segment", "Units", "Rate/unit (+5%)", "Value"],
        ["Pickup", "4,968", "€230.54", "€1,145,325"],
        ["N35 (3.5t)", "1,624", "€310.80", "€504,796"],
        ["N75+ (5-7.5t)", "969", "€775.95", "€751,967"],
        ["F-series", "348", "€931.35", "€323,798"],
        ["= Market potential", "7,909", "", "€2,725,886"],
    ],
    Inches(0.32), Inches(1.62), Inches(9.4), Inches(2.35),
    [Inches(2.6), Inches(1.8), Inches(2.2), Inches(2.8)],
)

db.txt(s, "Your FY2027 target — last year's actual, plus a slice of that potential",
       Inches(0.32), Inches(4.20), Inches(9.4), Inches(0.3), size=13, bold=True, color=RED)
styled_table(
    s,
    [
        ["", "Value"],
        ["FY2026 actual (Sales-to-Dealer)", "€4,047,903"],
        ["+ Stretch (1.8% of market potential)", "+€75,486"],
        ["= FY2027 target (+1.9% vs FY2026)", "€4,123,389"],
    ],
    Inches(0.32), Inches(4.54), Inches(9.4), Inches(1.55),
    [Inches(5.5), Inches(3.9)],
)

db.bullet_list(
    s,
    ["These are two separate chains, not one list to add up: potential is units × price; "
     "your target is actual + a small slice of potential. The 1.8% stretch is 1.8% of €2.73M "
     "potential (€75K), not 1.8% of your €4.05M actual."],
    Inches(0.32), Inches(6.15), Inches(12.7), Inches(0.7), size=12,
)

# ---- Slide 8: the growth story, the price move, and the incentive -----------
s = db.build_content(prs, "A growing market, and what FY2027 reflects", eyebrow="FY2027 Target", page_no=12)
card(s, Inches(0.32), Inches(1.35), Inches(6.0), Inches(3.1), "1", "Your growth",
     ["Portugal's fleet is up +9.3% — real, organic growth, built from your own registrations.",
      "That's the market you've built. It's the foundation for everything else on this slide."])
card(s, Inches(6.5), Inches(1.35), Inches(6.5), Inches(3.1), "2", "The price move",
     ["ISZE is applying a 5% price adjustment for FY2027, consistent with every ISZE market this year.",
      "Applied per vehicle segment, not one blended rate."])

db.txt(s, "What it means for your target",
       Inches(0.32), Inches(4.65), Inches(9.4), Inches(0.3), size=13, bold=True, color=RED)
styled_table(
    s,
    [
        ["", "Value"],
        ["FY2027 target (Sales-to-Dealer)", "€4,123,389"],
        ["vs FY2026 actual (€4,047,903)", "+1.9%"],
    ],
    Inches(0.32), Inches(4.98), Inches(9.4), Inches(1.1),
    [Inches(5.5), Inches(3.9)],
)
db.bullet_list(
    s,
    ["As in previous cycles, we'd expect an incentive to sit alongside this adjustment — that approval "
     "is still pending on our side. We'll confirm as soon as we have it."],
    Inches(0.32), Inches(6.15), Inches(12.7), Inches(0.6), size=12.5,
)

# ---- Slide 9: SPA — the real process, four cards -----------------------------
s = db.build_content(prs, "SPA", eyebrow="SPA", page_no=13)
card(s, Inches(0.32), Inches(1.35), Inches(3.06), Inches(3.8), "1", "I-Motors proposal",
     ["I-Motors submits a proposed parts list."])
card(s, Inches(3.53), Inches(1.35), Inches(3.06), Inches(3.8), "2", "ISZE review",
     ["ISZE reviews the proposal against network data and fit."])
card(s, Inches(6.74), Inches(1.35), Inches(3.06), Inches(3.8), "3", "Counter-proposal",
     ["ISZE returns a counter-proposal where needed."])
card(s, Inches(9.95), Inches(1.35), Inches(3.06), Inches(3.8), "4", "Final approval",
     ["Signed off by ISZE management."])
db.txt(s, "Purpose: higher turnover for both sides.",
       Inches(0.32), Inches(5.35), Inches(9.4), Inches(0.4), size=14, bold=True, color=RED)

# ---- Slide 10: R&M — discussion questions, two cards -------------------------
s = db.build_content(prs, "R&M — let's align on the market", eyebrow="R&M", page_no=14)
card(s, Inches(0.32), Inches(1.30), Inches(6.0), Inches(4.9), "L", "LCV",
     [
         "How is the LCV market moving for you right now?",
         "How much fleet business do you carry — is it a large share?",
         "What are the biggest hurdles you're facing?",
         "Where are your real strengths in this segment?",
     ])
card(s, Inches(6.5), Inches(1.30), Inches(6.5), Inches(4.9), "C", "CV / P700",
     [
         "Is P700 R&M live yet?",
         "What do you expect from it, and can you share a forecast?",
         "How is the collaboration with the provider going?",
         "Does R&M business often come bundled with tenders — roughly what share?",
     ])

# ---- Slide 11: data request, card layout --------------------------------------
s = db.build_content(prs, "Sales-to-Dealer Data — From 01/01/2025", eyebrow="Ask", page_no=15)
card(s, Inches(0.32), Inches(1.35), Inches(3.95), Inches(3.6), "1", "Faster replenishment",
     ["Real demand data lets us restock faster when your sales pick up — fewer stockouts on fast movers."])
card(s, Inches(4.47), Inches(1.35), Inches(3.95), Inches(3.6), "2", "Sharper insight",
     ["Part-by-part visibility into where you're underperforming — feeds directly into the SPA."])
card(s, Inches(8.62), Inches(1.35), Inches(3.95), Inches(3.6), "3", "Shared benefit",
     ["Better availability for you, a sharper target for us — same data, both sides gain."])

# ---- Slide 12: next steps -----------------------------------------------------
s = db.build_content(prs, "Next steps", eyebrow="Summary", page_no=16)
db.bullet_list(
    s,
    [
        "Confirm FY2027 target: €4,123,389 Sales-to-Dealer (+1.9% vs FY2026 actual).",
        "Confirm the incentive alongside the price adjustment once approved on our side.",
        "Agree Sales-to-Dealer data-sharing arrangement, effective 01/01/2025.",
        "SPA: I-Motors' proposal, ISZE review and counter-proposal cycle to follow.",
        "R&M: align on LCV market view and P700 status/forecast.",
        "Genuine parts share and parts sales target — detail to follow per the standing agenda.",
    ],
    Inches(0.32), Inches(1.35), Inches(11.5), Inches(3.2), size=15,
)

db.build_closing(prs)

out_path = os.path.join(
    os.path.expanduser("~"),
    "Downloads",
    "ISZE_Portugal_GPS_Target_FY2027_Jul2026.pptx",
)
prs.save(out_path)
print("Saved:", out_path)
