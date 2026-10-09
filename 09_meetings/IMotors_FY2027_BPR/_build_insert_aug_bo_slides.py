# -*- coding: utf-8 -*-
"""Insert August BO deep-dive slides into I-Motors Sep-closed review deck."""
from __future__ import annotations
import copy, json, shutil
from pathlib import Path
from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt, Emu

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SRC = ROOT / "09_meetings/IMotors_FY2027_BPR/I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx"
OUT = ROOT / "09_meetings/IMotors_FY2027_BPR/I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx"
BAK = ROOT / "09_meetings/IMotors_FY2027_BPR/_bak_I_Motors_FY2027_BPR_2026-10-06_Sep_closed_pre_aug_bo.pptx"
SUMMARY = ROOT / "01_data/90_INBOX/_imotors_bo_compare_20261006/IMOTORS_BO_HISTORY_ANALYSIS_20261006/summary.json"
CMD = ROOT / "09_meetings/IMotors_FY2027_BPR/OPEN_I_Motors_BPR_2026-10-06_Sep_closed.cmd"

S = json.loads(SUMMARY.read_text(encoding="utf-8"))
aug = next(m for m in S["monthly"] if m["ym"] == "2026-08")
age = S["age_band_aug"]
l1 = S["aug_by_l1"]
only_them = S["top_only_them"][:5]
both = S["top_both"][:5]

BG, PANEL, BORDER = "262626", "303030", "6E6E6E"
WHITE, MUTED, GRID = "F2F2F2", "BDBDBD", "4D4D4D"
RED, AMBER, GREY = "E30613", "F5A000", "B7B7B7"
FONT = "Aptos"

def rgb(h):
    return RGBColor.from_string(h)

def txt(slide, x, y, w, h, text, size=10, color=WHITE, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
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
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)

def panel(slide, points, x=9.86, y=1.46, w=3.25, h=5.58):
    rect(slide, x, y, w, h, PANEL, BORDER)
    txt(slide, x + 0.28, y + 0.26, w - 0.5, 0.2, "OBSERVATIONS / QUESTIONS", 7.5, RED, True)
    yy = y + 0.72
    step = (h - 0.95) / max(len(points), 1)
    for i, pnt in enumerate(points):
        rect(slide, x + 0.28, yy + 0.07, 0.09, 0.09, RED if i == 0 else AMBER, shape=MSO_SHAPE.OVAL)
        txt(slide, x + 0.52, yy, w - 0.8, step - 0.08, pnt, 8.4, WHITE)
        yy += step

def style_chart(ch, num_fmt="#,##0", legend=True):
    ch.font.name = FONT
    ch.font.size = Pt(8)
    ch.font.color.rgb = rgb(MUTED)
    ch.has_title = False
    if legend:
        ch.has_legend = True
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.color.rgb = rgb(MUTED)
        ch.legend.font.size = Pt(8)
    else:
        ch.has_legend = False
    va = ch.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb(GRID)
    va.major_gridlines.format.line.width = Pt(0.5)
    va.format.line.fill.background()
    va.tick_labels.font.color.rgb = rgb(MUTED)
    va.tick_labels.font.size = Pt(7.5)
    va.tick_labels.number_format = num_fmt
    va.tick_labels.number_format_is_linked = False
    ca = ch.category_axis
    ca.format.line.color.rgb = rgb(GRID)
    ca.tick_labels.font.color.rgb = rgb(MUTED)
    ca.tick_labels.font.size = Pt(7.5)

def col_fill(series, c):
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = rgb(c)
    series.format.line.fill.background()

def labels(series, fmt, color=WHITE, pos=XL_LABEL_POSITION.OUTSIDE_END, size=7.5):
    dl = series.data_labels
    dl.show_value = True
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.font.size = Pt(size)
    dl.font.color.rgb = rgb(color)
    dl.font.bold = True
    dl.position = pos

def base(prs, section, title, sub, source, page_no):
    # use blank layout - try index 6 then 0
    layout = None
    for i in range(len(prs.slide_layouts)):
        try:
            layout = prs.slide_layouts[i]
            if "Blank" in (layout.name or "") or i == 6:
                break
        except Exception:
            continue
    if layout is None:
        layout = prs.slide_layouts[0]
    s = prs.slides.add_slide(layout)
    # paint background
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = rgb(BG)
    bg.line.fill.background()
    # send to back via z-order: move element to first position
    spTree = s.shapes._spTree
    sp = bg._element
    spTree.remove(sp)
    spTree.insert(2, sp)

    txt(s, 0.25, 0.10, 3.8, 0.18, "ISZE  ·  VEHICLE PARTS & ACCESSORIES", 6.6, WHITE, True)
    txt(s, 0.25, 0.43, 7.5, 0.22, section.upper(), 7.5, RED, True)
    txt(s, 0.25, 0.68, 9.45, 0.66, title, 18 if len(title) > 70 else 20, WHITE, True)
    txt(s, 0.25, 1.42, 9.45, 0.24, sub, 8.5, MUTED)
    hline(s, 0.25, 7.18, 12.85, "575757")
    txt(s, 0.25, 7.24, 11.5, 0.16, source, 6.5, "8C8C8C")
    txt(s, 12.55, 7.24, 0.55, 0.16, str(page_no), 7, MUTED, align=PP_ALIGN.RIGHT)
    return s

def eur_k(v):
    v = float(v)
    if abs(v) >= 1000:
        return f"€{v/1000:.1f}k"
    return f"€{v:,.0f}"

def set_run_text(shape, new_text):
    """Replace first paragraph text keeping font of first run where possible."""
    tf = shape.text_frame
    if not tf.paragraphs:
        return
    p = tf.paragraphs[0]
    if p.runs:
        # clear extra runs
        p.runs[0].text = new_text
        for r in p.runs[1:]:
            r.text = ""
    else:
        r = p.add_run()
        r.text = new_text

def replace_containing(slide, needle, replacement):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        full = sh.text_frame.text
        if needle in full:
            # rebuild all paragraphs simply as one block if multi
            # safer: replace in each run
            for para in sh.text_frame.paragraphs:
                for run in para.runs:
                    if needle in run.text:
                        run.text = run.text.replace(needle, replacement)
            # if split across runs, replace whole text frame
            if needle in sh.text_frame.text:
                # flatten to first run
                text = sh.text_frame.text.replace(needle, replacement)
                first = True
                for para in sh.text_frame.paragraphs:
                    for run in para.runs:
                        if first:
                            run.text = text
                            first = False
                        else:
                            run.text = ""
            return True
    return False

# --- backup and open ---
shutil.copy2(SRC, BAK)
prs = Presentation(str(SRC))

# Fix discussion slide 26 (index 25) stale fill-rate claim
slide26 = prs.slides[25]
replace_containing(
    slide26,
    "I Motors → dealer fill rate is at its 85% target; ISZE → I Motors is below 93%.\n\nDiscuss: the part numbers behind the ISZE misses, and a stock floor so dealer fill rate holds.",
    "I Motors → dealer fill rate fell to 81.0% in September; ISZE → I Motors stays below 93%.\n\nDiscuss: part numbers behind the misses, and a stock floor so dealer fill rate recovers to 85%.",
)
# shorter fallback if newlines differ
replace_containing(slide26, "I Motors → dealer fill rate is at its 85% target", "I Motors → dealer fill rate fell to 81.0% in September")
replace_containing(slide26, "MOS 2.2", "MOS 2.5")

# Fix slide 17 question to point into August deep dive
slide17 = prs.slides[16]
replace_containing(
    slide17,
    "Question: is 2.5 months a deliberate stock target, and which families will I Motors rebuild first?",
    "Question: which aged back-order euros (see next slides, August book) should clear first while MOS rebuilds?",
)

# --- build two new slides at end, then reorder ---
src_note = "Source: I Motors Backordered lines 2026.xlsx (month-end 31 Aug 2026); AIM catalogue cut. September KPI 495 lines not PN-cut here."

# Slide A - age / euro
s18 = base(
    prs,
    "Back orders  ·  August book",
    "August looked calm on line count — almost half the open euro was older than 90 days",
    "I Motors back orders at 31 Aug 2026  |  282 lines  |  €76.4k open  |  line count matches the KPI B/O row",
    src_note,
    18,
)
# tiles
for i, (lab, big, sub, col) in enumerate([
    ("OPEN LINES", "282", "Same as KPI B/O Aug", WHITE),
    ("OPEN EURO", "€76.4k", "Qty pending × unit price", WHITE),
    ("91+ DAYS", "€33.6k", "21 lines · 44% of Aug euro", RED),
    ("MEDIAN AGE", "6 days", "Most lines are recent", WHITE),
]):
    x = 0.40 + i * 2.35
    rect(s18, x, 1.75, 2.25, 1.15, PANEL, BORDER)
    txt(s18, x + 0.12, 1.85, 2.0, 0.18, lab, 7, RED, True)
    txt(s18, x + 0.12, 2.08, 2.0, 0.40, big, 22, col, True)
    txt(s18, x + 0.12, 2.52, 2.0, 0.30, sub, 7.5, MUTED)

# age euro chart
cd = CategoryChartData()
cd.categories = [f"{b}d" for b in age["band"]]
cd.add_series("Open €", age["eur"])
ch = s18.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.40), Inches(3.05), Inches(9.20), Inches(3.85), cd).chart
style_chart(ch, "€#,##0", legend=False)
col_fill(ch.series[0], RED)
try:
    labels(ch.series[0], "€#,##0", WHITE, XL_LABEL_POSITION.OUTSIDE_END, 7)
except Exception:
    pass
txt(s18, 0.50, 2.95, 4.5, 0.18, "OPEN EURO BY AGE BAND  ·  31 AUG", 8, RED, True)

panel(s18, [
    "August fill rate to dealers was still at target (85.4%) with 282 back-order lines — the count alone looked fine.",
    "€33.6k of the €76.4k open sat past 90 days. That pocket is mostly accident and body hardware, not fast wear parts.",
    "Median age is only 6 days: the book is young on count and old on money at the same time.",
    "Question: who owns clearing the aged body / shutter / fender euros before stock policy talks?",
])

# Slide B - families + shortlist
s19 = base(
    prs,
    "Back orders  ·  August book",
    "Accident and body lead August open euro; competitive wear is the shortlist still open with ISZE",
    "AIM catalogue families on the 31 Aug back-order extract  |  analysis stops at August",
    src_note,
    19,
)

# AIM L1 chart
l1_items = sorted(l1.items(), key=lambda kv: -kv[1]["eur"])[:6]
cd2 = CategoryChartData()
cd2.categories = [k.replace(" parts", "") for k, _ in l1_items]
cd2.add_series("Open €", [v["eur"] for _, v in l1_items])
ch2 = s19.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.40), Inches(1.75), Inches(5.4), Inches(5.15), cd2).chart
style_chart(ch2, "€#,##0", legend=False)
col_fill(ch2.series[0], "B7B7B7")
# highlight first bar red if possible
try:
    pt = ch2.series[0].points[0]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = rgb(RED)
except Exception:
    pass
txt(s19, 0.50, 1.75, 5.0, 0.18, "AUGUST OPEN € BY FAMILY", 8, RED, True)

# right column shortlists
rect(s19, 6.00, 1.75, 3.60, 2.45, PANEL, BORDER)
txt(s19, 6.15, 1.88, 3.3, 0.20, "AGED / ONLY ON THEIR AUG BOOK", 7.5, RED, True)
yy = 2.15
for r in only_them[:4]:
    line = f"{r['pn']}  {r['desc'][:18]}  {eur_k(r['their_eur'])}  {r['their_age_max']}d"
    txt(s19, 6.15, yy, 3.3, 0.38, line, 7.8, WHITE)
    yy += 0.42
txt(s19, 6.15, 3.85, 3.3, 0.25, "Not on ISZE open orders as of 6 Oct", 7.2, MUTED)

rect(s19, 6.00, 4.35, 3.60, 2.55, PANEL, BORDER)
txt(s19, 6.15, 4.48, 3.3, 0.20, "STILL OPEN BOTH SIDES (AUG↔OCT)", 7.5, RED, True)
yy = 4.75
for r in both[:4]:
    line = f"{r['pn']}  {r['desc'][:18]}  {eur_k(r['their_eur'])}"
    txt(s19, 6.15, yy, 3.3, 0.38, line, 7.8, WHITE)
    yy += 0.42
txt(s19, 6.15, 6.45, 3.3, 0.30, "Filters, pads, glass — shared shortlist", 7.2, MUTED)

panel(s19, [
    "Accident / body is the largest August euro block (€28.3k). Competitive is second (€21.1k).",
    "Aged body lines dominate ‘only on their book’. Competitive pads and filters show up on both sides.",
    "This cut stops at 31 August. September’s KPI jump to 495 lines is on the previous slide as a count only.",
    "Question: clear aged body euros first, or rebuild competitive cover with ISZE first?",
])

# --- reorder: move last 2 slides to after slide 17 (index 16) ---
# presentation.xml sldIdLst
pres = prs.part
sldIdLst = pres._element.find(qn("p:sldIdLst"))
ids = list(sldIdLst)
# last two are the new slides
new_ids = ids[-2:]
# remove them from end
for el in new_ids:
    sldIdLst.remove(el)
# insert after index 16 (0-based) → after 17th child
# current ids[16] is slide 17; insert after it → position 17
for i, el in enumerate(new_ids):
    sldIdLst.insert(17 + i, el)

# renumber page footers: find small right-bottom textboxes that look like page numbers
# After reorder, python-pptx slide order follows sldIdLst
prs.save(str(OUT))

# reopen and renumber
prs2 = Presentation(str(OUT))
for i, slide in enumerate(prs2.slides, 1):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        # page number boxes are short numeric at bottom right
        if t.isdigit() and sh.left > Inches(12.0) and sh.top > Inches(7.0):
            for para in sh.text_frame.paragraphs:
                for run in para.runs:
                    run.text = str(i)
                    break
prs2.save(str(OUT))

# ensure OPEN cmd
CMD.write_bytes(b'@echo off\r\nstart "" "%~dp0I_Motors_FY2027_Business_Performance_Review_2026-10-06_Sep_closed.pptx"\r\n')

print("OUT", OUT, OUT.stat().st_size)
print("BAK", BAK)
print("slides", len(prs2.slides))
# verify titles around insert
for i in range(15, 22):
    slide = prs2.slides[i]
    texts = [sh.text_frame.text.strip().replace("\n"," ")[:80] for sh in slide.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    print(f"{i+1:02d}", texts[1] if len(texts)>1 else texts[0] if texts else "?")
