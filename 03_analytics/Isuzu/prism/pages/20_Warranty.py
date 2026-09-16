# PRISM Module 20 — Warranty Intelligence
# Warranty-parts expense per distributor, by fiscal year — the direct erosion of net GPS.

"""
PRISM — Module 20: Warranty Intelligence

Warranty parts claims are billed revenue that never becomes retained gross:
net GPS = gross parts billing − warranty expense (see 01_data/06_Warranty/…).
This page surfaces the warranty line per distributor and fiscal year.
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

from config import DERIVED_DIR, data_freshness_date  # noqa: E402
from modules.plotly_style import style

WARRANTY_CSV = DERIVED_DIR / "distributor_warranty_expense_fiscal.csv"

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
FY_COLS = ["warr_FY2024", "warr_FY2025", "warr_FY2026"]


def _fmt_eur(v, decimals=0):
    if pd.isna(v):
        return "—"
    return f"€{v:,.{decimals}f}"


@st.cache_data(show_spinner="Loading warranty expense…")
def _load_warranty() -> pd.DataFrame:
    if not WARRANTY_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(WARRANTY_CSV)
    for c in FY_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


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
    <h1>🛡️ Warranty Intelligence</h1>
    <p>Warranty-parts expense per distributor, by fiscal year (Apr–Mar). This is the line that turns gross parts billing into retained net GPS.</p>
</div>
""", unsafe_allow_html=True)

df = _load_warranty()

if df.empty:
    st.info(
        f"Warranty expense file not found: `{WARRANTY_CSV.name}`.\n\n"
        "Rebuild with `python 01_data/91_build/build_warranty_canonical.py`.",
        icon="📂",
    )
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Filters")
    show_midi = st.toggle("Include MIDI (non-GPS channel)", value=False,
                          help="MIDI is a non-GPS channel — exclude from network totals by default.")
    selected_fy = st.radio(
        "Focus year",
        ["FY2026", "FY2025", "FY2024"],
        index=0,
        help="ISZE fiscal year runs Apr–Mar. FY2026 = Apr 2025 – Mar 2026.",
    )
    st.divider()
    st.caption(f"📅 Source: `{WARRANTY_CSV.name}`")
    st.caption("💰 JPY→EUR at 163.7 (UMI/MIDI lines)")
    st.caption(f"🔄 Built: {data_freshness_date()}")

focus_col = "warr_" + selected_fy

view = df.copy()
if not show_midi:
    view = view[view["db"] != "MIDI"]

# ── KPI row ───────────────────────────────────────────────────────────────────
tot = {fy: float(view[col].sum()) for fy, col in zip(["FY2024", "FY2025", "FY2026"], FY_COLS)}
focus_total = tot[selected_fy]
top_db = view.sort_values(focus_col, ascending=False).iloc[0] if len(view) else None
median_warr = float(view[focus_col].median()) if len(view) else 0.0
above_median = view[view[focus_col] > median_warr].sort_values(focus_col, ascending=False)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric(f"Network warranty · {selected_fy}", _fmt_eur(focus_total, 0))
with k2:
    st.metric("FY2024 → FY2025 → FY2026",
              " · ".join(_fmt_eur(tot[k], 0) for k in ["FY2024", "FY2025", "FY2026"]))
with k3:
    st.metric("Distributors", f"{len(view)}")
with k4:
    st.metric("Top exposure", f"{top_db['db']} — {_fmt_eur(top_db[focus_col], 0)}"
              if top_db is not None else "—")

st.divider()

# ── Trend by fiscal year ───────────────────────────────────────────────────────
st.markdown("#### Warranty expense trend (fiscal year)")
melt = view.melt(id_vars=["db"], value_vars=FY_COLS, var_name="fy", value_name="expense")
melt["fy"] = melt["fy"].str.replace("warr_", "")
try:
    fig_trend = px.bar(
        melt.sort_values("fy"),
        x="db", y="expense", color="fy", barmode="group",
        color_discrete_sequence=[ISZE_BLUE, "#8FA9C9", ISZE_ORANGE],
        labels={"db": "Distributor", "expense": "Warranty expense (€)", "fy": "Fiscal year"},
    )
    fig_trend.update_layout(
        height=420, margin=dict(l=10, r=10, t=20, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(gridcolor="#F0F0F0", tickprefix="€", tickformat=",.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35),
    )
    st.plotly_chart(style(fig_trend), width="stretch")
except Exception as e:
    st.warning(f"Trend chart unavailable: {e}")

st.divider()

# ── Focus-year ranking ────────────────────────────────────────────────────────
st.markdown(f"#### {selected_fy} — warranty expense by distributor")
rank = view.sort_values(focus_col, ascending=True).copy()
try:
    fig_rank = go.Figure(go.Bar(
        x=rank[focus_col],
        y=rank["db"],
        orientation="h",
        marker_color=[ISZE_ORANGE if r["db"] == (top_db["db"] if top_db is not None else "") else ISZE_BLUE for _, r in rank.iterrows()],
        text=[_fmt_eur(v, 0) for v in rank[focus_col]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} €<extra></extra>",
    ))
    fig_rank.update_layout(
        height=max(360, len(rank) * 26), margin=dict(l=10, r=90, t=10, b=20),
        xaxis_title="Warranty expense (€)", xaxis=dict(gridcolor="#F0F0F0", tickprefix="€", tickformat=",.0f"),
        yaxis_title="", plot_bgcolor="white", paper_bgcolor="white",
    )
    fig_rank.add_vline(
        x=median_warr, line_dash="dash", line_color="#94A3B8",
        annotation_text="network median", annotation_position="top",
    )
    st.plotly_chart(style(fig_rank), width="stretch")
    st.caption(
        f"Benchmark: network median warranty ({selected_fy}) = {_fmt_eur(median_warr, 0)}. "
        "Flag distributors above the network median warranty € — challenge the claim."
        + (
            f" Above median: {', '.join(str(r['db']) for _, r in above_median.iterrows())}."
            if len(above_median) else ""
        )
    )
except Exception as e:
    st.warning(f"Ranking chart unavailable: {e}")

st.divider()

# ── Table ─────────────────────────────────────────────────────────────────────
st.markdown("#### Full table (fiscal years)")
tbl = view.sort_values("warr_FY2026", ascending=False).copy()
for c in FY_COLS:
    tbl[c] = tbl[c].apply(lambda v: _fmt_eur(v, 0))
st.dataframe(
    tbl.rename(columns={
        "db": "Distributor",
        "warr_FY2024": "FY2024 (€)",
        "warr_FY2025": "FY2025 (€)",
        "warr_FY2026": "FY2026 (€)",
        "note": "Note",
    })[["Distributor", "FY2024 (€)", "FY2025 (€)", "FY2026 (€)", "Note"]],
    width="stretch", hide_index=True,
)
st.caption(
    "Name map: **RSA** = Norway distributor · **Greece** = Petros Petropoulos. "
    "MIDI is a non-GPS channel (excluded from totals above unless toggled)."
)

# ── Context ───────────────────────────────────────────────────────────────────
with st.expander("How this feeds net GPS"):
    st.markdown(
        "Net GPS billing = **gross parts billing − warranty expense** for that DB and fiscal year "
        "(see `01_data/06_Warranty/DISTRIBUTOR_WARRANTY_EXPENSE.md`). Warranty parts are still "
        "billed revenue, but they are returned against the distributor — so a rising warranty line "
        "erodes retained gross even while headline GPS looks flat. This page isolates that line so "
        "it can be tracked and challenged per distributor."
    )

st.markdown(
    '<div class="footer-note">PRISM Warranty Intelligence | Module 20 | '
    'Source: distributor_warranty_expense_fiscal.csv | Method: 01_data/06_Warranty/DISTRIBUTOR_WARRANTY_EXPENSE.md</div>',
    unsafe_allow_html=True,
)
