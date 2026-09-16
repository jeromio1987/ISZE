"""PRISM — ITUK hub (merged page, IA phase 5 · 2026-08-20).

One entry for the ITUK PMS narrative: Story · PN audit · Incentive, plus the
internal-only Dealer attach + Leakage. Absorbs 11_ITUK_PMS_Story, 6_ITUK_PMS_Audit,
the incentive block from 3_PMS, and the attach/leakage blocks from 18_Decision_Models.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import BETA_MODE, is_internal_mode  # noqa: E402
from modules.ituk_charts import (  # noqa: E402
    render_ituk_audit,
    render_ituk_incentive,
    render_ituk_internal,
    render_ituk_story,
)

st.markdown(
    """
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .ituk-hero { background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.1rem; }
    .ituk-hero h1 { color: #fff !important; margin: 0; font-size: 1.7rem; font-weight: 700; }
    .ituk-hero p  { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
</style>
""",
    unsafe_allow_html=True,
)

if st.session_state.get("beta_mode", BETA_MODE):
    st.warning("BETA MODE — not for distribution", icon="⚠️")

st.markdown(
    """
<div class="ituk-hero">
  <h1>ITUK — mix, not capture deficit</h1>
  <p>The ITUK PMS narrative with its receipts: the story, the part-number audit, the incentive, and (internal) attach &amp; dealer leakage.</p>
</div>
""",
    unsafe_allow_html=True,
)

internal = is_internal_mode()
tab_labels = ["Story", "PN audit", "Incentive"]
if internal:
    tab_labels.append("Internal — attach & leakage")
tabs = st.tabs(tab_labels)

with tabs[0]:
    render_ituk_story()
with tabs[1]:
    render_ituk_audit()
with tabs[2]:
    render_ituk_incentive()
if internal:
    with tabs[3]:
        render_ituk_internal()

st.caption(
    "ITUK hub · Story/Audit read `pms_capture_by_db_year.csv` / `ituk_pms_pn_audit.csv` · "
    "Attach & leakage are internal-only (association, not causal; call-order hint, not IML € gap)."
)
