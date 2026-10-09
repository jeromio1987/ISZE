# -*- coding: utf-8 -*-
"""ISZE_Kickback_Japan_Pack_20261007.pptx - visual rebuild, same filename.

The words are the previous version's words.  The visual layer is new: native
shapes and data-driven graphics in place of text on panels.

House style read out of ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx
(read only - that file is not touched):
    background 262626 | panel 303030 / 2C2C2C | red E30613 | ink F2F2F2
    muted BDBDBD | Aptos

Every euro figure traces to the source named on its own slide.  No quantity is
charted on any axis.  The Kaizen ring is drawn by _ring.py, whose construction was
proved by rendering and measuring the pixels (see the module docstring).
"""
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ring import add_ring  # noqa: E402

OUT_DIR = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
OUT = os.path.join(OUT_DIR, "ISZE_Kickback_Japan_Pack_20261007.pptx")
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_assets_japan_dyn")

BG = RGBColor(0x26, 0x26, 0x26)
PANEL = RGBColor(0x30, 0x30, 0x30)
PANEL_ALT = RGBColor(0x2C, 0x2C, 0x2C)
RED = RGBColor(0xE3, 0x06, 0x13)
WHITE = RGBColor(0xF2, 0xF2, 0xF2)
MUTED = RGBColor(0xBD, 0xBD, 0xBD)
GREEN = RGBColor(0x31, 0xA3, 0x54)
AMBER = RGBColor(0xF5, 0xA0, 0x00)
DIVIDER = RGBColor(0x4B, 0x4B, 0x4B)
FONT = "Aptos"

SW, SH = 13.3333, 7.5
L = 0.42
W = 12.49

prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
blank = prs.slide_layouts[6]


# ------------------------------------------------------------------ helpers
def new_slide():
    s = prs.slides.add_slide(blank)
    f = s.background.fill
    f.solid()
    f.fore_color.rgb = BG
    return s


def txt(s, x, y, w, h, runs, size=11, color=WHITE, bold=False,
        align=PP_ALIGN.LEFT, space_after=0, line_spacing=1.15, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(runs, str):
        runs = [runs]
    norm = [(r, size, color, bold) if not isinstance(r, tuple) else r for r in runs]
    for i, (text, sz, col, bd) in enumerate(norm):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = text
        run.font.size = Pt(sz)
        run.font.name = FONT
        run.font.bold = bd
        run.font.color.rgb = col
    return tb


def rect(s, x, y, w, h, fill=PANEL, line=None, rounded=False, radius=0.08):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    sh = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if rounded:
        try:
            sh.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(0.75)
    sh.text_frame.text = ""
    return sh


def vline(s, x, y, h, fill=RED, w=0.035):
    return rect(s, x, y, w, h, fill)


def pic(s, name, x, y, w=None, h=None):
    path = os.path.join(ASSETS, name)
    kw = {}
    if w is not None:
        kw["width"] = Inches(w)
    if h is not None:
        kw["height"] = Inches(h)
    return s.shapes.add_picture(path, Inches(x), Inches(y), **kw)


def header(s, label, page):
    txt(s, L, 0.25, 9.0, 0.22, "ISZE  \u00b7  VEHICLE PARTS & ACCESSORIES", 7.8, WHITE, True)
    txt(s, SW - L - 0.9, 0.25, 0.9, 0.22, page, 8.5, MUTED, True, PP_ALIGN.RIGHT)
    txt(s, L, 0.55, 12.49, 0.23, label, 9, RED, True)


def headline(s, text, size=19, y=0.86, h=0.62):
    txt(s, L, y, W, h, text, size, WHITE, True)
    rect(s, L, 1.60, W, 0.012, DIVIDER)


def source(s, text, y=7.05):
    txt(s, L, y, W, 0.32, text, 7.2, MUTED, line_spacing=1.12)


def closing(s, text, y=6.34, h=0.44, size=11.5, x=None, w=None):
    x = L if x is None else x
    w = W if w is None else w
    rect(s, x, y, w, h, PANEL)
    rect(s, x, y, 0.045, h, RED)
    txt(s, x + 0.18, y + 0.02, w - 0.36, h - 0.04, text, size, WHITE, True,
        anchor=MSO_ANCHOR.MIDDLE)


def statement(s, x, y, w, h, text, size=15, color=WHITE):
    rect(s, x, y, w, h, PANEL)
    rect(s, x, y, 0.055, h, RED)
    txt(s, x + 0.24, y + 0.08, w - 0.44, h - 0.16, text, size, color, True,
        anchor=MSO_ANCHOR.MIDDLE)


def kpi(s, x, y, w, value, label, color=WHITE, h=1.02, bar=None, vsize=20):
    rect(s, x, y, w, h, PANEL)
    rect(s, x, y, 0.045, h, color)
    txt(s, x + 0.17, y + 0.09, w - 0.30, 0.40, value, vsize, WHITE, True)
    txt(s, x + 0.17, y + 0.53, w - 0.28, h - 0.60, label, 8.8, MUTED, line_spacing=1.12)
    if bar is not None:
        frac = max(0.02, min(1.0, bar))
        by = y + h - 0.10
        rect(s, x + 0.17, by, w - 0.34, 0.045, RGBColor(0x45, 0x45, 0x45))
        rect(s, x + 0.17, by, (w - 0.34) * frac, 0.045, color)


def kpi_row(s, y, items, h=1.02, gap=0.17, x=None, width=None):
    n = len(items)
    x = L if x is None else x
    width = W if width is None else width
    w = (width - gap * (n - 1)) / n
    for i, it in enumerate(items):
        value, label, color = it[0], it[1], it[2]
        bar = it[3] if len(it) > 3 else None
        vsize = it[4] if len(it) > 4 else 20
        kpi(s, x + i * (w + gap), y, w, value, label, color, h, bar, vsize)
        # the label wraps inside its own box; give the row the height it needs
    return y + h


def bullets(s, x, y, w, items, gap=0.09, size=9.8, head_size=10.6, accent=RED):
    """items: list of (head, body).  Heights follow the wrapped text estimate."""
    for head, body in items:
        hh = est_h(head, w - 0.20, head_size)
        bh = est_h(body, w - 0.20, size) if body else 0.0
        vline(s, x, y, hh + bh + 0.03, accent)
        txt(s, x + 0.17, y, w - 0.20, hh + 0.04, head, head_size, WHITE, True)
        if body:
            txt(s, x + 0.17, y + hh + 0.04, w - 0.20, bh + 0.05, body, size, MUTED)
        y += hh + bh + 0.03 + gap
    return y


def est_lines(text, width_in, size_pt):
    cpl = max(1, int(width_in * 72.0 / (0.495 * size_pt)))
    return max(1, -(-len(text) // cpl))


def est_h(text, width_in, size_pt, line_spacing=1.16):
    return est_lines(text, width_in, size_pt) * (size_pt * line_spacing) / 72.0


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


# ============================================================ 1  COVER
s = new_slide()
rect(s, 0, 0, 0.09, SH, RED)
rect(s, 0.09, 0, 0.025, SH, RGBColor(0x7A, 0x0A, 0x12))
txt(s, 0.85, 0.72, 11.8, 0.30, "ISZE  \u00b7  VEHICLE PARTS & ACCESSORIES", 10, MUTED, True)
txt(s, 0.85, 1.30, 11.7, 0.75, "Retaining the kickback", 36, WHITE, True)
txt(s, 0.85, 2.16, 11.7, 0.55,
    "An incentive for independent distributors, tested against the data we now receive", 19, WHITE)
rect(s, 0.85, 2.92, 2.05, 0.035, RED)
txt(s, 0.85, 3.20, 7.20, 0.50,
    "The FY2027 programme plan is EUR 31.82M, up EUR 2.63M or 9.0% from EUR 29.19M in FY2026.",
    14.5, MUTED)
txt(s, 0.85, 3.74, 7.20, 1.02,
    ["Distributors are independent businesses we cannot instruct, and the data shows no year-end "
     "jump at scale: most end-of-year buying is explained by the 13 March 2026 price change and "
     "ordinary seasonal build.",
     "The incentive is how we make the growth worth their while."],
    size=14, color=WHITE, space_after=4, line_spacing=1.18)
txt(s, 0.85, 5.96, 11.5, 0.32,
    "Japan / IML management  \u00b7  7 October 2026  \u00b7  all figures in EUR", 9.5, MUTED)

# right stat block: the incentive, on its own
rect(s, 8.55, 3.18, 3.92, 2.42, PANEL)
rect(s, 8.55, 3.18, 0.05, 2.42, AMBER)
txt(s, 8.80, 3.36, 3.45, 0.24, "THE INCENTIVE", 8.6, AMBER, True)
txt(s, 8.80, 3.66, 3.45, 0.62, "EUR 393,000", 30, WHITE, True)
txt(s, 8.80, 4.34, 3.45, 0.24, "across eleven customers", 10.4, MUTED)
rect(s, 8.80, 4.66, 3.45, 0.012, DIVIDER)
txt(s, 8.80, 4.82, 3.45, 0.30, "1.2\u20131.4%", 16, WHITE, True)
txt(s, 8.80, 5.16, 3.45, 0.32, "of each customer's annual plan", 9.6, MUTED)

txt(s, 0.85, 7.06, 11.5, 0.22,
    "Source: programme plan and incentive table; budget_per_DB_reviewed_24042026.xlsx, "
    "'Incentive FY27'; 01_data/90_INBOX/EURO_SALES_TO_DEALER_EVIDENCE_20261007.md.",
    7.2, MUTED)
notes(s, "Purpose of the deck: ask Japan / IML management to retain the incentive, keep the rate and "
         "conditions, and add a 10% tolerance at the 6-month and 9-month checkpoints. The new data "
         "shows that a rule aimed at year-end jumping is guarding against something we cannot find at "
         "scale. All figures are EUR and traceable to the source line on each slide.")

# ================================================ 2  THE POSITION IN ONE SLIDE
s = new_slide()
header(s, "THE POSITION IN ONE SLIDE", "02")
headline(s, "What we are asking, and how we make it worth their while")
y = kpi_row(s, 1.74, [
    ("+9.0%", "Programme plan, FY2026 EUR 29.19M to FY2027 EUR 31.82M", AMBER, 0.46),
    ("6\u201312%", "A year on the Kosha path, FY2024 EUR 29.6M to FY2031 EUR 52.1M", GREEN, 0.30),
    ("EUR 393K", "Incentive across eleven customers, 1.2\u20131.4% of each plan", RED, 1.0),
    ("7 of 9", "Distributors at or above plan, FY2026", GREEN, 0.78),
], h=1.06)
chart_y = 2.98
statement(s, L, chart_y, 7.30, 1.66,
          "What we are asking independent distributors to do can only be achieved with them, not "
          "through them: they are the ones who decide how much of their shelf and their working "
          "capital Isuzu parts get.", size=14.0)
bullets(s, L, chart_y + 1.80, 7.30, [
    ("The ask", "EUR 29.19M to EUR 31.82M in FY2027, then roughly 6\u201312% a year to FY2031."),
    ("The channel", "Independent distributors, serving independent and multi-branded dealers."),
    ("The incentive", "EUR 393,000 across eleven customers, 1.2\u20131.4% of each customer's plan."),
    ("The check", "KPI reporting and sales-to-dealer reporting show whether growth is delivered."),
], size=9.4, head_size=10.2, gap=0.05)
pic(s, "s2_plan_bar.png", L + 7.62, chart_y, w=4.87)
txt(s, L + 7.62, chart_y + 2.26, 4.87, 0.32,
    "EUR m, FY2026 to FY2027.  Source: budget_per_DB_reviewed_24042026.xlsx, 'Incentive FY27'.",
    7.0, MUTED, line_spacing=1.10)
closing(s, "FY2026: nine distributors, EUR 21.58M plan to EUR 23.40M billed, +8.4%.",
        y=6.44, h=0.44, size=12)
source(s, "Sources: budget_per_DB_reviewed_24042026.xlsx, 'Incentive FY27'; ISZE Vehicle Parts FY2026 "
          "Year-End Review, 'Kosha Gap & FY2027'.", y=7.00)
notes(s, "This slide is the whole argument in miniature: the ask, the channel, the incentive and the "
         "check. Everything after it is evidence for one of these four lines.")

# ============================================ 3  WHY AN INCENTIVE
s = new_slide()
header(s, "THE PREMISE", "03")
headline(s, "Why an incentive, not an instruction")
rect(s, L, 1.78, W, 1.14, PANEL)
rect(s, L, 1.78, 0.055, 1.14, RED)
txt(s, L + 0.30, 1.82, W - 0.60, 1.06,
    "We cannot force a distributor to grow our brand. We can only make it worth their while.",
    25, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
pic(s, "s3_chain.png", L, 3.10, w=W)
closing(s, "In a market where the distributor can choose, the incentive is what makes Isuzu the brand "
           "they choose to grow.", y=5.66, h=0.62, size=16)
rect(s, L, 6.42, W, 0.44, PANEL)
rect(s, L, 6.42, 0.045, 0.44, AMBER)
txt(s, L + 0.18, 6.44, W - 0.36, 0.40,
    "We do not own the channel, we do not set their stock, and we cannot instruct a shelf decision.",
    10.6, MUTED, anchor=MSO_ANCHOR.MIDDLE)
source(s, "Source: internal programme view. This premise is the reason the mechanism is an incentive "
          "rather than a direction.", y=6.96)
notes(s, "The most emphatic slide. If management takes one thing from the pack, it is this: the channel "
         "is not ours to instruct, so the incentive is the only lever that scales. The three panels are "
         "the three decision points the money has to pass through.")

# ============================================ 4  WHO DELIVERS THE DATA
s = new_slide()
header(s, "THE REPORTING CONDITION", "04")
headline(s, "Who is already reporting, and where the gaps are")

# --- the three measures, named once, because they fail independently
rect(s, L, 1.70, W, 0.50, PANEL)
rect(s, L, 1.70, 0.055, 0.50, RED)
txt(s, L + 0.24, 1.73, 3.40, 0.44,
    "The panel carries three separate measures:",
    9.8, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
rect(s, 4.16, 1.79, 2.02, 0.32, PANEL_ALT)
txt(s, 4.16, 1.80, 2.02, 0.30, "Days of parts in stock", 9.2, WHITE, True,
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
rect(s, 6.34, 1.79, 1.62, 0.32, PANEL_ALT)
txt(s, 6.34, 1.80, 1.62, 0.30, "First fill rate", 9.2, WHITE, True,
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
rect(s, 8.12, 1.79, 3.06, 0.32, PANEL_ALT)
txt(s, 8.12, 1.80, 3.06, 0.30, "Parts sales, DB to dealer, in EUR", 9.2, WHITE, True,
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
txt(s, 11.20, 1.73, 1.71, 0.44, "a market can report\none and not the others",
    7.6, MUTED, line_spacing=1.16, anchor=MSO_ANCHOR.MIDDLE)

statement(s, L, 2.32, W, 0.52,
          "Most of the network is reporting now. The gaps are concentrated in six named markets, "
          "not scattered across the book.", size=13.5)

CY, CH = 2.94, 2.44
LX, LW = L, 7.10
RX, RW = 7.72, 5.19

# --- left: current
rect(s, LX, CY, LW, CH, PANEL)
rect(s, LX, CY, 0.05, CH, GREEN)
txt(s, LX + 0.22, CY + 0.11, LW - 0.44, 0.24, "CURRENT", 11.5, GREEN, True)
txt(s, LX + 0.22, CY + 0.39, LW - 0.44, 0.20, "All three measures.", 9.6, WHITE, True)
txt(s, LX + 0.22, CY + 0.62, LW - 0.44, 0.66,
    ["IUK  \u00b7  ITUK  \u00b7  Portugal  \u00b7  Romania  \u00b7  Sweden  \u00b7  Hungary",
     "Malta  \u00b7  Iceland  \u00b7  Norway  \u00b7  UTI"],
    10.4, WHITE, line_spacing=1.26)
txt(s, LX + 0.22, CY + 1.36, LW - 0.44, 0.20,
    "UTI reports to May 2026; the rest to June or July 2026.", 8.6, MUTED)
rect(s, LX + 0.22, CY + 1.62, LW - 0.44, 0.010, DIVIDER)
txt(s, LX + 0.22, CY + 1.72, LW - 0.44, 0.22, "Current, but incomplete", 9.8, AMBER, True)
txt(s, LX + 0.22, CY + 1.98, LW - 0.44, 0.20,
    "Ireland \u2014 stock and onward sales current; no fill rate.", 9.2, MUTED)
txt(s, LX + 0.22, CY + 2.19, LW - 0.44, 0.20,
    "Denmark \u2014 onward sales current; no stock and no fill rate.", 9.2, MUTED)

# --- right: not current
rect(s, RX, CY, RW, CH, PANEL)
rect(s, RX, CY, 0.05, CH, AMBER)
txt(s, RX + 0.22, CY + 0.12, RW - 0.44, 0.24, "NOT CURRENT", 11.5, AMBER, True)
txt(s, RX + 0.22, CY + 0.40, RW - 0.44, 0.20, "The month the measure last arrived.", 8.6, MUTED)
rows = [
    ("Germany (ISD) \u2014 February 2025", 0.66),
    ("2 October 2026 submission covers February to July 2026; not yet loaded.", 0.90),
    ("UMI \u2014 February 2025, no onward sales in any month", 1.14),
    ("Finland \u2014 September 2025", 1.41),
    ("Poland \u2014 January 2026, no stock measure", 1.68),
    ("Greece \u2014 May 2025, onward sales to November 2024", 1.95),
    ("Cyprus \u2014 nothing in any month", 2.22),
]
for text, dy in rows:
    small = dy in (0.90,)
    txt(s, RX + 0.22, CY + dy, RW - 0.44, 0.20, text, 7.8 if small else 8.9,
        MUTED if small else WHITE, not small)

# --- Benelux: no clean answer, told as such
rect(s, L, 5.48, W, 0.62, PANEL)
rect(s, L, 5.48, 0.05, 0.62, AMBER)
txt(s, L + 0.24, 5.52, W - 0.48, 0.54,
    "Benelux has no single answer, and we are not presenting one. It reports under three labels with "
    "different gaps: IBX (BE LUX) gives onward sales only; IBX (BENELUX) gives stock and fill only; "
    "IBX (NL) stopped in April 2025. Its position cannot be read from one row, and this split is the "
    "likely cause of the unresolved December 2024 question.", 8.6, WHITE, line_spacing=1.16,
    anchor=MSO_ANCHOR.MIDDLE)

closing(s, "A market that does not report is invisible to us, so this pack makes no claim about those "
           "markets. Ukraine, Armenia and Kazakhstan do not appear in the panel at all.",
        y=6.20, h=0.46, size=11.0)
source(s, "Source: 01_data/11_planning/KPI Master File august 2026.xlsx, sheet 'Parts Handling', blocks "
          "'Days of Parts in Stock' (header row 3), 'First Fill Rate' (row 30) and 'Parts Sales DB to DLR "
          "in EUR' (row 84). A month counts only where the block carries a value; 'N/D' (no report sent), "
          "'N/A' (not tracked) and the placeholders 'IBX' and 'Internal only' do not. AIOS and MIDI report "
          "all three measures but sit outside the ISZE distributor book.", y=6.76)
notes(s, "This slide is the proof behind the previous one: the incentive buys reporting, and here is who "
         "is actually delivering. Say the three measures out loud, because they fail independently. "
         "Say the strength first - most of the network is current. Then the concentration: six named "
         "markets. Then the point of the slide: a market that does not report is invisible to us. "
         "On Benelux, do not be drawn into one row: the same distributor is split across three labels "
         "and that is the honest answer. Germany is not current even though a submission arrived on "
         "2 October 2026, because it has not been loaded yet.")

# ============================================ 5  PORTUGAL
s = new_slide()
header(s, "WHAT THE DATA LETS US SEE", "05")
headline(s, "Portugal: flat billing, rising dealer sales")
y = kpi_row(s, 1.72, [
    ("EUR 109,377", "Billed to Imotors, August 2026", WHITE),
    ("EUR 130,310", "Its sales on to dealers, same month", GREEN),
    ("+0.8%", "Billing, April\u2013August vs same months 2025", WHITE, 0.02),
    ("+22.0%", "Sales to dealer, same comparison", GREEN, 0.55),
], h=1.02)
chart_y = 2.96
pic(s, "s4_divergence.png", L, 2.96, w=8.30)
txt(s, L, 6.34, 8.30, 0.16,
    "EUR a month, January 2025 to August 2026. The two crossing lines are the argument.",
    7.0, MUTED, line_spacing=1.10)

px, pw = 8.94, 3.97
statement(s, px, 2.96, pw, 1.20,
          "Imotors sells more on to its dealers than it buys from us, and has in four of the last "
          "five months.", size=13.0)
bullets(s, px, 4.30, pw, [
    ("The two series diverge",
     "April\u2013August billing EUR 695,293 to EUR 701,076 (+0.8%), while sales to dealer rose to "
     "EUR 743,244 from EUR 609,263 (+22.0%) on our valuation."),
    ("What that means",
     "Billing sat at 94.3% of dealer offtake in FY2027 to August, against 112.1% in FY2026."),
    ("Decision it enabled",
     "Do not read a billing fall as a demand fall."),
], size=9.2, head_size=10.0, gap=0.07)
closing(s, "A distributor that sells on more than it buys is drawing down stock, not losing the market.",
        y=6.46, h=0.48, size=11.0)
source(s, "Sources: 01_data/90_INBOX/EURO_SALES_TO_DEALER_EVIDENCE_20261007.md; "
          "01_data/90_INBOX/_stock_insights_20261007/portugal_billing_vs_sales_to_dealer.csv. The dealer "
          "euro is the dealer's volume valued at ISZE prices, not the distributor's selling price.",
       y=7.05)
notes(s, "Portugal is the cleanest example of why the new reporting matters. Our own billing says the "
         "market is flat. The dealer-side data says demand rose 22%. Without sales-to-dealer reporting "
         "we would have misread this market. The chart is the whole point of the slide: the lines cross "
         "in April 2026 and stay apart in four of the last five months.")

# ============================================ 6  THE WRONG FAMILIES
s = new_slide()
header(s, "WHAT THE DATA LETS US SEE", "06")
headline(s, "The campaign overstock sat in the wrong families")
y = kpi_row(s, 1.72, [
    ("EUR 225,744", "Net parts build from the campaign, all families", RED),
    ("EUR 113,525", "Held in brakes, accident & body and electrical", RED),
    ("EUR 16,923", "Held in one brake part, 8983767550", RED),
], h=0.98)
statement(s, L, 2.82, W, 0.80,
          "The campaign stock sat in brakes, body and electrical, while the fastest-turning "
          "maintenance family kept turning and was drawn down against purchases.", size=14.0)
pic(s, "s5_families.png", L, 3.72, w=7.30)
pic(s, "s5_brake_ring.png", 7.90, 3.72, w=2.45)
txt(s, 7.90, 6.06, 2.45, 0.34,
    "one brake part\n8983767550", 7.0, MUTED, align=PP_ALIGN.CENTER, line_spacing=1.10)

nx, nw = 10.53, 2.38
rect(s, nx, 3.72, nw, 2.45, PANEL)
rect(s, nx, 3.72, 0.045, 2.45, AMBER)
txt(s, nx + 0.15, 3.84, nw - 0.30, 0.40,
    "The three families over-built", 10.0, WHITE, True)
txt(s, nx + 0.15, 4.24, nw - 0.30, 0.88,
    "Brakes EUR 47,986.75\nAccident & Body EUR 41,707.58\nElectrical EUR 23,830.92",
    8.2, MUTED, line_spacing=1.32)
txt(s, nx + 0.15, 5.12, nw - 0.30, 0.20, "EUR 113,525.24 together", 8.6, WHITE, True)
txt(s, nx + 0.15, 5.38, nw - 0.30, 0.44,
    "Maintenance Service built EUR 11,994.61 and sold more than it took in.", 8.2, GREEN,
    line_spacing=1.28)
txt(s, nx + 0.15, 5.92, nw - 0.30, 0.20,
    "Rebalance by family.", 8.2, WHITE, True)
closing(s, "The next campaign should be aimed by family, not by a single campaign event.",
        y=6.46, h=0.42, size=11.0)
source(s, "Sources: STOCK_CAMPAIGN_INSIGHTS_ALL_CUSTOMERS_20261007.md (net build EUR 225,744); "
          "_stock_insights_20261007/portugal_family_stock_build.csv (family values); "
          "portugal_pn_stock_build.csv (part 8983767550). The family rows total EUR 225,364 against the "
          "EUR 225,744 headline; that difference is not explained, so the headline is cited to the report "
          "and the family values to the file. Euro only on every axis.", y=6.94)
notes(s, "Everything on this slide is in euros: never a count. The euro split is the finding. The two "
         "totals do not reconcile, and that is said on the slide rather than hidden.")

# ============================================ 7  THE UNDER-ORDERING
s = new_slide()
header(s, "WHAT THE DATA LETS US SEE", "07")
headline(s, "The under-ordering: a demand signal we cannot see in our own billing")
statement(s, L, 1.76, W, 0.82,
          "EUR 678,464 of parts across five distributors where dealers bought the identified parts "
          "faster than the distributors reordered.", size=15.5)
pic(s, "s6_distributors.png", L, 2.72, w=7.60)
pic(s, "s6_donut.png", 8.28, 2.72, w=3.35)

txt(s, L, 5.48, 7.60, 0.56,
    "What this is: dealers bought these parts faster than the distributors reordered them. It is a "
    "demand signal that does not appear in our own billing, which only records what the distributor "
    "chose to buy. Use it for replenishment timing, handled separately from overstock.",
    9.4, WHITE, line_spacing=1.18)
closing(s, "A signal we could not see before, and a second use for the reporting condition.",
        y=6.20, h=0.42, size=11.5)
source(s, "Source: 01_data/00_derived/replenishment_exceptions_cy2025.csv, signal "
          "leakage_high_sellthrough. Five distributors, values as billed at ISZE prices; they sum exactly "
          "to the total. Euro only.", y=6.72)
notes(s, "The five distributor values sum exactly to the total. This is the mirror image of the Portugal "
         "slide: here the distributor is behind the dealers, there it is ahead of them.")

# ============================================ 8  THE YEAR-END FINDING
s = new_slide()
header(s, "THE CENTRAL FINDING", "08")
headline(s, "They do not jump at the end of the fiscal year")
statement(s, L, 1.74, W, 0.78,
          "Across the programme, most end-of-fiscal-year buying is explained by the 13 March 2026 "
          "price change and ordinary seasonal build \u2014 not by distributors rushing to cross a target.",
          size=14.5)
pic(s, "s7_ituk.png", L, 2.60, w=W)
colw = (W - 0.36) / 3.0
for i, (head, body) in enumerate([
    ("The ITUK worked example, after ten months",
     "5.6% behind plan, on a run rate of EUR 515,524 a month."),
    ("February 2026",
     "EUR 861,719 \u2014 EUR 346,195 above ITUK's own run rate. That is the plan being chased and caught."),
    ("13 March 2026",
     "The price list changed, +5.96% across the whole book. ITUK volume ran 2.32\u00d7 normal in the "
     "twelve days before and fell to 0.60\u00d7 after; its weakest week of the quarter was EUR 84,018."),
]):
    cx = L + i * (colw + 0.18)
    rect(s, cx, 5.50, colw, 1.10, PANEL)
    rect(s, cx, 5.50, 0.045, 1.10, RED if i == 0 else AMBER)
    txt(s, cx + 0.15, 5.58, colw - 0.30, 0.22, head, 9.2, WHITE, True)
    txt(s, cx + 0.15, 5.84, colw - 0.30, 0.68, body, 8.6, MUTED, line_spacing=1.18)
closing(s, "February is a plan recovery and March is a price pre-buy \u2014 two different things in the "
           "same two months.  A rule designed to catch year-end jumping is guarding against something "
           "the data does not show at scale.", y=6.70, h=0.42, size=9.6)
source(s, "Sources: ITUK billing by month and by day, sales_fact.parquet (sold_to 2575); PR00 base-price "
          "comparison (weighted +5.96%, 13 March 2026). No distributor notice for the price change is on "
          "file, so February's cause cannot be closed from the data alone.", y=7.18)
notes(s, "The statement at the bottom of the source line must be said out loud: there is no notice on "
         "file for the 13 March change, so we cannot close February from the data alone. Stated, not "
         "implied.")

# ============================================ 9  THE PROPOSAL
s = new_slide()
header(s, "THE PROPOSAL", "09")
headline(s, "Keep the rate and the conditions. Add a tolerance.")
rect(s, L, 1.72, W, 0.90, PANEL)
rect(s, L, 1.72, 0.055, 0.90, RED)
txt(s, L + 0.26, 1.76, 6.50, 0.82,
    "A distributor remains eligible for the full annual incentive provided it is not more than 10% "
    "behind its target at the 6-month checkpoint and again at the 9-month checkpoint.",
    15, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)

# ---- the ring: a real cycle, drawn as shapes.
#      Every clearance below is computed: the step boxes sit OUTSIDE the ring's
#      outer radius, and the centre label sits INSIDE the ring's inner radius, so
#      nothing can cover the ring or the arrows.
RCX, RCY, RR = 10.15, 4.05, 1.30
BAND = 0.085
R_OUT = RR + BAND / 2.0
BW_, BH_ = 1.30, 0.86
CLEAR = 0.08
V_GAP = 0.43            # half box height
RC = RCX + R_OUT + CLEAR + BW_ / 2.0        # right box centre
LC = RCX - R_OUT - CLEAR - BW_ / 2.0        # left box centre
TC = RCY - R_OUT - CLEAR - V_GAP            # top box centre
BC = RCY + R_OUT + CLEAR + V_GAP            # bottom box centre
print("  ring: centre (%.2f, %.2f) r=%.2f  outer=%.3f" % (RCX, RCY, RR, R_OUT))
print("  step centres: top(%.2f,%.2f) right(%.2f,%.2f) bottom(%.2f,%.2f) left(%.2f,%.2f)"
      % (RCX, TC, RC, RCY, RCX, BC, LC, RCY))
print("  right box right edge %.3f (limit %.3f)" % (RC + BW_ / 2.0, SW - L))

add_ring(s, RCX, RCY, radius=RR, band=BAND)
step_boxes = [
    (RCX, TC, "1  \u00b7  ISZE / JAPAN", "Confirm the monthly plan for each distributor", RED),
    (RC, RCY, "2  \u00b7  ISZE / JAPAN", "Check at month 6 against the 10% tolerance", RED),
    (RCX, BC, "3  \u00b7  ISZE / JAPAN", "Check at month 9 against the 10% tolerance", RED),
    (LC, RCY, "4  \u00b7  ISZE", "Close the five reporting gaps and load ISD Feb-Jul 2026", AMBER),
]
for cx, cy, title, body, accent in step_boxes:
    bx, by = cx - BW_ / 2.0, cy - BH_ / 2.0
    rect(s, bx, by, BW_, BH_, PANEL, line=DIVIDER, rounded=True, radius=0.12)
    rect(s, bx + 0.12, by + 0.075, 0.05, 0.028, accent)
    txt(s, bx + 0.10, by + 0.09, BW_ - 0.20, 0.20, title, 7.0, accent, True)
    txt(s, bx + 0.10, by + 0.29, BW_ - 0.20, BH_ - 0.37, body, 8.2, WHITE, line_spacing=1.14)
txt(s, RCX - 1.10, RCY - 0.42, 2.20, 0.84,
    [("A cycle, not a single approval", 10.4, WHITE, True),
     ("clockwise from the top", 7.6, MUTED, False)],
    align=PP_ALIGN.CENTER, line_spacing=1.20)

# left: the four reasons, numbered to match the four steps on the ring
bullets(s, L, 2.80, 6.60, [
    ("1  It funds the visibility",
     "The reporting is what shows us stock and onward sales, market by market."),
    ("2  It keeps the plan live all year, not only in March",
     "The recovery counts at two checkpoints, so a slow start is no longer a write-off."),
    ("3  It supports dealers in the market",
     "Growth is read on goods moving on, not only on what the distributor buys in."),
    ("4  It makes the steep annual increases achievable",
     "For a distributor who could carry another brand instead, the incentive is the reason not to."),
], size=10.2, head_size=11.2, gap=0.09)
rect(s, L, 5.44, 6.60, 0.48, PANEL)
rect(s, L, 5.44, 0.045, 0.48, AMBER)
txt(s, L + 0.18, 5.46, 6.24, 0.44,
    "No change to the rate. No change to the total. One improvement to how eligibility is tested.",
    10.2, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
closing(s, "In a market where the distributor can choose, the incentive is what makes Isuzu the brand "
           "they choose to grow.", y=6.42, h=0.46, size=12.0)
source(s, "Source: FY2027 proposal; budget_per_DB_reviewed_24042026.xlsx, 'Incentive FY27'. Four steps, "
          "clockwise from the top; the plan is reset from the agreed monthly targets after every "
          "checkpoint.", y=6.98)
notes(s, "Close on the premise from slide 3. The single ask is the tolerance sentence; everything else on "
         "the slide is why it costs nothing and buys more. The ring is the review cycle: confirm the "
         "monthly plan, check at month 6 against the 10% tolerance, check at month 9, close the reporting "
         "gaps, and back to the plan. The arrows run clockwise and the loop closes.")

prs.save(OUT)
print("saved", OUT, os.path.getsize(OUT), "bytes,", len(prs.slides._sldIdLst), "slides")
