# -*- coding: utf-8 -*-
"""
UTI-facing slide: car park (UIO), gross parts billing & GPS % evolution.
Data: gps_billing_clean.json + warranty expense + UIO v19 + FY27 plan (internal workbook).
Refresh wallets: refresh_uti_kosha_wallets.py before rebuild when UIO v19 changes.
No external/source names on the slide face.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent
TEMPLATE_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ppt_template_v2")
sys.path.insert(0, str(TEMPLATE_DIR))

import isze_chart_theme as ct  # noqa: E402

from uti_gps_figures import load_evolution_rows, load_stretch_bundle  # noqa: E402

ct.FONT_FAMILY = "Calibri"
plt.rcParams["font.family"] = ct.FONT_FAMILY

BILLING_JSON = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_billing_clean.json")
WARRANTY_CSV = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\distributor_warranty_expense_fiscal.csv")
UIO_JSON = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\uio_2026.json")
PLAN_XLSX = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\UTI_Presentation"
    r"\All_Material\GPS_PMS_Rate_Models\GPS_PMS_UTI_Kosha_Model.xlsx"
)
CHART_DIR = HERE / "charts_out"
CHART_DIR.mkdir(exist_ok=True)

RED = RGBColor(0xCC, 0x0E, 0x1E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x5A, 0x5A, 0x5A)
LGRAY = RGBColor(0xF0, 0xF0, 0xF0)
SW, SH = Inches(13.33), Inches(7.5)

# Single-line x labels only — never stack two lines (overlap risk).
XLABELS = ["FY24", "FY25", "FY26", "FY27 plan"]


def load_uti_series() -> list[dict]:
    return load_evolution_rows()


def eur_m(v: float) -> float:
    return round(v / 1_000_000, 2)


def build_chart(rows: list[dict], path: Path) -> None:
    labels = [r["xlabel"] for r in rows]
    x = np.arange(len(labels))
    billing_m = [eur_m(r["billing_eur"]) for r in rows]
    uio = [r["uio"] for r in rows]
    gps = [r["gps_net_pct"] for r in rows]

    fig, ax1 = plt.subplots(figsize=(10.2, 4.8), dpi=200)
    fig.patch.set_facecolor(ct.WHITE)
    ax1.set_facecolor(ct.WHITE)

    w = 0.44
    bars = ax1.bar(
        x,
        billing_m,
        width=w,
        color=ct.RED,
        zorder=3,
        label="Parts billing — gross (€M)",
    )
    ax1.set_ylabel("Gross parts billing (€M)", fontsize=10, color=ct.CHARCOAL)
    ax1.set_ylim(0, max(billing_m) * 1.28)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=11, color=ct.CHARCOAL)
    ax1.tick_params(axis="x", pad=8)

    for i, (bar, val) in enumerate(zip(bars, billing_m)):
        if rows[i].get("is_plan"):
            ax1.annotate(
                f"€{val:.2f}M",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(-22, 6),
                textcoords="offset points",
                ha="right",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color=ct.CHARCOAL,
            )
            continue
        ax1.annotate(
            f"€{val:.2f}M",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=ct.CHARCOAL,
        )

    # UIO — right axis 1
    ax_uio = ax1.twinx()
    ax_uio.plot(x, uio, color=ct.CHARCOAL, marker="o", linewidth=2.2, markersize=7, label="Car park (units)", zorder=4)
    uio_lo = min(uio) * 0.92
    uio_hi = max(uio) * 1.06
    ax_uio.set_ylim(uio_lo, uio_hi)
    ax_uio.set_ylabel("Active parc (units)", fontsize=10, color=ct.CHARCOAL)
    ax_uio.tick_params(axis="y", labelsize=9, colors=ct.CHARCOAL)

    for i, (xi, u) in enumerate(zip(x, uio)):
        if rows[i].get("is_plan"):
            ax_uio.annotate(
                f"{u:,}",
                (xi, u),
                xytext=(20, 10),
                textcoords="offset points",
                ha="left",
                va="bottom",
                fontsize=8.5,
                color=ct.CHARCOAL,
            )
            continue
        ax_uio.annotate(
            f"{u:,}",
            (xi, u),
            xytext=(0, 11),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=ct.CHARCOAL,
        )

    # GPS % — right axis 2 (offset spine so scales don't clash)
    ax_gps = ax1.twinx()
    ax_gps.spines["right"].set_position(("outward", 58))
    ax_gps.plot(
        x,
        gps,
        color=ct.GRAY_MED,
        marker="s",
        linewidth=2.0,
        markersize=6,
        linestyle="--",
        label="GPS % (net of warranty)",
        zorder=4,
    )
    gps_lo = max(0, min(gps) - 8)
    gps_hi = max(gps) + 8
    ax_gps.set_ylim(gps_lo, gps_hi)
    ax_gps.set_ylabel("GPS % (net of warranty)", fontsize=10, color=ct.GRAY_MED)
    ax_gps.tick_params(axis="y", labelsize=9, colors=ct.GRAY_MED)

    for i, (xi, g) in enumerate(zip(x, gps)):
        yoff = -16
        if rows[i].get("is_plan"):
            yoff = -22
        ax_gps.annotate(
            f"{g:.1f}%",
            (xi, g),
            xytext=(0, yoff),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=8.5,
            color=ct.GRAY,
        )

    for spine in ("top",):
        ax1.spines[spine].set_visible(False)
    ax_uio.spines["top"].set_visible(False)
    ax_gps.spines["top"].set_visible(False)
    ax1.spines["left"].set_color(ct.GRAY_LIGHT)
    ax1.spines["bottom"].set_color(ct.GRAY_LIGHT)
    ax1.tick_params(axis="y", colors=ct.GRAY, labelsize=9)
    ax1.yaxis.grid(True, color=ct.GRAY_BG, linewidth=1.0, zorder=0)
    ax1.set_axisbelow(True)

    lines1, lab1 = ax1.get_legend_handles_labels()
    lines2, lab2 = ax_uio.get_legend_handles_labels()
    lines3, lab3 = ax_gps.get_legend_handles_labels()
    fig.legend(
        lines1 + lines2 + lines3,
        lab1 + lab2 + lab3,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=3,
        frameon=False,
        fontsize=8.5,
    )

    fig.text(
        0.5,
        0.01,
        "Bars = ISZE parts billing (transport & rebates excluded).  "
        "GPS % = (billing − warranty) ÷ max-spend wallet.  "
        "FY24–FY26 = complete ISZE fiscal years (Apr–Mar).",
        ha="center",
        fontsize=8.5,
        color=ct.GRAY,
    )

    fig.subplots_adjust(bottom=0.14, top=0.88, right=0.88)
    fig.savefig(path, bbox_inches="tight", facecolor=ct.WHITE, pad_inches=0.08)
    plt.close(fig)


def txt(s, t, l, top, w, h, size=14, bold=False, color=BLACK, align=PP_ALIGN.LEFT, italic=False, font="Calibri"):
    b = s.shapes.add_textbox(l, top, w, h)
    tf = b.text_frame
    tf.word_wrap = True
    for i, ln in enumerate(t.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        r.font.name = font


def scell(c, t, size=11, bold=False, color=BLACK, fill=WHITE, align=PP_ALIGN.CENTER):
    c.margin_top = Pt(2)
    c.margin_bottom = Pt(2)
    c.margin_left = Pt(5)
    c.margin_right = Pt(5)
    c.vertical_anchor = MSO_ANCHOR.MIDDLE
    c.fill.solid()
    c.fill.fore_color.rgb = fill
    tf = c.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = t
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = "Calibri"


def add_slide(prs: Presentation, rows: list[dict], chart_path: Path) -> None:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    f = s.background.fill
    f.solid()
    f.fore_color.rgb = WHITE

    txt(s, "ISUZU", Inches(0.28), Inches(6.80), Inches(2), Inches(0.55), size=18, bold=True, color=RED, font="Arial Black")
    bar = s.shapes.add_shape(1, 0, SH - Inches(0.13), SW, Inches(0.13))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RED
    bar.line.fill.background()

    txt(s, "UTI — car park, parts sales & GPS", Inches(0.28), Inches(0.28), Inches(12.5), Inches(0.6), size=28, bold=True)
    txt(
        s,
        "ISZE fiscal year  ·  gross billing (bars)  ·  GPS % net of warranty  ·  UIO v19",
        Inches(0.28),
        Inches(0.9),
        Inches(12.5),
        Inches(0.32),
        size=10,
        color=GRAY,
    )
    line = s.shapes.add_shape(1, Inches(0.28), Inches(1.18), Inches(12.77), Emu(38100))
    line.fill.solid()
    line.fill.fore_color.rgb = RED
    line.line.fill.background()

    s.shapes.add_picture(str(chart_path), Inches(0.42), Inches(1.25), width=Inches(8.45))

    tbl_rows = [["FY", "Car park", "Gross billing", "GPS %\n(net)"]]
    for r in rows:
        tbl_rows.append(
            [
                r["xlabel"],
                f"{r['uio']:,}",
                f"€{eur_m(r['billing_eur']):.2f}M",
                f"{r['gps_net_pct']:.1f}%",
            ]
        )

    gt = s.shapes.add_table(len(tbl_rows), 4, Inches(9.05), Inches(1.42), Inches(3.95), Inches(0.34 * len(tbl_rows))).table
    for j, cw in enumerate([Inches(1.05), Inches(0.95), Inches(1.05), Inches(0.9)]):
        gt.columns[j].width = cw
    for i, row in enumerate(tbl_rows):
        for j, val in enumerate(row):
            scell(
                gt.cell(i, j),
                val,
                size=10 if i else 9,
                bold=(i == 0),
                color=WHITE if i == 0 else BLACK,
                fill=RED if i == 0 else (LGRAY if i % 2 == 0 else WHITE),
                align=PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER,
            )

    box = s.shapes.add_shape(1, Inches(9.05), Inches(4.0), Inches(3.95), Inches(2.4))
    box.fill.solid()
    box.fill.fore_color.rgb = LGRAY
    box.line.fill.background()
    txt(s, "TAKEAWAYS", Inches(9.2), Inches(4.07), Inches(3.5), Inches(0.25), size=9, bold=True, color=RED)

    stretch = load_stretch_bundle()
    r25, r26, r27 = rows[1], rows[2], rows[3]
    bullets = [
        f"Active parc {r26['uio']:,} units in FY26 — max-spend wallet €{eur_m(r26['max_spend_eur']):.1f}M.",
        f"GPS % fell to {r25['gps_net_pct']:.1f}% in FY25 (higher warranty volume); recovered to {r26['gps_net_pct']:.1f}% in FY26.",
        f"FY27 Kosha base {r27['gps_net_pct']:.1f}% GPS — stretch proposal targets {stretch['gps_stretch']:.1f}%.",
        "FY24–FY26 are complete fiscal years — safe for like-for-like trend.",
    ]
    txt(s, "\n".join(f"—  {b}" for b in bullets), Inches(9.2), Inches(4.32), Inches(3.7), Inches(2.0), size=9.5)

    ns = s.notes_slide.notes_text_frame
    ns.clear()
    ns.text = (
        "UTI GPS EVOLUTION (3 min) — INTERNAL NOTES\n\n"
        "VISIBLE DEFINITIONS (say if asked):\n"
        "• Bars = ISZE parts billing only (transport, rebates & credit notes excluded; urgency surcharges normalised).\n"
        "• GPS % = NET of warranty: (billing − warranty expense) ÷ max-spend wallet.\n"
        "• FY26 is a complete fiscal year (Apr 25 – Mar 26).\n"
        "• FY24–FY25 are also complete fiscal years (Israel billing from Jan 2023).\n"
        "• FY27 column = reviewed plan target, not actuals.\n\n"
        "Do not mention internal workbook or planning tool names in the room.\n\n"
        f"FY25 warranty €{r25['warranty_eur']:,.0f} depressed net GPS — Q4 spike worth noting if challenged.\n"
        "Bridge to GPS stretch slide: Kosha base {0:.1f}% → commercial plan {1:.1f}% → stretch {2:.1f}%.".format(
            r27["gps_net_pct"], stretch["gps_plan"], stretch["gps_stretch"]
        )
    )


def main() -> None:
    rows = load_uti_series()
    chart_path = CHART_DIR / "uti_gps_evolution.png"
    build_chart(rows, chart_path)

    prs = Presentation()
    prs.slide_width = SW
    prs.slide_height = SH
    add_slide(prs, rows, chart_path)

    outputs = [
        OUT_DIR / "UTI_GPS_Evolution_Slide.pptx",
        Path(r"c:\Users\jerom\Downloads\UTI_GPS_Evolution_Slide.pptx"),
    ]
    for out in outputs:
        try:
            prs.save(str(out))
            print("saved", out)
        except PermissionError:
            alt = out.with_name(out.stem + "_NEW.pptx")
            prs.save(str(alt))
            print("LOCKED - saved", alt)

    print("\nData:")
    for r in rows:
        plan = " [plan]" if r["is_plan"] else ""
        print(
            f"  {r['xlabel']:12s}{plan}  UIO {r['uio']:>6,}  "
            f"gross €{r['billing_eur']:>12,.0f}  warr €{r['warranty_eur']:>9,.0f}  "
            f"GPS(net) {r['gps_net_pct']:5.1f}%"
        )


if __name__ == "__main__":
    main()
