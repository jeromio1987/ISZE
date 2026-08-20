"""PRISM - Customer Aftersales-Risk Ranking.

Parked 2026-08-18: unvalidated hand-weighted 0–100. Not a KPI. Early Warning
is the call list. Aftermarket scrape stays behind the internal launcher.

Source: db_aftersales_risk.csv (build_db_aftersales_risk.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR, is_internal_mode  # noqa: E402
from modules.internal_gate import CUSTOMER_RISK_SCRAPE, customer_risk_tab_labels  # noqa: E402
from modules.customer_risk_charts import (  # noqa: E402
    DEFAULT_W,
    STREET_FACTOR,
    compute_risk_scores,
    load_eucon_scrape,
    render_aftermarket_scrape,
    render_ranking_table,
    render_signal_breakdown,
    render_threat_map,
)


st.markdown(
    """
<style>
    .cr-hero { background: linear-gradient(120deg,#1B3A6B 0%,#2C5AA0 55%,#E87722 100%);
        padding:1.25rem 1.5rem;border-radius:12px;margin-bottom:1.1rem; }
    .cr-hero h1 { color:#fff!important;margin:0;font-size:1.7rem;font-weight:700; }
    .cr-hero p  { color:#E8F0FA;margin:.35rem 0 0;font-size:.9rem; }
    div[data-testid="metric-container"] { border:1px solid #E0E0E0;border-left:4px solid #1B3A6B;
        border-radius:8px;background:#fff; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="cr-hero">
  <h1>Customer Aftersales-Risk Ranking</h1>
  <p>Four aftersales signals, ranked. This is <b>not</b> a validated forecast —
  Early Warning is the call list. Prices compared at reference sell-out
  (list ×1.40 ×1.275 = ×1.785).</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading risk model...")
def _load() -> pd.DataFrame:
    fp = Path(DERIVED_DIR) / "db_aftersales_risk.csv"
    if not fp.exists():
        return pd.DataFrame()
    return pd.read_csv(fp)


df = _load()
if df.empty:
    st.warning(
        "Risk model not built. Run `python scripts/build_db_aftersales_risk.py` "
        "to generate `db_aftersales_risk.csv`, then reload."
    )
    st.stop()

year = int(df["year"].iloc[0])

st.warning(
    "This 0–100 ranking is an unvalidated hand-weighted rubric. It is not a KPI "
    "and it did not beat last year on a holdout. Use **Early Warning** for who "
    "to call this cycle."
)

# --------------------------------------------------------------------------
# Sidebar -- live re-weighting (recomputes score from stored n_* components)
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### Risk weights - {year}")
    st.caption("Re-weight the four signals. They are renormalised to sum to 1.")
    w_eucon = st.slider(
        "Aftermarket undercut vs reference sell-out", 0.0, 1.0, DEFAULT_W["eucon"], 0.05
    )
    w_aim = st.slider("AIM scraper high-risk %", 0.0, 1.0, DEFAULT_W["aim"], 0.05)
    w_contested = st.slider("Contested BVP capture", 0.0, 1.0, DEFAULT_W["contested"], 0.05)
    w_vor = st.slider("VOR / urgent share", 0.0, 1.0, DEFAULT_W["vor"], 0.05)
    if st.button("Reset to defaults"):
        st.rerun()

w_sum = w_eucon + w_aim + w_contested + w_vor or 1.0
W = {
    "eucon": w_eucon / w_sum,
    "aim": w_aim / w_sum,
    "contested": w_contested / w_sum,
    "vor": w_vor / w_sum,
}

df = compute_risk_scores(df, W)

# --------------------------------------------------------------------------
# KPI row
# --------------------------------------------------------------------------
top = df.iloc[0]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Highest-risk distributor", top["distributor_code"], f"score {top['risk_score']:.0f}")
k2.metric("Eucon undercut rev (network)", f"EUR {df['eucon_undercut_rev_eur'].sum():,.0f}")
k3.metric("AIM high-risk rev (network)", f"EUR {df['high_risk_rev_eur'].sum():,.0f}")
k4.metric("Contested rev (network)", f"EUR {df['contested_eur'].sum():,.0f}")

st.caption(
    "Score is a weighted **intensity index (0-100)**, not a euro sum. Internal down-trade "
    "(BVP capture) and external walk-out (Eucon/AIM) are different threats and are never added "
    "as euros - euro columns are shown separately for context."
)

internal = is_internal_mode()
tab_names = customer_risk_tab_labels(internal=internal)
tabs = st.tabs(tab_names)
tab_by_name = dict(zip(tab_names, tabs))

with tab_by_name["Ranking"]:
    render_ranking_table(df)

with tab_by_name["Signal breakdown"]:
    render_signal_breakdown(df)

with tab_by_name["Threat map"]:
    render_threat_map(df)

@st.cache_data(show_spinner="Loading scrape...")
def _load_eucon() -> pd.DataFrame:
    return load_eucon_scrape(DERIVED_DIR, STREET_FACTOR)


if CUSTOMER_RISK_SCRAPE in tab_by_name:
    with tab_by_name[CUSTOMER_RISK_SCRAPE]:
        st.caption(
            "PartsPool Autodoc DE/NO dated 29 Mar 2026 — not the 2023 UK workshop survey."
        )
        render_aftermarket_scrape(_load_eucon(), STREET_FACTOR)

with tab_by_name["Export"]:
    st.caption(f"Weights applied: {', '.join(f'{k} {v:.0%}' for k, v in W.items())}")
    st.dataframe(df, width="stretch", hide_index=True)
    st.download_button(
        f"Download ISZE_Customer_Risk_{year}.csv",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"ISZE_Customer_Risk_{year}.csv", mime="text/csv",
    )

st.caption(
    f"Customer Risk - {year} - source: db_aftersales_risk.csv - "
    f"reference sell-out factor ×{STREET_FACTOR} (unvalidated ranking)"
)
