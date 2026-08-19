"""
PRISM — Decision Models (next-gen layer, built 2026-06-10)

One page for the decision-oriented models:
  Waterfall  — the EUR identity (wallet -> captured -> gap)
  Runway     — Golden Window wallet projection to 2030
  Attach / Leakage / Elasticity — internal only (PRISM_INTERNAL=true)

Defection moved to Early Warning (2026-07-17). This page showed the raw
defection_alerts table; Early Warning ranks the same alerts alongside capture
slope and VOR stress, drops the dead categories (8 of 25 alerts are silent
13-33 months with EUR 0 trailing revenue — never bought, not defecting) and
attaches a euro. Nothing is lost by dropping the tab — see
docs/EARLY_WARNING_DESIGN.md.

All tabs read Data/derived CSVs produced by scripts/build_*.py.
Assumption-dependent fields carry their note column — surface it, never hide it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DERIVED_DIR, is_internal_mode  # noqa: E402
from modules.internal_gate import decision_tab_labels  # noqa: E402

# set_page_config is handled by app.py — do not call it in sub-pages
st.title("Decision Models")
st.caption(
    "Decision layer on top of the verified pipeline. Wallet = GPS max-spend "
    "ceiling (not a forecast). Age-spend curve pending from IML — wallets are "
    "age-flat. Assumption notes are shown per table."
)
st.info(
    "**Defection moved to 🚨 Early Warning.** The same alerts are ranked there "
    "against capture slope and VOR stress, with the dead categories separated out "
    "and a € attached.",
    icon="➡️",
)


def _load(name: str) -> pd.DataFrame:
    p = DERIVED_DIR / name
    if not p.exists():
        st.warning(f"{name} missing — run its build script first.")
        return pd.DataFrame()
    return pd.read_csv(p)


internal = is_internal_mode()
if not internal:
    st.caption(
        "Attach, ITUK dealer leakage, and elasticity stay on the internal PRISM "
        "launcher — double-click `run_prism_internal.ps1` when you are working alone."
    )

tab_names = decision_tab_labels(internal=internal)
tabs = st.tabs(tab_names)
tab_by_name = dict(zip(tab_names, tabs))
tab_wf, tab_rw = tab_by_name["€ Waterfall"], tab_by_name["Revenue Runway"]

with tab_wf:
    wf = _load("wallet_waterfall.csv")
    if not wf.empty:
        year = st.selectbox("Year", sorted(wf["year"].unique(), reverse=True), key="wf_year")
        w = wf[wf["year"] == year]
        net = w[[
            "theoretical_wallet_eur", "captured_genuine_eur", "captured_bvp_eur",
            "addressable_uncaptured_eur", "structural_nonaddressable_eur", "over_target_eur",
        ]].sum()
        # Identity: wallet = captured - over + addressable + structural
        # (over_target is capture above ceiling — must appear as a positive bar).
        structural = float(net["structural_nonaddressable_eur"])
        gap_label = "Uncaptured*" if structural == 0 else "Addressable gap*"
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Wallet ceiling", f"€{net['theoretical_wallet_eur']/1e6:.1f}M")
        c2.metric("Captured", f"€{(net['captured_genuine_eur']+net['captured_bvp_eur'])/1e6:.1f}M")
        c3.metric(gap_label, f"€{net['addressable_uncaptured_eur']/1e6:.1f}M")
        c4.metric(
            "Over-target",
            f"€{net['over_target_eur']/1e3:.0f}K" if net["over_target_eur"] < 1e6
            else f"€{net['over_target_eur']/1e6:.1f}M",
        )
        st.caption(
            "Ceiling = GPS max-spend (not a forecast; age-flat until IML curve). "
            f"{w['assumption_note'].iloc[0]}"
        )

        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "relative"],
            x=[
                "Wallet ceiling",
                "Captured genuine",
                "Captured BVP",
                gap_label,
                "Structural*",
                "Over-target",
            ],
            y=[
                net["theoretical_wallet_eur"],
                -net["captured_genuine_eur"],
                -net["captured_bvp_eur"],
                -net["addressable_uncaptured_eur"],
                -net["structural_nonaddressable_eur"],
                net["over_target_eur"],  # closes identity to ~0
            ],
        ))
        fig.update_layout(title=f"Network € identity — CY{year}", height=420)
        st.plotly_chart(fig, width="stretch")

        st.dataframe(
            w.sort_values("addressable_uncaptured_eur", ascending=False),
            width="stretch", hide_index=True,
        )

with tab_rw:
    rw = _load("revenue_runway.csv")
    if not rw.empty:
        st.caption(
            "BASELINE SCENARIO — CY2025 GPS% held flat; wallet age-flat (IML "
            "age-spend curve pending). Not a forecast."
        )
        dists = ["NETWORK"] + sorted(rw["distributor_code"].unique())
        pick = st.selectbox("Distributor", dists, key="rw_dist")
        if pick == "NETWORK":
            ser = rw.groupby("year", as_index=False)[["wallet_eur", "projected_capture_eur"]].sum()
        else:
            ser = rw[rw["distributor_code"] == pick]
        fig = px.line(ser, x="year", y=["wallet_eur", "projected_capture_eur"],
                      title=f"{pick} — wallet ceiling vs projected capture (CY2025 GPS% held flat)")
        fig.update_layout(height=420, yaxis_title="EUR")
        st.plotly_chart(fig, width="stretch")
        st.caption(rw["scenario_note"].iloc[0])
        peaks = rw.drop_duplicates("distributor_code")[
            ["distributor_code", "peak_wallet_year", "peak_wallet_eur",
             "wallet_2030_vs_2024_pct", "cum_wallet_2026_2030_eur",
             "cum_projected_capture_2026_2030_eur"]
        ].sort_values("cum_wallet_2026_2030_eur", ascending=False)
        st.dataframe(peaks, width="stretch", hide_index=True)

if internal:
    tab_att = tab_by_name["Attach"]
    tab_leak = tab_by_name["ITUK Leakage"]
    tab_el = tab_by_name["Elasticity"]

    with tab_att:
        at = _load("attach_rates.csv")
        if not at.empty:
            st.caption(
                at["method_note"].iloc[0]
                + " — lifts are association at dealer-year grain, not causal gateway proof."
            )
            cat = st.selectbox(
                "Anchor category (A)", sorted(at["category_a"].unique()),
                index=sorted(at["category_a"].unique()).index("lubricants")
                if "lubricants" in set(at["category_a"]) else 0,
            )
            sub = at[at["category_a"] == cat].sort_values("attach_lift", ascending=False)
            fig = px.bar(sub, x="category_b", y="attach_lift",
                         title=f"Attach lift: dealers buying {cat} also buy …")
            fig.add_hline(y=1.0, line_dash="dash")
            fig.update_layout(height=380)
            st.plotly_chart(fig, width="stretch")
            st.dataframe(sub.drop(columns=["method_note"]), width="stretch", hide_index=True)

    with tab_leak:
        dl = _load("dealer_leakage_ituk.csv")
        if not dl.empty:
            st.warning(
                "Relative mix benchmark only — NOT the IML service-schedule absolute PMS gap "
                "(€2.0M). Soft PMS-tag join (≈16% of ITUK sell-out units mapped). "
                "Use as a call-order hint, not a € commitment."
            )
            st.caption(dl["benchmark_note"].iloc[0])
            top = (dl.groupby("dealer_name", as_index=False)["gap_eur"].sum()
                   .sort_values("gap_eur", ascending=False).head(15))
            fig = px.bar(top, x="gap_eur", y="dealer_name", orientation="h",
                         title="ITUK dealers — relative mix gap € (call list, not IML gap)")
            fig.update_layout(height=480, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, width="stretch")
            drop_cols = [c for c in ("benchmark_note",) if c in dl.columns]
            st.dataframe(
                dl.drop(columns=drop_cols).head(200),
                width="stretch", hide_index=True,
            )

    with tab_el:
        el = _load("price_volume_elasticity.csv")
        if not el.empty:
            st.warning(
                "LOW POWER by construction (annual prices, 2 YoY transitions). "
                "Read as direction + rough magnitude — never quote a beta externally."
            )
            view = el[~el["low_power"]] if st.toggle("Adequate n only", value=True) else el
            fig = px.bar(view.sort_values("beta_elasticity"), x="beta_elasticity", y="category",
                         orientation="h", error_x="se_beta",
                         title="Price-volume response by category (beta, qty-weighted)")
            fig.add_vline(x=0, line_dash="dash")
            fig.update_layout(height=560)
            st.plotly_chart(fig, width="stretch")
            st.dataframe(view.drop(columns=["method_note"]), width="stretch", hide_index=True)
