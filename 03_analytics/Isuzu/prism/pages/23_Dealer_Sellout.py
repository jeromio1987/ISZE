# PRISM Module 23 — Dealer Sell-out explorer
# Multi-DB sell-out (DB→dealer) vs billing (ISZE→DB): genuine/BVP/contested mix + SPU.

"""
PRISM — Module 23: Dealer Sell-out

Network sell-through at the DB→dealer layer, vs what ISZE billed the DB. Shows
genuine-only / contested / BVP share and spend-per-unit at sell-out. Multi-DB:
IUK ≠ ITUK ≠ IMIE (Ireland) — never blended into one number.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR, data_freshness_date, is_internal_mode  # noqa: E402
from modules.plotly_style import style

MIX_CSV = DERIVED_DIR / "sellout_aim_network_mix_2025.csv"
SUBGROUP_CSV = DERIVED_DIR / "sellout_aim_by_subgroup_2025.csv"

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
LAYER_SELLOUT = "sellout_db_dlr"


@st.cache_data(show_spinner="Loading sell-out data…")
def _load() -> tuple[pd.DataFrame, pd.DataFrame]:
    mix = pd.read_csv(MIX_CSV) if MIX_CSV.exists() else pd.DataFrame()
    sub = pd.read_csv(SUBGROUP_CSV) if SUBGROUP_CSV.exists() else pd.DataFrame()
    return mix, sub


# ── Brand CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; --isze-light: #D6E4F0; }
    .main-header { background: linear-gradient(90deg, #1B3A6B 0%, #2C5AA0 100%);
        padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1rem; }
    .main-header h1 { color: white !important; margin: 0; font-size: 1.6rem; }
    .main-header p { color: #D6E4F0; margin: 0.2rem 0 0; font-size: 0.85rem; }
    div[data-testid="metric-container"] { border: 1px solid #E0E0E0;
        border-left: 4px solid #1B3A6B; border-radius: 6px; padding: 0.5rem 0.8rem; }
    [data-testid="stMetricValue"] { color: #1B3A6B; }
    .footer-note { font-size: 0.72rem; color: #999; padding-top: 1rem;
        border-top: 1px solid #EEE; margin-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🏪 Dealer Sell-out — network explorer</h1>
    <p>Sell-through at the DB→dealer layer vs ISZE→DB billing: genuine / contested / BVP mix and spend-per-unit, across every distributor that reports sell-out.</p>
</div>
""", unsafe_allow_html=True)

if not is_internal_mode():
    st.warning(
        "INTERNAL ONLY — this page exposes DB→dealer sell-through and mix. "
        "Not shown in the MD-safe launcher.",
        icon="🔒",
    )

mix, sub = _load()

if mix.empty and sub.empty:
    st.info(
        f"Sell-out files not found under `{DERIVED_DIR}`.\n\n"
        "Run the multi-DB dealer sell-out build (`build_dealer_sellout_aim_gps.py`).",
        icon="📂",
    )
    st.stop()

st.caption(
    "Layer: **sell-out = DB→dealer** (network sell-through) vs **billing = ISZE→DB**. "
    "IUK ≠ ITUK ≠ IMIE (Ireland) — each DB is its own market; never blended."
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Filters")
    if not mix.empty:
        dbs = sorted(mix["distributor_code"].dropna().unique().tolist())
        selected_dbs = st.multiselect("Distributors (empty = all)", options=dbs, default=[])
    else:
        selected_dbs = []
    st.divider()
    st.caption(f"📅 Source: sellout_aim_network_mix_2025.csv, sellout_aim_by_subgroup_2025.csv")
    st.caption("📆 CY2025")
    st.caption(f"🔄 Built: {data_freshness_date()}")

mix_v = mix.copy()
if selected_dbs:
    mix_v = mix_v[mix_v["distributor_code"].isin(selected_dbs)]

# ── KPI row ───────────────────────────────────────────────────────────────────
sell = mix_v[mix_v["layer"] == LAYER_SELLOUT]
if not sell.empty:
    tot_eur = float(sell["total_eur"].sum())
    tot_qty = float(sell["qty_year"].sum())
    n_db = sell["distributor_code"].nunique()
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Sell-out € (network)", f"€{tot_eur / 1e6:,.1f}M")
    with k2:
        st.metric("Sell-out qty", f"{tot_qty:,.0f}")
    with k3:
        st.metric("Distributors", f"{n_db}")
    with k4:
        st.metric("BVP share (€, mean)", f"{float(sell['bvp_pct'].mean()) * 100:.1f}%")
    st.divider()

# ── Mix: genuine vs contested vs BVP ──────────────────────────────────────────
if not sell.empty:
    st.markdown("#### Sell-out mix by distributor (€ share)")
    try:
        mix_plot = sell[["distributor_code", "genuine_only_pct", "genuine_contested_pct", "bvp_pct"]].copy()
        mix_plot["genuine_only_pct"] *= 100
        mix_plot["genuine_contested_pct"] *= 100
        mix_plot["bvp_pct"] *= 100
        mix_plot = mix_plot.set_index("distributor_code")
        fig_mix = px.bar(
            mix_plot, x=mix_plot.index,
            y=["genuine_only_pct", "genuine_contested_pct", "bvp_pct"],
            barmode="stack",
            color_discrete_map={
                "genuine_only_pct": ISZE_BLUE,
                "genuine_contested_pct": ISZE_ORANGE,
                "bvp_pct": "#8FA9C9",
            },
            labels={"value": "€ share (%)", "variable": "Bucket", "distributor_code": "Distributor"},
        )
        fig_mix.update_layout(
            height=420, margin=dict(l=10, r=10, t=20, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(gridcolor="#F0F0F0", ticksuffix="%"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        )
        st.plotly_chart(style(fig_mix), width="stretch")
        st.caption("Blue = genuine-only · Orange = contested (BVP crossref exists) · Grey = BVP. High contested share = substitution risk the BVP line is meant to defend.")
    except Exception as e:
        st.warning(f"Mix chart unavailable: {e}")
    st.divider()

# ── SPU: sell-out vs billing ──────────────────────────────────────────────────
if not mix_v.empty and "sellout_spu_eur" in mix_v and "billing_gps" in mix_v:
    st.markdown("#### Spend-per-unit — sell-out vs billing (€ per truck)")
    try:
        spu = mix_v[mix_v["layer"] == LAYER_SELLOUT][["distributor_code", "sellout_spu_eur", "billing_gps"]].copy()
        spu = spu.dropna(subset=["sellout_spu_eur"]).set_index("distributor_code")
        fig_spu = go.Figure()
        fig_spu.add_trace(go.Bar(name="Sell-out SPU", x=spu.index, y=spu["sellout_spu_eur"],
                                 marker_color=ISZE_BLUE))
        fig_spu.add_trace(go.Bar(name="Billing SPU", x=spu.index, y=spu["billing_gps"],
                                 marker_color=ISZE_ORANGE))
        fig_spu.update_layout(
            barmode="group", height=380, margin=dict(l=10, r=10, t=20, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(gridcolor="#F0F0F0", tickprefix="€"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        )
        st.plotly_chart(style(fig_spu), width="stretch")
        st.caption("Sell-out SPU above billing SPU = the DB is selling through faster than ISZE is billing (healthy demand); the reverse = stock building at dealer.")
    except Exception as e:
        st.warning(f"SPU chart unavailable: {e}")
    st.divider()

# ── Subgroup mix ───────────────────────────────────────────────────────────────
if not sub.empty:
    st.markdown("#### Genuine-only € share by part subgroup (sell-out layer)")
    try:
        sub_v = sub[sub["layer"] == LAYER_SELLOUT].copy()
        if selected_dbs:
            sub_v = sub_v[sub_v["distributor_code"].isin(selected_dbs)]
        only = sub_v[sub_v["aim_bucket"] == "genuine_only"].copy()
        if not only.empty:
            by_sg = only.groupby("report_subgroup", as_index=False)["eur"].sum()
            by_sg = by_sg.sort_values("eur", ascending=True).tail(20)
            fig_sg = px.bar(by_sg, x="eur", y="report_subgroup", orientation="h",
                            color_discrete_sequence=[ISZE_BLUE],
                            labels={"eur": "Genuine-only €", "report_subgroup": "Subgroup"})
            fig_sg.update_layout(height=max(360, len(by_sg) * 22), margin=dict(l=10, r=10, t=10, b=20),
                                 plot_bgcolor="white", paper_bgcolor="white",
                                 xaxis=dict(gridcolor="#F0F0F0", tickprefix="€"))
            st.plotly_chart(style(fig_sg), width="stretch")
            st.caption("Top subgroups by genuine-only € at the sell-out layer — the parts where the genuine line is still winning without a BVP contest.")
        else:
            st.info("No genuine-only rows in the subgroup file.")
    except Exception as e:
        st.warning(f"Subgroup chart unavailable: {e}")

st.markdown(
    '<div class="footer-note">PRISM Dealer Sell-out | Module 23 | '
    'Sources: sellout_aim_network_mix_2025.csv, sellout_aim_by_subgroup_2025.csv | IUK ≠ ITUK ≠ IMIE</div>',
    unsafe_allow_html=True,
)
