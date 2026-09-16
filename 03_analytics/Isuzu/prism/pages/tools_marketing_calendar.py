"""PRISM — PMS Marketing Calendar (moved from 3_PMS.py, IA phase 7)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

st.markdown(
    """
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .cal-hero { background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.1rem; }
    .cal-hero h1 { color: #fff !important; margin: 0; font-size: 1.7rem; font-weight: 700; }
    .cal-hero p  { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="cal-hero">
  <h1>2026 PMS Marketing Calendar</h1>
  <p>Planned service-part campaigns by quarter — which is active this month.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.caption(
    "Sample / partial — Q2–Q3 only (three campaigns shown). Not the full-year calendar."
)

current_month = datetime.now().month


def _campaign_status(months: list) -> str:
    return "ACTIVE" if current_month in months else ""


campaigns = [
    {"Quarter": "Q2", "Campaign": "Spring into Service", "Period": "Apr – Jun 2026",
     "PMS Focus": "Filters + Brakes (10–20% off)", "Status": _campaign_status([4, 5, 6])},
    {"Quarter": "Q3", "Campaign": "Parts Basket Pricing", "Period": "Aug – Sep 2026",
     "PMS Focus": "Fleet basket kits", "Status": _campaign_status([8, 9])},
    {"Quarter": "Q3", "Campaign": "Brakes & Safety", "Period": "Sep – Oct 2026",
     "PMS Focus": "Brakes + Lights", "Status": _campaign_status([9, 10])},
]
df_campaigns = pd.DataFrame(campaigns)
st.dataframe(df_campaigns, width="stretch", hide_index=True)
st.caption("ACTIVE = campaign running in current calendar month.")
