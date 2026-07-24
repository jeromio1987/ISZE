"""PRISM - Tender / R&M opportunity pipeline (from tender_data.json)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402
from modules import advanced_visuals as av  # noqa: E402


SRC = DERIVED_DIR / "tender_pipeline.csv"


@st.cache_data(show_spinner="Loading tender pipeline...")
def load() -> pd.DataFrame:
    d = pd.read_csv(SRC)
    if d["actionable"].dtype != bool:
        d["actionable"] = d["actionable"].astype(str).str.lower().isin(["true", "1"])
    return d


st.title("Tender / R&M opportunity pipeline")
st.caption("Scored public-tender opportunities — fleet R&M and parts contracts harvested from EU/UK notices.")

if not SRC.exists():
    st.error(f"Missing {SRC.name}. Run scripts/build_tender_pipeline.py first.")
    st.stop()

df = load()

total = len(df)
actionable = int(df["actionable"].sum())
parts = int(df["parts_signal"].sum())
rm = int(df["rm_contract"].sum())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Opportunities", f"{total:,}")
c2.metric("Actionable", f"{actionable:,}")
c3.metric("Carry parts signal", f"{parts / total:.0%}")
c4.metric("R&M contract", f"{rm / total:.0%}")

st.warning(
    "Qualified-pipeline view: counts and scores are real for every row, but **value is "
    "present on only 12 of 520** opportunities and deadlines on 55 — so this charts "
    "counts and scores, **not** € pipeline or award prices. Awarded line items "
    "(tenders_output.xlsx) are still empty; win/loss-vs-aftermarket pricing slots on top when they land.",
    icon="⚠️",
)

st.plotly_chart(av.fig_tender_funnel(DERIVED_DIR), use_container_width=True)
col1, col2 = st.columns(2)
col1.plotly_chart(av.fig_tender_country(DERIVED_DIR), use_container_width=True)
col2.plotly_chart(av.fig_tender_owner(DERIVED_DIR), use_container_width=True)
st.plotly_chart(av.fig_tender_scatter(DERIVED_DIR), use_container_width=True)

st.subheader("Action queue — top Attack / Selective opportunities")
queue = (
    df[df["decision"].isin(["Attack", "Selective"])]
    .sort_values("opportunity_score", ascending=False)
    .head(20)[["title", "country", "owner_suggested", "opportunity_score",
               "decision", "deadline_date", "url"]]
)
st.dataframe(
    queue,
    use_container_width=True,
    hide_index=True,
    column_config={"url": st.column_config.LinkColumn("Notice", display_text="Open ↗")},
)
