"""
PRISM — Parts Revenue Intelligence & Sales Monitor
ISZE Analytics Platform — Command Centre (helicopter view)

Single "front door" connecting every intelligence module into one cockpit, plus
a live network heatmap and alert ribbon driven by the verified derived data.

Navigation: st.navigation/st.Page (docs/DASHBOARD_IA.md §6). This entrypoint
runs on every page load — it owns st.set_page_config and the shared banners;
sub-pages under pages/ must not call st.set_page_config themselves.

Theme: Executive Premium (charcoal + gold, serif display).

Run with:
    python -m streamlit run app.py
"""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import streamlit as st

from config import BETA_MODE, DERIVED_DIR, GPS_SPU_BY_DB_CSV, INTERNAL_MODE

st.set_page_config(
    page_title="PRISM | ISZE Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "beta_mode" not in st.session_state:
    st.session_state["beta_mode"] = BETA_MODE

# ─── Navigation map — target IA per docs/DASHBOARD_IA.md §2 ──────────────────
# Phase 1 (nav shell): pages are regrouped into the 9-entry target structure,
# still as separate destinations — the tab-level merges (§4.1-4.5) land in
# later phases. Sections with >1 tile today are the ones still to be merged.
NAV_SECTIONS: list[dict] = [
    {"key": "Early Warning", "accent": "#E2231A",
     "blurb": "Who needs a call this cycle — silence, capture slope, VOR stress.", "tiles": [
        ("pages/0_Early_Warning.py", "🚨", "Early Warning",
         "One ranked list: who to act on, why this cycle, and the € exposed."),
     ]},
    {"key": "Fleet", "accent": "#1B3A6B",
     "blurb": "The denominator under every metric.", "tiles": [
        ("pages/1_UIO.py", "🚛", "UIO — Units in Operation",
         "Fleet size by distributor, model & registration year."),
        ("pages/19_Forecast.py", "📈", "Demand Forecast",
         "P5 baseline — DB × category outlook, backtest WAPE, no LLM."),
     ]},
    {"key": "Spend", "accent": "#2C5AA0",
     "blurb": "Genuine Parts Share: net sales € per truck per year.", "tiles": [
        ("pages/2_GPS.py", "📊", "GPS — Spend per Unit",
         "Genuine Parts Share: net sales € per truck per year."),
     ]},
    {"key": "Capture", "accent": "#2C5AA0",
     "blurb": "Service-PN capture vs expected demand from surviving parc.", "tiles": [
        ("pages/3_PMS.py", "🔧", "PMS — Capture Rate",
         "Service-PN capture vs expected demand from surviving parc."),
     ]},
    {"key": "Mix", "accent": "#B5651D",
     "blurb": "Genuine vs Best Value — the second line: capture more parc, defend on price.", "tiles": [
        ("pages/4_BVP.py", "⚡", "BVP Intelligence",
         "Genuine vs Best Value mix and substitution — capture/GPS/AIM live on their pages."),
        ("pages/13_DB_Parts_Mix.py", "🧩", "DB Parts Mix",
         "Per-distributor genuine / contested / BVP split."),
     ]},
    {"key": "Network Intelligence", "accent": "#E87722",
     "blurb": "Where revenue and risk concentrate across the network.", "tiles": [
        ("pages/5_Insights.py", "🧠", "Cross-Module Insights",
         "GPS × PMS × BVP signals fused across distributors & time."),
        ("pages/5_Strategic.py", "🎯", "Strategic Views · 13",
         "Capture, stockouts, premium and aftermarket — Early Warning is the call list."),
        ("pages/12_Offset_Insights.py", "🔀", "Offset Insights",
         "Movement, airfreight lumpiness, VOR power, capture ceiling."),
        ("pages/15_Customer_Risk.py", "⚠️", "Customer Risk Ranking",
         "Unvalidated intensity ranking — Early Warning is the call list."),
        ("pages/7_AIM_Review.py", "💶", "AIM Risk Review",
         "AIM classification & pricing-risk exposure by family."),
        ("pages/16_AIM_GPS_Matrix.py", "📐", "AIM × GPS Matrix",
         "Defend vs grow: spend per unit vs PMS capture quadrant."),
        ("pages/8_ASP_Monitor.py", "📉", "ASP Deviation Monitor",
         "Average selling-price drift vs benchmark."),
     ]},
    {"key": "ITUK", "accent": "#8E2DE2",
     "blurb": "The mix-not-capture story, with the receipts.", "tiles": [
        ("pages/11_ITUK_PMS_Story.py", "📖", "ITUK PMS Story",
         "The mix-not-capture narrative for ITUK's PMS book."),
        ("pages/6_ITUK_PMS_Audit.py", "🔍", "ITUK PMS PN Audit",
         "Line-level part-number audit behind the story."),
     ]},
    {"key": "Decision", "accent": "#0E7C66",
     "blurb": "MD-safe: the € identity and the runway. Defection lives on Early Warning.", "tiles": [
        ("pages/18_Decision_Models.py", "🧭", "Decision Models",
         "€ Waterfall · Revenue Runway."),
     ]},
    {"key": "Tools", "accent": "#555F6E",
     "blurb": "Generators and pipeline governance — collapsed by default.", "tiles": [
        ("pages/9_Review_Pack.py", "📦", "Review Pack",
         "Full distributor review pack for QBR meetings (incl. one-page scorecard)."),
        ("pages/6_Scorecard.py", "🏆", "Distributor Scorecard",
         "One-page performance scorecard PDF per distributor."),
        ("pages/14_Tender_Pipeline.py", "📋", "Tender Pipeline",
         "Fleet R&M tender opportunities by distributor."),
        ("pages/10_Data_Integrity.py", "🛡️", "Data Integrity",
         "Pipeline checks & cross-system distributor reconciliation."),
     ]},
]

TOTAL_MODULES = sum(len(s["tiles"]) for s in NAV_SECTIONS)

LIGHT_COLOR = {"green": "#1f9d6b", "amber": "#d99e2b", "red": "#c0392b", "unknown": "#9aa0aa"}

# Not ISZE distributors — kept out of the network view (TURKEY is a €35 / 0-unit
# noise row, documented as a non-distributor). Edit here to adjust the network scope.
EXCLUDE_DB = {"TURKEY"}


# ─── Live data — real numbers only, defensive on every read ──────────────────
@st.cache_data(show_spinner=False)
def load_intel() -> dict:
    out = {
        "distributors": "—", "latest_year": "—", "network_sales": "—",
        "data_checks": "—", "checks_ok": None,
        "heatmap": [], "counts": {}, "amber_names": [], "red_names": [],
    }
    try:
        gps = pd.read_csv(GPS_SPU_BY_DB_CSV)
        if "year" in gps and gps["year"].notna().any():
            latest = int(gps["year"].dropna().max())
            out["latest_year"] = str(latest)
            g = gps[(gps["year"] == latest) & (~gps["distributor_code"].isin(EXCLUDE_DB))].copy()
            out["distributors"] = str(g["distributor_code"].nunique())
            if "total_sales_eur" in g:
                tot = g["total_sales_eur"].sum()
                if tot:
                    out["network_sales"] = f"€{tot / 1_000_000:,.1f}M"
            tl = g.get("traffic_light")
            if tl is not None:
                out["counts"] = g["traffic_light"].value_counts().to_dict()
                out["amber_names"] = sorted(g.loc[g.traffic_light == "amber", "distributor_code"].tolist())
                out["red_names"] = sorted(g.loc[g.traffic_light == "red", "distributor_code"].tolist())
            rows = []
            def _num(v):
                return 0.0 if pd.isna(v) else float(v)
            for _, r in g.sort_values("total_sales_eur", ascending=False).iterrows():
                rows.append({
                    "code": str(r["distributor_code"]),
                    "spu": _num(r.get("spend_per_unit_eur")),
                    "sales": _num(r.get("total_sales_eur")),
                    "light": str(r.get("traffic_light") or "unknown"),
                })
            out["heatmap"] = rows
    except Exception:
        pass

    try:
        report = DERIVED_DIR / "_verification_report.json"
        if report.exists():
            s = json.loads(report.read_text(encoding="utf-8")).get("summary", {})
            p, w, f = s.get("pass", 0), s.get("warn", 0), s.get("fail", 0)
            out["data_checks"] = f"{p}/{p + w + f}"
            out["checks_ok"] = bool(s.get("ok", f == 0))
    except Exception:
        pass

    return out


def render_home() -> None:
    intel = load_intel()
    c = intel["counts"]

    # ─── Styling — Executive Premium ──────────────────────────────────────
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root { --char:#222018; --gold:#c9a227; --paper:#f7f6f3; --ink:#222018; --muted:#8a8678; }
    .stApp { background:var(--paper); }
    html, body, [class*="css"] { font-family:'Inter',system-ui,sans-serif; color:var(--ink); }
    .block-container { padding-top:1.4rem; max-width:1320px; }
    h1,h2,h3 { font-family:'Playfair Display',serif; }

    /* Hero */
    .hero { background:var(--char); color:#fff; border-radius:14px; padding:2.4rem 2.6rem; position:relative;
            box-shadow:0 24px 60px -34px rgba(34,32,24,.7); overflow:hidden; }
    .hero::before { content:""; position:absolute; left:0; top:1.8rem; bottom:1.8rem; width:3px; background:var(--gold); }
    .hero .eb { font:600 12px Inter; letter-spacing:.24em; text-transform:uppercase; color:var(--gold); padding-left:1.4rem; }
    .hero h1 { color:#fff; font-size:3.1rem; font-weight:800; margin:.3rem 0 0; padding-left:1.4rem; letter-spacing:.01em; }
    .hero h1 span { color:var(--gold); }
    .hero p { color:#b8b4a8; font-size:1.0rem; margin:.6rem 0 0; max-width:640px; padding-left:1.4rem; }
    .hero .meta { color:#7d7a6f; font-size:.78rem; margin-top:1rem; padding-left:1.4rem; letter-spacing:.02em; }

    /* KPI strip */
    .kpi-row { display:grid; grid-template-columns:repeat(5,1fr); gap:1rem; margin:1.3rem 0 1.4rem; }
    .kpi { background:#fff; border:1px solid #e8e4da; border-top:3px solid var(--gold); border-radius:8px; padding:1.05rem 1.2rem; }
    .kpi .v { font-family:'Playfair Display',serif; font-size:1.85rem; font-weight:800; color:var(--char); line-height:1.05; }
    .kpi .l { font-size:.68rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); margin-top:.35rem; }
    .kpi .ok { color:#1f9d6b; } .kpi .bad { color:#c0392b; }

    /* Alert ribbon */
    .ribbon { display:flex; gap:.7rem; flex-wrap:wrap; margin:0 0 1.6rem; }
    .chip { display:flex; align-items:center; gap:.5rem; background:#fff; border:1px solid #e8e4da;
            border-left:4px solid var(--gold); border-radius:8px; padding:.55rem .9rem; font-size:.86rem; }
    .chip b { color:var(--char); } .chip .m { color:var(--muted); }
    .chip.green { border-left-color:#1f9d6b; } .chip.amber { border-left-color:#d99e2b; } .chip.red { border-left-color:#c0392b; }

    /* Heatmap */
    .hm-head { display:flex; align-items:baseline; gap:.7rem; margin:.4rem 0 .8rem; }
    .hm-head h3 { font-size:1.25rem; font-weight:800; margin:0; }
    .hm-head span { font-size:.82rem; color:var(--muted); }
    .legend { margin-left:auto; font-size:.74rem; color:var(--muted); display:flex; gap:.9rem; align-items:center; }
    .legend i { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:.3rem; vertical-align:middle; }
    .heat { display:grid; grid-template-columns:repeat(6,1fr); gap:.6rem; margin-bottom:1.8rem; }
    .cell { background:#fff; border:1px solid #e8e4da; border-radius:10px; padding:.7rem .8rem; position:relative; overflow:hidden; }
    .cell::before { content:""; position:absolute; left:0; top:0; bottom:0; width:5px; }
    .cell .code { font-weight:700; font-size:.92rem; color:var(--char); }
    .cell .spu { font-family:'Playfair Display',serif; font-weight:800; font-size:1.15rem; color:var(--char); margin-top:.15rem; }
    .cell .sub { font-size:.68rem; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }
    .cell .sales { font-size:.74rem; color:var(--muted); margin-top:.2rem; }

    /* Section headers + tiles */
    .sec { display:flex; align-items:center; gap:.75rem; margin:1.6rem 0 .85rem; }
    .sec .bar { width:4px; height:28px; border-radius:4px; background:var(--gold); }
    .sec .h { font-family:'Playfair Display',serif; font-size:1.25rem; font-weight:700; color:var(--char); margin:0; }
    .sec .b { font-size:.82rem; color:var(--muted); margin:0; }
    .sec .badge { margin-left:auto; font-size:.7rem; font-weight:600; border:1px solid #d8d2c4; color:var(--muted); border-radius:999px; padding:.2rem .7rem; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius:10px !important; border:1px solid #e8e4da !important; background:#fff; transition:all .16s ease; height:100%;
        box-shadow:0 6px 18px -16px rgba(34,32,24,.5); }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform:translateY(-3px); border-color:var(--gold) !important; box-shadow:0 16px 34px -20px rgba(201,162,39,.55); }
    a[data-testid="stPageLink-NavLink"] { font-family:'Playfair Display',serif; font-weight:700 !important; font-size:1.04rem !important; color:var(--char) !important; padding:.2rem 0 !important; }
    a[data-testid="stPageLink-NavLink"]:hover { color:var(--gold) !important; background:transparent !important; }
    .tile-desc { color:var(--muted); font-size:.82rem; line-height:1.35; margin:.05rem 0 .15rem; }
</style>
""",
        unsafe_allow_html=True,
    )

    if BETA_MODE:
        st.warning("BETA MODE — running against beta UIO file. Not for distribution.", icon="⚠️")
    if INTERNAL_MODE:
        st.info(
            "INTERNAL MODE — extra tabs visible: attach, ITUK leakage, elasticity, "
            "demand-flow, aftermarket scrape.",
            icon="🔒",
        )

    # ─── Hero ──────────────────────────────────────────────────────────────
    today = datetime.now().strftime("%d %b %Y")
    st.markdown(
        f"""
<div class="hero">
  <div class="eb">ISZE · Isuzu Parts Intelligence</div>
  <h1>PR<span>I</span>SM</h1>
  <p>Parts Revenue Intelligence &amp; Sales Monitor — one helicopter view over the entire
     Isuzu aftersales network. Live signals up top; every module one click away.</p>
  <div class="meta">🛰️ {TOTAL_MODULES} modules · UIO → GPS → PMS → BVP → Network Intelligence · {today}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ─── KPI strip ─────────────────────────────────────────────────────────
    checks_cls = "ok" if intel["checks_ok"] else ("bad" if intel["checks_ok"] is False else "")
    checks_txt = f"{intel['data_checks']} green" if intel["checks_ok"] else intel["data_checks"]
    st.markdown(
        f"""
<div class="kpi-row">
  <div class="kpi"><div class="v">{intel['distributors']}</div><div class="l">Distributors covered</div></div>
  <div class="kpi"><div class="v">{intel['network_sales']}</div><div class="l">Network net sales · FY{intel['latest_year']}</div></div>
  <div class="kpi"><div class="v">{TOTAL_MODULES}</div><div class="l">Intelligence modules</div></div>
  <div class="kpi"><div class="v {checks_cls}">{checks_txt}</div><div class="l">Data integrity checks</div></div>
  <div class="kpi"><div class="v">{intel['latest_year']}</div><div class="l">Latest data year</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ─── Alert ribbon (computed signals only) ─────────────────────────────
    chips = []
    if intel["checks_ok"]:
        chips.append(f'<div class="chip green">🟢 <b>Data integrity</b> <span class="m">{intel["data_checks"]} checks green</span></div>')
    if c.get("green"):
        chips.append(f'<div class="chip green">🟢 <b>{c["green"]} green</b> <span class="m">on GPS spend-per-unit</span></div>')
    if intel["amber_names"]:
        names = ", ".join(intel["amber_names"])
        chips.append(f'<div class="chip amber">🟠 <b>{len(intel["amber_names"])} amber</b> <span class="m">GPS — {names}</span></div>')
    if intel["red_names"]:
        names = ", ".join(intel["red_names"])
        chips.append(f'<div class="chip red">🔴 <b>{len(intel["red_names"])} red</b> <span class="m">GPS — {names}</span></div>')
    if c.get("unknown"):
        chips.append(f'<div class="chip">⚪ <b>{c["unknown"]} unverified</b> <span class="m">no UIO actuals yet</span></div>')
    if chips:
        st.markdown(f'<div class="ribbon">{"".join(chips)}</div>', unsafe_allow_html=True)

    # ─── Network heatmap (real GPS traffic-light per distributor) ─────────
    if intel["heatmap"]:
        st.markdown(
            f"""
<div class="hm-head">
  <h3>Network at a glance</h3>
  <span>GPS spend-per-unit traffic-light · {len(intel['heatmap'])} distributors · FY{intel['latest_year']}</span>
  <span class="legend">
    <span><i style="background:#1f9d6b"></i>green</span>
    <span><i style="background:#d99e2b"></i>amber</span>
    <span><i style="background:#c0392b"></i>red</span>
    <span><i style="background:#9aa0aa"></i>unverified</span>
  </span>
</div>
""",
            unsafe_allow_html=True,
        )
        heat_html = '<div class="heat">' + "".join(
            f'<div class="cell"><div style="position:absolute;left:0;top:0;bottom:0;width:5px;background:{LIGHT_COLOR.get(r["light"], "#9aa0aa")}"></div>'
            f'<div class="code">{r["code"]}</div>'
            f'<div class="spu">{("€%s" % format(int(r["spu"]), ",")) if r["spu"] else "—"}</div>'
            f'<div class="sub">€ / unit · yr</div>'
            f'<div class="sales">{("€%.2fM" % (r["sales"]/1e6)) if r["sales"]>=1e6 else ("€%sk" % format(int(r["sales"]/1000), ","))} net sales</div>'
            f'</div>'
            for r in intel["heatmap"]
        ) + '</div>'
        st.markdown(heat_html, unsafe_allow_html=True)

    # ─── Cockpit grid ──────────────────────────────────────────────────────
    for sec in NAV_SECTIONS:
        st.markdown(
            f"""
<div class="sec">
  <div class="bar"></div>
  <div><p class="h">{sec['key']}</p><p class="b">{sec['blurb']}</p></div>
  <span class="badge">{len(sec['tiles'])} {'module' if len(sec['tiles']) == 1 else 'modules'}</span>
</div>
""",
            unsafe_allow_html=True,
        )
        tiles = sec["tiles"]
        cols = st.columns(min(len(tiles), 4), gap="medium")
        for i, (path, icon, title, desc) in enumerate(tiles):
            with cols[i % 4]:
                with st.container(border=True):
                    st.page_link(path, label=title, icon=icon)
                    st.markdown(f"<p class='tile-desc'>{desc}</p>", unsafe_allow_html=True)

    st.divider()
    st.caption(
        f"PRISM · ISZE Parts Revenue Intelligence · data: `{DERIVED_DIR}` · "
        "rebuild: `python scripts/build_strategic_contracts.py`"
    )


# ─── Navigation registration ──────────────────────────────────────────────
nav_map: dict[str, list[st.Page]] = {
    "": [st.Page(render_home, title="Home", icon="🛰️", default=True)],
}
for sec in NAV_SECTIONS:
    nav_map[sec["key"]] = [
        st.Page(path, title=title, icon=icon) for path, icon, title, _ in sec["tiles"]
    ]

nav = st.navigation(nav_map, position="sidebar", expanded=True)

with st.sidebar:
    st.markdown("## 🛰️ PRISM")
    st.caption("Parts Revenue Intelligence & Sales Monitor")
    st.badge("v2.0-beta" if BETA_MODE else "v2.0", color="orange" if BETA_MODE else "blue")

nav.run()
