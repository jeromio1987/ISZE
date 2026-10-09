# -*- coding: utf-8 -*-
"""ISZE_Kickback_Japan_Final_2026-10-09.pptx - one deck for the Japan presentation.

Built new; the two earlier decks in this folder are not touched.
Style: the dark house style of ISZE_Kickback_Japan_Pack_20261007.pptx.
Storyline: the ask -> the stake -> reason 1 (no year-end overstock, slides 4-8)
-> reason 2 (the data, slides 9-11) -> the proposal.

Figures: _analysis_yearend_20261009.json (analysis_yearend_network_20261009.py) and the
chart assets from assets_final_20261009.py. Text figures not in the JSON are quoted
from the source named in each slide's footnote and were re-checked on 2026-10-09.
"""
import json
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.dirname(HERE)
OUT = os.path.join(OUT_DIR, "ISZE_Kickback_Japan_Final_2026-10-09.pptx")
ASSETS = os.path.join(HERE, "_assets_final")
A = json.load(open(os.path.join(HERE, "_analysis_yearend_20261009.json"), encoding="utf-8"))

BG = RGBColor(0x26, 0x26, 0x26)
PANEL = RGBColor(0x30, 0x30, 0x30)
PANEL2 = RGBColor(0x3A, 0x3A, 0x3A)
RED = RGBColor(0xE3, 0x06, 0x13)
WHITE = RGBColor(0xF2, 0xF2, 0xF2)
MUTED = RGBColor(0xBD, 0xBD, 0xBD)
GREEN = RGBColor(0x31, 0xA3, 0x54)
AMBER = RGBColor(0xF5, 0xA0, 0x00)
GREYC = RGBColor(0x5A, 0x5A, 0x5A)
DIVIDER = RGBColor(0x4B, 0x4B, 0x4B)
FONT = "Aptos"
SW, SH = 13.3333, 7.5
L, W = 0.42, 12.49

prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
blank = prs.slide_layouts[6]
PAGE = [0]


def new_slide():
    s = prs.slides.add_slide(blank)
    f = s.background.fill
    f.solid()
    f.fore_color.rgb = BG
    PAGE[0] += 1
    return s


def txt(s, x, y, w, h, runs, size=11, color=WHITE, bold=False, align=PP_ALIGN.LEFT,
        space_after=0, line_spacing=1.12, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(runs, str):
        runs = [runs]
    for i, r in enumerate(runs):
        text, sz, col, bd = (r, size, color, bold) if not isinstance(r, tuple) else r
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


def rect(s, x, y, w, h, fill=PANEL, line=None, shape=MSO_SHAPE.RECTANGLE):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1.0)
    return sh


def pic(s, name, x, y, w=None, h=None):
    kw = {}
    if w is not None:
        kw["width"] = Inches(w)
    if h is not None:
        kw["height"] = Inches(h)
    return s.shapes.add_picture(os.path.join(ASSETS, name), Inches(x), Inches(y), **kw)


def header(s, label, accent=RED):
    txt(s, L, 0.25, 9.0, 0.22, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 7.8, WHITE, True)
    txt(s, SW - L - 0.9, 0.25, 0.9, 0.22, "%02d" % PAGE[0], 8.5, MUTED, True, PP_ALIGN.RIGHT)
    txt(s, L, 0.55, 12.0, 0.23, label, 9, accent, True)


def headline(s, text, size=24):
    txt(s, L, 0.84, W, 0.62, text, size, WHITE, True)
    rect(s, L, 1.55, W, 0.012, DIVIDER)


def source(s, text, y=7.08):
    txt(s, L, y, W, 0.3, text, 7.2, MUTED, line_spacing=1.1)


def bar(s, text, y=6.42, h=0.52, size=13, accent=RED, x=None, w=None):
    x = L if x is None else x
    w = W if w is None else w
    rect(s, x, y, w, h, PANEL)
    rect(s, x, y, 0.06, h, accent)
    txt(s, x + 0.24, y, w - 0.4, h, text, size, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)


def card(s, x, y, w, h, head, body, accent=RED, head_size=12, body_size=10.5, big=None,
         big_size=24, big_color=WHITE):
    rect(s, x, y, w, h, PANEL)
    rect(s, x, y, 0.06, h, accent)
    yy = y + 0.14
    if big:
        txt(s, x + 0.24, yy, w - 0.38, 0.5, big, big_size, big_color, True)
        yy += big_size / 72.0 * 1.35
    txt(s, x + 0.24, yy, w - 0.38, 0.4, head, head_size, WHITE, True)
    yy += head_size / 72.0 * 1.25 * (1 + len(head) // int((w - 0.38) * 72 / (0.5 * head_size)))
    if body:
        txt(s, x + 0.24, yy + 0.04, w - 0.38, h - (yy - y) - 0.1, body, body_size, MUTED,
            line_spacing=1.15)


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


P = A["pace"]
SH9 = A["febmar_share_9dist"]
STD = A["febmar_vs_own_run_billing_and_std"]
AFTER = A["apr_may_2026_pct_of_fy26_month_avg"]
DIST = ["IUK", "UMI", "UTI", "Germany", "Benelux", "Portugal", "Sweden", "Norway", "Ireland"]
n_after90 = sum(1 for n in DIST if AFTER[n] >= 90)
n_ahead = len(A["ahead_at_january"])
MS = A["march_split_per_working_day"]["ITUK"]

# =================================================================== 1  COVER
s = new_slide()
rect(s, 0, 0, 0.16, SH, RED)
txt(s, 0.75, 0.62, 9, 0.25, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 9, WHITE, True)
txt(s, 0.75, 1.02, 9, 0.25, "THE FY2027 DISTRIBUTOR INCENTIVE", 10, RED, True)
txt(s, 0.75, 1.75, 7.6, 1.2, "Keep the kickback", 50, WHITE, True)
txt(s, 0.75, 3.02, 7.1, 1.3,
    "It helps the network deliver a rising plan without year-end overstock, and it gives us the "
    "data to keep that growth healthy.", 19, MUTED, line_spacing=1.18)
rect(s, 8.75, 1.75, 3.95, 3.15, PANEL)
rect(s, 8.75, 1.75, 3.95, 0.06, RED)
txt(s, 9.05, 2.05, 3.5, 0.3, "THE INCENTIVE, FY2027", 9, MUTED, True)
txt(s, 9.05, 2.42, 3.5, 0.7, "EUR 393,000", 34, WHITE, True)
txt(s, 9.05, 3.25, 3.4, 1.4,
    ["across eleven customers", "about 1.2% of a EUR 31.82M plan",
     "paid only when the annual target is reached and the data is sent"],
    11.5, MUTED, space_after=5)
for i, (num, lab, acc) in enumerate([("1", "No year-end overstock", RED),
                                      ("2", "Data that makes the business smarter", GREEN)]):
    cx = 0.75 + i * 3.4
    rect(s, cx, 4.75, 0.42, 0.42, acc, shape=MSO_SHAPE.OVAL)
    txt(s, cx, 4.75, 0.42, 0.42, num, 14, WHITE, True, PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, cx + 0.55, 4.75, 4.3, 0.42, lab, 13, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
txt(s, 0.75, 6.55, 10, 0.3,
    "Isuzu Motors / IML management  ·  October 2026  ·  all figures in EUR", 10, MUTED)
notes(s, "Thank you for the time. I know the proposal on the table is to remove the kickback. I want "
         "to show you why we believe it should stay. There are two reasons, and both are in our data. "
         "First, distributors do not jump in at the end of the year and overstock. Second, the "
         "kickback is what gets us the monthly data, and that data makes our decisions better. The "
         "incentive is EUR 393,000 across eleven customers, about 1.2% of the plan, and it is only "
         "paid when the annual target is reached and the data is sent.")

# =================================================================== 2  THE CASE
s = new_slide()
header(s, "THE CASE ON ONE PAGE")
headline(s, "Two reasons to keep the kickback")
colw = (W - 0.3) / 2
for i, (num, title, acc, big, biglab, pts) in enumerate([
    ("1", "No year-end overstock", RED, f"{SH9['FY2026']:.1f}%",
     f"of FY2026 billing fell in February and March. It was {SH9['FY2024']:.1f}% and "
     f"{SH9['FY2025']:.1f}% in the two years before.",
     [f"{n_ahead} of 9 distributors were already ahead of plan by January.",
      "The two that finished short did not buy the gap.",
      "Where we see dealer sales, the extra buying went straight on to dealers."]),
    ("2", "Data that makes the business smarter", GREEN, "7 of 11",
     "customers send the monthly KPI sheet. Five also send every part sold to every dealer.",
     ["Portugal: our billing +0.8%, its dealer sales +22.0%.",
      "EUR 225,744 of campaign stock found in the wrong part families.",
      "EUR 678,464 of parts dealers bought faster than distributors reordered."]),
]):
    x = L + i * (colw + 0.3)
    rect(s, x, 1.82, colw, 4.3, PANEL)
    rect(s, x, 1.82, colw, 0.07, acc)
    rect(s, x + 0.3, 2.12, 0.5, 0.5, acc, shape=MSO_SHAPE.OVAL)
    txt(s, x + 0.3, 2.12, 0.5, 0.5, num, 18, WHITE, True, PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x + 0.95, 2.15, colw - 1.2, 0.5, title, 19, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x + 0.3, 2.9, 2.5, 0.8, big, 40, acc, True)
    txt(s, x + 2.75, 2.95, colw - 3.0, 0.9, biglab, 11.5, MUTED, line_spacing=1.15)
    rect(s, x + 0.3, 3.98, colw - 0.6, 0.012, DIVIDER)
    yy = 4.18
    for ptxt in pts:
        rect(s, x + 0.3, yy + 0.07, 0.11, 0.11, acc)
        txt(s, x + 0.55, yy, colw - 0.9, 0.5, ptxt, 12.5, WHITE)
        yy += 0.56
bar(s, "The decision: keep the rate and both conditions, the target and the data. "
       "Add a 10% tolerance at month 6 and month 9.", y=6.32, h=0.56, size=13.5)
source(s, "Sources: ISZE billing April 2023 to August 2026; FY2027 incentive table; distributor KPI "
          "sheets to July 2026; dealer-level sales files. Each figure is detailed on its own slide.")
notes(s, "This is the whole argument on one page. Reason one answers the concern about year-end "
         "buying. Reason two is what the kickback buys us besides growth: the data. The two are "
         "connected, because the only reason we can answer the year-end question with facts is that "
         "distributors send us their data. The decision we ask for is at the bottom: keep the rate, "
         "keep both conditions, and add one improvement, a 10% tolerance at month 6 and month 9.")

# =================================================================== 3  THE STAKE
s = new_slide()
header(s, "WHAT IS AT STAKE")
headline(s, "Isuzu's plan asks for 61% more parts sales in five years")
rect(s, L, 1.82, 7.25, 4.35, PANEL)
pic(s, "c3_kosha.png", L + 0.17, 1.92, w=6.9)
txt(s, L + 0.2, 5.62, 6.9, 0.45,
    "Kosha path: FY2024 and FY2025 actual, FY2026 projected, FY2027 to FY2031 target.",
    8.6, MUTED)
x2 = L + 7.5
for j, (big, lab, acc) in enumerate([
    ("+9.0%", "FY2027 programme plan: EUR 29.19M to EUR 31.82M across the eleven customers", RED),
    ("EUR 2.63M", "of extra parts sales asked from the distributors this year", RED),
    ("EUR 393K", "the incentive: about 15% of this year's increase, 1.2% of the plan", AMBER),
]):
    y = 1.82 + j * 1.0
    rect(s, x2, y, W - 7.5, 0.88, PANEL)
    rect(s, x2, y, 0.06, 0.88, acc)
    txt(s, x2 + 0.24, y + 0.1, 2.0, 0.6, big, 20, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x2 + 2.2, y + 0.1, W - 7.5 - 2.35, 0.7, lab, 10.5, MUTED, anchor=MSO_ANCHOR.MIDDLE)
rect(s, x2, 4.88, W - 7.5, 1.29, PANEL2)
txt(s, x2 + 0.24, 4.98, W - 7.5 - 0.45, 1.1,
    ["Our distributors are independent and carry other brands.",
     ("We cannot instruct them to grow Isuzu. We can only make it worth their while.", 12, WHITE,
      True)], 11, MUTED, space_after=4)
bar(s, "In a market where the distributor can choose, the kickback is what makes Isuzu the brand "
       "they choose to grow.", y=6.38, h=0.56, size=13)
source(s, "Sources: Kosha study, IML January 2026, as held in the ISZE FY2026 year-end review; FY2027 "
          "incentive table (eleven customers). The Kosha path and the programme plan cover different "
          "scopes and are not added together.")
notes(s, "The Kosha plan asks for parts sales to go from EUR 32.3 million this year to EUR 52.1 "
         "million in FY2031, plus 61%. This year alone the eleven programme customers are asked for "
         "9% more, EUR 2.63 million. The incentive is EUR 393,000, about 15% of that one-year "
         "increase. The important point: these distributors are independent. They carry other "
         "brands on the same shelf and with the same money. We cannot order them to grow Isuzu. The "
         "kickback is the tool that makes Isuzu the brand they choose to grow.")

# =================================================================== 4  REASON 1: SHARE
s = new_slide()
header(s, "REASON 1  ·  NO YEAR-END OVERSTOCK")
headline(s, "February and March are not getting bigger")
rect(s, L, 1.75, W, 0.5, PANEL2)
txt(s, L + 0.24, 1.75, W - 0.4, 0.5,
    [("The concern:  ", 12, AMBER, True)], 12, anchor=MSO_ANCHOR.MIDDLE)
txt(s, L + 1.5, 1.75, W - 1.7, 0.5,
    "distributors buy late in the year to reach the target, and leave stock behind.", 12, WHITE,
    anchor=MSO_ANCHOR.MIDDLE)
rect(s, L, 2.4, 5.4, 3.9, PANEL)
pic(s, "c4_febmar_network.png", L + 0.1, 2.42, h=3.86)
rect(s, L + 5.55, 2.4, W - 5.55, 3.9, PANEL)
pic(s, "c4_febmar_dots.png", L + 5.75, 2.42, h=3.86)
bar(s, "Six of nine sit inside or below their own range. Portugal's dealers bought its extra. "
       "Germany and Benelux are the two we cannot check.", y=6.42, h=0.52, size=12.5)
source(s, "Source: ISZE billing to the nine distributors in the programme, fiscal years April to March. "
          "ITUK, our own UK truck company, is on slide 7. * Benelux billing for April and May 2025 is "
          "about a quarter of a normal month, which matches a known gap in its order records.")
notes(s, "If distributors bought late to reach the target, February and March would take a bigger and "
         "bigger share of the year as the targets rise. They do not. For the nine distributors, "
         "February and March were 18.7% of the year in FY2024, 17.3% in FY2025 and 18.6% in FY2026. "
         "An even year would be 16.7%, so there is a small and stable seasonal lift, the same every "
         "year. On the right is each distributor against its own history. Six are inside or below "
         "their range. Of the three above, Portugal's dealers bought the extra, as the next slides "
         "show. Germany and Benelux are the two we cannot check: Germany stopped sending its data, "
         "and Benelux has a gap in its records. That is reason two in one sentence.")

# =================================================================== 5  REASON 1: PACE
s = new_slide()
header(s, "REASON 1  ·  NO YEAR-END OVERSTOCK")
headline(s, f"{n_ahead} of 9 were already ahead of plan by January")
rect(s, L, 1.82, 7.55, 4.35, PANEL)
pic(s, "c5_pace.png", L + 0.12, 1.9, w=7.3)
x2, w2 = L + 7.75, W - 7.75
um = P["UMI"]
card(s, x2, 1.82, w2, 1.38, "Nothing left to chase",
     f"UMI needed only EUR {um['needed_feb_mar']:,.0f} in February and March. Its February and "
     f"March were its quietest in three years: {A['febmar_share_per_db']['UMI']['FY2026']:.1f}% of "
     "its year.", accent=GREEN)
card(s, x2, 3.3, w2, 1.38, "Short, and did not buy the gap",
     f"Ireland finished EUR {-P['Ireland']['vs_plan_eur']:,.0f} short of plan and Benelux "
     f"EUR {-P['Benelux']['vs_plan_eur']:,.0f} short. Neither bought the difference.",
     accent=AMBER)
card(s, x2, 4.78, w2, 1.39, "The plan was delivered",
     "7 of 9 distributors finished FY2026 at or above plan, and together they closed 8.4% ahead.",
     accent=RED)
bar(s, "A distributor buying to cross the line would have bought the gap. The ones that were short "
       "did not.", y=6.38, h=0.56, size=13)
source(s, "Source: ISZE billing April 2025 to March 2026 against the FY2026 plan per customer in the "
          "FY2027 incentive table. Ten months of plan = 10/12 of the annual plan.")
notes(s, "This is the strongest test. To jump at year end, a distributor needs a reason: it must be "
         "behind. By the end of January six of the nine were already ahead of plan pace. They had "
         "no line left to cross. UMI needed only about EUR 36,000 in the last two months, and its "
         "February and March were in fact its quietest in three years. And the two that did finish "
         "short, Ireland by about EUR 15,000 and Benelux by about EUR 19,000, did not buy the "
         "difference. If the incentive were driving year-end stuffing, these are exactly the two "
         "who would have done it.")

# =================================================================== 6  REASON 1: DEALERS
s = new_slide()
header(s, "REASON 1  ·  NO YEAR-END OVERSTOCK")
headline(s, "The extra year-end buying went straight on to dealers")
rect(s, L, 1.82, 7.0, 4.35, PANEL)
pic(s, "c6_billed_vs_dealer.png", L + 0.35, 2.0, w=6.3)
x2, w2 = L + 7.2, W - 7.2
card(s, x2, 1.82, w2, 1.38, "distributors kept buying normally in April and May 2026",
     "At 90% or more of a normal month. Buying did not collapse after the year end.",
     accent=GREEN, big=f"{n_after90} of 9", big_size=24, head_size=11.5)
card(s, x2, 3.3, w2, 1.38, "Portugal's stock came back down",
     "75 days of stock in January, 96 in March, 79 by July. The March rise was sold through.",
     accent=GREEN, big="96 → 79 days", big_size=24, head_size=11.5)
card(s, x2, 4.78, w2, 1.39, "Seen only through the dealer files",
     "Four customers send a full year of dealer-level sales: IUK, Portugal, Ireland and ITUK. That "
     "is what makes this check possible.", accent=AMBER, head_size=11.5)
bar(s, "Where we can see dealer sales, nothing piled up. The goods were sold on.", y=6.38, h=0.56,
    size=13)
source(s, "Sources: ISZE billing; distributor dealer-level sales files, valued at ISZE prices (median "
          "billed price per part number); days of stock from the distributor KPI sheets. FY2026 "
          "monthly average for the April and May comparison.")
notes(s, "Here we look at the dealer side, which only the data condition shows us. In February and "
         "March IUK bought 17.8% more than its normal month, and its dealers bought 16.9% more. "
         "Portugal bought 29.8% more, and its dealers 25.2% more. Ireland was flat on both. The "
         "extra did not sit on a shelf: it went to the dealers. After the year end, seven of nine "
         "kept buying at a normal level in April and May. A year-end overstock would show a collapse "
         "in the following months, and we do not see one.")

# =================================================================== 7  REASON 1: ITUK
s = new_slide()
header(s, "REASON 1  ·  NO YEAR-END OVERSTOCK")
headline(s, "The one case that looked like a jump, explained")
rect(s, L, 1.75, W, 3.36, PANEL)
pic(s, "c7_ituk.png", L + 0.2, 1.8, w=W - 0.4)
it = P["ITUK"]
cw = (W - 0.3) / 3
for i, (head, body, acc) in enumerate([
    ("January: behind plan",
     f"ITUK, our own UK truck company, was at {it['pace_pct_of_10m_plan']:.1f}% of plan pace after ten "
     "months.", RED),
    ("February: the recovery",
     "EUR 861,719, which is EUR 346,195 above its own average. The plan being chased and caught.",
     AMBER),
    ("March: the price change",
     f"Before the 13 March price list, EUR {MS['per_wd_before']:,.0f} a working day. After it, "
     f"EUR {MS['per_wd_after']:,.0f}. Stock was back to 121 days by July.", AMBER),
]):
    x = L + i * (cw + 0.15)
    card(s, x, 5.22, cw, 1.1, head, body, accent=acc, head_size=11.5, body_size=10)
bar(s, "This is the case the 10% tolerance is designed for: a slow start is checked at month 6 and "
       "month 9, not left to the last two months.", y=6.45, h=0.52, size=12.2)
source(s, "Sources: ISZE billing to ITUK by month and by day; price list comparison, weighted +5.96% on "
          "13 March 2026; ITUK days of stock from its KPI sheet (125 in January, 140 in March, 121 in "
          "July 2026).")
notes(s, "ITUK is the one case that looked like a year-end jump, and it is our own company. It was "
         "behind plan after ten months. February was a genuine recovery. March was buying ahead of "
         "the price list that changed on 13 March: about EUR 57,000 a working day before the change "
         "and about EUR 33,000 after. Its dealers bought 29% more than normal in those two months, "
         "so part was sold on and part became stock, and that stock was back to 121 days by July. "
         "This is exactly why we propose the tolerance at month 6 and month 9: a slow start is "
         "caught early, so nobody has to recover the whole year in February and March.")

# =================================================================== 8  REASON 1: IBX
s = new_slide()
header(s, "REASON 1  ·  A GOOD CASE")
headline(s, "When stock rose, it was stock we asked for")
rect(s, L, 1.82, 7.65, 4.35, PANEL)
pic(s, "c8_ibx.png", L + 0.12, 2.02, w=7.4)
x2, w2 = L + 7.85, W - 7.85
card(s, x2, 1.82, w2, 1.38, "Below its band for most of the year",
     "IBX held too little stock to serve its dealers well: 32 days in January 2026.",
     accent=AMBER)
card(s, x2, 3.3, w2, 1.38, "Rebuilt into the agreed band",
     "63 days by July, inside the 60 to 75 days set for its supply route.", accent=GREEN)
card(s, x2, 4.78, w2, 1.39, "Visible because IBX reports",
     "This is IBX's own figure, sent to us every month under the kickback's data condition.",
     accent=GREEN)
bar(s, "Stock that rises into the agreed band is better service to dealers, not overstock.",
    y=6.38, h=0.56, size=13)
source(s, "Sources: IBX days of parts in stock from its monthly KPI sheet; target band from the ISZE "
          "distributor KPI targets FY2026-27, supply class A (road delivery up to 5 days, 60 to 75 "
          "days of stock).")
notes(s, "Not every stock increase is a problem. IBX in Benelux was below its target band for most of "
         "last year, at 32 days in January. It rebuilt stock to 63 days by July, inside the 60 to 75 "
         "day band we agreed for its supply route. That is better service for its dealers. And we "
         "only know this because IBX sends its stock figure every month.")

# =================================================================== 9  REASON 2: COVERAGE
s = new_slide()
header(s, "REASON 2  ·  THE DATA THE KICKBACK BUYS", GREEN)
headline(s, "Seven of eleven send their monthly figures. Closing the gaps is part of our ask")
cw = (W - 0.2) / 2
for i, (t, b) in enumerate([
    ("Monthly KPI sheet", "Days of stock, first fill rate and sales to dealers in euro."),
    ("Dealer-level sales file", "Every part sold to every dealer each month: date, part number "
                                "and quantity. No prices."),
]):
    x = L + i * (cw + 0.2)
    rect(s, x, 1.78, cw, 0.78, PANEL)
    rect(s, x, 1.78, 0.06, 0.78, GREEN)
    txt(s, x + 0.24, 1.86, cw - 0.4, 0.3, t, 12.5, WHITE, True)
    txt(s, x + 0.24, 2.17, cw - 0.4, 0.35, b, 10.5, MUTED)
GOOD, PART, NONE = GREEN, AMBER, GREYC
cust = [
    ("ITUK", ("to Jul 26", GOOD), ("yes", GOOD)),
    ("IUK", ("to Jul 26", GOOD), ("yes", GOOD)),
    ("Portugal", ("to Jul 26", GOOD), ("yes", GOOD)),
    ("Ireland", ("to Jul 26", GOOD), ("yes", GOOD)),
    ("UTI", ("to May 26", GOOD), ("part year", PART)),
    ("Sweden", ("to Jun 26", GOOD), ("no", NONE)),
    ("Norway", ("to Jun 26", GOOD), ("no", NONE)),
    ("Benelux", ("split", PART), ("no", NONE)),
    ("Germany", ("Feb 25 *", PART), ("no", NONE)),
    ("UMI", ("Feb 25", NONE), ("no", NONE)),
    ("Ukraine", ("none", NONE), ("no", NONE)),
]
gx0 = L + 1.75
gw = (W - 1.75) / len(cust)
gy = 2.82
for j, (name, k, d) in enumerate(cust):
    x = gx0 + j * gw
    txt(s, x, gy, gw - 0.06, 0.3, name, 10.5, WHITE, True, PP_ALIGN.CENTER)
    for r, (lab, col) in enumerate((k, d)):
        y = gy + 0.42 + r * 0.82
        rect(s, x + 0.03, y, gw - 0.1, 0.66, col)
        txt(s, x + 0.03, y, gw - 0.1, 0.66, lab, 9.5,
            WHITE if col != PART else RGBColor(0x22, 0x22, 0x22), True, PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
txt(s, L, gy + 0.42, 1.65, 0.66, "KPI sheet,\nlatest month", 10.5, MUTED, True, anchor=MSO_ANCHOR.MIDDLE)
txt(s, L, gy + 1.24, 1.65, 0.66, "Dealer-level\nsales file", 10.5, MUTED, True, anchor=MSO_ANCHOR.MIDDLE)
txt(s, gx0, gy + 2.0, W - 1.75, 0.6,
    "* Germany stopped in February 2025 and sent February to July 2026 on 2 October 2026; it is being "
    "loaded. Benelux reports under three separate lines, each with gaps. Ukraine sends no KPI sheet.",
    9, MUTED)
tw9 = (W - 0.3) / 3
for i, (big, lab, acc) in enumerate([
    ("7 of 11", "current on the monthly KPI sheet", GREEN),
    ("5 of 11", "send dealer-level sales files", GREEN),
    ("4 gaps", "on the KPI sheet: Benelux, Germany, UMI and Ukraine", AMBER),
]):
    x = L + i * (tw9 + 0.15)
    rect(s, x, 5.35, tw9, 0.78, PANEL)
    rect(s, x, 5.35, 0.06, 0.78, acc)
    txt(s, x + 0.24, 5.35, 1.6, 0.78, big, 22, WHITE, True, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x + 1.75, 5.35, tw9 - 1.9, 0.78, lab, 10.5, MUTED, anchor=MSO_ANCHOR.MIDDLE)
bar(s, "A market that does not report is a market we cannot see, and cannot defend in a "
       "discussion like this one.", y=6.32, h=0.56, size=13, accent=GREEN)
source(s, "Sources: distributor KPI master file, sheet Parts Handling, August 2026 edition (a month "
          "counts only when a figure was sent); dealer-level sales files held by ISZE. The eleven "
          "customers are those in the FY2027 incentive table.")
notes(s, "The kickback has two conditions: reach the target, and send the data. There are two kinds of "
         "data. The monthly KPI sheet gives stock, fill rate and sales to dealers in euro. The dealer "
         "file gives every part sold to every dealer, without prices. Seven of the eleven customers "
         "are current on the KPI sheet, and five send dealer files. Germany, UMI, Benelux and Ukraine "
         "are the gaps on the KPI sheet. Without the kickback, we lose the lever that closes these "
         "gaps, and every market we cannot see is a market where we cannot answer the question we "
         "discussed on the previous slides.")

# =================================================================== 10  REASON 2: PORTUGAL
s = new_slide()
header(s, "REASON 2  ·  WHAT THE DATA SHOWS", GREEN)
headline(s, "Portugal: our billing says flat, its dealers say +22%")
rect(s, L, 1.82, 8.4, 4.35, PANEL)
pic(s, "c10_portugal.png", L + 0.1, 1.92, w=8.2)
x2, w2 = L + 8.6, W - 8.6
card(s, x2, 1.82, w2, 1.38, "our billing to Imotors", "April to August 2026 against the same months "
     "of 2025.", accent=RED, big="+0.8%", big_size=26, head_size=11.5)
card(s, x2, 3.3, w2, 1.38, "Imotors' sales to its dealers", "Same months, same comparison.",
     accent=GREEN, big="+22.0%", big_size=26, head_size=11.5)
card(s, x2, 4.78, w2, 1.39, "The decision it changed",
     "Do not read a billing slowdown as a demand slowdown. Plan replenishment instead.",
     accent=GREEN, head_size=11.5)
bar(s, "Without the dealer data we would have read Portugal as a flat market. It is a growing one.",
    y=6.38, h=0.56, size=13, accent=GREEN)
source(s, "Sources: ISZE billing to Imotors; Imotors dealer-level sales file, valued at ISZE prices, "
          "so the two lines are on the same price basis. April to August: EUR 695,293 to EUR 701,076 "
          "billed; EUR 609,263 to EUR 743,244 sold to dealers.")
notes(s, "Portugal is the clearest example of what the data gives us. Our own billing to Imotors was "
         "flat this year, plus 0.8%. Its sales to its dealers were up 22%. Without the dealer file, "
         "we would have concluded the market was stalling. In fact demand is growing, and Imotors is "
         "drawing down stock. The right action is to plan its replenishment, not to cut its plan.")

# =================================================================== 11  REASON 2: FINDINGS
s = new_slide()
header(s, "REASON 2  ·  WHAT THE DATA SHOWS", GREEN)
headline(s, "Three findings our own billing could never show")
cw = (W - 0.3) / 3
for i, (tag, big, img, what, dec) in enumerate([
    ("PORTUGAL  ·  STOCK MIX", "EUR 225,744", "c11a_families.png",
     "net stock built after the campaign, mostly in brakes, body and electrical parts.",
     "Aim the next campaign by part family."),
    ("IUK  ·  CAMPAIGN TIMING", "EUR 764,436", "c11b_iuk.png",
     "of stock built after our own brake campaign: 51 to 97 days. Brake buying then fell 76%.",
     "Time campaigns on dealer demand."),
    ("FIVE MARKETS  ·  REPLENISHMENT", "EUR 678,464", "c11c_replenish.png",
     "of parts dealers bought faster than the distributors reordered them.",
     "Reorder earlier and avoid lost sales."),
]):
    x = L + i * (cw + 0.15)
    rect(s, x, 1.78, cw, 4.45, PANEL)
    rect(s, x, 1.78, cw, 0.06, GREEN)
    txt(s, x + 0.22, 1.96, cw - 0.4, 0.25, tag, 9, GREEN, True)
    txt(s, x + 0.22, 2.22, cw - 0.4, 0.5, big, 24, WHITE, True)
    txt(s, x + 0.22, 2.75, cw - 0.4, 0.7, what, 10.5, MUTED, line_spacing=1.15)
    pic(s, img, x + 0.3, 3.32, h=2.2)
    rect(s, x + 0.22, 5.62, cw - 0.44, 0.012, DIVIDER)
    txt(s, x + 0.22, 5.72, cw - 0.4, 0.4, [("Decision:  ", 11, GREEN, True)], 11)
    txt(s, x + 1.12, 5.72, cw - 1.3, 0.45, dec, 11, WHITE, True)
bar(s, "The data does not only protect against overstock. It finds growth.", y=6.38, h=0.56,
    size=13, accent=GREEN)
source(s, "Sources: Portugal net stock build January 2025 to August 2026 and part-family values, ISZE "
          "stock analysis of 7 October 2026; IUK days of stock December 2024 to December 2025 at its "
          "own daily billing rate; replenishment exceptions CY2025, the 100 most affected parts per "
          "market (ITUK, UTI, IUK, Ireland, Greece). Values at ISZE prices.")
notes(s, "Three examples of decisions the data changed. In Portugal the campaign stock sat in the "
         "wrong families: brakes, body and electrical, so the next campaign should be aimed by part "
         "family. At IUK our own brake campaign built EUR 764,000 of stock and buying then dropped "
         "76%, so we now size and time campaigns on dealer demand. And in five markets dealers "
         "bought parts faster than the distributor reordered them, EUR 678,000, which is a sales "
         "opportunity we could not see in our own billing. The data protects against overstock, and "
         "it also finds growth.")

# =================================================================== 12  PROPOSAL
s = new_slide()
header(s, "THE PROPOSAL")
headline(s, "Keep the kickback, and make it stronger")
asks = [
    ("1", "Keep the rate and the total", "EUR 393,000 across eleven customers, about 1.2% of plan."),
    ("2", "Keep both conditions", "Reach the annual target, and send the monthly data."),
    ("3", "Add a 10% tolerance", "Eligible if no more than 10% behind plan at month 6 and month 9."),
    ("4", "Close the data gaps", "KPI sheet from Germany, UMI, Benelux and Ukraine; dealer files from "
                                 "the six that do not send them yet."),
]
yy = 1.82
for num, t, b in asks:
    rect(s, L, yy, 6.2, 0.98, PANEL)
    rect(s, L + 0.2, yy + 0.24, 0.5, 0.5, RED, shape=MSO_SHAPE.OVAL)
    txt(s, L + 0.2, yy + 0.24, 0.5, 0.5, num, 16, WHITE, True, PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE)
    txt(s, L + 0.9, yy + 0.12, 5.2, 0.35, t, 14, WHITE, True)
    txt(s, L + 0.9, yy + 0.47, 5.2, 0.5, b, 10.5, MUTED)
    yy += 1.08
# FY2027 timeline
tx, tw = L + 6.5, W - 6.5
rect(s, tx, 1.82, tw, 4.22, PANEL)
txt(s, tx + 0.3, 1.98, tw - 0.6, 0.3, "HOW FY2027 WOULD RUN", 9.5, MUTED, True)
ly = 3.62
lx0, lx1 = tx + 0.55, tx + tw - 0.55
rect(s, lx0, ly, lx1 - lx0, 0.06, DIVIDER)
months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
step = (lx1 - lx0) / 11
for k, m in enumerate(months):
    cx = lx0 + k * step
    rect(s, cx - 0.06, ly - 0.03, 0.12, 0.12, GREEN, shape=MSO_SHAPE.OVAL)
    txt(s, cx - 0.3, ly + 0.2, 0.6, 0.25, m, 8.5, MUTED, align=PP_ALIGN.CENTER)
for k, (lab, body, col) in {
    0: ("Plan agreed", "monthly plan per distributor", WHITE),
    5: ("Month 6", "within 10% of plan?", AMBER),
    8: ("Month 9", "within 10% of plan?", AMBER),
    11: ("Year end", "target reached: paid", RED),
}.items():
    cx = lx0 + k * step
    rect(s, cx - 0.13, ly - 0.1, 0.26, 0.26, col, shape=MSO_SHAPE.OVAL)
    bx = min(max(cx - 0.75, tx + 0.15), tx + tw - 1.65)
    up = k in (0, 8)
    by = ly - 1.15 if up else ly + 0.55
    rect(s, bx, by, 1.5, 0.82, PANEL2)
    rect(s, bx, by, 1.5, 0.05, col)
    txt(s, bx + 0.1, by + 0.12, 1.3, 0.3, lab, 11, WHITE, True, PP_ALIGN.CENTER)
    txt(s, bx + 0.1, by + 0.42, 1.3, 0.4, body, 8.8, MUTED, align=PP_ALIGN.CENTER)
txt(s, tx + 0.3, 5.42, tw - 0.6, 0.5,
    [("Green dots: data sent every month. ", 9.5, GREEN, True),
     ("It is what makes each check possible.", 9.5, MUTED, False)], 9.5)
bar(s, "No change to the rate. No change to the total. A stronger rule, and a network we can see.",
    y=6.32, h=0.6, size=14)
source(s, "Month 6 = end of September 2026, month 9 = end of December 2026, in a fiscal year from April "
          "to March. The incentive is still paid only on the annual target and the data condition.")
notes(s, "Our proposal has four parts. Keep the rate and the total, EUR 393,000. Keep both "
         "conditions: the target and the data. Add one improvement: a distributor stays eligible if "
         "it is no more than 10% behind plan at month 6 and month 9, so a slow start is corrected "
         "early instead of in February and March. And close the data gaps, so that next year we can "
         "show this picture for every market, not only for most of them. In a market where the "
         "distributor can choose, the kickback is what makes Isuzu the brand they choose to grow. "
         "Thank you.")

prs.save(OUT)
print("saved", OUT, "slides", len(prs.slides))
