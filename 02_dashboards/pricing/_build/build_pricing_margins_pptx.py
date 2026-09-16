#!/usr/bin/env python3
"""Build ISZE FY2027 pricing-revision margin deck (PPTX).

Presents the margin model across the three lists:
  PR00 (class factors) · ZPR1 Israel (UMI 1797 / UTI 1799) · CIS (GA + CBC)
plus the IML formula inputs and the parts still missing from the revision.

Source of truth: 03_analytics/isze_pricing/config.yaml + pricing-basket-2026.md
Reuses the ISZE brand deck builder + chart theme (04_tools/ppt_template_v2).
"""
from __future__ import annotations

import os
import sys

from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE")
TPL = os.path.join(ROOT, "04_tools", "ppt_template_v2")
sys.path.insert(0, TPL)

import isze_chart_theme as ct  # noqa: E402
import isze_deck_builder as db  # noqa: E402

RED = db.RED
BLACK = db.BLACK
GRAY = db.GRAY
GRAY_BG = db.GRAY_BG
WHITE = db.WHITE

OUT = os.path.join(ROOT, "02_dashboards", "pricing", "ISZE_Pricing_Revision_Margins_FY2027.pptx")
CHART_DIR = os.path.join(ROOT, "02_dashboards", "pricing", "_build", "_margin_charts")
os.makedirs(CHART_DIR, exist_ok=True)

# class factor -> GM% (config.yaml, PR00 FY2026)
CLASSES = [
    ("P", 0.440, 56.0),
    ("C", 0.470, 53.0),
    ("D", 0.480, 52.0),
    ("M", 0.500, 50.0),
    ("F", 0.525, 47.5),
    ("V", 0.550, 45.0),
    ("J", 0.555, 44.5),
    ("T", 0.800, 20.0),
]

# ZPR1 = PR00 x 0.90 (flat -10%). Implied GM = 1 - class_factor/0.90.
def zpr1_gm(factor: float) -> float:
    return round((1 - factor / 0.90) * 100, 1)


def table(slide, headers, rows, left, top, width, height, col_widths=None,
          header_fill=RED, header_color=WHITE, body_size=13):
    n_rows = len(rows) + 1
    n_cols = len(headers)
    shp = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    tbl = shp.table
    if col_widths:
        for i, w in enumerate(col_widths):
            tbl.columns[i].width = w
    # header
    for c, h in enumerate(headers):
        cell = tbl.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_fill
        cell.margin_top = Emu(20000)
        cell.margin_bottom = Emu(20000)
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.RIGHT
        r = p.runs[0] if p.runs else p.add_run()
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.color.rgb = header_color
        r.font.name = "Calibri"
    # body
    for i, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = tbl.cell(i, c)
            cell.text = str(val)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 else GRAY_BG
            cell.margin_top = Emu(12000)
            cell.margin_bottom = Emu(12000)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.RIGHT
            r = p.runs[0] if p.runs else p.add_run()
            r.font.size = Pt(body_size)
            r.font.color.rgb = BLACK
            r.font.name = "Calibri"
            if c == 0:
                r.font.bold = True
    return shp


def section_label(slide, text, left, top, width):
    db.txt(slide, text.upper(), left, top, width, Inches(0.3),
           size=11, bold=True, color=RED)


# ---------------------------------------------------------------- charts --
PR00_GM = [g for _, _, g in CLASSES]
ZPR1_GM = [zpr1_gm(f) for _, f, _ in CLASSES]
cls_labels = [c for c, _, _ in CLASSES]

ct.bar_chart(
    cls_labels,
    {"PR00 GM %": PR00_GM},
    os.path.join(CHART_DIR, "pr00_gm.png"),
    value_fmt="{:,.1f}",
    figsize=(9.0, 4.2),
)

ct.bar_chart(
    cls_labels,
    {"PR00 GM %": PR00_GM, "ZPR1 −10%": ZPR1_GM},
    os.path.join(CHART_DIR, "pr00_vs_zpr1.png"),
    value_fmt="{:,.1f}",
    figsize=(9.6, 4.6),
)


# ---------------------------------------------------------------- slides --
prs = db.new_presentation()

# 1 · Cover
db.build_cover(
    prs,
    "FY2027 Pricing Revision",
    "Margin model across the three lists — PR00 · Israel (ZPR1) · CIS  |  ISZE internal",
    eyebrow="ISZE · VEHICLE PARTS & ACCESSORIES · PRICING",
)

# 2 · IML formula (unchanged)
s = db.build_content(prs, "The IML formula is untouched", eyebrow="Cost basis", page_no=2)
db.txt(s, "SP_EUR = FOB_EUR / class_factor    ·    FOB_EUR = BP_JPY / FX × source_discount",
       Inches(0.32), Inches(1.30), Inches(12.5), Inches(0.5), size=17, bold=True, color=BLACK)
db.txt(s, "ISZE has no pricing discretion — pass-through of IML base prices in JPY.",
       Inches(0.32), Inches(1.85), Inches(12.5), Inches(0.4), size=14, color=GRAY)
table(s, ["Input", "Value", "Basis"],
      [["FX rate", "163.7 JPY/EUR", "FY2026, Oct 2025"],
       ["Source J discount", "0.62", "Japan / IML sourced"],
       ["Source T discount", "0.611", "Thailand / IMIT sourced"],
       ["Class factor", "0.44 – 0.80", "Sets gross margin per class (next slide)"]],
      Inches(0.32), Inches(2.45), Inches(12.6), Inches(3.4),
      col_widths=[Inches(3.4), Inches(4.6), Inches(4.6)], body_size=14)
db.txt(s, "FX symmetry: prices were not reduced when JPY weakened without IML instruction.",
       Inches(0.32), Inches(6.15), Inches(12.5), Inches(0.4), size=12, color=GRAY)

# 3 · PR00 class factors -> GM
s = db.build_content(prs, "PR00 — gross margin by class factor", eyebrow="PR00 · main EU list", page_no=3)
db.add_picture_fit(s, os.path.join(CHART_DIR, "pr00_gm.png"),
                   Inches(0.32), Inches(1.30), Inches(6.5), Inches(5.0))
rows = [[c, f"{f:.3f}", f"{g:.1f}%"] for c, f, g in CLASSES]
table(s, ["Class", "Factor", "GM"], rows,
      Inches(7.2), Inches(1.30), Inches(5.7), Inches(5.3),
      col_widths=[Inches(1.7), Inches(2.0), Inches(2.0)], body_size=13)
db.txt(s, "GM = 1 − class_factor. P (56%) prices the most aggressively; T (20%) is the lowest-margin class.",
       Inches(7.2), Inches(6.75), Inches(5.7), Inches(0.6), size=11, color=GRAY)

# 4 · ZPR1 Israel
s = db.build_content(prs, "Israel (ZPR1) — flat −10% on PR00", eyebrow="ZPR1 · UMI 1797 / UTI 1799", page_no=4)
db.add_picture_fit(s, os.path.join(CHART_DIR, "pr00_vs_zpr1.png"),
                   Inches(0.32), Inches(1.30), Inches(6.9), Inches(5.0))
rows = [[c, f"{g:.1f}%", f"{zpr1_gm(f):.1f}%"] for c, f, g in CLASSES]
table(s, ["Class", "PR00", "ZPR1 −10%"], rows,
      Inches(7.5), Inches(1.30), Inches(5.4), Inches(5.3),
      col_widths=[Inches(1.6), Inches(1.9), Inches(1.9)], body_size=13)
db.txt(s, "Same 8 class factors, then −10% on the PR00 list. Realized ~40.8% GP vs 44.3% network (CY2024).",
       Inches(7.5), Inches(6.75), Inches(5.4), Inches(0.6), size=11, color=GRAY)

# 5 · CIS
s = db.build_content(prs, "CIS — flat 60% GM, class-independent", eyebrow="CIS · GA Armenia / CBC Kazakhstan", page_no=5)
db.rect(s, Inches(0.32), Inches(1.35), Inches(12.6), Inches(1.5), GRAY_BG)
db.txt(s, "SP = FOB / 0.40   →   60% gross margin", Inches(0.55), Inches(1.55), Inches(12.0), Inches(0.6),
       size=20, bold=True, color=BLACK)
db.txt(s, "Applied to every class. The highest margin in the system.",
       Inches(0.55), Inches(2.15), Inches(12.0), Inches(0.5), size=14, color=GRAY)
db.bullet_list(s, [
    "Recommended: make CIS class-dependent (end the flat 0.40).",
    "Segment by Qingling grey-import overlap: 40–45% GM where a Chinese equivalent exists.",
    "Hold 60% GM where it cannot be followed (Euro 6/7 aftertreatment, electronics, safety).",
    "EAEU customs union — goods landing in Kazakhstan circulate to Armenia duty-free.",
], Inches(0.32), Inches(3.25), Inches(12.5), Inches(2.6), size=14)
db.txt(s, "You cannot beat Qingling on price — protect margin on parts they cannot follow.",
       Inches(0.32), Inches(6.05), Inches(12.5), Inches(0.4), size=13, bold=True, color=RED)

# 6 · Three lists side by side
s = db.build_content(prs, "Three lists, three margin regimes", eyebrow="Summary", page_no=6)
cards = [
    ("PR00 · EU", "Class-implied", ["GM 20% – 56% by class", "P highest (56%), T lowest (20%)", "FY2026 realised +5.3% net"]),
    ("ZPR1 · Israel", "PR00 − 10% flat", ["Same class factors", "UMI 1797 · UTI 1799", "Realised ~40.8% GP"]),
    ("CIS · GA / CBC", "Flat 60% GM", ["Class-independent", "Highest margin in system", "Qingling grey-import at risk"]),
]
cw = Inches(4.05)
for i, (title, sub, pts) in enumerate(cards):
    x = Inches(0.32) + i * (cw + Inches(0.18))
    db.rect(s, x, Inches(1.35), cw, Inches(0.07), RED)
    db.txt(s, title, x + Inches(0.18), Inches(1.55), cw - Inches(0.32), Inches(0.5),
           size=17, bold=True, color=BLACK)
    db.txt(s, sub, x + Inches(0.18), Inches(2.05), cw - Inches(0.32), Inches(0.4),
           size=13, color=GRAY)
    db.bullet_list(s, pts, x + Inches(0.18), Inches(2.55), cw - Inches(0.36), Inches(2.8), size=13)

# 7 · Missing parts in the revision
s = db.build_content(prs, "Parts still missing from the revision", eyebrow="Data gaps", page_no=7)
db.bullet_list(s, [
    "522 PNs billed with no PR00 entry — €4.96M, 15.1% of CY2025 revenue. Outside the reach of any list-price action.",
    "800 PNs billed on superseded numbers — €1.82M. Route to successor, exclude from the delta.",
    "31 Spec C4 PNs still no PR00 in SAP (~€592k) — flagged NO_PR00_IN_SAP, do not re-request.",
    "UMI Shell/lubricants ~€526k parked (business off).",
    "Revision exception queue: 20,572 PN × DB rows flagged leakage / overstock / IAM undercut / high list exposure.",
], Inches(0.32), Inches(1.40), Inches(12.5), Inches(4.6), size=15)
db.txt(s, "These are data fixes, not pricing levers — close them before the alloc run ships.",
       Inches(0.32), Inches(6.05), Inches(12.5), Inches(0.4), size=13, bold=True, color=RED)

# 8 · Closing
db.build_closing(prs)

prs.save(OUT)
cmd = OUT[:-5] + ".cmd"
with open(cmd, "w", encoding="utf-8") as f:
    f.write(f'@echo off\r\nstart "" "%~dp0{os.path.basename(OUT)}"\r\n')
print("wrote", OUT)
print("wrote", cmd)
