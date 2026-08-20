# PRISM Module 24 — VPACC execution tracker
# FY2027 VPACC action plan: 121 actions across VP / ACC streams, progress + PIC + deadlines.

"""
PRISM — Module 24: VPACC execution tracker

The FY2027 VPACC action plan (July update): who owns what, and is it moving.
Two streams (VP / ACC). Progress is a plain status field, NOT a scored KPI.
A light monthly "TTL parts amount" trend is shown from the legacy orders block,
labelled as such (sheet_name_is_legacy_misnomer).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR, data_freshness_date  # noqa: E402
from modules.plotly_style import style

ACTION_PARQUET = DERIVED_DIR / "vpacc_fy2027_action_plan_july.parquet"
BLOCK_PARQUET = DERIVED_DIR / "vpacc_fy2027_monthly_db_block.parquet"

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"

STATUS_ORDER = ["started_and_in_progress", "started", "plan_made", "not_started_or_blank"]


@st.cache_data(show_spinner="Loading VPACC action plan…")
def _load_action() -> pd.DataFrame:
    if not ACTION_PARQUET.exists():
        return pd.DataFrame()
    df = pd.read_parquet(ACTION_PARQUET)
    df["pic"] = df["pic"].fillna("(unassigned)")
    df["progress_status"] = df["progress_status"].fillna("(blank)")
    return df


@st.cache_data(show_spinner="Loading VPACC orders block…")
def _load_block() -> pd.DataFrame:
    if not BLOCK_PARQUET.exists():
        return pd.DataFrame()
    df = pd.read_parquet(BLOCK_PARQUET)
    df["month_num"] = pd.to_numeric(df["month_num"], errors="coerce")
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
    <h1>🗂️ VPACC Execution Tracker</h1>
    <p>FY2027 VPACC action plan — who owns what, and is it moving. Progress is a plain status field, not a scored KPI.</p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "**VPACC** = Vehicle Parts & Accessories action plan (VP = Vehicle Parts · ACC = Accessories). "
    "**PIC** = person in charge (the named owner of each action)."
)

ap = _load_action()

if ap.empty:
    st.info(
        f"Action-plan parquet not found: `{ACTION_PARQUET.name}`.\n\n"
        "Rebuild with `python 01_data/91_build/build_vpacc_fy2027_action_plan.py`.",
        icon="📂",
    )
    st.stop()

st.warning(
    "Action plan is the **July update** (`update_month = July`). Progress values are draft "
    "statuses (plan_made / started / not_started_or_blank), not a scored KPI. The monthly orders "
    "block below is a legacy sheet (`sheet_name_is_legacy_misnomer`) — treat the parts-total line as directional.",
    icon="⚠️",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Filters")
    streams = ["All streams"] + sorted(ap["stream"].dropna().unique().tolist())
    selected_stream = st.selectbox("Stream", streams)
    st.divider()
    st.caption(f"📅 Source: `{ACTION_PARQUET.name}` (July)")
    st.caption(f"🔄 Built: {data_freshness_date()}")

view = ap.copy()
if selected_stream != "All streams":
    view = view[view["stream"] == selected_stream]

# ── KPI row ───────────────────────────────────────────────────────────────────
n = len(view)
started = int(view["progress_status"].isin(["started", "started_and_in_progress"]).sum())
n_pic = view["pic"].nunique()
n_deadline = int(view["deadline"].notna().sum()) if "deadline" in view else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Actions", f"{n}")
with k2:
    st.metric("Started / in-progress", f"{started} ({started / n * 100:.0f}%)" if n else "—")
with k3:
    st.metric("Owners (PIC)", f"{n_pic}")
with k4:
    st.metric("With period set", f"{n_deadline}")

st.divider()

# ── Status by stream ──────────────────────────────────────────────────────────
st.markdown("#### Progress status by stream")
try:
    pivot = (
        view.groupby(["stream", "progress_status"], dropna=False)
        .size().reset_index(name="count")
    )
    if not pivot.empty:
        fig = px.bar(
            pivot, x="stream", y="count", color="progress_status",
            color_discrete_sequence=[ISZE_BLUE, "#4A90D9", "#8FA9C9", ISZE_ORANGE],
            labels={"stream": "Stream", "count": "Actions", "progress_status": "Status"},
            category_orders={"progress_status": STATUS_ORDER},
        )
        fig.update_layout(
            height=360, margin=dict(l=10, r=10, t=20, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(gridcolor="#F0F0F0"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        )
        st.plotly_chart(style(fig), width="stretch")
except Exception as e:
    st.warning(f"Status chart unavailable: {e}")

st.divider()

# ── PIC workload ──────────────────────────────────────────────────────────────
st.markdown("#### Actions by owner (PIC)")
try:
    pic = view["pic"].value_counts().head(15).reset_index()
    pic.columns = ["pic", "count"]
    fig_pic = px.bar(
        pic.sort_values("count"), x="count", y="pic", orientation="h",
        color_discrete_sequence=[ISZE_BLUE],
        labels={"count": "Actions", "pic": "Owner"},
    )
    fig_pic.update_layout(
        height=max(320, len(pic) * 24), margin=dict(l=10, r=10, t=10, b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(gridcolor="#F0F0F0"),
    )
    st.plotly_chart(style(fig_pic), width="stretch")
except Exception as e:
    st.warning(f"PIC chart unavailable: {e}")

st.divider()

# ── Action table ──────────────────────────────────────────────────────────────
st.markdown("#### Action plan")
cols = ["stream", "objective", "action_point", "pic", "deadline", "progress_status"]
tbl_cols = [c for c in cols if c in view.columns]
tbl = view[tbl_cols].copy()
st.dataframe(
    tbl.rename(columns={
        "stream": "Stream", "objective": "Objective", "action_point": "Action",
        "pic": "Owner", "deadline": "Period", "progress_status": "Status",
    }),
    width="stretch", hide_index=True, height=480,
)

st.divider()

# ── Monthly parts-total trend (legacy block) ─────────────────────────────────
blk = _load_block()
if not blk.empty:
    st.markdown("#### Monthly parts total (legacy orders block)")
    ttl = blk[blk["db"] == "TTL parts amount"].sort_values("month_num").copy()
    if not ttl.empty:
        try:
            fig_ttl = px.line(
                ttl, x="month", y="value_eur", markers=True,
                color_discrete_sequence=[ISZE_ORANGE],
                labels={"month": "Month", "value_eur": "Parts total (€)"},
            )
            fig_ttl.update_layout(
                height=320, margin=dict(l=10, r=10, t=20, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
                yaxis=dict(gridcolor="#F0F0F0", tickprefix="€", tickformat=",.0f"),
            )
            st.plotly_chart(style(fig_ttl), width="stretch")
            st.caption(
                "Source sheet is a legacy misnomer (`source_sheet = 2018`, `year_label_missing` on most rows). "
                "Read as directional monthly parts volume, not an audited € figure."
            )
        except Exception as e:
            st.warning(f"Parts-total chart unavailable: {e}")

st.markdown(
    '<div class="footer-note">PRISM VPACC Tracker | Module 24 | '
    'Source: vpacc_fy2027_action_plan_july.parquet (July update) · vpacc_fy2027_monthly_db_block.parquet (legacy)</div>',
    unsafe_allow_html=True,
)
