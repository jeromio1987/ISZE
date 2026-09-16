"""
PRISM — ITUK PMS part-number audit (Contract 16).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402

AUDIT_CSV = DERIVED_DIR / "ituk_pms_pn_audit.csv"

st.title("ITUK PMS part-number audit")
st.caption(
    "Registry PMS lines for ITUK (N75 scope + multi PNs). "
    "Rebuild: `python scripts/build_ituk_pms_pn_audit.py`"
)

if not AUDIT_CSV.exists():
    st.error(f"Missing {AUDIT_CSV.name}. Run `python scripts/build_ituk_pms_pn_audit.py` after P1 build.")
    st.stop()

df = pd.read_csv(AUDIT_CSV)
years = sorted(int(y) for y in df["year"].dropna().unique())
cats = sorted(df["pms_category"].dropna().unique())

c1, c2 = st.columns(2)
with c1:
    year_sel = st.selectbox("Year", years, index=len(years) - 1 if years else 0)
with c2:
    cat_sel = st.selectbox("PMS category", cats, index=cats.index("oil_filter") if "oil_filter" in cats else 0)

sub = df[(df["year"] == year_sel) & (df["pms_category"] == cat_sel)].copy()
if sub.empty:
    st.warning("No rows for this year / category.")
    st.stop()

total_qty = float(sub["actual_qty"].sum())
st.metric("Category actual qty", f"{total_qty:,.0f}", help=f"Scope: {sub['scope'].iloc[0]}")

fig = px.bar(
    sub.sort_values("actual_qty", ascending=True),
    x="actual_qty",
    y="part_number",
    color="pms_type",
    orientation="h",
    text=sub.sort_values("actual_qty", ascending=True)["share_of_category_qty"].apply(
        lambda x: f"{x * 100:.0f}%"
    ),
    labels={"actual_qty": "Units", "part_number": "Part number", "pms_type": "Line"},
    title=f"ITUK {cat_sel} — CY{year_sel}",
)
fig.update_layout(height=max(320, len(sub) * 36), showlegend=True)
st.plotly_chart(fig, width='stretch')

st.dataframe(
    sub.sort_values("actual_qty", ascending=False),
    column_config={
        "actual_qty": st.column_config.NumberColumn(format="%.0f"),
        "actual_rev_eur": st.column_config.NumberColumn(format="€ %.0f"),
        "share_of_category_qty": st.column_config.NumberColumn(format="%.1%%"),
    },
    hide_index=True,
    width='stretch',
)

with st.expander("Methodology"):
    st.markdown(
        """
        - **Source:** `sales_fact.parquet` + ITUK registry + BVP-catalog PMS (`build_bvp_p0_p1` tagging).
        - **Scope:** ITUK `N75_only` filter (includes `pms_model=multi` PNs).
        - **Share:** PN qty ÷ category total qty for that year.
        - Use with `pms_capture_by_db_year.csv` total capture — not comparable to single-PN dealer studies.
        """
    )
