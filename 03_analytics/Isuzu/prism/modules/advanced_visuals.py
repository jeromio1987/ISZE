"""
Six advanced/offset visuals — framework-agnostic.

Each builder reads the real derived CSVs and returns a plotly go.Figure, so the
SAME figure renders in Streamlit, Quarto, and Dash with no rework.

  fig_trajectory_quiver   #1  GPS x capture MOVEMENT 2023->2025 (arrows, not dots)
  fig_lumpiness_airfreight#2  offset: demand lumpiness -> VOR/airfreight cost
  fig_demand_flow_sankey  #3  parc demand -> genuine / BVP / leakage (leakage INFERRED)
  fig_vor_pricing_power   #4  VOR revenue vs realised premium -> repricing call list
  fig_premium_defection   #5  genuine premium vs genuine unit share (does price cost share?)
  fig_capture_ceiling     #6  current genuine -> recoverable -> TAM ceiling bridge

All numbers come from the CSVs; no fabricated values. The leakage leg of #3 is an
INFERENCE (under-service gap), never a measured competitor figure.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
GREEN = "#2E7D32"
RED = "#C62828"
GREY = "#94A3B8"

_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Segoe UI, sans-serif", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#FAFBFC",
)

def _default_derived() -> Path:
    import os

    if env := os.environ.get("ISZE_DERIVED"):
        return Path(env)
    try:
        from config import DERIVED_DIR  # noqa: WPS433

        return Path(DERIVED_DIR)
    except ImportError:
        return Path(__file__).resolve().parents[2] / "data" / "derived"


DEFAULT_DERIVED = _default_derived()


def _d(derived_dir: str | Path | None) -> Path:
    return Path(derived_dir) if derived_dir else DEFAULT_DERIVED


def _read(derived_dir, name) -> pd.DataFrame:
    return pd.read_csv(_d(derived_dir) / name)


def _distributor_capture(derived_dir) -> pd.DataFrame:
    """Distributor x year total capture from pms_capture_by_db_year (clip 1.05)."""
    cap = _read(derived_dir, "pms_capture_by_db_year.csv")
    cap = cap[cap["line_type"] == "total"]
    g = cap.groupby(["distributor_code", "year"], as_index=False).agg(
        actual_qty=("actual_qty", "sum"), expected_qty=("expected_qty", "sum")
    )
    g["capture_rate"] = (g["actual_qty"] / g["expected_qty"].replace(0, np.nan)).clip(upper=1.05)
    return g.dropna(subset=["capture_rate"])


# ───────────────────────────── #1 trajectory quiver ─────────────────────────
def fig_trajectory_quiver(derived_dir=None, highlight: str = "ITUK") -> go.Figure:
    gps = _read(derived_dir, "gps_spu_by_distributor.csv")[
        ["distributor_code", "year", "spend_per_unit_eur"]
    ]
    cap = _distributor_capture(derived_dir)[["distributor_code", "year", "capture_rate"]]
    df = gps.merge(cap, on=["distributor_code", "year"], how="inner")
    ymin, ymax = int(df["year"].min()), int(df["year"].max())

    fig = go.Figure()
    for dist, g in df.groupby("distributor_code"):
        g = g.sort_values("year")
        start = g[g["year"] == ymin]
        end = g[g["year"] == ymax]
        if start.empty or end.empty:
            continue
        x0, y0 = float(start["spend_per_unit_eur"].iloc[0]), float(start["capture_rate"].iloc[0])
        x1, y1 = float(end["spend_per_unit_eur"].iloc[0]), float(end["capture_rate"].iloc[0])
        improving = (x1 >= x0) and (y1 >= y0)
        declining = (x1 <= x0) and (y1 <= y0)
        col = GREEN if improving else RED if declining else GREY
        is_hl = dist == highlight
        fig.add_trace(go.Scatter(
            x=g["spend_per_unit_eur"], y=g["capture_rate"], mode="lines+markers",
            line=dict(color=col, width=4 if is_hl else 1.5),
            marker=dict(size=[6] * (len(g) - 1) + [12], color=col),
            opacity=1.0 if is_hl else 0.5, name=dist,
            hovertemplate=f"<b>{dist}</b><br>GPS €%{{x:.0f}}<br>capture %{{y:.0%}}<extra></extra>",
            showlegend=is_hl,
        ))
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowwidth=2 if is_hl else 1,
                           arrowcolor=col, opacity=1.0 if is_hl else 0.45)
        if is_hl:
            fig.add_annotation(x=x1, y=y1, text=f"<b>{dist}</b>", showarrow=False,
                               yshift=14, font=dict(color=ISZE_ORANGE, size=13))
    fig.update_layout(**_LAYOUT, title=f"Distributor movement {ymin}→{ymax} — GPS/SPU vs PMS capture",
                      xaxis_title="GPS / SPU (€)", yaxis_title="PMS capture",
                      yaxis_tickformat=".0%", showlegend=False, height=620)
    fig.add_annotation(xref="paper", yref="paper", x=0.99, y=0.02, showarrow=False,
                       text="green = both ↑ · red = both ↓ · grey = mixed",
                       font=dict(size=11, color=GREY), align="right")
    return fig


# ─────────────────────── #2 lumpiness → airfreight (offset) ──────────────────
def fig_lumpiness_airfreight(derived_dir=None) -> go.Figure:
    dc = _read(derived_dir, "demand_classification.csv")
    dim = _read(derived_dir, "bvp_pn_dimension.csv")[["part_number", "product_family"]]
    dim["part_number"] = dim["part_number"].astype(str)
    dc["part_number"] = dc["part_number"].astype(str)
    dc = dc.merge(dim.drop_duplicates("part_number"), on="part_number", how="left")
    dc = dc.dropna(subset=["product_family"])
    dc["hard"] = dc["demand_class"].isin(["lumpy", "intermittent"])
    fam = dc.groupby("product_family").agg(
        rev=("total_revenue_eur", "sum"),
        hard_rev=("total_revenue_eur", lambda s: s[dc.loc[s.index, "hard"]].sum()),
        mean_cv2=("cv2", "mean"),
    ).reset_index()
    fam["hard_share"] = fam["hard_rev"] / fam["rev"].replace(0, np.nan)

    vor = _read(derived_dir, "vor_airfreight_risk.csv")
    vy = vor[vor["year"] == vor["year"].max()]
    vfam = vy.groupby("product_family", as_index=False).agg(
        vor_lines=("vor_line_count", "sum"), tot_lines=("total_line_count", "sum"))
    vfam["vor_pct"] = vfam["vor_lines"] / vfam["tot_lines"].replace(0, np.nan)

    m = fam.merge(vfam, on="product_family", how="inner").dropna(subset=["hard_share", "vor_pct"])
    m = m[m["rev"] > 0]
    fig = go.Figure(go.Scatter(
        x=m["hard_share"], y=m["vor_pct"], mode="markers+text",
        text=m["product_family"], textposition="top center", textfont=dict(size=9),
        marker=dict(size=np.sqrt(m["rev"].clip(lower=1)) * 0.6 + 6, color=m["mean_cv2"],
                    colorscale=[ISZE_BLUE, ISZE_ORANGE], showscale=True,
                    colorbar=dict(title="mean CV²")),
        hovertemplate="<b>%{text}</b><br>hard-to-stock rev %{x:.0%}<br>VOR %{y:.1%}<extra></extra>",
    ))
    fig.update_layout(**_LAYOUT,
                      title="Does lumpy demand drive airfreight?  (family-level, latest year)",
                      xaxis_title="Share of family revenue in lumpy/intermittent demand",
                      yaxis_title="VOR / urgent line share",
                      xaxis_tickformat=".0%", yaxis_tickformat=".1%", height=600)
    return fig


# ───────────────────────── #3 demand-flow Sankey ────────────────────────────
def fig_demand_flow_sankey(derived_dir=None) -> go.Figure:
    om = _read(derived_dir, "pms_opportunity_matrix.csv")
    om = om[om["year"] == om["year"].max()].copy()
    om["cap_t"] = om["capture_rate_total"].clip(upper=1.0)
    om["cap_g"] = om["capture_rate_genuine"].clip(upper=1.0)
    om["genuine_eur"] = (om["cap_g"] * om["tam_eur"]).clip(lower=0)
    om["bvp_eur"] = ((om["cap_t"] - om["cap_g"]).clip(lower=0) * om["tam_eur"])
    om["leak_eur"] = ((1 - om["cap_t"]).clip(lower=0) * om["tam_eur"])

    cats = sorted(om["pms_category"].unique())
    targets = ["Genuine (captured)", "BVP (captured)", "Leakage (INFERRED)"]
    nodes = cats + targets
    idx = {n: i for i, n in enumerate(nodes)}
    src, tgt, val, col = [], [], [], []
    flow_colors = {"Genuine (captured)": "rgba(27,58,107,0.55)",
                   "BVP (captured)": "rgba(232,119,34,0.55)",
                   "Leakage (INFERRED)": "rgba(198,40,40,0.45)"}
    for c in cats:
        r = om[om["pms_category"] == c]
        for t, field in [("Genuine (captured)", "genuine_eur"),
                         ("BVP (captured)", "bvp_eur"),
                         ("Leakage (INFERRED)", "leak_eur")]:
            v = float(r[field].sum())
            if v <= 0:
                continue
            src.append(idx[c]); tgt.append(idx[t]); val.append(v); col.append(flow_colors[t])
    node_col = [ISZE_BLUE] * len(cats) + [ISZE_BLUE, ISZE_ORANGE, RED]
    fig = go.Figure(go.Sankey(
        node=dict(label=nodes, color=node_col, pad=14, thickness=16,
                  line=dict(color="white", width=0.5)),
        link=dict(source=src, target=tgt, value=val, color=col,
                  hovertemplate="%{source.label} → %{target.label}<br>€%{value:,.0f}<extra></extra>"),
    ))
    total_leak = om["leak_eur"].sum()
    fig.update_layout(**_LAYOUT, height=600,
                      title=f"Where parc-implied demand goes (network, latest year) — "
                            f"red = INFERRED leakage ≈ €{total_leak:,.0f}, not measured")
    return fig


# ─────────────────────── #4 VOR pricing-power quadrant ───────────────────────
def fig_vor_pricing_power(derived_dir=None, highlight: str = "ITUK") -> go.Figure:
    wtp = _read(derived_dir, "vor_willingness_to_pay.csv")
    g = wtp.groupby("distributor_code").apply(
        lambda x: pd.Series({
            "exp_rev": x["expedited_revenue_eur"].sum(),
            "wpremium": np.average(x["premium_pct"], weights=x["expedited_revenue_eur"].clip(lower=1)),
            "pairs": len(x),
        }), include_groups=False).reset_index()
    g = g[g["exp_rev"] > 0]
    med_p = g["wpremium"].median()
    g["col"] = np.where(g["distributor_code"] == highlight, ISZE_ORANGE,
                        np.where(g["wpremium"] <= 0.01, RED, ISZE_BLUE))
    fig = go.Figure(go.Scatter(
        x=g["exp_rev"], y=g["wpremium"], mode="markers+text",
        text=g["distributor_code"], textposition="top center", textfont=dict(size=9),
        marker=dict(size=np.sqrt(g["pairs"]) * 3 + 6, color=g["col"]),
        hovertemplate="<b>%{text}</b><br>expedited rev €%{x:,.0f}<br>wtd premium %{y:.1%}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=RED,
                  annotation_text="zero premium = cost eaten", annotation_position="bottom right")
    fig.add_hline(y=med_p, line_dash="dot", line_color=GREY,
                  annotation_text=f"median {med_p:.1%}")
    fig.update_layout(**_LAYOUT, height=600,
                      title="VOR pricing power — high revenue + low premium (bottom-right) = repricing call list",
                      xaxis_title="Expedited revenue (€)", yaxis_title="Revenue-weighted VOR premium",
                      yaxis_tickformat=".0%")
    return fig


# ─────────────────────── #5 premium vs defection ────────────────────────────
def fig_premium_defection(derived_dir=None, highlight: str = "ITUK") -> go.Figure:
    pp = _read(derived_dir, "price_premium.csv")
    pp = pp[pp["year"] == pp["year"].max()].copy()
    pp = pp.dropna(subset=["price_premium_pct", "genuine_unit_share"])
    pp = pp[(pp["price_premium_pct"].between(-0.5, 5))
            & (pp["genuine_units"] >= 20) & (pp["bvp_units"] >= 20)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pp["price_premium_pct"], y=pp["genuine_unit_share"], mode="markers",
        marker=dict(size=np.sqrt(np.minimum(pp["genuine_units"], pp["bvp_units"]).clip(lower=1)) * 0.5 + 5,
                    color=np.where(pp["distributor_code"] == highlight, ISZE_ORANGE, ISZE_BLUE),
                    opacity=0.6),
        text=pp["distributor_code"] + " · " + pp["pms_category"],
        hovertemplate="<b>%{text}</b><br>genuine premium %{x:.0%}<br>genuine share %{y:.0%}<extra></extra>",
    ))
    # network trend line
    if len(pp) >= 3:
        b, a = np.polyfit(pp["price_premium_pct"], pp["genuine_unit_share"], 1)
        xs = np.linspace(pp["price_premium_pct"].min(), pp["price_premium_pct"].max(), 50)
        r = float(np.corrcoef(pp["price_premium_pct"], pp["genuine_unit_share"])[0, 1])
        fig.add_trace(go.Scatter(x=xs, y=a + b * xs, mode="lines",
                                 line=dict(color=RED, dash="dash"),
                                 name=f"trend (r={r:.2f})"))
    fig.update_layout(**_LAYOUT, height=600,
                      title="Does charging more for genuine cost you share?  (dist × category, latest year)",
                      xaxis_title="Genuine ASP premium vs BVP", yaxis_title="Genuine unit share",
                      xaxis_tickformat=".0%", yaxis_tickformat=".0%")
    return fig


# ─────────────────────── #6 capture-ceiling bridge ──────────────────────────
def fig_capture_ceiling(derived_dir=None, highlight: str = "ITUK") -> go.Figure:
    rec = _read(derived_dir, "capture_recovery_model.csv")
    om = _read(derived_dir, "pms_opportunity_matrix.csv")
    om = om[om["year"] == om["year"].max()]
    d = rec[rec["distributor_code"] == highlight]
    omd = om[om["distributor_code"] == highlight]
    if d.empty or omd.empty:
        return go.Figure(layout=go.Layout(title=f"No recovery data for {highlight}", **_LAYOUT))
    tam = float(omd["tam_eur"].sum())
    # current genuine € ≈ capture_rate_genuine * tam per category
    cur_genuine = float((omd["capture_rate_genuine"].clip(upper=1.0) * omd["tam_eur"]).sum())
    under = float(d.loc[d["gap_type"] == "under_service", "gap_revenue_at_genuine"].sum())
    subst = float(d.loc[d["gap_type"] == "substitution", "gap_revenue_at_genuine"].sum())
    catgap = float(d.loc[d["gap_type"] == "catalog_gap", "gap_revenue_at_genuine"].sum())
    fig = go.Figure(go.Waterfall(
        orientation="v",
        x=["Current genuine €", "+ recover under-service", "+ win back from BVP", "+ close catalog gap", "TAM ceiling"],
        measure=["absolute", "relative", "relative", "relative", "total"],
        y=[cur_genuine, under, subst, catgap, tam],
        text=[f"€{v:,.0f}" for v in [cur_genuine, under, subst, catgap, tam]],
        connector=dict(line=dict(color=GREY)),
        increasing=dict(marker=dict(color=GREEN)), totals=dict(marker=dict(color=ISZE_BLUE)),
    ))
    fig.update_layout(**_LAYOUT, height=600,
                      title=f"Capture-ceiling bridge — {highlight} (latest year): current → recoverable → TAM")
    return fig


def fig_db_parts_mix(derived_dir=None, highlight: str = "ITUK") -> go.Figure:
    """Genuine-only / contested / BVP share of total parts revenue, per DB (latest year).

    Honest total-revenue mix from db_parts_mix_classification.csv. NOT competitor
    wallet share — non-Isuzu aftermarket brands never touch our invoice.
    """
    d = _read(derived_dir, "db_parts_mix_classification.csv")
    d = d[d["year"] == d["year"].max()].sort_values("total_eur")
    fig = go.Figure()
    for col, name, color in (
        ("bvp_pct", "BVP", RED),
        ("genuine_contested_pct", "Genuine (contested)", ISZE_ORANGE),
        ("genuine_only_pct", "Genuine only", ISZE_BLUE),
    ):
        fig.add_bar(y=d["distributor_code"], x=d[col], name=name, orientation="h",
                    marker_color=color)
    if highlight in set(d["distributor_code"]):
        fig.add_annotation(x=1.02, y=highlight, text="◀", showarrow=False,
                           font=dict(color=ISZE_ORANGE, size=14), xref="x", yref="y")
    fig.update_layout(**_LAYOUT, barmode="stack", height=620,
                      xaxis=dict(title="Share of total parts revenue", tickformat=".0%"),
                      legend=dict(orientation="h", y=-0.1),
                      title="Parts mix per distributor (latest year): genuine / contested / BVP")
    return fig


# ───────────────────────── tender pipeline (from tender_data.json) ───────────
DECISION_COLORS = {"Attack": "#E2231A", "Selective": ISZE_ORANGE, "Watch": ISZE_BLUE, "Ignore": GREY}
DECISION_ORDER = ["Attack", "Selective", "Watch", "Ignore"]


def _tender(derived_dir=None) -> pd.DataFrame:
    """Tender opportunity pipeline. Qualified-pipeline only — value present on ~12
    of 520 rows, so never chart € here, only counts and scores."""
    d = _read(derived_dir, "tender_pipeline.csv")
    if d["actionable"].dtype != bool:
        d["actionable"] = d["actionable"].astype(str).str.lower().isin(["true", "1"])
    return d


def fig_tender_funnel(derived_dir=None) -> go.Figure:
    c = _tender(derived_dir)["decision"].value_counts()
    order = [k for k in DECISION_ORDER if k in c.index]
    vals = [int(c[k]) for k in order]
    fig = go.Figure(go.Bar(x=order, y=vals, text=vals, textposition="outside",
                           marker_color=[DECISION_COLORS[k] for k in order]))
    fig.update_layout(**_LAYOUT, height=420, yaxis=dict(title="Opportunities"),
                      title="Tender pipeline — qualification funnel (520 scored opportunities)")
    return fig


def fig_tender_country(derived_dir=None) -> go.Figure:
    d = _tender(derived_dir)
    c = d[d["actionable"]]["country"].value_counts().head(12).sort_values()
    fig = go.Figure(go.Bar(y=c.index.tolist(), x=c.values.tolist(), orientation="h",
                           marker_color=ISZE_BLUE, text=c.values.tolist(), textposition="auto"))
    fig.update_layout(**_LAYOUT, height=460, xaxis=dict(title="Actionable opportunities"),
                      title="Actionable tender opportunities by country (top 12)")
    return fig


def fig_tender_owner(derived_dir=None) -> go.Figure:
    d = _tender(derived_dir)
    c = d[d["actionable"]]["owner_suggested"].value_counts().sort_values()
    fig = go.Figure(go.Bar(y=c.index.tolist(), x=c.values.tolist(), orientation="h",
                           marker_color=ISZE_ORANGE, text=c.values.tolist(), textposition="auto"))
    fig.update_layout(**_LAYOUT, height=420, xaxis=dict(title="Actionable opportunities"),
                      title="Actionable tender opportunities by owner")
    return fig


def fig_tender_scatter(derived_dir=None) -> go.Figure:
    d = _tender(derived_dir)
    d = d[(d["decision"] != "Ignore") & d["fit_score"].notna() & d["win_score"].notna()]
    fig = go.Figure()
    for dec in ["Attack", "Selective", "Watch"]:
        g = d[d["decision"] == dec]
        if g.empty:
            continue
        fig.add_scatter(
            x=g["fit_score"], y=g["win_score"], mode="markers", name=dec,
            marker=dict(size=(g["opportunity_score"] / 4).clip(6, 28),
                        color=DECISION_COLORS[dec], line=dict(width=0.5, color="white"), opacity=0.75),
            text=g["title"],
            hovertemplate="%{text}<br>fit %{x} · win %{y}<extra></extra>",
        )
    fig.update_layout(**_LAYOUT, height=480, xaxis=dict(title="Fit score"),
                      yaxis=dict(title="Win-probability score"),
                      legend=dict(orientation="h", y=-0.15),
                      title="Tender qualification map — fit × win (bubble = opportunity score)")
    return fig


BUILDERS = {
    "trajectory_quiver": ("Distributor Movement", fig_trajectory_quiver),
    "lumpiness_airfreight": ("Lumpiness → Airfreight", fig_lumpiness_airfreight),
    "demand_flow_sankey": ("Demand-Flow Sankey", fig_demand_flow_sankey),
    "vor_pricing_power": ("VOR Pricing Power", fig_vor_pricing_power),
    "premium_defection": ("Premium vs Defection", fig_premium_defection),
    "capture_ceiling": ("Capture-Ceiling Bridge", fig_capture_ceiling),
    "db_parts_mix": ("DB Parts Mix", fig_db_parts_mix),
    "tender_funnel": ("Tender Funnel", fig_tender_funnel),
    "tender_country": ("Tender by Country", fig_tender_country),
    "tender_owner": ("Tender by Owner", fig_tender_owner),
    "tender_scatter": ("Tender Fit×Win", fig_tender_scatter),
}


def build_all(derived_dir=None, highlight: str = "ITUK") -> dict[str, go.Figure]:
    out = {}
    for key, (_, fn) in BUILDERS.items():
        try:
            out[key] = fn(derived_dir=derived_dir, highlight=highlight) if "highlight" in fn.__code__.co_varnames else fn(derived_dir=derived_dir)
        except Exception as e:  # keep one bad chart from killing the set
            out[key] = go.Figure(layout=go.Layout(title=f"{key} failed: {e}", **_LAYOUT))
    return out
