"""PRISM — Early Warning.

One ops page: who do I act on this cycle, and why. Collapses the risk signal
previously scattered across Decision Models -> Defection, Strategic (triple
threat / VOR / geographic) and the Customer Risk page into one ranked list.

Three signals only — silence, capture slope, VOR stress (see
scripts/build_early_warning.py for why those three and not concentration or
price exposure). The page is the list; charts live inside a row's drill-down,
not in tabs.

Source: early_warning.csv + early_warning_signals.csv (build_early_warning.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402
from modules.strategic_build import PMS_CAPTURE_BY_DB_CSV  # noqa: E402

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
ISZE_RED = "#E2231A"
ISZE_GREY = "#9AA0A6"
ISZE_GREEN = "#0E7C66"

SEV_COLOR = {"act": ISZE_RED, "watch": ISZE_ORANGE, "dormant": ISZE_GREY}
SIG_LABEL = {"silence": "Silence", "capture": "Capture", "vor": "VOR"}

st.markdown(
    """
<style>
    .ew-hero { background: linear-gradient(120deg,#1B3A6B 0%,#2C5AA0 55%,#E2231A 100%);
        padding:1.25rem 1.5rem;border-radius:12px;margin-bottom:1.1rem; }
    .ew-hero h1 { color:#fff!important;margin:0;font-size:1.7rem;font-weight:700; }
    .ew-hero p  { color:#E8F0FA;margin:.35rem 0 0;font-size:.9rem; }
    div[data-testid="metric-container"] { border:1px solid #E0E0E0;border-left:4px solid #1B3A6B;
        border-radius:8px;background:#fff; }
    .ew-chip { display:inline-block;padding:1px 8px;border-radius:10px;font-size:.72rem;
        font-weight:600;color:#fff;margin-right:4px; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="ew-hero">
  <h1>Early Warning</h1>
  <p>One list, ranked. Silence · capture slope · VOR stress — who needs a call this cycle, and why.</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading early-warning list…")
def _load() -> tuple[pd.DataFrame, pd.DataFrame]:
    d = Path(DERIVED_DIR)
    ew_fp, sig_fp = d / "early_warning.csv", d / "early_warning_signals.csv"
    if not ew_fp.exists() or not sig_fp.exists():
        return pd.DataFrame(), pd.DataFrame()
    return pd.read_csv(ew_fp), pd.read_csv(sig_fp)


@st.cache_data(show_spinner=False)
def _capture_hist() -> pd.DataFrame:
    pms = pd.read_csv(PMS_CAPTURE_BY_DB_CSV)
    return pms[pms["line_type"] == "total"][
        ["year", "distributor_code", "pms_category", "capture_rate"]
    ]


@st.cache_data(show_spinner=False)
def _vor_hist() -> pd.DataFrame:
    fp = Path(DERIVED_DIR) / "vor_seasonality.csv"
    return pd.read_csv(fp) if fp.exists() else pd.DataFrame()


ew, sig = _load()
if ew.empty:
    st.warning(
        "Early-warning list not built. Run `python scripts/build_early_warning.py` "
        "to generate `early_warning.csv`, then reload."
    )
    st.stop()

meta_cols = [
    "silence_horizon", "dealer_horizon", "vor_horizon",
    "capture_years_used", "capture_years_dropped", "capture_last_complete",
]
meta = {c: (ew[c].iloc[0] if c in ew.columns else "—") for c in meta_cols}

# --------------------------------------------------------------------------
# Honesty banner — the horizons are not "today" and are not all the same
# --------------------------------------------------------------------------
st.info(
    f"**\"This cycle\" = the data horizon, not today.** Distributor billing runs to "
    f"**{meta['silence_horizon']}**; ITUK dealer sell-out is staler at "
    f"**{meta['dealer_horizon']}**; VOR to **{meta['vor_horizon']}**. "
    f"Capture slopes are fitted on complete years **{meta['capture_years_used']}** only — "
    f"the partial year {meta['capture_years_dropped']} is excluded because a part-billed "
    "year reads as a false cliff. € shown is **revenue sitting on the alarming categories "
    "(exposure)** — not a loss, not a leakage estimate."
)

# --------------------------------------------------------------------------
# KPI row
# --------------------------------------------------------------------------
live = ew[ew["severity_name"] != "dormant"]
n_act = int((ew["severity_name"] == "act").sum())
k1, k2, k3, k4 = st.columns(4)
# delta_color="off" throughout: a green ↑ next to "5 watch" or "€605K exposed"
# reads as good news on a page where every number is a problem.
k1.metric("Act now", f"{n_act}",
          f"{int((ew['severity_name']=='watch').sum())} watch", delta_color="off")
k2.metric("€ exposed (live alarms)", f"€{live['eur_exposed'].sum()/1e3:,.0f}K",
          "revenue on alarming categories", delta_color="off")
k3.metric("Top exposure", f"{ew.iloc[0]['entity']}",
          f"€{ew.iloc[0]['eur_exposed']/1e3:,.0f}K", delta_color="off")
k4.metric("Signals fired", f"{len(sig[~sig['dormant']])}",
          f"across {len(ew)} entities", delta_color="off")

# --------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------
f1, f2, f3 = st.columns([1.4, 1.3, 1.6])
with f1:
    sev_pick = st.multiselect(
        "Severity", ["act", "watch", "dormant"], default=["act", "watch"],
        help="Dormant = category silent >12 months with zero revenue. Dead, not defecting.",
    )
with f2:
    lvl_pick = st.multiselect("Level", sorted(ew["level"].unique()),
                              default=sorted(ew["level"].unique()))
with f3:
    sig_pick = st.multiselect(
        "Must have signal", ["silence", "capture", "vor"], default=[],
        help="Empty = any signal. Pick one or more to filter to entities firing them.",
    )

view = ew[ew["severity_name"].isin(sev_pick) & ew["level"].isin(lvl_pick)].copy()
for s in sig_pick:
    view = view[view[f"sig_{s}"] > 0]

if view.empty:
    st.success("No entities match this filter.")
    st.stop()

# --------------------------------------------------------------------------
# The priority list — this page IS this table
# --------------------------------------------------------------------------
st.markdown(f"##### Priority list — {len(view)} entities")

tbl = view[[
    "priority", "entity", "level", "severity_name", "eur_exposed",
    "sig_silence", "sig_capture", "sig_vor", "n_signals",
    "why_this_cycle", "risk_score_context",
]].rename(columns={
    "priority": "#", "entity": "Entity", "level": "Grain", "severity_name": "Severity",
    "eur_exposed": "€ exposed", "sig_silence": "Silence", "sig_capture": "Capture",
    "sig_vor": "VOR", "n_signals": "Signals", "why_this_cycle": "Why this cycle",
    "risk_score_context": "Risk score (context)",
})

st.dataframe(
    tbl, width="stretch", hide_index=True, height=min(560, 60 + 36 * len(tbl)),
    column_config={
        "#": st.column_config.NumberColumn(width="small"),
        "€ exposed": st.column_config.NumberColumn(format="€%.0f", width="small"),
        "Silence": st.column_config.ProgressColumn(
            "Silence", min_value=0, max_value=2, format=" ", width="small"),
        "Capture": st.column_config.ProgressColumn(
            "Capture", min_value=0, max_value=2, format=" ", width="small"),
        "VOR": st.column_config.ProgressColumn(
            "VOR", min_value=0, max_value=2, format=" ", width="small"),
        "Why this cycle": st.column_config.TextColumn(width="large"),
        "Risk score (context)": st.column_config.NumberColumn(
            format="%.0f", width="small",
            help="Customer-Risk weighted index. Context only — never ranks this list.",
        ),
    },
)
st.caption(
    "Signal bars: 0 = ok · 1 = watch · 2 = act. Ranked by severity, then € exposed, then how "
    "many signals agree. Risk score is context (price exposure moves with the scraper, not "
    "with the customer) and never sorts the list."
)

# --------------------------------------------------------------------------
# Drill-down — one entity, its fired signals and the series behind them
# --------------------------------------------------------------------------
st.markdown("##### Drill-down")
pick = st.selectbox(
    "Entity", view["entity"].tolist(),
    format_func=lambda e: (
        f"{int(view.loc[view.entity==e,'priority'].iloc[0])}. {e} — "
        f"{view.loc[view.entity==e,'severity_name'].iloc[0]} · "
        f"€{view.loc[view.entity==e,'eur_exposed'].iloc[0]:,.0f} exposed"
    ),
)

row = view[view["entity"] == pick].iloc[0]
mine = sig[sig["entity"] == pick]

c1, c2, c3 = st.columns([1, 1.2, 2])
c1.metric("Priority", f"#{int(row['priority'])}", row["severity_name"], delta_color="off")
c2.metric("€ exposed", f"€{row['eur_exposed']/1e3:,.1f}K" if row["eur_exposed"] >= 1000
          else f"€{row['eur_exposed']:,.0f}")
c3.metric("Signals firing", ", ".join(sorted(SIG_LABEL[s] for s in mine["signal"].unique())))

for _, s in mine.sort_values(["level_val", "eur"], ascending=False).iterrows():
    icon = {"act": "🔴", "watch": "🟠"}.get(
        {2: "act", 1: "watch"}.get(int(s["level_val"]), ""), "⚪")
    tag = " · dormant" if s["dormant"] else ""
    st.markdown(f"{icon} **{SIG_LABEL[s['signal']]}**{tag} — {s['reason']}")

if row["level"] == "dealer":
    st.caption(
        f"Dealer grain: ITUK sell-out carries no revenue column and its own horizon "
        f"({meta['dealer_horizon']}). Silence is measured against that, and no € is attributed."
    )

# --- capture series for the declining categories ---------------------------
cap_sigs = mine[mine["signal"] == "capture"]
if not cap_sigs.empty:
    hist = _capture_hist()
    dropped_years = {
        int(y) for y in str(meta["capture_years_dropped"]).split(",") if y.strip().isdigit()
    }
    fig = go.Figure()
    for _, s in cap_sigs.iterrows():
        h = hist[
            (hist["distributor_code"] == row["distributor_code"])
            & (hist["pms_category"] == s["pms_category"])
        ].sort_values("year")
        if h.empty:
            continue
        fitted = h[~h["year"].isin(dropped_years)]
        fig.add_trace(go.Scatter(
            x=fitted["year"], y=fitted["capture_rate"], mode="lines+markers",
            name=str(s["pms_category"]).replace("_", " "),
            hovertemplate="%{x}: %{y:.1%}<extra></extra>",
        ))
        excl = h[h["year"].isin(dropped_years)]
        if not excl.empty:
            fig.add_trace(go.Scatter(
                x=excl["year"], y=excl["capture_rate"], mode="markers",
                name=f"{str(s['pms_category']).replace('_',' ')} (partial yr — excluded)",
                marker=dict(symbol="x", size=9, color=ISZE_GREY),
                hovertemplate="%{x}: %{y:.1%} — partial year, not fitted<extra></extra>",
            ))
    fig.update_layout(
        template="plotly_white", font=dict(family="Segoe UI"), height=320,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFC",
        yaxis_tickformat=".0%", yaxis_title="PMS capture rate", xaxis_title="",
        title="Capture trend — declining categories (× = partial year, excluded from fit)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, x=0),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    # Years are integers — without dtick plotly interpolates 2,023.5 ticks.
    fig.update_xaxes(dtick=1, tickformat="d")
    st.plotly_chart(fig, width="stretch")

# --- weekly VOR series -----------------------------------------------------
vh = _vor_hist()
if not vh.empty and row["level"] == "distributor":
    v = vh[vh["distributor_code"] == row["distributor_code"]].copy()
    if not v.empty:
        v["t"] = v["year"] * 100 + v["week_of_year"]
        v = v.sort_values("t").tail(56)
        v["label"] = v["year"].astype(str) + "-W" + v["week_of_year"].astype(str).str.zfill(2)
        recent_cut = v["t"].iloc[-4] if len(v) >= 4 else v["t"].iloc[0]
        colors = [ISZE_RED if t >= recent_cut else ISZE_BLUE for t in v["t"]]
        figv = go.Figure(go.Bar(
            x=v["label"], y=v["vor_pct"], marker_color=colors,
            customdata=v[["vor_count", "total_order_count"]],
            hovertemplate="%{x}<br>VOR %{y:.0%}<br>%{customdata[0]} of %{customdata[1]} orders<extra></extra>",
        ))
        base = v.iloc[:-4]["vor_count"].sum() / max(v.iloc[:-4]["total_order_count"].sum(), 1)
        figv.add_hline(y=base, line_dash="dash", line_color=ISZE_GREY,
                       annotation_text=f"own baseline {base:.0%}", annotation_position="top left")
        figv.update_layout(
            template="plotly_white", font=dict(family="Segoe UI"), height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFC",
            yaxis_tickformat=".0%", yaxis_title="VOR share of orders",
            title="Weekly VOR share — last 56 weeks (red = the 4-week window scored)",
            margin=dict(l=10, r=10, t=40, b=10),
        )
        figv.update_xaxes(showticklabels=False)
        st.plotly_chart(figv, width="stretch")
        st.caption(
            "VOR share is weighted by order count, so a thin week cannot swing the read. "
            "A DB that always ships VOR is not an alarm — only movement against its own "
            "baseline is."
        )

# --------------------------------------------------------------------------
# Export — the whole v1 "alerting stack"
# --------------------------------------------------------------------------
st.markdown("##### Export")
e1, e2 = st.columns(2)
with e1:
    st.download_button(
        f"Download priority list ({len(view)} entities)",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name=f"ISZE_Early_Warning_{meta['silence_horizon']}.csv",
        mime="text/csv", width="stretch",
    )
with e2:
    st.download_button(
        f"Download fired signals ({len(sig)} rows)",
        data=sig.to_csv(index=False).encode("utf-8"),
        file_name=f"ISZE_Early_Warning_signals_{meta['silence_horizon']}.csv",
        mime="text/csv", width="stretch",
    )

st.caption(
    f"Early Warning · horizon {meta['silence_horizon']} (dealer {meta['dealer_horizon']}, "
    f"VOR {meta['vor_horizon']}) · source: early_warning.csv · "
    "Rebuild: `python scripts/build_early_warning.py`"
)
