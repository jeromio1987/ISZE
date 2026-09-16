"""PRISM — Internal shelf (IA phase 7 · 2026-08-20).

Consolidates the internal-only analyst views that must never sit on an MD path:
  - Customer aftersales-risk threat map + signal breakdown (from 15_Customer_Risk)
  - Aftermarket scrape (PartsPool Autodoc, gated)
  - Demand-Flow Sankey (inferred leakage)
  - Price-volume elasticity (low power by construction)
Only registered in nav when PRISM_INTERNAL=true.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR, is_internal_mode  # noqa: E402
from modules import advanced_visuals as av  # noqa: E402
from modules.customer_risk_charts import (  # noqa: E402
    DEFAULT_W,
    STREET_FACTOR,
    compute_risk_scores,
    load_eucon_scrape,
    render_aftermarket_scrape,
    render_signal_breakdown,
    render_threat_map,
)
from modules.plotly_style import style  # noqa: E402

st.markdown(
    """
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .shelf-hero { background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.1rem; }
    .shelf-hero h1 { color: #fff !important; margin: 0; font-size: 1.7rem; font-weight: 700; }
    .shelf-hero p  { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
</style>
""",
    unsafe_allow_html=True,
)

if not is_internal_mode():
    st.warning("INTERNAL ONLY — this page is not shown in the MD-safe launcher.", icon="🔒")
    st.stop()

st.markdown(
    """
<div class="shelf-hero">
  <h1>Internal shelf</h1>
  <p>Analyst-only views that must not sit on a distributor path: customer-risk breakdown, aftermarket scrape, inferred leakage and elasticity.</p>
</div>
""",
    unsafe_allow_html=True,
)


def _load(name: str) -> pd.DataFrame:
    p = DERIVED_DIR / name
    if not p.exists():
        st.warning(f"{name} missing — run its build script first.")
        return pd.DataFrame()
    return pd.read_csv(p)


tabs = st.tabs(["Customer risk", "Aftermarket scrape", "Demand-flow (inferred)", "Elasticity"])

with tabs[0]:
    df = _load("db_aftersales_risk.csv")
    if not df.empty:
        st.warning(
            "This 0–100 ranking is an unvalidated hand-weighted rubric — not a KPI, and it did not "
            "beat last year on a holdout. The call list is Early Warning; these views are for the "
            "threat-map / signal-breakdown analyst reading only."
        )
        df = compute_risk_scores(df, dict(DEFAULT_W))
        render_threat_map(df)
        st.markdown("---")
        render_signal_breakdown(df)

with tabs[1]:
    st.caption("PartsPool Autodoc DE/NO dated 29 Mar 2026 — not the 2023 UK workshop survey.")
    eu = load_eucon_scrape(DERIVED_DIR, STREET_FACTOR)
    render_aftermarket_scrape(eu, STREET_FACTOR)

with tabs[2]:
    st.caption(
        "⚠️ The 'Leakage' leg and any leakage figure are an INFERENCE (under-service gap), "
        "not a measured competitor number — internal use only."
    )
    try:
        st.plotly_chart(style(av.fig_demand_flow_sankey(DERIVED_DIR)), width="stretch")
    except Exception as e:  # noqa: BLE001
        st.info(f"Demand-flow unavailable: {e}")

with tabs[3]:
    el = _load("price_volume_elasticity.csv")
    if not el.empty:
        st.warning(
            "LOW POWER by construction (annual prices, 2 YoY transitions). "
            "Read as direction + rough magnitude — never quote a beta externally."
        )
        import plotly.express as px
        view = el[~el["low_power"]] if st.toggle("Adequate n only", value=True) else el
        fig = px.bar(view.sort_values("beta_elasticity"), x="beta_elasticity", y="category",
                     orientation="h", error_x="se_beta",
                     title="Price-volume response by category (beta, qty-weighted)")
        fig.add_vline(x=0, line_dash="dash")
        fig.update_layout(height=560)
        st.plotly_chart(style(fig), width="stretch")
        st.dataframe(view.drop(columns=["method_note"]), width="stretch", hide_index=True)

st.caption("Internal shelf · gated behind PRISM_INTERNAL · sources under `01_data/00_derived/`")
