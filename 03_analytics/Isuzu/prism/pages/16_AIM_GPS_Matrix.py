"""PRISM — GPS x PMS-capture strategic quadrant by distributor.

Axis change 2026-07-17: x was AIM pricing-risk exposure, gated at a hardcoded
0.12 that no distributor has ever crossed (all-time max 0.0487) — the quadrant
was a 1-D restatement of GPS. x is now PMS total capture. AIM exposure is kept
in the table as context, not as an axis.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR))

from config import AIM_GPS_MATRIX_CSV  # noqa: E402

# set_page_config is in app.py only (multipage app)

st.markdown(
    """
<div style="background:linear-gradient(90deg,#1B3A6B,#E87722);padding:1rem 1.25rem;border-radius:8px;margin-bottom:1rem">
  <h1 style="color:#fff;margin:0;font-size:1.5rem">GPS × PMS Capture — Strategic Quadrant</h1>
  <p style="color:#E8F0FA;margin:.35rem 0 0;font-size:.9rem">
    Spend per unit vs PMS workshop capture · CY from derived pipeline
  </p>
</div>
""",
    unsafe_allow_html=True,
)

if not AIM_GPS_MATRIX_CSV.exists():
    st.warning("Run `python scripts/build_aim_gps_matrix.py` after P4/P5 build.")
    st.stop()

df = pd.read_csv(AIM_GPS_MATRIX_CSV)
years = sorted(int(y) for y in df["year"].dropna().unique())

# Default to the newest COMPLETE year. A part-year's absolute spend/unit is not
# comparable to a full year's, so opening on it invites reading a calendar
# artifact as a network collapse.
complete = [y for y in years if not bool(df.loc[df["year"] == y, "is_partial_year"].iloc[0])]
default_year = (complete or years)[-1]

year = st.sidebar.selectbox("Year", years, index=years.index(default_year))
sub = df[df["year"] == year].copy()

is_partial = bool(sub["is_partial_year"].iloc[0])
coverage = float(sub["year_coverage_pct"].iloc[0])
if is_partial:
    st.warning(
        f"**CY{year} is a partial year — billing data covers ~{coverage:.0%} of it.** "
        f"Spend-per-unit and capture are part-year totals and must not be read as, or "
        f"compared against, a full year. The quadrant split still holds *within* CY{year} "
        f"(every distributor is truncated by the same window), but absolute € and capture "
        f"are not annual figures."
    )

quadrants = sorted(sub["quadrant"].dropna().unique())
sel_q = st.sidebar.multiselect("Quadrant", quadrants, default=quadrants)
if sel_q:
    sub = sub[sub["quadrant"].isin(sel_q)]

med_g = float(sub["gps_median_benchmark_eur"].iloc[0]) if not sub.empty else float("nan")
med_c = float(sub["capture_median_benchmark"].iloc[0]) if not sub.empty else float("nan")
scope = sub["capture_axis_scope"].iloc[0] if not sub.empty else "all"

plot = sub[sub["gps_spu_eur"].notna() & sub["capture_axis"].notna()]
n_excl = len(sub) - len(plot)

fig = px.scatter(
    plot,
    x="capture_axis",
    y="gps_spu_eur",
    color="quadrant",
    hover_name="distributor_code",
    hover_data=["country", "gps_sales_eur", "pms_expected_qty", "pms_actual_qty"],
    labels={
        "capture_axis": f"PMS capture ({scope} categories)",
        "gps_spu_eur": "GPS spend per unit (€)",
    },
    title=f"Distributors CY{year} — median GPS €{med_g:,.0f} · median capture {med_c:.1%}",
)
fig.add_hline(y=med_g, line_dash="dot", line_color="#999")
fig.add_vline(x=med_c, line_dash="dot", line_color="#999")
st.plotly_chart(fig, use_container_width=True)

if n_excl:
    st.caption(
        f"{n_excl} row(s) not plotted — no UIO denominator and/or no PMS expected-demand "
        f"basis, so neither axis is defined. They are listed as *insufficient data* below "
        f"rather than being scored as weak."
    )

st.dataframe(
    sub[
        [
            "distributor_code",
            "country",
            "region",
            "gps_spu_eur",
            "gps_traffic_light",
            "capture_axis",
            "pms_capture_filters",
            "quadrant_label",
            "gps_sales_eur",
            "aim_high_risk_pct",
        ]
    ].sort_values("gps_spu_eur", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "capture_axis": st.column_config.NumberColumn(f"PMS capture ({scope})", format="%.1f%%"),
        "pms_capture_filters": st.column_config.NumberColumn("Capture (oil/fuel/air)", format="%.1f%%"),
        "aim_high_risk_pct": st.column_config.NumberColumn("AIM risk % (context)", format="%.2f%%"),
    },
)

st.caption(
    "**Defend** = high GPS · high capture — **Attach gap** = high GPS · low capture "
    "(spending, not servicing) — **Wallet gap** = low GPS · high capture (servicing, "
    "small wallet) — **Priority target** = both below median. Axes split on the "
    "**within-year** network median, so a partial year stays internally comparable. "
    "`aim_high_risk_pct` is shown as context only: network CY2025 exposure is 0.99% and "
    "no distributor has ever exceeded 4.9%, so it does not separate anyone. "
    "Air-filter expected demand carries FACTS.md flag C (0.5 interval factor is a "
    "**provisional** assumption pending IML). Source: `aim_gps_matrix.csv`."
)
