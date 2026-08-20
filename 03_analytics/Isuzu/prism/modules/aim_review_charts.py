"""AIM pricing-risk exposure renderers.

Extracted from pages/7_AIM_Review.py (docs/DASHBOARD_IA.md §6 P2) so Network
Intelligence's "Pricing & competition" tab can reuse Network Overview /
Family Detail without duplicating the page. No visual changes from the
original page. (Two dead helpers from the source page — _rag_color and
_style_high_risk_pct, superseded by the inline _highlight_risk/_highlight_fam_risk
closures below — were dropped as unused.)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
from modules.plotly_style import style


def render_network_overview(
    aim_db: pd.DataFrame, selected_year: int, dist_multi: list[str], aim_dists: list[str],
) -> None:
    filtered_db = aim_db[
        (aim_db["year"] == selected_year)
        & (aim_db["distributor_code"].isin(dist_multi if dist_multi else aim_dists))
    ].copy()

    if filtered_db.empty:
        st.warning("No data for the selected filters.")
        return

    display_cols = {
        "distributor_code": "Distributor",
        "year": "Year",
        "net_sales_eur": "Net sales (€)",
        "aim_match_rate_rev": "AIM match rate",
        "high_risk_rev_eur": "High-risk rev (€)",
        "high_risk_rev_pct": "High-risk %",
        "strategic_rev_eur": "Strategic rev (€)",
    }

    network_mean_pct = aim_db[aim_db["year"] == selected_year]["high_risk_rev_pct"].mean()

    table_df = filtered_db[list(display_cols.keys())].copy()

    if "high_risk_rev_pct" in table_df.columns:
        table_df["vs_network_pp"] = (
            (table_df["high_risk_rev_pct"] - network_mean_pct) * 100
        ).round(1)

    table_df = table_df.sort_values("high_risk_rev_eur", ascending=False)

    rename_map = dict(display_cols)
    rename_map["vs_network_pp"] = "vs network (pp)"
    table_df = table_df.rename(columns=rename_map)

    def _fmt_table(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for col in ["Net sales (€)", "High-risk rev (€)", "Strategic rev (€)"]:
            if col in out.columns:
                out[col] = out[col].apply(
                    lambda v: f"€{int(round(v)):,}" if pd.notna(v) else "—"
                )
        if "AIM match rate" in out.columns:
            out["AIM match rate"] = out["AIM match rate"].apply(
                lambda v: f"{v * 100:.1f}%" if pd.notna(v) else "—"
            )
        return out

    raw_pct = table_df["High-risk %"].copy() if "High-risk %" in table_df.columns else None

    fmt_df = _fmt_table(table_df.copy())

    if "High-risk %" in fmt_df.columns and raw_pct is not None:
        fmt_df["High-risk %"] = raw_pct.apply(
            lambda v: f"{v * 100:.1f}%" if pd.notna(v) else "—"
        )

    def _highlight_risk(row):
        styles = [""] * len(row)
        if "High-risk %" in row.index:
            idx = row.index.get_loc("High-risk %")
            try:
                raw_val = raw_pct.iloc[row.name] if raw_pct is not None else None
            except Exception:
                raw_val = None
            if raw_val is not None and pd.notna(raw_val):
                if raw_val < 0.05:
                    styles[idx] = "background-color: #C8E6C9"
                elif raw_val <= 0.15:
                    styles[idx] = "background-color: #FFF9C4"
                else:
                    styles[idx] = "background-color: #FFCDD2"
        return styles

    fmt_df = fmt_df.reset_index(drop=True)
    if raw_pct is not None:
        raw_pct = raw_pct.reset_index(drop=True)

    styled = fmt_df.style.apply(_highlight_risk, axis=1)
    st.dataframe(styled, width='stretch', hide_index=True)

    st.markdown("---")

    chart_df = aim_db[
        (aim_db["year"] == selected_year)
        & (~aim_db["high_risk_rev_pct"].isna())
    ].copy()
    chart_df = chart_df.sort_values("high_risk_rev_pct", ascending=False)

    if chart_df.empty:
        return

    is_subset = len(dist_multi) < len(aim_dists) and len(dist_multi) > 0
    bar_colors = [
        ISZE_ORANGE if (is_subset and d in dist_multi) else ISZE_BLUE
        for d in chart_df["distributor_code"]
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=chart_df["distributor_code"],
            y=chart_df["high_risk_rev_pct"] * 100,
            marker_color=bar_colors,
            name="High-risk %",
            hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.add_hline(
        y=network_mean_pct * 100,
        line_dash="dash",
        line_color="#555555",
        annotation_text=f"Network mean: {network_mean_pct * 100:.1f}%",
        annotation_position="top right",
    )
    fig.update_layout(
        title=f"High-risk revenue % by distributor — {selected_year}",
        xaxis_title="Distributor",
        yaxis_title="High-risk rev %",
        yaxis_ticksuffix="%",
        template="plotly_white",
        font=dict(family="Segoe UI"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FAFBFC",
        showlegend=False,
        height=380,
    )
    st.plotly_chart(style(fig), width='stretch')


def render_family_detail(aim_family: pd.DataFrame, selected_year: int, key: str = "fam_dist_sel") -> None:
    if aim_family.empty:
        st.warning("AIM family-level data not available.")
        return

    fam_dists = sorted(aim_family["distributor_code"].dropna().unique().tolist())
    default_fam_dist = "ITUK" if "ITUK" in fam_dists else (fam_dists[0] if fam_dists else None)
    fam_dist_sel = st.selectbox(
        "Distributor",
        options=fam_dists,
        index=fam_dists.index(default_fam_dist) if default_fam_dist in fam_dists else 0,
        key=key,
    )

    fam_df = aim_family[
        (aim_family["distributor_code"] == fam_dist_sel)
        & (aim_family["year"] == selected_year)
    ].copy()

    if fam_df.empty:
        st.warning(f"No family-level AIM data for {fam_dist_sel} in {selected_year}.")
        return

    fam_df = fam_df.sort_values("aim_high_risk_rev_eur", ascending=False)

    tbl_cols = {
        "product_family": "Product family",
        "aim_l1_hints": "AIM hints",
        "catalog_sales_eur": "Catalog sales (€)",
        "aim_high_risk_rev_eur": "High-risk rev (€)",
        "aim_high_risk_rev_pct": "High-risk %",
        "vs_network_risk_pp": "vs network median (pp)",
        "bvp_share_eur": "BVP share (€%)",
    }

    disp_fam = fam_df[[c for c in tbl_cols if c in fam_df.columns]].copy()
    disp_fam = disp_fam.rename(columns=tbl_cols)

    raw_risk_pct = (
        disp_fam["High-risk %"].copy() if "High-risk %" in disp_fam.columns else None
    )

    for col in ["Catalog sales (€)", "High-risk rev (€)"]:
        if col in disp_fam.columns:
            disp_fam[col] = disp_fam[col].apply(
                lambda v: f"€{int(round(v)):,}" if pd.notna(v) else "—"
            )
    for col in ["High-risk %", "BVP share (€%)"]:
        if col in disp_fam.columns:
            disp_fam[col] = disp_fam[col].apply(
                lambda v: f"{v * 100:.1f}%" if pd.notna(v) else "—"
            )
    if "vs network median (pp)" in disp_fam.columns:
        disp_fam["vs network median (pp)"] = disp_fam["vs network median (pp)"].apply(
            lambda v: f"{v:+.1f}pp" if pd.notna(v) else "—"
        )

    disp_fam = disp_fam.reset_index(drop=True)
    if raw_risk_pct is not None:
        raw_risk_pct = raw_risk_pct.reset_index(drop=True)

    def _highlight_fam_risk(row):
        styles = [""] * len(row)
        if "High-risk %" in row.index:
            idx = row.index.get_loc("High-risk %")
            try:
                raw_val = raw_risk_pct.iloc[row.name] if raw_risk_pct is not None else None
            except Exception:
                raw_val = None
            if raw_val is not None and pd.notna(raw_val):
                if raw_val < 0.05:
                    styles[idx] = "background-color: #C8E6C9"
                elif raw_val <= 0.15:
                    styles[idx] = "background-color: #FFF9C4"
                else:
                    styles[idx] = "background-color: #FFCDD2"
        return styles

    st.dataframe(
        disp_fam.style.apply(_highlight_fam_risk, axis=1),
        width='stretch',
        hide_index=True,
    )

    st.markdown("---")

    scatter_df = fam_df.dropna(
        subset=["catalog_sales_eur", "aim_high_risk_rev_pct", "aim_high_risk_rev_eur"]
    ).copy()
    if scatter_df.empty:
        return

    scatter_df["aim_high_risk_rev_pct_display"] = scatter_df["aim_high_risk_rev_pct"] * 100
    scatter_df["hover_text"] = (
        scatter_df["product_family"].fillna("")
        + "<br>"
        + scatter_df.get("aim_l1_hints", pd.Series("", index=scatter_df.index)).fillna("")
    )
    fig2 = px.scatter(
        scatter_df,
        x="catalog_sales_eur",
        y="aim_high_risk_rev_pct_display",
        size="aim_high_risk_rev_eur",
        color="vs_network_risk_pp",
        color_continuous_scale=px.colors.diverging.RdBu_r,
        color_continuous_midpoint=0,
        hover_name="product_family",
        hover_data={"aim_l1_hints": True, "aim_high_risk_rev_pct_display": ":.1f"},
        labels={
            "catalog_sales_eur": "Catalog sales (€)",
            "aim_high_risk_rev_pct_display": "High-risk rev %",
            "vs_network_risk_pp": "vs network (pp)",
        },
        title=f"AIM risk by product family — {fam_dist_sel} · {selected_year}",
    )
    fig2.update_layout(
        template="plotly_white",
        font=dict(family="Segoe UI"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FAFBFC",
        height=420,
    )
    st.plotly_chart(style(fig2), width='stretch')


def render_gap_closer(derived_dir) -> None:
    gap_files = sorted(Path(derived_dir).glob("aim_gap_suggestions_*.csv"))
    if not gap_files:
        st.info(
            "No gap-closer output found. Run "
            "`python Tools/autodoc_scraper/aim_gap_closer.py` to generate "
            "`aim_gap_suggestions_YYYYMMDD.csv`."
        )
        return

    latest = gap_files[-1]
    gap_df = pd.read_csv(latest)
    st.caption(f"Source: `{latest.name}` · {len(gap_df):,} unclassified revenue-bearing PNs")

    total_rev = gap_df["revenue_cy25_eur"].sum()
    high_conf = gap_df[gap_df["confidence"] >= 3.0]
    high_conf_rev = high_conf["revenue_cy25_eur"].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Unclassified PNs", f"{len(gap_df):,}")
    m2.metric("CY2025 revenue", f"€{total_rev:,.0f}")
    m3.metric("Auto-classifiable", f"{len(high_conf):,}", "conf ≥ 3.0")
    m4.metric("Auto-class revenue", f"€{high_conf_rev:,.0f}", f"{high_conf_rev/total_rev*100:.0f}% of gap")

    st.markdown("---")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        l1_options = ["(all)"] + sorted(gap_df["sug1_l1"].dropna().unique().tolist())
        l1_filter = st.selectbox("Suggested L1", options=l1_options, index=0)
    with c2:
        min_conf = st.slider("Min confidence", 0.0, 10.0, 0.0, 0.5)
    with c3:
        min_rev = st.number_input("Min revenue €", min_value=0, value=0, step=500)

    view = gap_df.copy()
    if l1_filter != "(all)":
        view = view[view["sug1_l1"] == l1_filter]
    view = view[view["confidence"] >= min_conf]
    view = view[view["revenue_cy25_eur"] >= min_rev]
    view = view.sort_values("revenue_cy25_eur", ascending=False).reset_index(drop=True)

    st.caption(
        f"Showing {len(view):,} of {len(gap_df):,} rows · "
        f"€{view['revenue_cy25_eur'].sum():,.0f} revenue in view"
    )

    display_cols = [
        "pn", "description", "price_eur", "revenue_cy25_eur",
        "sug1_l1", "sug1_l2", "sug1_combined", "confidence",
        "sug2_l1", "sug2_l2", "eq_hit", "validated",
    ]
    display_cols = [c for c in display_cols if c in view.columns]
    st.dataframe(
        view[display_cols],
        width='stretch',
        hide_index=True,
        column_config={
            "revenue_cy25_eur": st.column_config.NumberColumn("Revenue (€)", format="€%.0f"),
            "price_eur": st.column_config.NumberColumn("Price (€)", format="€%.2f"),
            "sug1_combined": st.column_config.NumberColumn("Score", format="%.3f"),
            "confidence": st.column_config.NumberColumn("Conf", format="%.2f"),
        },
        height=520,
    )

    st.download_button(
        label=f"Download {latest.stem}_filtered.csv",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name=f"{latest.stem}_filtered.csv",
        mime="text/csv",
    )
