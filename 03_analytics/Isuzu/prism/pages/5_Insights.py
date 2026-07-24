"""
PRISM — Layer 3: Cross-Module Intelligence
Combines GPS, PMS, and BVP signals across distributors and time.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import (
    BETA_MODE,
    DERIVED_DIR,
    resolve_mapping_path,
    resolve_uio_path,
)
from modules.bvp_dashboard_data import load_bvp_bundle, derived_status
from modules.data_prep import load_distributor_mapping, load_uio_from_excel, get_distributor_metadata
from modules.sales_loader import load_prism_sales
from modules.gps_engine import calculate_multiyear_trends
from modules.pms_engine import classify_pms_sales
from modules.insights_charts import (
    render_bvp_capture_quadrant,
    render_capture_trajectory,
    render_displacement_severity,
    render_growth_decomposition,
    render_network_benchmark,
    render_opportunity_matrix,
    render_pareto,
    render_seasonal_pattern,
)

# ---------------------------------------------------------------------------
# CSS and beta banner
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .ins-hero {
        background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.25rem;
    }
    .ins-hero h1 { color: #fff !important; margin: 0; font-size: 1.75rem; font-weight: 700; }
    .ins-hero p { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
    .insight-card {
        background: #F8FAFC; border: 1px solid #E2E8F0;
        border-left: 4px solid #E87722; border-radius: 8px;
        padding: 0.85rem 1rem; margin: 0.5rem 0 1rem; font-size: 0.92rem;
    }
    div[data-testid="metric-container"] {
        border: 1px solid #E0E0E0; border-left: 4px solid #1B3A6B;
        border-radius: 8px; background: #fff;
    }
    [data-testid="stMetricValue"] { color: #1B3A6B; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

if st.session_state.get("beta_mode", BETA_MODE):
    st.warning("BETA MODE — not for distribution", icon="⚠️")

st.markdown("""
<div class="ins-hero">
  <h1>🔭 Insights — Where the Network Wins and Leaks</h1>
  <p>The signals that only surface when genuine-parts spend, service capture and aftermarket pressure are read together.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data loading (all cached)
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Loading BVP bundle…")
def _load_bundle():
    return load_bvp_bundle()


@st.cache_data(show_spinner="Loading mapping…")
def _load_mapping():
    return load_distributor_mapping(str(resolve_mapping_path()))


@st.cache_data(show_spinner="Loading UIO…")
def _load_uio():
    return load_uio_from_excel(str(resolve_uio_path()))


@st.cache_data(show_spinner="Loading sales…")
def _load_sales(_hash):
    df_map = _load_mapping()
    df, _ = load_prism_sales(df_map)
    return df


@st.cache_data(show_spinner="Computing GPS trends…")
def _load_gps_trends(year_type):
    df_map = _load_mapping()
    df_uio = _load_uio()
    df_meta = get_distributor_metadata(df_map)
    df_sales = _load_sales("v1")
    return calculate_multiyear_trends(df_sales, df_uio, df_meta, year_type=year_type)


@st.cache_data(show_spinner="Computing monthly PMS…")
def _load_monthly_pms(year_type):
    df_sales = _load_sales("v1")
    df_classified = classify_pms_sales(df_sales)
    col = "fiscal_year" if year_type == "fiscal" else "year"
    grp = (
        df_classified[df_classified["is_pms"]]
        .groupby([col, "month", "pms_category"])
        .agg(qty=("billed_qty", "sum"), revenue_eur=("net_sales_value", "sum"))
        .reset_index()
        .rename(columns={col: "year_value"})
    )
    return grp


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

bundle = _load_bundle()
status = derived_status()

try:
    df_mapping = _load_mapping()
    df_meta = get_distributor_metadata(df_mapping)
    df_sales = _load_sales("v1")
    sales_ok = True
except Exception:
    sales_ok = False

pms_all = bundle["pms_capture"]
mix_sub = bundle["mix_subgroup"]
aim_db = bundle["aim_db"]
sub_pair = bundle["substitution_pair"]

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Scope")
    year_type_label = st.radio(
        "Year type",
        ["Calendar Year", "Fiscal Year (Apr–Mar)"],
        help="FY2024 = Apr 2024 – Mar 2025.",
    )
    year_type = "fiscal" if "Fiscal" in year_type_label else "calendar"

    years_avail = []
    if not pms_all.empty and "year" in pms_all.columns:
        years_avail = sorted(pms_all["year"].dropna().astype(int).unique().tolist())
    year_sel = st.multiselect(
        "Years",
        years_avail,
        default=years_avail[-2:] if len(years_avail) >= 2 else years_avail,
    )
    latest_y = max(year_sel) if year_sel else (max(years_avail) if years_avail else None)

    dists_avail = []
    if not pms_all.empty and "distributor_code" in pms_all.columns:
        dists_avail = sorted(pms_all["distributor_code"].dropna().unique().tolist())
    dist_sel = st.multiselect("Distributors", dists_avail, default=dists_avail)

    st.divider()
    for label, ok in list(status.items())[:10]:
        st.write(f"{'✅' if ok else '❌'} `{label}`")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_opp, tab_quad, tab_growth, tab_traj, tab_bench, tab_disp, tab_seas, tab_pareto = st.tabs([
    "🎯 Opportunity Matrix",
    "📐 BVP × Capture",
    "📈 Growth Decomp",
    "🔥 Trajectory",
    "🏆 Benchmark",
    "💀 Displacement",
    "📅 Seasonal",
    "📊 Pareto",
])

with tab_opp:
    render_opportunity_matrix(pms_all, aim_db, mix_sub, dist_sel, dists_avail, latest_y)

with tab_quad:
    render_bvp_capture_quadrant(pms_all, mix_sub, dist_sel, dists_avail, latest_y)

with tab_growth:
    if not sales_ok:
        st.info("Sales data not loaded — cannot compute GPS trends.")
    else:
        try:
            df_trend = _load_gps_trends(year_type)
        except Exception as e:
            st.warning(f"GPS trend load failed: {e}")
        else:
            render_growth_decomposition(df_trend, dist_sel)

with tab_traj:
    render_capture_trajectory(pms_all, dist_sel, dists_avail)

with tab_bench:
    render_network_benchmark(pms_all, dist_sel, dists_avail, latest_y)

with tab_disp:
    render_displacement_severity(sub_pair, year_sel, dist_sel, latest_y)

with tab_seas:
    if not sales_ok:
        st.info("Sales data not loaded — cannot compute monthly pattern.")
    else:
        try:
            df_pms_monthly = _load_monthly_pms(year_type)
        except Exception as e:
            st.warning(f"Seasonal chart failed: {e}")
        else:
            render_seasonal_pattern(df_pms_monthly)

with tab_pareto:
    if not sales_ok:
        st.info("Sales data not loaded.")
    else:
        try:
            render_pareto(df_sales, dist_sel, year_type)
        except Exception as e:
            st.warning(f"Pareto chart failed: {e}")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.caption(
    "PRISM Cross-Module Intelligence · Layer 3 · "
    f"Data: GPS + PMS + BVP bundle · Derived: `{DERIVED_DIR}` · "
    "Rebuild all: `build_sales_fact_from_cy.py` → `build_bvp_p*.py`"
)
