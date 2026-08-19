"""PRISM — P5 Forecast (read-only, Mode B internal).

Portfolio view: DB × category baseline forecast, backtest WAPE, next-6-month outlook.
Source: forecast_final.parquet, backtest_report.parquet, forecast_final_*.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"

st.markdown(
    f"""
<style>
    .fc-hero {{ background: linear-gradient(120deg,{ISZE_BLUE} 0%,#2C5AA0 100%);
        padding:1.2rem 1.4rem;border-radius:12px;margin-bottom:1rem; }}
    .fc-hero h1 {{ color:#fff!important;margin:0;font-size:1.6rem; }}
    .fc-hero p {{ color:#E8F0FA;margin:.3rem 0 0;font-size:.88rem; }}
</style>
<div class="fc-hero">
  <h1>Demand Forecast</h1>
  <p>P5 baseline — Holt/seasonal-naive + linear trend + parc proxy. No LLM. Overrides logged separately.</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading forecast…")
def _load() -> tuple[pd.DataFrame, pd.DataFrame, Path | None]:
    d = Path(DERIVED_DIR)
    fp = d / "forecast_final.parquet"
    bt = d / "backtest_report.parquet"
    csvs = sorted(d.glob("forecast_final_*.csv"))
    csv_path = csvs[-1] if csvs else None
    if not fp.exists():
        return pd.DataFrame(), pd.DataFrame(), csv_path
    return pd.read_parquet(fp), pd.read_parquet(bt) if bt.exists() else pd.DataFrame(), csv_path


final, backtest, csv_path = _load()

if final.empty:
    st.warning("No forecast on disk. Run `python 04_tools/forecast/build_forecast_baseline.py` then `build_forecast_final.py`.")
    st.stop()

dbs = sorted(final["db_code"].unique())
db = st.selectbox("Distributor", dbs, index=dbs.index("ITUK") if "ITUK" in dbs else 0)
sub = final[final["db_code"] == db].copy()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Series", sub[["category"]].nunique())
c2.metric("Horizon rows", len(sub))
c3.metric("Next month units", int(sub.loc[sub["horizon_step"] == 1, "units_forecast"].sum()))
c4.metric("Next month €", f"{sub.loc[sub['horizon_step'] == 1, 'revenue_forecast'].sum():,.0f}")

if not backtest.empty:
    bt_db = backtest[backtest["db_code"] == db]
    if not bt_db.empty:
        st.subheader("Backtest WAPE by category")
        show = bt_db.sort_values("wape_best").head(20)
        fig = px.bar(
            show,
            x="category",
            y="wape_best",
            color="best_model",
            title=f"{db} — median WAPE {bt_db['wape_best'].median():.1f}%",
            labels={"wape_best": "WAPE %", "category": "Category"},
        )
        fig.update_layout(xaxis_tickangle=-45, height=420)
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Next 6 months — top categories by €")
top_cat = (
    sub.groupby("category", as_index=False)["revenue_forecast"]
    .sum()
    .sort_values("revenue_forecast", ascending=False)
    .head(8)["category"]
)
plot_df = sub[sub["category"].isin(top_cat)]
fig2 = px.line(
    plot_df,
    x="forecast_month",
    y="units_forecast",
    color="category",
    markers=True,
    title=f"{db} unit forecast (best model per series)",
)
fig2.update_layout(height=440)
st.plotly_chart(fig2, use_container_width=True)

with st.expander("Full forecast table"):
    st.dataframe(
        sub.sort_values(["category", "horizon_step"])[
            ["category", "forecast_month", "units_forecast", "revenue_forecast", "best_model", "wape_best"]
        ],
        use_container_width=True,
        hide_index=True,
    )

if csv_path:
    st.caption(f"CSV refresh: `{csv_path.name}`")
