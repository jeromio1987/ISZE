"""PRISM — Distributor Review Pack page."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from modules.bvp_dashboard_data import load_bvp_bundle  # noqa: E402
from modules.scorecard_pdf import build_scorecard  # noqa: E402
from modules.review_pack_pdf import build_review_pack  # noqa: E402


ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"

st.markdown(
    """
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .pack-hero {
        background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.25rem;
    }
    .pack-hero h1 { color: #fff !important; margin: 0; font-size: 1.75rem; font-weight: 700; }
    .pack-hero p  { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
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
<div class="pack-hero">
  <h1>Distributor Review Pack</h1>
  <p>Full pre-meeting document — scorecard + trends + AIM + substitution</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading data bundle…")
def _load():
    return load_bvp_bundle()


bundle = _load()
gps_db: pd.DataFrame = bundle.get("gps_db", pd.DataFrame())
network_percentile: pd.DataFrame = bundle.get("network_percentile", pd.DataFrame())
capture_recovery: pd.DataFrame = bundle.get("capture_recovery", pd.DataFrame())

if gps_db.empty:
    st.warning(
        "GPS data not loaded. Run `python scripts/build_strategic_contracts.py` to build "
        "derived CSVs, then reload this page."
    )
    st.stop()

dists_avail = sorted(gps_db["distributor_code"].dropna().unique().tolist())
years_avail = sorted(gps_db["year"].dropna().astype(int).unique().tolist())

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Review Pack controls")

    default_dist = "ITUK" if "ITUK" in dists_avail else (dists_avail[0] if dists_avail else None)
    if not dists_avail:
        st.error("No distributors found in GPS data.")
        st.stop()

    dist_sel = st.selectbox(
        "Distributor",
        options=dists_avail,
        index=dists_avail.index(default_dist) if default_dist in dists_avail else 0,
    )

    default_years = years_avail[-3:] if len(years_avail) >= 3 else years_avail
    years_sel = st.multiselect(
        "Year range",
        options=years_avail,
        default=default_years,
        help="Select up to 3 years for trend analysis",
    )
    if not years_sel:
        years_sel = default_years

    years_sel = sorted([int(y) for y in years_sel])
    latest_year = years_sel[-1]

# ---------------------------------------------------------------------------
# Preview metrics
# ---------------------------------------------------------------------------
gps_row = gps_db[
    (gps_db["distributor_code"] == dist_sel) & (gps_db["year"] == latest_year)
]

gps_spu = None
if not gps_row.empty and "spend_per_unit_eur" in gps_row.columns:
    v = gps_row.iloc[0]["spend_per_unit_eur"]
    gps_spu = None if (isinstance(v, float) and math.isnan(v)) else v

pms_total_capture = None
if not network_percentile.empty:
    np_row = network_percentile[
        (network_percentile["distributor_code"] == dist_sel)
        & (network_percentile["year"] == latest_year)
        & (network_percentile["metric"] == "total_capture")
    ]
    if not np_row.empty:
        v = np_row.iloc[0].get("raw_value", None)
        pms_total_capture = None if (v is None or (isinstance(v, float) and math.isnan(v))) else v

recovery_gap = None
if not capture_recovery.empty:
    rec_df = capture_recovery[capture_recovery["distributor_code"] == dist_sel]
    if not rec_df.empty and "gap_revenue_at_genuine" in rec_df.columns:
        recovery_gap = rec_df["gap_revenue_at_genuine"].sum()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "GPS/SPU",
        f"€{int(round(gps_spu)):,}" if gps_spu is not None else "—",
        help="Genuine Parts Spend per Unit in Operation (€)",
    )

with col2:
    st.metric(
        "PMS Total Capture",
        f"{pms_total_capture * 100:.1f}%" if pms_total_capture is not None else "—",
        help="Total PMS capture rate for latest year",
    )

with col3:
    st.metric(
        "Recovery Opportunity",
        f"€{int(round(recovery_gap)):,}" if recovery_gap is not None else "—",
        help="Total gap at genuine ASP across all categories",
    )

st.divider()

# ---------------------------------------------------------------------------
# PDF generation — two buttons side by side
# ---------------------------------------------------------------------------
years_label = f"{years_sel[0]}-{years_sel[-1]}" if len(years_sel) > 1 else str(years_sel[0])
st.subheader(f"Generate documents for {dist_sel} — {years_label}")

# Session-state cache keys
scorecard_cache_key = f"{dist_sel}_{latest_year}"
pack_cache_key = f"{dist_sel}_{years_sel}"

# Clear cached PDFs when selection changes
if st.session_state.get("scorecard_key") != scorecard_cache_key:
    st.session_state.pop("scorecard_pdf", None)
    st.session_state["scorecard_key"] = scorecard_cache_key

if st.session_state.get("pack_key") != str(pack_cache_key):
    st.session_state.pop("pack_pdf", None)
    st.session_state["pack_key"] = str(pack_cache_key)

btn_col1, btn_col2 = st.columns(2)

with btn_col1:
    if st.button("Generate Scorecard (5 pages)", type="primary"):
        with st.spinner(f"Building scorecard for {dist_sel}…"):
            try:
                pdf_buf = build_scorecard(dist_sel, bundle, latest_year)
                st.session_state["scorecard_pdf"] = pdf_buf.getvalue()
            except Exception as exc:
                st.error(f"Scorecard generation failed: {exc}")

    if "scorecard_pdf" in st.session_state:
        scorecard_filename = f"ISZE_Scorecard_{dist_sel}_{latest_year}.pdf"
        st.download_button(
            label=f"Download {scorecard_filename}",
            data=st.session_state["scorecard_pdf"],
            file_name=scorecard_filename,
            mime="application/pdf",
            type="primary",
        )
        st.success("Scorecard ready.")

with btn_col2:
    if st.button("Generate Review Pack (full)", type="secondary"):
        with st.spinner(f"Building review pack for {dist_sel}…"):
            try:
                pdf_buf = build_review_pack(dist_sel, bundle, years_sel)
                st.session_state["pack_pdf"] = pdf_buf.getvalue()
            except Exception as exc:
                st.error(f"Review pack generation failed: {exc}")

    if "pack_pdf" in st.session_state:
        pack_filename = f"ISZE_ReviewPack_{dist_sel}_{years_label}.pdf"
        st.download_button(
            label=f"Download {pack_filename}",
            data=st.session_state["pack_pdf"],
            file_name=pack_filename,
            mime="application/pdf",
            type="secondary",
        )
        st.success("Review pack ready.")
