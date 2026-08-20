"""PRISM — Distributor Performance Scorecard PDF generator."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from modules.bvp_dashboard_data import load_bvp_bundle  # noqa: E402
from modules.scorecard_pdf import build_scorecard  # noqa: E402


st.markdown(
    """
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .scorecard-hero {
        background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.25rem;
    }
    .scorecard-hero h1 { color: #fff !important; margin: 0; font-size: 1.75rem; font-weight: 700; }
    .scorecard-hero p  { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
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
<div class="scorecard-hero">
  <h1>Distributor Scorecard</h1>
  <p>Generate a PDF performance scorecard for any distributor</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading data bundle…")
def _load():
    return load_bvp_bundle()


bundle = _load()
gps_db = bundle.get("gps_db", pd.DataFrame())
network_percentile = bundle.get("network_percentile", pd.DataFrame())
capture_recovery = bundle.get("capture_recovery", pd.DataFrame())

if gps_db.empty:
    st.warning(
        "GPS data not loaded. Run `python scripts/build_strategic_contracts.py` to build "
        "the derived CSVs, then reload this page."
    )
    st.stop()

dists_avail = sorted(gps_db["distributor_code"].dropna().unique().tolist())
years_avail = sorted(gps_db["year"].dropna().astype(int).unique().tolist())

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Scorecard controls")

    default_dist = "ITUK" if "ITUK" in dists_avail else (dists_avail[0] if dists_avail else None)
    if not dists_avail:
        st.error("No distributors found in GPS data.")
        st.stop()

    dist_sel = st.selectbox(
        "Distributor",
        options=dists_avail,
        index=dists_avail.index(default_dist) if default_dist in dists_avail else 0,
    )

    default_year = years_avail[-1] if years_avail else None
    year_sel = st.selectbox(
        "Data year",
        options=years_avail,
        index=len(years_avail) - 1 if years_avail else 0,
    )

# ---------------------------------------------------------------------------
# Network at a glance (MD view — all markets, selected year)
# ---------------------------------------------------------------------------
st.subheader(f"Network at a glance — {year_sel}")

net = gps_db[(gps_db["year"] == year_sel) & gps_db["spend_per_unit_eur"].notna()].copy()
if not net.empty:
    net["label"] = net["country"].fillna(net["distributor_code"])
    tot_sales = net["total_sales_eur"].sum()
    uio_sum = net["uio_units"].sum()
    avg_spu = (tot_sales / uio_sum) if uio_sum else None
    best = net.loc[net["spend_per_unit_eur"].idxmax()]
    net_recovery = None
    if not capture_recovery.empty and "gap_revenue_at_genuine" in capture_recovery.columns:
        rec_yr = capture_recovery[capture_recovery["year"] == year_sel]
        net_recovery = rec_yr["gap_revenue_at_genuine"].sum() if not rec_yr.empty else None

    n1, n2, n3, n4 = st.columns(4)
    n1.metric("Network sales", f"€{tot_sales/1e6:.1f}M")
    n2.metric("Avg genuine spend / truck", f"€{avg_spu:,.0f}" if avg_spu else "—",
              help="Network genuine parts revenue ÷ total UIO")
    n3.metric("Best market", f"€{best['spend_per_unit_eur']:,.0f}/truck", help=best["label"])
    n4.metric("Recovery opportunity", f"€{net_recovery/1e6:.1f}M" if net_recovery else "—",
              help="Total PMS capture gap valued at genuine ASP, this year")

    tl = {"green": "#1a9e5f", "amber": "#E87722", "yellow": "#E8B722", "red": "#E3001B"}
    nb = net.sort_values("spend_per_unit_eur")
    fig_net = go.Figure(
        go.Bar(
            x=nb["spend_per_unit_eur"], y=nb["label"], orientation="h",
            marker_color=[tl.get(str(t), "#1B3A6B") for t in nb["traffic_light"]],
            text=[f"€{v:,.0f}" for v in nb["spend_per_unit_eur"]], textposition="outside",
        )
    )
    fig_net.update_layout(
        title=f"Genuine parts spend per truck (€ / vehicle in operation) — {year_sel}",
        template="plotly_white", font=dict(family="Segoe UI"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFC",
        height=max(360, 26 * len(nb)), margin=dict(l=10, r=40, t=46, b=20),
        xaxis_title="€ per truck", yaxis_title="",
    )
    st.plotly_chart(fig_net, width="stretch")
    st.caption(
        "How much genuine-parts revenue each market generates per truck on the road. "
        "Colour = performance traffic light. The recovery opportunity is what closing the "
        "PMS capture gap would add at genuine prices — the size of the prize."
    )

st.divider()

# ---------------------------------------------------------------------------
# Selected distributor detail + PDF export
# ---------------------------------------------------------------------------
st.subheader(f"Distributor detail — {dist_sel} · {year_sel}")

gps_row = gps_db[
    (gps_db["distributor_code"] == dist_sel) & (gps_db["year"] == year_sel)
]

gps_spu = None
if not gps_row.empty and "spend_per_unit_eur" in gps_row.columns:
    v = gps_row.iloc[0]["spend_per_unit_eur"]
    gps_spu = None if (isinstance(v, float) and math.isnan(v)) else v

pms_total_capture = None
if not network_percentile.empty:
    np_row = network_percentile[
        (network_percentile["distributor_code"] == dist_sel)
        & (network_percentile["year"] == year_sel)
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
# PDF generation
# ---------------------------------------------------------------------------
st.subheader(f"Generate scorecard for {dist_sel} — {year_sel}")

# Clear cached PDF when distributor or year changes
cache_key = f"{dist_sel}_{year_sel}"
if st.session_state.get("scorecard_key") != cache_key:
    st.session_state.pop("scorecard_pdf", None)
    st.session_state["scorecard_key"] = cache_key

if st.button("Generate Scorecard PDF", type="primary"):
    with st.spinner(f"Building scorecard for {dist_sel}…"):
        try:
            pdf_buf = build_scorecard(dist_sel, bundle, int(year_sel))
            st.session_state["scorecard_pdf"] = pdf_buf.getvalue()
        except Exception as exc:
            st.error(f"PDF generation failed: {exc}")

if "scorecard_pdf" in st.session_state:
    st.download_button(
        label=f"⬇ Download ISZE_Scorecard_{dist_sel}_{year_sel}.pdf",
        data=st.session_state["scorecard_pdf"],
        file_name=f"ISZE_Scorecard_{dist_sel}_{year_sel}.pdf",
        mime="application/pdf",
        type="primary",
    )
    st.success("Scorecard ready.")
