# PRISM Layer 1 — UIO is the denominator for all metrics in this application

"""
PRISM — Module 1: Fleet (Units in Operation)

The installed base = the engine of the aftersales business. Every truck on the
road is recurring genuine-parts and PMS demand. This page leads with that
story (MD view); the denominator/methodology detail is kept in an expander
for the analysts. Data role for GPS/PMS is unchanged.
"""

import sys
from pathlib import Path

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from config import BETA_MODE, resolve_uio_path
from modules.data_prep import load_uio_from_excel
from modules.plotly_style import style

# ─── Constants ────────────────────────────────────────────────────────────────

ISZE_BLUE = "#1B3A6B"
ISZE_RED = "#E3001B"
CHART_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font_color="#333333",
    xaxis=dict(gridcolor="#F0F0F0", linecolor="#CCCCCC"),
    yaxis=dict(gridcolor="#F0F0F0", linecolor="#CCCCCC"),
    margin=dict(l=40, r=20, t=40, b=40),
)

# Official IML surviving parc figures (fixed until new IML data received)
IML_N75_PARC = 8_515
IML_N75_TOTAL = 12_228
IML_N75_ATTRITION = 28.5

IML_N35_PARC = 9_818
IML_N35_TOTAL = 10_919
IML_N35_ATTRITION = 9.4

SERVICE_FREQ = 0.5  # services/year — 40,000 km interval ÷ ~20,000 km/yr
CORE_PARC = IML_N75_PARC + IML_N35_PARC
SERVICE_EVENTS = int(CORE_PARC * SERVICE_FREQ)

# distributor_code → country (most codes are already country names)
CODE_TO_COUNTRY = {
    "ITUK": "United Kingdom", "IUK": "United Kingdom",
    "UTI": "Israel", "UMI": "Israel",
}


def to_country(code: str) -> str:
    return CODE_TO_COUNTRY.get(code, str(code).replace("_", " ").title())


# set_page_config is handled by app.py — do not call it in sub-pages

if st.session_state.get("beta_mode", BETA_MODE):
    st.warning("BETA MODE — not for distribution", icon="⚠️")

st.title("🚛 Fleet on the Road — the Engine of Aftersales")
st.caption(
    "Every Isuzu in operation is recurring genuine-parts and PMS demand. "
    "How big the base is, where it sits, and whether it is growing."
)

st.divider()

# ─── Load UIO data ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading fleet data...")
def _load_uio() -> pd.DataFrame:
    return load_uio_from_excel(str(resolve_uio_path()))


df_uio = pd.DataFrame()
uio_path = None
try:
    uio_path = resolve_uio_path()
    df_uio = _load_uio()
except FileNotFoundError:
    pass
except Exception as exc:
    st.warning(f"Unexpected error loading fleet data: `{exc}`.", icon="⚠️")

if df_uio.empty:
    st.warning(
        "Fleet (UIO) workbook not found.\n\n"
        "Place the IML UIO Excel (V17) in `ISZE/UIO/_CURRENT/` or `prism/data/`.",
        icon="📂",
    )
    if uio_path:
        st.caption(f"Last resolved path: `{uio_path}`")
    st.stop()

# Coerce types
required_cols = {"distributor_code", "year", "uio_units"}
if required_cols - set(df_uio.columns):
    st.error(f"Fleet data missing columns: `{required_cols - set(df_uio.columns)}`.", icon="🚫")
    st.stop()

df_uio["year"] = pd.to_numeric(df_uio["year"], errors="coerce")
df_uio["uio_units"] = pd.to_numeric(df_uio["uio_units"], errors="coerce")
df_uio = df_uio.dropna(subset=["year", "uio_units"])
df_uio["year"] = df_uio["year"].astype(int)
df_uio["uio_units"] = df_uio["uio_units"].astype(int)
df_uio["country"] = df_uio["distributor_code"].apply(to_country)

available_years = sorted(df_uio["year"].unique(), reverse=True)
latest = available_years[0]
prev = available_years[1] if len(available_years) > 1 else None

df_now = df_uio[df_uio["year"] == latest]
total_now = int(df_now["uio_units"].sum())
total_prev = int(df_uio[df_uio["year"] == prev]["uio_units"].sum()) if prev else None
yoy_abs = (total_now - total_prev) if total_prev else None
yoy_pct = (100 * yoy_abs / total_prev) if total_prev else None

by_country = (
    df_now.groupby("country")["uio_units"].sum().sort_values(ascending=False)
)
n_markets = by_country.shape[0]
top_ctry = by_country.index[0]
top_ctry_share = round(100 * by_country.iloc[0] / total_now)
isr = int(by_country.get("Israel", 0))
isr_rank = (list(by_country.index).index("Israel") + 1) if "Israel" in by_country.index else None

# ─── Hero KPIs ─────────────────────────────────────────────────────────────────

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric(
        "Isuzu fleet on the road",
        f"{total_now:,}",
        delta=(f"{yoy_abs:+,} vs {prev} ({yoy_pct:+.1f}%)" if yoy_abs is not None else None),
    )
with k2:
    st.metric("Markets", n_markets, help="Distributor territories with active UIO")
with k3:
    st.metric(
        "Core truck parc (N75+N35)",
        f"{CORE_PARC:,}",
        help="Official IML surviving parc — the PMS-tracked fleet",
    )
with k4:
    st.metric(
        "Scheduled services / year",
        f"≈ {SERVICE_EVENTS:,}",
        help=f"Core parc × {SERVICE_FREQ}/yr service frequency — the recurring PMS parts pulse",
    )

# ─── MD narrative ───────────────────────────────────────────────────────────────

trend_word = "growing" if (yoy_pct or 0) > 0.5 else "shrinking" if (yoy_pct or 0) < -0.5 else "flat"
trend_clause = (
    f"The base is <b>{trend_word}</b> ({yoy_pct:+.1f}% vs {prev}), "
    + ("<b>expanding</b>" if (yoy_pct or 0) >= 0 else "<b>eroding</b>")
    + " the addressable parts revenue."
    if yoy_pct is not None else ""
)
isr_clause = (
    f" <b>Israel</b> is the #{isr_rank} market ({isr:,} units)." if isr_rank else ""
)
st.markdown(
    f"""
<div style="background:linear-gradient(135deg,#16202e,#243345);color:#eef3f8;
border-radius:14px;padding:20px 24px;font-size:16px;line-height:1.55">
<b>{total_now:,}</b> Isuzu vehicles are in operation across <b>{n_markets}</b> markets —
the recurring engine of the parts business. The core N75/N35 truck parc
(<b>{CORE_PARC:,}</b> units) alone generates roughly <b>{SERVICE_EVENTS:,} scheduled
services a year</b>, each a genuine-parts and PMS opportunity. <b>{top_ctry}</b> leads
with {top_ctry_share}% of the fleet.{isr_clause} {trend_clause}
<span style="display:block;margin-top:10px;font-size:14px;color:#aab8c8;
border-top:1px solid #33455a;padding-top:10px">
→ A growing base lifts aftersales revenue even at flat capture; a shrinking one
erodes it regardless of how well we sell. This is the denominator every GPS and
PMS number divides by.</span>
</div>
""",
    unsafe_allow_html=True,
)

st.divider()

# ─── Where the fleet is (by market) ─────────────────────────────────────────────

st.subheader(f"Where the fleet is — by market · {latest}")
bc = by_country.sort_values(ascending=True)
fig_ctry = go.Figure(
    go.Bar(
        x=bc.values, y=bc.index, orientation="h",
        marker_color=[ISZE_RED if c in ("United Kingdom", "Israel") else ISZE_BLUE for c in bc.index],
        text=[f"{v:,}" for v in bc.values], textposition="outside",
    )
)
fig_ctry.update_layout(
    **CHART_LAYOUT, xaxis_title="Vehicles in operation", yaxis_title="",
    height=max(360, 26 * len(bc)),
)
st.plotly_chart(style(fig_ctry), width="stretch")
st.caption("UK and Israel highlighted — the two largest markets and the focus of current parts analysis.")

st.divider()

# ─── Is the engine growing? (total fleet trend) ─────────────────────────────────

st.subheader("Is the engine growing?")
trend = df_uio.groupby("year")["uio_units"].sum().reset_index()
trend = trend[trend["year"] <= 2024]  # actuals only; 2025+ is proxy
fig_tr = go.Figure(
    go.Bar(
        x=trend["year"], y=trend["uio_units"], marker_color=ISZE_BLUE,
        text=[f"{v:,}" for v in trend["uio_units"]], textposition="outside",
    )
)
fig_tr.update_layout(
    **CHART_LAYOUT, xaxis_title="Year", yaxis_title="Total fleet (UIO)", height=380,
)
fig_tr.update_xaxes(dtick=1, tickformat="d")
st.plotly_chart(style(fig_tr), width="stretch")
st.caption("Total Isuzu fleet on the road, all markets. 2020–2024 actuals (IML V17). 2025/26 use 2024 as proxy.")

st.divider()

# ─── Detail (analyst view, collapsed) ───────────────────────────────────────────

with st.expander("Distributor-level detail & methodology"):
    st.markdown(
        f"**Core parc attrition (official IML):** "
        f"N75 {IML_N75_ATTRITION}% ({IML_N75_TOTAL - IML_N75_PARC:,} of {IML_N75_TOTAL:,} attrited) · "
        f"N35 {IML_N35_ATTRITION}% ({IML_N35_TOTAL - IML_N35_PARC:,} of {IML_N35_TOTAL:,}). "
        f"Service frequency {SERVICE_FREQ}/yr = 40,000 km interval ÷ ~20,000 km/yr."
    )
    df_table = (
        df_now[["distributor_code", "country", "uio_units"]]
        .sort_values("uio_units", ascending=False)
        .reset_index(drop=True)
    )
    st.dataframe(df_table, width="stretch", hide_index=True)
    st.caption(
        f"UIO source: `{uio_path}` (IML V17, sheet `1.UIO Overview`). "
        "UIO = registered − attrited (surviving parc), the denominator for GPS (spend/unit) "
        "and PMS (capture rate). Annual refresh; see `data/README.md`."
    )
