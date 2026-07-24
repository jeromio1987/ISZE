"""PRISM - Customer Aftersales-Risk Ranking.

Which distributors carry the most aftersales risk? Blends four per-DB signals
(Eucon street-undercut price exposure, AIM scraper high-risk %, contested BVP
capture, VOR/urgent share) into one weighted intensity index. Re-weight live in
the sidebar. Source: db_aftersales_risk.csv (build_db_aftersales_risk.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402
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
  <p>Which customers are most likely to defect to aftermarket — ranked by price exposure, competitive pressure and urgency.
  Prices grossed to street (list ×1.40 ×1.275 = ×1.785), since ISZE sits upstream.</p>
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

# --------------------------------------------------------------------------
# Sidebar -- live re-weighting (recomputes score from stored n_* components)
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### Risk weights - {year}")
    st.caption("Re-weight the four signals. They are renormalised to sum to 1.")
    w_eucon = st.slider("Eucon price undercut (street)", 0.0, 1.0, DEFAULT_W["eucon"], 0.05)
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

tab_rank, tab_break, tab_map, tab_scrape, tab_export = st.tabs(
    ["Ranking", "Signal breakdown", "Threat map", "Aftermarket scrape", "Export"]
)

with tab_rank:
    render_ranking_table(df)

with tab_break:
    render_signal_breakdown(df)

with tab_map:
    render_threat_map(df)

@st.cache_data(show_spinner="Loading scrape...")
def _load_eucon() -> pd.DataFrame:
    return load_eucon_scrape(DERIVED_DIR, STREET_FACTOR)


with tab_scrape:
    render_aftermarket_scrape(_load_eucon(), STREET_FACTOR)

with tab_export:
    st.caption(f"Weights applied: {', '.join(f'{k} {v:.0%}' for k, v in W.items())}")
    st.dataframe(df, width="stretch", hide_index=True)
    st.download_button(
        f"Download ISZE_Customer_Risk_{year}.csv",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"ISZE_Customer_Risk_{year}.csv", mime="text/csv",
    )

st.caption(f"Customer Risk - {year} - source: db_aftersales_risk.csv - street factor x{STREET_FACTOR}")
