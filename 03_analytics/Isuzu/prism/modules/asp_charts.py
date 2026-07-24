"""ASP (average selling price) deviation-from-network-median renderers.

Extracted from pages/8_ASP_Monitor.py (docs/DASHBOARD_IA.md §6 P2) so the
same views can be reused from Network Intelligence's "Pricing & competition"
tab without duplicating the page. No visual changes from the original page.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"

FLAG_COLORS = {
    "alert": "#FFCDD2",
    "watch": "#FFF9C4",
    "premium": "#BBDEFB",
    "ok": "#C8E6C9",
}
FLAG_TEXT = {
    "alert": "#C62828",
    "watch": "#F57F17",
    "premium": "#1565C0",
    "ok": "#2E7D32",
}


def compute_asp_deviation(df: pd.DataFrame, yr: int) -> pd.DataFrame:
    """Per-distributor ASP deviation from the network median, by PMS category."""
    sub = df[df["year"] == yr].copy()
    if sub.empty:
        return pd.DataFrame()
    network_med = (
        sub.groupby("pms_category")["avg_sp_eur"]
        .median()
        .rename("network_median_asp")
    )
    sub = sub.join(network_med, on="pms_category")
    sub["asp_deviation_pct"] = (
        (sub["avg_sp_eur"] - sub["network_median_asp"]) / sub["network_median_asp"]
    )

    def _flag(v: float) -> str:
        if pd.isna(v):
            return "ok"
        if v < -0.20:
            return "alert"
        if v < -0.10:
            return "watch"
        if v > 0.20:
            return "premium"
        return "ok"

    sub["deviation_flag"] = sub["asp_deviation_pct"].apply(_flag)
    return sub


def render_deviation_heatmap(asp_df: pd.DataFrame, selected_year: int) -> None:
    st.subheader(f"ASP deviation from network median (%) — {selected_year}")

    if asp_df.empty:
        st.warning("No data available for the selected year.")
        return

    pivot = asp_df.pivot_table(
        index="distributor_code",
        columns="pms_category",
        values="asp_deviation_pct",
        aggfunc="mean",
    )
    if pivot.empty:
        return

    z = pivot.values * 100  # convert to %
    annot = [[f"{v:.1f}%" if not pd.isna(v) else "" for v in row] for row in z]

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=z,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale="RdBu",
            zmid=0,
            text=annot,
            texttemplate="%{text}",
            textfont={"size": 9},
            colorbar=dict(title="Dev %", ticksuffix="%"),
            hoverongaps=False,
            hovertemplate="Distributor: %{y}<br>Category: %{x}<br>Deviation: %{z:.1f}%<extra></extra>",
        )
    )
    fig_heat.update_layout(
        template="plotly_white",
        font=dict(family="Segoe UI"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FAFBFC",
        height=max(300, len(pivot.index) * 28 + 120),
        margin=dict(l=100, r=40, t=40, b=100),
        xaxis=dict(tickangle=-40),
    )
    st.plotly_chart(fig_heat, width='stretch')


def render_alert_table(asp_df: pd.DataFrame, threshold_pct: int, selected_year: int) -> None:
    threshold = threshold_pct / 100.0
    st.subheader(f"Alert table — deviation > {threshold_pct}%")

    if asp_df.empty:
        st.info("No data to display.")
        return

    alert_df = asp_df[asp_df["asp_deviation_pct"].abs() > threshold].copy()
    alert_df = alert_df.sort_values("asp_deviation_pct", ascending=True)

    if alert_df.empty:
        st.success(f"No distributors exceed the {threshold_pct}% deviation threshold for {selected_year}.")
        return

    alert_display = alert_df[
        ["distributor_code", "pms_category", "year", "avg_sp_eur",
         "network_median_asp", "asp_deviation_pct", "deviation_flag"]
    ].copy()
    alert_display = alert_display.rename(
        columns={
            "distributor_code": "Distributor",
            "pms_category": "Category",
            "year": "Year",
            "avg_sp_eur": "Distributor ASP (€)",
            "network_median_asp": "Network median (€)",
            "asp_deviation_pct": "Deviation %",
            "deviation_flag": "Flag",
        }
    )

    raw_dev = alert_display["Deviation %"].copy().reset_index(drop=True)
    raw_flag = alert_display["Flag"].copy().reset_index(drop=True)

    alert_display["Distributor ASP (€)"] = alert_display["Distributor ASP (€)"].apply(
        lambda v: f"€{v:,.2f}" if pd.notna(v) else "—"
    )
    alert_display["Network median (€)"] = alert_display["Network median (€)"].apply(
        lambda v: f"€{v:,.2f}" if pd.notna(v) else "—"
    )
    alert_display["Deviation %"] = raw_dev.apply(
        lambda v: f"{v * 100:+.1f}%" if pd.notna(v) else "—"
    )

    alert_display = alert_display.reset_index(drop=True)

    def _style_alert(row):
        styles = [""] * len(row)
        if "Flag" in row.index:
            flag_idx = row.index.get_loc("Flag")
            try:
                flag = raw_flag.iloc[row.name]
            except Exception:
                flag = "ok"
            bg = FLAG_COLORS.get(flag, "")
            styles[flag_idx] = f"background-color: {bg}"
        return styles

    st.dataframe(
        alert_display.style.apply(_style_alert, axis=1),
        width='stretch',
        hide_index=True,
    )

    st.download_button(
        label=f"Download ISZE_ASP_Alerts_{selected_year}.csv",
        data=alert_df.to_csv(index=False).encode("utf-8"),
        file_name=f"ISZE_ASP_Alerts_{selected_year}.csv",
        mime="text/csv",
    )


def render_distributor_drilldown(
    asp_df: pd.DataFrame, opp_dists: list[str], selected_year: int, key: str = "drill_dist",
) -> None:
    st.subheader("Distributor drill-down")

    if asp_df.empty:
        return

    default_drill = "ITUK" if "ITUK" in opp_dists else (opp_dists[0] if opp_dists else None)
    drill_dist = st.selectbox(
        "Select distributor",
        options=opp_dists,
        index=opp_dists.index(default_drill) if default_drill in opp_dists else 0,
        key=key,
    )

    drill_df = asp_df[asp_df["distributor_code"] == drill_dist].copy()

    if drill_df.empty:
        st.info(f"No data for {drill_dist} in {selected_year}.")
        return

    drill_df = drill_df.sort_values("asp_deviation_pct", ascending=True)
    drill_df["dev_pct_display"] = drill_df["asp_deviation_pct"] * 100
    bar_colors = [FLAG_COLORS.get(f, ISZE_BLUE) for f in drill_df["deviation_flag"]]

    fig_drill = go.Figure()
    fig_drill.add_trace(
        go.Bar(
            x=drill_df["pms_category"],
            y=drill_df["dev_pct_display"],
            marker_color=bar_colors,
            hovertemplate="%{x}<br>%{y:+.1f}%<extra></extra>",
            name="ASP deviation",
        )
    )
    fig_drill.add_hline(y=0, line_color="#333333", line_width=1.5)
    fig_drill.update_layout(
        title=f"ASP deviation by category — {drill_dist} · {selected_year}",
        xaxis_title="PMS category",
        yaxis_title="ASP deviation %",
        yaxis_ticksuffix="%",
        template="plotly_white",
        font=dict(family="Segoe UI"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FAFBFC",
        showlegend=False,
        height=380,
    )
    st.plotly_chart(fig_drill, width='stretch')
