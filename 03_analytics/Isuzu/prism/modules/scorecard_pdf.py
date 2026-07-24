"""ReportLab PDF scorecard generator for ISZE distributor performance."""

from __future__ import annotations

import math
from datetime import date
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ISZE_BLUE = colors.HexColor("#1B3A6B")
ISZE_ORANGE = colors.HexColor("#E87722")
ISZE_LIGHT = colors.HexColor("#D6E4F0")
ROW_ALT = colors.HexColor("#F5F8FC")
RED = colors.HexColor("#C62828")
GRAY = colors.HexColor("#777777")
WHITE = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 1.5 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

_METRIC_LABEL_MAP = {
    "gps_spu": "GPS/SPU (€)",
    "total_capture": "Total PMS capture",
    "genuine_capture": "Genuine capture",
    "bvp_mix": "BVP mix",
}
_METRIC_ORDER = ["gps_spu", "total_capture", "genuine_capture", "bvp_mix"]

_GAP_COLORS = {
    "substitution": colors.HexColor("#E87722"),
    "catalog_gap": colors.HexColor("#C62828"),
    "under_service": colors.HexColor("#AAAAAA"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_eur(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"€{int(round(v)):,}"


def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v * 100:.1f}%"


def _fmt_slope(v) -> str:
    # slope column is stored in fraction/yr (capture_rate is a 0..1 fraction);
    # express as percentage-points per year for display.
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    pp = v * 100.0
    if abs(pp) < 0.1:
        return "→ flat"
    arrow = "↑" if pp > 0 else "↓"
    sign = "+" if pp > 0 else ""
    return f"{arrow} {sign}{pp:.1f}pp/yr"


def _fig_to_image(fig) -> BytesIO:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


def _not_available(styles) -> Paragraph:
    return Paragraph("<i>Data not available</i>", styles["na"])


def _section_heading(title: str, styles) -> list:
    return [
        Paragraph(title, styles["heading"]),
        _heading_rule(),
        Spacer(1, 6),
    ]


def _heading_rule() -> Table:
    t = Table([[""] * 1], colWidths=[CONTENT_W], rowHeights=[2])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ISZE_BLUE)]))
    return t


def _build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "heading": ParagraphStyle(
            "heading",
            parent=base["Normal"],
            fontSize=13,
            textColor=ISZE_BLUE,
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.black,
            fontName="Helvetica",
        ),
        "na": ParagraphStyle(
            "na",
            parent=base["Normal"],
            fontSize=9,
            textColor=GRAY,
            fontName="Helvetica-Oblique",
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Normal"],
            fontSize=14,
            textColor=WHITE,
            fontName="Helvetica-Bold",
        ),
        "cover_code": ParagraphStyle(
            "cover_code",
            parent=base["Normal"],
            fontSize=28,
            textColor=ISZE_ORANGE,
            fontName="Helvetica-Bold",
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            parent=base["Normal"],
            fontSize=10,
            textColor=GRAY,
            fontName="Helvetica",
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            parent=base["Normal"],
            fontSize=9,
            textColor=GRAY,
            fontName="Helvetica",
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontSize=8,
            textColor=RED,
            fontName="Helvetica",
        ),
    }


def _table_style_base(n_rows: int, header_col_span: int = None) -> TableStyle:
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), ISZE_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ROW_ALT, WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D0D0D0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    return TableStyle(cmds)


# ---------------------------------------------------------------------------
# Section 1 — Cover
# ---------------------------------------------------------------------------

def _build_cover(dist_code: str, country: str, region: str, latest_year: int, styles) -> list:
    elements = []

    # Blue banner
    banner_data = [[Paragraph("DISTRIBUTOR PERFORMANCE SCORECARD", styles["cover_title"])]]
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

    elements.append(Paragraph(
        f"Data year: {latest_year} &nbsp;&nbsp;|&nbsp;&nbsp; Generated: {date.today().strftime('%d %b %Y')}",
        styles["cover_meta"],
    ))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("CONFIDENTIAL — ISZE Internal Use Only", styles["footer"]))
    elements.append(Spacer(1, 24))

    return elements


# ---------------------------------------------------------------------------
# Section 2 — Network Position
# ---------------------------------------------------------------------------

def _radar_chart(metrics: list[str], percentiles: list[float]) -> BytesIO:
    n = len(metrics)
    angles = [i * 2 * math.pi / n for i in range(n)] + [0]
    vals = list(percentiles) + [percentiles[0]]

    fig, ax = plt.subplots(figsize=(3.2, 3.2), subplot_kw={"polar": True})
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6, color="#888888")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=7, color="#333333")
    ax.plot(angles, vals, color="#E87722", linewidth=1.5)
    ax.fill(angles, vals, color="#E87722", alpha=0.25)
    ax.spines["polar"].set_color("#CCCCCC")
    ax.grid(color="#DDDDDD", linewidth=0.5)
    fig.tight_layout(pad=0.3)
    return _fig_to_image(fig)


def _build_network_position(
    dist_code: str,
    network_percentile: pd.DataFrame,
    latest_year: int,
    styles,
) -> list:
    elements = []
    elements += _section_heading("Network Position", styles)

    if network_percentile.empty:
        elements.append(_not_available(styles))
        return elements

    df = network_percentile[
        (network_percentile["distributor_code"] == dist_code)
        & (network_percentile["year"] == latest_year)
    ].copy()

    if df.empty:
        elements.append(_not_available(styles))
        return elements

    df = df[df["metric"].isin(_METRIC_ORDER)].copy()
    df["metric"] = pd.Categorical(df["metric"], categories=_METRIC_ORDER, ordered=True)
    df = df.sort_values("metric")

    # Build table rows
    header = ["KPI", "This distributor", "Network median", "Percentile"]
    rows = [header]
    for _, row in df.iterrows():
        label = _METRIC_LABEL_MAP.get(row["metric"], row["metric"])
        raw = row.get("raw_value", float("nan"))
        median = row.get("network_median", float("nan"))
        pct = row.get("percentile_rank", float("nan"))
        # Format raw/median based on metric type
        if row["metric"] == "gps_spu":
            raw_str = _fmt_eur(raw)
            med_str = _fmt_eur(median)
        else:
            raw_str = _fmt_pct(raw)
            med_str = _fmt_pct(median)
        pct_str = f"{pct:.0f}th" if not (isinstance(pct, float) and math.isnan(pct)) else "—"
        rows.append([label, raw_str, med_str, pct_str])

    col_w = [CONTENT_W * x for x in [0.40, 0.20, 0.20, 0.20]]

    # Radar chart
    metric_labels = [_METRIC_LABEL_MAP.get(m, m) for m in df["metric"].tolist()]
    pct_vals = df["percentile_rank"].fillna(0).tolist()

    radar_buf = None
    if len(metric_labels) >= 3:
        radar_buf = _radar_chart(metric_labels, pct_vals)

    # Side-by-side layout: table left, radar right
    if radar_buf:
        tbl_w = CONTENT_W * 0.56
        img_w = CONTENT_W * 0.40
        col_w_adj = [tbl_w * x for x in [0.42, 0.20, 0.20, 0.18]]
        tbl = Table(rows, colWidths=col_w_adj)
        tbl.setStyle(_table_style_base(len(rows)))
        img = Image(radar_buf, width=img_w, height=img_w)
        side_table = Table([[tbl, img]], colWidths=[tbl_w + 0.5 * cm, img_w])
        side_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(side_table)
    else:
        tbl = Table(rows, colWidths=col_w)
        tbl.setStyle(_table_style_base(len(rows)))
        elements.append(tbl)

    elements.append(Spacer(1, 12))
    return elements


# ---------------------------------------------------------------------------
# Section 3 — PMS Capture Detail
# ---------------------------------------------------------------------------

def _build_pms_capture(
    dist_code: str,
    pms_capture: pd.DataFrame,
    capture_trajectory: pd.DataFrame,
    latest_year: int,
    styles,
) -> list:
    elements = []
    elements += _section_heading("PMS Capture Detail", styles)

    if pms_capture.empty:
        elements.append(_not_available(styles))
        return elements

    df = pms_capture[
        (pms_capture["distributor_code"] == dist_code)
        & (pms_capture["year"] == latest_year)
    ].copy()

    if df.empty:
        elements.append(_not_available(styles))
        return elements

    total_df = df[df["line_type"] == "total"].set_index("pms_category")
    genuine_df = df[df["line_type"] == "genuine"].set_index("pms_category")
    categories = sorted(set(total_df.index) | set(genuine_df.index))

    # Trajectory slopes
    slope_map: dict[str, tuple[float, bool]] = {}
    if not capture_trajectory.empty:
        traj = capture_trajectory[capture_trajectory["distributor_code"] == dist_code]
        for _, r in traj.iterrows():
            slope_map[r["pms_category"]] = (
                r.get("trend_slope_pp_per_year", float("nan")),
                bool(r.get("alert_declining", False)),
            )

    header = ["Category", "Total capture", "Genuine capture", "BVP gap (pp)", "Revenue gap (€)", "Trend"]
    rows = [header]
    declining_rows: list[int] = []

    for i, cat in enumerate(categories):
        tot_row = total_df.loc[cat] if cat in total_df.index else None
        gen_row = genuine_df.loc[cat] if cat in genuine_df.index else None

        tot_rate = tot_row["capture_rate"] if tot_row is not None and "capture_rate" in tot_row.index else float("nan")
        gen_rate = gen_row["capture_rate"] if gen_row is not None and "capture_rate" in gen_row.index else float("nan")
        rev_gap = tot_row["revenue_gap_eur"] if tot_row is not None and "revenue_gap_eur" in tot_row.index else float("nan")

        bvp_gap = float("nan")
        if not (isinstance(tot_rate, float) and math.isnan(tot_rate)) and \
           not (isinstance(gen_rate, float) and math.isnan(gen_rate)):
            bvp_gap = (tot_rate - gen_rate) * 100

        slope, declining = slope_map.get(cat, (float("nan"), False))
        trend_str = _fmt_slope(slope)

        rows.append([
            cat,
            _fmt_pct(tot_rate),
            _fmt_pct(gen_rate),
            f"{bvp_gap:.1f}pp" if not math.isnan(bvp_gap) else "—",
            _fmt_eur(rev_gap),
            trend_str,
        ])
        if declining:
            declining_rows.append(i + 1)  # +1 for header row

    col_w = [CONTENT_W * x for x in [0.22, 0.14, 0.16, 0.14, 0.18, 0.16]]
    tbl = Table(rows, colWidths=col_w)
    style_cmds = _table_style_base(len(rows))
    for ri in declining_rows:
        style_cmds.add("TEXTCOLOR", (5, ri), (5, ri), ISZE_ORANGE)
        style_cmds.add("FONTNAME", (5, ri), (5, ri), "Helvetica-Bold")
    tbl.setStyle(style_cmds)
    elements.append(tbl)
    elements.append(Spacer(1, 12))
    return elements


# ---------------------------------------------------------------------------
# Section 4 — Capture Trajectory
# ---------------------------------------------------------------------------

def _trajectory_chart(traj_df: pd.DataFrame, latest_year: int) -> BytesIO:
    fig, ax = plt.subplots(figsize=(7, 3.5))

    # Pick up to 5 categories with most data points
    cat_counts = traj_df.groupby("pms_category")["year"].count().sort_values(ascending=False)
    top_cats = cat_counts.head(5).index.tolist()

    palette = ["#1B3A6B", "#E87722", "#2C5AA0", "#43A047", "#C62828"]

    for idx, cat in enumerate(top_cats):
        sub = traj_df[traj_df["pms_category"] == cat].sort_values("year")
        hist = sub[~sub["is_projected"].astype(bool)]
        proj = sub[sub["is_projected"].astype(bool)]
        color = palette[idx % len(palette)]

        if not hist.empty:
            ax.plot(
                hist["year"], hist["capture_rate"] * 100,
                color=color, linewidth=1.8, label=cat, marker="o", markersize=3,
            )
        if not proj.empty:
            # Connect last historical point if available
            connect_x = [hist["year"].iloc[-1]] if not hist.empty else []
            connect_y = [hist["capture_rate"].iloc[-1] * 100] if not hist.empty else []
            ax.plot(
                connect_x + proj["year"].tolist(),
                connect_y + (proj["capture_rate"] * 100).tolist(),
                color=color, linewidth=1.5, linestyle="--",
            )

    ax.axvline(x=latest_year, color="#999999", linewidth=1.0, linestyle="--", alpha=0.7)
    ax.text(
        latest_year + 0.05, ax.get_ylim()[1] * 0.97,
        str(latest_year),
        fontsize=7, color="#888888", va="top",
    )

    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Capture rate (%)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.legend(fontsize=7, loc="best", framealpha=0.8)
    ax.set_facecolor("#FAFBFC")
    fig.patch.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#E0E0E0", linewidth=0.5)
    fig.tight_layout(pad=0.4)
    return _fig_to_image(fig)


def _build_capture_trajectory(
    dist_code: str,
    capture_trajectory: pd.DataFrame,
    latest_year: int,
    styles,
) -> list:
    elements = []
    elements += _section_heading("Capture Trajectory (Historical + Forecast)", styles)

    if capture_trajectory.empty:
        elements.append(_not_available(styles))
        return elements

    df = capture_trajectory[capture_trajectory["distributor_code"] == dist_code].copy()

    if df.empty:
        elements.append(_not_available(styles))
        return elements

    chart_buf = _trajectory_chart(df, latest_year)
    img = Image(chart_buf, width=CONTENT_W, height=CONTENT_W * 0.45)
    elements.append(img)
    elements.append(Spacer(1, 12))
    return elements


# ---------------------------------------------------------------------------
# Section 5 — Capture Recovery Opportunity
# ---------------------------------------------------------------------------

def _build_capture_recovery(
    dist_code: str,
    capture_recovery: pd.DataFrame,
    styles,
) -> list:
    elements = []
    elements += _section_heading("Capture Recovery Opportunity", styles)

    if capture_recovery.empty:
        elements.append(_not_available(styles))
        return elements

    df = capture_recovery[capture_recovery["distributor_code"] == dist_code].copy()

    if df.empty:
        elements.append(_not_available(styles))
        return elements

    total_gap = df["gap_revenue_at_genuine"].sum() if "gap_revenue_at_genuine" in df.columns else 0

    elements.append(Paragraph(
        f"Total gap at genuine ASP: <b>{_fmt_eur(total_gap)}</b>",
        ParagraphStyle(
            "gap_total",
            fontName="Helvetica",
            fontSize=11,
            textColor=ISZE_BLUE,
            spaceBefore=4,
            spaceAfter=6,
        ),
    ))

    if "gap_revenue_at_genuine" in df.columns:
        df = df.sort_values("gap_revenue_at_genuine", ascending=False)

    header = ["Category", "Gap type", "Capture actual", "Gap (€ at genuine ASP)", "BVP share"]
    rows = [header]

    for _, row in df.iterrows():
        gap_type = row.get("gap_type", "")
        rows.append([
            row.get("pms_category", ""),
            gap_type,
            _fmt_pct(row.get("capture_rate_actual", float("nan"))),
            _fmt_eur(row.get("gap_revenue_at_genuine", float("nan"))),
            _fmt_pct(row.get("bvp_unit_share", float("nan"))),
        ])

    col_w = [CONTENT_W * x for x in [0.25, 0.18, 0.17, 0.25, 0.15]]
    tbl = Table(rows, colWidths=col_w)
    style_cmds = _table_style_base(len(rows))

    # Colour-code gap_type column (index 1) per data row
    _gap_type_rl = {
        "substitution": ISZE_ORANGE,
        "catalog_gap": RED,
        "under_service": GRAY,
    }
    for ri, row_data in enumerate(rows[1:], start=1):
        gt = row_data[1].lower() if row_data[1] else ""
        color = _gap_type_rl.get(gt, colors.black)
        style_cmds.add("TEXTCOLOR", (1, ri), (1, ri), color)
        style_cmds.add("FONTNAME", (1, ri), (1, ri), "Helvetica-Bold")

    tbl.setStyle(style_cmds)
    elements.append(tbl)
    elements.append(Spacer(1, 12))
    return elements


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_scorecard(
    distributor_code: str,
    bundle: dict,
    latest_year: int,
) -> BytesIO:
    """Build a distributor performance scorecard PDF and return it as BytesIO."""
    gps_db = bundle.get("gps_db", pd.DataFrame())
    network_percentile = bundle.get("network_percentile", pd.DataFrame())
    pms_capture = bundle.get("pms_capture", pd.DataFrame())
    capture_trajectory = bundle.get("capture_trajectory", pd.DataFrame())
    capture_recovery = bundle.get("capture_recovery", pd.DataFrame())

    # Resolve country/region from gps_db
    country, region = "", ""
    if not gps_db.empty:
        mask = (gps_db["distributor_code"] == distributor_code) & (gps_db["year"] == latest_year)
        row = gps_db[mask]
        if row.empty:
            row = gps_db[gps_db["distributor_code"] == distributor_code]
        if not row.empty:
            country = str(row.iloc[0].get("country", "") or "")
            region = str(row.iloc[0].get("region", "") or "")

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

    story = []
    story += _build_cover(distributor_code, country, region, latest_year, styles)
    story += _build_network_position(distributor_code, network_percentile, latest_year, styles)
    story += _build_pms_capture(distributor_code, pms_capture, capture_trajectory, latest_year, styles)
    story += _build_capture_trajectory(distributor_code, capture_trajectory, latest_year, styles)
    story += _build_capture_recovery(distributor_code, capture_recovery, styles)

    doc.build(story)
    buf.seek(0)
    return buf
