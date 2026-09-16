"""PRISM — AIM Risk Review page."""

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
from modules.aim_review_charts import (  # noqa: E402
    render_family_detail,
    render_gap_closer,
    render_network_overview,
)


st.markdown(
    """
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .aim-hero {
        background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.25rem;
    }
    .aim-hero h1 { color: #fff !important; margin: 0; font-size: 1.75rem; font-weight: 700; }
    .aim-hero p  { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
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
<div class="aim-hero">
  <h1>AIM Risk Review</h1>
  <p>AIM classification exposure by distributor and product family</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading data bundle…")
def _load():
    return load_bvp_bundle()


bundle = _load()
aim_db: pd.DataFrame = bundle.get("aim_db", pd.DataFrame())
aim_family: pd.DataFrame = bundle.get("aim_family", pd.DataFrame())

if aim_db.empty:
    st.warning(
        "AIM exposure data not loaded. "
        "Run `python scripts/build_strategic_contracts.py` to build derived CSVs, then reload."
    )
    st.stop()

aim_years = sorted(aim_db["year"].dropna().astype(int).unique().tolist())
aim_dists = sorted(aim_db["distributor_code"].dropna().unique().tolist())
latest_year = aim_years[-1] if aim_years else None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### AIM Scope")
    year_sel = st.selectbox(
        "Year",
        options=aim_years,
        index=len(aim_years) - 1 if aim_years else 0,
    )
    dist_multi = st.multiselect(
        "Distributors",
        options=aim_dists,
        default=aim_dists,
    )

selected_year = int(year_sel) if year_sel is not None else latest_year

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_network, tab_family, tab_gap, tab_export = st.tabs(
    ["Network Overview", "Family Detail", "Gap Closer", "Export"]
)

with tab_network:
    render_network_overview(aim_db, selected_year, dist_multi, aim_dists)

with tab_family:
    render_family_detail(aim_family, selected_year)

with tab_gap:
    render_gap_closer(DERIVED_DIR)

with tab_export:
    export_db = aim_db[
        (aim_db["year"] == selected_year)
        & (aim_db["distributor_code"].isin(dist_multi if dist_multi else aim_dists))
    ].copy()

    export_fam = pd.DataFrame()
    if not aim_family.empty:
        export_fam = aim_family[
            (aim_family["year"] == selected_year)
            & (aim_family["distributor_code"].isin(dist_multi if dist_multi else aim_dists))
        ].copy()

    st.subheader("AIM Exposure — Network level")
    st.dataframe(export_db, width='stretch', hide_index=True)

    if not export_db.empty:
        st.download_button(
            label=f"Download ISZE_AIM_Review_{selected_year}.csv",
            data=export_db.to_csv(index=False).encode("utf-8"),
            file_name=f"ISZE_AIM_Review_{selected_year}.csv",
            mime="text/csv",
        )

    if not export_fam.empty:
        st.subheader("AIM Family Risk")
        st.dataframe(export_fam, width='stretch', hide_index=True)
        st.download_button(
            label=f"Download ISZE_AIM_Family_{selected_year}.csv",
            data=export_fam.to_csv(index=False).encode("utf-8"),
            file_name=f"ISZE_AIM_Family_{selected_year}.csv",
            mime="text/csv",
        )

st.caption(f"AIM Review · Data: `{DERIVED_DIR}`")
