# -*- coding: utf-8 -*-
"""Build Don't Lose the Deal feasibility HTML from the 2026-10-08 study numbers."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ROOT / "Isuzu Universe" / "01_Strategy"
HTML_NAME = "DLOD_NETWORK_FEASIBILITY_2026-10-08.html"
CMD_NAME = "OPEN_DLOD_NETWORK_FEASIBILITY_2026-10-08.cmd"
CHART_EXTRACT = ROOT / "01_data" / "90_INBOX" / "_tmp_chart_umd_extract.js.html"
REF_HTML = ROOT / "02_dashboards" / "pricing" / "ISZE_Pricing_Revision_AIM_Source.html"

PAYLOAD = {
    "as_of": "2026-10-08",
    "programme": "Don't Lose the Deal",
    "moa_path": r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\FY26_ITUK_DLOD_2026-03.docx.pdf",
    "moa_summary": "ISZE pays ITUK EUR 30,000 for Don't Lose the Deal if ITUK provides the activity record. No margin/%GM in the agreement.",
    "isze_gp_pct_yoshimoto": 50,
    "ituk_normal_margin_pct": 47,
    "ituk_retained_margin_band": "41-43",
    "fy_window": "FY2026 = 1 Apr 2025 – 31 Mar 2026",
    "verdict": (
        "Don't Lose the Deal is already a real UK programme with a case register, "
        "a measured support total, and an intentional ISZE opex line of EUR 30,000 "
        "for ITUK — including in the FY27 budget. Scaling is feasible if Japan "
        "approves an annual envelope and markets copy ITUK's deal-file discipline."
    ),
    "kpis": {
        "ituk_support_gbp": 54921.79,
        "regional_cases": 218,
        "cases_by_region": {"North": 170, "South West": 33, "South East": 15},
        "isze_credit_eur": 30000,
        "ituk_fy2026_billed_eur": 6957525,
        "pct05_ituk_eur": 34788,
        "network_fy2026_billed_eur": 32582306,
        "pct05_network_eur": 162912,
        "competitor_price_filled": {"filled": 1, "of": 218},
        "pilot_envelope_eur_lo": 70000,
        "pilot_envelope_eur_hi": 80000,
        "median_unit_support_gbp": 86,
        "avg_unit_support_gbp": 172,
        "p90_unit_support_gbp": 505,
        "median_retained_margin_pct": 43,
        "avg_retained_margin_pct": 41,
        "ituk_credit_as_pct_billed": 0.43,
    },
    "region_support_gbp": [
        {"region": "Northern Region", "support_gbp": 26689.58, "cases": 170},
        {"region": "Fleet Support", "support_gbp": 14878.95, "cases": None},
        {"region": "South West", "support_gbp": 9466.25, "cases": 33},
        {"region": "South East", "support_gbp": 3887.01, "cases": 15},
    ],
    "envelopes": [
        {"db": "ITUK", "billed_eur": 6957525, "env_eur": 34788, "note": "Live; budget EUR 30k"},
        {"db": "IUK", "billed_eur": 6048309, "env_eur": 30242, "note": "Pilot next"},
        {"db": "UTI", "billed_eur": 3242540, "env_eur": 16213, "note": "Never blend with UMI"},
        {"db": "UMI", "billed_eur": 3079678, "env_eur": 15398, "note": "IDS Israel = UMI only"},
        {"db": "Germany", "billed_eur": 2731950, "env_eur": 13660, "note": "Wait"},
        {"db": "Belgium", "billed_eur": 2203112, "env_eur": 11016, "note": "Wait"},
        {"db": "Portugal", "billed_eur": 1853613, "env_eur": 9268, "note": "Pilot candidate"},
        {"db": "Norway", "billed_eur": 1653639, "env_eur": 8268, "note": "Wait"},
        {"db": "Sweden", "billed_eur": 1438426, "env_eur": 7192, "note": "Wait"},
        {"db": "Ireland", "billed_eur": 1145257, "env_eur": 5726, "note": "Pilot candidate"},
        {"db": "Greece", "billed_eur": 471586, "env_eur": 2358, "note": "Wait"},
        {"db": "Cyprus", "billed_eur": 412224, "env_eur": 2061, "note": "Skip unless Japan insists"},
        {"db": "Hungary", "billed_eur": 349882, "env_eur": 1749, "note": "Wait"},
        {"db": "Finland", "billed_eur": 328901, "env_eur": 1645, "note": "Wait"},
        {"db": "Malta", "billed_eur": 205187, "env_eur": 1026, "note": "Skip unless Japan insists"},
        {"db": "Romania", "billed_eur": 189715, "env_eur": 949, "note": "Wait"},
        {"db": "Denmark", "billed_eur": 180803, "env_eur": 904, "note": "Wait"},
        {"db": "Iceland", "billed_eur": 89959, "env_eur": 450, "note": "Wait"},
    ],
    "pilot_vs_full": [
        {"label": "Pilot ask (ITUK + IUK + one market)", "eur": 75000, "kind": "pilot"},
        {"label": "Full-book 0.5% (18 distributors)", "eur": 162912, "kind": "full"},
        {"label": "Sep 23 flat EUR 30k × 19 (not recommended)", "eur": 570000, "kind": "old"},
    ],
    "scorecard": [
        {"db": "ITUK", "data": 5, "network": 5, "pressure": 5, "register": "Already has Duncan file", "pilot": "Continue — template"},
        {"db": "IUK", "data": 5, "network": 5, "pressure": 4, "register": "No register yet", "pilot": "Pilot next"},
        {"db": "Ireland", "data": 4, "network": 3, "pressure": 3, "register": "No", "pilot": "Pilot candidate"},
        {"db": "Portugal", "data": 3, "network": 3, "pressure": 3, "register": "No", "pilot": "Pilot candidate"},
        {"db": "UTI", "data": 4, "network": 3, "pressure": 3, "register": "No — own register only", "pilot": "Wait / separate"},
        {"db": "UMI", "data": 4, "network": 4, "pressure": 3, "register": "No — never with UTI", "pilot": "Wait / separate"},
        {"db": "Greece", "data": 3, "network": 4, "pressure": 3, "register": "No; StD months limited", "pilot": "Wait"},
        {"db": "Belgium", "data": 2, "network": 4, "pressure": 3, "register": "No", "pilot": "Wait"},
        {"db": "Germany", "data": 2, "network": 3, "pressure": 3, "register": "No", "pilot": "Wait"},
        {"db": "Nordics (NO/SE/FI/DK/IS)", "data": 2, "network": 3, "pressure": 2, "register": "No", "pilot": "Wait — tiny envelopes"},
        {"db": "Hungary / Romania", "data": 2, "network": 3, "pressure": 2, "register": "No", "pilot": "Wait"},
        {"db": "Cyprus / Malta", "data": 1, "network": 1, "pressure": 2, "register": "No", "pilot": "Skip unless Japan insists"},
    ],
    "unknowns": [
        "True win rate (won/lost not systematically logged to SAP order refs).",
        "Competitor Price blank on 217 of 218 regional lines — proof gap.",
        "Exact fleet-table row count behind the GBP 14,879 fleet block.",
        "Memorandum text on disk not re-found.",
        "Whether the Yoshimoto-facing PMS brake proposal is framed as SPA, Don't Lose the Deal, or both.",
        "MIDI inclusion in the P&L reserve vs operating ownership (MIDI is out-of-book for this owner's pilot).",
        "Japan willingness to delegate case approval inside an annual envelope.",
        "Local competition-law advice per market.",
        "Loyalty score lift — soft return; no fake euro attached.",
        "True incremental retention vs jobs that would have been won anyway (year-two question).",
    ],
    "top_dealers_support_gbp": [
        {"dealer": "WVC", "support_gbp": 5627},
        {"dealer": "CTC", "support_gbp": 4182},
        {"dealer": "JDS Manchester", "support_gbp": 3743},
    ],
    "sources": [
        r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\DLOD_NETWORK_FEASIBILITY_2026-10-08.md",
        r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\DLOD_NETWORK_ROLLOUT_2026-09-23.md",
        r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ituk_std_mail_hunt_20260903\pulled_attachments\2026-03-10_1026_Duncan_DLAD - All regions 2026 Overall.xlsx",
        r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\distributor_dimension.csv",
        r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\order_headers_from_Order_Detail.csv",
        r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_dlad_extract_20261008.json",
    ],
}

CSS = r"""
:root{
  --navy:#15233c; --navy2:#1d3054; --terra:#c0552d; --paper:#f7f4ee;
  --ink:#222; --muted:#6b6459; --line:#d9d3c8; --band:#eef3f9;
  --good:#1e6b4f; --amber:#a8721f; --amber-bg:#fdf3e3; --amber-bd:#e6cf9f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  font-size:14px;line-height:1.5}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
h1{font-size:26px;letter-spacing:-.2px}
h2{font-size:18px;margin-bottom:4px}
h3{font-size:15px}
.wrap{max-width:1180px;margin:0 auto;padding:22px 22px 56px}
header.top{border-bottom:3px solid var(--navy);padding-bottom:14px;margin-bottom:18px}
.sub{color:var(--muted);font-size:13px;margin-top:8px;max-width:920px}
.badge{display:inline-block;background:var(--navy);color:var(--paper);
  font-size:11px;letter-spacing:.6px;text-transform:uppercase;
  padding:3px 9px;border-radius:2px;margin-right:8px}
.badge.terra{background:var(--terra)}
.verdict{background:#fff;border:1px solid var(--line);border-left:4px solid var(--terra);
  padding:14px 16px;margin-bottom:18px}
.verdict p{margin:0;font-size:15px;line-height:1.55;color:var(--ink)}
.verdict .ask{margin-top:10px;font-size:13.5px;color:var(--navy)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));
  gap:12px;margin-bottom:20px}
.kpi{background:#fff;border:1px solid var(--line);padding:13px 15px;position:relative;
  border-top:3px solid var(--navy)}
.kpi.t{border-top-color:var(--terra)}
.kpi.a{border-top-color:var(--amber)}
.kpi .lab{font-size:11px;letter-spacing:.55px;text-transform:uppercase;color:var(--muted);
  display:flex;align-items:center;gap:5px}
.kpi .val{font-size:22px;font-weight:600;color:var(--navy);margin-top:5px;
  font-variant-numeric:tabular-nums}
.kpi .note{font-size:11.5px;color:var(--muted);margin-top:3px}
.info{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;
  border-radius:50%;background:var(--navy);color:#fff;font-size:9.5px;cursor:help;
  position:relative;flex:0 0 auto}
.info .tip{display:none;position:absolute;bottom:22px;left:50%;transform:translateX(-50%);
  width:280px;background:var(--navy);color:var(--paper);font-size:12px;line-height:1.45;
  padding:9px 11px;border-radius:3px;z-index:60;text-transform:none;letter-spacing:0;
  font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25);text-align:left}
.info .tip b{color:#f0b49a}
.info:hover .tip,.info:focus .tip{display:block}
.grid{display:grid;gap:16px;margin-bottom:18px}
.g2{grid-template-columns:1fr 1fr}
@media(max-width:900px){.g2{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);padding:15px 16px 14px}
.card .q{font-size:13px;color:var(--muted);margin:2px 0 12px}
.chartbox{position:relative;height:320px}
.chartbox.short{height:240px}
.chartbox.tall{height:420px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;
  font-weight:600;font-size:11.5px;letter-spacing:.35px;text-transform:uppercase}
th.n,td.n{text-align:right;font-variant-numeric:tabular-nums}
td{padding:7px 9px;border-bottom:1px solid var(--line);color:var(--ink)}
tbody tr:nth-child(even){background:var(--band)}
.tblwrap{max-height:440px;overflow:auto;border:1px solid var(--line)}
.warn{background:var(--amber-bg);border:1px solid var(--amber-bd);border-left:4px solid var(--amber);
  padding:12px 14px;font-size:13px;color:#5e4a1c;margin-bottom:18px}
.warn h3{color:var(--amber);margin-bottom:6px}
.warn ul{margin:6px 0 0;padding-left:18px}
.warn li{margin:3px 0}
.tag{display:inline-block;font-size:10.5px;letter-spacing:.4px;text-transform:uppercase;
  padding:2px 7px;border-radius:2px;margin-left:6px;vertical-align:middle}
.tag.m{background:#dce8df;color:var(--good)}
.tag.p{background:#e8e0d4;color:#6b5340}
.tag.u{background:var(--amber-bg);color:var(--amber)}
.pillrow{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 0}
.pill{background:var(--paper);border:1px solid var(--line);padding:6px 10px;font-size:12.5px}
.pill b{color:var(--navy)}
.sec{margin:22px 0 8px}
.route{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-top:10px}
.step{background:#fff;border:1px solid var(--line);border-top:3px solid var(--navy);padding:12px 13px}
.step.now{border-top-color:var(--terra)}
.step .n{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.step .t{font-family:Georgia,serif;color:var(--navy);font-size:15px;margin:4px 0 6px}
.step .d{font-size:12.5px;color:var(--ink)}
.foot{font-size:12px;color:var(--muted);border-top:1px solid var(--line);
  padding-top:12px;margin-top:28px}
.foot code{font-size:11px;word-break:break-all;display:block;margin:2px 0}
.mech{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px}
@media(max-width:800px){.mech{grid-template-columns:1fr}}
.mech .box{background:#fff;border:1px solid var(--line);padding:12px}
.mech .who{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.mech .what{font-size:13.5px;margin-top:4px;color:var(--ink)}
"""

BODY = r"""
<div class="wrap">
<header class="top">
  <div>
    <span class="badge">Don't Lose the Deal</span>
    <span class="badge terra">Internal feasibility</span>
    <span class="badge">As of 8 Oct 2026</span>
  </div>
  <h1 style="margin-top:10px">Network feasibility — can this scale past ITUK?</h1>
  <div class="sub">Case-by-case support when a workshop job is about to walk to an independent quote.
    Not a catalogue price change and not a standing SPA. Programme name locked: Don't Lose the Deal
    (DLOD / DLAD spelling variants in SAP). FY language. Euros first.</div>
</header>

<section class="verdict">
  <p id="verdict-text"></p>
  <p class="ask"><b>Ask for next week (Proposed):</b> confirm FY27 ITUK <b>EUR 30,000</b> stays in budget,
    and approve a pilot reserve of about <b>EUR 70–80k</b> (ITUK already counted + IUK ~EUR 30k + Ireland or Portugal),
    with local case approval inside the envelope and a mandatory case register.
    Full-book 0.5% (~EUR 163k) stays a later option.</p>
</section>

<div class="kpis" id="kpis"></div>

<div class="warn" id="competitor-gap">
  <h3>Competitor-proof gap — Measured</h3>
  <p style="margin:0">Only <b>1 of 218</b> regional deal lines has Competitor Price filled.
    The deal file proves the programme runs; it does not yet prove each job was under a documented rival quote.
    Any pilot must require competitor evidence (or a typed reason code) before support above a threshold.</p>
</div>

<div class="sec">
<div class="card" style="margin-bottom:18px">
  <h2>Authority — MOA and margin layers</h2>
  <p class="q">Signed agreement vs mail vs Duncan register — do not blend</p>
  <table>
    <thead><tr><th>Layer</th><th>Figure / rule</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td>Signed MOA</td><td>EUR 30,000 if ITUK provides the activity record. <b>No margin / %GM</b> in the agreement.</td><td>FY26_ITUK_DLOD_2026-03.docx.pdf</td></tr>
      <tr><td>ISZE GP on programme deals</td><td>~50%</td><td>Jerome → Yoshimoto (Mar 2026 DocuSign thread)</td></tr>
      <tr><td>ITUK normal / retained</td><td>~47% before offer · ~41–43% median after</td><td>Duncan deal file</td></tr>
    </tbody>
  </table>
</div>
<h2>How the money moves</h2>
  <p class="q" style="color:var(--muted);margin:4px 0 0">Three layers — ISZE co-funds; it does not pay 100% of every deal line.</p>
</div>
<div class="mech">
  <div class="box"><div class="who">Dealer</div><div class="what">Sells at a defended price; keeps retained margin on the offer (~41–43% median on regional lines). Normal margin before offer ~47%. Nothing below cost.</div></div>
  <div class="box"><div class="who">ITUK</div><div class="what">Funds Normal DN minus Offer to dealer × qty. Duncan Overall Summary: <b>£54,922</b> total support.</div></div>
  <div class="box"><div class="who">ISZE</div><div class="what">Refunds via CR / rebate (~<b>EUR 30,000</b> documents). Same figure is an intentional FY27 budget line.</div></div>
</div>
<div class="pillrow">
  <div class="pill">Median unit support <b>£86</b></div>
  <div class="pill">Average <b>£172</b> <span class="tag p">skew</span></div>
  <div class="pill">Normal margin before offer <b>~47%</b></div>
  <div class="pill">Retained after offer <b>~41–43%</b> median</div>
  <div class="pill">Below cost <b>none</b></div>
  <div class="pill">P90 <b>£505</b></div>
  <div class="pill">ITUK EUR 30k = <b>0.43%</b> of FY2026 parts billed</div>
  <div class="pill">0.5% of ITUK billed = <b>EUR 34,788</b> <span class="tag p">Proposed</span></div>
</div>

<div class="grid g2" style="margin-top:18px">
  <div class="card">
    <h2>Where did ITUK support land?</h2>
    <div class="q">ITUK support by region / fleet — Duncan Overall Summary (GBP), Measured</div>
    <div class="chartbox"><canvas id="chartRegion"></canvas></div>
  </div>
  <div class="card">
    <h2>Pilot ask vs full-book envelope</h2>
    <div class="q">Proposed next ask (~EUR 70–80k) vs 0.5% of 18-distributor billed vs old flat EUR 30k × 19</div>
    <div class="chartbox short"><canvas id="chartPilot"></canvas></div>
  </div>
</div>

<div class="card" style="margin-bottom:18px">
  <h2>If every book market capped at 0.5% of FY2026 parts billed</h2>
  <div class="q">Envelope = 0.5% × fy2026_net_sales_eur from distributor_dimension (network rows). Cap / reserve — not a spend promise. MIDI out of primary table.</div>
  <div class="chartbox tall"><canvas id="chartEnv"></canvas></div>
</div>

<div class="sec"><h2>Recommended route</h2></div>
<div class="route">
  <div class="step now"><div class="n">1 · Now</div><div class="t">Harden ITUK</div><div class="d">Keep FY27 EUR 30,000. Enforce competitor price + outcome + order ref. Monthly claim pack that reconciles Duncan support to the ISZE credit.</div></div>
  <div class="step"><div class="n">2 · Next</div><div class="t">Pilot IUK</div><div class="d">Same Excel template, separate envelope ~EUR 30,000 (0.5% of FY2026 billed). IUK and ITUK pots never mixed.</div></div>
  <div class="step"><div class="n">3 · Prove outside UK</div><div class="t">Ireland or Portugal</div><div class="d">Ireland ~EUR 5.7k or Portugal ~EUR 9.3k at 0.5%. Sales-to-dealer files exist for later before/after reads.</div></div>
  <div class="step"><div class="n">4 · Later</div><div class="t">Expand via P&amp;L reserve</div><div class="d">Only after twelve months of win-rate and family-euro readouts. Prefer %-of-billed caps. Full-estate free-for-all not recommended.</div></div>
</div>

<div class="sec" style="margin-top:22px"><h2>What the money is meant to buy back</h2></div>
<div class="grid g2">
  <div class="card">
    <h3>Primary return</h3>
    <p style="margin:8px 0 0;font-size:13.5px">Retained workshop jobs and the parts basket that rides with them. Deal-file comments talk about stopping second-hand / internet / walk-away — job retention, not catalogue clearance. Families in the file: driveline, injectors / fuel, NOx / aftertreatment, engine hard parts, turbos, DEF, sensors.</p>
  </div>
  <div class="card">
    <h3>Vs SPA and list revision</h3>
    <p style="margin:8px 0 0;font-size:13.5px">SPA and list revision remain the structural tools (%GM / list for the book). Don't Lose the Deal is the <b>exception budget</b> when a live competitor quote would lose the job. Do not let it postpone a needed price revision. Do not double-dip with an open SPA on the same part.</p>
  </div>
</div>

<div class="sec" style="margin-top:18px"><h2>Readiness scorecard — Jerome's book</h2>
  <p style="color:var(--muted);font-size:13px;margin:4px 0 10px">Scores 1–5. Data = sales to dealer or rich billing. Network = IDS / known dealer estate. Pressure = competitive intensity (UK Measured; others proxy).</p>
</div>
<div class="tblwrap" style="margin-bottom:18px">
  <table id="scorecard"><thead>
    <tr><th>Distributor</th><th class="n">Data</th><th class="n">Network</th><th class="n">Pressure</th><th>Register</th><th>Pilot?</th></tr>
  </thead><tbody></tbody></table>
</div>

<div class="card" style="margin-bottom:18px">
  <h2>0.5% envelope table</h2>
  <div class="q">FY2026 parts billed and Proposed 0.5% cap — Measured billed, Proposed arithmetic</div>
  <div class="tblwrap" style="max-height:360px">
    <table id="envTable"><thead>
      <tr><th>Distributor</th><th class="n">FY2026 billed EUR</th><th class="n">0.5% envelope EUR</th><th>Note</th></tr>
    </thead><tbody></tbody></table>
  </div>
</div>

<div class="warn" id="unknowns">
  <h3>Unknowns — left open, not filled with assumptions</h3>
  <ul id="unknownList"></ul>
</div>

<div class="card" style="margin-bottom:18px">
  <h2>Sep 23 correction</h2>
  <p style="margin:8px 0 0;font-size:13.5px">The September note said zero cases because it searched billing text only.
    Duncan's deal file was already on disk and was not opened. That study is corrected here:
    <b>~218 regional cases</b> plus a fleet block, <b>£54,922</b> ITUK support, and EUR 30k as a
    <b>budgeted</b> FY27 line (also VPACC action plan + Pricing P&amp;L DLOD reserve) — not only an inferred credit rate.</p>
</div>

<footer class="foot">
  <div><b>Sources and as-of</b> — figures taken from the feasibility study dated 8 October 2026. No new euros invented for this page.</div>
  <div id="sources" style="margin-top:8px"></div>
  <div style="margin-top:10px">Labels: Measured / Proposed / Unknown match the study. Sales to dealer. %GM, not markup factors. UTI ≠ UMI; IUK ≠ ITUK.</div>
</footer>
</div>
"""

JS = r"""
(function(){
  var P = JSON.parse(document.getElementById('payload').textContent);
  var NAVY = '#15233c', TERRA = '#c0552d', AMBER = '#a8721f', MUTED = '#6b6459', LINE = '#d9d3c8';

  document.getElementById('verdict-text').textContent = P.verdict;

  function tip(html){
    return '<span class="info" tabindex="0">i<span class="tip">'+html+'</span></span>';
  }
  function eur(n){
    return 'EUR ' + Math.round(n).toLocaleString('en-GB');
  }
  function gbp(n){
    return '£' + Math.round(n).toLocaleString('en-GB');
  }

  var k = P.kpis;
  var kpiHtml = [
    {lab:'ITUK support (Duncan)', val:gbp(k.ituk_support_gbp), note:'Overall Summary total · Measured', cls:'', tip:'Sum of Fleet + North + South West + South East in Duncan Overall Summary. Workbook period in the 10 Mar 2026 deal file. Window: deal-file period, not a full FY cut.'},
    {lab:'Regional cases', val:String(k.regional_cases), note:'N 170 / SW 33 / SE 15 · Measured', cls:'', tip:'Regional lines with both Normal DN and Offer. Fleet money is extra; exact fleet row count is Unknown.'},
    {lab:'ISZE credit / FY27 line', val:eur(k.isze_credit_eur), note:'Intentional budget line · Confirmed', cls:'t', tip:'Round EUR 30,000 CR / rebate documents tagged DLOD or DLAD to ITUK. Same figure sits in FY27 budget, VPACC action plan, and Pricing P&L DLOD reserve. Co-funding — not 100% of every deal line.'},
    {lab:'0.5% of ITUK billed', val:eur(k.pct05_ituk_eur), note:'of '+eur(k.ituk_fy2026_billed_eur)+' · Proposed', cls:'', tip:'0.5% × ITUK FY2026 parts billed (fy2026_net_sales_eur). Cap / reserve idea on top of the existing EUR 30k practice. FY = 1 Apr 2025 – 31 Mar 2026.'},
    {lab:'Network 0.5% (18 DBs)', val:eur(k.pct05_network_eur), note:'of '+eur(k.network_fy2026_billed_eur)+' · Proposed', cls:'', tip:'Sum of 0.5% envelopes for 18 network distributors in distributor_dimension. Later option — not the first ask. MIDI markets excluded from this primary sum.'},
    {lab:'Competitor price filled', val:'1 / 218', note:'Proof gap · Measured', cls:'a', tip:'Only one regional line has Competitor Price filled. Excludes: inventing a win rate. Window: same Duncan regional extract.'},
    {lab:'Pilot reserve ask', val:'EUR 70–80k', note:'ITUK + IUK + one market · Proposed', cls:'t', tip:'ITUK EUR 30k (already in budget) + IUK ~EUR 30k at 0.5% + Ireland (~EUR 5.7k) or Portugal (~EUR 9.3k). Held in Pricing P&L DLOD reserve. Local approval inside envelope.'}
  ];
  document.getElementById('kpis').innerHTML = kpiHtml.map(function(x){
    return '<div class="kpi '+(x.cls||'')+'"><div class="lab">'+x.lab+' '+tip(x.tip)+'</div>'+
      '<div class="val">'+x.val+'</div><div class="note">'+x.note+'</div></div>';
  }).join('');

  var scBody = document.querySelector('#scorecard tbody');
  scBody.innerHTML = P.scorecard.map(function(r){
    var pilotClass = /Pilot|Continue|candidate/i.test(r.pilot) ? ' style="color:#c0552d;font-weight:600"' : '';
    return '<tr><td><b>'+r.db+'</b></td><td class="n">'+r.data+'</td><td class="n">'+r.network+
      '</td><td class="n">'+r.pressure+'</td><td>'+r.register+'</td><td'+pilotClass+'>'+r.pilot+'</td></tr>';
  }).join('');

  var et = document.querySelector('#envTable tbody');
  et.innerHTML = P.envelopes.map(function(r){
    return '<tr><td><b>'+r.db+'</b></td><td class="n">'+Math.round(r.billed_eur).toLocaleString('en-GB')+
      '</td><td class="n">'+Math.round(r.env_eur).toLocaleString('en-GB')+'</td><td>'+r.note+'</td></tr>';
  }).join('') + '<tr><td><b>Sum (18)</b></td><td class="n"><b>'+
    Math.round(P.kpis.network_fy2026_billed_eur).toLocaleString('en-GB')+
    '</b></td><td class="n"><b>'+Math.round(P.kpis.pct05_network_eur).toLocaleString('en-GB')+
    '</b></td><td>Proposed total ceiling</td></tr>';

  document.getElementById('unknownList').innerHTML = P.unknowns.map(function(u){
    return '<li>'+u+'</li>';
  }).join('');

  document.getElementById('sources').innerHTML = P.sources.map(function(s){
    return '<code>'+s+'</code>';
  }).join('');

  Chart.defaults.font.family = '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif';
  Chart.defaults.color = MUTED;

  var reg = P.region_support_gbp;
  new Chart(document.getElementById('chartRegion'), {
    type: 'bar',
    data: {
      labels: reg.map(function(r){ return r.region; }),
      datasets: [{
        label: 'ITUK support (GBP)',
        data: reg.map(function(r){ return r.support_gbp; }),
        backgroundColor: [TERRA, NAVY, '#3d5a80', '#6b6459'],
        borderWidth: 0,
        borderRadius: 2
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {display:false},
        tooltip: {
          callbacks: {
            afterBody: function(items){
              var i = items[0].dataIndex;
              var c = reg[i].cases;
              return c == null ? 'Fleet block — row count Unknown' : (c + ' regional cases');
            },
            label: function(ctx){ return '£' + Math.round(ctx.raw).toLocaleString('en-GB'); }
          }
        }
      },
      scales: {
        x: {grid:{color:LINE}, ticks:{callback:function(v){return '£'+Number(v).toLocaleString('en-GB');}}},
        y: {grid:{display:false}}
      }
    }
  });

  var pv = P.pilot_vs_full;
  new Chart(document.getElementById('chartPilot'), {
    type: 'bar',
    data: {
      labels: pv.map(function(r){ return r.label; }),
      datasets: [{
        label: 'EUR',
        data: pv.map(function(r){ return r.eur; }),
        backgroundColor: pv.map(function(r){
          return r.kind==='pilot' ? TERRA : (r.kind==='full' ? NAVY : '#b8aea0');
        }),
        borderWidth: 0,
        borderRadius: 2
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {display:false},
        tooltip: {callbacks:{label:function(ctx){return 'EUR '+Math.round(ctx.raw).toLocaleString('en-GB');}}}
      },
      scales: {
        x: {grid:{color:LINE}, ticks:{callback:function(v){return 'EUR '+Number(v).toLocaleString('en-GB');}}},
        y: {grid:{display:false}, ticks:{font:{size:11}}}
      }
    }
  });

  var env = P.envelopes.slice().sort(function(a,b){ return b.env_eur - a.env_eur; });
  new Chart(document.getElementById('chartEnv'), {
    type: 'bar',
    data: {
      labels: env.map(function(r){ return r.db; }),
      datasets: [{
        label: '0.5% envelope (EUR)',
        data: env.map(function(r){ return r.env_eur; }),
        backgroundColor: env.map(function(r){
          if (r.db==='ITUK' || r.db==='IUK') return TERRA;
          if (r.db==='Ireland' || r.db==='Portugal') return '#c07850';
          return NAVY;
        }),
        borderWidth: 0,
        borderRadius: 2
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {display:false},
        tooltip: {
          callbacks: {
            afterBody: function(items){
              var i = items[0].dataIndex;
              return env[i].note + ' · billed EUR ' + Math.round(env[i].billed_eur).toLocaleString('en-GB');
            },
            label: function(ctx){ return 'EUR ' + Math.round(ctx.raw).toLocaleString('en-GB'); }
          }
        }
      },
      scales: {
        x: {grid:{color:LINE}, ticks:{callback:function(v){return Number(v).toLocaleString('en-GB');}}},
        y: {grid:{display:false}, ticks:{font:{size:11}}}
      }
    }
  });
})();
"""


def extract_chart_js() -> str:
    if CHART_EXTRACT.exists():
        return CHART_EXTRACT.read_text(encoding="utf-8")
    text = REF_HTML.read_text(encoding="utf-8")
    start = text.find("<script>!function(t,e)")
    if start < 0:
        raise SystemExit("Chart.js not found in reference HTML")
    end = text.find("</script>", start)
    return text[start : end + 9]


def main() -> None:
    chart = extract_chart_js()
    payload_json = json.dumps(PAYLOAD, ensure_ascii=False, indent=None)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Don't Lose the Deal — network feasibility (8 Oct 2026)</title>
<style>
{CSS}
</style>
</head>
<body>
{BODY}
<script type="application/json" id="payload">{payload_json}</script>
{chart}
<script>
{JS}
</script>
</body>
</html>
"""
    out = OUT_DIR / HTML_NAME
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size:,} bytes)")

    cmd = OUT_DIR / CMD_NAME
    cmd.write_bytes(
        b"@echo off\r\n"
        b'start "" "%~dp0DLOD_NETWORK_FEASIBILITY_2026-10-08.html"\r\n'
    )
    print(f"Wrote {cmd} (CRLF)")


if __name__ == "__main__":
    main()
