"""
PRISM — Offset Insights (6 new cross-data visuals)

Movement, lumpiness→airfreight, demand-flow Sankey, VOR pricing power,
premium-vs-defection, capture-ceiling bridge. All figures come from
modules/advanced_visuals.py so they are identical in Quarto / Dash.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR, is_internal_mode  # noqa: E402
from modules import advanced_visuals as av  # noqa: E402
from modules.internal_gate import OFFSET_DEMAND_FLOW, offset_tab_labels  # noqa: E402

st.markdown(
    """
<style>
  .ofs-hero { background: linear-gradient(120deg,#1B3A6B 0%,#2C5AA0 60%,#E87722 100%);
    padding:1.25rem 1.5rem;border-radius:12px;margin-bottom:1.25rem;}
  .ofs-hero h1{color:#fff!important;margin:0;font-size:1.75rem;font-weight:700;}
  .ofs-hero p{color:#E8F0FA;margin:.35rem 0 0;font-size:.9rem;}
</style>
<div class="ofs-hero"><h1>Offset Insights</h1>
<p>Where parts revenue moves and what can be recovered.</p></div>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading distributors…")
def _distributors() -> list[str]:
    g = pd.read_csv(DERIVED_DIR / "gps_spu_by_distributor.csv")
    return sorted(g["distributor_code"].dropna().unique().tolist())


dists = _distributors()
default_ix = dists.index("ITUK") if "ITUK" in dists else 0
highlight = st.selectbox("Highlight distributor", dists, index=default_ix)

internal = is_internal_mode()
if internal:
    st.caption(
        "⚠️ The Sankey 'Leakage' leg and any leakage figure are an INFERENCE "
        "(under-service gap), not a measured competitor number — internal use only."
    )

tab_names = offset_tab_labels(internal=internal)
tabs = st.tabs(tab_names)
tab_by_name = dict(zip(tab_names, tabs))

with tab_by_name["1 · Movement"]:
    st.markdown("Each distributor's path 2023→2025 on GPS/SPU × capture. **Arrow = direction of travel.**")
    st.plotly_chart(av.fig_trajectory_quiver(DERIVED_DIR, highlight), width='stretch')
with tab_by_name["2 · Lumpiness→Airfreight"]:
    st.markdown("Offset of demand-class work × VOR data: do families with lumpy demand generate more airfreight?")
    st.plotly_chart(av.fig_lumpiness_airfreight(DERIVED_DIR), width='stretch')
if OFFSET_DEMAND_FLOW in tab_by_name:
    with tab_by_name[OFFSET_DEMAND_FLOW]:
        st.markdown("Parc-implied demand (TAM) → genuine / BVP / leakage, by category.")
        st.plotly_chart(av.fig_demand_flow_sankey(DERIVED_DIR), width='stretch')
with tab_by_name["4 · VOR Pricing Power"]:
    st.markdown("Who runs high expedited volume at **zero premium** (bottom-right) — the repricing call list.")
    st.plotly_chart(av.fig_vor_pricing_power(DERIVED_DIR, highlight), width='stretch')
with tab_by_name["5 · Premium vs Defection"]:
    st.markdown("Does a higher genuine premium correlate with **lower** genuine unit share? (defection test)")
    st.plotly_chart(av.fig_premium_defection(DERIVED_DIR, highlight), width='stretch')
with tab_by_name["6 · Capture Ceiling"]:
    st.markdown(f"Current genuine € → recoverable layers → TAM ceiling for **{highlight}**.")
    st.plotly_chart(av.fig_capture_ceiling(DERIVED_DIR, highlight), width='stretch')
