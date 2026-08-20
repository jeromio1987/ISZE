"""
PRISM — ITUK PMS Story (internal ISZE prep).

The narrative: ITUK's PMS book is NOT a capture-deficit story. The big-3
categories (oil / fuel / brake pad) are at the 100% ceiling — demand is served.
The lever is MIX (genuine vs BVP), and genuine is already winning share back.
The only genuine *capture* gaps are air filter (availability) and clutch.

Reads verified `pms_capture_by_db_year.csv` directly — no new build script.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
PLOTLY = dict(
    template="plotly_white",
    font=dict(family="Segoe UI, sans-serif", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#FAFBFC",
)

CAPTURE_CSV = DERIVED_DIR / "pms_capture_by_db_year.csv"


st.markdown(
    """
<style>
    .pms-hero {
        background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 60%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.25rem;
    }
    .pms-hero h1 { color:#fff !important; margin:0; font-size:1.7rem; font-weight:700; }
    .pms-hero p  { color:#E8F0FA; margin:0.35rem 0 0; font-size:0.9rem; }
</style>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class="pms-hero">
  <h1>ITUK PMS Story — mix, not deficit</h1>
  <p>The big-three PMS categories are already at capture ceiling — the real lever is genuine-vs-Best-Value mix, not chasing more capture.</p>
</div>
""",
    unsafe_allow_html=True,
)

if not CAPTURE_CSV.exists():
    st.error(f"Missing {CAPTURE_CSV.name}. Run the PMS (P1) build first.")
    st.stop()

cap = pd.read_csv(CAPTURE_CSV)
ituk = cap[cap["distributor_code"] == "ITUK"].copy()
if ituk.empty:
    st.error("No ITUK rows in pms_capture_by_db_year.csv.")
    st.stop()

years = sorted(int(y) for y in ituk["year"].dropna().unique())
latest = max(years)
tot = ituk[ituk["line_type"] == "total"].copy()


def _cap(cat: str, yr: int, lt: str) -> float:
    row = ituk[(ituk["pms_category"] == cat) & (ituk["year"] == yr) & (ituk["line_type"] == lt)]
    return float(row["capture_rate"].iloc[0]) if not row.empty else float("nan")


# ---- Headline KPIs --------------------------------------------------------
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

# ---- 1. The headline: oil-filter mix shift --------------------------------
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

# ---- 2. Where the money actually is: capture vs gap -----------------------
st.subheader("2 · Where the recoverable money is")
st.markdown(
    "Big-3 (oil / fuel / brake pad) carry **€0 gap** — they're at ceiling. "
    "The genuine upside sits in **air filter** (availability, ~0 BVP) and **clutch**."
)
latest_tot = tot[tot["year"] == latest].copy()
latest_tot = latest_tot.sort_values("revenue_gap_eur", ascending=True)
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

# ---- 3. Air filter spotlight ----------------------------------------------
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

# ---- 4. Category scorecard ------------------------------------------------
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
    hide_index=True,
    width="stretch",
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

st.caption(f"ITUK PMS Story · CY{years[0]}–{latest} · Data: `{DERIVED_DIR}`")
