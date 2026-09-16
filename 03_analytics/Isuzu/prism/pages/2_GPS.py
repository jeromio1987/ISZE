# PRISM Layer 2A — GPS (Spend per Unit) divides net sales against UIO

"""
PRISM — Module 2: GPS (Genuine Parts Share / Spend per Unit)

Net Sales EUR divided by Units in Operation, by distributor and year.
Migrated from gps_dashboard/app.py — tabs 1-4 and Export tab.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import zipfile
import io as _io
from datetime import datetime

# ── Path setup (prism root only — do not prepend legacy gps_dashboard/) ───────
APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import (
    BETA_MODE,
    DATA_ROOT,
    DERIVED_DIR,
    GPS_MODEL_TARGETS_CSV,
    data_freshness_date,
    data_status,
    resolve_mapping_path,
    resolve_uio_path,
)
from modules.data_prep import (
    load_distributor_mapping, load_uio_from_excel, load_uio_detail_from_excel,
    get_distributor_metadata, UIO_PROXY_YEAR,
)
from modules.sales_loader import load_prism_sales
from modules.gps_model_targets import load_gps_model_targets
from modules.gps_engine import (
    calculate_spend_per_unit, calculate_multiyear_trends,
    calculate_model_weighted_gps, calculate_model_weighted_multiyear_trends,
    get_top_parts, get_summary_kpis, calculate_monthly_sales,
    GPS_TARGET_EUR_PER_UNIT, GPS_AMBER_EUR_PER_UNIT,
)
from modules.export_engine import export_gps_dashboard_excel
from modules.pms_engine import PMS_PN_REGISTRY, CATEGORY_LABELS
from modules.fig_key_catalog import enrich_top_parts_table, load_catalog_index
from modules.plotly_style import style

# set_page_config is handled by app.py — do not call it in sub-pages

# Beta banner
if st.session_state.get("beta_mode", BETA_MODE):
    st.warning("BETA MODE — not for distribution", icon="⚠️")

# ── Brand CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Brand colours */
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

    .kpi-card {
        background: white;
        border: 1px solid #E0E0E0;
        border-left: 4px solid #1B3A6B;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    }
    .kpi-label { font-size: 0.75rem; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-value { font-size: 1.6rem; font-weight: 700; color: #1B3A6B; }
    .kpi-sub { font-size: 0.75rem; color: #888; }

    .proxy-warning {
        background: #FFF3CD;
        border: 1px solid #FFD700;
        border-radius: 4px;
        padding: 0.4rem 0.8rem;
        font-size: 0.8rem;
        color: #856404;
    }

    /* Traffic lights in tables */
    .tl-green { background-color: #C8E6C9; color: #1B5E20; border-radius: 4px; padding: 2px 6px; }
    .tl-amber { background-color: #FFE5B4; color: #7B3F00; border-radius: 4px; padding: 2px 6px; }
    .tl-red { background-color: #FFCCCC; color: #7F0000; border-radius: 4px; padding: 2px 6px; }

    div[data-testid="metric-container"] {
        border: 1px solid #E0E0E0;
        border-left: 4px solid #1B3A6B;
        border-radius: 6px;
        padding: 0.5rem 0.8rem;
    }
    [data-testid="stMetricValue"] { color: #1B3A6B; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 0.4rem 1rem;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .footer-note {
        font-size: 0.72rem;
        color: #999;
        padding-top: 1rem;
        border-top: 1px solid #EEE;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
PALETTE = [
    "#1B3A6B", "#E87722", "#2C5AA0", "#F4A460", "#4A90D9",
    "#8B4513", "#70B8FF", "#D2691E", "#003087", "#FFA07A",
    "#1E90FF", "#CD853F", "#87CEEB", "#D2691E", "#4169E1"
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

def _traffic_color(v, low=50, mid=150):
    if pd.isna(v):
        return None
    if v >= mid:
        return "background-color: #C8E6C9"
    elif v >= low:
        return "background-color: #FFE5B4"
    else:
        return "background-color: #FFCCCC"

def _style_spu(val):
    return _traffic_color(val) or ""


def _gps_pct_bar_color(pct: float) -> str:
    """Traffic light for GPS % of model wallet (study row-38 style)."""
    if pd.isna(pct):
        return "#CCCCCC"
    if pct >= 70:
        return "#2E7D32"
    if pct >= 40:
        return "#F9A825"
    return "#C62828"


def _style_gps_pct(val):
    if pd.isna(val):
        return ""
    if val >= 70:
        return "background-color: #C8E6C9; color: #1B5E20"
    if val >= 40:
        return "background-color: #FFE5B4; color: #7B3F00"
    return "background-color: #FFCCCC; color: #7F0000"


# ── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading distributor mapping…")
def _load_mapping():
    return load_distributor_mapping(str(resolve_mapping_path()))

@st.cache_data(show_spinner="Loading UIO data…")
def _load_uio():
    return load_uio_from_excel(str(resolve_uio_path()))

@st.cache_data(show_spinner="Loading UIO by model…")
def _load_uio_detail():
    return load_uio_detail_from_excel(str(resolve_uio_path()))

@st.cache_data(show_spinner="Computing model-weighted GPS trends…")
def _load_model_gps_trends(year_type):
    df_map = _load_mapping()
    df_uio_detail = _load_uio_detail()
    df_meta = get_distributor_metadata(df_map)
    df_sales = _load_sales("v1")
    return calculate_model_weighted_multiyear_trends(
        df_sales, df_uio_detail, df_meta, year_type=year_type
    )


@st.cache_data(show_spinner="Computing GPS scoreboard…")
def _load_gps_scoreboard(year_type, year):
    df_map = _load_mapping()
    df_uio_detail = _load_uio_detail()
    df_meta = get_distributor_metadata(df_map)
    df_sales = _load_sales("v1")
    df_score, _ = calculate_model_weighted_gps(
        df_sales, df_uio_detail, df_meta, year=int(year), year_type=year_type
    )
    return df_score

@st.cache_data(show_spinner="Loading sales data…")
def _load_sales(mapping_hash):
    df_map = _load_mapping()
    df, _source = load_prism_sales(df_map)
    return df

@st.cache_data(show_spinner="Computing year-on-year trends…")
def _load_trends(year_type):
    df_map = _load_mapping()
    df_uio = _load_uio()
    df_meta = get_distributor_metadata(df_map)
    df_sales = _load_sales("v1")
    df_trend = calculate_multiyear_trends(df_sales, df_uio, df_meta, year_type=year_type)
    return df_trend


# ── Check data files exist before loading ─────────────────────────────────────
_status = data_status()
_sales_ok = _status["sales_parquet"] or _status["sales_csv_derived"] or _status["sales_legacy"]

if not (_status["mapping"] and _status["uio"] and _sales_ok):
    st.info(
        "GPS data files not found.\n\n"
        "**Canonical sales:** run from `prism/`:\n"
        "`python scripts/build_sales_fact_from_cy.py`\n"
        f"→ `{DERIVED_DIR / 'sales_fact.parquet'}`\n\n"
        "**Also need:** distributor mapping + UIO workbook.\n"
        f"**ISZE Data root:** `{DATA_ROOT}`"
    )
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df_mapping = _load_mapping()
    df_uio = _load_uio()
    df_meta = get_distributor_metadata(df_mapping)
    df_sales = _load_sales("v1")
except Exception as e:
    st.error(
        f"Failed to load data: {e}\n\n"
        "Check that the following files are in the data/ folder:\n"
        "- `distributor_master_mapping.csv`\n"
        "- `UIO_v17.xlsx`\n"
        "- `sales_detailed_for_claude_full_fixed.tsv`"
    )
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🚛 ISZE GPS Dashboard — Spend per Unit (€/truck)</h1>
    <p>Isuzu Motors Europe | Vehicle Parts Sales | Confidential</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Filters")

    year_type_label = st.radio(
        "Year type",
        ["Calendar Year (Jan–Dec)", "Fiscal Year (Apr–Mar)"],
        help="ISZE Fiscal Year runs April–March. FY2024 = Apr 2024 – Mar 2025.",
    )
    year_type = "fiscal" if "Fiscal" in year_type_label else "calendar"

    # Available years
    if year_type == "fiscal":
        available_years = sorted(df_sales['fiscal_year'].dropna().unique().astype(int).tolist())
    else:
        available_years = sorted(df_sales['year'].dropna().unique().astype(int).tolist())

    default_year = 2025 if 2025 in available_years else (
        2024 if 2024 in available_years else available_years[-1]
    )
    selected_year = st.selectbox(
        "Period",
        options=available_years,
        index=available_years.index(default_year),
        format_func=lambda y: f"FY{y} (Apr {y}–Mar {y+1})" if year_type == "fiscal" else str(y),
    )

    st.divider()

    # Distributor filter
    dist_options = sorted(df_sales['distributor_code'].unique().tolist())
    selected_dists = st.multiselect(
        "Distributors (leave empty = all)",
        options=dist_options,
        default=[],
    )

    st.divider()
    st.caption("📅 Data: 2022–2026 YTD")
    st.caption("📌 UIO: V17 Excel (2020–2024 actual; 2025/2026 = 2024 proxy)")
    st.caption("🔢 ITUK/IUK and UTI/UMI split by CV/LCV segment")
    st.caption(f"🔄 Built: {data_freshness_date()}")

# ── Apply filters ─────────────────────────────────────────────────────────────
df_sales_filtered = df_sales.copy()
if selected_dists:
    df_sales_filtered = df_sales_filtered[
        df_sales_filtered['distributor_code'].isin(selected_dists)
    ]
# ── Calculate metrics ─────────────────────────────────────────────────────────
df_spu = calculate_spend_per_unit(
    df_sales_filtered, df_uio, df_meta,
    year=selected_year, year_type=year_type,
)

period_label = (
    f"FY{selected_year} (Apr {selected_year}–Mar {selected_year+1})"
    if year_type == "fiscal"
    else str(selected_year)
)

uio_is_proxy = selected_year not in [2020, 2021, 2022, 2023, 2024]
n_proxy = int(df_spu.get('uio_proxy', pd.Series(False)).sum()) if 'uio_proxy' in df_spu.columns else 0

# ── UIO proxy warning (only for 2025/2026) ───────────────────────────────────
if uio_is_proxy:
    st.markdown(
        f'<div class="proxy-warning">⚠️ <strong>UIO proxy active for {period_label}</strong> — '
        f'No actual UIO data for this year. Using 2024 UIO as denominator. '
        f'Results show sales volume change vs fixed fleet.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

# ── Incomplete fiscal-year warning ────────────────────────────────────────────
if year_type == "fiscal" and "billing_date" in df_sales.columns:
    last_billing = pd.to_datetime(df_sales["billing_date"], errors="coerce").max()
    fy_end = pd.Timestamp(year=selected_year + 1, month=3, day=31)
    if pd.notna(last_billing) and last_billing < fy_end:
        months_present = (
            (last_billing.year - selected_year) * 12 + (last_billing.month - 4) + 1
        )
        months_present = max(0, min(12, months_present))
        st.warning(
            f"⚠️ **Incomplete fiscal year — {period_label} is only {months_present} of 12 months.** "
            f"Sales data ends {last_billing:%d %b %Y}; a full FY{selected_year} needs data through "
            f"31 Mar {selected_year + 1}. Every figure on this page is a **partial-year total** — "
            "do not read it as a full-year number.",
            icon="⚠️",
        )

# ── Known data quality flags ──────────────────────────────────────────────────
with st.expander("ℹ️ Known data quality flags", expanded=False):
    st.markdown("""
**Poland (POLAND):** UIO = 27 units (declining, D-Max only market per IBX data).
Sales = €2M+/year → spend/unit is not a meaningful metric. Exclude from benchmarking.

**ITUK vs IUK:** Now correctly split. ITUK = CV trucks (LD + F-Series UIO: 22,389 in 2024).
IUK = LCV D-Max (UIO: 48,876 in 2024). Previously both incorrectly used 71,265 combined.

**UTI vs UMI (Israel):** Now correctly split. UTI = CV trucks (Universal Trucks Israel, LD+MD: 10,668 in 2024).
UMI = LCV D-Max (Universal Motors Israel: 18,349 in 2024). Previously both used combined 29,017.

**MIDI (Italy):** Excluded. No ISZE direct sales data available; Italy UIO (92k) not attributable to ISZE.

**UIO source:** V17 Excel (ISUZU_UIO_Overview_2026_v17.xlsx). Actuals 2020–2024.
2025/2026 use 2024 as proxy (flagged where applied).
    """)
st.markdown("")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 GPS Overview",
    "📈 Trends",
    "🔍 Part Explorer",
    "📥 Export",
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1: GPS Overview
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader(f"Spend per Unit | {period_label}")

    # KPI tiles
    df_with_uio = df_spu[df_spu['uio_units'] > 0]
    total_sales = df_spu['total_sales_eur'].sum()
    n_dist = df_spu['distributor_code'].nunique()
    avg_spu = df_with_uio['spend_per_unit_eur'].mean() if not df_with_uio.empty else 0
    max_spu = df_with_uio['spend_per_unit_eur'].max() if not df_with_uio.empty else 0
    top_dist = (
        df_with_uio.loc[df_with_uio['spend_per_unit_eur'].idxmax(), 'distributor_code']
        if not df_with_uio.empty else "—"
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Sales", f"€{total_sales/1e6:.2f}M")
    with col2:
        st.metric("Active Distributors", str(n_dist))
    with col3:
        st.metric("Avg Spend/Unit *", f"€{avg_spu:,.1f}")
    with col4:
        st.metric("Top Performer", top_dist, delta=f"€{max_spu:,.1f}/unit")
    with col5:
        n_no_uio = df_spu[df_spu['uio_units'] == 0]['distributor_code'].nunique()
        st.metric("Without UIO data", str(n_no_uio), delta="excluded from avg", delta_color="off")

    st.caption("* Average across distributors with UIO data only")
    st.divider()

    # Main chart: Spend per Unit bar chart
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### Spend per Unit by Distributor (€/vehicle)")
        st.caption(
            "**Formula: SPU = Net genuine parts sales (€) ÷ Units in Operation** "
            "| Reads: how much genuine parts revenue is generated per truck in the fleet per year. "
            "🟢 ≥ €150 (on-target) · 🟡 €50–149 (below potential) · 🔴 < €50 (critical underperformance). "
            "€150 benchmark = ISZE minimum viable penetration for a mixed N75/N35/LCV fleet."
        )
        df_chart = df_spu[df_spu['uio_units'] > 0].sort_values(
            'spend_per_unit_eur', ascending=True
        )
        if not df_chart.empty:
            colors = []
            for v in df_chart['spend_per_unit_eur']:
                if v >= 150:
                    colors.append('#2E7D32')
                elif v >= 50:
                    colors.append('#F9A825')
                else:
                    colors.append('#C62828')

            fig = go.Figure(go.Bar(
                x=df_chart['spend_per_unit_eur'],
                y=df_chart['distributor_code'],
                orientation='h',
                marker_color=colors,
                text=[f"€{v:,.1f}" for v in df_chart['spend_per_unit_eur']],
                textposition='outside',
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Spend/Unit: €%{x:,.1f}<br>"
                    "<extra></extra>"
                ),
            ))
            fig.add_vline(x=150, line_dash="dash", line_color="#1B3A6B",
                          annotation_text="€150 threshold", annotation_position="top right")
            fig.add_vline(x=50, line_dash="dot", line_color="#888",
                          annotation_text="€50 threshold")
            fig.update_layout(
                height=max(350, len(df_chart) * 28),
                margin=dict(l=10, r=80, t=20, b=20),
                xaxis_title="EUR per vehicle in UIO",
                yaxis_title="",
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(gridcolor='#F0F0F0'),
            )
            st.plotly_chart(style(fig), width='stretch')
        else:
            st.info("No distributors with UIO data in current selection.")

    with col_right:
        st.markdown("#### Total Sales by Distributor")
        st.caption(
            "⚠️ Raw revenue — not normalized by fleet size. "
            "Large markets always appear higher regardless of performance. "
            "Use SPU (left) to compare actual efficiency."
        )
        df_sales_chart = df_spu.nlargest(20, 'total_sales_eur').sort_values(
            'total_sales_eur', ascending=True
        )
        fig2 = go.Figure(go.Bar(
            x=df_sales_chart['total_sales_eur'],
            y=df_sales_chart['distributor_code'],
            orientation='h',
            marker_color=ISZE_BLUE,
            text=[f"€{v/1e3:,.0f}K" for v in df_sales_chart['total_sales_eur']],
            textposition='outside',
        ))
        fig2.update_layout(
            height=max(350, len(df_sales_chart) * 28),
            margin=dict(l=10, r=80, t=20, b=20),
            xaxis_title="EUR",
            yaxis_title="",
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(gridcolor='#F0F0F0'),
        )
        st.plotly_chart(style(fig2), width='stretch')

    st.divider()
    st.markdown("#### Detail Table")

    df_display = df_spu[[
        'distributor_code', 'country',
        'total_sales_eur', 'total_qty', 'uio_units', 'uio_year',
        'spend_per_unit_eur', 'uio_proxy',
    ]].copy()
    df_display = df_display.sort_values('spend_per_unit_eur', ascending=False, na_position='last')
    df_display['Spend/Unit'] = df_display['spend_per_unit_eur'].apply(_traffic_label)
    df_display['Sales EUR'] = df_display['total_sales_eur'].apply(lambda x: _fmt_eur(x, 0))
    df_display['Qty'] = df_display['total_qty'].apply(
        lambda x: f"{int(x):,}" if pd.notna(x) else "—"
    )
    df_display['UIO'] = df_display.apply(
        lambda r: f"{int(r['uio_units']):,} ({int(r['uio_year'])})" if r['uio_units'] > 0 else "No data",
        axis=1,
    )
    df_display['UIO Source'] = df_display['uio_proxy'].apply(
        lambda x: "⚠️ 2024 proxy" if x else "✅ actual"
    )

    df_show = df_display.rename(columns={
        'distributor_code': 'Distributor',
    })[['Distributor', 'country', 'Sales EUR', 'Qty', 'UIO', 'Spend/Unit', 'UIO Source']]

    st.dataframe(df_show, width='stretch', hide_index=True)

    # No-UIO distributors note
    no_uio = df_spu[df_spu['uio_units'] == 0][['distributor_code', 'country', 'total_sales_eur']]
    if not no_uio.empty:
        with st.expander(f"ℹ️ {len(no_uio)} distributors excluded from spend/unit (no UIO data)"):
            no_uio_show = no_uio.rename(columns={
                'distributor_code': 'Distributor',
                'total_sales_eur': 'Sales EUR',
            })
            no_uio_show['Sales EUR'] = no_uio_show['Sales EUR'].apply(lambda x: _fmt_eur(x, 0))
            st.dataframe(no_uio_show, width='stretch', hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2: Trends
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Year-on-Year Trends")

    with st.spinner("Computing trends across all years…"):
        df_trend = _load_trends(year_type)
        df_model_trend = _load_model_gps_trends(year_type)

    if df_trend.empty and df_model_trend.empty:
        st.info("No trend data available.")
    else:
        df_trend_uio = df_trend[df_trend["uio_units"] > 0].sort_values(
            ["distributor_code", "year_value"]
        ) if not df_trend.empty else df_trend
        df_mt = df_model_trend[df_model_trend["uio_units"] > 0].sort_values(
            ["distributor_code", "year_value"]
        ) if not df_model_trend.empty else df_model_trend
        all_dists = sorted(
            df_mt["distributor_code"].unique().tolist()
            if not df_mt.empty
            else (df_trend_uio["distributor_code"].unique().tolist() if not df_trend_uio.empty else [])
        )

        def _year_label(y: int) -> str:
            if year_type == "fiscal":
                return f"FY{y}"
            return str(y)

        # ── Wallet capture % scoreboard — all distributors (ITUK study row 38) ──
        st.markdown(f"#### Wallet capture % scoreboard | {period_label}")
        st.caption(
            "**Formula: wallet capture % = Actual sales ÷ Target wallet × 100** "
            "| Target wallet = Σ(UIO per model × max genuine parts €/vehicle/year) "
            "| Rates: N75/N50/N62 **€1,120** · F-Series/MD **€1,344** · LCV/D-Max **€250** "
            "| Reads: what share of the theoretical maximum genuine parts wallet is being captured. "
            "🟢 ≥ 70% · 🟡 40–70% · 🔴 < 40% "
            "| 100% line = full capture of the maximum per-model target (not the same as ITUK study row 38, which uses 66% × 1.12 stretch)."
        )

        df_score = _load_gps_scoreboard(year_type, selected_year)
        df_score = df_score[df_score["uio_units"] > 0].copy()
        df_score = df_score[df_score["gps_pct"].notna()].sort_values("gps_pct", ascending=False)

        if df_score.empty:
            st.info("No GPS scoreboard data for this period (check UIO + sales).")
        else:
            n_db = len(df_score)
            med_gps = df_score["gps_pct"].median()
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Distributors ranked", str(n_db))
            with c2:
                st.metric("Median wallet capture %", f"{med_gps:.0f}%")
            with c3:
                top = df_score.iloc[0]
                st.metric("Highest wallet capture %", top["distributor_code"], f"{top['gps_pct']:.0f}%")

            chart_h = max(320, min(720, 26 * len(df_score)))
            fig_board = go.Figure(
                go.Bar(
                    x=df_score["gps_pct"],
                    y=df_score["distributor_code"],
                    orientation="h",
                    marker_color=[_gps_pct_bar_color(v) for v in df_score["gps_pct"]],
                    text=[f"{v:.0f}%" for v in df_score["gps_pct"]],
                    textposition="outside",
                    customdata=np.stack(
                        [
                            df_score["total_sales_eur"],
                            df_score["target_wallet_eur"],
                            df_score["spend_per_unit_eur"],
                            df_score["uio_units"],
                        ],
                        axis=-1,
                    ),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Wallet capture: %{x:.0f}%<br>"
                        "Sales: €%{customdata[0]:,.0f}<br>"
                        "Target wallet: €%{customdata[1]:,.0f}<br>"
                        "Spend/unit: €%{customdata[2]:,.1f}<br>"
                        "UIO: %{customdata[3]:,.0f}<extra></extra>"
                    ),
                )
            )
            fig_board.add_vline(
                x=100,
                line_dash="dash",
                line_color="#1B3A6B",
                annotation_text="100%",
                annotation_position="top",
            )
            fig_board.update_layout(
                height=chart_h,
                margin=dict(l=10, r=60, t=20, b=20),
                plot_bgcolor="white",
                paper_bgcolor="white",
                xaxis=dict(title="Wallet capture % of target wallet", ticksuffix="%", gridcolor="#F0F0F0"),
                yaxis=dict(title="", autorange="reversed"),
            )
            st.plotly_chart(style(fig_board), width='stretch')

            tbl = df_score[
                [
                    "distributor_code",
                    "gps_pct",
                    "total_sales_eur",
                    "target_wallet_eur",
                    "spend_per_unit_eur",
                    "uio_units",
                    "wallet_mix_n75_pct",
                    "wallet_mix_f_pct",
                    "wallet_mix_lcv_pct",
                    "uio_proxy",
                ]
            ].copy()
            tbl["Rank"] = range(1, len(tbl) + 1)
            show = tbl.rename(
                columns={
                    "distributor_code": "Distributor",
                    "gps_pct": "Wallet capture %",
                    "total_sales_eur": "Sales €",
                    "target_wallet_eur": "Target wallet €",
                    "spend_per_unit_eur": "Spend/unit €",
                    "uio_units": "UIO",
                    "wallet_mix_n75_pct": "N75 mix %",
                    "wallet_mix_f_pct": "F mix %",
                    "wallet_mix_lcv_pct": "LCV mix %",
                    "uio_proxy": "UIO proxy",
                }
            )[
                [
                    "Rank",
                    "Distributor",
                    "Wallet capture %",
                    "Sales €",
                    "Target wallet €",
                    "Spend/unit €",
                    "UIO",
                    "N75 mix %",
                    "F mix %",
                    "LCV mix %",
                    "UIO proxy",
                ]
            ]
            gps_numeric = tbl["gps_pct"].tolist()
            show["Sales €"] = show["Sales €"].map(lambda x: _fmt_eur(x, 0))
            show["Target wallet €"] = show["Target wallet €"].map(lambda x: _fmt_eur(x, 0))
            show["Spend/unit €"] = show["Spend/unit €"].map(lambda x: _fmt_eur(x, 1))
            show["UIO"] = show["UIO"].map(lambda x: f"{int(x):,}")
            show["Wallet capture %"] = [f"{v:.0f}%" for v in gps_numeric]
            for col in ("N75 mix %", "F mix %", "LCV mix %"):
                show[col] = show[col].map(lambda x: f"{x:.0f}%")
            show["UIO proxy"] = show["UIO proxy"].map(lambda x: "Yes" if x else "")

            def _color_gps_column(_col):
                return [_style_gps_pct(v) for v in gps_numeric]

            styled = show.style.apply(_color_gps_column, subset=["Wallet capture %"])
            st.dataframe(styled, width='stretch', hide_index=True)

        with st.expander("Model targets & ITUK study reference", expanded=False):
            st.markdown(
                "Row 38 in *ITUK Parts Sales Target Study* = **Actual ÷ sum(model stretch targets)**. "
                "PRISM uses **maximum** €/vehicle rates (your GPS table); ITUK planning also applies "
                "66% × 1.12 stretch on potential — so ITUK study % will read lower than 100% max-wallet."
            )
            try:
                st.dataframe(
                    load_gps_model_targets(str(GPS_MODEL_TARGETS_CSV)),
                    width='stretch',
                    hide_index=True,
                )
            except Exception as exc:
                st.warning(f"Could not load targets: {exc}")

        if not df_mt.empty:
            with st.expander("Wallet capture % heatmap by year (all distributors)", expanded=False):
                pivot = df_mt.pivot_table(
                    index="distributor_code",
                    columns="year_value",
                    values="gps_pct",
                    aggfunc="mean",
                )
                pivot = pivot.sort_index()
                yr_cols = [c for c in pivot.columns if pd.notna(c)]
                pivot.columns = [_year_label(int(c)) for c in yr_cols]
                st.dataframe(
                    pivot.style.applymap(_style_gps_pct).format("{:.0f}%", na_rep="—"),
                    width='stretch',
                )

            with st.expander("Single distributor — year-on-year line", expanded=False):
                pick = st.selectbox(
                    "Distributor",
                    options=sorted(df_mt["distributor_code"].unique()),
                    index=(
                        sorted(df_mt["distributor_code"].unique()).index("ITUK")
                        if "ITUK" in df_mt["distributor_code"].values
                        else 0
                    ),
                    key="gps_yoy_pick",
                )
                df_one = df_mt[df_mt["distributor_code"] == pick].sort_values("year_value")
                if not df_one.empty:
                    df_one = df_one.copy()
                    df_one["yoy_pp"] = df_one["gps_pct"].diff()
                    labels = []
                    for i, row in df_one.iterrows():
                        if pd.isna(row["yoy_pp"]):
                            labels.append(f"{row['gps_pct']:.0f}%")
                        else:
                            sign = "+" if row["yoy_pp"] >= 0 else ""
                            labels.append(f"{row['gps_pct']:.0f}%<br>({sign}{row['yoy_pp']:.0f}pp)")
                    fig_yoy = go.Figure(
                        go.Scatter(
                            x=df_one["year_value"].map(_year_label),
                            y=df_one["gps_pct"],
                            mode="lines+markers+text",
                            text=labels,
                            textposition="top center",
                            line=dict(color=ISZE_BLUE, width=2),
                            marker=dict(size=8),
                        )
                    )
                    fig_yoy.add_hline(
                        y=100,
                        line_dash="dash",
                        line_color="#888",
                        annotation_text="100% = full wallet capture",
                        annotation_position="bottom right",
                    )
                    fig_yoy.update_layout(
                        height=340,
                        yaxis_title="Wallet capture %",
                        xaxis_title="Period",
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        yaxis=dict(gridcolor="#F0F0F0"),
                        margin=dict(t=40, b=20),
                    )
                    st.caption(
                        "**Wallet capture % year-on-year for selected distributor.** "
                        "pp = percentage point change vs prior year. "
                        "Upward trend = improving wallet capture. "
                        "Flat line = neither gaining nor losing share of the potential."
                    )
                    st.plotly_chart(style(fig_yoy), width='stretch')

        st.divider()

        st.markdown("#### Spend per Unit Trend by Distributor (€/vehicle)")
        st.caption(
            "**Formula: SPU = Net genuine parts sales (€) ÷ UIO** "
            "| Shows whether a distributor is extracting more or less value per truck over time, "
            "independent of fleet size changes. "
            "A rising line = improving genuine parts penetration. A falling line = losing ground. "
            "📌 Each year uses year-matched UIO (2022–2024 actual). 2025/2026 use 2024 as proxy — "
            "SPU change in those years reflects sales movement only, not real fleet changes."
        )
        if df_trend_uio.empty:
            st.info("Spend/unit trend chart needs legacy UIO totals — reload after UIO file is available.")
        else:
            default_dists = [
                d for d in ['ITUK', 'IUK', 'UTI', 'UMI', 'NORWAY', 'PORTUGAL', 'GERMANY', 'IRELAND']
                if d in all_dists
            ]
            selected_trend_dists = st.multiselect(
                "Distributors to display",
                options=sorted(df_trend_uio['distributor_code'].unique()),
                default=default_dists[:6] if default_dists else all_dists[:6],
            )

            df_trend_filtered = df_trend_uio[
                df_trend_uio['distributor_code'].isin(selected_trend_dists)
            ]

            if not df_trend_filtered.empty:
                fig3 = px.line(
                    df_trend_filtered,
                    x='year_value',
                    y='spend_per_unit_eur',
                    color='distributor_code',
                    markers=True,
                    labels={
                        'year_value': 'Year',
                        'spend_per_unit_eur': 'Spend/Unit (EUR)',
                        'distributor_code': 'Distributor',
                    },
                    color_discrete_sequence=PALETTE,
                )
                fig3.add_hline(
                    y=150, line_dash="dash", line_color="#1B3A6B",
                    annotation_text="€150 — ISZE minimum target", opacity=0.5,
                    annotation_position="bottom right",
                )
                fig3.update_layout(
                    height=450,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    yaxis=dict(gridcolor='#F0F0F0', tickprefix="€"),
                    xaxis=dict(gridcolor='#F0F0F0', dtick=1),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                    margin=dict(l=10, r=10, t=20, b=10),
                )
                st.plotly_chart(style(fig3), width='stretch')

            st.divider()

            st.markdown("#### Revenue Growth YoY by Distributor (%)")
            st.caption(
                "**YoY % = (Sales this year − Sales prior year) ÷ Sales prior year × 100** "
                "| Unlike absolute sales, this removes fleet-size bias. "
                "A distributor with 100k trucks shouldn't automatically look better than one with 5k. "
                "🟢 positive = growing genuine parts revenue · 🔴 negative = declining."
            )
            if selected_trend_dists and not df_trend.empty:
                df_sales_trend = df_trend[
                    df_trend['distributor_code'].isin(selected_trend_dists)
                ].sort_values(['distributor_code', 'year_value'])
                df_sales_trend = df_sales_trend.copy()
                df_sales_trend['yoy_pct'] = df_sales_trend.groupby('distributor_code')['total_sales_eur'].pct_change() * 100
                df_yoy = df_sales_trend.dropna(subset=['yoy_pct'])
                if not df_yoy.empty:
                    fig4 = px.bar(
                        df_yoy,
                        x='year_value',
                        y='yoy_pct',
                        color='distributor_code',
                        barmode='group',
                        labels={
                            'year_value': 'Year',
                            'yoy_pct': 'Revenue growth (%)',
                            'distributor_code': 'Distributor',
                        },
                        color_discrete_sequence=PALETTE,
                    )
                    fig4.add_hline(y=0, line_color="#333", line_width=1)
                    fig4.update_layout(
                        height=400,
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        yaxis=dict(gridcolor='#F0F0F0', ticksuffix="%"),
                        xaxis=dict(gridcolor='#F0F0F0', dtick=1),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.35),
                        margin=dict(l=10, r=10, t=20, b=10),
                    )
                    st.plotly_chart(style(fig4), width='stretch')
                else:
                    st.info("Need at least two years of data per distributor to compute YoY growth.")

            st.divider()

            st.markdown("#### Spend per Unit Summary Table (€/vehicle)")
            pivot = df_trend_uio.pivot_table(
                index='distributor_code',
                columns='year_value',
                values='spend_per_unit_eur',
                aggfunc='mean',
            ).reset_index().rename(columns={'distributor_code': 'Distributor'})
            for c in [col for col in pivot.columns if col != "Distributor"]:
                pivot[c] = pivot[c].apply(lambda x: f"€{x:,.1f}" if pd.notna(x) else "—")
            st.dataframe(pivot, width='stretch', hide_index=True)
            st.caption("UIO: actual V17 data for 2020–2024. 2025/2026 = 2024 proxy (⚠️)")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3: Part Explorer
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Part Explorer")
    st.caption("Explore top-selling parts by distributor and year. Useful for PMS classification validation.")

    col1, col2, col3 = st.columns(3)
    with col1:
        exp_year = st.selectbox(
            "Year", available_years, key="exp_year",
            index=available_years.index(selected_year),
        )
    with col2:
        exp_dist = st.selectbox(
            "Distributor (or All)",
            ["All"] + sorted(df_sales['distributor_code'].unique().tolist()),
            key="exp_dist",
        )
    with col3:
        top_n = st.slider("Top N parts", 10, 100, 30, key="exp_n")

    dist_filter = None if exp_dist == "All" else exp_dist

    with st.spinner("Loading parts…"):
        df_parts = get_top_parts(
            df_sales, year=exp_year, year_type=year_type,
            distributor_code=dist_filter, top_n=top_n,
        )

    if not df_parts.empty:
        st.markdown(
            f"#### Top {top_n} Parts by Revenue — {exp_dist} | "
            f"{'FY' if year_type == 'fiscal' else ''}{exp_year}"
        )

        @st.cache_data(show_spinner=False)
        def _load_parts_catalog_index():
            return load_catalog_index()

        _catalog = _load_parts_catalog_index()
        df_parts = enrich_top_parts_table(df_parts, _catalog)
        df_parts["Sales EUR"] = df_parts["total_sales_eur"].apply(lambda x: _fmt_eur(x, 0))
        df_parts["Qty"] = df_parts["total_qty"].apply(lambda x: f"{int(x):,}")
        df_parts["# Markets"] = df_parts["n_distributors"]
        df_parts["Fig Key"] = df_parts["fig_key"].fillna("—")
        df_parts["PMS Category"] = df_parts["pms_category"].fillna("—")

        st.dataframe(
            df_parts.rename(
                columns={
                    "part_number": "Part Number",
                    "description": "Description",
                    "rank": "Rank",
                    "category_hint": "Category",
                }
            )[
                [
                    "Rank",
                    "Part Number",
                    "Description",
                    "Fig Key",
                    "PMS Category",
                    "Category",
                    "Sales EUR",
                    "Qty",
                    "# Markets",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        if _catalog.empty:
            st.warning(
                "Fig-key catalogue not built. Run: "
                "`python scripts/build_fig_key_dimension.py` "
                "(after `build_pr00_classification.py` and `build_bvp_p0_p1.py`)."
            )
        st.caption(
            "Category from `parts_catalog_dimension.csv` (GPS V2): "
            "✅/🔑 = PMS registry or EPC fig key · "
            "📘 = PR00 family/group · "
            "🟦/🟧 = keyword fallback · "
            "Rebuild: `build_fig_key_dimension.py` · "
            "Add EPC rows in `data/fig_key_pn_overrides.csv`."
        )

        if not _catalog.empty and exp_dist != "All":
            rollup_path = DERIVED_DIR / "sales_by_db_fig_key_year.csv"
            if rollup_path.is_file():
                fk = pd.read_csv(rollup_path)
                sub = fk[
                    (fk["distributor_code"] == exp_dist)
                    & (fk["year"] == exp_year)
                    & (fk["fig_key"] != "unmapped")
                ].sort_values("net_sales_eur", ascending=False)
                if not sub.empty:
                    st.markdown(f"#### Sales by fig key — {exp_dist} CY{exp_year}")
                    st.dataframe(
                        sub[
                            [
                                "fig_key",
                                "fig_key_label",
                                "net_sales_eur",
                                "billed_qty",
                                "distinct_pns",
                            ]
                        ].rename(
                            columns={
                                "fig_key": "Fig key",
                                "fig_key_label": "Label",
                                "net_sales_eur": "Net sales EUR",
                                "billed_qty": "Qty",
                                "distinct_pns": "PNs",
                            }
                        ),
                        width="stretch",
                        hide_index=True,
                    )
    else:
        st.info("No parts data for current selection.")

    st.divider()
    st.markdown("#### 📅 YTD Comparison — Current Year vs Prior Year (Same Period)")
    st.caption(
        "**Compares YTD sales for the current year up to the latest available month, "
        "against the same months in the prior year.** "
        "| Removes seasonality bias — a fair like-for-like comparison. "
        "| Growth = genuine parts revenue increasing vs same period last year."
    )

    try:
        df_monthly = calculate_monthly_sales(df_sales, year_type=year_type)
        if not df_monthly.empty:
            yr_col = "year_value"
            available_ytd_years = sorted(df_monthly[yr_col].dropna().unique().astype(int).tolist(), reverse=True)
            if len(available_ytd_years) >= 2:
                current_ytd_yr = available_ytd_years[0]
                prior_ytd_yr = available_ytd_years[1]
                # Latest month with data in current year
                current_months = df_monthly[df_monthly[yr_col] == current_ytd_yr]["month"].dropna().unique()
                if len(current_months) > 0:
                    max_month = int(max(current_months))
                    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

                    df_curr = df_monthly[
                        (df_monthly[yr_col] == current_ytd_yr) & (df_monthly["month"] <= max_month)
                    ].groupby("distributor_code").agg(ytd_sales=("net_sales_eur", "sum")).reset_index()

                    df_prior = df_monthly[
                        (df_monthly[yr_col] == prior_ytd_yr) & (df_monthly["month"] <= max_month)
                    ].groupby("distributor_code").agg(prior_sales=("net_sales_eur", "sum")).reset_index()

                    df_ytd = df_curr.merge(df_prior, on="distributor_code", how="outer").fillna(0)
                    df_ytd["yoy_pct"] = (df_ytd["ytd_sales"] - df_ytd["prior_sales"]) / df_ytd["prior_sales"].replace(0, np.nan) * 100
                    df_ytd = df_ytd.sort_values("yoy_pct", ascending=True)

                    if selected_dists:
                        df_ytd = df_ytd[df_ytd["distributor_code"].isin(selected_dists)]

                    st.caption(
                        f"Comparing Jan–{month_names[max_month]} {current_ytd_yr} "
                        f"vs Jan–{month_names[max_month]} {prior_ytd_yr}"
                    )

                    colors_ytd = [ISZE_ORANGE if v >= 0 else "#C62828" for v in df_ytd["yoy_pct"]]
                    fig_ytd = go.Figure(go.Bar(
                        x=df_ytd["yoy_pct"],
                        y=df_ytd["distributor_code"],
                        orientation="h",
                        marker_color=colors_ytd,
                        text=df_ytd["yoy_pct"].apply(lambda v: f"+{v:.1f}%" if v >= 0 else f"{v:.1f}%" if pd.notna(v) else "—"),
                        textposition="outside",
                        customdata=np.stack([df_ytd["ytd_sales"], df_ytd["prior_sales"]], axis=-1),
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            f"YTD {current_ytd_yr}: €%{{customdata[0]:,.0f}}<br>"
                            f"YTD {prior_ytd_yr}: €%{{customdata[1]:,.0f}}<br>"
                            "YoY: %{x:.1f}%<extra></extra>"
                        ),
                    ))
                    fig_ytd.add_vline(x=0, line_color="#333", line_width=1)
                    fig_ytd.update_layout(
                        height=max(300, len(df_ytd) * 28),
                        margin=dict(l=10, r=80, t=20, b=20),
                        xaxis_title="YoY revenue growth (%)",
                        xaxis=dict(ticksuffix="%", gridcolor="#F0F0F0"),
                        plot_bgcolor="white", paper_bgcolor="white",
                    )
                    st.plotly_chart(style(fig_ytd), width='stretch')
    except Exception as _e:
        st.caption(f"YTD comparison unavailable: {_e}")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 4: Export
# ═════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Export Dashboard")

    with st.spinner("Computing full trend data for export…"):
        df_trend_exp = _load_trends(year_type)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📊 Excel: GPS Dashboard")
        st.markdown(
            f"Generates a formatted Excel workbook for **{period_label}**.\n\n"
            "Includes: Executive Summary, Spend per Unit table (with traffic lights), "
            "Year-on-Year trends, and Metadata sheet."
        )
        if st.button("Generate Excel", type="primary"):
            with st.spinner("Generating Excel…"):
                try:
                    xlsx_bytes = export_gps_dashboard_excel(
                        df_spu=df_spu,
                        df_trend=df_trend_exp,
                        selected_year=selected_year,
                        year_type=year_type,
                    )
                    fy_label = f"FY{selected_year}" if year_type == "fiscal" else str(selected_year)
                    filename = f"ISZE_GPS_Dashboard_{fy_label}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    st.download_button(
                        label="⬇️ Download Excel",
                        data=xlsx_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="secondary",
                    )
                    st.success(f"✅ Excel generated: {filename}")
                except Exception as e:
                    st.error(f"Export failed: {e}")

    with col_right:
        st.markdown("#### 📋 CSV Export (Power BI)")
        st.markdown(
            "Exports flat CSV files for Power BI ingestion:\n"
            "- `spend_per_unit.csv` — full SPU table (all distributors)\n"
            "- `trends.csv` — year-on-year data (year-matched UIO)\n"
        )
        if st.button("Generate CSVs", type="secondary"):
            with st.spinner("Generating CSVs…"):
                zip_buf = _io.BytesIO()
                with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr("spend_per_unit.csv", df_spu.to_csv(index=False))
                    zf.writestr(
                        "trends.csv",
                        df_trend_exp.to_csv(index=False) if not df_trend_exp.empty else "",
                    )

                zip_buf.seek(0)
                fy_label = f"FY{selected_year}" if year_type == "fiscal" else str(selected_year)
                st.download_button(
                    label="⬇️ Download ZIP",
                    data=zip_buf.read(),
                    file_name=f"ISZE_GPS_CSV_{fy_label}_{datetime.now().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                    type="secondary",
                )
                st.success("✅ CSVs generated")

    st.divider()

    st.markdown("#### 📋 Raw Data Preview")
    with st.expander("Show filtered sales data (first 500 rows)"):
        year_col = 'fiscal_year' if year_type == "fiscal" else 'year'
        df_raw_preview = df_sales_filtered[df_sales_filtered[year_col] == selected_year].head(500)
        st.dataframe(df_raw_preview, width='stretch')

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer-note">ISZE GPS Dashboard — Confidential | '
    'Vehicle Parts Sales, Isuzu Motors Europe | '
    f'Data: 2022–2026 YTD | UIO Reference: 2024 | '
    f'Built: {data_freshness_date()}</div>',
    unsafe_allow_html=True,
)
