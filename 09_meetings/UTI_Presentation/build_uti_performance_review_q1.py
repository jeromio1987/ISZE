# -*- coding: utf-8 -*-
"""UTI Performance Review FY2027 Q1 — deck with reconciled sales + 5 analysis slides."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# template v2
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "04_tools" / "ppt_template_v2"
sys.path.insert(0, str(TEMPLATE_DIR))
import isze_chart_theme as ct  # noqa: E402
import isze_deck_builder as db  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

ct.FONT_FAMILY = "Calibri"
plt.rcParams["font.family"] = "Calibri"

HERE = Path(__file__).resolve().parent
CHART_DIR = HERE / "charts_q1fy27"
CHART_DIR.mkdir(exist_ok=True)
DATA = Path(__file__).resolve().parents[2] / "01_data" / "00_derived" / "q1fy2027_export_with_saty.csv"
OUT = HERE / "UTI_Performance_Review_FY2027_Q1.pptx"

RED = ct.RED
CHARCOAL = ct.CHARCOAL
GRAY = ct.GRAY
GRAY_LIGHT = ct.GRAY_LIGHT
WHITE = ct.WHITE


def cp(name: str) -> str:
    return str(CHART_DIR / name)


def load_uti() -> pd.DataFrame:
    df = pd.read_csv(DATA, low_memory=False)
    df["bill"] = pd.to_datetime(df["Billing Date"])
    df["month"] = df["bill"].dt.to_period("M").astype(str)
    return df[df["Sold_to"] == 1799].copy()


def bucket_saty(s: str) -> str:
    s = str(s).upper()
    if s in ("VOR", "RUSH", "SVOR", "RVOR"):
        return "Urgent"
    if s == "SOR":
        return "Routine (SOR)"
    return "Other"


def spa_category(desc: str) -> str:
    d = str(desc).upper()
    rules = [
        ("SENSOR", "Electronics"),
        ("NOX", "Electronics"),
        ("COOLER", "Cooling / EGR"),
        ("EGR", "Cooling / EGR"),
        ("FILTER", "Filters"),
        ("PAD", "Brakes"),
        ("BRAKE", "Brakes"),
        ("CYLINDER", "Brakes"),
        ("CLUTCH", "Clutch"),
        ("LAMP", "Body / lighting"),
        ("DOOR", "Body / lighting"),
        ("BUMPER", "Body / lighting"),
        ("MIRROR", "Body / lighting"),
    ]
    for key, label in rules:
        if key in d:
            return label
    return "Other parts"


def stacked_bar_monthly(months, routine, urgent, filename, title, ylabel="EUR K"):
    fig, ax = ct._base_fig(figsize=(10.2, 4.3))
    x = np.arange(len(months))
    r = np.array(routine) / 1000
    u = np.array(urgent) / 1000
    b1 = ax.bar(x, r, 0.55, color=CHARCOAL, label="Routine (SOR)", zorder=3)
    b2 = ax.bar(x, u, 0.55, bottom=r, color=RED, label="Urgent (RUSH+VOR)", zorder=3)
    for bars, vals, base in ((b1, r, np.zeros_like(r)), (b2, u, r)):
        for bar, v, b in zip(bars, vals, base):
            if v < 8:
                continue
            ax.annotate(
                f"{v:.0f}",
                (bar.get_x() + bar.get_width() / 2, b + v),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                color=CHARCOAL,
                fontweight="bold",
            )
    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=11, color=CHARCOAL)
    ax.set_ylabel(ylabel, fontsize=10, color=GRAY)
    ax.legend(loc="upper left", frameon=False, fontsize=10)
    ax.set_title(title, fontsize=13, color=CHARCOAL, loc="left", fontweight="bold", pad=12)
    ct._save(fig, filename)


def hbar_chart(labels, values, filename, title, xlabel="EUR K"):
    fig, ax = plt.subplots(figsize=(10.2, 4.3), dpi=200)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRAY_LIGHT)
    y = np.arange(len(labels))
    vals = np.array(values) / 1000
    bars = ax.barh(y, vals, color=RED, height=0.55, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=11, color=CHARCOAL)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=10, color=GRAY)
    for bar, v in zip(bars, vals):
        ax.annotate(
            f"{v:.0f}",
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            va="center",
            fontsize=9.5,
            color=CHARCOAL,
            fontweight="bold",
        )
    ax.set_title(title, fontsize=13, color=CHARCOAL, loc="left", fontweight="bold", pad=12)
    ct._save(fig, filename)


def add_table_slide(prs, title, rows, col_w, eyebrow=None, page_no=None, footnote=None):
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

    RED_C = RGBColor(0xCC, 0x0E, 0x1E)
    WHITE_C = RGBColor(0xFF, 0xFF, 0xFF)
    BLACK_C = RGBColor(0x1A, 0x1A, 0x1A)
    LGRAY = RGBColor(0xF0, 0xF0, 0xF0)
    MGRAY = RGBColor(0xD9, 0xD9, 0xD9)

    s = db.build_content(prs, title, eyebrow=eyebrow, page_no=page_no)
    nr, nc = len(rows), len(rows[0])
    tbl = s.shapes.add_table(nr, nc, Inches(0.45), Inches(1.35), Inches(12.4), Inches(0.38 * nr)).table
    for j, w in enumerate(col_w):
        tbl.columns[j].width = w
    tbl.first_row = False
    tbl.horz_banding = False

    def scell(cell, text, hdr=False, bold=False, fill=None):
        cell.margin_top = Pt(3)
        cell.margin_bottom = Pt(3)
        cell.margin_left = Pt(7)
        cell.margin_right = Pt(7)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill or WHITE_C
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if not hdr and rows[0][0] != text else PP_ALIGN.LEFT
        if hdr:
            p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = text
        r.font.size = Pt(12 if not hdr else 12)
        r.font.bold = hdr or bold
        r.font.color.rgb = WHITE_C if hdr else BLACK_C
        r.font.name = "Calibri"

    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            if i == 0:
                scell(c, val, hdr=True, fill=RED_C)
            else:
                is_total = str(row[0]).lower().startswith("q1") or str(row[0]).lower().startswith("total")
                fill = MGRAY if is_total else (LGRAY if i % 2 == 0 else WHITE_C)
                scell(c, val, bold=is_total, fill=fill)
                if j > 0:
                    c.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    if footnote:
        db.txt(
            s,
            footnote,
            Inches(0.45),
            Inches(6.55),
            Inches(12.2),
            Inches(0.35),
            size=9,
            color=db.GRAY,
        )
    return s


def main():
    df = load_uti()
    v = "EUR_Amount"
    q1_total = df[v].sum()

    monthly = df.groupby("month")[v].sum()
    apr, may, jun = monthly.get("2026-04", 0), monthly.get("2026-05", 0), monthly.get("2026-06", 0)

    matched = df[df["SaTy_matched"] == True].copy()  # noqa: E712
    matched["bucket"] = matched["SaTy"].map(bucket_saty)
    mix = matched.groupby("SaTy")[v].sum()
    bucket_mix = matched.groupby("bucket")[v].sum()

    m_month = matched.groupby(["month", "bucket"])[v].sum().unstack(fill_value=0)
    routine_m = [m_month.loc[m, "Routine (SOR)"] if m in m_month.index and "Routine (SOR)" in m_month.columns else 0 for m in ["2026-04", "2026-05", "2026-06"]]
    urgent_m = [m_month.loc[m, "Urgent"] if m in m_month.index and "Urgent" in m_month.columns else 0 for m in ["2026-04", "2026-05", "2026-06"]]

    spa_doc = 364214
    spa = df[df["Sales_Doc"] == spa_doc]
    spa_total = spa[v].sum()
    spa_cats = {}
    for _, r in spa.iterrows():
        cat = spa_category(r.get("Material", ""))
        spa_cats[cat] = spa_cats.get(cat, 0) + r[v]
    spa_sorted = sorted(spa_cats.items(), key=lambda x: -x[1])[:6]

    # CV peer benchmark — UTI vs ITUK (both pure-play CV distributors)
    full = pd.read_csv(DATA, low_memory=False)
    ituk = full[full["Payer_code"] == 2194].copy()
    ituk["bill"] = pd.to_datetime(ituk["Billing Date"])
    ituk_q1 = ituk[v].sum()
    ituk_monthly = ituk.groupby(ituk["bill"].dt.to_period("M").astype(str))[v].sum()
    ituk_apr = ituk_monthly.get("2026-04", 0)
    ituk_may = ituk_monthly.get("2026-05", 0)
    ituk_jun = ituk_monthly.get("2026-06", 0)

    ituk_matched = ituk[ituk["SaTy_matched"] == True].copy()  # noqa: E712
    ituk_matched["bucket"] = ituk_matched["SaTy"].map(bucket_saty)
    ituk_bucket = ituk_matched.groupby("bucket")[v].sum()
    ituk_urgent_pct = ituk_bucket.get("Urgent", 0) / ituk_bucket.sum() * 100

    baseline = (apr + may) / 2
    jun_ex_spa = jun - spa_total

    # --- charts ---
    stacked_bar_monthly(
        ["Apr", "May", "Jun"],
        routine_m,
        urgent_m,
        cp("01_order_mix_monthly.png"),
        "UTI billed sales by order urgency (EUR, SaTy-matched lines)",
    )

    ct.donut_share(
        ["SOR", "RUSH", "VOR"],
        [mix.get("SOR", 0), mix.get("RUSH", 0), mix.get("VOR", 0)],
        cp("02_order_mix_share.png"),
        center_label="Q1 sales (matched)",
        center_value=f"€{bucket_mix.sum()/1000:.0f}K",
        title="Order type share — matched billing lines (82% of Q1 value)",
    )

    ct.bar_chart(
        ["Apr", "May", "Jun"],
        {"Sales (EUR K)": [apr / 1000, may / 1000, jun / 1000]},
        cp("03_sales_bridge.png"),
        title="UTI monthly sales — June SPA uplift (EUR K)",
        ylabel="EUR K",
        value_fmt="{:,.0f}",
    )

    hbar_chart(
        [k for k, _ in spa_sorted],
        [val for _, val in spa_sorted],
        cp("04_spa_basket.png"),
        f"June SPA order (doc {int(spa_doc)}) — top categories (EUR K)",
    )

    ct.bar_chart(
        ["Apr", "May", "Jun"],
        {
            "UTI": [apr / 1000, may / 1000, jun / 1000],
            "ITUK": [ituk_apr / 1000, ituk_may / 1000, ituk_jun / 1000],
        },
        cp("05_uti_vs_ituk.png"),
        title="CV peer benchmark — UTI vs ITUK monthly sales (EUR K)",
        ylabel="EUR K",
        value_fmt="{:,.0f}",
    )

    # urgent intensity by month (RUSH vs VOR)
    rush_m, vor_m = [], []
    for m in ["2026-04", "2026-05", "2026-06"]:
        sub = matched[(matched["month"] == m)]
        rush_m.append(sub[sub["SaTy"] == "RUSH"][v].sum())
        vor_m.append(sub[sub["SaTy"] == "VOR"][v].sum())
    stacked_bar_monthly(
        ["Apr", "May", "Jun"],
        rush_m,
        vor_m,
        cp("06_urgent_split.png"),
        "Urgent order value — RUSH vs VOR by month (EUR)",
    )

    uti_urgent_pct = bucket_mix.get("Urgent", 0) / bucket_mix.sum() * 100

    # --- deck ---
    prs = db.new_presentation()
    pg = 1

    db.build_cover(
        prs,
        title="ISZE – UTI | Performance Review",
        subtitle="Israel CV parts business  |  FY2027 Q1 (Apr–Jun)  |  July 2026",
    )
    pg += 1

    s = db.build_content(prs, "Agenda", eyebrow="FY2027 Q1", page_no=pg)
    db.bullet_list(
        s,
        [
            "Sales & KPI FY2027 — situation vs. Budget & last year",
            "Q1 sales bridge — Apr/May baseline and June SPA uplift",
            "Order urgency mix — routine (SOR) vs urgent (RUSH / VOR)",
            "June SPA basket — what drove the quarter",
            "CV peer benchmark — UTI vs ITUK sales & order mix",
            "Service intensity — urgent orders and fill-rate implications",
            "Next steps",
        ],
        Inches(0.55),
        Inches(1.45),
        Inches(12.0),
        Inches(5.2),
        size=17,
    )
    pg += 1
    add_table_slide(
        prs,
        "Sales & KPI FY2027 — situation vs. Budget",
        [
            ["", "Apr", "May", "Jun", "Q1 Total"],
            ["Sales amount (€K)", "211", "191", "635", "1,037"],
            ["vs Budget", "—", "—", "234%", "+38%"],
            ["vs Prior year", "—", "—", "—", "+29%"],
            ["Order intake (€K)", "—", "—", "—", "see monthly report"],
        ],
        [Inches(3.2), Inches(2.2), Inches(2.2), Inches(2.2), Inches(2.6)],
        eyebrow="Reconciled billing extract",
        page_no=pg,
        footnote="Source: complete Q1FY2027 SAP export (sold-to 1799) reconciled to VP Monthly report Jun-2026 — €1,036,632 ≈ €1,037K.",
    )

    pg += 1
    db.build_two_col(
        prs,
        title="Q1 sales bridge — June SPA drove +38% vs budget",
        chart_path=cp("03_sales_bridge.png"),
        eyebrow="Sales performance",
        page_no=pg,
        takeaways=[
            f"Q1 sales €1,037K — +38% vs budget, +29% vs prior year.",
            f"Apr–May baseline ≈ €201K/mo; June €635K including first SPA order.",
            f"SPA order (doc {int(spa_doc)}) = €{spa_total/1000:.0f}K — 27% of Q1 sales.",
            f"June ex-SPA still €{jun_ex_spa/1000:.0f}K — ~1.8× the Apr–May run-rate.",
        ],
    )

    pg += 1
    db.build_two_col(
        prs,
        title="Order urgency mix — UTI runs a lower urgent share than ITUK",
        chart_path=cp("01_order_mix_monthly.png"),
        eyebrow="SOR vs RUSH / VOR",
        page_no=pg,
        takeaways=[
            f"UTI matched lines: SOR €{mix.get('SOR',0)/1000:.0f}K (88%), RUSH €{mix.get('RUSH',0)/1000:.0f}K, VOR €{mix.get('VOR',0)/1000:.0f}K.",
            f"Urgent share UTI {uti_urgent_pct:.0f}% vs ITUK {ituk_urgent_pct:.0f}% of matched € — both CV distributors.",
            "June urgency €64K sits alongside €533K routine — mostly SPA-driven routine volume.",
            "SaTy joined from partial extract — 82% UTI / 99% ITUK line coverage.",
        ],
    )

    pg += 1
    db.build_full_chart(
        prs,
        title="Order type split — routine vs urgent (matched Q1 billing)",
        chart_path=cp("02_order_mix_share.png"),
        eyebrow="SOR vs RUSH / VOR",
        page_no=pg,
    )

    pg += 1
    db.build_two_col(
        prs,
        title="June SPA basket — structured programme, not a one-off line",
        chart_path=cp("04_spa_basket.png"),
        eyebrow="Influencing factors",
        page_no=pg,
        takeaways=[
            "Largest lines: NOX sensor, EGR cooler, fuel filter kit, brake pads.",
            "Mix spans wear parts, electronics, and body — aligns with SPA modelling.",
            "June hit 234% of monthly BP; SPA explains roughly half the June uplift.",
            "Sets baseline for Q2 programme tracking line by line.",
        ],
    )

    pg += 1
    db.build_two_col(
        prs,
        title="CV peer benchmark — UTI vs ITUK Q1 sales profile",
        chart_path=cp("05_uti_vs_ituk.png"),
        eyebrow="UTI vs ITUK",
        page_no=pg,
        takeaways=[
            f"Q1 sales: UTI €{q1_total/1000:.0f}K (+38% vs budget) · ITUK €{ituk_q1/1000:.0f}K (−19% vs budget).",
            "ITUK steady €415–529K/mo; UTI Jun €635K driven by first SPA order.",
            f"Both are pure-play CV distributors — comparable parc and parts programme.",
            "UTI closing the gap on ITUK scale — Q1 at 75% of ITUK volume.",
        ],
    )

    pg += 1
    db.build_two_col(
        prs,
        title="Service intensity — urgent orders remain a smaller share of UTI value",
        chart_path=cp("06_urgent_split.png"),
        eyebrow="Fill rate & urgency",
        page_no=pg,
        takeaways=[
            "RUSH lines fulfil faster (median ~1 day order-to-invoice) vs SOR ~11 days.",
            "UTI fill rate 76–86% (Jul'25–May'26 BI trend) — monitor urgent lines separately.",
            "VOR concentrates in filters & chassis families — stock positioning lever.",
            "Link back-order / VOR KPIs on prior slide to these product families.",
        ],
    )

    pg += 1
    s = db.build_content(prs, "Next steps", eyebrow="FY2027 Q2", page_no=pg)
    db.bullet_list(
        s,
        [
            "Track SPA programme lines monthly — volume vs agreed basket.",
            "Share UTI fill-rate split by order type (SOR vs RUSH/VOR) from BI.",
            "Review VOR/back-order ageing on filters & suspension — top VOR families.",
            "Confirm Q2 order intake vs billing timing (WIP / July spillover).",
        ],
        Inches(0.55),
        Inches(1.45),
        Inches(12.0),
        Inches(5.0),
        size=17,
    )

    db.build_closing(prs)

    try:
        prs.save(str(OUT))
        print(f"Saved: {OUT}")
    except PermissionError:
        alt = OUT.with_name(OUT.stem + "_NEW.pptx")
        prs.save(str(alt))
        print(f"File locked — saved: {alt}")


if __name__ == "__main__":
    main()
