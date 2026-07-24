"""PRISM - Per-distributor parts mix (genuine / contested / BVP)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402


ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
BVP_RED = "#E2231A"
SRC = DERIVED_DIR / "db_parts_mix_classification.csv"

BUCKET_COLORS = {
    "BVP": BVP_RED,
    "Genuine (contested)": ISZE_ORANGE,
    "Genuine only": ISZE_BLUE,
}


@st.cache_data(show_spinner="Loading classification...")
def load_mix() -> pd.DataFrame:
    return pd.read_csv(SRC)


st.title("Per-distributor parts mix")
st.caption(
    "Genuine / contested / BVP split of total parts revenue. "
    "Computed from invoicing + catalogue crossref - not competitor wallet share."
)

if not SRC.exists():
    st.error(f"Missing {SRC.name}. Run scripts/build_db_parts_classification.py first.")
    st.stop()

df = load_mix()
years = sorted(df["year"].unique())
year = st.selectbox("Year", years, index=len(years) - 1)
d = df[df["year"] == year].copy()

net = d["total_eur"].sum()
bvp = d["bvp_eur"].sum()
contested = d["contested_eur"].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Network parts revenue", f"EUR {net:,.0f}")
c2.metric("BVP share of total", f"{bvp / net:.1%}")
c3.metric("BVP share of contested basket", f"{bvp / contested:.1%}" if contested else "n/a")

st.info(
    "**Contested** = genuine parts that have a BVP equivalent in the catalogue - "
    "the conquerable basket. **Genuine only** has no BVP alternative. "
    "Non-Isuzu aftermarket brands never touch our invoice and are not shown.",
    icon="ℹ️",
)

# Stacked mix per DB
plot = d.sort_values("total_eur", ascending=True)
fig = go.Figure()
for col, name in (
    ("bvp_pct", "BVP"),
    ("genuine_contested_pct", "Genuine (contested)"),
    ("genuine_only_pct", "Genuine only"),
):
    fig.add_bar(
        y=plot["distributor_code"], x=plot[col], name=name,
        orientation="h", marker_color=BUCKET_COLORS[name],
    )
fig.update_layout(
    barmode="stack", height=620, title=f"Parts mix per distributor (CY{year})",
    xaxis_title="Share of total parts revenue", xaxis_tickformat=".0%",
    legend_orientation="h", legend_y=-0.12, margin=dict(l=10, r=10, t=50, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# Per-DB drilldown
st.subheader("Distributor drilldown")
dbs = d.sort_values("total_eur", ascending=False)["distributor_code"].tolist()
pick = st.selectbox("Distributor", dbs)
row = d[d["distributor_code"] == pick].iloc[0]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Parts revenue", f"EUR {row.total_eur:,.0f}")
k2.metric("BVP %", f"{row.bvp_pct:.1%}")
k3.metric("Contested %", f"{row.genuine_contested_pct:.1%}")
k4.metric(
    "Contested BVP capture",
    f"{row.contested_bvp_capture:.1%}" if pd.notna(row.contested_bvp_capture) else "n/a",
)

donut = px.pie(
    names=["BVP", "Genuine (contested)", "Genuine only"],
    values=[row.bvp_eur, row.genuine_contested_eur, row.genuine_only_eur],
    color=["BVP", "Genuine (contested)", "Genuine only"],
    color_discrete_map=BUCKET_COLORS, hole=0.55,
)
donut.update_layout(height=380, title=f"{pick} - revenue by bucket (CY{year})")
st.plotly_chart(donut, use_container_width=True)

st.subheader("Full table")
st.dataframe(
    d[[
        "distributor_code", "total_eur", "bvp_pct",
        "genuine_contested_pct", "genuine_only_pct", "contested_bvp_capture",
    ]].sort_values("total_eur", ascending=False),
    use_container_width=True, hide_index=True,
)
