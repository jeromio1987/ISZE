"""
ISZE GPS & Spend per Unit Dashboard
Isuzu Motors Europe — Vehicle Parts Sales

Run with:
    streamlit run app.py

Data files expected in ./data/ folder (symlinked or copied from source):
    - sales_detailed_for_claude_full_fixed.tsv
    - uio_distributor_year.csv
    - distributor_master_mapping.csv
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

# Data directory: prefer ISZE/Data/derived, then local ./data, then ../data
_ISZE_DATA = APP_DIR.parent.parent.parent / "Data"
_DERIVED_PARQUET = _ISZE_DATA / "derived" / "sales_fact.parquet"
_local_data = APP_DIR / "data"
_parent_data = APP_DIR.parent / "data"
if (_local_data / "distributor_master_mapping.csv").exists():
    DATA_DIR = _local_data
elif (_parent_data / "distributor_master_mapping.csv").exists():
    DATA_DIR = _parent_data
else:
    DATA_DIR = _local_data

# PRISM shared loaders (when prism package is present)
_PRISM_ROOT = APP_DIR.parent / "prism"
if _PRISM_ROOT.exists():
    sys.path.insert(0, str(_PRISM_ROOT))
    try:
        from config import resolve_mapping_path, resolve_uio_path
        from modules.sales_loader import load_prism_sales
        _USE_PRISM_PATHS = True
    except ImportError:
        _USE_PRISM_PATHS = False
else:
    _USE_PRISM_PATHS = False

from modules.data_prep import (
    load_distributor_mapping, load_uio_from_excel, load_sales_data,
    get_distributor_metadata, UIO_PROXY_YEAR
)
from modules.gps_calculator import (
    calculate_spend_per_unit, calculate_multiyear_trends,
    calculate_monthly_sales, get_top_parts, get_summary_kpis
)
from modules.export_engine import export_gps_dashboard_excel
from modules.pms_engine import (
    classify_pms_sales, calculate_pms_capture,
    calculate_ituk_incentive, get_pms_summary_by_distributor,
    PMS_PN_REGISTRY, CATEGORY_LABELS, PHASE1_CATEGORIES,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ISZE | GPS Dashboard",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

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


# ── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading distributor mapping…")
def _load_mapping():
    if _USE_PRISM_PATHS:
        return load_distributor_mapping(str(resolve_mapping_path()))
    return load_distributor_mapping(str(DATA_DIR / "distributor_master_mapping.csv"))

@st.cache_data(show_spinner="Loading UIO data…")
def _load_uio():
    if _USE_PRISM_PATHS:
        return load_uio_from_excel(str(resolve_uio_path()))
    for name in [
        "ISUZU_UIO_Overview_2026_v17.xlsx",
        "ISUZU_UIO_Overview_2026_v13.xlsx",
        "ISUZU_UIO_Overview_2026_v12.xlsx",
    ]:
        p = DATA_DIR / name
        if p.exists():
            return load_uio_from_excel(str(p))
    raise FileNotFoundError(f"UIO Excel file not found in {DATA_DIR}")

@st.cache_data(show_spinner="Loading sales data…")
def _load_sales(mapping_hash):
    df_map = _load_mapping()
    if _USE_PRISM_PATHS:
        df, _source = load_prism_sales(df_map)
        return df
    for name in [
        "sales_detailed_for_claude_full_fixed.tsv",
        "sales_detailed_for_claude_full_fixed(1).csv",
        "sales_detailed_for_claude_full_fixed.csv",
    ]:
        p = DATA_DIR / name
        if p.exists():
            return load_sales_data(str(p), df_map)
    if _DERIVED_PARQUET.exists():
        df, _source = load_prism_sales(df_map)
        return df
    raise FileNotFoundError(
        f"Sales data not found. Build {_DERIVED_PARQUET} or add TSV under {DATA_DIR}"
    )

@st.cache_data(show_spinner="Computing year-on-year trends…")
def _load_trends(year_type):
    df_map = _load_mapping()
    df_uio = _load_uio()
    df_meta = get_distributor_metadata(df_map)
    df_sales = _load_sales("v1")
    df_trend = calculate_multiyear_trends(df_sales, df_uio, df_meta, year_type=year_type)
    return df_trend


# ── Helpers ───────────────────────────────────────────────────────────────────
ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
PALETTE = [
    "#1B3A6B", "#E87722", "#2C5AA0", "#F4A460", "#4A90D9",
    "#8B4513", "#70B8FF", "#D2691E", "#003087", "#FFA07A",
    "#1E90FF", "#CD853F", "#87CEEB", "#D2691E", "#4169E1"
]

def _fmt_eur(v, decimals=0):
    if pd.isna(v): return "—"
    return f"€{v:,.{decimals}f}"

def _traffic_label(v, low=50, mid=150):
    if pd.isna(v): return "—"
    if v >= mid: return f"🟢 {_fmt_eur(v,1)}"
    elif v >= low: return f"🟡 {_fmt_eur(v,1)}"
    else: return f"🔴 {_fmt_eur(v,1)}"

def _traffic_color(v, low=50, mid=150):
    if pd.isna(v): return None
    if v >= mid: return "background-color: #C8E6C9"
    elif v >= low: return "background-color: #FFE5B4"
    else: return "background-color: #FFCCCC"

def _style_spu(val):
    return _traffic_color(val) or ""


# ── Main layout ───────────────────────────────────────────────────────────────
def main():
    # Load data
    try:
        df_mapping = _load_mapping()
        df_uio = _load_uio()          # multi-year from V13 Excel
        df_meta = get_distributor_metadata(df_mapping)
        df_sales = _load_sales("v1")
    except Exception as e:
        st.error(f"❌ Failed to load data: {e}")
        st.stop()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="main-header">
        <h1>🚛 ISZE GPS Dashboard — Genuine Parts Share & Spend per Unit</h1>
        <p>Isuzu Motors Europe | Vehicle Parts Sales | Confidential</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Isuzu_logo.svg/200px-Isuzu_logo.svg.png",
                 width=120) if False else None  # Skip logo if no internet
        st.title("⚙️ Filters")

        year_type_label = st.radio(
            "Year type",
            ["Calendar Year (Jan–Dec)", "Fiscal Year (Apr–Mar)"],
            help="ISZE Fiscal Year runs April–March. FY2024 = Apr 2024 – Mar 2025."
        )
        year_type = "fiscal" if "Fiscal" in year_type_label else "calendar"

        # Available years
        if year_type == "fiscal":
            available_years = sorted(df_sales['fiscal_year'].dropna().unique().astype(int).tolist())
        else:
            available_years = sorted(df_sales['year'].dropna().unique().astype(int).tolist())

        default_year = 2024 if 2024 in available_years else available_years[-1]
        selected_year = st.selectbox(
            "Period",
            options=available_years,
            index=available_years.index(default_year),
            format_func=lambda y: f"FY{y} (Apr {y}–Mar {y+1})" if year_type == "fiscal" else str(y)
        )

        st.divider()

        # Region filter
        regions = ["All regions"] + sorted(df_meta['region'].dropna().unique().tolist())
        selected_region = st.selectbox("Region", regions)

        # Distributor filter
        dist_options = sorted(df_sales['distributor_code'].unique().tolist())
        if selected_region != "All regions":
            filtered_dist = df_meta[df_meta['region'] == selected_region]['distributor_code'].tolist()
            dist_options = [d for d in dist_options if d in filtered_dist]

        selected_dists = st.multiselect(
            "Distributors (leave empty = all)",
            options=dist_options,
            default=[],
        )

        st.divider()
        st.caption("📅 Data: 2022–2026 YTD")
        st.caption("📌 UIO: V13 Excel (2020–2024 actual; 2025/2026 = 2024 proxy)")
        st.caption("🔢 ITUK/IUK and UTI/UMI split by CV/LCV segment")
        st.caption(f"🔄 Built: {datetime.now().strftime('%d %b %Y')}")

    # ── Apply filters ─────────────────────────────────────────────────────────
    df_sales_filtered = df_sales.copy()
    if selected_dists:
        df_sales_filtered = df_sales_filtered[
            df_sales_filtered['distributor_code'].isin(selected_dists)
        ]
    if selected_region != "All regions":
        valid_dists = df_meta[df_meta['region'] == selected_region]['distributor_code'].tolist()
        df_sales_filtered = df_sales_filtered[
            df_sales_filtered['distributor_code'].isin(valid_dists)
        ]

    # ── Calculate metrics ─────────────────────────────────────────────────────
    df_spu = calculate_spend_per_unit(
        df_sales_filtered, df_uio, df_meta,
        year=selected_year, year_type=year_type
    )

    period_label = f"FY{selected_year} (Apr {selected_year}–Mar {selected_year+1})" \
                   if year_type == "fiscal" else str(selected_year)

    uio_is_proxy = selected_year not in [2020, 2021, 2022, 2023, 2024]
    n_proxy = int(df_spu.get('uio_proxy', pd.Series(False)).sum()) if 'uio_proxy' in df_spu.columns else 0

    # ── UIO proxy warning (only for 2025/2026) ───────────────────────────────
    if uio_is_proxy:
        st.markdown(
            f'<div class="proxy-warning">⚠️ <strong>UIO proxy active for {period_label}</strong> — '
            f'No V13 UIO data for this year. Using 2024 UIO as denominator. '
            f'Results show sales volume change vs fixed fleet.</div>',
            unsafe_allow_html=True
        )
        st.markdown("")

    # ── Known data quality flags ──────────────────────────────────────────────
    with st.expander("ℹ️ Known data quality flags", expanded=False):
        st.markdown("""
**Poland (POLAND):** UIO = 27 units in V13 (declining, D-Max only market per IBX data).
Sales = €2M+/year → spend/unit is not a meaningful metric. Exclude from benchmarking.

**ITUK vs IUK:** Now correctly split. ITUK = CV trucks (LD + F-Series UIO: 22,389 in 2024).
IUK = LCV D-Max (UIO: 48,876 in 2024). Previously both incorrectly used 71,265 combined.

**UTI vs UMI (Israel):** Now correctly split. UTI = CV trucks (Universal Trucks Israel, LD+MD: 10,668 in 2024).
UMI = LCV D-Max (Universal Motors Israel: 18,349 in 2024). Previously both used combined 29,017.

**MIDI (Italy):** Excluded. No ISZE direct sales data available; Italy UIO (92k) not attributable to ISZE.

**UIO source:** V13 Excel (ISUZU_UIO_Overview_2026_v13.xlsx). Actuals 2020–2024.
2025/2026 use 2024 as proxy (flagged where applied).
        """)
    st.markdown("")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 GPS Overview",
        "📈 Trends",
        "🗺️ By Region",
        "🔍 Part Explorer",
        "🔧 PMS Coverage",
        "📥 Export",
    ])

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 1: GPS Overview
    # ═════════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader(f"Spend per Unit | {period_label}")

        # KPI tiles
        df_with_uio = df_spu[df_spu['uio_units'] > 0]
        total_sales = df_spu['total_sales_eur'].sum()
        n_dist = df_spu['distributor_code'].nunique()
        avg_spu = df_with_uio['spend_per_unit_eur'].mean() if not df_with_uio.empty else 0
        max_spu = df_with_uio['spend_per_unit_eur'].max() if not df_with_uio.empty else 0
        top_dist = df_with_uio.loc[df_with_uio['spend_per_unit_eur'].idxmax(), 'distributor_code'] \
                   if not df_with_uio.empty else "—"

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
            df_chart = df_spu[df_spu['uio_units'] > 0].sort_values(
                'spend_per_unit_eur', ascending=True
            )
            if not df_chart.empty:
                # Color by traffic light
                colors = []
                for v in df_chart['spend_per_unit_eur']:
                    if v >= 150: colors.append('#2E7D32')
                    elif v >= 50: colors.append('#F9A825')
                    else: colors.append('#C62828')

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
                    )
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
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No distributors with UIO data in current selection.")

        with col_right:
            st.markdown("#### Total Sales by Distributor")
            # Top 20 by sales (largest first), sorted ascending for horizontal bar display
            df_sales_chart = df_spu.nlargest(20, 'total_sales_eur').sort_values('total_sales_eur', ascending=True)
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
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.markdown("#### Detail Table")

        # Build display table
        df_display = df_spu[[
            'distributor_code', 'country', 'region',
            'total_sales_eur', 'total_qty', 'uio_units', 'uio_year',
            'spend_per_unit_eur', 'uio_proxy'
        ]].copy()
        df_display = df_display.sort_values('spend_per_unit_eur', ascending=False, na_position='last')
        df_display['Spend/Unit'] = df_display['spend_per_unit_eur'].apply(_traffic_label)
        df_display['Sales EUR'] = df_display['total_sales_eur'].apply(lambda x: _fmt_eur(x, 0))
        df_display['Qty'] = df_display['total_qty'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
        df_display['UIO'] = df_display.apply(
            lambda r: f"{int(r['uio_units']):,} ({int(r['uio_year'])})" if r['uio_units'] > 0 else "No data",
            axis=1
        )
        df_display['UIO Source'] = df_display['uio_proxy'].apply(lambda x: "⚠️ 2024 proxy" if x else "✅ actual")

        df_show = df_display.rename(columns={
            'distributor_code': 'Distributor',
            'country': 'Country',
            'region': 'Region',
        })[['Distributor', 'Country', 'Region', 'Sales EUR', 'Qty', 'UIO', 'Spend/Unit', 'UIO Source']]

        st.dataframe(df_show, use_container_width=True, hide_index=True)

        # No-UIO distributors note
        no_uio = df_spu[df_spu['uio_units'] == 0][['distributor_code', 'country', 'total_sales_eur']]
        if not no_uio.empty:
            with st.expander(f"ℹ️ {len(no_uio)} distributors excluded from spend/unit (no UIO data)"):
                no_uio_show = no_uio.rename(columns={
                    'distributor_code': 'Distributor', 'country': 'Country', 'total_sales_eur': 'Sales EUR'
                })
                no_uio_show['Sales EUR'] = no_uio_show['Sales EUR'].apply(lambda x: _fmt_eur(x, 0))
                st.dataframe(no_uio_show, use_container_width=True, hide_index=True)

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 2: Trends
    # ═════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Year-on-Year Trends")

        with st.spinner("Computing trends across all years…"):
            df_trend = _load_trends(year_type)

        if df_trend.empty:
            st.info("No trend data available.")
        else:
            st.markdown("#### Spend per Unit Trend by Distributor (€/vehicle)")
            st.caption("📌 Each year uses its own UIO (2022–2024 actual from V13). 2025/2026 use 2024 proxy.")

            df_trend_uio = df_trend[df_trend['uio_units'] > 0].sort_values(['distributor_code', 'year_value'])

            # Select distributors to show
            all_dists = sorted(df_trend_uio['distributor_code'].unique().tolist())
            default_dists = [d for d in ['ITUK', 'IUK', 'UTI', 'UMI', 'NORWAY', 'PORTUGAL', 'GERMANY', 'IRELAND'] if d in all_dists]
            selected_trend_dists = st.multiselect(
                "Distributors to display",
                options=all_dists,
                default=default_dists[:6] if default_dists else all_dists[:6],
            )

            df_trend_filtered = df_trend_uio[df_trend_uio['distributor_code'].isin(selected_trend_dists)]

            if not df_trend_filtered.empty:
                fig3 = px.line(
                    df_trend_filtered,
                    x='year_value',
                    y='spend_per_unit_eur',
                    color='distributor_code',
                    markers=True,
                    labels={'year_value': 'Year', 'spend_per_unit_eur': 'Spend/Unit (EUR)', 'distributor_code': 'Distributor'},
                    color_discrete_sequence=PALETTE,
                )
                fig3.add_hline(y=150, line_dash="dash", line_color="#1B3A6B",
                               annotation_text="€150 target", opacity=0.5)
                fig3.update_layout(
                    height=450, plot_bgcolor='white', paper_bgcolor='white',
                    yaxis=dict(gridcolor='#F0F0F0', tickprefix="€"),
                    xaxis=dict(gridcolor='#F0F0F0', dtick=1),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                    margin=dict(l=10, r=10, t=20, b=10),
                )
                st.plotly_chart(fig3, use_container_width=True)

            st.divider()

            # ── Total Sales Trend ─────────────────────────────────────────
            st.markdown("#### Total Sales Trend by Distributor (EUR)")
            if selected_trend_dists:
                df_sales_trend = df_trend[df_trend['distributor_code'].isin(selected_trend_dists)]
                fig4 = px.bar(
                    df_sales_trend, x='year_value', y='total_sales_eur',
                    color='distributor_code', barmode='group',
                    labels={'year_value': 'Year', 'total_sales_eur': 'Sales (EUR)', 'distributor_code': 'Distributor'},
                    color_discrete_sequence=PALETTE,
                )
                fig4.update_layout(
                    height=400, plot_bgcolor='white', paper_bgcolor='white',
                    yaxis=dict(gridcolor='#F0F0F0', tickprefix="€", tickformat=",.0f"),
                    xaxis=dict(gridcolor='#F0F0F0', dtick=1),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.35),
                    margin=dict(l=10, r=10, t=20, b=10),
                )
                st.plotly_chart(fig4, use_container_width=True)

            st.divider()

            # ── Pivot table ──────────────────────────────────────────────
            st.markdown("#### Spend per Unit Summary Table (€/vehicle)")
            pivot = df_trend_uio.pivot_table(
                index='distributor_code', columns='year_value', values='spend_per_unit_eur', aggfunc='mean'
            ).reset_index().rename(columns={'distributor_code': 'Distributor'})
            for c in [col for col in pivot.columns if c != 'Distributor']:
                pivot[c] = pivot[c].apply(lambda x: f"€{x:,.1f}" if pd.notna(x) else "—")
            st.dataframe(pivot, use_container_width=True, hide_index=True)
            st.caption("UIO: actual V13 data for 2022–2024. 2025/2026 = 2024 proxy (⚠️)")

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 3: By Region
    # ═════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader(f"Regional Breakdown | {period_label}")

        if df_spu.empty:
            st.info("No data for current selection.")
        else:
            # ── Regional aggregation from df_spu (region already attached) ──
            df_reg_agg = (
                df_spu.groupby('region')
                .agg(
                    total_sales_eur=('total_sales_eur', 'sum'),
                    n_distributors=('distributor_code', 'nunique'),
                )
                .reset_index()
                .sort_values('total_sales_eur', ascending=False)
            )

            col1, col2 = st.columns([2, 3])

            with col1:
                st.markdown("#### Sales by Region")
                fig5 = px.pie(
                    df_reg_agg,
                    values='total_sales_eur',
                    names='region',
                    color_discrete_sequence=PALETTE,
                    hole=0.4,
                )
                fig5.update_layout(
                    height=350,
                    margin=dict(l=10, r=10, t=20, b=10),
                    legend=dict(orientation="v"),
                )
                fig5.update_traces(texttemplate='%{label}<br>€%{value:,.0f}')
                st.plotly_chart(fig5, use_container_width=True)

            with col2:
                st.markdown("#### Spend per Unit by Distributor")
                df_grp_chart = df_spu[df_spu['uio_units'] > 0].sort_values(
                    'spend_per_unit_eur', ascending=True
                )
                if not df_grp_chart.empty:
                    colors_grp = []
                    for v in df_grp_chart['spend_per_unit_eur']:
                        if v >= 150: colors_grp.append('#2E7D32')
                        elif v >= 50: colors_grp.append('#F9A825')
                        else: colors_grp.append('#C62828')

                    fig6 = go.Figure(go.Bar(
                        x=df_grp_chart['spend_per_unit_eur'],
                        y=df_grp_chart['distributor_code'],
                        orientation='h',
                        marker_color=colors_grp,
                        text=[f"€{v:,.1f}" for v in df_grp_chart['spend_per_unit_eur']],
                        textposition='outside',
                        customdata=df_grp_chart[['total_sales_eur', 'uio_units', 'region']].values,
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Spend/Unit: €%{x:,.1f}<br>"
                            "Total Sales: €%{customdata[0]:,.0f}<br>"
                            "UIO: %{customdata[1]:,}<br>"
                            "Region: %{customdata[2]}<extra></extra>"
                        )
                    ))
                    fig6.add_vline(x=150, line_dash="dash", line_color=ISZE_BLUE, opacity=0.7)
                    fig6.update_layout(
                        height=max(300, len(df_grp_chart) * 30),
                        margin=dict(l=10, r=80, t=20, b=20),
                        xaxis_title="EUR per vehicle",
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        xaxis=dict(gridcolor='#F0F0F0'),
                    )
                    st.plotly_chart(fig6, use_container_width=True)

            st.divider()
            st.markdown("#### Regional Summary Table")
            st.dataframe(
                df_reg_agg.rename(columns={
                    'region': 'Region',
                    'total_sales_eur': 'Sales EUR',
                    'n_distributors': '# Distributors',
                }).assign(**{'Sales EUR': lambda d: d['Sales EUR'].apply(lambda x: _fmt_eur(x, 0))}),
                use_container_width=True,
                hide_index=True
            )

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 4: Part Explorer
    # ═════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Part Explorer")
        st.caption("Explore top-selling parts by distributor and year. Useful for PMS classification validation.")

        col1, col2, col3 = st.columns(3)
        with col1:
            exp_year = st.selectbox("Year", available_years, key="exp_year",
                                    index=available_years.index(selected_year))
        with col2:
            exp_dist = st.selectbox(
                "Distributor (or All)",
                ["All"] + sorted(df_sales['distributor_code'].unique().tolist()),
                key="exp_dist"
            )
        with col3:
            top_n = st.slider("Top N parts", 10, 100, 30, key="exp_n")

        dist_filter = None if exp_dist == "All" else exp_dist

        with st.spinner("Loading parts…"):
            df_parts = get_top_parts(
                df_sales, year=exp_year, year_type=year_type,
                distributor_code=dist_filter, top_n=top_n
            )

        if not df_parts.empty:
            st.markdown(f"#### Top {top_n} Parts by Revenue — {exp_dist} | {'FY' if year_type == 'fiscal' else ''}{exp_year}")

            # Registry-first classification with keyword fallback
            def _classify_hint(row):
                pn = str(row.get('part_number', '')).strip().lstrip('0')
                desc = row.get('description', '')

                # Registry lookup first (confirmed PMS PNs)
                if pn in PMS_PN_REGISTRY:
                    m = PMS_PN_REGISTRY[pn]
                    cat_label = CATEGORY_LABELS.get(m['category'], m['category'])
                    return f"✅ PMS: {cat_label} ({m['model']})"

                # Keyword fallback for non-registry parts
                if pd.isna(desc):
                    return "—"
                desc_u = str(desc).upper()
                if "OIL" in desc_u and "FILTER" in desc_u:    return "🟦 PMS: Oil Filter"
                if "AIR" in desc_u and "FILTER" in desc_u:    return "🟦 PMS: Air Filter"
                if "FUEL" in desc_u and "FILTER" in desc_u:   return "🟦 PMS: Fuel Filter"
                if "ADBLUE" in desc_u or "AD BLUE" in desc_u: return "🟦 PMS: AdBlue Filter"
                if "FILTER" in desc_u:                         return "🔷 Filter (other)"
                if "PAD" in desc_u and "BRAKE" in desc_u:     return "🟧 Wear: Brake Pad"
                if "DISC" in desc_u and "BRAKE" in desc_u:    return "🟧 Wear: Brake Disc"
                if "CLUTCH" in desc_u:                         return "🟧 Wear: Clutch"
                if "WIPER" in desc_u or "BLADE" in desc_u:    return "🟧 Wear: Wiper"
                if "BELT" in desc_u:                           return "🟧 Wear: Belt"
                return "⬜ Unclassified"

            df_parts['Category Hint'] = df_parts.apply(_classify_hint, axis=1)
            df_parts['Sales EUR'] = df_parts['total_sales_eur'].apply(lambda x: _fmt_eur(x, 0))
            df_parts['Qty'] = df_parts['total_qty'].apply(lambda x: f"{int(x):,}")
            df_parts['# Markets'] = df_parts['n_distributors']

            st.dataframe(
                df_parts.rename(columns={'part_number': 'Part Number', 'description': 'Description', 'rank': 'Rank'})[
                    ['Rank', 'Part Number', 'Description', 'Category Hint', 'Sales EUR', 'Qty', '# Markets']
                ],
                use_container_width=True,
                hide_index=True,
            )
            st.caption("✅ = confirmed PMS part number from ITUK registry (Apr 2026). Others = keyword-based hint.")
        else:
            st.info("No parts data for current selection.")

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 5: PMS Coverage
    # ═════════════════════════════════════════════════════════════════════════
    with tab5:
        st.subheader(f"PMS Coverage Analysis | {period_label}")

        # ── Section 1: Phase 1 scope notice ──────────────────────────────────
        st.info(
            "Phase 1 focus: N75 / 7.5t fleet (NPR75/4HK1 and NPR88/4JZ1). "
            "N35 shown as reference only."
        )

        # ── Compute PMS capture (cached per year/type/dist) ───────────────────
        try:
            dist_filter_pms = selected_dists[0] if len(selected_dists) == 1 else None
            pms_result = calculate_pms_capture(
                df_sales_filtered,
                year=selected_year,
                year_type=year_type,
                distributor_code=dist_filter_pms,
            )
        except Exception as e:
            st.error(f"PMS calculation error: {e}")
            st.stop()

        summary_df = pms_result['summary_df']
        has_pms_data = pms_result['total_actual_eur'] > 0

        if not has_pms_data:
            st.info(
                "No PMS part numbers found in the sales data for the current selection. "
                "Check that part_number column is populated and that the selected year has data."
            )
        else:
            # ── Section 2: KPI row ────────────────────────────────────────────
            cap_rates = pms_result['capture_rate_by_category']
            brake_cap   = cap_rates.get('brake_pad', None)
            air_cap     = cap_rates.get('air_filter', None)
            total_actual = pms_result['total_actual_eur']
            total_opp    = pms_result['total_opportunity_eur']

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

            # ── Section 3: Capture rate horizontal bar chart ──────────────────
            st.markdown("#### Capture Rate by Category")
            st.caption("Green ≥ 60% | Amber 30–60% | Red < 30%")

            phase1_rows = summary_df[summary_df['category'].isin(PHASE1_CATEGORIES)].copy()
            if not phase1_rows.empty:
                phase1_rows = phase1_rows.sort_values('capture_rate', ascending=True)
                bar_colors = []
                for v in phase1_rows['capture_rate']:
                    if v >= 0.60:   bar_colors.append('#2E7D32')
                    elif v >= 0.30: bar_colors.append('#F9A825')
                    else:           bar_colors.append('#C62828')

                annotations = [
                    f"{int(a)} / {int(e)}"
                    for a, e in zip(
                        phase1_rows['actual_qty'],
                        phase1_rows['expected_qty'],
                    )
                ]

                fig_cap = go.Figure(go.Bar(
                    x=phase1_rows['capture_rate'] * 100,
                    y=phase1_rows['category_label'],
                    orientation='h',
                    marker_color=bar_colors,
                    text=[f"{v*100:.1f}%" for v in phase1_rows['capture_rate']],
                    textposition='outside',
                    customdata=list(zip(
                        phase1_rows['actual_qty'],
                        phase1_rows['expected_qty'],
                        annotations,
                    )),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Capture rate: %{x:.1f}%<br>"
                        "Actual qty: %{customdata[0]:,.0f}<br>"
                        "Expected qty: %{customdata[1]:,.0f}<extra></extra>"
                    ),
                ))
                fig_cap.add_vline(x=60, line_dash="dash", line_color="#2E7D32",
                                  annotation_text="60% target", annotation_position="top right")
                fig_cap.add_vline(x=30, line_dash="dot", line_color="#F9A825",
                                  annotation_text="30%")
                fig_cap.update_layout(
                    height=max(280, len(phase1_rows) * 55),
                    margin=dict(l=10, r=80, t=20, b=20),
                    xaxis_title="Capture Rate (%)",
                    xaxis=dict(range=[0, 115], gridcolor='#F0F0F0'),
                    yaxis_title="",
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                )
                st.plotly_chart(fig_cap, use_container_width=True)

            st.divider()

            # ── Section 4: Opportunity table ──────────────────────────────────
            st.markdown("#### Revenue Opportunity Table")
            opp_display = summary_df[[
                'category_label', 'actual_qty', 'expected_qty',
                'capture_rate', 'avg_sp_eur', 'revenue_gap_eur',
            ]].copy()
            opp_display['capture_rate_pct'] = opp_display['capture_rate'].apply(
                lambda x: f"{x*100:.1f}%"
            )
            opp_display['avg_sp_eur_fmt']     = opp_display['avg_sp_eur'].apply(
                lambda x: _fmt_eur(x, 2) if x > 0 else "—"
            )
            opp_display['revenue_gap_eur_fmt'] = opp_display['revenue_gap_eur'].apply(
                lambda x: _fmt_eur(x, 0) if x > 0 else "—"
            )
            opp_display['actual_qty_fmt']   = opp_display['actual_qty'].apply(
                lambda x: f"{int(x):,}"
            )
            opp_display['expected_qty_fmt'] = opp_display['expected_qty'].apply(
                lambda x: f"{int(x):,}" if x > 0 else "—"
            )
            st.dataframe(
                opp_display.rename(columns={
                    'category_label':    'Category',
                    'actual_qty_fmt':    'Actual Qty',
                    'expected_qty_fmt':  'Expected Qty',
                    'capture_rate_pct':  'Capture Rate',
                    'avg_sp_eur_fmt':    'Avg SP (€)',
                    'revenue_gap_eur_fmt': 'Revenue Gap (€)',
                })[['Category', 'Actual Qty', 'Expected Qty', 'Capture Rate', 'Avg SP (€)', 'Revenue Gap (€)']],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "Expected Qty = surviving parc × services/year × addressable %. "
                "Revenue Gap = (Expected − Actual) × Avg SP. Capture capped at 100%."
            )

            st.divider()

            # ── Section 5: Distributor breakdown ─────────────────────────────
            st.markdown("#### Distributor Breakdown")
            dist_summary = get_pms_summary_by_distributor(
                df_sales_filtered, year=selected_year, year_type=year_type
            )

            if dist_summary.empty:
                st.info("No distributor-level PMS data available.")
            elif not selected_dists:
                # All distributors: stacked bar by category
                pivot_dist = dist_summary.groupby(
                    ['distributor_code', 'category_label']
                ).agg(revenue_eur=('revenue_eur', 'sum')).reset_index()

                fig_dist = px.bar(
                    pivot_dist,
                    x='distributor_code',
                    y='revenue_eur',
                    color='category_label',
                    labels={
                        'distributor_code': 'Distributor',
                        'revenue_eur': 'PMS Sales (EUR)',
                        'category_label': 'Category',
                    },
                    color_discrete_sequence=PALETTE,
                )
                fig_dist.update_layout(
                    height=420,
                    margin=dict(l=10, r=10, t=20, b=10),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    yaxis=dict(gridcolor='#F0F0F0', tickprefix='€', tickformat=',.0f'),
                    legend=dict(orientation='h', yanchor='bottom', y=-0.35),
                )
                st.plotly_chart(fig_dist, use_container_width=True)
            else:
                # Single distributor: just show the summary table
                dist_show = dist_summary[[
                    'distributor_code', 'category_label', 'model',
                    'qty', 'revenue_eur', 'avg_sp_eur',
                ]].copy()
                dist_show['revenue_eur_fmt'] = dist_show['revenue_eur'].apply(lambda x: _fmt_eur(x, 0))
                dist_show['avg_sp_eur_fmt']  = dist_show['avg_sp_eur'].apply(
                    lambda x: _fmt_eur(x, 2) if x > 0 else "—"
                )
                dist_show['qty_fmt'] = dist_show['qty'].apply(lambda x: f"{int(x):,}")
                st.dataframe(
                    dist_show.rename(columns={
                        'distributor_code': 'Distributor',
                        'category_label':   'Category',
                        'model':            'Model',
                        'qty_fmt':          'Qty',
                        'revenue_eur_fmt':  'Revenue (€)',
                        'avg_sp_eur_fmt':   'Avg SP (€)',
                    })[['Distributor', 'Category', 'Model', 'Qty', 'Revenue (€)', 'Avg SP (€)']],
                    use_container_width=True,
                    hide_index=True,
                )

        st.divider()

        # ── Section 6: ITUK incentive panel ──────────────────────────────────
        show_ituk_panel = (
            not selected_dists or
            'ITUK' in selected_dists or
            any('ITUK' in d.upper() for d in selected_dists)
        )
        if show_ituk_panel:
            st.markdown("#### ITUK Incentive Structure")
            col_tier, col_stretch = st.columns([1, 1])

            with col_tier:
                st.markdown("**Dealer Credit Tiers (PMS volume performance)**")
                tier_data = pd.DataFrame([
                    {"Target Threshold": "100% of target (baseline)",  "Dealer Credit": "£250"},
                    {"Target Threshold": "125% of target (+25% uplift)", "Dealer Credit": "£500"},
                    {"Target Threshold": "150% of target (+50% uplift)", "Dealer Credit": "£750"},
                    {"Target Threshold": "Best N75 brake conversion",    "Dealer Credit": "+£500 bonus"},
                    {"Target Threshold": "Best air filter attachment",   "Dealer Credit": "+£500 bonus"},
                ])
                st.dataframe(tier_data, use_container_width=True, hide_index=True)

            with col_stretch:
                st.markdown("**2030 Stretch Tracker — ITUK / UK Market**")
                stretch_data = pd.DataFrame([
                    {"Metric": "2025 baseline",     "Value": "£12.87M",  "Notes": "Actual FY2025"},
                    {"Metric": "2026 plan (77% UIO)", "Value": "£13.13M", "Notes": "77% UIO share target"},
                    {"Metric": "2026 stretch (80% UIO)", "Value": "£13.64M", "Notes": "Stretch target"},
                    {"Metric": "ISZE kickback pot",  "Value": "£62,052", "Notes": "Available for dealers"},
                ])
                st.dataframe(stretch_data, use_container_width=True, hide_index=True)

            # Incentive calculation (if ITUK data is present and year has data)
            if has_pms_data:
                with st.expander("Show incremental performance vs baseline"):
                    try:
                        df_incentive = calculate_ituk_incentive(
                            df_sales, year=selected_year, year_type=year_type
                        )
                        if not df_incentive.empty:
                            df_inc_display = df_incentive.copy()
                            df_inc_display['pct_of_target_fmt'] = df_inc_display['pct_of_target'].apply(
                                lambda x: f"{x*100:.1f}%"
                            )
                            df_inc_display['bonus_tier_fmt'] = df_inc_display['bonus_tier'].fillna('Below target')
                            df_inc_display['baseline_qty_fmt']   = df_inc_display['baseline_qty'].apply(
                                lambda x: f"{x:,.1f}"
                            )
                            df_inc_display['actual_qty_fmt']     = df_inc_display['actual_qty'].apply(
                                lambda x: f"{x:,.1f}"
                            )
                            df_inc_display['incremental_qty_fmt'] = df_inc_display['incremental_qty'].apply(
                                lambda x: f"{x:+,.1f}"
                            )
                            st.dataframe(
                                df_inc_display.rename(columns={
                                    'category_label':      'Category',
                                    'baseline_qty_fmt':    'Baseline Qty',
                                    'actual_qty_fmt':      'Actual Qty',
                                    'incremental_qty_fmt': 'Incremental',
                                    'pct_of_target_fmt':   '% of Target',
                                    'bonus_tier_fmt':      'Bonus Tier',
                                    'bonus_amount_gbp':    'Bonus (£)',
                                })[['Category', 'Baseline Qty', 'Actual Qty',
                                    'Incremental', '% of Target', 'Bonus Tier', 'Bonus (£)']],
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.info("No ITUK incentive data available for this period.")
                    except Exception as e:
                        st.warning(f"Incentive calc unavailable: {e}")

        st.divider()

        # ── Section 7: Marketing calendar ────────────────────────────────────
        st.markdown("#### 2026 PMS Marketing Calendar")
        current_month = datetime.now().month

        def _campaign_status(months: list) -> str:
            return "ACTIVE" if current_month in months else ""

        campaigns = [
            {
                "Quarter":    "Q2",
                "Campaign":   "Spring into Service",
                "Period":     "Apr – Jun 2026",
                "PMS Focus":  "Filters + Brakes (10–20% off)",
                "Status":     _campaign_status([4, 5, 6]),
            },
            {
                "Quarter":    "Q3",
                "Campaign":   "Parts Basket Pricing",
                "Period":     "Aug – Sep 2026",
                "PMS Focus":  "Fleet basket kits",
                "Status":     _campaign_status([8, 9]),
            },
            {
                "Quarter":    "Q3",
                "Campaign":   "Brakes & Safety",
                "Period":     "Sep – Oct 2026",
                "PMS Focus":  "Brakes + Lights",
                "Status":     _campaign_status([9, 10]),
            },
        ]
        df_campaigns = pd.DataFrame(campaigns)
        st.dataframe(df_campaigns, use_container_width=True, hide_index=True)
        st.caption("ACTIVE = campaign running in current calendar month.")

    # ═════════════════════════════════════════════════════════════════════════
    # TAB 6: Export
    # ═════════════════════════════════════════════════════════════════════════
    with tab6:
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
                    import zipfile
                    import io as _io

                    zip_buf = _io.BytesIO()
                    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr("spend_per_unit.csv", df_spu.to_csv(index=False))
                        zf.writestr("trends.csv", df_trend_exp.to_csv(index=False) if not df_trend_exp.empty else "")

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
            st.dataframe(df_raw_preview, use_container_width=True)

    # Footer
    st.markdown(
        '<div class="footer-note">ISZE GPS Dashboard — Confidential | '
        'Vehicle Parts Sales, Isuzu Motors Europe | '
        f'Data: 2022–2026 YTD | UIO Reference: 2024 | '
        f'Built: {datetime.now().strftime("%d %b %Y")}</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
