# PRISM Layer 2B — PMS capture rate divides actual PN sales against expected demand (derived from UIO)

"""
PRISM — Module 3: PMS (Preventive Maintenance Service Coverage)

PMS capture rate: actual parts sold vs expected demand
based on surviving parc x service frequency.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR))

from config import (
    BETA_MODE,
    BVP_PN_DIMENSION_CSV,
    DATA_ROOT,
    DERIVED_DIR,
    PMS_SUMMARY_BY_DB_CSV,
    data_freshness_date,
    resolve_mapping_path,
    resolve_uio_path,
)
from modules.data_prep import (
    build_uio_lookup,
    load_distributor_mapping,
    load_uio_from_excel,
    get_distributor_metadata,
)
from modules.bvp_analytics import resolve_uio_for_distributor
from modules.pms_derived_loader import derived_capture_available, load_pms_capture_derived
from modules.sales_loader import load_prism_sales
from modules.pms_engine import (
    calculate_pms_capture,
    calculate_ituk_incentive,
    get_pms_summary_by_distributor,
    PHASE1_CATEGORIES,
    LCV_DISTRIBUTORS,
    parc_config_for_distributor,
)
from modules.plotly_style import style

# set_page_config is handled by app.py — do not call it in sub-pages

# ── Helpers ───────────────────────────────────────────────────────────────────
ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
PALETTE = [
    "#1B3A6B", "#E87722", "#2C5AA0", "#F4A460", "#4A90D9",
    "#8B4513", "#70B8FF", "#D2691E", "#003087", "#FFA07A",
    "#1E90FF", "#CD853F", "#87CEEB", "#D2691E", "#4169E1",
]


def _fmt_eur(v, decimals=0):
    if pd.isna(v):
        return "—"
    return f"€{v:,.{decimals}f}"


def _traffic_label(v, low=50, mid=150):
    if pd.isna(v):
        return "—"
    if v >= mid:
        return f"🟢 {_fmt_eur(v, 1)}"
    elif v >= low:
        return f"🟡 {_fmt_eur(v, 1)}"
    else:
        return f"🔴 {_fmt_eur(v, 1)}"


# ── Brand CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root {
        --isze-blue: #1B3A6B;
        --isze-orange: #E87722;
        --isze-light: #D6E4F0;
    }
    .main-header {
        background: linear-gradient(90deg, #1B3A6B 0%, #2C5AA0 100%);
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .main-header h1 { color: white !important; margin: 0; font-size: 1.6rem; }
    .main-header p { color: #D6E4F0; margin: 0.2rem 0 0; font-size: 0.85rem; }

    div[data-testid="metric-container"] {
        border: 1px solid #E0E0E0;
        border-left: 4px solid #1B3A6B;
        border-radius: 6px;
        padding: 0.5rem 0.8rem;
    }
    [data-testid="stMetricValue"] { color: #1B3A6B; }

    .footer-note {
        font-size: 0.72rem;
        color: #999;
        padding-top: 1rem;
        border-top: 1px solid #EEE;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Beta banner ───────────────────────────────────────────────────────────────
if st.session_state.get("beta_mode", BETA_MODE):
    st.warning("BETA MODE — not for distribution", icon="⚠️")

# ── Cached loaders ────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading distributor mapping…")
def _load_mapping():
    return load_distributor_mapping(str(resolve_mapping_path()))


@st.cache_data(show_spinner="Loading UIO data…")
def _load_uio():
    return load_uio_from_excel(str(resolve_uio_path()))


@st.cache_data(show_spinner="Loading sales data…")
def _load_sales(_mapping_hash):
    df_map = _load_mapping()
    df, _source = load_prism_sales(df_map)
    return df


@st.cache_data(show_spinner="Loading BVP dimension…")
def _load_bvp_dim():
    if BVP_PN_DIMENSION_CSV.exists():
        return pd.read_csv(BVP_PN_DIMENSION_CSV)
    return pd.DataFrame()


@st.cache_data(show_spinner="Loading derived PMS summary…")
def _load_pms_db_summary():
    """Per-distributor PMS rollup (verified pipeline). Same source as the per-DB briefs."""
    if PMS_SUMMARY_BY_DB_CSV.exists():
        return pd.read_csv(PMS_SUMMARY_BY_DB_CSV)
    return pd.DataFrame()


def _pms_confidence(db: str) -> str:
    """Capture-number confidence: HIGH = own DVLA UIO (ITUK); LOW = BVP-only / genuine-data gap; else MED (v18 model)."""
    if db == "ITUK":
        return "HIGH"
    if db in ("UMI", "UTI"):
        return "LOW"
    return "MED"


# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df_mapping = _load_mapping()
    df_meta = get_distributor_metadata(df_mapping)
    df_sales = _load_sales("v1")
except FileNotFoundError as e:
    st.info(
        f"Data files not found: {e}\n\n"
        "Build canonical sales first:\n"
        "`python scripts/build_sales_fact_from_cy.py`\n"
        f"Target: `{DERIVED_DIR / 'sales_fact.parquet'}`\n\n"
        f"ISZE Data root: `{DATA_ROOT}`",
        icon="📂",
    )
    st.stop()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🔧 PMS — Are We Keeping the Service Business?</h1>
    <p>Of the scheduled-service parts these trucks are due, how many we actually supply — every point we miss is revenue going to the aftermarket.</p>
</div>
""", unsafe_allow_html=True)
st.caption(
    "**Capture rate** = parts sold ÷ parts the fleet is due (surviving parc × service frequency). "
    "100% means we supply every scheduled service; below 100% is genuine-parts revenue leaking to aftermarket."
)

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Filters")

    year_type_label = st.radio(
        "Year type",
        ["Calendar Year (Jan–Dec)", "Fiscal Year (Apr–Mar)"],
        help="ISZE Fiscal Year runs April–March. FY2024 = Apr 2024 – Mar 2025.",
    )
    year_type = "fiscal" if "Fiscal" in year_type_label else "calendar"

    if year_type == "fiscal":
        available_years = sorted(df_sales["fiscal_year"].dropna().unique().astype(int).tolist())
    else:
        available_years = sorted(df_sales["year"].dropna().unique().astype(int).tolist())

    default_year = 2025 if 2025 in available_years else (
        2024 if 2024 in available_years else (available_years[-1] if available_years else 2025)
    )
    selected_year = st.selectbox(
        "Period",
        options=available_years,
        index=available_years.index(default_year) if default_year in available_years else len(available_years) - 1,
        format_func=lambda y: f"FY{y} (Apr {y}–Mar {y+1})" if year_type == "fiscal" else str(y),
    )

    st.divider()

    regions = ["All regions"] + sorted(df_meta["region"].dropna().unique().tolist())
    selected_region = st.selectbox("Region", regions)

    dist_options = sorted(df_sales["distributor_code"].unique().tolist())
    if selected_region != "All regions":
        filtered_dist = df_meta[df_meta["region"] == selected_region]["distributor_code"].tolist()
        dist_options = [d for d in dist_options if d in filtered_dist]

    selected_dists = st.multiselect(
        "Distributors (leave empty = all)",
        options=dist_options,
        default=[],
    )

    st.divider()
    fill_catalog = st.toggle(
        "BVP catalogue PMS (live mode)",
        value=True,
        help="Live recompute: include all BVP-catalog PMS PNs, not registry-only.",
    )

    st.divider()
    derived_ok = derived_capture_available()
    data_mode_options = ["Derived (verified pipeline)"]
    if derived_ok:
        default_mode_idx = 0
    else:
        data_mode_options.append("Live (recompute from sales)")
        default_mode_idx = 0
    if derived_ok:
        data_mode_options.append("Live (recompute from sales)")

    data_mode = st.radio(
        "Data source",
        data_mode_options,
        index=default_mode_idx,
        help=(
            "Derived = pms_capture_by_db_year.csv after verify_derived_pipeline. "
            "Live = recompute from sales + UIO (uses ITUK DVLA override when set)."
        ),
    )
    use_derived = "Derived" in data_mode

    st.divider()
    st.caption("📅 Data: 2022–2026 YTD")
    if use_derived:
        st.caption("📌 UIO: from derived capture (ITUK = 22,389 DVLA)")
    else:
        st.caption("📌 UIO: V17 Excel + ITUK DVLA override (22,389)")
    st.caption("🔧 PMS Phase 1: N75 (NPR75/4HK1 + NPR88/4JZ1)")
    st.caption("📐 Intervals: prism/data/pms_capture_assumptions.yaml")
    st.caption(f"🔄 Built: {data_freshness_date()}")
    st.caption("📖 Metrics: prism/docs/metric_dictionary.md")

# ── Apply filters ─────────────────────────────────────────────────────────────
df_sales_filtered = df_sales.copy()
if selected_dists:
    df_sales_filtered = df_sales_filtered[
        df_sales_filtered["distributor_code"].isin(selected_dists)
    ]
if selected_region != "All regions":
    valid_dists = df_meta[df_meta["region"] == selected_region]["distributor_code"].tolist()
    df_sales_filtered = df_sales_filtered[
        df_sales_filtered["distributor_code"].isin(valid_dists)
    ]

period_label = (
    f"FY{selected_year} (Apr {selected_year}–Mar {selected_year+1})"
    if year_type == "fiscal"
    else str(selected_year)
)

# ── Section 1: Phase 1 scope notice ──────────────────────────────────────────
if selected_dists and all(d in LCV_DISTRIBUTORS for d in selected_dists):
    st.info(
        "**IUK / UMI (LCV):** PMS uses D-Max / pickup PNs (N35 + LCV_DMax registry) — "
        "not N75 truck parts. Denominator = LCV UIO from V13 (e.g. IUK ~48,876 in 2024)."
    )
else:
    st.info(
        "Phase 1 focus: N75 / 7.5t fleet (NPR75/4HK1 and NPR88/4JZ1). "
        "Select **IUK** alone to see LCV D-Max capture."
    )

# ── Compute PMS capture ───────────────────────────────────────────────────────
dist_filter_pms = selected_dists[0] if len(selected_dists) == 1 else None
dist_codes = selected_dists if selected_dists else None

if use_derived and year_type != "calendar":
    st.warning(
        "Derived capture is built on **calendar years**. Switch to Calendar Year or use Live mode for fiscal.",
        icon="ℹ️",
    )
    use_derived = False

try:
    if use_derived:
        if not derived_capture_available():
            st.error("Derived PMS capture file missing. Run run_pipeline_and_verify.ps1.")
            st.stop()
        pms_result = load_pms_capture_derived(
            year=selected_year,
            distributor_codes=dist_codes,
            line_type="total",
        )
        meta = pms_result.get("meta", {})
        if meta.get("uio_units"):
            st.success(
                f"**Derived pipeline** — UIO {meta['uio_units']:,} "
                f"({meta.get('uio_source', 'v13')}, scope {meta.get('scope', '—')})",
                icon="✅",
            )
        else:
            st.info("**Derived pipeline** — network aggregate (select one distributor for UIO detail).")
    else:
        parc_cfg = None
        if dist_filter_pms:
            df_uio = _load_uio()
            uio_lookup, uio_proxy = build_uio_lookup(df_uio)
            uio_units, uio_proxy_used, uio_source = resolve_uio_for_distributor(
                dist_filter_pms, selected_year, uio_lookup, uio_proxy
            )
            parc_cfg = parc_config_for_distributor(
                dist_filter_pms,
                {"uio_units": uio_units} if uio_units else None,
            )
            if uio_units:
                proxy_note = " (2024 proxy)" if uio_proxy_used else ""
                st.caption(
                    f"Live UIO: **{uio_units:,}** — {uio_source}{proxy_note}"
                )
        pms_result = calculate_pms_capture(
            df_sales_filtered,
            year=selected_year,
            year_type=year_type,
            distributor_code=dist_filter_pms,
            parc_config=parc_cfg,
            df_dim=_load_bvp_dim(),
            fill_catalog_pms=fill_catalog,
        )
except Exception as e:
    st.error(f"PMS calculation error: {e}")
    st.stop()

summary_df = pms_result["summary_df"]
has_pms_data = pms_result["total_actual_eur"] > 0

if not has_pms_data:
    # No PMS data state
    st.info(
        "No PMS part numbers found in the sales data for the current selection. "
        "Check that the `part_number` column is populated and that the selected "
        "year has data. PMS capture rates require sales rows tagged against the "
        "ITUK pilot registry plus BVP-catalog PMS parts (filters, wear, urea).",
        icon="🔧",
    )
else:
    # ── Section 2: KPI row ────────────────────────────────────────────────────
    cap_rates = pms_result["capture_rate_by_category"]
    brake_cap = cap_rates.get("brake_pad", None)
    air_cap = cap_rates.get("air_filter", None)
    total_actual = pms_result["total_actual_eur"]
    total_opp = pms_result["total_opportunity_eur"]

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total PMS Sales", f"€{total_actual:,.0f}")
    with kpi2:
        st.metric(
            "Brake Pad Capture",
            f"{brake_cap * 100:.1f}%" if brake_cap is not None else "—",
        )
    with kpi3:
        st.metric(
            "Air Filter Capture",
            f"{air_cap * 100:.1f}%" if air_cap is not None else "—",
        )
    with kpi4:
        st.metric("Revenue Opportunity", f"€{total_opp:,.0f}")

    st.divider()

    # ── Section 3: Capture rate horizontal bar chart ──────────────────────────
    st.markdown("#### Capture Rate by Category")
    st.caption("Green ≥ 60% | Amber 30–60% | Red < 30%")

    try:
        phase1_rows = summary_df[summary_df["category"].isin(PHASE1_CATEGORIES)].copy()
        if not phase1_rows.empty:
            phase1_rows = phase1_rows.sort_values("capture_rate", ascending=True)
            bar_colors = []
            for v in phase1_rows["capture_rate"]:
                if v >= 0.60:
                    bar_colors.append("#2E7D32")
                elif v >= 0.30:
                    bar_colors.append("#F9A825")
                else:
                    bar_colors.append("#C62828")

            annotations = [
                f"{int(a)} / {int(e)}"
                for a, e in zip(
                    phase1_rows["actual_qty"],
                    phase1_rows["expected_qty"],
                )
            ]

            fig_cap = go.Figure(go.Bar(
                x=phase1_rows["capture_rate"] * 100,
                y=phase1_rows["category_label"],
                orientation="h",
                marker_color=bar_colors,
                text=[f"{v*100:.1f}%" for v in phase1_rows["capture_rate"]],
                textposition="outside",
                customdata=list(zip(
                    phase1_rows["actual_qty"],
                    phase1_rows["expected_qty"],
                    annotations,
                )),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Capture rate: %{x:.1f}%<br>"
                    "Actual qty: %{customdata[0]:,.0f}<br>"
                    "Expected qty: %{customdata[1]:,.0f}<extra></extra>"
                ),
            ))
            fig_cap.add_vline(
                x=60,
                line_dash="dash",
                line_color="#2E7D32",
                annotation_text="60% target",
                annotation_position="top right",
            )
            fig_cap.add_vline(
                x=30,
                line_dash="dot",
                line_color="#F9A825",
                annotation_text="30%",
            )
            fig_cap.update_layout(
                height=max(280, len(phase1_rows) * 55),
                margin=dict(l=10, r=80, t=20, b=20),
                xaxis_title="Capture Rate (%)",
                xaxis=dict(range=[0, 115], gridcolor="#F0F0F0"),
                yaxis_title="",
                plot_bgcolor="white",
                paper_bgcolor="white",
            )
            st.plotly_chart(style(fig_cap), width='stretch')
        else:
            st.info("No Phase 1 category data available for the capture rate chart.")
    except Exception as e:
        st.warning(f"Capture rate chart unavailable: {e}")

    st.divider()

    # ── Section 4: Revenue Opportunity Table ─────────────────────────────────
    st.markdown("#### Revenue Opportunity Table")
    try:
        opp_display = summary_df[[
            "category_label", "actual_qty", "expected_qty",
            "capture_rate", "avg_sp_eur", "revenue_gap_eur",
        ]].copy()
        opp_display["capture_rate_pct"] = opp_display["capture_rate"].apply(
            lambda x: f"{x*100:.1f}%"
        )
        opp_display["avg_sp_eur_fmt"] = opp_display["avg_sp_eur"].apply(
            lambda x: _fmt_eur(x, 2) if x > 0 else "—"
        )
        opp_display["revenue_gap_eur_fmt"] = opp_display["revenue_gap_eur"].apply(
            lambda x: _fmt_eur(x, 0) if x > 0 else "—"
        )
        opp_display["actual_qty_fmt"] = opp_display["actual_qty"].apply(
            lambda x: f"{int(x):,}"
        )
        opp_display["expected_qty_fmt"] = opp_display["expected_qty"].apply(
            lambda x: f"{int(x):,}" if x > 0 else "—"
        )
        st.dataframe(
            opp_display.rename(columns={
                "category_label":      "Category",
                "actual_qty_fmt":      "Actual Qty",
                "expected_qty_fmt":    "Expected Qty",
                "capture_rate_pct":    "Capture Rate",
                "avg_sp_eur_fmt":      "Avg SP (€)",
                "revenue_gap_eur_fmt": "Revenue Gap (€)",
            })[["Category", "Actual Qty", "Expected Qty", "Capture Rate", "Avg SP (€)", "Revenue Gap (€)"]],
            width='stretch',
            hide_index=True,
        )
        st.caption(
            "Expected Qty = surviving parc × services/year × addressable %. "
            "Revenue Gap = (Expected − Actual) × Avg SP. Capture capped at 100%."
        )
    except Exception as e:
        st.warning(f"Opportunity table unavailable: {e}")

    st.divider()

    # ── Section 5: Distributor Breakdown ─────────────────────────────────────
    st.markdown("#### Distributor Breakdown")
    try:
        dist_summary = get_pms_summary_by_distributor(
            df_sales_filtered, year=selected_year, year_type=year_type
        )

        if dist_summary.empty:
            st.info("No distributor-level PMS data available.")
        elif not selected_dists:
            # All distributors: stacked bar by category
            pivot_dist = (
                dist_summary.groupby(["distributor_code", "category_label"])
                .agg(revenue_eur=("revenue_eur", "sum"))
                .reset_index()
            )
            fig_dist = px.bar(
                pivot_dist,
                x="distributor_code",
                y="revenue_eur",
                color="category_label",
                labels={
                    "distributor_code": "Distributor",
                    "revenue_eur": "PMS Sales (EUR)",
                    "category_label": "Category",
                },
                color_discrete_sequence=PALETTE,
            )
            fig_dist.update_layout(
                height=420,
                margin=dict(l=10, r=10, t=20, b=10),
                plot_bgcolor="white",
                paper_bgcolor="white",
                yaxis=dict(gridcolor="#F0F0F0", tickprefix="€", tickformat=",.0f"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.35),
            )
            st.plotly_chart(style(fig_dist), width='stretch')
        else:
            # Single or filtered distributor: show detail table
            dist_show = dist_summary[[
                "distributor_code", "category_label", "model",
                "qty", "revenue_eur", "avg_sp_eur",
            ]].copy()
            dist_show["revenue_eur_fmt"] = dist_show["revenue_eur"].apply(
                lambda x: _fmt_eur(x, 0)
            )
            dist_show["avg_sp_eur_fmt"] = dist_show["avg_sp_eur"].apply(
                lambda x: _fmt_eur(x, 2) if x > 0 else "—"
            )
            dist_show["qty_fmt"] = dist_show["qty"].apply(lambda x: f"{int(x):,}")
            st.dataframe(
                dist_show.rename(columns={
                    "distributor_code": "Distributor",
                    "category_label":   "Category",
                    "model":            "Model",
                    "qty_fmt":          "Qty",
                    "revenue_eur_fmt":  "Revenue (€)",
                    "avg_sp_eur_fmt":   "Avg SP (€)",
                })[["Distributor", "Category", "Model", "Qty", "Revenue (€)", "Avg SP (€)"]],
                width='stretch',
                hide_index=True,
            )
    except Exception as e:
        st.warning(f"Distributor breakdown unavailable: {e}")

st.divider()

# ── Section 5b: Network capture league (derived authority, all distributors) ──
st.markdown("#### Network Capture League — € Gap by Distributor")
st.caption(
    "Per-distributor PMS capture from the **verified pipeline** (`pms_summary_by_db.csv`), "
    "ranked by € gap to 100% capture. Network view — independent of the sidebar filters; "
    "reconciles to the per-DB briefs and FACTS.md §1 (ITUK)."
)
try:
    league = _load_pms_db_summary()
    if league.empty:
        st.info(
            "Derived per-distributor summary not found (`pms_summary_by_db.csv`). "
            "Run `run_pipeline_and_verify.ps1`."
        )
    else:
        from modules.year_coverage import latest_complete_year

        ly = latest_complete_year([int(y) for y in league["year"].dropna().unique()])
        league = league[league["year"] == ly].copy()
        league["conf"] = league["distributor_code"].apply(_pms_confidence)
        conf_color = {"HIGH": "#1B3A6B", "MED": "#8FA9C9", "LOW": "#C62828"}
        # Quotable-KPI firewall (DECISIONS.md 2026-07-21 Fix 2): rank on the gap sum
        # that EXCLUDES zero-actual-sales categories (their €0 gap is a hidden gap,
        # not a small one). Fall back to the plain sum until the summary is rebuilt.
        gap_col = (
            "revenue_gap_eur_sum_quotable"
            if "revenue_gap_eur_sum_quotable" in league.columns
            else "revenue_gap_eur_sum"
        )
        nonq_col = "n_nonquotable_categories" if "n_nonquotable_categories" in league.columns else None
        net_gap = float(league[gap_col].sum())
        top3_gap = float(league.nlargest(3, gap_col)[gap_col].sum())

        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric(f"Network € gap (CY{ly})", f"€{net_gap:,.0f}")
        with k2:
            st.metric("Distributors", f"{len(league)}")
        with k3:
            st.metric("Top 3 share", f"{top3_gap / net_gap * 100:.0f}%" if net_gap else "—")

        league_chart = league.sort_values(gap_col, ascending=True)
        fig_league = go.Figure(go.Bar(
            x=league_chart[gap_col],
            y=league_chart["distributor_code"],
            orientation="h",
            marker_color=[conf_color[c] for c in league_chart["conf"]],
            text=[f"{r * 100:.0f}% cap" for r in league_chart["capture_rate_total_wtd"]],
            textposition="outside",
            customdata=list(zip(
                league_chart["capture_rate_total_wtd"] * 100,
                league_chart["capture_rate_genuine_wtd"] * 100,
                league_chart["uio_units"],
                league_chart["conf"],
                league_chart[nonq_col] if nonq_col else [0] * len(league_chart),
            )),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "€ gap to 100%: €%{x:,.0f}<br>"
                "Total capture: %{customdata[0]:.1f}%<br>"
                "Genuine capture: %{customdata[1]:.1f}%<br>"
                "UIO: %{customdata[2]:,.0f}<br>"
                "Confidence: %{customdata[3]}<br>"
                "Non-quotable categories: %{customdata[4]}<extra></extra>"
            ),
        ))
        fig_league.update_layout(
            height=max(360, len(league_chart) * 26),
            margin=dict(l=10, r=90, t=10, b=20),
            xaxis_title=f"€ gap to 100% capture (CY{ly})",
            xaxis=dict(gridcolor="#F0F0F0", tickprefix="€", tickformat=",.0f"),
            yaxis_title="",
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(style(fig_league), width='stretch')
        st.caption(
            "Bar colour = capture-number confidence — **Blue** HIGH (own DVLA UIO, ITUK) · "
            "**Grey** MED (central v18 parc model) · **Red** LOW (BVP-only / genuine-data gap — UMI, UTI; € gap directional only)."
        )

        league_tbl = league.sort_values(gap_col, ascending=False).copy()
        league_tbl["UIO"] = league_tbl["uio_units"].apply(lambda x: f"{int(x):,}")
        league_tbl["Total cap"] = league_tbl["capture_rate_total_wtd"].apply(lambda x: f"{x * 100:.1f}%")
        league_tbl["Genuine cap"] = league_tbl["capture_rate_genuine_wtd"].apply(lambda x: f"{x * 100:.1f}%")
        league_tbl["Oil cap"] = league_tbl["oil_filter_capture"].apply(lambda x: f"{x * 100:.0f}%")
        league_tbl["€ gap"] = league_tbl[gap_col].apply(lambda x: _fmt_eur(x, 0))
        if nonq_col:
            league_tbl["Non-quotable"] = league_tbl[nonq_col].astype(int)
        st.dataframe(
            league_tbl.rename(columns={
                "distributor_code": "Distributor",
                "conf": "Conf",
            })[["Distributor", "UIO", "Total cap", "Genuine cap", "Oil cap", "€ gap"]
               + (["Non-quotable"] if nonq_col else []) + ["Conf"]],
            width='stretch',
            hide_index=True,
        )
        st.caption(
            "€ gap is a gross-SP **ceiling** to 100% capture — before any realistic pilot target "
            "(+1% filters / +3% wear) and **before netting BVP in-tent retention (BVP is not leakage)**, "
            "so the winnable slice is materially smaller. Air-filter demand uses a provisional 0.5× interval "
            "factor (~every 2nd service — flag C, pending IML confirmation); brake-shoe ~0% capture network-wide is fitment/availability, not a winnable gap. "
            "**Non-quotable** = categories with zero actual sales whose € gap is excluded from the ranking (DECISIONS.md 2026-07-21)."
        )
except Exception as e:
    st.warning(f"Network capture league unavailable: {e}")

st.divider()

# ── Section 6: ITUK Incentive Structure ──────────────────────────────────────
show_ituk_panel = (
    not selected_dists
    or "ITUK" in selected_dists
    or any("ITUK" in d.upper() for d in selected_dists)
)
if show_ituk_panel:
    st.markdown("#### ITUK Incentive Structure")
    col_tier, col_stretch = st.columns([1, 1])

    with col_tier:
        st.markdown("**Dealer Credit Tiers (PMS volume performance)**")
        tier_data = pd.DataFrame([
            {"Target Threshold": "100% of target (baseline)",    "Dealer Credit": "£250"},
            {"Target Threshold": "125% of target (+25% uplift)", "Dealer Credit": "£500"},
            {"Target Threshold": "150% of target (+50% uplift)", "Dealer Credit": "£750"},
            {"Target Threshold": "Best N75 brake conversion",    "Dealer Credit": "+£500 bonus"},
            {"Target Threshold": "Best air filter attachment",   "Dealer Credit": "+£500 bonus"},
        ])
        st.dataframe(tier_data, width='stretch', hide_index=True)

    with col_stretch:
        st.markdown("**2030 Stretch Tracker — ITUK / UK Market**")
        stretch_data = pd.DataFrame([
            {"Metric": "2025 baseline",          "Value": "£12.87M",  "Notes": "Actual FY2025"},
            {"Metric": "2026 plan (77% UIO)",    "Value": "£13.13M",  "Notes": "77% UIO share target"},
            {"Metric": "2026 stretch (80% UIO)", "Value": "£13.64M",  "Notes": "Stretch target"},
            {"Metric": "ISZE kickback pot",       "Value": "£62,052",  "Notes": "Available for dealers"},
        ])
        st.dataframe(stretch_data, width='stretch', hide_index=True)

    if has_pms_data:
        with st.expander("Show incremental performance vs baseline"):
            try:
                df_incentive = calculate_ituk_incentive(
                    df_sales, year=selected_year, year_type=year_type
                )
                if not df_incentive.empty:
                    df_inc_display = df_incentive.copy()
                    df_inc_display["pct_of_target_fmt"] = df_inc_display["pct_of_target"].apply(
                        lambda x: f"{x*100:.1f}%"
                    )
                    df_inc_display["bonus_tier_fmt"] = df_inc_display["bonus_tier"].fillna("Below target")
                    df_inc_display["baseline_qty_fmt"] = df_inc_display["baseline_qty"].apply(
                        lambda x: f"{x:,.1f}"
                    )
                    df_inc_display["actual_qty_fmt"] = df_inc_display["actual_qty"].apply(
                        lambda x: f"{x:,.1f}"
                    )
                    df_inc_display["incremental_qty_fmt"] = df_inc_display["incremental_qty"].apply(
                        lambda x: f"{x:+,.1f}"
                    )
                    st.dataframe(
                        df_inc_display.rename(columns={
                            "category_label":       "Category",
                            "baseline_qty_fmt":     "Baseline Qty",
                            "actual_qty_fmt":       "Actual Qty",
                            "incremental_qty_fmt":  "Incremental",
                            "pct_of_target_fmt":    "% of Target",
                            "bonus_tier_fmt":       "Bonus Tier",
                            "bonus_amount_gbp":     "Bonus (£)",
                        })[["Category", "Baseline Qty", "Actual Qty",
                            "Incremental", "% of Target", "Bonus Tier", "Bonus (£)"]],
                        width='stretch',
                        hide_index=True,
                    )
                else:
                    st.info("No ITUK incentive data available for this period.")
            except Exception as e:
                st.warning(f"Incentive calc unavailable: {e}")

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer-note">'
    "PRISM PMS Coverage | Layer 2B | Phase 1: N75 | "
    "Metrics: prism/docs/metric_dictionary.md | PN Authority: ITUK Apr 2026 | "
    "Marketing calendar moved to Tools."
    "</div>",
    unsafe_allow_html=True,
)
