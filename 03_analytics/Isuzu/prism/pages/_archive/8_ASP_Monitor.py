"""PRISM — ASP Deviation Monitor page."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402
from modules.bvp_dashboard_data import load_bvp_bundle  # noqa: E402
from modules.asp_charts import (  # noqa: E402
    compute_asp_deviation,
    render_alert_table,
    render_deviation_heatmap,
    render_distributor_drilldown,
)


st.markdown(
    """
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .asp-hero {
        background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.25rem;
    }
    .asp-hero h1 { color: #fff !important; margin: 0; font-size: 1.75rem; font-weight: 700; }
    .asp-hero p  { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
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
<div class="asp-hero">
  <h1>Selling-Price Discipline</h1>
  <p>Where each market sells genuine parts above or below the network norm — a pricing-discipline and margin signal.</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading data bundle…")
def _load():
    return load_bvp_bundle()


bundle = _load()
pms_opp: pd.DataFrame = bundle.get("pms_opportunity", pd.DataFrame())

if pms_opp.empty or "avg_sp_eur" not in pms_opp.columns:
    st.warning(
        "PMS opportunity data not loaded or missing avg_sp_eur column. "
        "Run `python scripts/build_strategic_contracts.py` to rebuild derived CSVs."
    )
    st.stop()

opp_years = sorted(pms_opp["year"].dropna().astype(int).unique().tolist())
opp_dists = sorted(pms_opp["distributor_code"].dropna().unique().tolist())
latest_year = opp_years[-1] if opp_years else None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ASP Scope")
    year_sel = st.selectbox(
        "Year",
        options=opp_years,
        index=len(opp_years) - 1 if opp_years else 0,
    )
    threshold_pct = st.slider(
        "Alert threshold (%)",
        min_value=5,
        max_value=30,
        value=10,
        step=1,
        help="Flag distributors where |ASP deviation| exceeds this threshold",
    )

selected_year = int(year_sel) if year_sel is not None else latest_year


@st.cache_data(show_spinner=False)
def _compute_asp(df: pd.DataFrame, yr: int) -> pd.DataFrame:
    return compute_asp_deviation(df, yr)


asp_df = _compute_asp(pms_opp, selected_year)

render_deviation_heatmap(asp_df, selected_year)
st.markdown("---")
render_alert_table(asp_df, threshold_pct, selected_year)
st.markdown("---")
render_distributor_drilldown(asp_df, opp_dists, selected_year)

st.caption(f"ASP Monitor · Data: `{DERIVED_DIR}`")
