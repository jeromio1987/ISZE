# -*- coding: utf-8 -*-
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

RED       = RGBColor(0xCC, 0x0E, 0x1E)
LIGHT_RED = RGBColor(0xDC, 0x60, 0x6E)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
BLACK     = RGBColor(0x1A, 0x1A, 0x1A)
GRAY      = RGBColor(0x5A, 0x5A, 0x5A)
LGRAY     = RGBColor(0xF0, 0xF0, 0xF0)
MGRAY     = RGBColor(0xD9, 0xD9, 0xD9)

SW, SH = Inches(13.33), Inches(7.5)
TEMPLATE = r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu\isuzu-ppt-template\assets\template.pptx"

prs = Presentation(TEMPLATE)
while prs.slides:
    rId = prs.slides._sldIdLst[0].rId
    prs.part.drop_rel(rId); del prs.slides._sldIdLst[0]

def set_white_bg(s):
    f = s.background.fill; f.solid(); f.fore_color.rgb = WHITE

def txt(s, text, left, top, width, height, size=14, bold=False, color=BLACK,
        align=PP_ALIGN.LEFT, font="Calibri", wrap=True, anchor=None):
    box = s.shapes.add_textbox(left, top, width, height); tf = box.text_frame
    tf.word_wrap = wrap
    if anchor is not None: tf.vertical_anchor = anchor
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold
        r.font.color.rgb = color; r.font.name = font
    return box

def rect(s, left, top, width, height, fill_color, rounded=False):
    sh = s.shapes.add_shape(5 if rounded else 1, left, top, width, height)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill_color
    sh.line.fill.background(); sh.shadow.inherit = False
    return sh

def oval(s, left, top, width, height, fill_color):
    sh = s.shapes.add_shape(9, left, top, width, height)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill_color
    sh.line.fill.background(); sh.shadow.inherit = False
    return sh

def add_logo(s, left, top, size=18):
    return txt(s, "ISUZU", left, top, Inches(2.0), Inches(0.55),
               size=size, bold=True, color=RED, font="Arial Black")

def add_footer_bar(s):
    h = Inches(0.13); rect(s, 0, SH - h, SW, h, RED)

def content(title, tag="CANDIDATE SLIDE — internal"):
    s = prs.slides.add_slide(prs.slide_layouts[6]); set_white_bg(s)
    add_logo(s, Inches(0.28), Inches(6.80)); add_footer_bar(s)
    txt(s, title, Inches(0.28), Inches(0.30), Inches(12.77), Inches(0.72),
        size=30, bold=True, color=BLACK)
    rect(s, Inches(0.28), Inches(1.02), Inches(12.77), Emu(38100), RED)
    txt(s, tag, Inches(9.0), Inches(6.95), Inches(4.0), Inches(0.3),
        size=9, color=MGRAY, align=PP_ALIGN.RIGHT)
    return s

def body(s, items, x=Inches(0.6), y=Inches(1.45), w=Inches(12.1), size=17):
    box = s.shapes.add_textbox(x, y, w, Inches(5.0)); tf = box.text_frame
    tf.word_wrap = True
    for i, (lvl, lead, rest) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10 if lvl == 0 else 5)
        mark = "•  " if lvl == 0 else "      –  "; sz = size if lvl == 0 else size-2
        r0 = p.add_run(); r0.text = mark
        r0.font.size = Pt(sz); r0.font.color.rgb = (RED if lvl==0 else GRAY)
        r0.font.bold = (lvl==0); r0.font.name="Calibri"
        if lead:
            r1=p.add_run(); r1.text=lead+(" " if rest else "")
            r1.font.size=Pt(sz); r1.font.bold=True; r1.font.color.rgb=BLACK; r1.font.name="Calibri"
        if rest:
            r2=p.add_run(); r2.text=rest
            r2.font.size=Pt(sz); r2.font.color.rgb=BLACK; r2.font.name="Calibri"
    return box

def style_cell(cell, text, size=12, bold=False, color=BLACK, fill=None, align=PP_ALIGN.LEFT):
    cell.margin_top=Pt(3); cell.margin_bottom=Pt(3)
    cell.margin_left=Pt(7); cell.margin_right=Pt(7)
    cell.vertical_anchor=MSO_ANCHOR.MIDDLE
    if fill is not None:
        cell.fill.solid(); cell.fill.fore_color.rgb=fill
    else:
        cell.fill.solid(); cell.fill.fore_color.rgb=WHITE
    tf=cell.text_frame; tf.word_wrap=True
    p=tf.paragraphs[0]; p.alignment=align
    r=p.add_run(); r.text=text
    r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=color; r.font.name="Calibri"

def add_table(s, rows, x, y, w, col_w, header_fill=RED, body_size=12, hdr_size=12):
    nr=len(rows); nc=len(rows[0])
    gt=s.shapes.add_table(nr,nc,x,y,w,Inches(0.4*nr)).table
    for j,cw in enumerate(col_w): gt.columns[j].width=cw
    # disable default banding
    gt.first_row=False; gt.horz_banding=False
    for i,row in enumerate(rows):
        for j,val in enumerate(row):
            cell=gt.cell(i,j)
            if i==0:
                style_cell(cell,val,size=hdr_size,bold=True,color=WHITE,fill=header_fill,
                           align=PP_ALIGN.LEFT if j==0 else PP_ALIGN.CENTER)
            else:
                fill = LGRAY if i%2==0 else WHITE
                bold = (row[0].lower().startswith("total"))
                style_cell(cell,val,size=body_size,bold=bold,color=BLACK,fill=(MGRAY if bold else fill),
                           align=PP_ALIGN.LEFT if j==0 else PP_ALIGN.CENTER)
    return gt

# =====================================================================
# COVER / divider
s = prs.slides.add_slide(prs.slide_layouts[6]); set_white_bg(s)
add_logo(s, Inches(0.38), Inches(0.22), size=26); add_footer_bar(s)
txt(s, "Candidate slides", Inches(0.5), Inches(2.6), Inches(11), Inches(1.0),
    size=38, bold=True, color=BLACK)
txt(s, "Pick what to move into the UTI meeting deck. Internal — not for sharing as-is.",
    Inches(0.5), Inches(3.7), Inches(11), Inches(0.6), size=16, color=GRAY)

# ---- A: BP FY27 performance ----
s = content("BP FY27 — start of year")
add_table(s, [
    ["FY27 (€K)", "Apr", "May", "YTD"],
    ["Sales", "211", "191", "402"],
    ["Budget", "247", "235", "482"],
    ["vs Budget", "−14%", "−19%", "−17%"],
    ["Prior year", "294", "286", "580"],
    ["vs Prior year", "−28%", "−33%", "−31%"],
    ["Order intake", "182", "238", "420"],
], Inches(0.6), Inches(1.45), Inches(6.4),
   [Inches(2.5), Inches(1.3), Inches(1.3), Inches(1.3)], body_size=13, hdr_size=13)
body(s, [
    (0, "Soft start:", "YTD sales €402K — −17% vs budget, −31% vs last year."),
    (0, "Both months below plan", "(Apr −14%, May −19%)."),
    (0, "Order intake turning up:", "May €238K vs €182K in April."),
    (0, "Full-year budget €3.1M", "(prior year €2.9M) — recovery builds from here."),
], x=Inches(7.4), y=Inches(1.55), w=Inches(5.6), size=15)

# ---- B: GPS / PMS capture ----
s = content("UTI Genuine Parts capture (PMS, 2025)")
add_table(s, [
    ["Category", "Capture", "Genuine", "Annual gap"],
    ["Brake pad", "23%", "23%", "€110K"],
    ["Clutch (disc + plate)", "2%", "0%", "€83K"],
    ["Air filter", "50%", "1%", "€28K"],
    ["Oil filter", "128%", "0%", "—"],
    ["Fuel filter", "102%", "0%", "—"],
    ["Total identified gap", "", "", "≈ €221K"],
], Inches(0.6), Inches(1.45), Inches(6.6),
   [Inches(2.9), Inches(1.25), Inches(1.25), Inches(1.2)], body_size=12.5, hdr_size=12.5)
body(s, [
    (0, "Two different stories:", ""),
    (1, "Brakes & clutch", "– lost to the aftermarket (≈€193K). A price / SPA lever."),
    (1, "Filters", "– captured, but almost entirely BVP, not genuine. A mix / upsell question."),
    (0, "Brake pad is the biggest single gap", "and the trend is declining."),
    (0, "Parc basis ≈ 10,700 units", "(Israel)."),
], x=Inches(7.5), y=Inches(1.55), w=Inches(5.5), size=14)

# ---- C: how it connects ----
s = content("How the topics connect")
steps = [
    ("1", "Sales down", "YTD −31% vs last year"),
    ("2", "SPA flexibility", "defend price on contested lines"),
    ("3", "Recapture the PMS gap", "≈ €221K/yr — brakes, clutch, filters"),
    ("4", "Needs accurate UIO", "to size it on the real parc"),
]
bx, by, bw, bh, gap = Inches(0.45), Inches(2.45), Inches(2.85), Inches(2.3), Inches(0.32)
for i,(num,title,sub) in enumerate(steps):
    x = Emu(int(bx) + i*(int(bw)+int(gap)))
    card = rect(s, x, by, bw, bh, LGRAY, rounded=True)
    rect(s, x, by, bw, Inches(0.18), RED, rounded=False)
    oval(s, Emu(int(x)+int(Inches(0.2))), Emu(int(by)+int(Inches(0.35))), Inches(0.62), Inches(0.62), RED)
    txt(s, num, Emu(int(x)+int(Inches(0.2))), Emu(int(by)+int(Inches(0.43))), Inches(0.62), Inches(0.5),
        size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txt(s, title, Emu(int(x)+int(Inches(0.18))), Emu(int(by)+int(Inches(1.15))), Emu(int(bw)-int(Inches(0.36))), Inches(0.7),
        size=15, bold=True, color=BLACK)
    txt(s, sub, Emu(int(x)+int(Inches(0.18))), Emu(int(by)+int(Inches(1.65))), Emu(int(bw)-int(Inches(0.36))), Inches(0.6),
        size=12, color=GRAY)
    if i < 3:
        ax = Emu(int(x)+int(bw)+int(Inches(0.02)))
        txt(s, "›", ax, Emu(int(by)+int(Inches(0.85))), Inches(0.3), Inches(0.6),
            size=30, bold=True, color=RED, align=PP_ALIGN.CENTER)
txt(s, "One logic: a softer market makes price flexibility and capturing more of the existing parc's "
       "demand the two ways to protect the business — both depend on knowing the real UIO.",
    Inches(0.5), Inches(5.1), Inches(12.3), Inches(0.9), size=15, color=BLACK)

# ---- D: GPS spend-per-unit trend ----
s = content("GPS — genuine + value parts spend per vehicle")
cd = CategoryChartData()
cd.categories = ["2023", "2024", "2025"]
cd.add_series("Spend per unit (€)", (331, 249, 313))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(0.6), Inches(1.5), Inches(7.2), Inches(4.6), cd)
chart = gf.chart; chart.has_legend = False
plot = chart.plots[0]; plot.has_data_labels = True
plot.data_labels.number_format = '€0'; plot.data_labels.number_format_is_linked = False
plot.data_labels.font.size = Pt(13); plot.data_labels.font.bold = True
for series in plot.series:
    series.format.fill.solid(); series.format.fill.fore_color.rgb = RED
body(s, [
    (0, "", "Parts spend per vehicle dipped in 2024, recovered in 2025."),
    (0, "2025 ≈ €313/unit,", "still below the 2023 level of €331."),
    (0, "On a parc of ≈ 10,700 units", "— so small per-unit moves scale quickly."),
    (0, "", "The PMS gap shows where the next per-unit gains sit."),
], x=Inches(8.1), y=Inches(1.7), w=Inches(4.9), size=15)

import os
out = r"C:\Users\jerom\Desktop\claude\ISZE\Preparation Meetings\UTI\UTI_Candidate_Slides.pptx"
try:
    prs.save(out); print("saved", out)
except PermissionError:
    alt = out.replace(".pptx","_v2.pptx"); prs.save(alt); print("LOCKED - saved", alt)
