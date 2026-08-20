# PRISM Module 21 — Price Realization / Pocket explorer
# List price → billed (pocket) by distributor & year, plus ZPR1 vs PR00 channel gap.

"""
PRISM — Module 21: Price Realization

How much of list price survives to the pocket: realization = billed ÷ list value.
Net-only (gross/SPA/condition are closed — see FACTS.md). Also shows the ZPR1
(dealer-channel) vs PR00 (list) gap per payer, and the no-list coverage blind spot.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR, data_freshness_date, is_internal_mode  # noqa: E402
from modules.plotly_style import style

REALIZATION_NETWORK_CSV = DERIVED_DIR / "pr00_realization_network_cy.csv"
REALIZATION_BY_DB_CSV = DERIVED_DIR / "pr00_realization_by_db_cy.csv"
ZPR1_VS_PR00_CSV = DERIVED_DIR / "zpr1_vs_pr00_by_payer_year.csv"

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"


def _fmt_eur(v, decimals=0):
    if pd.isna(v):
        return "—"
    return f"€{v:,.{decimals}f}"


def _pct(v, decimals=1):
    if pd.isna(v):
        return "—"
    return f"{v:.{decimals}f}%"


@st.cache_data(show_spinner="Loading realization data…")
def _load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    net = pd.read_csv(REALIZATION_NETWORK_CSV) if REALIZATION_NETWORK_CSV.exists() else pd.DataFrame()
    by_db = pd.read_csv(REALIZATION_BY_DB_CSV) if REALIZATION_BY_DB_CSV.exists() else pd.DataFrame()
    zpr1 = pd.read_csv(ZPR1_VS_PR00_CSV) if ZPR1_VS_PR00_CSV.exists() else pd.DataFrame()
    return net, by_db, zpr1


# ── Brand CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; --isze-light: #D6E4F0; }
    .main-header { background: linear-gradient(90deg, #1B3A6B 0%, #2C5AA0 100%);
        padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1rem; }
    .main-header h1 { color: white !important; margin: 0; font-size: 1.6rem; }
    .main-header p { color: #D6E4F0; margin: 0.2rem 0 0; font-size: 0.85rem; }
    div[data-testid="metric-container"] { border: 1px solid #E0E0E0;
        border-left: 4px solid #1B3A6B; border-radius: 6px; padding: 0.5rem 0.8rem; }
    [data-testid="stMetricValue"] { color: #1B3A6B; }
    .footer-note { font-size: 0.72rem; color: #999; padding-top: 1rem;
        border-top: 1px solid #EEE; margin-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>💶 Price Realization — list to pocket</h1>
    <p>How much of the PR00 list price survives to the pocket (billed ÷ list), per distributor and year — and where the ZPR1 dealer channel sits below list.</p>
</div>
""", unsafe_allow_html=True)

if not is_internal_mode():
    st.warning(
        "INTERNAL ONLY — this page reveals ISZE discounting (list→pocket) and the "
        "ZPR1 dealer-channel margin. Not shown in the MD-safe launcher.",
        icon="🔒",
    )

net, by_db, zpr1 = _load()

if net.empty and by_db.empty:
    st.info(
        f"Realization files not found under `{DERIVED_DIR}`.\n\n"
        "Run the pricing realization build before viewing.",
        icon="📂",
    )
    st.stop()

# ── Integrity banner ──────────────────────────────────────────────────────────
status = net["status"].iloc[0] if not net.empty and "status" in net else "—"
st.warning(
    f"Data integrity: **{status}** — realization is list-vs-billed on **net** sales "
    "(gross / SPA / condition are not available on the billing extract — closed 2026-08-11). "
    "Read as directional until QA is signed.",
    icon="⚠️",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Filters")
    years = []
    if not by_db.empty:
        years = sorted(by_db["year"].dropna().unique().astype(int).tolist())
    if years:
        selected_year = st.selectbox("Year", years, index=len(years) - 1)
    else:
        selected_year = None
    st.divider()
    st.caption(f"📅 Source: pr00_realization_*.csv, zpr1_vs_pr00_by_payer_year.csv")
    st.caption(f"🔄 Built: {data_freshness_date()}")

# ── KPI row (network) ─────────────────────────────────────────────────────────
if not net.empty:
    latest = net.iloc[-1]
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Realization (latest)", _pct(latest.get("realization_pct")))
    with k2:
        st.metric("PR00 coverage", _pct(latest.get("coverage_pct")))
    with k3:
        st.metric("No-list € (blind spot)", _fmt_eur(latest.get("no_list_eur"), 0))
    with k4:
        st.metric("Period", str(latest.get("year")) + " " + str(latest.get("period", "")))
    st.divider()

# ── Network trend ─────────────────────────────────────────────────────────────
if not net.empty:
    st.markdown("#### Network realization & coverage (calendar year)")
    try:
        trend = net.copy()
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend["year"], y=trend["realization_pct"], name="Realization %",
            mode="lines+markers", line=dict(color=ISZE_BLUE, width=3),
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend["year"], y=trend["coverage_pct"], name="PR00 coverage %",
            mode="lines+markers", line=dict(color=ISZE_ORANGE, width=2, dash="dash"),
        ))
        fig_trend.update_layout(
            height=340, margin=dict(l=10, r=10, t=20, b=20),
            xaxis_title="Year", yaxis_title="%",
            yaxis=dict(gridcolor="#F0F0F0"),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        )
        st.plotly_chart(style(fig_trend), width="stretch")
    except Exception as e:
        st.warning(f"Trend chart unavailable: {e}")
    st.divider()

# ── DB realization (focus year) ───────────────────────────────────────────────
if not by_db.empty and selected_year is not None:
    st.markdown(f"#### Realization by distributor — {selected_year}")
    dby = by_db[by_db["year"] == selected_year].sort_values("realization_pct", ascending=True).copy()
    try:
        fig_db = go.Figure(go.Bar(
            x=dby["realization_pct"], y=dby["db"], orientation="h",
            marker_color=[ISZE_ORANGE if v < 90 else ISZE_BLUE for v in dby["realization_pct"]],
            text=[f"{v:.1f}%" for v in dby["realization_pct"]],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>Realization: %{x:.1f}%<br>"
                "No-list €: %{customdata[0]:,.0f}<br>Coverage: %{customdata[1]:.1f}%<extra></extra>"
            ),
            customdata=list(zip(dby["no_list_eur"], dby["coverage_pct"])),
        ))
        fig_db.add_vline(x=100, line_dash="dot", line_color="#999",
                         annotation_text="list = pocket", annotation_position="top right")
        fig_db.update_layout(
            height=max(400, len(dby) * 24), margin=dict(l=10, r=90, t=10, b=20),
            xaxis_title="Realization % (billed ÷ list value)",
            xaxis=dict(gridcolor="#F0F0F0"),
            yaxis_title="", plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(style(fig_db), width="stretch")
        st.caption("Orange = realization below 90% (pocket erosion). Realization >100% = billed above list (data/currency timing).")
    except Exception as e:
        st.warning(f"DB chart unavailable: {e}")

    st.markdown("#### Table — realization & coverage")
    t = dby.sort_values("realization_pct").copy()
    t["parts_eur"] = t["parts_eur"].apply(_fmt_eur)
    t["no_list_eur"] = t["no_list_eur"].apply(_fmt_eur)
    t["coverage_pct"] = t["coverage_pct"].apply(_pct)
    t["realization_pct"] = t["realization_pct"].apply(_pct)
    st.dataframe(
        t.rename(columns={
            "db": "Distributor", "parts_eur": "Parts €", "no_list_eur": "No-list €",
            "coverage_pct": "Coverage", "realization_pct": "Realization",
        })[["Distributor", "Parts €", "No-list €", "Coverage", "Realization"]],
        width="stretch", hide_index=True,
    )
    st.divider()

# ── ZPR1 vs PR00 channel gap ──────────────────────────────────────────────────
if not zpr1.empty:
    st.markdown("#### ZPR1 (dealer-channel price) vs PR00 (list price) — median gap by payer")
    st.caption(
        "PR00 = **list price** · ZPR1 = **dealer-channel price**. "
        "Payers: **UTI** (code 1799) ≠ **UMI** (code 1797) — never blended; "
        "**2372** is a separate, standalone payer."
    )
    try:
        zp = zpr1.sort_values(["year", "payer"]).copy()
        fig_z = px.bar(
            zp, x="payer", y="median_zpr1_vs_pr00_pct", color="year", barmode="group",
            color_discrete_sequence=[ISZE_BLUE, "#8FA9C9", ISZE_ORANGE, "#F4A460"],
            labels={"payer": "Payer", "median_zpr1_vs_pr00_pct": "Median gap vs PR00 (%)", "year": "Year"},
        )
        fig_z.update_layout(
            height=360, margin=dict(l=10, r=10, t=20, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(gridcolor="#F0F0F0", ticksuffix="%"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        )
        st.plotly_chart(style(fig_z), width="stretch")
        st.caption("Negative % = ZPR1 dealer price sits below PR00 list. A deepening gap is discount/condition pressure, not mix.")
    except Exception as e:
        st.warning(f"ZPR1 chart unavailable: {e}")

st.markdown(
    '<div class="footer-note">PRISM Price Realization | Module 21 | '
    'Net-only (gross/SPA closed) | Sources: pr00_realization_*.csv, zpr1_vs_pr00_by_payer_year.csv</div>',
    unsafe_allow_html=True,
)
