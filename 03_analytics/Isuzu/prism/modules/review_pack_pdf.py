"""ReportLab PDF builder for ISZE Distributor Review Pack."""

from __future__ import annotations

import math
from datetime import date
from io import BytesIO
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# Re-import helpers from scorecard_pdf where they are module-level
from modules.scorecard_pdf import (
    _fig_to_image,
    _fmt_eur,
    _fmt_pct,
    _section_heading,
    _build_styles,
    _table_style_base,
    _not_available,
    _build_network_position,
    _build_capture_trajectory,
    _build_capture_recovery,
    ISZE_BLUE,
    ISZE_ORANGE,
    ISZE_LIGHT,
    ROW_ALT,
    RED,
    GRAY,
    WHITE,
    PAGE_W,
    PAGE_H,
    MARGIN,
    CONTENT_W,
    _METRIC_LABEL_MAP,
    _METRIC_ORDER,
)

# ---------------------------------------------------------------------------
# Local helpers (supplement scorecard_pdf helpers)
# ---------------------------------------------------------------------------

def _trend_arrow(latest, prior) -> tuple[str, str]:
    """Return (arrow_char, color_hex) comparing latest vs prior value."""
    try:
        diff = float(latest) - float(prior)
    except (TypeError, ValueError):
        return "→", "#888888"
    if abs(diff) < 0.01:
        return "→", "#888888"
    return ("↑", "#2E7D32") if diff > 0 else ("↓", "#C62828")


def _safe_float(v) -> Optional[float]:
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Section 1 — Cover
# ---------------------------------------------------------------------------

def _build_review_cover(
    dist_code: str,
    country: str,
    region: str,
    years: list[int],
    styles,
) -> list:
    elements: list = []

    banner_data = [[Paragraph("DISTRIBUTOR REVIEW PACK", styles["cover_title"])]]
    banner = Table(banner_data, colWidths=[CONTENT_W])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ISZE_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    elements.append(banner)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph(dist_code, styles["cover_code"]))
    elements.append(Spacer(1, 6))

    loc = f"{country} · {region}" if country and region else (country or region or "")
    if loc:
        elements.append(Paragraph(loc, styles["cover_sub"]))
        elements.append(Spacer(1, 4))

    years_str = f"{years[0]}–{years[-1]}" if len(years) > 1 else str(years[0])
    elements.append(Paragraph(
        f"Coverage: {years_str} &nbsp;&nbsp;|&nbsp;&nbsp; Generated: {date.today().strftime('%d %b %Y')}",
        styles["cover_meta"],
    ))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("CONFIDENTIAL — ISZE Internal Use Only", styles["footer"]))
    elements.append(Spacer(1, 24))
    elements.append(PageBreak())
    return elements


# ---------------------------------------------------------------------------
# Section 2 — 3-Year KPI Trend
# ---------------------------------------------------------------------------

def _kpi_trend_chart(
    kpi_rows: list[dict],  # [{year, gps_spu, total_capture}]
) -> Optional[BytesIO]:
    """Dual-axis line chart: GPS/SPU (left) + total PMS capture % (right)."""
    if not kpi_rows:
        return None

    df = pd.DataFrame(kpi_rows).sort_values("year")
    valid_spu = df["gps_spu"].dropna()
    valid_cap = df["total_capture"].dropna()
    if valid_spu.empty and valid_cap.empty:
        return None

    fig, ax1 = plt.subplots(figsize=(7, 3.2))
    ax2 = ax1.twinx()

    years_list = df["year"].tolist()

    if not valid_spu.empty:
        ax1.plot(
            df["year"], df["gps_spu"],
            color="#1B3A6B", linewidth=2, marker="o", markersize=5, label="GPS/SPU (€)",
        )
        ax1.set_ylabel("GPS/SPU (€)", fontsize=8, color="#1B3A6B")
        ax1.tick_params(axis="y", labelcolor="#1B3A6B", labelsize=7)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"€{x:,.0f}"))

    if not valid_cap.empty:
        ax2.plot(
            df["year"], df["total_capture"] * 100,
            color="#E87722", linewidth=2, marker="s", markersize=5, linestyle="--",
            label="Total PMS capture %",
        )
        ax2.set_ylabel("PMS capture %", fontsize=8, color="#E87722")
        ax2.tick_params(axis="y", labelcolor="#E87722", labelsize=7)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))

    ax1.set_xlabel("Year", fontsize=8)
    ax1.tick_params(axis="x", labelsize=7)
    ax1.set_xticks(years_list)
    ax1.set_facecolor("#FAFBFC")
    fig.patch.set_facecolor("white")
    ax1.spines["top"].set_visible(False)
    ax1.grid(axis="y", color="#E0E0E0", linewidth=0.5)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="best", framealpha=0.8)

    fig.tight_layout(pad=0.4)
    return _fig_to_image(fig)


def _build_kpi_trend(
    dist_code: str,
    gps_db: pd.DataFrame,
    network_percentile: pd.DataFrame,
    aim_db: pd.DataFrame,
    years: list[int],
    styles,
) -> list:
    elements: list = []
    years_str = f"{years[0]}–{years[-1]}" if len(years) > 1 else str(years[0])
    elements += _section_heading(f"Performance Trend — {years_str}", styles)

    kpi_rows = []
    table_rows = [["Year", "GPS/SPU (€)", "Total PMS capture", "Genuine capture",
                   "High-risk rev %", "Net sales (€)", "Trend"]]

    prev_spu = None
    for yr in sorted(years):
        row: dict = {"year": yr, "gps_spu": None, "total_capture": None}

        # GPS/SPU
        if not gps_db.empty:
            g = gps_db[(gps_db["distributor_code"] == dist_code) & (gps_db["year"] == yr)]
            if not g.empty:
                row["gps_spu"] = _safe_float(g.iloc[0].get("spend_per_unit_eur"))

        # PMS metrics from network_percentile
        tot_cap = gen_cap = None
        if not network_percentile.empty:
            np_sub = network_percentile[
                (network_percentile["distributor_code"] == dist_code)
                & (network_percentile["year"] == yr)
            ]
            tot_row = np_sub[np_sub["metric"] == "total_capture"]
            if not tot_row.empty:
                tot_cap = _safe_float(tot_row.iloc[0].get("raw_value"))
                row["total_capture"] = tot_cap
            gen_row = np_sub[np_sub["metric"] == "genuine_capture"]
            if not gen_row.empty:
                gen_cap = _safe_float(gen_row.iloc[0].get("raw_value"))

        # AIM
        hr_pct = net_sales = None
        if not aim_db.empty:
            a = aim_db[(aim_db["distributor_code"] == dist_code) & (aim_db["year"] == yr)]
            if not a.empty:
                hr_pct = _safe_float(a.iloc[0].get("high_risk_rev_pct"))
                net_sales = _safe_float(a.iloc[0].get("net_sales_eur"))

        # Trend arrow vs previous year GPS/SPU
        if prev_spu is not None and row["gps_spu"] is not None:
            arrow, _ = _trend_arrow(row["gps_spu"], prev_spu)
        else:
            arrow = "—"
        prev_spu = row["gps_spu"]

        kpi_rows.append(row)
        table_rows.append([
            str(yr),
            _fmt_eur(row["gps_spu"]),
            _fmt_pct(tot_cap),
            _fmt_pct(gen_cap),
            _fmt_pct(hr_pct),
            _fmt_eur(net_sales),
            arrow,
        ])

    col_w = [CONTENT_W * x for x in [0.10, 0.16, 0.16, 0.16, 0.14, 0.16, 0.12]]
    tbl = Table(table_rows, colWidths=col_w)
    style = _table_style_base(len(table_rows))

    # Colour trend arrow column
    for ri, row_data in enumerate(table_rows[1:], start=1):
        arrow = row_data[6]
        if arrow == "↑":
            style.add("TEXTCOLOR", (6, ri), (6, ri), colors.HexColor("#2E7D32"))
        elif arrow == "↓":
            style.add("TEXTCOLOR", (6, ri), (6, ri), RED)
        else:
            style.add("TEXTCOLOR", (6, ri), (6, ri), GRAY)
        style.add("FONTNAME", (6, ri), (6, ri), "Helvetica-Bold")

    tbl.setStyle(style)
    elements.append(tbl)
    elements.append(Spacer(1, 12))

    # Line chart
    chart_buf = _kpi_trend_chart(kpi_rows)
    if chart_buf:
        img = Image(chart_buf, width=CONTENT_W, height=CONTENT_W * 0.42)
        elements.append(img)
        elements.append(Spacer(1, 12))

    return elements


# ---------------------------------------------------------------------------
# Section 4 — AIM Exposure
# ---------------------------------------------------------------------------

def _build_aim_exposure(
    dist_code: str,
    aim_db: pd.DataFrame,
    aim_family: pd.DataFrame,
    latest_year: int,
    styles,
) -> list:
    elements: list = []
    elements += _section_heading("AIM Risk Exposure", styles)

    if aim_db.empty:
        elements.append(_not_available(styles))
        return elements

    db_row = aim_db[
        (aim_db["distributor_code"] == dist_code) & (aim_db["year"] == latest_year)
    ]

    if db_row.empty:
        elements.append(_not_available(styles))
        return elements

    r = db_row.iloc[0]
    match_rate = _safe_float(r.get("aim_match_rate_rev"))
    hr_rev = _safe_float(r.get("high_risk_rev_eur"))
    hr_pct = _safe_float(r.get("high_risk_rev_pct"))

    # Summary metrics row (3 columns)
    metric_data = [[
        Paragraph(f"<b>Match rate</b><br/>{_fmt_pct(match_rate)}", styles["body"]),
        Paragraph(f"<b>High-risk revenue</b><br/>{_fmt_eur(hr_rev)}", styles["body"]),
        Paragraph(f"<b>High-risk % of sales</b><br/>{_fmt_pct(hr_pct)}", styles["body"]),
    ]]
    col_w3 = [CONTENT_W / 3] * 3
    metric_tbl = Table(metric_data, colWidths=col_w3)
    metric_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D0D0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D0D0")),
        ("BACKGROUND", (0, 0), (-1, -1), ISZE_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(metric_tbl)
    elements.append(Spacer(1, 10))

    # Top 5 product families
    if not aim_family.empty:
        fam_df = aim_family[
            (aim_family["distributor_code"] == dist_code)
            & (aim_family["year"] == latest_year)
        ].copy()

        if not fam_df.empty and "aim_high_risk_rev_eur" in fam_df.columns:
            fam_df = fam_df.sort_values("aim_high_risk_rev_eur", ascending=False).head(5)

            header = ["Family", "AIM hints", "High-risk rev (€)", "High-risk %", "vs network (pp)"]
            rows = [header]
            for _, row in fam_df.iterrows():
                vs_net = _safe_float(row.get("vs_network_risk_pp"))
                vs_str = f"{vs_net:+.1f}pp" if vs_net is not None else "—"
                rows.append([
                    str(row.get("product_family", "")),
                    str(row.get("aim_l1_hints", ""))[:40],
                    _fmt_eur(_safe_float(row.get("aim_high_risk_rev_eur"))),
                    _fmt_pct(_safe_float(row.get("aim_high_risk_rev_pct"))),
                    vs_str,
                ])

            col_w = [CONTENT_W * x for x in [0.24, 0.28, 0.18, 0.14, 0.16]]
            tbl = Table(rows, colWidths=col_w)
            tbl.setStyle(_table_style_base(len(rows)))
            elements.append(tbl)

    elements.append(Spacer(1, 12))
    return elements


# ---------------------------------------------------------------------------
# Section 5 — Substitution Pressure
# ---------------------------------------------------------------------------

def _substitution_bar_chart(sub_df: pd.DataFrame) -> Optional[BytesIO]:
    if sub_df.empty:
        return None

    df = sub_df.head(8).copy()
    df = df.sort_values("bvp_share_units", ascending=True)

    fig, ax = plt.subplots(figsize=(7, 3.5))
    bars = ax.barh(
        df["product_subgroup"],
        df["bvp_share_units"] * 100,
        color="#E87722",
        edgecolor="white",
        height=0.6,
    )
    ax.axvline(x=50, color="#C62828", linewidth=1.5, linestyle="--", alpha=0.8,
               label="50% BVP threshold")
    ax.set_xlabel("BVP unit share (%)", fontsize=8)
    ax.set_xlim(0, max(df["bvp_share_units"].max() * 105, 55))
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=7, loc="lower right")
    ax.set_facecolor("#FAFBFC")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#E0E0E0", linewidth=0.5)
    fig.tight_layout(pad=0.4)
    return _fig_to_image(fig)


def _build_substitution(
    dist_code: str,
    substitution_db: pd.DataFrame,
    latest_year: int,
    styles,
) -> list:
    elements: list = []
    elements += _section_heading("BVP Substitution Pressure", styles)

    if substitution_db.empty:
        elements.append(_not_available(styles))
        return elements

    sub_df = substitution_db[
        (substitution_db["distributor_code"] == dist_code)
        & (substitution_db["year"] == latest_year)
    ].copy()

    if sub_df.empty:
        elements.append(_not_available(styles))
        return elements

    if "bvp_share_units" in sub_df.columns:
        sub_df = sub_df.sort_values("bvp_share_units", ascending=False)

    top8 = sub_df.head(8)

    header = ["Subgroup", "Genuine qty", "BVP qty", "BVP share %", "Genuine (€)", "BVP (€)"]
    rows = [header]
    for _, row in top8.iterrows():
        rows.append([
            str(row.get("product_subgroup", "")),
            f"{int(row.get('genuine_qty', 0)):,}" if pd.notna(row.get("genuine_qty")) else "—",
            f"{int(row.get('bvp_qty', 0)):,}" if pd.notna(row.get("bvp_qty")) else "—",
            f"{row.get('bvp_share_units', 0) * 100:.1f}%" if pd.notna(row.get("bvp_share_units")) else "—",
            _fmt_eur(_safe_float(row.get("genuine_eur"))),
            _fmt_eur(_safe_float(row.get("bvp_eur"))),
        ])

    col_w = [CONTENT_W * x for x in [0.24, 0.13, 0.13, 0.14, 0.18, 0.18]]
    tbl = Table(rows, colWidths=col_w)
    tbl.setStyle(_table_style_base(len(rows)))
    elements.append(tbl)
    elements.append(Spacer(1, 10))

    # Horizontal bar chart
    chart_buf = _substitution_bar_chart(sub_df)
    if chart_buf:
        img = Image(chart_buf, width=CONTENT_W, height=CONTENT_W * 0.48)
        elements.append(img)

    elements.append(Spacer(1, 12))
    return elements


# ---------------------------------------------------------------------------
# Section 3 — PMS Capture Detail (re-uses scorecard helper via same import path)
# ---------------------------------------------------------------------------
# We import _build_pms_capture from scorecard_pdf directly
from modules.scorecard_pdf import _build_pms_capture  # noqa: E402


# ---------------------------------------------------------------------------
# Section 9 — Meeting Agenda
# ---------------------------------------------------------------------------

def _build_agenda(
    dist_code: str,
    latest_year: int,
    hr_pct: Optional[float],
    gap_total: float,
    styles,
) -> list:
    elements: list = []
    elements += _section_heading("Suggested Meeting Agenda", styles)

    hr_str = f"{hr_pct:.1%}" if hr_pct is not None else "N/A"
    gap_str = f"€{gap_total:,.0f}" if gap_total else "N/A"

    agenda_items = [
        f"Performance review — {latest_year} KPIs vs targets",
        f"AIM risk: {hr_str} high-risk revenue — action plan",
        f"PMS capture recovery: {gap_str} opportunity",
        "BVP substitution: top 3 product families at risk",
        "Next steps and commitments",
    ]

    body_style = ParagraphStyle(
        "agenda_body",
        parent=styles["body"],
        fontSize=10,
        spaceBefore=6,
        spaceAfter=4,
        leftIndent=12,
    )
    label_style = ParagraphStyle(
        "agenda_label",
        parent=body_style,
        textColor=ISZE_BLUE,
        fontName="Helvetica-Bold",
    )

    for i, item in enumerate(agenda_items, start=1):
        elements.append(Paragraph(f"{i}. {item}", body_style))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"Prepared for {dist_code} · {latest_year} · ISZE Aftersales",
        styles["cover_meta"],
    ))
    return elements


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_review_pack(
    distributor_code: str,
    bundle: dict,
    years: list[int],
) -> BytesIO:
    """Build a full distributor review pack PDF and return as BytesIO."""
    years = sorted(years)
    latest_year = years[-1]

    gps_db = bundle.get("gps_db", pd.DataFrame())
    network_percentile = bundle.get("network_percentile", pd.DataFrame())
    pms_capture = bundle.get("pms_capture", pd.DataFrame())
    capture_trajectory = bundle.get("capture_trajectory", pd.DataFrame())
    capture_recovery = bundle.get("capture_recovery", pd.DataFrame())
    aim_db = bundle.get("aim_db", pd.DataFrame())
    aim_family = bundle.get("aim_family", pd.DataFrame())
    substitution_db = bundle.get("substitution_db", pd.DataFrame())

    # Resolve country / region
    country, region = "", ""
    if not gps_db.empty:
        mask = (gps_db["distributor_code"] == distributor_code) & (gps_db["year"] == latest_year)
        g_row = gps_db[mask]
        if g_row.empty:
            g_row = gps_db[gps_db["distributor_code"] == distributor_code]
        if not g_row.empty:
            country = str(g_row.iloc[0].get("country", "") or "")
            region = str(g_row.iloc[0].get("region", "") or "")

    # Compute agenda values
    hr_pct_agenda: Optional[float] = None
    if not aim_db.empty:
        a = aim_db[(aim_db["distributor_code"] == distributor_code) & (aim_db["year"] == latest_year)]
        if not a.empty:
            hr_pct_agenda = _safe_float(a.iloc[0].get("high_risk_rev_pct"))

    gap_total: float = 0.0
    if not capture_recovery.empty:
        rec = capture_recovery[capture_recovery["distributor_code"] == distributor_code]
        if not rec.empty and "gap_revenue_at_genuine" in rec.columns:
            gap_total = rec["gap_revenue_at_genuine"].sum()

    styles = _build_styles()

    buf = BytesIO()
    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2 * MARGIN, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

    story: list = []

    # Section 1 — Cover
    story += _build_review_cover(distributor_code, country, region, years, styles)

    # Section 2 — 3-Year KPI Trend
    story += _build_kpi_trend(
        distributor_code, gps_db, network_percentile, aim_db, years, styles
    )
    story.append(PageBreak())

    # Section 3 — Network Position
    story += _build_network_position(distributor_code, network_percentile, latest_year, styles)
    story.append(PageBreak())

    # Section 4 — AIM Exposure
    story += _build_aim_exposure(distributor_code, aim_db, aim_family, latest_year, styles)
    story.append(PageBreak())

    # Section 5 — Substitution Pressure
    story += _build_substitution(distributor_code, substitution_db, latest_year, styles)
    story.append(PageBreak())

    # Section 6 — PMS Capture Detail
    story += _build_pms_capture(distributor_code, pms_capture, capture_trajectory, latest_year, styles)
    story.append(PageBreak())

    # Section 7 — Capture Trajectory
    story += _build_capture_trajectory(distributor_code, capture_trajectory, latest_year, styles)
    story.append(PageBreak())

    # Section 8 — Recovery Opportunity
    story += _build_capture_recovery(distributor_code, capture_recovery, styles)
    story.append(PageBreak())

    # Section 9 — Meeting Agenda
    story += _build_agenda(distributor_code, latest_year, hr_pct_agenda, gap_total, styles)

    doc.build(story)
    buf.seek(0)
    return buf
