"""ITUK hub render functions — extracted for the merged ituk.py (IA phase 5).

Lift-and-shift of the bodies of 11_ITUK_PMS_Story.py and 6_ITUK_PMS_Audit.py so
the ITUK hub can host them as tabs alongside Incentive + internal Attach/Leakage.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import DERIVED_DIR

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
from modules.plotly_style import BASE_LAYOUT as PLOTLY, style


def render_ituk_story() -> None:
    """ITUK PMS Story — the mix-not-deficit narrative (body of 11_ITUK_PMS_Story.py)."""
    CAPTURE_CSV = DERIVED_DIR / "pms_capture_by_db_year.csv"
    if not CAPTURE_CSV.exists():
        st.error(f"Missing {CAPTURE_CSV.name}. Run the PMS (P1) build first.")
        return

    cap = pd.read_csv(CAPTURE_CSV)
    ituk = cap[cap["distributor_code"] == "ITUK"].copy()
    if ituk.empty:
        st.error("No ITUK rows in pms_capture_by_db_year.csv.")
        return

    years = sorted(int(y) for y in ituk["year"].dropna().unique())
    latest = max(years)
    tot = ituk[ituk["line_type"] == "total"].copy()

    def _cap(cat: str, yr: int, lt: str) -> float:
        row = ituk[(ituk["pms_category"] == cat) & (ituk["year"] == yr) & (ituk["line_type"] == lt)]
        return float(row["capture_rate"].iloc[0]) if not row.empty else float("nan")

    served = tot[(tot["year"] == latest) & (tot["capture_rate"] >= 0.999)]["pms_category"].nunique()
    total_cats = tot[tot["year"] == latest]["pms_category"].nunique()
    recoverable = float(tot[tot["year"] == latest]["revenue_gap_eur"].sum())
    oil_gen_first = _cap("oil_filter", years[0], "genuine")
    oil_gen_last = _cap("oil_filter", latest, "genuine")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Categories at 100% capture", f"{served} / {total_cats}", help=f"CY{latest}, total line")
    k2.metric(
        "Oil-filter genuine capture",
        f"{oil_gen_last:.0%}",
        delta=f"{(oil_gen_last - oil_gen_first) * 100:+.0f} pp vs CY{years[0]}",
        help="Genuine alone vs expected oil-filter demand. >100% = BVP now pure overflow.",
    )
    k3.metric("Recoverable revenue gap", f"€{recoverable:,.0f}", help=f"Sum of total-line revenue_gap_eur, CY{latest}")
    k4.metric("Fleet (UIO)", f"{int(tot['uio_units'].iloc[0]):,}", help="ITUK DVLA parc, denominator for expected demand")

    st.divider()
    st.subheader("1 · Oil filter — the mix-shift story in one chart")
    st.markdown(
        "Total capture is **pinned at 100%** every year — demand is fully served. "
        "What changed is *who* serves it: genuine capture climbed "
        f"**{oil_gen_first:.0%} → {oil_gen_last:.0%}**. By CY{latest} genuine alone covers expected "
        "demand, so BVP has gone from carrying the category to pure overflow."
    )
    oil = ituk[ituk["pms_category"] == "oil_filter"].sort_values("year")
    oil_q = oil.pivot_table(index="year", columns="line_type", values="actual_qty", aggfunc="sum").fillna(0)
    c_left, c_right = st.columns([3, 2])
    with c_left:
        fig = go.Figure()
        fig.add_bar(x=oil_q.index, y=oil_q.get("genuine", 0), name="Genuine units", marker_color=ISZE_BLUE)
        fig.add_bar(x=oil_q.index, y=oil_q.get("bvp", 0), name="BVP units", marker_color=ISZE_ORANGE)
        fig.update_layout(barmode="stack", title="Oil filter — units by line type", height=360, **PLOTLY)
        fig.update_xaxes(tickmode="array", tickvals=list(oil_q.index))
        st.plotly_chart(fig, width="stretch")
    with c_right:
        oil_gen = oil[oil["line_type"] == "genuine"].sort_values("year")
        gline = go.Figure()
        gline.add_scatter(
            x=oil_gen["year"], y=oil_gen["capture_rate"],
            mode="lines+markers", name="Genuine capture", line=dict(color=ISZE_BLUE, width=3),
        )
        gline.add_hline(y=1.0, line_dash="dot", line_color="#888", annotation_text="100% of demand")
        gline.update_layout(title="Genuine capture trajectory", height=360, **PLOTLY)
        gline.update_yaxes(tickformat=".0%")
        gline.update_xaxes(tickmode="array", tickvals=years)
        st.plotly_chart(gline, width="stretch")

    st.divider()
    st.subheader("2 · Where the recoverable money is")
    st.markdown(
        "Big-3 (oil / fuel / brake pad) carry **€0 gap** — they're at ceiling. "
        "The genuine upside sits in **air filter** (availability, ~0 BVP) and **clutch**."
    )
    latest_tot = tot[tot["year"] == latest].copy().sort_values("revenue_gap_eur", ascending=True)
    fig2 = go.Figure()
    fig2.add_bar(
        x=latest_tot["revenue_gap_eur"],
        y=latest_tot["pms_category"],
        orientation="h",
        marker_color=[ISZE_ORANGE if g > 1000 else ISZE_BLUE for g in latest_tot["revenue_gap_eur"]],
        text=[f"€{g:,.0f}  ({c:.0%})" for g, c in zip(latest_tot["revenue_gap_eur"], latest_tot["capture_rate"])],
        textposition="outside",
    )
    fig2.update_layout(title=f"Recoverable revenue gap by category — CY{latest}", height=380, **PLOTLY)
    fig2.update_xaxes(title="Revenue gap (€)")
    st.plotly_chart(fig2, width="stretch")

    st.divider()
    st.subheader("3 · Air filter — the clean genuine opportunity")
    af = ituk[(ituk["pms_category"] == "air_filter") & (ituk["line_type"] == "total")].sort_values("year")
    af_first, af_last = af["capture_rate"].iloc[0], af["capture_rate"].iloc[-1]
    af_gap = float(af["revenue_gap_eur"].iloc[-1])
    a1, a2, a3 = st.columns(3)
    a1.metric("Total capture", f"{af_last:.0%}", delta=f"{(af_last - af_first) * 100:+.0f} pp", help=f"CY{years[0]}→{latest}")
    a2.metric("Annual revenue gap", f"€{af_gap:,.0f}", help=f"CY{latest}")
    a3.metric("Substitution risk", "Negligible", help="BVP ~0 units — this is availability, not BVP loss")
    st.markdown(
        f"Air filter sits at **{af_last:.0%}** total capture with almost no BVP presence — meaning the "
        f"missing **€{af_gap:,.0f}/yr** is genuine demand ITUK simply isn't serving, *not* lost to BVP. "
        "Cleanest single line in the book: availability / stocking, no competitive displacement to fight."
    )

    st.divider()
    st.subheader(f"4 · Category scorecard — CY{latest}")
    rows = []
    for cat in sorted(ituk["pms_category"].unique()):
        t = ituk[(ituk["pms_category"] == cat) & (ituk["year"] == latest) & (ituk["line_type"] == "total")]
        if t.empty:
            continue
        bvp_q = float(ituk[(ituk["pms_category"] == cat) & (ituk["year"] == latest) & (ituk["line_type"] == "bvp")]["actual_qty"].sum())
        gen_q = float(ituk[(ituk["pms_category"] == cat) & (ituk["year"] == latest) & (ituk["line_type"] == "genuine")]["actual_qty"].sum())
        tot_q = bvp_q + gen_q
        cr = float(t["capture_rate"].iloc[0])
        gap = float(t["revenue_gap_eur"].iloc[0])
        bvp_share = bvp_q / tot_q if tot_q else 0.0
        if cr >= 0.999:
            verdict = "At ceiling — mix play" if bvp_share > 0.05 else "At ceiling — genuine-led"
        elif bvp_share > 0.05:
            verdict = "Gap + substitution"
        elif tot_q == 0:
            verdict = "Catalog gap (no sales)"
        else:
            verdict = "Gap — availability"
        rows.append(
            {"Category": cat, "Total capture": cr, "BVP unit share": bvp_share,
             "Revenue gap €": gap, "Genuine units": int(gen_q), "BVP units": int(bvp_q), "Verdict": verdict}
        )
    score = pd.DataFrame(rows).sort_values("Revenue gap €", ascending=False)
    st.dataframe(
        score,
        column_config={
            "Total capture": st.column_config.NumberColumn(format="%.0f%%"),
            "BVP unit share": st.column_config.NumberColumn(format="%.0f%%"),
            "Revenue gap €": st.column_config.NumberColumn(format="€ %,.0f"),
        },
        hide_index=True, width="stretch",
    )

    with st.expander("Methodology & talking points"):
        st.markdown(
            f"""
            **Source:** `pms_capture_by_db_year.csv` (line_type = total / genuine / bvp), ITUK only.
            Expected demand = UIO {int(tot['uio_units'].iloc[0]):,} × service rate × addressable %, capped at 100% total capture.

            **The three things to say internally:**
            1. **Don't lead with "capture deficit."** Oil, fuel, brake pad are at 100% — saying ITUK under-serves PMS is wrong and they'll know it.
            2. **Lead with mix.** Oil-filter genuine capture went {oil_gen_first:.0%} → {oil_gen_last:.0%}: genuine is reclaiming the category, BVP is now overflow. That's the win to protect and extend.
            3. **The real € upside is air filter (€{af_gap:,.0f}/yr, availability) + clutch (~€240K, low capture).** These are genuine-incremental, not BVP fights.

            **% capture > 100% on genuine** means genuine units alone exceed modelled expected demand — interpret as "genuine fully covers the parc," not a data error.

            **⚠️ Cross-category caveat (data-integrity flag C):** expected demand uses one flat service
            rate for all consumable filters (oil = fuel = air). Air filters are replaced far less often
            than oil, so the air denominator is overstated and air capture is artificially **deflated**.
            Compare a category against its own trajectory over time — do **not** rank air vs oil/fuel on
            capture % until air gets a real, schedule-sourced replacement interval.
            """
        )


def render_ituk_audit() -> None:
    """ITUK PMS part-number audit (body of 6_ITUK_PMS_Audit.py)."""
    AUDIT_CSV = DERIVED_DIR / "ituk_pms_pn_audit.csv"
    if not AUDIT_CSV.exists():
        st.error(f"Missing {AUDIT_CSV.name}. Run `python scripts/build_ituk_pms_pn_audit.py` after P1 build.")
        return

    df = pd.read_csv(AUDIT_CSV)
    years = sorted(int(y) for y in df["year"].dropna().unique())
    cats = sorted(df["pms_category"].dropna().unique())

    c1, c2 = st.columns(2)
    with c1:
        year_sel = st.selectbox("Year", years, index=len(years) - 1 if years else 0, key="ituk_audit_year")
    with c2:
        cat_sel = st.selectbox("PMS category", cats, index=cats.index("oil_filter") if "oil_filter" in cats else 0, key="ituk_audit_cat")

    sub = df[(df["year"] == year_sel) & (df["pms_category"] == cat_sel)].copy()
    if sub.empty:
        st.warning("No rows for this year / category.")
        return

    total_qty = float(sub["actual_qty"].sum())
    st.metric("Category actual qty", f"{total_qty:,.0f}", help=f"Scope: {sub['scope'].iloc[0]}")

    fig = px.bar(
        sub.sort_values("actual_qty", ascending=True),
        x="actual_qty", y="part_number", color="pms_type", orientation="h",
        text=sub.sort_values("actual_qty", ascending=True)["share_of_category_qty"].apply(lambda x: f"{x * 100:.0f}%"),
        labels={"actual_qty": "Units", "part_number": "Part number", "pms_type": "Line"},
        title=f"ITUK {cat_sel} — CY{year_sel}",
    )
    fig.update_layout(height=max(320, len(sub) * 36), showlegend=True)
    st.plotly_chart(style(fig), width="stretch")

    st.dataframe(
        sub.sort_values("actual_qty", ascending=False),
        column_config={
            "actual_qty": st.column_config.NumberColumn(format="%.0f"),
            "actual_rev_eur": st.column_config.NumberColumn(format="€ %.0f"),
            "share_of_category_qty": st.column_config.NumberColumn(format="%.1%%"),
        },
        hide_index=True, width="stretch",
    )


def render_ituk_incentive() -> None:
    """ITUK Incentive Structure (block from 3_PMS.py §6)."""
    col_tier, col_stretch = st.columns([1, 1])
    with col_tier:
        st.markdown("**Dealer Credit Tiers (PMS volume performance)**")
        tier_data = pd.DataFrame([
            {"Target Threshold": "100% of target (baseline)",    "Dealer Credit": "£250"},
            {"Target Threshold": "125% of target (+25% uplift)", "Dealer Credit": "£500"},
            {"Target Threshold": "150% of target (+50% uplift)", "Dealer Credit": "£750"},
            {"Target Threshold": "Best N75 brake conversion",    "Dealer Credit": "+£500 bonus"},
            {"Target Threshold": "Best air filter attachment",   "Dealer Credit": "+£500 bonus"},
        ])
        st.dataframe(tier_data, width="stretch", hide_index=True)
    with col_stretch:
        st.markdown("**2030 Stretch Tracker — ITUK / UK Market**")
        stretch_data = pd.DataFrame([
            {"Metric": "2025 baseline",          "Value": "£12.87M",  "Notes": "Actual FY2025"},
            {"Metric": "2026 plan (77% UIO)",    "Value": "£13.13M",  "Notes": "77% UIO share target"},
            {"Metric": "2026 stretch (80% UIO)", "Value": "£13.64M",  "Notes": "Stretch target"},
            {"Metric": "ISZE kickback pot",       "Value": "£62,052",  "Notes": "Available for dealers"},
        ])
        st.dataframe(stretch_data, width="stretch", hide_index=True)


def render_ituk_internal() -> None:
    """Attach + ITUK dealer leakage (internal-only; body from 18_Decision_Models.py)."""
    def _load(name: str) -> pd.DataFrame:
        p = DERIVED_DIR / name
        if not p.exists():
            st.warning(f"{name} missing — run its build script first.")
            return pd.DataFrame()
        return pd.read_csv(p)

    st.markdown("#### Dealer attach (association, not causal)")
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
            key="ituk_att_cat",
        )
        sub = at[at["category_a"] == cat].sort_values("attach_lift", ascending=False)
        fig = px.bar(sub, x="category_b", y="attach_lift",
                     title=f"Attach lift: dealers buying {cat} also buy …")
        fig.add_hline(y=1.0, line_dash="dash")
        fig.update_layout(height=380)
        st.plotly_chart(style(fig), width="stretch")
        st.dataframe(sub.drop(columns=["method_note"]), width="stretch", hide_index=True)

    st.divider()
    st.markdown("#### ITUK dealer leakage (relative mix benchmark)")
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
        st.plotly_chart(style(fig), width="stretch")
        drop_cols = [c for c in ("benchmark_note",) if c in dl.columns]
        st.dataframe(dl.drop(columns=drop_cols).head(200), width="stretch", hide_index=True)
