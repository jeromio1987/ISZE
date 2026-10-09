"""Add ONE slide to the LATEST kickback deck: the kickback-as-leverage dynamic arrow chain.

Target (Jerome: 'the latest on only'):
  09_meetings/Kickback_FY2026_Jump_Case/ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx
  (20 slides, 12192000 x 6858000 EMU). The 17-slide 'ISZE_Kickback_Management_Revised_2026-10-07.pptx'
  is NOT touched.

The new slide is APPENDED as slide 21 (page number 20). Appending means not one existing slide
is edited or renumbered, which is what '+' a new slide without disturbing the flow requires.

House style read from the file itself (slide by slide, XML + shape runs), not assumed:
  slide background  solidFill 262626
  panel / card fill 303030
  white F2F2F2, muted BDBDBD, red E30613, amber F5A000, green 31A354
  header divider 4B4B4B, 0.6pt
  font  Aptos everywhere, lnSpc 110%
  header  'ISZE  .  VEHICLE PARTS & ACCESSORIES' 7.8pt bold F2F2F2 at (0.42, 0.25)
  page no. 8.5pt bold BDBDBD right-aligned at (12.20, 0.25)
  section label 9.0pt bold E30613, spc=65, at (0.42, 0.55)
  title 19.0pt bold F2F2F2 at (0.42, 0.87)
  source line 7.6pt BDBDBD at (0.42, 7.09)

Chain geometry: four CHEVRON autoshapes, one per stage, pitched so that the point of each
chevron lands exactly inside the notch of the next -> a continuous, visibly connected arrow
band left to right. Chevron depth = adj * min(w,h); with w=3.3175", h=3.10", adj=0.0839 the
depth is 0.26"; pitch = w - depth = 3.0575" makes point and notch coincide exactly.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from copy import deepcopy

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt, Emu
from lxml import etree

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = ROOT / "09_meetings" / "Kickback_FY2026_Jump_Case"
PPTX = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
BACKUP_DIR = HERE / "_build" / "_backup"
BACKUP = BACKUP_DIR / "ISZE_Kickback_Management_Revised_v2_2026-10-07.orig.pptx"

# -- house style, read from the deck itself --
BG, PANEL, GRID = "262626", "303030", "4B4B4B"
WHITE, MUTED = "F2F2F2", "BDBDBD"
RED, AMBER, GREEN = "E30613", "F5A000", "31A354"
FONT = "Aptos"


def rgb(h):
    return RGBColor.from_string(h)


def no_line(shape):
    shape.line.fill.background()


def solid(shape, hex_fill):
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(hex_fill)


def kill_shadow(shape):
    try:
        shape.shadow.inherit = False
    except Exception:
        pass


def set_norm_autofit(tf):
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    for tag in ("a:noAutofit", "a:spAutoFit", "a:normAutofit"):
        e = bodyPr.find(qn(tag))
        if e is not None:
            bodyPr.remove(e)
    bodyPr.append(etree.SubElement(bodyPr, qn("a:normAutofit")))


def txt(slide, x, y, w, h, paras, size, color, bold=False, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP, spc=None, space_before=None, line_spacing=1.10):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    set_norm_autofit(tf)
    lines = paras if isinstance(paras, (list, tuple)) else [paras]
    for i, line in enumerate(lines):
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
        if spc is not None:
            r.font._rPr.set("spc", str(spc))
        r.font._rPr.set("lang", "en-US")
    return tb


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
    kill_shadow(s)
    return s


def hline(slide, x, y, w, color, width=0.6):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y),
                                   Inches(x + w), Inches(y))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    return c


# ============================ backup ============================
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
if not BACKUP.exists():
    shutil.copy2(PPTX, BACKUP)
    print("backup written:", BACKUP)
else:
    print("backup already present:", BACKUP)

prs = Presentation(str(PPTX))
n_before = len(prs.slides._sldIdLst)
assert n_before == 20, "expected 20 slides, found %d" % n_before
s20 = list(prs.slides)[19]
s20_label = s20.shapes[2].text_frame.text
assert s20_label.strip().upper() == "DECISION AND FOLLOW-UP", s20_label
print("deck before:", n_before, "slides; slide 20 section label =", s20_label)

# use the same layout part as slides 2-5 and 11-20 (slideLayout1.xml, master 1)
target_layout = None
for master in prs.slide_masters:
    for lay in master.slide_layouts:
        if lay.part.partname == "/ppt/slideLayouts/slideLayout1.xml":
            target_layout = lay
print("layout chosen:", target_layout.name, target_layout.part.partname)

slide = prs.slides.add_slide(target_layout)
print("placeholders carried from layout:", len(slide.placeholders))
for ph in list(slide.placeholders):
    ph._element.getparent().remove(ph._element)

slide.background.fill.solid()
slide.background.fill.fore_color.rgb = rgb(BG)

num = n_before  # new slide is 21 -> page number 20

# ============================ header ============================
txt(slide, 0.42, 0.25, 9.00, 0.22, "ISZE  \u00b7  VEHICLE PARTS & ACCESSORIES", 7.8, WHITE, True)
txt(slide, 12.20, 0.25, 0.70, 0.22, "%02d" % num, 8.5, MUTED, True, align=PP_ALIGN.RIGHT)
txt(slide, 0.42, 0.55, 12.49, 0.23, "THE KICKBACK AS LEVERAGE FOR DATA", 9.0, RED, True, spc=65)
txt(slide, 0.42, 0.87, 12.49, 0.57,
    "From the kickback to a higher distributor service level", 19.0, WHITE, True)
hline(slide, 0.42, 1.53, 12.49, GRID)

# ============================ arrow chain ============================
# four stacked CHEVRON arrows, point of one inside the notch of the next
N = 4
CW = 12.49                 # content width
ML = 0.42
CHEV_H = 3.10
DEPTH = 0.26               # notch / point depth
CHEV_W = (CW + 3 * DEPTH) / 4.0     # 3.3175 -> total span == CW when pitch = W - DEPTH
PITCH = CHEV_W - DEPTH
print("chevron w=%.4f pitch=%.4f span=%.4f" % (CHEV_W, PITCH, 3 * PITCH + CHEV_W))
ADJ = DEPTH / min(CHEV_W, CHEV_H)
print("chevron adj=%.5f" % ADJ)

STAGES = [
    {
        "chip": "1",
        "heading": "The kickback is the leverage for data",
        "body": [
            "Reporting is an existing condition of the incentive, not a separate reward. "
            "Distributors send monthly dealer-level detail (invoice date, part number, quantity, "
            "no prices) and the monthly KPI and SPI check sheets.",
            "Sending today: IUK, ITUK, Ireland, Portugal, Greece and Romania. "
            "UTI reports part of the year.",
            "Not sending: Germany (ISD), Benelux (IBX), UMI, Sweden and Norway.",
        ],
    },
    {
        "chip": "2",
        "heading": "The insights that visibility buys",
        "body": [
            "iMotors (Portugal): ISZE billing ran 16.2% below plan for April to September 2026, "
            "while sales to dealers rose 25.0% year on year for April to August 2026. Reported "
            "stock was 2.2 months against a 3.0-month target in August 2026. Lower billing did "
            "not mean lower dealer demand.",
            "IUK: a EUR 764,436 stock build, 51 to 97 days after the brake campaign, then 76% "
            "less buying for four months.",
            "Five markets: EUR 678,464 of parts dealers pulled through faster than the "
            "distributors reordered.",
        ],
    },
    {
        "chip": "3",
        "heading": "KPI positioning",
        "body": [
            "Fill rate: standard at least 95%, floor 92%. Back orders: at most 15 lines per "
            "EUR 100K of monthly dealer sales.",
            "Days of stock by supply class: A road (up to 5 days) 60 to 75; B road or short sea "
            "(5 to 12 days) 75 to 90; C by sea (3 weeks or more) 90 to 120.",
            "IBX returned into its 60 to 75-day band (32 to 63, January to July 2026); ITUK above "
            "in all 21 reported months, Ireland all 24, IUK 17 of 24.",
            "ISD cannot be placed: gap since January 2025; its 2 October 2026 submission stays "
            "indicative until loaded.",
        ],
    },
    {
        "chip": "4",
        "heading": "A higher distributor service level",
        "body": [
            "Distributors that can be measured can be managed, and those that hold the right "
            "stock serve their own dealers better.",
            "The objective is the right stock for each market and parts family, not a uniform "
            "increase in stock.",
        ],
    },
]

CHEV_TOP = 1.96
CHIP_TOP = 1.60
TEXT_INSET = 0.30           # clears the 0.26 notch and the 0.26 point
TEXT_W = CHEV_W - 2 * TEXT_INSET
print("card text width = %.4f in" % TEXT_W)

for i, st in enumerate(STAGES):
    cx = ML + i * PITCH
    # stage chip above the arrow
    rect(slide, cx, CHIP_TOP, 0.28, 0.22, RED)
    txt(slide, cx, CHIP_TOP + 0.005, 0.28, 0.21, st["chip"], 9.0, WHITE, True,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # the arrow itself
    ch = rect(slide, cx, CHEV_TOP, CHEV_W, CHEV_H, PANEL, line=RED,
              shape=MSO_SHAPE.CHEVRON, line_pt=1.0)
    ch.adjustments[0] = ADJ
    # heading + body, inset past the notch and the point
    txt(slide, cx + TEXT_INSET, CHEV_TOP + 0.14, TEXT_W, 0.46, st["heading"], 11.0, WHITE, True)
    txt(slide, cx + TEXT_INSET, CHEV_TOP + 0.62, TEXT_W, 2.42, st["body"], 9.5, MUTED,
        space_before=4.0)

# chain discharges into the closing block
CHEV_BOTTOM = CHEV_TOP + CHEV_H
for i in range(N):
    cx = ML + i * PITCH + CHEV_W / 2.0
    rect(slide, cx - 0.12, CHEV_BOTTOM + 0.04, 0.24, 0.14, RED, shape=MSO_SHAPE.DOWN_ARROW)

# ============================ the tension (closing block) ============================
PAN_TOP = 5.28
PAN_H = 1.68
rect(slide, 0.42, PAN_TOP, 12.49, PAN_H, PANEL)
rect(slide, 0.42, PAN_TOP, 12.49, 0.05, RED)
txt(slide, 0.60, PAN_TOP + 0.08, 11.90, 0.18, "THE TENSION", 9.0, RED, True, spc=65)
txt(slide, 0.60, PAN_TOP + 0.28, 11.90, 0.86, [
    "The network is being asked for a further 9.0% this year: the programme plan rising from "
    "EUR 29.19M in FY2026 to EUR 31.82M in FY2027, EUR 2.63M of additional sales, and then "
    "roughly 6% to 12% a year through to FY2031, taking the Kosha path from EUR 29.6M to EUR 52.1M.",
    "A plan that steep cannot be chased blind. It works only if we can see whether an increase "
    "is delivered or merely billed.",
    "The only thing that gives us that sight is the data, and the only thing that gets us the "
    "data is the reporting condition inside the kickback.",
], 10.5, MUTED, space_before=4.0)
rect(slide, 0.60, PAN_TOP + 1.20, 0.04, 0.36, RED)
txt(slide, 0.76, PAN_TOP + 1.22, 11.70, 0.34,
    "Weaken the kickback and you do not just remove the reward. "
    "You remove the visibility that makes the growth achievable.", 12.2, WHITE, True)

# ============================ source line ============================
txt(slide, 0.42, 7.09, 12.49, 0.40,
    "Sources: budget_per_DB_reviewed_24042026.xlsx, 'Incentive FY27'; FY2026 Year-End Review, "
    "'Kosha Gap & FY2027'; ISZE_DB_KPI_Targets_FY2627_v1.xlsx; KPI Master File august 2026.xlsx; "
    "monthly distributor reporting.",
    7.6, MUTED)

# speaker note (the deck keeps source detail in notes)
slide.notes_slide.notes_text_frame.text = (
    "PRESENTER / Stage 1 the reporting condition inside the incentive delivers the data. "
    "Emphasise that reporting is an existing condition of the incentive, not a separate reward: "
    "monthly dealer-level detail with invoice date, part number and quantity but no prices, plus "
    "the monthly KPI and SPI check sheets. Name who sends today (IUK, ITUK, Ireland, Portugal, "
    "Greece, Romania; UTI part of the year) and who does not (Germany/ISD, Benelux/IBX, UMI, "
    "Sweden, Norway).\n"
    "Stage 2 the insight the data buys. Lead with iMotors because it is the clearest proof that "
    "billing alone cannot be read as demand: ISZE billing 16.2% below plan for April to September "
    "2026 while sales to dealers rose 25.0% year on year for April to August 2026, with reported "
    "stock at 2.2 months against a 3.0-month target in August 2026. Then IUK (EUR 764,436 stock "
    "build, 51 to 97 days after the brake campaign, then 76% less buying for four months) and the "
    "five markets (EUR 678,464 of parts that dealers pulled through faster than the distributors "
    "reordered). Do not list more than these three.\n"
    "Stage 3 KPI positioning turns a reading into a management position. Standards: fill rate at "
    "least 95% with a 92% floor; back orders at most 15 lines per EUR 100K of monthly dealer "
    "sales; days of stock by supply class A (road, up to 5 days) 60 to 75, B (road or short sea, "
    "5 to 12 days) 75 to 90, C (by sea, 3 weeks or more) 90 to 120. Positions: IBX returned into "
    "its 60 to 75-day band, 32 to 63 days January to July 2026; ITUK above its band in all 21 "
    "reported months; Ireland all 24; IUK 17 of 24; ISD cannot be placed, gap since January 2025, "
    "with its 2 October 2026 submission indicative until loaded.\n"
    "Stage 4 the payoff. Distributors that can be measured can be managed, and those holding the "
    "right stock serve their own dealers better. The objective is the right stock for each market "
    "and parts family, not a uniform increase in stock.\n"
    "The tension. The network is asked for a further 9.0% this year, the programme plan rising "
    "from EUR 29.19M in FY2026 to EUR 31.82M in FY2027, EUR 2.63M of additional sales, then "
    "roughly 6% to 12% a year to FY2031, taking the Kosha path from EUR 29.6M to EUR 52.1M. Close "
    "on the line: weaken the kickback and you do not just remove the reward, you remove the "
    "visibility that makes the growth achievable.\n"
    "SOURCES. FY2026 EUR 29.19M and FY2027 EUR 31.82M, +9.0% / EUR 2.63M, from "
    "budget_per_DB_reviewed_24042026.xlsx, sheet 'Incentive FY27'. Kosha path FY2024 EUR 29.6M to "
    "FY2031 EUR 52.1M from the FY2026 Year-End Review, 'Kosha Gap & FY2027'. KPI standards from "
    "ISZE_DB_KPI_Targets_FY2627_v1.xlsx, sheets 'Assumptions' and 'Targets FY26-27' (fill "
    "standard 95%, floor 92%; class A 60-75, B 75-90, C 90-120 days; back orders 15 lines per "
    "EUR 100K). IBX 32 to 63 days, January to July 2026, is its own class A band of 60 to 75 "
    "days, not a minimum. iMotors 2.2 months against a 3.0-month target is the distributor's own "
    "reported basis and is labelled as such; the two bases are different standards and are not "
    "mixed.\n"
    "CARE POINTS. No order-mix improvement is claimed for IBX or ISD: the records are incomplete "
    "and the sign reverses when the affected months are removed. iMotors did not reduce its "
    "maintenance family: in the family file it billed 14,662 units and sold on 15,007, so the net "
    "parts build sat in brakes, body and electrical while the fastest-turning maintenance family "
    "kept turning. Do not state any minimum stock figure in months for IBX."
)

OUT = PPTX
# save the edited presentation to a scratch file, then repair the duplicate-master defect and
# land the result at OUT (in place). See repair_kickback_v2_master_20261007.py for the diagnosis.
TMP_OUT = HERE / "_build" / "_tmp_with_new_slide.pptx"
prs.save(str(TMP_OUT))
print("saved working copy:", TMP_OUT)

sys.path.insert(0, str(HERE / "_build"))
from repair_kickback_v2_master_20261007 import repair  # noqa: E402

info = repair(TMP_OUT, OUT)
print("master repair:", info)
TMP_OUT.unlink()
print("saved:", OUT)

# ============================ static self-check ============================
prs2 = Presentation(str(OUT))
SW, SH = prs2.slide_width, prs2.slide_height
EMU_IN = 914400
print("slides now:", len(prs2.slides._sldIdLst))
bad = []
for si, s in enumerate(prs2.slides, 1):
    for sh in s.shapes:
        l, t, w, h = sh.left, sh.top, sh.width, sh.height
        if l is None:
            continue
        if l < -10000 or t < -10000 or l + w > SW + 10000 or t + h > SH + 10000:
            bad.append("S%02d OUTSIDE %s l=%.2f t=%.2f r=%.2f b=%.2f"
                       % (si, sh.name, l / EMU_IN, t / EMU_IN, (l + w) / EMU_IN, (t + h) / EMU_IN))
print("off-slide shapes:", len(bad))
for b in bad:
    print("  ", b)
new = list(prs2.slides)[20]
print("new slide shape count:", len(new.shapes))
for sh in new.shapes:
    if sh.shape_type is not None and sh.has_text_frame and not sh.text_frame.text.strip():
        pass
    try:
        ast = str(sh.auto_shape_type)
    except Exception:
        ast = "(not autoshape)"
    if "CHEVRON" in ast or "ARROW" in ast:
        print("  arrow shape", sh.name, ast, "adj", [a for a in sh.adjustments])
