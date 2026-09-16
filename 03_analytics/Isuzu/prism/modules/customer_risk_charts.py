"""Customer aftersales-risk ranking renderers.

Extracted from pages/15_Customer_Risk.py (docs/DASHBOARD_IA.md §6 P2). The
Ranking/Breakdown/Map views feed Network Intelligence tab 1 ("Most exposed");
the aftermarket-scrape view moves to the internal shelf under Tools — both
land there in a later phase. No visual changes from the original page.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
ISZE_RED = "#E2231A"
ISZE_GREY = "#9AA0A6"
from modules.plotly_style import style

# Default weights -- mirror build_db_aftersales_risk.py
DEFAULT_W = {"eucon": 0.35, "aim": 0.25, "contested": 0.25, "vor": 0.15}
STREET_FACTOR = 1.785  # list x1.40 (DB) x1.275 (dealer)


def compute_risk_scores(df: pd.DataFrame, w: dict[str, float]) -> pd.DataFrame:
    """Recompute risk_score + component contributions from normalised weights."""
    df = df.copy()
    df["comp_eucon"] = 100 * w["eucon"] * df["n_eucon"]
    df["comp_aim"] = 100 * w["aim"] * df["n_aim"]
    df["comp_contested"] = 100 * w["contested"] * df["n_contested"]
    df["comp_vor"] = 100 * w["vor"] * df["n_vor"]
    df["risk_score"] = df["comp_eucon"] + df["comp_aim"] + df["comp_contested"] + df["comp_vor"]
    df = df.sort_values("risk_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


def render_ranking_table(df: pd.DataFrame) -> None:
    show = df[[
        "rank", "distributor_code", "risk_score", "net_sales_eur",
        "eucon_undercut_pct", "high_risk_rev_pct", "contested_bvp_capture", "vor_urgent_share",
        "eucon_undercut_rev_eur", "high_risk_rev_eur", "contested_eur",
    ]].copy()
    rename = {
        "rank": "#", "distributor_code": "Distributor", "risk_score": "Risk score",
        "net_sales_eur": "Net sales EUR", "eucon_undercut_pct": "Eucon undercut %",
        "high_risk_rev_pct": "AIM high-risk %", "contested_bvp_capture": "BVP capture %",
        "vor_urgent_share": "VOR/urgent %", "eucon_undercut_rev_eur": "Eucon undercut EUR",
        "high_risk_rev_eur": "AIM high-risk EUR", "contested_eur": "Contested EUR",
    }
    show = show.rename(columns=rename)

    raw_score = show["Risk score"].copy()

    def _hi(row):
        styles = [""] * len(row)
        idx = row.index.get_loc("Risk score")
        v = raw_score.iloc[row.name]
        if v >= 55:
            styles[idx] = "background-color:#FFCDD2"
        elif v >= 35:
            styles[idx] = "background-color:#FFF9C4"
        else:
            styles[idx] = "background-color:#C8E6C9"
        return styles

    st.dataframe(
        show.style.apply(_hi, axis=1).format({
            "Risk score": "{:.1f}",
            "Net sales EUR": "EUR {:,.0f}", "Eucon undercut EUR": "EUR {:,.0f}",
            "AIM high-risk EUR": "EUR {:,.0f}", "Contested EUR": "EUR {:,.0f}",
            "Eucon undercut %": "{:.1%}", "AIM high-risk %": "{:.2%}",
            "BVP capture %": "{:.1%}", "VOR/urgent %": "{:.1%}",
        }),
        width="stretch", hide_index=True, height=560,
    )


def render_signal_breakdown(df: pd.DataFrame) -> None:
    st.markdown("**What drives each distributor's score** - stacked weighted contributions.")
    bd = df.sort_values("risk_score", ascending=True)
    fig = go.Figure()
    parts = [
        ("comp_eucon", "Eucon price (ref. sell-out)", ISZE_RED),
        ("comp_aim", "AIM scraper", ISZE_ORANGE),
        ("comp_contested", "BVP capture", ISZE_BLUE),
        ("comp_vor", "VOR/urgent", ISZE_GREY),
    ]
    for col, label, color in parts:
        fig.add_trace(go.Bar(
            y=bd["distributor_code"], x=bd[col], name=label, orientation="h",
            marker_color=color, hovertemplate=f"%{{y}}<br>{label}: %{{x:.1f}}<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack", template="plotly_white", font=dict(family="Segoe UI"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFC",
        height=max(420, 26 * len(bd)), xaxis_title="Weighted risk contribution (sum = score)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(style(fig), width="stretch")


def render_threat_map(df: pd.DataFrame) -> None:
    st.markdown(
        "**External walk-out vs internal down-trade.** X = Eucon undercut share vs reference sell-out "
        "(price-driven loss to named aftermarket). Y = BVP capture of contested demand "
        "(loss one tier down to our own value line). Bubble = net sales. "
        "**Top-right = fighting on both fronts.**"
    )
    mp = df.copy()
    fig2 = px.scatter(
        mp, x="eucon_undercut_pct", y="contested_bvp_capture",
        size="net_sales_eur", color="risk_score",
        color_continuous_scale=["#C8E6C9", "#FFF9C4", "#E2231A"],
        hover_name="distributor_code", size_max=55,
        labels={
            "eucon_undercut_pct": "Eucon undercut share vs reference sell-out",
            "contested_bvp_capture": "BVP capture of contested demand",
            "risk_score": "Risk score",
        },
    )
    fig2.update_traces(
        text=mp["distributor_code"], textposition="top center",
        mode="markers+text", textfont=dict(size=10),
    )
    med_x = mp["eucon_undercut_pct"].median()
    med_y = mp["contested_bvp_capture"].median()
    fig2.add_vline(x=med_x, line_dash="dot", line_color="#999")
    fig2.add_hline(y=med_y, line_dash="dot", line_color="#999")
    fig2.update_layout(
        template="plotly_white", font=dict(family="Segoe UI"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFC", height=560,
        xaxis_tickformat=".0%", yaxis_tickformat=".0%",
    )
    st.plotly_chart(style(fig2), width="stretch")


def load_eucon_scrape(derived_dir, street_factor: float = STREET_FACTOR) -> pd.DataFrame:
    fp = Path(derived_dir) / "eucon_price_gap.csv"
    if not fp.exists():
        return pd.DataFrame()
    e = pd.read_csv(fp)
    e["street_price"] = e["ISZE_IE40_Price_EUR"] * street_factor
    e["db_price"] = e["ISZE_IE40_Price_EUR"] * 1.40
    e["delta_vs_street"] = (e["Avg_Competitor_EUR"] - e["street_price"]) / e["street_price"]
    e["undercut_list"] = e["Avg_Competitor_EUR"] < e["ISZE_IE40_Price_EUR"]
    e["undercut_street"] = e["Avg_Competitor_EUR"] < e["street_price"]
    return e


def render_aftermarket_scrape(eu: pd.DataFrame, street_factor: float = STREET_FACTOR) -> None:
    if eu.empty:
        st.warning("`eucon_price_gap.csv` not found - run the Eucon scrape pipeline.")
        return

    u = eu[eu["undercut_street"]].copy()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Benchmarked PNs", f"{len(eu)}")
    s2.metric("Undercut at LIST", f"{int(eu['undercut_list'].sum())}", "IE40 view")
    s3.metric("Undercut at reference sell-out", f"{int(eu['undercut_street'].sum())}",
              f"+{int(eu['undercut_street'].sum() - eu['undercut_list'].sum())} vs list")
    s4.metric("Rev on undercut PNs (ref. sell-out)", f"EUR {u['rev_eur'].sum():,.0f}")

    st.info(
        "**We sit upstream.** At IE40 list the aftermarket undercuts "
        f"**{int(eu['undercut_list'].sum())}/{len(eu)}** parts. Gross the genuine price up "
        f"through the channel to the counter (x{street_factor}) and that jumps to "
        f"**{int(eu['undercut_street'].sum())}/{len(eu)}** - the price gap is real where the "
        "customer actually buys, not where we invoice."
    )

    # --- Brand leaderboard: who attacks us, on how many street-undercut PNs
    st.markdown("##### Who undercuts us - aftermarket brand leaderboard")
    br = u.assign(brand=u["Brands_Found"].fillna("").str.split(",")).explode("brand")
    br["brand"] = br["brand"].str.strip()
    br = br[br["brand"] != ""]
    lead = (
        br.groupby("brand")
        .agg(pns=("pn", "nunique"), rev=("rev_eur", "sum"))
        .sort_values("pns", ascending=True)
        .reset_index()
    )
    figb = go.Figure(go.Bar(
        y=lead["brand"], x=lead["pns"], orientation="h", marker_color=ISZE_ORANGE,
        customdata=lead["rev"],
        hovertemplate="%{y}<br>%{x} PNs undercut<br>ISZE rev on those PNs: EUR %{customdata:,.0f}<extra></extra>",
    ))
    figb.update_layout(
        template="plotly_white", font=dict(family="Segoe UI"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFC",
        height=max(360, 22 * len(lead)), xaxis_title="ISZE PNs undercut at reference sell-out",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(style(figb), width="stretch")

    # --- Price position scatter (street-based)
    st.markdown("##### Price position - revenue vs gap to reference sell-out")
    sc = u.dropna(subset=["rev_eur", "delta_vs_street"]).copy()
    sc["arena"] = sc["contested"].map(lambda c: "Contested (BVP pair)" if c else "No BVP pair")
    figs = px.scatter(
        sc, x="rev_eur", y="delta_vs_street", size="rev_eur", color="arena",
        color_discrete_map={"Contested (BVP pair)": ISZE_RED, "No BVP pair": ISZE_BLUE},
        hover_name="description", size_max=48,
        labels={"rev_eur": "ISZE revenue on part (EUR)",
                "delta_vs_street": "AM avg vs reference sell-out (- = cheaper)"},
    )
    figs.update_layout(
        template="plotly_white", font=dict(family="Segoe UI"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFC", height=460,
        yaxis_tickformat=".0%",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    figs.add_hline(y=0, line_dash="dash", line_color="#555")
    st.plotly_chart(style(figs), width="stretch")

    # --- Detail table
    st.markdown("##### Undercut parts (reference sell-out) - the defend list")
    det = u.sort_values("rev_eur", ascending=False)[[
        "pn", "description", "rev_eur", "ISZE_IE40_Price_EUR", "db_price",
        "street_price", "Min_Competitor_EUR", "Avg_Competitor_EUR",
        "delta_vs_street", "Competitor_Count", "Brands_Found", "Countries_Found",
    ]].rename(columns={
        "pn": "Part", "description": "Description", "rev_eur": "ISZE rev",
        "ISZE_IE40_Price_EUR": "List", "db_price": "+DB 40%", "street_price": "Ref. sell-out",
        "Min_Competitor_EUR": "AM min", "Avg_Competitor_EUR": "AM avg",
        "delta_vs_street": "AM vs ref. sell-out", "Competitor_Count": "# offers",
        "Brands_Found": "Brands", "Countries_Found": "Countries",
    })
    det["AM vs ref. sell-out"] = det["AM vs ref. sell-out"] * 100
    st.dataframe(
        det, width="stretch", hide_index=True, height=420,
        column_config={
            "ISZE rev": st.column_config.NumberColumn(format="EUR %.0f"),
            "List": st.column_config.NumberColumn(format="EUR %.2f"),
            "+DB 40%": st.column_config.NumberColumn(format="EUR %.2f"),
            "Ref. sell-out": st.column_config.NumberColumn(format="EUR %.2f"),
            "AM min": st.column_config.NumberColumn(format="EUR %.2f"),
            "AM avg": st.column_config.NumberColumn(format="EUR %.2f"),
            "AM vs ref. sell-out": st.column_config.NumberColumn(format="%.0f%%"),
        },
    )
    st.caption(
        "Eucon/AutoDoc aftermarket trade benchmark. 'AM vs ref. sell-out' negative = aftermarket "
        "cheaper than genuine at the counter. Revenue per brand double-counts across brands "
        "(multiple brands per PN) - use # PNs as the primary attack measure."
    )
