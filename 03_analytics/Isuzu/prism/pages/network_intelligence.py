"""
PRISM — Network Intelligence (merged page, IA phase 3 · 2026-08-20).

One surface for "where does the network win or leak". Absorbs:
  5_Insights, 5_Strategic, 12_Offset_Insights, 7_AIM_Review, 8_ASP_Monitor, 16_AIM_GPS_Matrix
into 7 tabs per docs/DASHBOARD_IA.md §4.2. Customer Risk (15) is NOT merged here —
its Ranking is superseded by Early Warning; its Threat-map/Breakdown/scrape views
move to the Tools internal shelf in a later phase (IA §4.2 note, phase 7).

The internal-only Demand-Flow Sankey stays behind PRISM_INTERNAL.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import (  # noqa: E402
    AIM_GPS_MATRIX_CSV,
    BETA_MODE,
    DERIVED_DIR,
    is_internal_mode,
    resolve_mapping_path,
    resolve_uio_path,
)
from modules.bvp_dashboard_data import load_bvp_bundle, derived_status  # noqa: E402
from modules.data_prep import (  # noqa: E402
    get_distributor_metadata,
    load_distributor_mapping,
    load_uio_from_excel,
)
from modules.sales_loader import load_prism_sales  # noqa: E402
from modules.gps_engine import calculate_multiyear_trends  # noqa: E402
from modules.pms_engine import classify_pms_sales  # noqa: E402
from modules import advanced_visuals as av  # noqa: E402

from modules.insights_charts import (  # noqa: E402
    render_capture_trajectory as insights_capture_trajectory,
    render_displacement_severity,
    render_growth_decomposition,
    render_network_benchmark,
    render_opportunity_matrix,
    render_pareto,
    render_seasonal_pattern,
)
from modules.strategic_charts import (  # noqa: E402
    render_capture_recovery,
    render_capture_trajectory as strategic_capture_trajectory,
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
from modules.aim_review_charts import (  # noqa: E402
    render_family_detail,
    render_gap_closer,
    render_network_overview,
)
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
    .ni-hero { background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.1rem; }
    .ni-hero h1 { color: #fff !important; margin: 0; font-size: 1.7rem; font-weight: 700; }
    .ni-hero p  { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
    div[data-testid="metric-container"] { border: 1px solid #E0E0E0; border-left: 4px solid #1B3A6B;
        border-radius: 8px; background: #fff; }
</style>
""",
    unsafe_allow_html=True,
)

if st.session_state.get("beta_mode", BETA_MODE):
    st.warning("BETA MODE — not for distribution", icon="⚠️")

st.markdown(
    """
<div class="ni-hero">
  <h1>Network Intelligence</h1>
  <p>Where revenue and risk concentrate across the network — capture, spend, pricing, substitution and supply stress, fused into one surface.</p>
</div>
""",
    unsafe_allow_html=True,
)


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading data bundle…")
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
    return load_prism_sales(_load_mapping())[0]


@st.cache_data(show_spinner="Computing GPS trends…")
def _load_gps_trends(year_type):
    df_sales = _load_sales("v1")
    df_uio = _load_uio()
    df_meta = get_distributor_metadata(_load_mapping())
    return calculate_multiyear_trends(df_sales, df_uio, df_meta, year_type=year_type)


@st.cache_data(show_spinner="Computing monthly PMS…")
def _load_monthly_pms(year_type):
    df_classified = classify_pms_sales(_load_sales("v1"))
    col = "fiscal_year" if year_type == "fiscal" else "year"
    return (
        df_classified[df_classified["is_pms"]]
        .groupby([col, "month", "pms_category"])
        .agg(qty=("billed_qty", "sum"), revenue_eur=("net_sales_value", "sum"))
        .reset_index()
        .rename(columns={col: "year_value"})
    )


bundle = _load_bundle()
status = derived_status()

gps_db = bundle.get("gps_db", pd.DataFrame())
pms_all = bundle.get("pms_capture", pd.DataFrame())
mix_sub = bundle.get("mix_subgroup", pd.DataFrame())
aim_db = bundle.get("aim_db", pd.DataFrame())
aim_family = bundle.get("aim_family", pd.DataFrame())
sub_pair = bundle.get("substitution_pair", pd.DataFrame())
pms_opp = bundle.get("pms_opportunity", pd.DataFrame())

years_avail = (
    sorted(gps_db["year"].dropna().astype(int).unique().tolist()) if not gps_db.empty else []
)
dists_avail = (
    sorted(gps_db["distributor_code"].dropna().unique().tolist()) if not gps_db.empty else []
)

try:
    df_sales = _load_sales("v1")
    sales_ok = True
except Exception:
    df_sales = pd.DataFrame()
    sales_ok = False


# ── Unified sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Network scope")
    year_type_label = st.radio(
        "Year type",
        ["Calendar Year", "Fiscal Year (Apr–Mar)"],
        help="FY2024 = Apr 2024 – Mar 2025.",
    )
    year_type = "fiscal" if "Fiscal" in year_type_label else "calendar"

    year_sel = st.multiselect(
        "Years",
        years_avail,
        default=years_avail[-3:] if years_avail else [],
    )
    latest_y = max(year_sel) if year_sel else (max(years_avail) if years_avail else None)

    highlight = st.selectbox(
        "Highlight distributor",
        ["ITUK"] + [d for d in dists_avail if d != "ITUK"],
    )

    dist_sel = st.multiselect("Distributors", dists_avail, default=dists_avail)

    asp_threshold = st.slider("ASP alert threshold (%)", 5, 30, 10, 1)

    st.divider()
    st.caption(f"Data: `{DERIVED_DIR}`")
    for label, ok in list(status.items())[:8]:
        st.write(f"{'✅' if ok else '❌'} `{label}`")


# ── Tabs (IA §4.2) ───────────────────────────────────────────────────────────
(
    tab_opp,
    tab_growth,
    tab_bench,
    tab_pricing,
    tab_sub,
    tab_vor,
    tab_rev,
) = st.tabs(
    [
        "💶 Opportunity €",
        "📈 Trajectory & growth",
        "🏆 Benchmark & quadrant",
        "💰 Pricing & competition",
        "💀 Substitution pressure",
        "🚚 Supply stress (VOR)",
        "🏛️ Revenue structure",
    ]
)


def _guard(fn, *args, **kwargs):
    """Call a render fn; swallow a missing-CSV error into a friendly notice."""
    try:
        fn(*args, **kwargs)
    except Exception as e:  # noqa: BLE001
        st.info(f"View unavailable (build the derived CSV first): {e}")


# ── 2 · Opportunity € ─────────────────────────────────────────────────────────
with tab_opp:
    _guard(render_opportunity_matrix, pms_all, aim_db, mix_sub, dist_sel, dists_avail, latest_y)
    st.markdown("---")
    _guard(render_pms_opportunity, pms_opp, year_sel, highlight, latest_y)
    st.markdown("---")
    _guard(render_capture_recovery, bundle.get("capture_recovery", pd.DataFrame()), highlight)
    st.markdown("---")
    _guard(lambda: st.plotly_chart(av.fig_capture_ceiling(DERIVED_DIR, highlight), width="stretch"))

# ── 3 · Trajectory & growth ───────────────────────────────────────────────────
with tab_growth:
    _guard(insights_capture_trajectory, pms_all, dist_sel, dists_avail)
    st.markdown("---")
    _guard(strategic_capture_trajectory, bundle.get("capture_trajectory", pd.DataFrame()), year_sel, highlight, latest_y)
    st.markdown("---")
    if sales_ok:
        _guard(
            lambda: render_growth_decomposition(_load_gps_trends(year_type), dist_sel)
        )
    st.markdown("---")
    _guard(lambda: st.plotly_chart(av.fig_trajectory_quiver(DERIVED_DIR, highlight), width="stretch"))

# ── 4 · Benchmark & quadrant ──────────────────────────────────────────────────
with tab_bench:
    _guard(render_network_benchmark, pms_all, dist_sel, dists_avail, latest_y)
    st.markdown("---")
    _guard(render_network_percentile, bundle.get("network_percentile", pd.DataFrame()), year_sel, highlight, latest_y)
    st.markdown("---")
    if AIM_GPS_MATRIX_CSV.exists():
        m = pd.read_csv(AIM_GPS_MATRIX_CSV)
        myears = sorted(int(y) for y in m["year"].dropna().unique())
        complete = [y for y in myears if not bool(m.loc[m["year"] == y, "is_partial_year"].iloc[0])] if "is_partial_year" in m else myears
        dyear = (complete or myears)[-1] if myears else None
        if dyear is not None:
            import plotly.express as px
            sub = m[m["year"] == dyear].copy()
            med_g = float(sub["gps_median_benchmark_eur"].iloc[0]) if not sub.empty else float("nan")
            med_c = float(sub["capture_median_benchmark"].iloc[0]) if not sub.empty else float("nan")
            plot = sub[sub["gps_spu_eur"].notna() & sub["capture_axis"].notna()]
            fig = px.scatter(
                plot, x="capture_axis", y="gps_spu_eur", color="quadrant",
                hover_name="distributor_code", hover_data=["country", "gps_sales_eur"],
                labels={"capture_axis": "PMS capture", "gps_spu_eur": "GPS spend/unit (€)"},
                title=f"AIM × GPS quadrant (CY{dyear}) — median GPS €{med_g:,.0f} · capture {med_c:.1%}",
            )
            fig.add_hline(y=med_g, line_dash="dot", line_color="#999")
            fig.add_vline(x=med_c, line_dash="dot", line_color="#999")
            st.plotly_chart(fig, width="stretch")

# ── 5 · Pricing & competition ─────────────────────────────────────────────────
with tab_pricing:
    _guard(render_price_premium, bundle.get("price_premium", pd.DataFrame()), year_sel, highlight, latest_y)
    st.markdown("---")
    _guard(lambda: st.plotly_chart(av.fig_premium_defection(DERIVED_DIR, highlight), width="stretch"))
    st.markdown("---")
    if not pms_opp.empty and "avg_sp_eur" in pms_opp.columns:
        asp_years = sorted(pms_opp["year"].dropna().astype(int).unique().tolist())
        asp_year = asp_years[-1] if asp_years else None
        asp_df = compute_asp_deviation(pms_opp, asp_year)
        render_deviation_heatmap(asp_df, asp_year)
        render_alert_table(asp_df, asp_threshold, asp_year)
        render_distributor_drilldown(asp_df, sorted(pms_opp["distributor_code"].dropna().unique().tolist()), asp_year)
    st.markdown("---")
    if not aim_db.empty:
        aim_years = sorted(aim_db["year"].dropna().astype(int).unique().tolist())
        aim_year = aim_years[-1] if aim_years else None
        _guard(render_network_overview, aim_db, aim_year, dist_sel, dists_avail)
        _guard(render_family_detail, aim_family, aim_year)
        _guard(render_gap_closer, DERIVED_DIR)

# ── 6 · Substitution pressure ─────────────────────────────────────────────────
with tab_sub:
    _guard(render_displacement_severity, sub_pair, year_sel, dist_sel, latest_y)
    st.markdown("---")
    _guard(render_substitution_timeline, bundle.get("substitution_timeline", pd.DataFrame()), year_sel, highlight)
    st.markdown("---")
    _guard(render_part_lifecycle, bundle.get("part_lifecycle", pd.DataFrame()), highlight)

# ── 7 · Supply stress (VOR) ───────────────────────────────────────────────────
with tab_vor:
    st.caption(
        "VOR = **Vehicle Off Road** — urgent/expedited orders where the vehicle "
        "cannot wait for the normal replenishment cycle."
    )
    _guard(render_vor_airfreight, bundle.get("vor_airfreight", pd.DataFrame()), year_sel, highlight, latest_y)
    st.markdown("---")
    _guard(render_vor_seasonality, bundle.get("vor_seasonality", pd.DataFrame()), year_sel, highlight, latest_y)
    st.markdown("---")
    _guard(render_vor_profile, bundle.get("vor_profile", pd.DataFrame()), year_sel, highlight, latest_y)
    st.markdown("---")
    _guard(lambda: st.plotly_chart(av.fig_lumpiness_airfreight(DERIVED_DIR), width="stretch"))
    st.markdown("---")
    _guard(lambda: st.plotly_chart(av.fig_vor_pricing_power(DERIVED_DIR, highlight), width="stretch"))
    if is_internal_mode():
        st.markdown("---")
        st.caption(
            "⚠️ The Sankey 'Leakage' leg and any leakage figure are an INFERENCE "
            "(under-service gap), not a measured competitor number — internal use only."
        )
        _guard(lambda: st.plotly_chart(av.fig_demand_flow_sankey(DERIVED_DIR), width="stretch"))

# ── 8 · Revenue structure ─────────────────────────────────────────────────────
with tab_rev:
    if sales_ok:
        _guard(render_pareto, df_sales, dist_sel, year_type)
        st.markdown("---")
        _guard(render_seasonal_pattern, _load_monthly_pms(year_type))
        st.markdown("---")
    _guard(render_revenue_concentration, bundle.get("revenue_concentration", pd.DataFrame()), year_sel, highlight, latest_y)
    st.markdown("---")
    _guard(render_revenue_waterfall, bundle.get("revenue_waterfall", pd.DataFrame()), year_sel, highlight)
    st.markdown("---")
    _guard(
        render_geographic_risk,
        bundle.get("distributor_geo", pd.DataFrame()),
        gps_db,
        year_sel,
        highlight,
        latest_y,
    )

st.caption(
    f"Network Intelligence · Data: `{DERIVED_DIR}` · "
    "Customer Risk ranking lives on Early Warning; its Threat-map/scrape views move to Tools (later phase)."
)
