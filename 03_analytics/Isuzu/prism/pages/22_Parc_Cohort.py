# PRISM Module 22 — Parc Cohorts / Golden Window transition
# JP VIN shipment cohort (rolling 60m) — parc aging and PMS-age entry, NOT UIO v19.

"""
PRISM — Module 22: Parc Cohorts

A shipment-cohort view of the young CV parc from the JP VIN register. This is a
denominator signal, not a replacement for UIO v19: ex ITUK/UTI, rolling-60m only.
Shows which vehicles enter PMS-age when (the ICE D-Max/N-series window 2025–2032).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR))

from config import DATA_ROOT, data_freshness_date  # noqa: E402
from modules.plotly_style import style

# Working register is the parquet (VIN_register.parquet); the .csv is the Excel
# convenience copy. Read the parquet so the page tracks the canonical register.
VIN_PARQUET = DATA_ROOT / "07_UIO" / "vin" / "VIN_register.parquet"

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"


@st.cache_data(show_spinner="Loading VIN register…")
def _load_vin() -> pd.DataFrame:
    if not VIN_PARQUET.exists():
        return pd.DataFrame()
    return pd.read_parquet(VIN_PARQUET)


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
    <h1>🚛 Parc Cohorts — Golden Window transition</h1>
    <p>Shipment-cohort view of the CV parc from the JP VIN register — which vehicles age into PMS-service window when.</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "**JP VIN shipment cohort (rolling 60m) — ex ITUK / UTI.** This is a cohort signal, "
    "not the registered UIO (v19) denominator. Do not compare these counts to UIO totals.",
    icon="⚠️",
)

df = _load_vin()

if df.empty:
    st.info(
        f"VIN register not found: `{VIN_PARQUET}`.\n\n"
        "Rebuild with `python 01_data/07_UIO/vin/build_vin_register.py`.",
        icon="📂",
    )
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Filters")
    series_opts = ["All series"] + sorted(df["series"].dropna().unique().tolist())
    selected_series = st.selectbox("Series", series_opts)
    st.divider()
    st.caption(f"📅 Source: `{VIN_PARQUET.name}`")
    st.caption("⏱ Rolling-60m as-of: 2026-07-27")
    st.caption(f"🔄 Built: {data_freshness_date()}")

view = df.copy()
if selected_series != "All series":
    view = view[view["series"] == selected_series]

# ── KPI row ───────────────────────────────────────────────────────────────────
n_total = len(view)
n_pms = int(view["in_pms_rolling_60m"].sum()) if "in_pms_rolling_60m" in view else 0
n_db = view["db_code"].nunique() if "db_code" in view else 0
min_yr = view["invoice_year"].dropna().min() if "invoice_year" in view else "—"
max_yr = view["invoice_year"].dropna().max() if "invoice_year" in view else "—"

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Vehicles in cohort", f"{n_total:,}")
with k2:
    st.metric("In PMS rolling-60m", f"{n_pms:,} ({n_pms / n_total * 100:.0f}%)" if n_total else "—")
with k3:
    st.metric("Distributors", f"{n_db}")
with k4:
    st.metric("Cohort years", f"{min_yr}–{max_yr}")

st.divider()

# ── Cohort aging ───────────────────────────────────────────────────────────────
st.markdown("#### Cohort aging — vehicles by invoice year")
if "invoice_year" in view:
    try:
        age = view["invoice_year"].value_counts().sort_index().reset_index()
        age.columns = ["invoice_year", "count"]
        fig_age = px.bar(
            age, x="invoice_year", y="count",
            color_discrete_sequence=[ISZE_BLUE],
            labels={"invoice_year": "Invoice year", "count": "Vehicles"},
        )
        fig_age.update_layout(
            height=360, margin=dict(l=10, r=10, t=20, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(gridcolor="#F0F0F0"),
        )
        st.plotly_chart(style(fig_age), width="stretch")
    except Exception as e:
        st.warning(f"Cohort chart unavailable: {e}")

st.divider()

# ── Series / GVW mix ──────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    st.markdown("#### Series mix (N vs F)")
    if "series" in view:
        try:
            s = view["series"].value_counts().reset_index()
            s.columns = ["series", "count"]
            fig_s = px.pie(s, names="series", values="count", hole=0.45,
                           color_discrete_sequence=[ISZE_BLUE, ISZE_ORANGE, "#8FA9C9", "#F4A460"])
            fig_s.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(style(fig_s), width="stretch")
        except Exception as e:
            st.warning(f"Series chart unavailable: {e}")
with c2:
    st.markdown("#### Nominal GVW class")
    if "gvw_t" in view:
        try:
            g = view["gvw_t"].value_counts().sort_index().reset_index()
            g.columns = ["gvw_t", "count"]
            fig_g = px.bar(g, x="gvw_t", y="count",
                           color_discrete_sequence=[ISZE_ORANGE],
                           labels={"gvw_t": "GVW (t)", "count": "Vehicles"})
            fig_g.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10),
                                plot_bgcolor="white", paper_bgcolor="white",
                                yaxis=dict(gridcolor="#F0F0F0"))
            st.plotly_chart(style(fig_g), width="stretch")
        except Exception as e:
            st.warning(f"GVW chart unavailable: {e}")

st.divider()

# ── By distributor ─────────────────────────────────────────────────────────────
st.markdown("#### Vehicles by distributor (cohort)")
if "db_code" in view:
    try:
        dbc = view["db_code"].value_counts().head(20).reset_index()
        dbc.columns = ["distributor", "count"]
        fig_d = px.bar(dbc.sort_values("count"), x="count", y="distributor", orientation="h",
                       color_discrete_sequence=[ISZE_BLUE],
                       labels={"count": "Vehicles", "distributor": "Distributor"})
        fig_d.update_layout(height=max(320, len(dbc) * 24), margin=dict(l=10, r=10, t=10, b=20),
                            plot_bgcolor="white", paper_bgcolor="white",
                            xaxis=dict(gridcolor="#F0F0F0"))
        st.plotly_chart(style(fig_d), width="stretch")
    except Exception as e:
        st.warning(f"Distributor chart unavailable: {e}")

st.markdown(
    '<div class="footer-note">PRISM Parc Cohorts | Module 22 | '
    'Source: 01_data/07_UIO/vin/VIN_register.csv | Cohort only — NOT UIO v19 | ex ITUK/UTI</div>',
    unsafe_allow_html=True,
)
