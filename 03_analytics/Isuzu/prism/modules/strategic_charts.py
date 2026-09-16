"""Streamlit chart renderers for Strategic Views (15 dashboards)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.bvp_dashboard_data import fmt_eur, fmt_pct

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"

from modules.plotly_style import BASE_LAYOUT as PLOTLY

LIFECYCLE_COLORS = {
    "emerging": "#2E7D32",
    "growing": "#43A047",
    "mature": "#1B3A6B",
    "declining": "#E87722",
    "zombie": "#C62828",
}


def _years(df: pd.DataFrame, year_sel: list[int]) -> pd.DataFrame:
    if df.empty or "year" not in df.columns or not year_sel:
        return df
    return df[df["year"].isin(year_sel)].copy()


def _missing(name: str) -> None:
    st.warning(f"**{name}** data not built yet. Run `python scripts/build_strategic_contracts.py`.")


# render_triple_threat removed 2026-08-20 (superseded by Early Warning; duplicate-tab trim)


def render_pms_opportunity(df: pd.DataFrame, year_sel: list[int], highlight: str, latest_y: int | None) -> None:
    if df.empty:
        _missing("PMS Opportunity Matrix")
        return
    st.markdown(
        "Capture vs **Total Addressable Market (TAM, €)** — the full € of expected "
        "service demand — by PMS category; colour = BVP share of capture (pp)."
    )
    d = _years(df, year_sel)
    y = latest_y or int(d["year"].max())
    d = d[d["year"] == y]
    if d.empty:
        st.warning("No rows for selected year.")
        return
    d = d.copy()
    # Quotable-KPI firewall (DECISIONS.md 2026-07-21): zero-actual-sales categories
    # book TAM=€0 (avg_sp=0), which plots them as "no opportunity" when the real
    # gap is unknowable. Exclude them from the TAM axis and surface the count.
    if "revenue_gap_quotable" in d.columns:
        d["_quotable"] = d["revenue_gap_quotable"].fillna(True).astype(bool)
        n_nonq = int((~d["_quotable"]).sum())
        d = d[d["_quotable"]]
        if n_nonq:
            st.caption(
                f"{n_nonq} category row(s) with zero actual sales excluded from the TAM axis "
                f"(their € gap is not quotable)."
            )
    d["highlight"] = d["distributor_code"].apply(lambda x: "★ " + x if x == highlight else x)
    fig = px.scatter(
        d,
        x="capture_rate_total",
        y="tam_eur",
        color="genuine_bvp_gap_pp",
        facet_col="pms_category",
        facet_col_wrap=3,
        hover_name="highlight",
        labels={
            "capture_rate_total": "Total capture",
            "tam_eur": "TAM (€)",
            "genuine_bvp_gap_pp": "BVP gap (pp)",
        },
        color_continuous_scale=["#1B3A6B", "#E87722"],
    )
    # Facet grid with wrap=3: give each row of subplots enough height or the
    # ~11 category facets collapse into Plotly's 450px default and become
    # unreadable (IA phase-3 merge regression).
    n_cats = d["pms_category"].nunique()
    n_rows = max(1, (n_cats + 2) // 3)
    fig.update_layout(
        **PLOTLY,
        title=f"PMS Opportunity Matrix ({y})",
        height=240 * n_rows + 80,
    )
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig, width='stretch')


def render_network_percentile(df: pd.DataFrame, year_sel: list[int], highlight: str, latest_y: int | None) -> None:
    if df.empty:
        _missing("Network Percentile")
        return
    st.markdown("Percentile rank vs network (100 = best) for five KPIs.")
    y = latest_y or int(df["year"].max())
    d = df[(df["year"] == y) & (df["distributor_code"] == highlight)]
    highlight_found = not d.empty
    if not highlight_found:
        st.caption(f"No rows for {highlight} — showing network median profile.")
        d = (
            df[df["year"] == y]
            .groupby("metric", as_index=False)["percentile_rank"]
            .median()
        )
    fig = go.Figure(
        go.Scatterpolar(
            r=d["percentile_rank"],
            theta=d["metric"],
            fill="toself",
            line_color=ISZE_ORANGE if highlight_found else ISZE_BLUE,
            name=highlight,
        )
    )
    fig.update_layout(
        **PLOTLY,
        polar=dict(radialaxis=dict(range=[0, 100], tickvals=[0, 25, 50, 75, 100])),
        title=f"Network percentile — {highlight} ({y})",
        showlegend=False,
    )
    st.plotly_chart(fig, width='stretch')
    tbl = df[df["year"] == y].pivot_table(
        index="distributor_code", columns="metric", values="percentile_rank", aggfunc="first"
    )
    st.dataframe(tbl.round(1), width='stretch')


def render_vor_airfreight(df: pd.DataFrame, year_sel: list[int], highlight: str, latest_y: int | None) -> None:
    if df.empty:
        _missing("Flying Gold / VOR risk")
        return
    y = latest_y or int(df["year"].max())
    d = df[(df["year"] == y) & (df["distributor_code"] == highlight)]
    if d.empty:
        d = _years(df, year_sel)
        d = d[d["year"] == y]
    st.markdown("VOR/urgent % vs backorder rate by product family — bubble = airfreight risk score.")
    d = d.copy()
    d["bubble_size"] = d["airfreight_risk_score"].clip(lower=0.01)
    fig = px.scatter(
        d,
        x="vor_pct",
        y="backorder_rate",
        size="bubble_size",
        color="product_family",
        hover_data=["vor_line_count", "weight_class"],
        labels={"vor_pct": "VOR %", "backorder_rate": "Backorder rate"},
    )
    fig.update_layout(**PLOTLY, title=f"Flying Gold map — {highlight} ({y})")
    fig.update_xaxes(tickformat=".1%")
    fig.update_yaxes(tickformat=".1%")
    st.plotly_chart(fig, width='stretch')


def render_vor_seasonality(df: pd.DataFrame, year_sel: list[int], highlight: str, latest_y: int | None) -> None:
    if df.empty:
        _missing("VOR Seasonality")
        return
    y = latest_y or int(df["year"].max())
    d = df[(df["distributor_code"] == highlight) & (df["year"] == y)]
    if d.empty:
        st.warning("No seasonality rows for selection.")
        return
    fig = px.line(
        d.sort_values("week_of_year"),
        x="week_of_year",
        y="vor_pct",
        markers=True,
        labels={"week_of_year": "Week", "vor_pct": "VOR %"},
        title=f"VOR seasonality — {highlight} ({y})",
    )
    fig.update_layout(**PLOTLY)
    fig.update_yaxes(tickformat=".1%")
    st.plotly_chart(fig, width='stretch')


def render_vor_profile(df: pd.DataFrame, year_sel: list[int], highlight: str, latest_y: int | None) -> None:
    if df.empty:
        _missing("VOR Order Profile")
        return
    y = latest_y or int(df["year"].max())
    d = df[(df["distributor_code"] == highlight) & (df["year"] == y)]
    if d.empty:
        st.warning("No profile rows.")
        return
    fig = px.bar(
        d.sort_values("pct_of_total_lines", ascending=True),
        x="pct_of_total_lines",
        y="order_type",
        orientation="h",
        text=d["pct_of_total_lines"].map(lambda v: f"{v:.1%}"),
        labels={"pct_of_total_lines": "% of lines", "order_type": "Order type"},
        title=f"Order mix vs network — {highlight} ({y})",
    )
    fig.add_vline(x=d["network_avg_pct"].mean(), line_dash="dash", line_color="#94A3B8")
    fig.update_layout(**PLOTLY)
    fig.update_xaxes(tickformat=".1%")
    st.plotly_chart(fig, width='stretch')


def render_capture_trajectory(df: pd.DataFrame, year_sel: list[int], highlight: str, latest_y: int | None) -> None:
    if df.empty:
        _missing("Capture Trajectory")
        return
    d = df[df["distributor_code"] == highlight].copy()
    if d.empty:
        st.warning("No trajectory for highlighted distributor.")
        return
    cats = st.multiselect(
        "PMS categories",
        sorted(d["pms_category"].unique()),
        default=sorted(d["pms_category"].unique())[:3],
    )
    d = d[d["pms_category"].isin(cats)]
    d = d.copy()
    d["line_style"] = d["is_projected"].map({True: "dash", False: "solid"})
    fig = px.line(
        d,
        x="year",
        y="capture_rate",
        color="pms_category",
        line_dash="line_style",
        line_dash_map={"dash": "dash", "solid": "solid"},
        markers=True,
        labels={"capture_rate": "Capture rate", "year": "Year"},
        title=f"Capture trajectory + forecast — {highlight}",
    )
    alerts = d[d["alert_declining"] & ~d["is_projected"]]["pms_category"].unique()
    if len(alerts):
        st.error(f"Declining capture alert: {', '.join(alerts)}")
    fig.update_layout(**PLOTLY)
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, width='stretch')


def render_part_lifecycle(df: pd.DataFrame, highlight: str) -> None:
    if df.empty:
        _missing("Part Lifecycle")
        return
    st.markdown(
        "Revenue by lifecycle stage (network-wide). The point isn't the mature bar — "
        "it's how thin **emerging** is. Only ~3% of revenue sits in parts new enough to "
        "refill the funnel; as the mature base ages into zombie, little is behind it."
    )
    d = df.copy()
    d["stage"] = d["lifecycle_stage"].where(d["first_billing_year"] < 2024, "emerging")
    order = ["emerging", "mature", "zombie"]
    rev = (
        d.groupby("stage", as_index=False)["total_revenue_eur"].sum()
        .assign(_o=lambda x: x["stage"].map({s: i for i, s in enumerate(order)}))
        .sort_values("_o")
    )
    fig = px.bar(
        rev,
        x="stage",
        y="total_revenue_eur",
        color="stage",
        color_discrete_map=LIFECYCLE_COLORS,
        category_orders={"stage": order},
        title="Revenue by lifecycle stage — emerging is the intake funnel",
        labels={"total_revenue_eur": "Revenue (€)", "stage": "Lifecycle stage"},
    )
    fig.update_layout(**PLOTLY, showlegend=False)
    st.plotly_chart(fig, width='stretch')
    st.caption(
        "⚠️ *Emerging* = parts first invoiced in 2024–25, inside our 2023-start window. "
        "It undercounts (anything genuinely new in 2023 is left-censored) — treat it as a floor."
    )
    zombies = df[(df["lifecycle_stage"] == "zombie") & df["has_bvp_equivalent"]].head(50)
    if not zombies.empty:
        st.markdown("**Zombie genuine PNs** (BVP substitute exists)")
        st.dataframe(
            zombies[
                ["part_number", "product_family", "pms_category", "last_billing_year", "total_revenue_eur"]
            ],
            width='stretch',
            hide_index=True,
        )


def render_revenue_concentration(df: pd.DataFrame, year_sel: list[int], highlight: str, latest_y: int | None) -> None:
    if df.empty:
        _missing("Revenue Concentration")
        return
    y = latest_y or int(df["year"].max())
    d = df[(df["year"] == y) & (df["line_type"] == "total")].sort_values("gini_coefficient", ascending=False)
    fig = px.bar(
        d,
        x="distributor_code",
        y="gini_coefficient",
        color="distributor_code",
        labels={"gini_coefficient": "Revenue concentration (0 = even, 1 = one part is everything)"},
        title=f"Revenue concentration — network ({y})",
    )
    if highlight in d["distributor_code"].values:
        fig.add_annotation(
            x=highlight,
            y=float(d.loc[d["distributor_code"] == highlight, "gini_coefficient"].iloc[0]),
            text="★",
            showarrow=False,
            font=dict(size=16, color=ISZE_ORANGE),
        )
    fig.update_layout(**PLOTLY, showlegend=False)
    st.plotly_chart(fig, width='stretch')
    st.caption(
        "Gini coefficient: **higher = more revenue riding on fewer part numbers = "
        "more concentration risk** (0 = every part bills evenly, 1 = a single part is everything)."
    )
    hl = df[(df["distributor_code"] == highlight) & (df["year"] == y)]
    if not hl.empty:
        st.dataframe(hl, width='stretch', hide_index=True)


def render_revenue_waterfall(df: pd.DataFrame, year_sel: list[int], highlight: str) -> None:
    if df.empty:
        _missing("Revenue Waterfall")
        return
    pairs = sorted(df[["year_from", "year_to"]].drop_duplicates().itertuples(index=False, name=None))
    pair = st.selectbox("Year pair", pairs, format_func=lambda p: f"{p[0]} → {p[1]}")
    d = df[
        (df["distributor_code"] == highlight)
        & (df["year_from"] == pair[0])
        & (df["year_to"] == pair[1])
    ]
    if d.empty:
        st.warning("No waterfall rows for this distributor / year pair.")
        return
    fam = st.selectbox("Product family", sorted(d["product_family"].unique()))
    row = d[d["product_family"] == fam].iloc[0]
    fig = go.Figure(
        go.Waterfall(
            x=["Base", "Volume", "Price", "Mix", "End"],
            measure=["absolute", "relative", "relative", "relative", "total"],
            y=[
                row["revenue_base_eur"],
                row["delta_volume_eur"],
                row["delta_price_eur"],
                row["delta_mix_eur"],
                row["revenue_end_eur"],
            ],
            connector=dict(line=dict(color="#94A3B8")),
        )
    )
    fig.update_layout(**PLOTLY, title=f"Genuine revenue bridge — {highlight} · {fam}")
    st.plotly_chart(fig, width='stretch')


def render_price_premium(df: pd.DataFrame, year_sel: list[int], highlight: str, latest_y: int | None) -> None:
    if df.empty:
        _missing("Price Premium")
        return
    y = latest_y or int(df["year"].max())
    d = df[(df["distributor_code"] == highlight) & (df["year"] == y)].sort_values("price_premium_pct")
    if d.empty:
        st.warning("No premium rows (need both genuine & BVP in category).")
        return
    fig = px.bar(
        d,
        x="price_premium_pct",
        y="pms_category",
        orientation="h",
        color="genuine_unit_share",
        labels={"price_premium_pct": "Genuine premium vs BVP", "pms_category": "Category"},
        title=f"Price premium acceptance — {highlight} ({y})",
    )
    fig.update_layout(**PLOTLY)
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig, width='stretch')


# render_basket_correlation removed 2026-08-20 (parked Contract 8; CSV still builds but tab dropped)


def render_substitution_timeline(df: pd.DataFrame, year_sel: list[int], highlight: str) -> None:
    if df.empty:
        _missing("Substitution Timeline")
        return
    d = _years(df[df["distributor_code"] == highlight], year_sel)
    if d.empty:
        st.warning("No substitution timeline rows.")
        return
    fams = st.multiselect(
        "Families",
        sorted(d["product_family"].dropna().unique()),
        default=sorted(d["product_family"].dropna().unique())[:5],
    )
    d = d[d["product_family"].isin(fams)]
    fig = px.line(
        d.sort_values(["product_family", "year"]),
        x="year",
        y="genuine_unit_share",
        color="product_family",
        markers=True,
        labels={"genuine_unit_share": "Genuine unit share"},
        title=f"Substitution invasion — {highlight}",
    )
    fig.update_layout(**PLOTLY)
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, width='stretch')


def render_geographic_risk(
    geo: pd.DataFrame,
    gps_db: pd.DataFrame,
    year_sel: list[int],
    highlight: str,
    latest_y: int | None,
) -> None:
    if geo.empty or gps_db.empty:
        _missing("Geographic risk (geo + GPS)")
        return
    y = latest_y or int(gps_db["year"].max())
    geo_slim = geo.drop(columns=["country"], errors="ignore")
    g = gps_db[gps_db["year"] == y].merge(geo_slim, on="distributor_code", how="inner")
    g = g.dropna(subset=["lat", "lon"])
    if g.empty:
        st.warning("No geocoded distributors.")
        return
    g["size"] = g["spend_per_unit_eur"].fillna(0).clip(lower=50)
    g["is_hl"] = g["distributor_code"] == highlight
    fig = px.scatter_geo(
        g,
        lat="lat",
        lon="lon",
        size="size",
        color="spend_per_unit_eur",
        hover_name="distributor_code",
        hover_data=["country", "territory_label", "region"],
        color_continuous_scale=["#D6E4F0", ISZE_BLUE, ISZE_ORANGE],
        title=f"Geographic GPS/SPU — {y}",
    )
    fig.update_geos(scope="europe", showcountries=True)
    fig.update_layout(**PLOTLY)
    st.plotly_chart(fig, width='stretch')


def render_capture_recovery(df: pd.DataFrame, highlight: str) -> None:
    if df.empty:
        _missing("Capture Recovery")
        return
    d = df[df["distributor_code"] == highlight]
    if d.empty:
        st.warning("No recovery model rows.")
        return
    fig = px.bar(
        d.sort_values("gap_revenue_at_genuine", ascending=True),
        x="gap_revenue_at_genuine",
        y="pms_category",
        color="gap_type",
        orientation="h",
        labels={"gap_revenue_at_genuine": "Gap € @ genuine ASP", "gap_type": "Gap type"},
        title=f"Capture recovery — {highlight} (latest year)",
    )
    fig.update_layout(**PLOTLY)
    st.plotly_chart(fig, width='stretch')
    st.dataframe(d, width='stretch', hide_index=True)
