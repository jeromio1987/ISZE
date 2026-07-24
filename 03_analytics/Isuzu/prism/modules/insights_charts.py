"""Cross-Module Insights renderers (GPS x PMS x BVP fused signals).

Extracted from pages/5_Insights.py (docs/DASHBOARD_IA.md §6 P2) so Network
Intelligence can reuse these views without duplicating the page. No visual
changes from the original page — the "BVP × Capture" quadrant kill (redundant
with pages/16_AIM_GPS_Matrix.py) is deferred to the P3 merge, not done here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.bvp_product_nav import subgroup_label
from modules.pms_engine import CATEGORY_LABELS, classify_pms_sales

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
PALETTE = [
    "#1B3A6B", "#E87722", "#2C5AA0", "#F4A460", "#4A90D9",
    "#8B4513", "#70B8FF", "#D2691E", "#003087", "#FFA07A",
]
PLOTLY_BASE = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Segoe UI, sans-serif", size=12),
)


def _tc(v, lo=0.3, hi=0.6):
    """Traffic colour for capture rate."""
    if pd.isna(v):
        return "#CCCCCC"
    return "#2E7D32" if v >= hi else ("#F9A825" if v >= lo else "#C62828")


def render_opportunity_matrix(
    pms_all: pd.DataFrame,
    aim_db: pd.DataFrame,
    mix_sub: pd.DataFrame,
    dist_sel: list[str],
    dists_avail: list[str],
    latest_y: int | None,
) -> None:
    st.markdown("#### 🎯 Opportunity Matrix — Gap per Truck × AIM Risk × BVP Mix")
    st.caption(
        "**X axis:** AIM high-risk revenue share (% of revenue exposed to IAM competition) "
        "| **Y axis:** Revenue gap per truck (untapped € per vehicle per year per category) "
        "| **Bubble size:** Absolute revenue gap (€) "
        "| **Color:** BVP unit mix % — how much of current sales is already BVP "
        "| Bubbles top-right = highest priority: large gap, high IAM risk, high BVP substitution."
    )

    if pms_all.empty or latest_y is None:
        st.info("No PMS capture data available.")
        return

    df_opp = pms_all[
        (pms_all["line_type"] == "total") &
        (pms_all["year"] == latest_y) &
        (pms_all["distributor_code"].isin(dist_sel if dist_sel else dists_avail))
    ].copy()
    df_opp = df_opp[df_opp["uio_units"] > 0].copy()
    df_opp["gap_per_truck"] = df_opp["revenue_gap_eur"] / df_opp["uio_units"]
    df_opp["category_label"] = df_opp["pms_category"].map(CATEGORY_LABELS).fillna(df_opp["pms_category"])

    if not aim_db.empty and "high_risk_rev_pct" in aim_db.columns:
        aim_latest = aim_db[aim_db["year"] == latest_y].copy() if "year" in aim_db.columns else aim_db.copy()
        df_opp = df_opp.merge(
            aim_latest[["distributor_code", "high_risk_rev_pct"]],
            on="distributor_code", how="left"
        )
    else:
        df_opp["high_risk_rev_pct"] = np.nan

    mix_cat_col = "product_subgroup" if "product_subgroup" in mix_sub.columns else "pms_category"
    if not mix_sub.empty and mix_cat_col in mix_sub.columns:
        mix_latest = mix_sub[mix_sub["year"] == latest_y].copy() if "year" in mix_sub.columns else mix_sub.copy()
        df_opp = df_opp.merge(
            mix_latest[["distributor_code", mix_cat_col, "bvp_share_units"]].rename(
                columns={mix_cat_col: "pms_category"}
            ),
            on=["distributor_code", "pms_category"], how="left"
        )
    else:
        df_opp["bvp_share_units"] = np.nan

    df_plot = df_opp.dropna(subset=["gap_per_truck"]).copy()
    if df_plot.empty:
        st.info("Not enough data for opportunity matrix — check that derived CSVs are built.")
    else:
        x_col = "high_risk_rev_pct" if df_plot["high_risk_rev_pct"].notna().any() else "capture_rate"
        x_label = "AIM high-risk revenue %" if x_col == "high_risk_rev_pct" else "Capture rate"
        color_col = "bvp_share_units" if df_plot["bvp_share_units"].notna().any() else "category_label"

        fig = px.scatter(
            df_plot,
            x=x_col,
            y="gap_per_truck",
            size="revenue_gap_eur",
            color=color_col,
            text="distributor_code",
            hover_data={
                "distributor_code": True,
                "category_label": True,
                "revenue_gap_eur": ":,.0f",
                "gap_per_truck": ":.1f",
                x_col: ":.1%" if x_col == "capture_rate" else ":.0%",
            },
            labels={
                x_col: x_label,
                "gap_per_truck": "Revenue gap per truck (€)",
                "revenue_gap_eur": "Total gap (€)",
            },
            color_continuous_scale=["#2E7D32", "#F9A825", "#C62828"] if color_col == "bvp_share_units" else None,
        )
        if x_col == "high_risk_rev_pct":
            fig.add_vline(x=0.3, line_dash="dash", line_color="#999",
                          annotation_text="30% AIM threshold")
        max_gap = df_plot["revenue_gap_eur"].max()
        sizeref = 2.0 * max_gap / (40.0 ** 2) if max_gap > 0 else 1.0
        fig.update_traces(
            textposition="top center",
            marker=dict(opacity=0.8, sizemode="area", sizeref=sizeref),
        )
        fig.update_layout(**PLOTLY_BASE, height=520, margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig, width='stretch')

    st.markdown("#### Ranked Opportunities")
    rank_cols = ["distributor_code", "category_label", "gap_per_truck", "revenue_gap_eur", "capture_rate"]
    if "high_risk_rev_pct" in df_opp.columns:
        rank_cols.append("high_risk_rev_pct")
    if "bvp_share_units" in df_opp.columns:
        rank_cols.append("bvp_share_units")
    rank_df = df_opp[[c for c in rank_cols if c in df_opp.columns]].copy()
    rank_df = rank_df.sort_values("gap_per_truck", ascending=False).head(30).reset_index(drop=True)
    rank_df.index += 1
    for col in ["gap_per_truck", "revenue_gap_eur"]:
        if col in rank_df.columns:
            rank_df[col] = rank_df[col].apply(lambda x: f"€{x:,.0f}" if pd.notna(x) else "—")
    for col in ["capture_rate", "bvp_share_units", "high_risk_rev_pct"]:
        if col in rank_df.columns:
            rank_df[col] = rank_df[col].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "—")
    st.dataframe(rank_df.rename(columns={
        "distributor_code": "Distributor", "category_label": "Category",
        "gap_per_truck": "Gap/truck", "revenue_gap_eur": "Total gap",
        "capture_rate": "Capture", "bvp_share_units": "BVP mix",
        "high_risk_rev_pct": "AIM risk",
    }), width='stretch')


def render_bvp_capture_quadrant(
    pms_all: pd.DataFrame,
    mix_sub: pd.DataFrame,
    dist_sel: list[str],
    dists_avail: list[str],
    latest_y: int | None,
) -> None:
    st.markdown("#### 📐 BVP Mix × PMS Capture — Quadrant Analysis")
    st.caption(
        "**Formula: X = BVP unit share = BVP qty ÷ (Genuine + BVP qty)** "
        "| **Y = Total PMS capture rate = (Genuine + BVP) qty ÷ Expected demand** "
        "| **Top-left:** High capture, low BVP → genuine-dominant, strong performer "
        "| **Top-right:** High capture, high BVP → BVP is filling gap, net positive "
        "| **Bottom-left:** Low capture, low BVP → IAM winning, no BVP offset "
        "| **Bottom-right:** High BVP, low total capture → BVP replaced genuine but IAM still winning — worst quadrant."
    )

    if pms_all.empty or mix_sub.empty or latest_y is None:
        st.info("Requires both PMS capture and BVP mix data. Check that derived CSVs are built.")
        return

    df_cap = pms_all[
        (pms_all["line_type"] == "total") &
        (pms_all["year"] == latest_y) &
        (pms_all["distributor_code"].isin(dist_sel if dist_sel else dists_avail))
    ].copy()

    mix_cat_col = "product_subgroup" if "product_subgroup" in mix_sub.columns else "pms_category"
    mix_y = mix_sub[mix_sub["year"] == latest_y].copy() if "year" in mix_sub.columns else mix_sub.copy()
    df_cap = df_cap.merge(
        mix_y[["distributor_code", mix_cat_col, "bvp_share_units"]].rename(
            columns={mix_cat_col: "pms_category"}
        ),
        on=["distributor_code", "pms_category"], how="inner"
    )
    df_cap["category_label"] = df_cap["pms_category"].map(CATEGORY_LABELS).fillna(df_cap["pms_category"])

    cat_pick = st.selectbox(
        "Category",
        ["All"] + sorted(df_cap["pms_category"].dropna().unique().tolist()),
        format_func=lambda c: "All categories" if c == "All" else CATEGORY_LABELS.get(c, c),
        key="quad_cat",
    )
    df_q = df_cap.copy() if cat_pick == "All" else df_cap[df_cap["pms_category"] == cat_pick].copy()

    if df_q.empty:
        st.info("No data for this selection.")
        return

    fig = px.scatter(
        df_q,
        x="bvp_share_units",
        y="capture_rate",
        color="distributor_code",
        symbol="category_label" if cat_pick == "All" else None,
        text="distributor_code",
        size="revenue_gap_eur",
        hover_data={
            "category_label": True,
            "capture_rate": ":.0%",
            "bvp_share_units": ":.0%",
            "revenue_gap_eur": ":,.0f",
        },
        labels={"bvp_share_units": "BVP unit mix %", "capture_rate": "Total PMS capture rate"},
        color_discrete_sequence=PALETTE,
    )
    fig.add_vline(x=0.20, line_dash="dash", line_color="#999",
                  annotation_text="20% BVP threshold", annotation_position="top right")
    fig.add_hline(y=0.50, line_dash="dash", line_color="#999",
                  annotation_text="50% capture threshold", annotation_position="top right")
    for x_, y_, txt, col in [
        (0.05, 0.75, "🟢 Genuine strong", "#2E7D32"),
        (0.55, 0.75, "🟡 BVP additive", "#F9A825"),
        (0.05, 0.25, "🔴 IAM winning", "#C62828"),
        (0.55, 0.25, "⚠️ Both losing", "#C62828"),
    ]:
        fig.add_annotation(x=x_, y=y_, text=txt, showarrow=False,
                           font=dict(color=col, size=11), xref="x", yref="y")
    fig.update_traces(textposition="top center", marker=dict(opacity=0.85))
    fig.update_layout(
        **PLOTLY_BASE, height=520,
        xaxis=dict(tickformat=".0%", range=[-0.05, 1.05], gridcolor="#F0F0F0"),
        yaxis=dict(tickformat=".0%", range=[-0.05, 1.05], gridcolor="#F0F0F0"),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    st.plotly_chart(fig, width='stretch')


def render_growth_decomposition(df_trend: pd.DataFrame, dist_sel: list[str]) -> None:
    st.markdown("#### 📈 Growth Decomposition — SPU Change vs UIO Change")
    st.caption(
        "**X axis: UIO YoY % = (UIO this year − UIO prior year) ÷ UIO prior year** "
        "| **Y axis: SPU YoY % = (Spend/unit this year − Spend/unit prior year) ÷ Spend/unit prior year** "
        "| **Top-right:** Fleet growing AND penetration improving — best position "
        "| **Top-left:** Fleet shrinking but squeezing more per truck — defensive success "
        "| **Bottom-right:** Fleet growing but not capturing new trucks — loyalty gap "
        "| **Bottom-left:** Fleet shrinking AND penetration falling — critical."
    )

    if df_trend.empty:
        st.info("No multi-year GPS trend data available.")
        return

    df_t = df_trend.sort_values(["distributor_code", "year_value"]).copy()
    df_t["spu_yoy"] = df_t.groupby("distributor_code")["spend_per_unit_eur"].pct_change()
    df_t["uio_yoy"] = df_t.groupby("distributor_code")["uio_units"].pct_change()
    df_t = df_t.dropna(subset=["spu_yoy", "uio_yoy"]).copy()
    df_t = df_t[df_t["distributor_code"].isin(dist_sel if dist_sel else df_t["distributor_code"].unique())].copy()

    yr_pick = st.selectbox(
        "Show year-on-year change for",
        sorted(df_t["year_value"].unique(), reverse=True),
        key="growth_yr",
    )
    df_g = df_t[df_t["year_value"] == yr_pick].copy()

    if df_g.empty:
        st.info("No data for this year.")
        return

    fig = px.scatter(
        df_g,
        x="uio_yoy",
        y="spu_yoy",
        text="distributor_code",
        color="distributor_code",
        size="total_sales_eur",
        hover_data={
            "spend_per_unit_eur": ":,.1f",
            "uio_units": ":,.0f",
            "total_sales_eur": ":,.0f",
        },
        labels={"uio_yoy": "UIO YoY change", "spu_yoy": "SPU YoY change"},
        color_discrete_sequence=PALETTE,
    )
    fig.add_vline(x=0, line_color="#333", line_width=1)
    fig.add_hline(y=0, line_color="#333", line_width=1)
    for x_, y_, txt, col in [
        (0.08, 0.08, "🚀 Fleet & penetration growing", "#2E7D32"),
        (-0.18, 0.08, "💪 Squeezing shrinking fleet", "#F9A825"),
        (0.08, -0.08, "⚠️ Not capturing new trucks", "#F9A825"),
        (-0.18, -0.08, "🔴 Losing on both dimensions", "#C62828"),
    ]:
        fig.add_annotation(x=x_, y=y_, text=txt, showarrow=False,
                           font=dict(color=col, size=10), xref="x", yref="y")
    fig.update_traces(textposition="top center", marker=dict(opacity=0.85))
    fig.update_layout(
        **PLOTLY_BASE, height=520,
        xaxis=dict(tickformat=".0%", gridcolor="#F0F0F0"),
        yaxis=dict(tickformat=".0%", gridcolor="#F0F0F0"),
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig, width='stretch')


def render_capture_trajectory(pms_all: pd.DataFrame, dist_sel: list[str], dists_avail: list[str]) -> None:
    st.markdown("#### 🔥 PMS Capture Rate Trajectory")
    st.caption(
        "**Each cell = total PMS capture rate for that distributor in that year** "
        "| 🟢 ≥ 60% · 🟡 30–60% · 🔴 < 30% "
        "| Read rows left-to-right: improving = shading getting greener, declining = getting redder. "
        "| Direction column shows the trend from the last two available years."
    )

    if pms_all.empty:
        st.info("No PMS capture data available.")
        return

    cat_t = st.selectbox(
        "Category",
        sorted(pms_all["pms_category"].dropna().unique()),
        format_func=lambda c: CATEGORY_LABELS.get(c, c),
        key="traj_cat",
    )
    df_traj = pms_all[
        (pms_all["line_type"] == "total") &
        (pms_all["pms_category"] == cat_t) &
        (pms_all["distributor_code"].isin(dist_sel if dist_sel else dists_avail))
    ].copy()

    if df_traj.empty:
        st.info("No data.")
        return

    pivot = df_traj.pivot_table(
        index="distributor_code", columns="year",
        values="capture_rate", aggfunc="mean",
    )
    yr_cols = sorted(pivot.columns)
    pivot = pivot.sort_values(yr_cols[-1], ascending=False)

    if len(yr_cols) >= 2:
        delta = pivot[yr_cols[-1]] - pivot[yr_cols[-2]]
        pivot["Direction"] = delta.apply(
            lambda d: "↑ Improving" if d > 0.02 else ("↓ Declining" if d < -0.02 else "→ Flat")
        )

    fmt_pivot = pivot.copy()
    for c in yr_cols:
        fmt_pivot[c] = pivot[c].apply(lambda v: f"{v*100:.0f}%" if pd.notna(v) else "—")

    def _color_df(df):
        return pd.DataFrame(
            [
                [
                    f"background-color: {_tc(pivot.loc[idx, col])}"
                    if col in yr_cols and not pd.isna(pivot.loc[idx, col]) else ""
                    for col in df.columns
                ]
                for idx in df.index
            ],
            index=df.index, columns=df.columns,
        )

    styled = fmt_pivot.style.apply(_color_df, axis=None, subset=yr_cols)
    st.dataframe(styled, width='stretch')


def render_network_benchmark(
    pms_all: pd.DataFrame, dist_sel: list[str], dists_avail: list[str], latest_y: int | None,
) -> None:
    st.markdown("#### 🏆 Network Benchmark — Parts per 100 Trucks")
    st.caption(
        "**Formula: sell rate = actual qty sold ÷ UIO × 100** "
        "| Reads: how many parts of this type did each distributor sell per 100 trucks in their fleet. "
        "| Best-in-class = highest observed rate across the network. "
        "| Gap to best = how many extra units the distributor would sell if it matched the top performer."
    )

    if pms_all.empty or latest_y is None:
        st.info("No PMS capture data available.")
        return

    cat_b = st.selectbox(
        "Category",
        sorted(pms_all["pms_category"].dropna().unique()),
        format_func=lambda c: CATEGORY_LABELS.get(c, c),
        key="bench_cat",
    )
    df_b = pms_all[
        (pms_all["line_type"] == "total") &
        (pms_all["pms_category"] == cat_b) &
        (pms_all["year"] == latest_y) &
        (pms_all["distributor_code"].isin(dist_sel if dist_sel else dists_avail)) &
        (pms_all["uio_units"] > 0)
    ].copy()

    if df_b.empty:
        st.info("No data.")
        return

    df_b["per_100"] = df_b["actual_qty"] / df_b["uio_units"] * 100
    best = df_b["per_100"].max()
    df_b["gap_to_best"] = best - df_b["per_100"]
    df_b["gap_units"] = df_b["gap_to_best"] * df_b["uio_units"] / 100
    df_b = df_b.sort_values("per_100", ascending=True)

    colors = [ISZE_ORANGE if v == best else ISZE_BLUE for v in df_b["per_100"]]
    fig = go.Figure(go.Bar(
        x=df_b["per_100"],
        y=df_b["distributor_code"],
        orientation="h",
        marker_color=colors,
        text=df_b["per_100"].apply(lambda v: f"{v:.1f}"),
        textposition="outside",
        customdata=np.stack([df_b["uio_units"], df_b["gap_to_best"], df_b["gap_units"]], axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Sell rate: %{x:.1f} per 100 trucks<br>"
            "UIO: %{customdata[0]:,.0f}<br>"
            "Gap to best: %{customdata[1]:.1f} per 100<br>"
            "Gap in units: %{customdata[2]:,.0f}<extra></extra>"
        ),
    ))
    fig.add_vline(x=best, line_dash="dash", line_color=ISZE_ORANGE,
                  annotation_text=f"Best: {best:.1f}", annotation_position="top right")
    fig.update_layout(
        **PLOTLY_BASE,
        height=max(320, len(df_b) * 30),
        xaxis_title="Parts sold per 100 trucks",
        margin=dict(l=10, r=80, t=40, b=20),
        xaxis=dict(gridcolor="#F0F0F0"),
    )
    st.plotly_chart(fig, width='stretch')

    st.markdown("#### Gap to best-in-class")
    gap_tbl = df_b[["distributor_code", "per_100", "gap_to_best", "gap_units", "uio_units"]].sort_values(
        "gap_to_best", ascending=False
    ).copy()
    gap_tbl["per_100"] = gap_tbl["per_100"].apply(lambda v: f"{v:.1f}")
    gap_tbl["gap_to_best"] = gap_tbl["gap_to_best"].apply(lambda v: f"{v:.1f}")
    gap_tbl["gap_units"] = gap_tbl["gap_units"].apply(lambda v: f"{v:,.0f}")
    gap_tbl["uio_units"] = gap_tbl["uio_units"].apply(lambda v: f"{v:,.0f}")
    st.dataframe(gap_tbl.rename(columns={
        "distributor_code": "Distributor", "per_100": "Sell rate/100",
        "gap_to_best": "Gap to best", "gap_units": "Units unrealised", "uio_units": "UIO",
    }), width='stretch', hide_index=True)


def render_displacement_severity(
    sub_pair: pd.DataFrame, year_sel: list[int], dist_sel: list[str], latest_y: int | None,
) -> None:
    st.markdown("#### 💀 BVP Displacement Severity per Part Pair")
    st.caption(
        "**Formula: displacement ratio = BVP qty ÷ genuine qty (for matched OE↔BVP pairs)** "
        "| Ratio = 0.1: BVP marginal, genuine dominant "
        "| Ratio = 1.0: parity — BVP selling as much as genuine "
        "| Ratio > 1.0: BVP is outselling the genuine counterpart — genuine has been displaced "
        "| Ratio > 5.0: genuine effectively dead on this pair."
    )

    if sub_pair.empty:
        st.info("No substitution pair data. Run `python scripts\\build_bvp_crossref_sales.py`.")
        return

    df_disp = sub_pair.copy()
    if year_sel and "year" in df_disp.columns:
        df_disp = df_disp[df_disp["year"].isin(year_sel)].copy()
    if dist_sel and "distributor_code" in df_disp.columns:
        df_disp = df_disp[df_disp["distributor_code"].isin(dist_sel)].copy()
    if latest_y and "year" in df_disp.columns:
        df_disp = df_disp[df_disp["year"] == latest_y].copy()

    if "genuine_qty" not in df_disp.columns or "bvp_qty" not in df_disp.columns:
        st.info("Substitution pair data missing `genuine_qty` / `bvp_qty` columns. Rebuild with updated script.")
        return

    df_disp = df_disp[df_disp["genuine_qty"] > 0].copy()
    df_disp["displacement_ratio"] = df_disp["bvp_qty"] / df_disp["genuine_qty"]
    df_disp["severity"] = df_disp["displacement_ratio"].apply(
        lambda r: "🔴 Displaced (>5x)" if r > 5 else (
            "🟠 Dominant (>1x)" if r > 1 else (
                "🟡 Parity (0.5-1x)" if r >= 0.5 else "🟢 Genuine leads"
            )
        )
    )
    df_disp = df_disp.sort_values("displacement_ratio", ascending=False)

    c1, c2, c3 = st.columns(3)
    c1.metric("Pairs with BVP>Genuine", f"{(df_disp['displacement_ratio'] > 1).sum():,}")
    c2.metric("Pairs at parity (0.5–1x)", f"{((df_disp['displacement_ratio'] >= 0.5) & (df_disp['displacement_ratio'] <= 1)).sum():,}")
    c3.metric("Max displacement ratio", f"{df_disp['displacement_ratio'].max():.1f}x")

    fig = px.histogram(
        df_disp,
        x="displacement_ratio",
        nbins=40,
        color_discrete_sequence=[ISZE_BLUE],
        labels={"displacement_ratio": "BVP qty ÷ Genuine qty"},
    )
    fig.add_vline(x=1, line_dash="dash", line_color="#C62828",
                  annotation_text="1.0 = parity", annotation_position="top right")
    fig.update_layout(
        **PLOTLY_BASE, height=300,
        xaxis_title="Displacement ratio (BVP ÷ genuine)",
        yaxis_title="Pair count",
        margin=dict(l=10, r=40, t=30, b=30),
    )
    st.plotly_chart(fig, width='stretch')

    st.markdown("#### Top displaced pairs (BVP outselling genuine)")
    show_cols = ["distributor_code", "xref_genuine_pn", "xref_bvp_pn",
                 "displacement_ratio", "genuine_qty", "bvp_qty", "severity"]
    if "product_subgroup" in df_disp.columns:
        show_cols.insert(1, "product_subgroup")
    tbl = df_disp[[c for c in show_cols if c in df_disp.columns]].head(50).copy()
    if "product_subgroup" in tbl.columns:
        tbl["product_subgroup"] = tbl["product_subgroup"].map(subgroup_label)
    tbl["displacement_ratio"] = tbl["displacement_ratio"].apply(lambda v: f"{v:.2f}x")
    st.dataframe(tbl, width='stretch', hide_index=True)


def render_seasonal_pattern(df_pms_monthly: pd.DataFrame) -> None:
    st.markdown("#### 📅 Seasonal Demand Pattern by PMS Category")
    st.caption(
        "**Monthly PMS parts sold across all distributors, averaged across years.** "
        "| Shows which parts peak in which months — use to time campaigns correctly. "
        "| April–June: spring service season. September–October: pre-winter brakes. "
        "| Jan/Aug/Dec: typical low seasons (holidays, end-year slowdown)."
    )

    if df_pms_monthly.empty:
        st.info("No monthly PMS data available.")
        return

    df_pms_monthly = df_pms_monthly.copy()
    df_pms_monthly["category_label"] = df_pms_monthly["pms_category"].map(CATEGORY_LABELS).fillna(df_pms_monthly["pms_category"])

    yr_seas = st.multiselect(
        "Filter years",
        sorted(df_pms_monthly["year_value"].unique()),
        default=sorted(df_pms_monthly["year_value"].unique()),
        key="seas_yr",
    )
    df_seas = df_pms_monthly[df_pms_monthly["year_value"].isin(yr_seas)].copy() if yr_seas else df_pms_monthly.copy()

    df_avg = df_seas.groupby(["month", "pms_category", "category_label"]).agg(
        avg_qty=("qty", "mean"),
        avg_rev=("revenue_eur", "mean"),
    ).reset_index()

    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
    }
    df_avg["month_name"] = df_avg["month"].map(month_names)

    metric = st.radio("Show", ["Avg qty", "Avg revenue (€)"], horizontal=True, key="seas_metric")
    y_col = "avg_qty" if metric == "Avg qty" else "avg_rev"

    fig = px.bar(
        df_avg.sort_values("month"),
        x="month_name",
        y=y_col,
        color="category_label",
        barmode="group",
        category_orders={"month_name": list(month_names.values())},
        labels={"month_name": "Month", y_col: metric, "category_label": "Category"},
        color_discrete_sequence=PALETTE,
    )
    for m_start, m_end, label, col in [
        (4, 6, "Spring into Service", "rgba(46,125,50,0.12)"),
        (9, 10, "Brakes & Safety", "rgba(200,98,40,0.12)"),
    ]:
        fig.add_vrect(
            x0=month_names[m_start], x1=month_names[m_end],
            fillcolor=col, line_width=0,
            annotation_text=label, annotation_position="top left",
        )
    fig.update_layout(
        **PLOTLY_BASE, height=430,
        legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig, width='stretch')


def render_pareto(df_sales: pd.DataFrame, dist_sel: list[str], year_type: str) -> None:
    st.markdown("#### 📊 Revenue Concentration — Pareto Analysis")
    st.caption(
        "**Shows what share of total revenue comes from the top N% of SKUs.** "
        "| Typical result: top 20% of SKUs = 70–80% of revenue (Pareto principle). "
        "| A very steep curve = high concentration risk. If a competitor targets your top 10 SKUs, "
        "what share of revenue is at risk? "
        "| PMS parts highlighted — these are the most defensible (branded + service-driven demand)."
    )

    col_y = "fiscal_year" if year_type == "fiscal" else "year"
    if col_y not in df_sales.columns:
        st.info("Year column not found in sales data.")
        return

    available_yr = sorted(df_sales[col_y].dropna().unique().astype(int).tolist(), reverse=True)
    yr_pareto = st.selectbox("Year", available_yr, key="pareto_yr2")
    df_p = df_sales[df_sales[col_y] == yr_pareto].copy()
    if dist_sel:
        df_p = df_p[df_p["distributor_code"].isin(dist_sel)].copy()

    df_p_class = classify_pms_sales(df_p)
    sku_agg = (
        df_p_class.groupby(["part_number", "is_pms"])
        .agg(revenue=("net_sales_value", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    sku_agg = sku_agg[sku_agg["revenue"] > 0].reset_index(drop=True)

    if sku_agg.empty:
        st.info("No revenue data for this selection.")
        return

    total_rev = sku_agg["revenue"].sum()
    sku_agg["cum_pct"] = sku_agg["revenue"].cumsum() / total_rev
    sku_agg["sku_pct"] = (sku_agg.index + 1) / len(sku_agg)

    c1, c2, c3 = st.columns(3)
    top20_rev = sku_agg[sku_agg["sku_pct"] <= 0.20]["revenue"].sum() / total_rev
    top10_rev = sku_agg[sku_agg["sku_pct"] <= 0.10]["revenue"].sum() / total_rev
    pms_rev = sku_agg[sku_agg["is_pms"] == True]["revenue"].sum() / total_rev  # noqa: E712
    c1.metric("Top 10% SKUs = % of revenue", f"{top10_rev*100:.0f}%")
    c2.metric("Top 20% SKUs = % of revenue", f"{top20_rev*100:.0f}%")
    c3.metric("PMS parts = % of revenue", f"{pms_rev*100:.0f}%")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sku_agg["sku_pct"] * 100,
        y=sku_agg["cum_pct"] * 100,
        mode="lines",
        name="All SKUs",
        line=dict(color=ISZE_BLUE, width=2),
    ))
    pms_mask = sku_agg["is_pms"] == True  # noqa: E712
    fig.add_trace(go.Scatter(
        x=sku_agg[pms_mask]["sku_pct"] * 100,
        y=sku_agg[pms_mask]["cum_pct"] * 100,
        mode="markers",
        name="PMS parts",
        marker=dict(color=ISZE_ORANGE, size=6, symbol="circle"),
    ))
    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                  line=dict(dash="dash", color="#CCCCCC"))
    fig.add_vline(x=20, line_dash="dot", line_color="#999",
                  annotation_text="Top 20% of SKUs", annotation_position="top right")
    fig.update_layout(
        **PLOTLY_BASE, height=450,
        xaxis_title="% of SKUs (ranked by revenue)",
        yaxis_title="% of cumulative revenue",
        xaxis=dict(ticksuffix="%", gridcolor="#F0F0F0"),
        yaxis=dict(ticksuffix="%", gridcolor="#F0F0F0"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(fig, width='stretch')
