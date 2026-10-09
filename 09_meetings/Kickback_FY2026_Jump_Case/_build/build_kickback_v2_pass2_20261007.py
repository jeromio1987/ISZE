"""Pass 2 on the v2 kickback deck (2026-10-07): add the iMotors persuasion slide, add the
multi-brand European logic slide, put real data into the coloured cards, and fix the false
maintenance claim on the old slide 10.

Target file (same name, no re-versioning):
  09_meetings/Kickback_FY2026_Jump_Case/ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx

WHAT THIS DOES
  A. old slide 10: corrects 'Maintenance family reduced 20%.' to the file's actual finding
     (see maintenance_finding() below and the docstring of verify_sources_for_new_slides).
  B. inserts the iMotors persuasion slide immediately BEFORE old slide 10
     (the section 'VALUE OF THE REPORTING  |  WIDER REVIEW'), because the '20%' row it carries
     is the false one - so the persuading slide lands first and the corrected row sits after it.
  C. inserts the multi-brand European logic slide immediately BEFORE the closing
     'DECISION AND FOLLOW-UP' slide, so the argument is complete before the decision.
  D. re-runs the PowerPoint package repair (duplicate second master) so the file still opens.

HOUSE STYLE, read out of the file itself (not assumed)
  background 262626, panel 303030, divider 4B4B4B
  ink F2F2F2, muted BDBDBD, red E30613, amber F5A000, green 31A354
  Aptos everywhere, lnSpc 110%
  header 7.8pt bold ink at (0.42, 0.25); page no. 8.5pt bold muted right-aligned at (12.20, 0.25)
  section label 9.0pt bold red spc=65 at (0.42, 0.55); title 19.0pt bold ink at (0.42, 0.87)
  divider at y=1.53; source line 7.6pt muted at (0.42, 7.09)
  card = rect 303030 + 0.045in accent bar + value 21-23pt bold + label 8.5-10.2pt muted
"""
from __future__ import annotations

import shutil
import sys
from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
PPTX = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
ASSETS = HERE / "_build" / "_assets_leverage2"
BACKUP_DIR = HERE / "_build" / "_backup"
BACKUP = BACKUP_DIR / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pass1.pptx"
WORK = HERE / "_build" / "_tmp_pass2.pptx"

BG, PANEL, GRID, TRACK = "262626", "303030", "4B4B4B", "3B3B3B"
WHITE, MUTED = "F2F2F2", "BDBDBD"
RED, AMBER, GREEN = "E30613", "F5A000", "31A354"
FONT = "Aptos"
PG = 16  # placeholder slide number, patched at the end


def rgb(h):
    return RGBColor.from_string(h)


def solid(sh, h):
    sh.fill.solid()
    sh.fill.fore_color.rgb = rgb(h)


def no_line(sh):
    sh.line.fill.background()


def no_shadow(sh):
    try:
        sh.shadow.inherit = False
    except Exception:
        pass


def set_autofit(tf):
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    for tag in ("a:noAutofit", "a:spAutoFit"):
        e = bodyPr.find(qn(tag))
        if e is not None:
            bodyPr.remove(e)
    if bodyPr.find(qn("a:normAutofit")) is None:
        etree.SubElement(bodyPr, qn("a:normAutofit"))


def txt(slide, x, y, w, h, paras, size, color, bold=False, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP, spc=None, space_before=None, line_spacing=1.10):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    set_autofit(tf)
    for i, line in enumerate(paras if isinstance(paras, (list, tuple)) else [paras]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        if space_before is not None and i > 0:
            p.space_before = Pt(space_before)
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = FONT
        r.font.color.rgb = rgb(color)
        r.font._rPr.set("lang", "en-US")
        if spc is not None:
            r.font._rPr.set("spc", str(spc))
    return tb


def bare(slide, x, y, w, h):
    """An empty textbox, for building rich paragraphs run by run."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    set_autofit(tf)
    return tf


def para(tf, runs, size=10, align=PP_ALIGN.LEFT, space_before=0.0, line_spacing=1.10,
         first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.line_spacing = line_spacing
    p.space_before = Pt(space_before)
    for text, color, bold, sz in runs:
        r = p.add_run()
        r.text = text
        r.font.size = Pt(sz if sz else size)
        r.font.bold = bold
        r.font.name = FONT
        r.font.color.rgb = rgb(color)
        r.font._rPr.set("lang", "en-US")
    return p


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE, line_pt=1.0):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        solid(s, fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(line_pt)
    else:
        no_line(s)
    no_shadow(s)
    return s


def hline(slide, x, y, w, color=GRID, width=0.6):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y),
                                   Inches(x + w), Inches(y))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    return c


def pic(slide, path, x, y, w, h):
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))


def head(slide, section, title, page):
    txt(slide, 0.42, 0.25, 9.00, 0.22, "ISZE  \u00b7  VEHICLE PARTS & ACCESSORIES", 7.8, WHITE, True)
    txt(slide, 12.20, 0.25, 0.70, 0.22, page, 8.5, MUTED, True, align=PP_ALIGN.RIGHT)
    txt(slide, 0.42, 0.55, 12.49, 0.23, section.upper(), 9.0, RED, True, spc=65)
    txt(slide, 0.42, 0.87, 12.49, 0.57, title, 19.0, WHITE, True)
    hline(slide, 0.42, 1.53, 12.49)


def card(slide, x, y, w, h, accent):
    rect(slide, x, y, w, h, PANEL)
    rect(slide, x, y, 0.045, h, accent)


def index_bar(slide, x, y, w, value, vmax, accent, marker_at, marker_label, scale_label):
    """A bar that fills against a reference, with the reference drawn as a marker."""
    rect(slide, x, y, w, 0.10, TRACK)
    frac = max(0.0, min(1.0, value / vmax))
    rect(slide, x, y, max(0.03, w * frac), 0.10, accent)
    mx = x + w * (marker_at / vmax)
    rect(slide, mx - 0.008, y - 0.045, 0.016, 0.19, WHITE)
    txt(slide, mx + 0.06, y - 0.10, 2.2, 0.16, marker_label, 7.0, WHITE, True)
    txt(slide, x, y + 0.16, w, 0.16, scale_label, 7.0, MUTED)


# =============================================================== helpers for slides
def section_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(BG)
    return s


def find_slide(prs, needle, in_section=False):
    for idx, s in enumerate(list(prs.slides)):
        for sh in s.shapes:
            if not sh.has_text_frame:
                continue
            t = sh.text_frame.text
            if needle in t:
                if in_section:
                    # only the red section label counts
                    try:
                        if str(sh.text_frame.paragraphs[0].runs[0].font.color.rgb) != RED:
                            continue
                    except Exception:
                        continue
                return idx
    raise SystemExit("slide not found: %s" % needle)


# =============================================================== backup
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
if not BACKUP.exists():
    shutil.copy2(PPTX, BACKUP)
    print("backup written:", BACKUP)
else:
    print("backup already present:", BACKUP)

prs = Presentation(str(PPTX))
n_before = len(prs.slides._sldIdLst)
print("deck before:", n_before, "slides")
head_layout = None
for master in prs.slide_masters:
    for lay in master.slide_layouts:
        if lay.part.partname == "/ppt/slideLayouts/slideLayout1.xml":
            head_layout = lay
assert head_layout is not None

# =============================================================== A. fix old slide 10
idx10 = find_slide(prs, "VALUE OF THE REPORTING  |  WIDER REVIEW", in_section=True)
s10 = list(prs.slides)[idx10]
assert idx10 == 9, "expected the wider-review slide at position 10, found %d" % (idx10 + 1)
fixed = False
for sh in s10.shapes:
    if not sh.has_text_frame:
        continue
    for p in sh.text_frame.paragraphs:
        joined = "".join(r.text for r in p.runs)
        if "Maintenance family reduced 20%" in joined:
            p.runs[0].text = "Maintenance family kept turning: 14,662 billed, 15,007 sold on."
            for extra in list(p.runs[1:]):
                extra._r.getparent().remove(extra._r)
            newp = sh.text_frame.add_paragraph()
            newp.line_spacing = p.line_spacing
            nr = newp.add_run()
            nr.text = "One brake part: 214 pieces, EUR 16,923."
            nr.font.size = Pt(12.0)
            nr.font.name = FONT
            nr.font.color.rgb = rgb("BDBDBD")
            nr.font._rPr.set("lang", "en-US")
            fixed = True
print("A. old slide 10 maintenance row corrected:", fixed)
assert fixed

# title + one headline sentence on old slide 10, for the corrected reading
for sh in s10.shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("Reporting identifies where to rebalance"):
        sh.text_frame.paragraphs[0].runs[0].text = (
            "Reporting shows where stock sits in the wrong families"
        )
        break
for sh in s10.shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("The same reporting can show excess stock"):
        sh.text_frame.paragraphs[0].runs[0].text = (
            "The net build sat in brakes, body and electrical while the fastest-turning "
            "maintenance family kept turning and sold on more than it bought."
        )
        break
# the three card sub-lines on that slide that implied a family reduction
for sh in s10.shapes:
    if not sh.has_text_frame:
        continue
    t = sh.text_frame.text
    if t.startswith("Reported net parts build"):
        sh.text_frame.paragraphs[0].runs[0].text = "Reported net parts build, Jan 2025 to Aug 2026"
    if t.startswith("Brakes, body and electrical"):
        sh.text_frame.paragraphs[0].runs[0].text = "Brakes, body and electrical"
# the caveat that the family file does not foot to the headline
for sh in s10.shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith(
            "Source: supplied kickback review. Diagnostic values retained"):
        sh.text_frame.paragraphs[0].runs[0].text = (
            "Sources: headline EUR 225,744 and 2,252 parts from STOCK_CAMPAIGN_INSIGHTS_ALL_CUSTOMERS_"
            "20261007.md; family values from portugal_family_stock_build.csv, whose 42 rows total "
            "EUR 225,364, so the family detail is presented as its own value and not as a sum to the "
            "headline; part 8983767550 from portugal_pn_stock_build.csv."
        )
        break

# the preserved wider-review speaker notes still carried the false family claim in two places
FALSE = ("while the fastest-turning maintenance family was cut 20%")
TRUE = ("while the fastest-turning maintenance family was drawn down, not cut "
        "(billed 14,662 units, sold on 15,007)")
notes_fixed = 0
for s_ in (s10,):
    pass
for s_ in prs.slides:
    if not s_.has_notes_slide or s_.notes_slide.notes_text_frame is None:
        continue
    tf = s_.notes_slide.notes_text_frame
    for p in tf.paragraphs:
        for r in p.runs:
            if FALSE in r.text:
                r.text = r.text.replace(FALSE, TRUE)
                notes_fixed += 1
print("notes runs corrected:", notes_fixed)
assert notes_fixed >= 2

# =============================================================== B. persuasion slide
PERS = section_slide(prs, head_layout)
head(PERS, "I MOTORS  |  THE OVERSTOCK VISUALISED",
     "It ordered less, sold more, and held the wrong stock", "16")

txt(PERS, 0.42, 1.58, 12.49, 0.22,
    "ISZE billing against sales to dealer  \u00b7  EUR per month  \u00b7  the two lines move apart",
    10.5, MUTED)
pic(PERS, ASSETS / "imotors_divergence.png", 0.42, 1.86, 6.20, 2.30)

txt(PERS, 6.80, 1.58, 6.10, 0.22,
    "Net parts build by family  \u00b7  EUR  \u00b7  the six largest of 42 rows", 10.5, MUTED)
pic(PERS, ASSETS / "imotors_family_build.png", 6.62, 1.86, 6.01, 2.30)
txt(PERS, 6.62, 4.18, 6.10, 0.18,
    "Values from the family file; its 42 rows total EUR 225,364 and do not foot to the "
    "EUR 225,744 headline.", 7.4, MUTED)

# three dynamic cards
CY, CH = 4.44, 1.36
# card 1: stock against target, filled bar with a target marker
card(PERS, 0.42, CY, 4.038, CH, AMBER)
txt(PERS, 0.60, CY + 0.12, 3.68, 0.22, "I MOTORS  |  STOCK AGAINST TARGET", 9.5, AMBER, True)
txt(PERS, 0.60, CY + 0.36, 3.68, 0.38, "2.2 of 3.0 months", 20.0, WHITE, True)
index_bar(PERS, 0.60, CY + 0.88, 3.68, 2.2, 3.0, AMBER, 3.0, "target 3.0", "")
txt(PERS, 0.60, CY + 1.02, 3.68, 0.34,
    "Reported months of stock against the distributor's own 3.0-month target, August 2026.",
    8.5, MUTED)
# card 2: the divergence
card(PERS, 4.648, CY, 4.038, CH, RED)
txt(PERS, 4.83, CY + 0.12, 3.68, 0.22, "I MOTORS  |  TWO LINES MOVING APART", 9.5, RED, True)
pic(PERS, ASSETS / "imotors_divergence_small.png", 4.83, CY + 0.34, 3.90, 1.00)
# card 3: brake pads before / after
card(PERS, 8.876, CY, 4.038, CH, GREEN)
txt(PERS, 9.06, CY + 0.12, 3.68, 0.22, "I MOTORS  |  BRAKE PADS, BEFORE AND AFTER", 9.5, GREEN, True)
pic(PERS, ASSETS / "imotors_brake_pair.png", 9.06, CY + 0.34, 3.66, 0.58)
txt(PERS, 9.06, CY + 0.98, 3.68, 0.34,
    "1,370 bought and 994 sold to dealers in FY2026; 93 bought and 406 sold in FY2027 to August.",
    8.5, MUTED)

# the single part callout
PC_Y = 5.82
rect(PERS, 0.42, PC_Y, 12.49, 1.00, "383838")
rect(PERS, 0.42, PC_Y, 0.05, 1.00, RED)
txt(PERS, 0.62, PC_Y + 0.08, 8.20, 0.20, "SINGLE PART DOING THE WORK OF A PARAGRAPH", 8.6, RED, True)
txt(PERS, 0.62, PC_Y + 0.31, 8.20, 0.28,
    "Brake part 8983767550: 468 billed, 254 sold to dealers, 214 pieces still held", 12.6, WHITE, True)
txt(PERS, 0.62, PC_Y + 0.62, 8.20, 0.36,
    "214 pieces is not a finding on its own: it is EUR 16,923 of one part number parked on a "
    "shelf, while the fastest-turning families kept selling and the build sat in brakes, body "
    "and electrical.", 8.5, MUTED)
txt(PERS, 8.95, PC_Y + 0.12, 3.80, 0.42, "EUR 16,923", 22.0, AMBER, True, align=PP_ALIGN.RIGHT)
txt(PERS, 8.95, PC_Y + 0.58, 3.80, 0.18, "held in 214 pieces of one brake part", 8.5, MUTED,
    align=PP_ALIGN.RIGHT)
txt(PERS, 8.95, PC_Y + 0.76, 3.80, 0.18, "8983767550  \u00b7  468 billed, 254 sold on",
    8.5, MUTED, align=PP_ALIGN.RIGHT)

txt(PERS, 0.42, 6.90, 12.49, 0.24,
    "A distributor that looks quiet in our billing is selling more than ever while holding the "
    "wrong stock.", 12.2, WHITE, True)
txt(PERS, 0.42, 7.19, 12.49, 0.30,
    "Sources: headline net parts build EUR 225,744 across 2,252 parts, and 487 monthly back-order "
    "lines against a 305 target, from STOCK_CAMPAIGN_INSIGHTS_ALL_CUSTOMERS_20261007.md; family and "
    "part values from portugal_family_stock_build.csv and portugal_pn_stock_build.csv, whose rows "
    "total EUR 225,364 and not the headline; monthly billing, days of stock and the campaign window "
    "from portugal_reference_case_monthly.csv, campaign_window_totals.csv and the I Motors business "
    "review of 24 Sep 2026, slides 3, 8, 12 and 17; sales to dealer per "
    "portugal_billing_vs_sales_to_dealer.csv. Sales to dealer is not end-customer sales.",
    6.4, MUTED)

# =============================================================== C. European logic slide
EUR = section_slide(prs, head_layout)
head(EUR, "THE EUROPEAN LOGIC",
     "The distributor carries other brands on the same shelf and the same capital", " ")

txt(EUR, 0.42, 1.62, 6.10, 2.06, [
    "The European distributor is a multi-brand, independent business. An Isuzu parts line sits "
    "beside other brands on the same shelf and against the same working capital. Every euro it "
    "puts into Isuzu stock is a euro it does not put into another brand, and every Isuzu purchase "
    "is a decision it is free not to make.",
    "An incentive is therefore not a gift. In a single-brand market the push is close to "
    "automatic; in a multi-brand market it has to be earned every month against other brands' "
    "offers, stocking terms and margin deals. Where the distributor can choose, the incentive is "
    "how we hold attention.",
], 10.4, MUTED, space_before=5.0)
txt(EUR, 0.42, 1.62, 6.10, 0.24, "MULTI-BRAND, INDEPENDENT, AND ABLE TO CHOOSE", 9.5, RED, True, spc=65)

txt(EUR, 6.80, 1.62, 6.10, 0.24, "AND WE ARE THE DEARER ALTERNATIVE", 9.5, RED, True, spc=65)
txt(EUR, 6.80, 1.96, 6.10, 1.50, [
    "By our own measurement, an aftermarket price on file sits at a median 0.56 of our reference "
    "dealer price: the outside seller is about 44% cheaper than what a customer pays at our dealer "
    "counter.",
    "The measurement is narrow. An aftermarket price exists for 266 part numbers, 21.0% of parts "
    "billed, and a confirmed or likely competitor part number for only 78. \u201cNo alternative "
    "found\u201d mostly means that none was found, not that none exists. The observed prices are "
    "mostly German, Norwegian and UK listings, not Portuguese shop prices.",
], 10.4, MUTED, space_before=5.0)

# three dynamic cards
CY, CH = 3.86, 1.66
card(EUR, 0.42, CY, 4.038, CH, AMBER)
txt(EUR, 0.60, CY + 0.12, 3.68, 0.22, "AFTERMARKET PRICE AGAINST OURS", 9.5, AMBER, True)
txt(EUR, 0.60, CY + 0.34, 3.68, 0.38, "0.56 of our price", 19.0, WHITE, True)
index_bar(EUR, 0.60, CY + 0.86, 3.68, 0.56, 1.20, AMBER, 1.00, "our reference = 1.00",
          "266 part numbers, 21.0% of parts billed")
txt(EUR, 0.60, CY + 1.28, 3.68, 0.32,
    "A lower bar means the outside seller is cheaper. Weighted by parts billed the median is 0.44.",
    8.5, MUTED)

card(EUR, 4.648, CY, 4.038, CH, RED)
txt(EUR, 4.83, CY + 0.12, 3.68, 0.22, "HOW MUCH OF THE CATALOGUE IS PRICED", 9.5, RED, True)
txt(EUR, 4.83, CY + 0.34, 3.68, 0.38, "120 of 1,924", 19.0, WHITE, True)
index_bar(EUR, 4.83, CY + 0.86, 3.68, 120, 1924, RED, 1924, "full family", "")
txt(EUR, 4.83, CY + 1.06, 3.68, 0.56,
    "Portugal competitive family: an aftermarket price was observed for 120 part numbers, about "
    "31.6% of that family's CY2025 list value. The pressure is measured on a narrow part of the "
    "catalogue.", 8.5, MUTED)

card(EUR, 8.876, CY, 4.038, CH, GREEN)
txt(EUR, 9.06, CY + 0.12, 3.68, 0.22, "WHAT IS BEING ASKED BY FY2031", 9.5, GREEN, True)
txt(EUR, 9.06, CY + 0.34, 3.68, 0.38, "EUR 29.6M \u2192 52.1M", 19.0, WHITE, True)
pic(EUR, ASSETS / "growth_ask.png", 9.06, CY + 0.78, 3.66, 0.82)
txt(EUR, 9.06, CY + 1.66 - 0.14, 3.68, 0.18,
    "Ten customer plans, FY26 to FY27", 7.8, MUTED)

txt(EUR, 0.42, 5.86, 12.49, 0.20, "THE STAKE", 9.5, RED, True, spc=65)
txt(EUR, 0.42, 6.06, 12.49, 0.60, [
    "The growth asked for is 9.0% this year and roughly 6-12% a year to FY2031, taking the Kosha "
    "path from EUR 29.6M to EUR 52.1M, in the wider context of Isuzu's IX 2030 plan already noted "
    "on slide 3. Four of the ten customer plans rise by more than 12%, and Benelux by 3.4%.",
], 10.4, MUTED)
rect(EUR, 0.42, 6.72, 0.05, 0.34, RED)
txt(EUR, 0.60, 6.74, 12.30, 0.32,
    "In a market where the distributor can choose, the incentive is what makes Isuzu the brand "
    "they choose to grow.", 13.0, WHITE, True)
txt(EUR, 0.42, 7.13, 12.49, 0.34,
    "Sources: aftermarket index, the 266 part numbers and 21.0% of parts billed from "
    "ISZE_Pricing_Policy_Paper_2026-10-02.html, section 8, on the provisional 2.19 reference dealer "
    "basis; competitor part number count and the country caveat from the same section; Portugal "
    "coverage and list-value share from "
    "09_meetings/IMotors_FY2027_BPR/_competitive_price_overlap_20261006/summary.json; Kosha path "
    "and customer plan increases from slide 3 of this deck. The network index and the Portugal "
    "coverage are different bases and are not compared.",
    6.5, MUTED)

# =============================================================== notes
PERS.notes_slide.notes_text_frame.text = (
    "PRESENTER / This is the single most persuasive fact in the deck, and the purpose of the slide "
    "is to make the room feel it rather than read it. A distributor we ran campaigns with bought "
    "into the wrong families and then slowed its ordering, while the families that actually turn "
    "kept selling. That is real money parked on a shelf, and in our own billing it looks like weak "
    "demand when it is close to the opposite. Only the onward-sales reporting shows the difference: "
    "the insight proves the value of the data, and the data is what the kickback's reporting "
    "condition buys.\n"
    "THE CONTRAST. ISZE billing ran 16.2% below plan for April to September 2026 while sales to "
    "dealers rose 25.0% year on year for April to August 2026. Reported stock was 2.2 months "
    "against a 3.0-month target in August 2026. The chart on the left is the 16 months the "
    "distributor actually reported: the two lines move apart, and the gap widens to its widest in "
    "August 2026. The chart on the right is the net parts build by family - the cash is in brakes, "
    "accident and body, and electrical, not in the parts that move every day.\n"
    "THE SINGLE PART. Brake part 8983767550: 468 billed, 254 sold to dealers, 214 pieces still "
    "held, EUR 16,923. Use it as the concrete image. Make the point that 214 pieces is not a "
    "finding on its own - it is EUR 16,923 of one part number sitting on a shelf while the "
    "fast-moving families were drawn down.\n"
    "THE MECHANISM. Our campaign created the buy-in; their reporting revealed the hangover. "
    "The maintenance family is the clearest proof that the build was in the wrong place: it billed "
    "14,662 units and sold on 15,007, so the fastest-turning family was drawn down against "
    "purchases, not reduced or cut. Do not say the maintenance family fell 20%. That figure is a "
    "year-on-year fall in BILLING EURO for that family (EUR 142,427 in FY2025 to EUR 114,232 in "
    "FY2026, -19.8%), which is what a drawn-down family looks like on our side of the ledger, not "
    "evidence that the family shrank.\n"
    "MIXED SOURCES - KEEP THEM SEPARATE. The EUR 225,744 headline and the 2,252 parts are from "
    "STOCK_CAMPAIGN_INSIGHTS_ALL_CUSTOMERS_20261007.md. The family bars are from "
    "portugal_family_stock_build.csv, whose 42 rows total EUR 225,364 - about EUR 380 less than the "
    "headline. The difference is not explained, so the family bars are presented as their own "
    "values and must NOT be described as summing to the headline. Do not claim that the largest "
    "six families add up to the total.\n"
    "DATA AND SCOPE. The stock series only starts in November 2024 and has a gap at August 2026, "
    "so no longer history is implied. The monthly billing-versus-dealer chart covers the 16 months "
    "reported: September to December 2025 are missing and are shown as a break, not as zero. Sales "
    "to dealer is not end-customer sales. The two charts are different bases - billing euros are "
    "ISZE's prices to the distributor, dealer offtake is valued at ISZE unit prices - so the levels "
    "are not comparable price bases even though the directions are.\n"
    "[Sources] ISZE business billing and the distributor's monthly sales-to-dealer reports "
    "(sold-to 519 and 92) as compiled in 01_data/90_INBOX/_stock_insights_20261007/; "
    "portugal_billing_vs_sales_to_dealer.csv; portugal_family_stock_build.csv; "
    "portugal_pn_stock_build.csv; portugal_reference_case_monthly.csv; campaign_window_totals.csv; "
    "I_Motors_FY2027_Business_Performance_Review_2026-09-24_with_forecast_slide.pptx, slides 3, 8, "
    "10, 12 and 17."
)

EUR.notes_slide.notes_text_frame.text = (
    "PRESENTER / Use this slide to answer the question of why an incentive is needed at all in "
    "Europe, and to set the stake before the decision is taken. Keep it factual, not a lecture.\n"
    "THE ARGUMENT. The European distributor is a multi-brand, independent business. An Isuzu parts "
    "line sits beside other brands on the same shelf and against the same working capital. Every "
    "euro it puts into Isuzu stock is a euro it does not put into another brand, and every Isuzu "
    "purchase is a decision it is free not to make. In a single-brand market the push is close to "
    "automatic; in a multi-brand market it has to be earned every month against other brands' "
    "offers, stocking terms and margin deals. That is why the incentive is not a gift - it is how "
    "we hold attention in a market that has a choice.\n"
    "THE PRICE GAP, AND ITS LIMITS. By our own measurement an aftermarket price on file sits at a "
    "median 0.56 of our reference dealer price, so the outside seller is about 44% cheaper than "
    "what a customer pays at our dealer counter; weighted by parts billed the median is 0.44. State "
    "the limits in the same breath: this covers 266 part numbers, 21.0% of parts billed, a "
    "confirmed or likely competitor part number exists for only 78, and the observed prices are "
    "mostly German, Norwegian and UK listings rather than Portuguese shop prices. \u201cNo "
    "alternative found\u201d mostly means none was found, not that none exists.\n"
    "PORTUGAL, ON ITS OWN BASIS. In the Portugal competitive family, 1,924 part numbers, an "
    "aftermarket price was observed for 120, covering about 31.6% of that family's CY2025 list "
    "value. Do not mix this with the network index: the two are different bases and the slide does "
    "not compare them.\n"
    "THE STAKE. The plan asks 9.0% this year and roughly 6-12% a year to FY2031, the Kosha path "
    "from EUR 29.6M to EUR 52.1M, in the wider context of Isuzu's IX 2030 plan already noted on "
    "slide 3. Four of the ten customer plans rise by more than 12%; Benelux by only 3.4%. A "
    "multi-brand distributor will only commit to an increase like that in a brand it carries "
    "alongside others if there is a reason to prioritise it. The incentive is that reason.\n"
    "CLOSE ON. In a market where the distributor can choose, the incentive is what makes Isuzu the "
    "brand they choose to grow.\n"
    "[Sources] ISZE_Pricing_Policy_Paper_2026-10-02.html, section 8, outside-price index on the "
    "provisional 2.19 reference dealer basis, and the same section's coverage counts; "
    "09_meetings/IMotors_FY2027_BPR/_competitive_price_overlap_20261006/summary.json for the "
    "Portugal coverage; slide 3 of this deck, "
    "90_archive/root_files/ISZE Vehicle Parts - FY2026 Year-End Review.xlsx, sheet "
    "'Kosha Gap & FY2027'; 01_data/11_planning/budget_per_DB_reviewed_24042026.xlsx, sheet "
    "'Incentive FY27'. Isuzu's IX 2030 plan (JPY 6tn sales) is external context only."
)

# =============================================================== reorder + renumber
def move_slide(prs, old_index, new_index):
    lst = prs.slides._sldIdLst
    ids = list(lst)
    el = ids[old_index]
    lst.remove(el)
    lst.insert(new_index, el)


# added order is: 1..21 original, 22 persuasion, 23 european
move_slide(prs, 21, 9)    # persuasion -> immediately before the wider-review slide (now index 10)
move_slide(prs, 22, 20)   # european    -> immediately before the closing decision slide (now 21)
prs.save(str(WORK))
print("reordered copy saved:", WORK)

prs = Presentation(str(WORK))
slides = list(prs.slides)
print("deck after reorder:", len(slides), "slides")
for i, s in enumerate(slides, 1):
    sect = ""
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    try:
                        if str(r.font.color.rgb) == RED and r.font.size and r.font.size.pt == 9.0:
                            sect = r.text
                    except Exception:
                        pass
    print("   %02d  %s" % (i, sect))
    # page marker = the small right-aligned box at x 12.20
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        if sh.left is not None and abs(sh.left / 914400 - 12.20) < 0.02 \
                and abs((sh.top or 0) / 914400 - 0.25) < 0.02:
            sh.text_frame.paragraphs[0].runs[0].text = "%02d" % (i - 1)

# sanity: the sections that must exist, in order
labels = []
for s in slides:
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    try:
                        if str(r.font.color.rgb) == RED and r.font.size and r.font.size.pt == 9.0:
                            labels.append(r.text)
                    except Exception:
                        pass
order = ["THE OVERSTOCK VISUALISED", "THE EUROPEAN LOGIC", "DECISION AND FOLLOW-UP"]
pos = {k: [i for i, t in enumerate(labels) if k in t] for k in order}
print("positions:", pos)
assert pos["THE OVERSTOCK VISUALISED"] and pos["THE EUROPEAN LOGIC"]
assert pos["THE OVERSTOCK VISUALISED"][0] < pos["THE EUROPEAN LOGIC"][0] < pos["DECISION AND FOLLOW-UP"][0]

prs.save(str(PPTX))
print("saved:", PPTX)

