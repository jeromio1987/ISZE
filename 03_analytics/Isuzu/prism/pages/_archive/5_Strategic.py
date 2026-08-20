"""
PRISM — Strategic Views

All 13 remaining dashboards from docs/dashboard_contracts.md.
Most-exposed (Contract 4) lives on Early Warning. Basket correlation
(Contract 8) is parked — CSV still built, tab dropped 2026-08-18.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402
from modules.ui_links import page_link  # noqa: E402
from modules.bvp_dashboard_data import load_bvp_bundle  # noqa: E402
from modules.strategic_charts import (  # noqa: E402
    render_capture_recovery,
    render_capture_trajectory,
    render_geographic_risk,
    render_network_percentile,
    render_part_lifecycle,
    render_pms_opportunity,
    render_price_premium,
    render_revenue_concentration,
    render_revenue_waterfall,
    render_substitution_timeline,
    render_vor_airfreight,
    render_vor_profile,
    render_vor_seasonality,
)

st.markdown(
    """
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .strat-hero {
        background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.25rem;
    }
    .strat-hero h1 { color: #fff !important; margin: 0; font-size: 1.75rem; font-weight: 700; }
    .strat-hero p  { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
    div[data-testid="metric-container"] {
        border: 1px solid #E0E0E0; border-left: 4px solid #1B3A6B;
        border-radius: 8px; background: #fff;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="strat-hero">
  <h1>Strategic Views</h1>
  <p>Where revenue and risk concentrate across the network — capture, price premium, stockouts and aftermarket pressure, in one place.</p>
</div>
""",
    unsafe_allow_html=True,
)

page_link(
    "pages/0_Early_Warning.py",
    "Early Warning — who to call this cycle",
    "🚨",
)
st.caption(
    "Triple-threat scatter is not on this page — Early Warning is the call list. "
    "Basket correlation is parked (`basket_correlation.csv` still builds)."
)


@st.cache_data(show_spinner="Loading strategic bundle…")
def _load():
    return load_bvp_bundle()


bundle = _load()
gps_db = bundle.get("gps_db", pd.DataFrame())
years_avail = (
    sorted(gps_db["year"].dropna().astype(int).unique().tolist()) if not gps_db.empty else []
)
dists_avail = (
    sorted(gps_db["distributor_code"].dropna().unique().tolist()) if not gps_db.empty else []
)

with st.sidebar:
    st.markdown("### Scope")
    year_sel = st.multiselect("Years", years_avail, default=years_avail[-3:] if years_avail else [])
    highlight = st.selectbox(
        "Highlight distributor",
        ["ITUK"] + [d for d in dists_avail if d != "ITUK"],
    )
    latest_y = max(year_sel) if year_sel else (max(years_avail) if years_avail else None)

(
    tab_opp,
    tab_pct,
    tab_gold,
    tab_vor_season,
    tab_vor_prof,
    tab_traj,
    tab_life,
    tab_gini,
    tab_water,
    tab_prem,
    tab_sub,
    tab_geo,
    tab_rec,
) = st.tabs(
    [
        "PMS opportunity (€)",
        "Network ranking",
        "Airfreight cost (emergency)",
        "Stockout seasonality",
        "Stockout profile",
        "Capture trend",
        "Part lifecycle",
        "Revenue concentration",
        "Revenue bridge",
        "Price vs aftermarket",
        "Aftermarket substitution",
        "Geographic risk",
        "Capture recovery (€)",
    ]
)

with tab_opp:
    render_pms_opportunity(bundle.get("pms_opportunity"), year_sel, highlight, latest_y)

with tab_pct:
    render_network_percentile(bundle.get("network_percentile"), year_sel, highlight, latest_y)

with tab_gold:
    render_vor_airfreight(bundle.get("vor_airfreight"), year_sel, highlight, latest_y)

with tab_vor_season:
    render_vor_seasonality(bundle.get("vor_seasonality"), year_sel, highlight, latest_y)

with tab_vor_prof:
    render_vor_profile(bundle.get("vor_profile"), year_sel, highlight, latest_y)

with tab_traj:
    render_capture_trajectory(bundle.get("capture_trajectory"), year_sel, highlight, latest_y)

with tab_life:
    render_part_lifecycle(bundle.get("part_lifecycle"), highlight)

with tab_gini:
    render_revenue_concentration(bundle.get("revenue_concentration"), year_sel, highlight, latest_y)

with tab_water:
    render_revenue_waterfall(bundle.get("revenue_waterfall"), year_sel, highlight)

with tab_prem:
    render_price_premium(bundle.get("price_premium"), year_sel, highlight, latest_y)

with tab_sub:
    render_substitution_timeline(bundle.get("substitution_timeline"), year_sel, highlight)

with tab_geo:
    render_geographic_risk(
        bundle.get("distributor_geo"),
        bundle.get("gps_db"),
        year_sel,
        highlight,
        latest_y,
    )

with tab_rec:
    render_capture_recovery(bundle.get("capture_recovery"), highlight)

st.caption(
    f"Strategic Views · Data: `{DERIVED_DIR}` · "
    "Rebuild: `python scripts/build_strategic_contracts.py`"
)
