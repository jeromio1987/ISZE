# -*- coding: utf-8 -*-
"""Build the self-contained HTML for the Don't Lose the Deal other-distributors study (2026-10-08).
Chart-first, one embedded JSON payload, Chart.js inlined, no network calls."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = ROOT / "Isuzu Universe" / "01_Strategy"
HTML = OUT_DIR / "DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.html"
CMD = OUT_DIR / "OPEN_DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.cmd"
CHART = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"

pl = json.loads((HERE / "payload.json").read_text(encoding="utf-8"))
md = json.loads((HERE / "model.json").read_text(encoding="utf-8"))
D = {d["code"]: d for d in pl["dists"]}
NAME = {"ITUK": "ITUK", "IUK": "IUK", "UTI": "UTI", "UMI": "UMI", "GERMANY": "Germany", "BELGIUM": "Belgium", "PORTUGAL": "Portugal",
        "NORWAY": "Norway", "SWEDEN": "Sweden", "IRELAND": "Ireland", "GREECE": "Greece", "CYPRUS": "Cyprus", "HUNGARY": "Hungary",
        "FINLAND": "Finland", "MALTA": "Malta", "ROMANIA": "Romania", "DENMARK": "Denmark", "ICELAND": "Iceland"}
TIER_A = ["IUK", "UTI", "GERMANY", "BELGIUM", "PORTUGAL"]
TIER_B = ["NORWAY", "SWEDEN", "IRELAND"]
STEP = {"A": "No-money log, two quarters", "B": "Not now", "C": "No case-by-case programme", "REF": "Reference: runs today"}

rows = []
for r in md["rows"]:
    c = r["code"]
    d = D[c]
    tier = "REF" if c == "ITUK" else "A" if c in TIER_A else "B" if c in TIER_B else "C"
    rows.append(dict(code=c, name=NAME[c], tier=tier, step=STEP[tier], scope=d["scope"], P=r["P"], g=r["g"], mpv=r["margin_per_vehicle"],
                     bill=r["bill_per_case"], cases=r["cases_central"], net=r["net_central"], cost=r["cost_central"], gain=r["gain_central"],
                     p50=r["p_star_phi50"], p100=r["p_star_phi100"], dealers=d["dealers"], rebate26=d["rebate_fy26"], rebate25=d["rebate_fy25"],
                     billed=d["billed"], warranty=d["warranty"],
                     rnote="; ".join("{} €{:,.0f}".format(k, v) for k, v in __import__('collections').OrderedDict((x["klass"], 0) for x in d["rebate_labelled"]).items() for v in [sum(y["eur"] for y in d["rebate_labelled"] if y["klass"] == k)])))

reg = pd.read_csv(HERE / "register_lines_classified.csv", low_memory=False)
sup_gbp = reg.sup
bands = []
for lab, lo, hi in (("under £150", 0, 150), ("£150 to £500", 150, 500), ("£500 and over", 500, 1e9)):
    m = (sup_gbp >= lo) & (sup_gbp < hi)
    bands.append(dict(label=lab, lines=int(m.sum()), lines_share=float(m.mean()), support=float(sup_gbp[m].sum()), support_share=float(sup_gbp[m].sum() / sup_gbp.sum())))

others = [r for r in rows if r["code"] != "ITUK"]
payload = dict(
    asof="2026-10-08", rho=md["params"]["rho"], rows=rows, bands=bands, families=pl["register"]["families"][:8],
    contest=[c for c in pl["contest"] if c["markets"] != "all 18 distributors"], selffund=md["selffund"], eps=md["blanket_eps"],
    totals=md["totals"], network=dict(net=sum(r["net"] for r in others), cost=sum(r["cost"] for r in others), gain=sum(r["gain"] for r in others),
                                      ceiling=sum(r["ceiling_u3"] for r in md["rows"] if r["code"] != "ITUK"), pool=sum(r["P"] for r in others),
                                      rebate26=sum(r["rebate26"] for r in rows), rebate26_others=sum(r["rebate26"] for r in others), kickback=pl["rebate_class_totals"]["kickback"]),
    itcheck=md["itcheck"], register=dict(lines=pl["register"]["lines"], normal_margin=pl["register"]["normal_margin_on_dn"],
                                           retained=pl["register"]["retained_margin_on_offer"], support_over_dn=pl["register"]["support_over_dn"],
                                           blank=pl["register"]["comment_blank"], comp=pl["register"]["comp_price_filled"]),
    u=pl["intensity"],
)

CSS = r"""
:root{
  --navy:#15233c; --navy2:#1d3054; --terra:#c0552d; --paper:#f7f4ee;
  --ink:#222; --muted:#6b6459; --line:#d9d3c8; --band:#eef3f9; --card:#fff;
  --good:#1e6b4f; --amber:#a8721f; --amber-bg:#fdf3e3; --amber-bd:#e6cf9f; --grey:#9a948a;
}
:root[data-theme="dark"]{ color-scheme:light }
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;font-size:14px;line-height:1.5}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
h1{font-size:26px;letter-spacing:-.2px;line-height:1.2}
h2{font-size:18px;margin-bottom:4px}
h3{font-size:15px}
.wrap{max-width:1180px;margin:0 auto;padding:22px 20px 56px}
header.top{border-bottom:3px solid var(--navy);padding-bottom:14px;margin-bottom:18px}
.sub{color:var(--muted);font-size:13px;margin-top:8px;max-width:920px}
.badge{display:inline-block;background:var(--navy);color:var(--paper);font-size:11px;letter-spacing:.6px;text-transform:uppercase;
  padding:3px 9px;border-radius:2px;margin:0 8px 4px 0}
.badge.terra{background:var(--terra)}
.verdict{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--terra);padding:14px 16px;margin-bottom:18px}
.verdict p{margin:0 0 8px;font-size:15px;line-height:1.55}
.verdict p:last-child{margin:0}
.verdict .ask{font-size:13.5px;color:var(--navy)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(176px,1fr));gap:12px;margin-bottom:20px}
.kpi{background:var(--card);border:1px solid var(--line);padding:13px 15px;position:relative;border-top:3px solid var(--navy)}
.kpi.t{border-top-color:var(--terra)} .kpi.a{border-top-color:var(--amber)}
.kpi .lab{font-size:11px;letter-spacing:.55px;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;gap:5px}
.kpi .val{font-size:22px;font-weight:600;color:var(--navy);margin-top:5px;font-variant-numeric:tabular-nums}
.kpi .note{font-size:11.5px;color:var(--muted);margin-top:3px}
.info{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;border-radius:50%;background:var(--navy);
  color:#fff;font-size:9.5px;cursor:help;position:static;flex:0 0 auto}
.info .tip{display:none;position:absolute;left:8px;right:8px;top:38px;width:auto;background:var(--navy);
  color:var(--paper);font-size:12px;line-height:1.45;padding:9px 11px;border-radius:3px;z-index:200;text-transform:none;
  letter-spacing:0;font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25);text-align:left;border-left:3px solid var(--terra)}
.info .tip b{color:#f0b49a}
.info:hover .tip,.info:focus .tip{display:block}
.grid{display:grid;gap:16px;margin-bottom:18px}
.g2{grid-template-columns:1fr 1fr}
@media(max-width:900px){.g2{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);padding:15px 16px 14px;min-width:0}
.card .q{font-size:13px;color:var(--muted);margin:2px 0 12px}
.card .fn{font-size:11.5px;color:var(--muted);margin-top:8px}
.chartbox{position:relative;height:330px;min-width:0}
.pair{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:10px}
@media(max-width:640px){.pair{grid-template-columns:minmax(0,1fr)}}
.chartbox.short{height:260px} .chartbox.tall{height:440px}
table{border-collapse:collapse;width:100%;font-size:13px}
thead th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;font-weight:600;font-size:11.5px;
  letter-spacing:.35px;text-transform:uppercase;position:sticky;top:0;z-index:5}
th.n,td.n{text-align:right;font-variant-numeric:tabular-nums}
tbody td{padding:7px 9px;border-bottom:1px solid var(--line);color:var(--ink);background:var(--card)}
tbody tr:nth-child(even) td{background:var(--band);color:var(--ink)}
tbody tr.ref td{background:#e8e0d4;color:var(--ink)}
.tblwrap{overflow-x:auto;border:1px solid var(--line)}
.tier{display:inline-block;min-width:22px;text-align:center;font-weight:700;padding:1px 6px;border-radius:2px;color:#fff;background:var(--grey)}
.tier.A{background:var(--terra)} .tier.B{background:var(--navy2)} .tier.REF{background:var(--navy)}
.warn{background:var(--amber-bg);border:1px solid var(--amber-bd);border-left:4px solid var(--amber);padding:12px 14px;font-size:13px;color:#5e4a1c;margin-bottom:18px}
.warn h3{color:var(--amber);margin-bottom:6px}
.warn ul{margin:6px 0 0;padding-left:18px} .warn li{margin:3px 0}
.sec{margin:24px 0 8px}
.calc{display:grid;grid-template-columns:minmax(260px,1fr) 1.4fr;gap:20px}
@media(max-width:900px){.calc{grid-template-columns:1fr}}
.sl{margin-bottom:13px}
.sl label{display:flex;justify-content:space-between;font-size:12.5px;color:var(--navy);font-weight:600}
.sl label output{color:var(--terra);font-variant-numeric:tabular-nums}
.sl input[type=range]{width:100%;accent-color:var(--terra)}
.sl .h{font-size:11.5px;color:var(--muted)}
.res{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;align-content:start}
.res .r{background:var(--band);border:1px solid var(--line);padding:11px 13px}
.res .r .lab{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.res .r .val{font-size:22px;font-weight:600;color:var(--navy);font-variant-numeric:tabular-nums;margin-top:3px}
.res .r .val.neg{color:var(--terra)}
.res .r .note{font-size:11.5px;color:var(--muted)}
.btn{background:var(--navy);color:var(--paper);border:0;padding:7px 12px;font-size:12.5px;cursor:pointer;border-radius:2px}
.route{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin-top:10px}
.step{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--navy);padding:12px 13px}
.step.now{border-top-color:var(--terra)}
.step .n{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.step .t{font-family:Georgia,serif;color:var(--navy);font-size:15px;margin:4px 0 6px}
.step .d{font-size:12.5px}
.foot{font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:12px;margin-top:28px}
.foot code{font-size:11px;word-break:break-all;display:block;margin:2px 0}
.tag{display:inline-block;font-size:10.5px;letter-spacing:.4px;text-transform:uppercase;padding:2px 7px;border-radius:2px;margin-left:6px;vertical-align:middle}
.tag.m{background:#dce8df;color:var(--good)} .tag.p{background:#e8e0d4;color:#6b5340} .tag.u{background:var(--amber-bg);color:var(--amber)}
"""

BODY = r"""
<div class="wrap">
<header class="top">
  <div><span class="badge">Don't Lose the Deal</span><span class="badge terra">Internal study</span><span class="badge">8 Oct 2026</span><span class="badge">FY2026 = 1 Apr 2025 to 31 Mar 2026</span></div>
  <h1 style="margin-top:10px">Would Don't Lose the Deal earn its money at the other distributors?</h1>
  <div class="sub">Direct effect (the job that is kept) and indirect effect (the customer who stays), for the 17 distributors in your book other than ITUK.
  Euros first, ISZE margin, hard parts only. Written companion with every argument and source:
  <b>DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.md</b> in the same folder.</div>
</header>

<section class="verdict">
  <p id="v1"></p>
  <p id="v2"></p>
  <p class="ask" id="v3"></p>
</section>

<div class="kpis" id="kpis"></div>

<div class="sec" id="calc"><h2>Try your own assumptions</h2>
  <p style="color:var(--muted);font-size:13px;margin:4px 0 10px">Every number below moves with the sliders. The starting position is the central case of the study.
  Most of these inputs are not measured anywhere; the ones that are, are marked in the notes.</p></div>
<div class="card calc" style="margin-bottom:18px">
  <div>
    <div class="sl"><label>Share of hard-part billing on supported cases <output id="o_u"></output></label>
      <input type="range" id="s_u" min="0.5" max="12" step="0.5" value="3">
      <div class="h">ITUK shows at least 3.3% (measured). Other markets: unknown.</div></div>
    <div class="sl"><label>ISZE funds this share of the discount <output id="o_phi"></output></label>
      <input type="range" id="s_phi" min="0" max="100" step="5" value="50">
      <div class="h">Your design choice. ITUK keeps ~41–43% median margin on the offer (~47% before), so it can fund much of it itself.</div></div>
    <div class="sl"><label>Supported jobs that really would have been lost <output id="o_p"></output></label>
      <input type="range" id="s_p" min="0" max="100" step="5" value="50">
      <div class="h">The save rate. Not measured anywhere. This is what the no-money log would find out.</div></div>
    <div class="sl"><label>Extra parts that ride along on a saved job <output id="o_b"></output></label>
      <input type="range" id="s_b" min="0" max="50" step="5" value="0">
      <div class="h">Not measured. Zero until the log shows it.</div></div>
    <div class="sl"><label>Saved customers who stay because of it <output id="o_d"></output></label>
      <input type="range" id="s_d" min="0" max="100" step="5" value="0">
      <div class="h">Counted as the average ISZE margin per truck per year, for the years below.</div></div>
    <div class="sl"><label>…for how many years <output id="o_y"></output></label>
      <input type="range" id="s_y" min="1" max="5" step="1" value="3"></div>
    <button class="btn" id="reset">Back to the central case</button>
  </div>
  <div>
    <div class="res" id="res"></div>
    <p class="fn" style="font-size:11.5px;color:var(--muted);margin-top:10px">Net = ISZE margin on saved jobs + margin on customers who stay − ISZE's credit. ISZE's credit = ISZE share × support given, and support given is 0.32 euro per euro ISZE billed on supported cases (measured at ITUK). Break-even save rate = the save rate at which net is zero.</p>
  </div>
</div>

<div class="grid g2" id="row1">
  <div class="card">
    <h2>Where is the hard-part money to defend?</h2>
    <div class="q">FY2026 billing on hard parts, warranty removed. Terracotta = tier A, blue = tier B, sand = tier C, navy = ITUK (reference). The bar says how big the base is, not whether anyone competes for it.</div>
    <div class="chartbox tall"><canvas id="cPool"></canvas></div>
    <div class="fn">Measured: sales_fact.parquet, warranty file. Tier A = 40 or more supported cases a year at the central case, B = 25 to 40, C = fewer.</div>
  </div>
  <div class="card">
    <h2>What does the network earn at different save rates?</h2>
    <div class="q">Net to ISZE a year across the 17 other distributors, for four levels of touch share (the share of hard-part billing that sits on supported cases). Moves with the sliders for ISZE share, extra parts and customers who stay.</div>
    <div class="chartbox tall"><canvas id="cEarn"></canvas></div>
    <div class="fn" id="earnNote"></div>
  </div>
</div>

<div class="grid g2" id="row2">
  <div class="card">
    <h2>Who pays for the discount decides the break-even</h2>
    <div class="q">Save rate needed at ITUK's economics, by how much of the discount ISZE funds and how many saved customers stay three years.</div>
    <div class="chartbox"><canvas id="cFund"></canvas></div>
    <div class="fn">Inferred from the ITUK register: ISZE margin 47.7%, support 0.32 euro per euro billed.</div>
  </div>
  <div class="card">
    <h2>Do independents really undercut ISZE on hard parts?</h2>
    <div class="q">Share of covered hard-part billing where the independent price is 10% or more below ISZE, or above ISZE. The second line of each label says how much of the billing the price list covers.</div>
    <div class="chartbox tall"><canvas id="cComp"></canvas></div>
    <div class="fn">Measured, listings not workshop quotes. Nothing covers Israel, Portugal, Ireland, Belgium, Sweden or the small markets. Samples are 2 to 17 part numbers.</div>
  </div>
</div>

<div class="grid g2" id="row3">
  <div class="card">
    <h2>ISZE already pays year-end kickbacks. How big is DLOD next to them?</h2>
    <div class="q">FY2026 year-end credits per distributor (mostly labelled kickback in the order file), against the central-case cost of a DLOD programme there.</div>
    <div class="chartbox"><canvas id="cReb"></canvas></div>
    <div class="fn">Measured: credit documents in sales_fact, labelled from the order file. Kickback terms are not in the data.</div>
  </div>
  <div class="card">
    <h2>Where does ITUK's support go?</h2>
    <div class="q">Left: part families. Right: size of case, share of cases against share of the money.</div>
    <div class="pair">
      <div class="chartbox short"><canvas id="cFam"></canvas></div>
      <div class="chartbox short"><canvas id="cBand"></canvas></div>
    </div>
    <div class="fn">Measured: 218 regional lines, GBP at 1.17. 64% of the cases are under £150 and carry 20% of the money.</div>
  </div>
</div>

<div class="sec" id="verd"><h2>Verdict by distributor</h2>
  <p style="color:var(--muted);font-size:13px;margin:4px 0 10px">Updates with the sliders. Tier and next step are fixed at the central case.</p></div>
<div class="tblwrap" style="margin-bottom:18px"><table id="tbl"><thead>
  <tr><th>Distributor</th><th>Tier</th><th class="n">Hard-part billing</th><th class="n">Cases a year</th><th class="n">ISZE credit</th><th class="n">Margin on saved jobs</th><th class="n">Customers who stay</th><th class="n">Net</th><th class="n">Break-even save rate</th><th>Next step</th></tr>
</thead><tbody></tbody></table></div>

<div class="warn" id="unk"><h3>Unknown today</h3><ul>
  <li>The save rate in any market. The register only records jobs that were supported and invoiced, so lost jobs are invisible.</li>
  <li>Whether ITUK would run Don't Lose the Deal without ISZE's credit.</li>
  <li>The kickback terms: what triggers them, whether they can change in the FY27 proposal, and whether DLOD would be paid on top of them. The order file labels the credits (kickback, scrap support, DLOD, sales support) but not their formula.</li>
  <li>Distributor margins on hard parts outside the UK, and competitor prices on hard parts outside the UK, Germany and Norway.</li>
  <li>Retention effect and extra parts on the job. Duncan's 2025 workbook and any cases after 9 March 2026. Local competition-law advice.</li>
</ul></div>

<div class="sec"><h2>What to do</h2></div>
<div class="route">
  <div class="step now"><div class="n">1 · Now</div><div class="t">Clean the ITUK numbers</div><div class="d">Get Duncan's 2025 workbook and any cases after 9 March 2026, so ITUK has one clean year.</div></div>
  <div class="step now"><div class="n">2 · Now</div><div class="t">Fold DLOD into the FY27 kickback</div><div class="d">Nine distributors received €430k of year-end credits in FY2026, €313k of it labelled kickback. A case-based slice of the kickback costs nothing extra.</div></div>
  <div class="step"><div class="n">3 · Two quarters</div><div class="t">No-money log in UTI, IUK, Germany, Belgium, Portugal</div><div class="d">Competitor price, outcome, invoice number, for every at-risk hard-part job. Lost jobs too. UTI first.</div></div>
  <div class="step"><div class="n">4 · After the log</div><div class="t">Fund where the save rate beats break-even</div><div class="d">About 100 logged cases per market. Fund a share of the discount, not all of it, as a case-based part of the kickback.</div></div>
</div>

<footer class="foot">
  <div><b>Sources</b> (all under C:\Users\jerom\Desktop\claude\ISZE\). Every number on this page comes from the embedded payload, built by the scripts in 01_data\91_build\dlod_other_dbs_20261008\ (_analysis.py, _model.py).</div>
  <code>01_data\90_INBOX\ituk_std_mail_hunt_20260903\pulled_attachments\2026-03-10_1026_Duncan_DLAD - All regions 2026 Overall.xlsx</code>
  <code>01_data\00_derived\sales_fact.parquet · distributor_dimension.csv · distributor_warranty_expense_fiscal.csv · warranty_raw_grain.csv · order_headers_from_Order_Detail.csv · gps_spu_by_distributor.csv · eucon_price_gap.csv · eucon_uk_survey_2023_price_gap.csv · iam_ks_price_gap.csv</code>
  <div style="margin-top:8px">Labels: measured numbers are counted in the files above. The sliders' starting values are proposed assumptions. Sales to dealer, %GM and margin. UTI and UMI are never blended; IUK and ITUK are never blended.</div>
</footer>
</div>
"""

JS = r"""
(function(){
  var P = JSON.parse(document.getElementById('payload').textContent);
  var NAVY='#15233c', TERRA='#c0552d', NAVY2='#3d5a80', GREY='#9a948a', MUTED='#6b6459', LINE='#d9d3c8', SAND='#c9bfae';
  function eur(n){ var s=n<0?'−':''; n=Math.abs(n); return s+'€'+Math.round(n).toLocaleString('en-GB'); }
  function ek(n){ var s=n<0?'−':''; n=Math.abs(n); return s+(n>=1000?'€'+(n/1000).toFixed(1)+'k':'€'+Math.round(n)); }
  function pc(x,d){ return (x*100).toFixed(d||0)+'%'; }
  function tip(h){ return '<span class="info" tabindex="0">i<span class="tip">'+h+'</span></span>'; }
  var N = P.network, rho = P.rho;
  var others = P.rows.filter(function(r){return r.code!=='ITUK';});
  var itu = P.rows.filter(function(r){return r.code==='ITUK';})[0];

  document.getElementById('v1').textContent = 'No, not as a way to grow sales. Don\'t Lose the Deal protects a repair job that is about to go to a cheaper independent quote; it does not create demand. At the other 17 distributors it is a small defensive tool: about '+eur(Math.round(N.net/1000)*1000)+' of ISZE margin a year at the central case, anywhere from a loss of '+ek(-P.totals.u3_p25)+' to a gain of '+ek(P.totals.u3_p75)+' depending on how many supported jobs really were saves. The ceiling, with every job saved and ISZE paying nothing, is about '+eur(Math.round(N.ceiling/1000)*1000)+'.';
  document.getElementById('v2').textContent = 'Customers who stay add real value (a kept truck is worth ISZE '+eur(P.rows.filter(function(r){return r.code==="UTI"})[0].mpv)+' to '+eur(itu.mpv)+' of margin a year at the truck distributors, about '+eur(others.filter(function(r){return r.code==="IUK"})[0].mpv)+' at IUK) but they do not change the answer: they lower the save rate ISZE needs from about '+pc(itu.p50)+' to roughly 21% to 32%, and only if half of saved customers would otherwise have left for good. Only five markets (UTI, IUK, Germany, Belgium, Portugal) are big enough to run it, and ISZE already pays '+eur(Math.round(N.rebate26/1000)*1000)+' of year-end credits to nine distributors, '+eur(Math.round(N.kickback/1000)*1000)+' of it kickback.';
  document.getElementById('v3').innerHTML = '<b>Recommendation:</b> no new money yet. Run a no-money log of at-risk hard-part jobs for two quarters in those five markets, then fund a share of the discount, as a case-based part of the kickback, only where the logged save rate beats the break-even.';

  var kp = [
    {lab:'Central case, all 17', val:eur(Math.round(N.net/100)*100)+' a year', note:'range '+ek(P.totals.u3_p25)+' to +'+ek(P.totals.u3_p75), cls:'t',
     tip:'<b>Net to ISZE a year.</b> 3% of hard-part billing on supported cases (ITUK\'s floor), ISZE funds half the discount, half the supported jobs really would have been lost, no extra parts. Cost '+eur(N.cost)+', margin kept '+eur(N.gain)+'. Proposed assumptions, measured inputs.'},
    {lab:'Ceiling', val:eur(Math.round(N.ceiling/1000)*1000), note:'every job saved, ISZE pays nothing',
     tip:'<b>Upper limit.</b> ISZE margin on the 3% of hard-part billing that sits on supported cases, with a 100% save rate and no credit. Not reachable; it shows the size of the prize. About 1% of ISZE margin on all parts at these distributors.'},
    {lab:'Save rate needed', val:pc(itu.p50)+' / '+pc(itu.p100), note:'ISZE funds half / all',
     tip:'<b>Break-even save rate</b> = ISZE share of the discount × 0.32 ÷ ISZE margin (47.7% at ITUK). Funding the whole discount needs about 7 in 10 supported jobs to be real saves; funding half needs about 1 in 3.'},
    {lab:'Rebates paid FY2026', val:eur(Math.round(N.rebate26/1000)*1000), note:'nine distributors, €313k labelled kickback', cls:'a',
     tip:'<b>Year-end credit documents</b> ("Rebate Material", mostly 24 to 31 March 2026) in sales_fact, labelled in the order file: '+eur(N.kickback)+' kickback to eight distributors; ITUK also €35,000 scrap support and €30,000 DLOD; UMI €20,000 sales support. Kickback terms are not in the data.'},
    {lab:'Markets with enough volume', val:'5 of 17', note:'40+ supported cases a year',
     tip:'<b>Operating volume at the central case.</b> UTI, IUK, Germany, Belgium, Portugal. Twelve others would see fewer than 35 cases a year, nine of them fewer than 15. A dealer does not form a habit on one case a year.'},
    {lab:'Competition on hard parts', val:'under 1% to 11%', note:'of billing has a competitor price', cls:'a',
     tip:'<b>Coverage of competitor price evidence</b> on hard parts: UK workshop 2023, UK trade-shop 2026, Germany/Norway online 2026. Nothing for Israel, Portugal, Ireland, Belgium, Sweden or the small markets.'}
  ];
  document.getElementById('kpis').innerHTML = kp.map(function(x){
    return '<div class="kpi '+(x.cls||'')+'"><div class="lab">'+x.lab+' '+tip(x.tip)+'</div><div class="val">'+x.val+'</div><div class="note">'+x.note+'</div></div>';
  }).join('');

  // ---------- calculator
  var S = {u:.03, phi:.5, p:.5, b:0, d:0, y:3};
  var DEF = JSON.parse(JSON.stringify(S));
  function calc(r, s){
    var R = s.u*r.P, cases = R/r.bill, support = rho*R, cost = s.phi*support;
    var gain = s.p*r.g*(1+s.b)*R, ret = s.p*s.d*s.y*(r.mpv||0)*cases;
    var den = r.g*(1+s.b)*R + s.d*s.y*(r.mpv||0)*cases;
    return {R:R, cases:cases, cost:cost, gain:gain, ret:ret, net:gain+ret-cost, pstar: den>0 ? cost/den : null};
  }
  function netAll(s){ var t=0; others.forEach(function(r){ t += calc(r,s).net; }); return t; }
  function sumAll(s,k){ var t=0; others.forEach(function(r){ t += calc(r,s)[k]; }); return t; }
  function tierSum(s,tier){ var t=0; others.forEach(function(r){ if(r.tier===tier) t += calc(r,s).net; }); return t; }
  function stateFromUI(){
    S.u = +document.getElementById('s_u').value/100; S.phi = +document.getElementById('s_phi').value/100;
    S.p = +document.getElementById('s_p').value/100; S.b = +document.getElementById('s_b').value/100;
    S.d = +document.getElementById('s_d').value/100; S.y = +document.getElementById('s_y').value;
  }
  function setUI(){
    document.getElementById('s_u').value = S.u*100; document.getElementById('s_phi').value = S.phi*100;
    document.getElementById('s_p').value = S.p*100; document.getElementById('s_b').value = S.b*100;
    document.getElementById('s_d').value = S.d*100; document.getElementById('s_y').value = S.y;
  }
  function labels(){
    document.getElementById('o_u').textContent = (S.u*100).toFixed(1)+'%';
    document.getElementById('o_phi').textContent = Math.round(S.phi*100)+'%';
    document.getElementById('o_p').textContent = Math.round(S.p*100)+'%';
    document.getElementById('o_b').textContent = '+'+Math.round(S.b*100)+'%';
    document.getElementById('o_d').textContent = Math.round(S.d*100)+'%';
    document.getElementById('o_y').textContent = S.y+(S.y===1?' year':' years');
  }
  // network break-even save rate by bisection
  function beSave(s){
    var lo=0, hi=1.0, f=function(p){ var t=JSON.parse(JSON.stringify(s)); t.p=p; return netAll(t); };
    if (f(1) < 0) return null;
    if (f(0) >= 0) return 0;
    for (var i=0;i<40;i++){ var m=(lo+hi)/2; if (f(m)<0) lo=m; else hi=m; }
    return hi;
  }
  function renderRes(){
    var net = netAll(S), cost = sumAll(S,'cost'), cases = sumAll(S,'cases'), be = beSave(S);
    var cells = [
      {lab:'Net to ISZE, all 17 a year', val:ek(net), neg:net<0, note:'cost '+ek(cost)+', margin and customers kept '+ek(sumAll(S,'gain')+sumAll(S,'ret'))},
      {lab:'Tier A markets only', val:ek(tierSum(S,'A')), neg:tierSum(S,'A')<0, note:'UTI, IUK, Germany, Belgium, Portugal'},
      {lab:'Save rate needed (network)', val: be===null ? 'never' : pc(be), neg:false, note:'you chose '+pc(S.p)+(be!==null && S.p<be ? ' — below break-even' : '')},
      {lab:'Supported cases a year', val:Math.round(cases).toLocaleString('en-GB'), neg:false, note:'about '+Math.round(cases/others.length)+' per market on average'}
    ];
    document.getElementById('res').innerHTML = cells.map(function(c){
      return '<div class="r"><div class="lab">'+c.lab+'</div><div class="val'+(c.neg?' neg':'')+'">'+c.val+'</div><div class="note">'+c.note+'</div></div>';
    }).join('');
  }
  function renderTable(){
    var body = document.querySelector('#tbl tbody');
    var rank={REF:0,A:1,B:2,C:3};
    var ordered = P.rows.slice().sort(function(a,b){ return rank[a.tier]-rank[b.tier] || b.P-a.P; });
    body.innerHTML = ordered.map(function(r){
      var c = calc(r,S);
      return '<tr class="'+(r.tier==='REF'?'ref':'')+'"><td><b>'+r.name+'</b>'+(r.tier==='REF'?' (reference)':'')+'</td><td><span class="tier '+r.tier+'">'+(r.tier==='REF'?'ref':r.tier)+'</span></td>'+
        '<td class="n">'+eur(r.P)+'</td><td class="n">'+Math.round(c.cases)+'</td><td class="n">'+eur(c.cost)+'</td><td class="n">'+eur(c.gain)+'</td><td class="n">'+eur(c.ret)+'</td>'+
        '<td class="n"><b'+(c.net<0?' style="color:#c0552d"':'')+'>'+eur(c.net)+'</b></td><td class="n">'+(c.pstar===null?'n/a':pc(c.pstar))+'</td><td>'+r.step+'</td></tr>';
    }).join('');
  }

  // ---------- charts
  Chart.defaults.font.family='-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif';
  Chart.defaults.color = MUTED;
  var tierCol = {A:TERRA, B:NAVY2, C:SAND, REF:NAVY};
  var poolRows = P.rows.slice().sort(function(a,b){return b.P-a.P;});
  new Chart(document.getElementById('cPool'),{type:'bar',
    data:{labels:poolRows.map(function(r){return r.name+(r.tier==='REF'?' (ref.)':'');}),
      datasets:[{data:poolRows.map(function(r){return r.P;}),backgroundColor:poolRows.map(function(r){return tierCol[r.tier];}),borderWidth:0,borderRadius:2}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){var r=poolRows[c.dataIndex];return eur(r.P)+' hard-part billing';},
        afterBody:function(it){var r=poolRows[it[0].dataIndex];return 'Tier '+(r.tier==='REF'?'ref':r.tier)+' · ~'+Math.round(r.cases)+' supported cases a year · net '+eur(r.net)+' at the central case';}}}},
      scales:{x:{grid:{color:LINE},ticks:{callback:function(v){return '€'+(v/1e6).toFixed(1)+'M';}}},y:{grid:{display:false},ticks:{font:{size:11}}}}}});

  var earnChart = new Chart(document.getElementById('cEarn'),{type:'line',
    data:{labels:[],datasets:[]},
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'bottom',labels:{boxWidth:14}},tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+ek(c.raw*1000);}}}},
      scales:{x:{title:{display:true,text:'Share of supported jobs that really were saves'},grid:{color:LINE},ticks:{maxTicksLimit:11,autoSkip:true,maxRotation:0}},
              y:{title:{display:true,text:'Net to ISZE, €k a year'},grid:{color:LINE},ticks:{callback:function(v){return v+'k';}}}}}});
  function renderEarn(){
    var xs=[]; for(var p=0;p<=100;p+=5) xs.push(p);
    var cfg=[{u:.01,col:SAND,l:'1% touch share'},{u:.03,col:TERRA,l:'3% (ITUK floor)'},{u:.06,col:NAVY2,l:'6%'},{u:.10,col:NAVY,l:'10%'}];
    earnChart.data.labels = xs.map(function(x){return x+'%';});
    earnChart.data.datasets = cfg.map(function(c){
      return {label:c.l,borderColor:c.col,backgroundColor:c.col,borderWidth:2.2,pointRadius:0,tension:0,
        data:xs.map(function(x){var s=JSON.parse(JSON.stringify(S)); s.u=c.u; s.p=x/100; return netAll(s)/1000;})};
    });
    earnChart.data.datasets.push({label:'Break-even (zero)',borderColor:'#6b6459',borderDash:[5,4],borderWidth:1.2,pointRadius:0,data:xs.map(function(){return 0;})});
    earnChart.update();
    var be = beSave(S);
    document.getElementById('earnNote').textContent = 'Break-even save rate across the network at your sliders: '+(be===null?'never':pc(be))+'. ISZE funds '+Math.round(S.phi*100)+'% of the discount; extra parts '+Math.round(S.b*100)+'%; customers who stay '+Math.round(S.d*100)+'% for '+S.y+' years.';
  }

  // who funds
  (function(){
    var shares=[.25,.5,1.0], ds=[0,.25,.5];
    var cfg=[{d:0,col:NAVY,l:'Saved jobs only'},{d:.25,col:NAVY2,l:'1 in 4 saved customers stays 3 years'},{d:.5,col:TERRA,l:'1 in 2 stays 3 years'}];
    new Chart(document.getElementById('cFund'),{type:'bar',
      data:{labels:['ISZE funds a quarter','ISZE funds half','ISZE funds all'],
        datasets:cfg.map(function(c){return {label:c.l,backgroundColor:c.col,borderRadius:2,
          data:shares.map(function(f){var cost=f*rho*itu.bill; var den=itu.g*itu.bill+c.d*3*itu.mpv; return cost/den*100;})};})},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}},
        tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+c.raw.toFixed(0)+'% of supported jobs must be real saves';}}}},
        scales:{y:{beginAtZero:true,max:80,grid:{color:LINE},title:{display:true,text:'Save rate needed, %'}},x:{grid:{display:false}}}}});
  })();

  // competition
  (function(){
    var c = P.contest;
    var lab = c.map(function(x){
      var m = x.source.indexOf('Online')===0 ? 'DE/NO online 2026' : x.source.indexOf('workshop')>0 ? 'UK workshop 2023' : 'UK trade shop 2026';
      var w = x.markets==='Germany + Norway' ? 'DE+NO billing' : x.markets+' billing';
      return [m, w+' · '+(x.coverage*100).toFixed(1)+'% covered'];
    });
    new Chart(document.getElementById('cComp'),{type:'bar',
      data:{labels:lab,datasets:[
        {label:'Independent 10%+ below ISZE',data:c.map(function(x){return x.share_below10*100;}),backgroundColor:TERRA,borderRadius:2},
        {label:'Independent above ISZE price',data:c.map(function(x){return x.share_above*100;}),backgroundColor:NAVY,borderRadius:2}]},
      options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}},
        tooltip:{callbacks:{label:function(ctx){return ctx.dataset.label+': '+ctx.raw.toFixed(0)+'%';},
          afterBody:function(it){var x=c[it[0].dataIndex];return x.pns_hard_in_pool+' hard parts priced; average gap '+(x.wtd_delta*100).toFixed(0)+'%';}}}},
        scales:{x:{beginAtZero:true,max:100,grid:{color:LINE},title:{display:true,text:'% of covered hard-part billing'}},y:{grid:{display:false},ticks:{font:{size:10.5}}}}}});
  })();

  // rebates
  (function(){
    var rr = P.rows.filter(function(r){return r.rebate26>0;}).sort(function(a,b){return b.rebate26-a.rebate26;});
    new Chart(document.getElementById('cReb'),{type:'bar',
      data:{labels:rr.map(function(r){return r.name;}),datasets:[
        {label:'Year-end credits FY2026',data:rr.map(function(r){return r.rebate26;}),backgroundColor:NAVY,borderRadius:2},
        {label:'DLOD at the central case (ISZE credit)',data:rr.map(function(r){return r.cost;}),backgroundColor:TERRA,borderRadius:2}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}},
        tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+eur(c.raw);},afterBody:function(it){var r=rr[it[0].dataIndex];return ['Labels: '+(r.rnote||'none'),'DLOD cost = '+pc(r.cost/r.rebate26)+' of the credits'];}}}},
        scales:{y:{grid:{color:LINE},ticks:{callback:function(v){return '€'+(v/1000)+'k';}}},x:{grid:{display:false},ticks:{font:{size:11}}}}}});
  })();

  // ITUK register
  (function(){
    var f = P.families;
    new Chart(document.getElementById('cFam'),{type:'bar',
      data:{labels:f.map(function(x){return x.fam.replace('Intake Exhaust Emission','Exhaust / DPF');}),datasets:[{data:f.map(function(x){return x.share*100;}),backgroundColor:NAVY,borderRadius:2}]},
      options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return c.raw.toFixed(0)+'% of support';}}}},
        scales:{x:{grid:{color:LINE},ticks:{callback:function(v){return v+'%';}}},y:{grid:{display:false},ticks:{font:{size:10.5}}}}}});
    var b = P.bands;
    new Chart(document.getElementById('cBand'),{type:'bar',
      data:{labels:b.map(function(x){return x.label;}),datasets:[
        {label:'Share of cases',data:b.map(function(x){return x.lines_share*100;}),backgroundColor:SAND,borderRadius:2},
        {label:'Share of the money',data:b.map(function(x){return x.support_share*100;}),backgroundColor:TERRA,borderRadius:2}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:10.5}}},
        tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+c.raw.toFixed(0)+'%';},afterBody:function(it){var x=b[it[0].dataIndex];return x.lines+' lines, £'+Math.round(x.support).toLocaleString('en-GB');}}}},
        scales:{y:{beginAtZero:true,grid:{color:LINE},ticks:{callback:function(v){return v+'%';}}},x:{grid:{display:false},ticks:{font:{size:10.5}}}}}});
  })();

  function all(){ stateFromUI(); labels(); renderRes(); renderTable(); renderEarn(); }
  ['s_u','s_phi','s_p','s_b','s_d','s_y'].forEach(function(id){ document.getElementById(id).addEventListener('input', all); });
  document.getElementById('reset').addEventListener('click', function(){ Object.assign(S, JSON.parse(JSON.stringify(DEF))); setUI(); all(); });
  setUI(); all();
  window.__dlod = {calc:calc, netAll:netAll, S:S, P:P};
})();
"""


def main():
    chart = CHART.read_text(encoding="utf-8")
    chart = re.sub(r"//# sourceMappingURL=.*", "", chart)
    pj = json.dumps(payload, ensure_ascii=False, default=float)
    html = (
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Don't Lose the Deal, other distributors</title>"
        "<style>" + CSS + "</style></head><body>" + BODY +
        "<script type=\"application/json\" id=\"payload\">" + pj.replace("</", "<\\/") + "</script>"
        "<script>" + chart + "</script>"
        "<script>" + JS + "</script></body></html>"
    )
    HTML.write_text(html, encoding="utf-8")
    CMD.write_bytes(b'@echo off\r\nstart "" "%~dp0DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.html"\r\n')
    print("written", HTML, HTML.stat().st_size)


if __name__ == "__main__":
    main()
