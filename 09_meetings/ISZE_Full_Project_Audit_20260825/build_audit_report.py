# -*- coding: utf-8 -*-
"""Build ISZE Full Project Audit HTML (self-contained, chart-first, ~50 print pages)."""
from pathlib import Path

OUT = Path(__file__).resolve().parent
CHART = (OUT / "chart.umd.js").read_text(encoding="utf-8")
# strip any leftover source map
if "//# sourceMappingURL" in CHART:
    CHART = CHART.split("//# sourceMappingURL")[0]

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ISZE Full Project Audit — August 2026</title>
<style>
*{box-sizing:border-box;}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;font-size:10.5px;line-height:1.55;background:#fff;}
h1,h2,h3,h4{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0;}
@page{size:A4;margin:14mm 14mm 18mm 14mm;}
.cover{position:relative;min-height:267mm;margin:0;padding:28mm 22mm 20mm;
  background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;page-break-after:always;}
.cover h1{color:#fff;font-size:40px;line-height:1.1;max-width:160mm;}
.cover .rule{width:54mm;height:3px;background:#c0552d;margin:8mm 0 7mm;}
.cover .sub{font-size:15px;color:#c5d0e0;max-width:150mm;line-height:1.45;}
.cover .meta{position:absolute;bottom:22mm;left:22mm;right:22mm;font-size:11px;color:#9aabbf;
  display:flex;justify-content:space-between;border-top:1px solid rgba(255,255,255,.2);padding-top:4mm;}
.cover .verdict{margin-top:14mm;background:rgba(0,0,0,.22);border-left:3px solid #c0552d;padding:5mm 6mm;max-width:155mm;}
.cover .verdict strong{color:#fff;font-size:13px;}
.wrap{padding:0 2mm 8mm;}
h2.sec{font-size:17px;margin:7mm 0 2mm;padding-bottom:2mm;border-bottom:2px solid #1a2b4a;page-break-after:avoid;}
h2.sec .no{color:#c0552d;}
h3{font-size:12.5px;margin:4.5mm 0 1.5mm;color:#15233c;page-break-after:avoid;}
p{margin:0 0 2.2mm;}
ul,ol{margin:0 0 3mm;padding-left:4.5mm;}
li{margin-bottom:1.2mm;}
.page{page-break-before:always;}
.callout{border-left:3px solid #c0552d;background:#f7f4ee;padding:3mm 4mm;margin:3mm 0;page-break-inside:avoid;}
.callout.green{border-left-color:#1d9e75;}
.callout.red{border-left-color:#e24b4a;}
.callout.amber{border-left-color:#eda100;}
.kpi-row{display:flex;gap:3mm;flex-wrap:wrap;margin:3mm 0 4mm;}
.kpi{flex:1 1 38mm;min-width:36mm;background:#f7f4ee;border:1px solid #d9d3c8;padding:3mm 3.5mm;page-break-inside:avoid;}
.kpi .lbl{font-size:8.5px;text-transform:uppercase;letter-spacing:.04em;color:#6b6256;}
.kpi .val{font-family:Georgia,serif;font-size:20px;color:#15233c;margin-top:1mm;}
.kpi .note{font-size:8.5px;color:#6b6256;margin-top:1mm;}
.kpi.warn .val{color:#b23b3b;}
.kpi.ok .val{color:#2e7d54;}
table{width:100%;border-collapse:collapse;margin:2mm 0 4mm;font-size:9.2px;page-break-inside:avoid;}
th{background:#1a2b4a;color:#f7f4ee;text-align:left;padding:2.2mm 2.4mm;font-size:8.5px;text-transform:uppercase;}
td{padding:2mm 2.4mm;border-bottom:.5px solid #d9d3c8;vertical-align:top;}
tbody tr:nth-child(even){background:#f7f4ee;}
tr{page-break-inside:avoid;}
.tag{display:inline-block;font-size:8px;padding:.6mm 1.8mm;border-radius:2px;font-weight:600;letter-spacing:.03em;}
.tag-prod{background:#1a2b4a;color:#f7f4ee;}
.tag-pilot{background:#2a78d6;color:#fff;}
.tag-stub{background:#eda100;color:#15233c;}
.tag-dead{background:#888780;color:#fff;}
.tag-miss{background:#e24b4a;color:#fff;}
.tag-ok{background:#1d9e75;color:#fff;}
.chart-box{position:relative;width:100%;margin:2mm 0 4mm;page-break-inside:avoid;}
.two{display:flex;gap:4mm;}
.two > div{flex:1;}
.muted{color:#6b6256;font-size:9px;}
.footer{position:fixed;bottom:7mm;left:14mm;right:14mm;font-size:7.4px;color:#6b6256;
  display:flex;justify-content:space-between;border-top:.5px solid #d9d3c8;padding-top:1.2mm;}
.toc a{color:#15233c;text-decoration:none;}
.toc li{margin-bottom:1.6mm;}
.matrix td.g{background:#d8f0e4;color:#1a3d2e;}
.matrix td.a{background:#fce9c4;color:#5a3d00;}
.matrix td.r{background:#f6d4d2;color:#5a1a1a;}
.matrix td.n{background:#eef3f9;color:#222;}
.small{font-size:8.8px;}
.hr{height:0;border:0;border-top:1px solid #d9d3c8;margin:4mm 0;}
</style>
</head>
<body>
<div class="footer"><span>ISZE Full Project Audit · Confidential · Mode B internal</span><span>Audit as-of 25 Aug 2026</span></div>

<!-- ===================== COVER ===================== -->
<section class="cover">
  <div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#9aabbf;">Isuzu Europe · Aftersales Analytics</div>
  <h1>Full Project Audit</h1>
  <div class="rule"></div>
  <p class="sub">What would make ISZE the best parts sales analytics programme that exists — and how to get the best sales analyses on everything.</p>
  <div class="verdict">
    <strong>Verdict:</strong> ISZE is already a strong Level&nbsp;3 analytical operating system on the ISZE→DB spine
    (€103.57M parts base, PMS/GPS/BVP, green-gated facts). It is not yet world-class, because the decision loop is unfinished
    (23,236 ledger opportunities, 0 outcomes), dealer sell-out covers only 5 distributors, billing truth stops at 31 Mar 2026,
    and 1,677 files sit unsorted in INBOX. Best-in-class is not more dashboards — it is network sell-out/fill, locked interval
    assumptions, validated pocket price, and a weekly ledger→realised-€ cadence.
  </div>
  <div class="meta">
    <span>Prepared by Auto · 5 parallel audit agents · Outlook COM live</span>
    <span>Print length target ~50 pages</span>
  </div>
</section>

<div class="wrap">

<!-- ===================== TOC ===================== -->
<h2 class="sec"><span class="no">00</span> Contents</h2>
<ol class="toc">
  <li><a href="#s01">Executive summary &amp; scorecard</a></li>
  <li><a href="#s02">What “best in the world” means for Isuzu Europe parts</a></li>
  <li><a href="#s03">Capability maturity (L1–L5) — where we sit</a></li>
  <li><a href="#s04">Data we have — core data inventory</a></li>
  <li><a href="#s05">Data health — top 20 issues</a></li>
  <li><a href="#s06">Missing data — ranked unlocks</a></li>
  <li><a href="#s07">Emails &amp; mailbox — families, gaps, process failures</a></li>
  <li><a href="#s08">What we’re not doing — analytical methods</a></li>
  <li><a href="#s09">Surfaces catalog — production / pilot / stub / dead</a></li>
  <li><a href="#s10">Operating model gaps</a></li>
  <li><a href="#s11">Anti-patterns already in the repo</a></li>
  <li><a href="#s12">90-day plan to earn Level 4</a></li>
  <li><a href="#s13">12-month plan toward Level 5</a></li>
  <li><a href="#s14">Prioritized bets matrix</a></li>
  <li><a href="#s15">Appendix A — evidence paths</a></li>
  <li><a href="#s16">Appendix B — mail subject hits (live COM)</a></li>
  <li><a href="#s17">Appendix C — INBOX composition</a></li>
  <li><a href="#s18">Appendix D — closed doors (do not re-open)</a></li>
  <li><a href="#s19">Appendix E — quote discipline</a></li>
  <li><a href="#s20">Appendix F — one-page operator checklist</a></li>
</ol>

<div class="callout">
  <strong>How this audit was built.</strong> Parallel agents covered (1) data inventory, (2) mail/email families,
  (3) dashboards &amp; analytics maturity, (4) best-in-class strategy, (5) live Outlook COM probe.
  Numbers below are cited from FACTS / verification / ledger meta / live COM — not invented.
</div>

<!-- ===================== 01 EXEC ===================== -->
<h2 class="sec page" id="s01"><span class="no">01</span> Executive summary &amp; scorecard</h2>

<div class="kpi-row">
  <div class="kpi ok"><div class="lbl">Parts base</div><div class="val">€103.57M</div><div class="note">GPS-facing parts only · snapshot</div></div>
  <div class="kpi"><div class="lbl">sales_fact rows</div><div class="val">477,505</div><div class="note">2023-01-03 → 2026-03-31</div></div>
  <div class="kpi warn"><div class="lbl">Verify gate</div><div class="val">114 / 1 / 1</div><div class="note">pass / warn / fail · not green</div></div>
  <div class="kpi warn"><div class="lbl">INBOX backlog</div><div class="val">1,677</div><div class="note">files · ~477 MB unsorted</div></div>
  <div class="kpi"><div class="lbl">Ledger open rows</div><div class="val">23,236</div><div class="note">Open action rows — not euros · 20,572 PRICE_REVISION queue · €22.1M at stake separate · 0 outcomes</div></div>
  <div class="kpi"><div class="lbl">Maturity</div><div class="val">L3.7 / 5</div><div class="note">analytical OS; partial decision OS</div></div>
</div>

<p class="muted"><strong>How to read the radar:</strong> scale is 0–100. Blue = honest Today. Orange dashed = best-in-class ambition (outer ring, typically 85–95) — not a mid-chart “40” ring.</p>
<div class="two">
  <div class="chart-box" style="height:340px;"><canvas id="cScore" role="img" aria-label="Scorecard dimensions 0 to 100"></canvas></div>
  <div class="chart-box" style="height:340px;"><canvas id="cMaturity" role="img" aria-label="Maturity level bars"></canvas></div>
</div>

<h3>Five sentences that matter</h3>
<ol>
  <li><strong>The spine works.</strong> Billing → PMS capture → GPS SPU → BVP mix → early warning is production-grade on PRISM (:8503).</li>
  <li><strong>The channel is half-blind.</strong> Only five distributors have sell-out on disk; UMI (and DE/BE/PT/Nordics) are missing — elasticity and share-of-wallet stay blocked.</li>
  <li><strong>Time is stale at the core.</strong> <code>sales_fact</code> ends 31 Mar 2026 while newer raw (incl. Q1FY2027) already sits on disk — Apr–Aug 2026 is invisible to every derived KPI.</li>
  <li><strong>Mail is a goldmine with a broken conveyor.</strong> G0a interaction layer is live (9,001 rows); attachment intake for PartSales/StD is still manual; Online Archive / sap4* 2020–22 never landed.</li>
  <li><strong>Action without outcomes is inventory theatre.</strong> The Action Ledger correctly refuses invented realised € — but until Monday triage starts, 23k rows are a museum, not an OS.</li>
</ol>

<div class="callout green">
  <strong>What would make this the best project:</strong> every euro of the €103.57M parts base explained by
  parc × capture × mix × price × leakage × fleet opportunity — with a green quote gate and ledger outcomes —
  and ruthless refusal of closed doors / invented denominators.
</div>

<!-- ===================== 02 VISION ===================== -->
<h2 class="sec page" id="s02"><span class="no">02</span> What “best in the world” means here</h2>
<p>Retail-funnel language does not apply. ISZE sells to distributors (DB), who sell to dealers, who sell to fleets.
World-class aftersales analytics for this channel means the following eight truths are measurable, current, and actionable:</p>

<table>
  <thead><tr><th>Truth</th><th>Definition</th><th>Instrumented today?</th><th>Gap</th></tr></thead>
  <tbody>
    <tr><td>Wallet</td><td>GPS spend per UIO unit</td><td><span class="tag tag-ok">YES</span></td><td>CY2026 partial; CIS not in 18-db GPS</td></tr>
    <tr><td>Capture</td><td>PMS expected vs actual service demand</td><td><span class="tag tag-ok">YES</span></td><td>IML air:oil provisional; brake factor open</td></tr>
    <tr><td>Mix</td><td>Genuine vs BVP penetration</td><td><span class="tag tag-ok">YES</span></td><td>EPC supersession unvalidated</td></tr>
    <tr><td>Channel honesty</td><td>DB→DLR sell-out / leakage / SoW</td><td><span class="tag tag-pilot">PARTIAL</span></td><td>5 DBs only; UMI missing</td></tr>
    <tr><td>Pocket price</td><td>List → net realisation</td><td><span class="tag tag-pilot">PARTIAL</span></td><td>Lists landed; joins not validated</td></tr>
    <tr><td>Parc</td><td>UIO dual-lane discipline</td><td><span class="tag tag-ok">YES</span></td><td>v19; stale v17 copy warning</td></tr>
    <tr><td>Fleet R&amp;M</td><td>Tender addressable-if-won</td><td><span class="tag tag-pilot">PARTIAL</span></td><td>€1,488 on 3 sized rows; portals incomplete</td></tr>
    <tr><td>Cadence</td><td>Signal→action→realised €</td><td><span class="tag tag-stub">STUB</span></td><td>Ledger 0 outcomes; P4 draft</td></tr>
  </tbody>
</table>

<h3>Explicit non-goals (closed doors)</h3>
<ul>
  <li>Gross / SPA / condition columns on SAP billing — permanently unavailable; design around net + dated lists only.</li>
  <li>New AIM 0–100 pricing-risk score — null backtest; ambition retired.</li>
  <li>Quoting ISZE→DB price-volume elasticity — wrong grain; resume only on DB→DLR after sell-out coverage.</li>
  <li>Inventing CY GPS % or tender “expected revenue”.</li>
  <li>CRM rollout / call transcripts / live ERP write-back as critical path (org programmes, not analytics blockers).</li>
</ul>

<div class="callout">
  Best-in-class competitors (OEM aftersales intelligence) win on <em>dealer channel truth</em>, <em>fill/lost sales</em>,
  and <em>closed-loop campaign ROI</em>. ISZE already wins on capture mathematics and quote discipline. The gap is channel + loop.
</div>

<!-- ===================== 03 MATURITY ===================== -->
<h2 class="sec page" id="s03"><span class="no">03</span> Capability maturity — L1 to L5</h2>

<table class="matrix">
  <thead><tr><th>Level</th><th>Meaning</th><th>ISZE evidence</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>L1 Archive</td><td>Spreadsheets only</td><td>Exited years ago</td><td class="g">DONE</td></tr>
    <tr><td>L2 Reporting</td><td>Decks &amp; workbooks</td><td>Still present in meetings / GPS xlsx</td><td class="a">LINGERS</td></tr>
    <tr><td>L3 Analytical OS</td><td>Spine + dictionary + PRISM + verify</td><td>sales_fact 477k · fig_key 98.6% · PRISM live</td><td class="g">HOME</td></tr>
    <tr><td>L4 Decision OS</td><td>Quote gate, ledger, schedules, honest radar</td><td>Ledger built; gate currently red; triage empty</td><td class="a">PARTIAL</td></tr>
    <tr><td>L5 Closed-loop</td><td>Calibrated action→€; network sell-out; forecast</td><td>Not proven</td><td class="r">NOT YET</td></tr>
  </tbody>
</table>

<p class="muted">Assessment: <strong>L3.7 / 5</strong> — solid L3 with partial L4 artefacts that have not yet changed operating behaviour.</p>

<h3>L3 evidence (keep)</h3>
<ul>
  <li>Pipeline verify culture: 114 checks on 2026-08-25 (even when red, the gate exists).</li>
  <li>FACTS.md as single narrative authority with drift anchor.</li>
  <li>PRISM pages: GPS, PMS, BVP, Network Intelligence, Warranty, Realization, Parc, Sell-out, VPACC.</li>
  <li>Metric dictionary + data integrity flags documented.</li>
</ul>

<h3>L4 partial evidence (finish)</h3>
<ul>
  <li>Action Ledger: 23,236 open · adapter sum €22.1M (mixed bases — not one wallet) · 0 ACTIONED outcomes.</li>
  <li>P2a mail layer: 9,001 interactions · 926 commitments · 203 stakeholders · account_health draft.</li>
  <li>Tender engine: 211 notices / 186 opportunities · GPS floor €1,488 on 3 sized rows · honest nulls.</li>
  <li>Schedulers: Tender Monitor, PMS/IAM Refresh, LiveStateAudit — with known drift on retired folders.</li>
</ul>

<div class="chart-box" style="height:300px;"><canvas id="cGaps" role="img" aria-label="Unlock ranking"></canvas></div>

<!-- ===================== 04 DATA HAVE ===================== -->
<h2 class="sec page" id="s04"><span class="no">04</span> Data we have — core data inventory</h2>
<p>Under <code>01_data\</code>: <strong>2,527 files · ~2.2 GB</strong>. Having files is not the same as being ready for sales decisions. The core commercial datasets exist; what blocks decisions is freshness and incomplete dealer sell-out reporting.</p>

<div class="two">
  <div class="chart-box" style="height:320px;"><canvas id="cFolders" role="img" aria-label="Files by folder"></canvas></div>
  <div>
    <h3>Core datasets in active use</h3>
    <p class="small muted" style="margin:0 0 8px;">The working commercial data chain from ISZE billing through distributor capture, GPS, mix, and channel sales — not a folder dump.</p>
    <ul class="small">
      <li><strong>Billing</strong> — sales_fact.parquet (477,505) · CY23–25 raw · sales_2026tillApril · Israel GPS extract</li>
      <li><strong>UIO</strong> — v19 canonical under 06_uio\_CURRENT · VIN JP partial</li>
      <li><strong>PMS</strong> — pms_capture_by_db_year (~3,024) · opportunity matrix · service schedule PDFs</li>
      <li><strong>GPS</strong> — gps_spu_by_distributor · Calculator v9 · kickback/stretch pilots</li>
      <li><strong>BVP</strong> — catalog · genuine_bvp_crossref · mix tables</li>
      <li><strong>Pricing</strong> — PR00/ZPR1 2023–2026 history · Eucon 2023 · PartsPool 2026-03</li>
      <li><strong>Sell-out</strong> — ITUK, IUK, Ireland, Greece, UTI (holes) under 12_raw\dealer_sales</li>
      <li><strong>Warranty</strong> — CV/LCV 2025 · UMI to 2026-05</li>
      <li><strong>Tender</strong> — tender_data.json live 2026-08-25</li>
      <li><strong>Ops</strong> — action_ledger · ids_dealer_network · VPACC July</li>
      <li><strong>Mail facts</strong> — 17_interactions (G0a, no bodies)</li>
    </ul>
  </div>
</div>

<h3>Sell-out coverage — which distributors report dealer retail sales to ISZE</h3>
<p>We have sell-out files for five distributors (with gaps); UMI and most other markets have never filed. Without network sell-out we cannot measure share-of-wallet or true DB→dealer price elasticity — we see what we ship, not what dealers actually sell.</p>
<table>
  <thead><tr><th>Distributor</th><th>Raw</th><th>Long CSV</th><th>Period</th><th>Notes</th></tr></thead>
  <tbody>
    <tr><td>ITUK</td><td>CY2025 StD</td><td>missing long</td><td>2025</td><td>No CY2026 dealer×PN yet</td></tr>
    <tr><td>IUK (D-Max)</td><td>Demand Jul YTD</td><td>CY25 + CY26YTD</td><td>2025–Jul26</td><td>Qty only · ≠ ITUK</td></tr>
    <tr><td>Ireland (Harris)</td><td>StD</td><td>CY25 + CY26YTD</td><td>2025–Jul26</td><td>Qty only · ≠ IUK ≠ IMIE</td></tr>
    <tr><td>Greece (Petros)</td><td>Qties 2025</td><td>missing long</td><td>2025</td><td>pn_newest_rollup flag</td></tr>
    <tr><td>UTI 1799</td><td>PartSales months</td><td>missing long</td><td>2025 Aug–Dec + 2026 Jan–Jun</td><td><strong>2025 Feb–Jul hole</strong></td></tr>
    <tr><td>UMI 1797</td><td>—</td><td>—</td><td>—</td><td><span class="tag tag-miss">NEVER FILED</span></td></tr>
    <tr><td>DE / BE / PT / Nordics…</td><td>—</td><td>—</td><td>—</td><td><span class="tag tag-miss">NO FAMILY</span></td></tr>
  </tbody>
</table>

<div class="chart-box" style="height:260px;"><canvas id="cSellout" role="img" aria-label="Sell-out coverage"></canvas></div>

<!-- ===================== 05 HEALTH ===================== -->
<h2 class="sec page" id="s05"><span class="no">05</span> Data health — top 20 issues</h2>
<p>Ranked by impact on sales-analysis quality. Issues 1–5 block almost every “best analysis on everything” ambition.</p>

<table>
  <thead><tr><th>#</th><th>Issue</th><th>Impact</th><th>Evidence</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>sales_fact ends 2026-03-31 while newer raw exists (incl. Q1FY2027)</td><td>All derived KPIs blind to Apr–Aug 2026</td><td>verify + 12_raw\sales</td></tr>
    <tr><td>2</td><td>Sell-out only 5 DBs</td><td>No network SoW / DB→DLR elasticity</td><td>_registry.yaml</td></tr>
    <tr><td>3</td><td>No UMI sell-out (≠ UTI 1799)</td><td>Top billing ask unanswered</td><td>SELLOUT_COVERAGE_ASKS</td></tr>
    <tr><td>4</td><td>No DE / BE / PT (+Nordics) sell-out</td><td>Network analyses fake-complete</td><td>registry</td></tr>
    <tr><td>5</td><td>UTI 2025 Feb–Jul missing</td><td>YoY UTI sell-out broken</td><td>SOURCE hunt logs</td></tr>
    <tr><td>6</td><td>Long CSVs missing ITUK / UTI / Greece</td><td>Adapters fragile; second layer incomplete</td><td>00_derived</td></tr>
    <tr><td>7</td><td>LCV warranty ends Nov 2025</td><td>Warranty Intelligence incomplete</td><td>Warranty_LCV_2025</td></tr>
    <tr><td>8</td><td>Verify fail: raw_cy2025 expects CY2025.XLSX</td><td>Quote gate red (config drift)</td><td>_verification_report</td></tr>
    <tr><td>9</td><td>metrics_snapshot / isze_data lag (Aug 17–19 vs Aug 25)</td><td>Dashboards quote stale tiles</td><td>as_of timestamps</td></tr>
    <tr><td>10</td><td>INBOX 1,677 / ~477 MB unsorted</td><td>Landed sources not wired</td><td>90_INBOX</td></tr>
    <tr><td>11</td><td>ITUK StD = CY2025 only</td><td>No 2026 dealer×PN</td><td>ITUK folder</td></tr>
    <tr><td>12</td><td>List-to-pocket not validated</td><td>Leakage € not quotable</td><td>pricing history</td></tr>
    <tr><td>13</td><td>IAM/Eucon vintage mix</td><td>Competitor packs mislabelled</td><td>PartsPool vs Eucon 2023</td></tr>
    <tr><td>14</td><td>Net-only billing (closed)</td><td>SPA/mix discount split impossible</td><td>roadmap closed door</td></tr>
    <tr><td>15</td><td>PMS Flag C air:oil provisional; ITUK brake 0.4 vs 0.8 open</td><td>Capture € stories soft</td><td>FACTS / roadmap</td></tr>
    <tr><td>16</td><td>N35 PMS registry missing</td><td>Capture blind on N35 markets</td><td>OS map</td></tr>
    <tr><td>17</td><td>LCV SCR chassis cutoffs missing</td><td>Generation-aware intervals blocked</td><td>service_schedules</td></tr>
    <tr><td>18</td><td>Stale UIO v17 under prism</td><td>Verify warn; confusion risk</td><td>verification warn</td></tr>
    <tr><td>19</td><td>Tender value thin; portals incomplete</td><td>Hero € from 3 sized rows</td><td>god-tier checklist</td></tr>
    <tr><td>20</td><td>Manifest / dictionary path drift</td><td>Agents file to wrong homes</td><td>DATA_MANIFEST vs code</td></tr>
  </tbody>
</table>

<div class="callout red">
  <strong>Immediate quote-gate blocker:</strong> verification is not green (fail: missing flag <code>raw_cy2025</code>).
  Monthly refresh runbook requires 0 fail before external numbers move. Fix config alias or rename — do not pretend green.
</div>

<!-- ===================== 06 MISSING ===================== -->
<h2 class="sec page" id="s06"><span class="no">06</span> Missing data — ranked unlocks</h2>
<p>These are the datasets that unlock the next tier of sales analyses. Not “nice to have” — each removes a hard ceiling.</p>

<table>
  <thead><tr><th>Rank</th><th>Missing / incomplete</th><th>Unlocks</th><th>How to get it</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>SAP billing through latest closed month</td><td>Every KPI current; ledger outcomes measurable past Mar-31</td><td>Ingest Q1FY2027 + post-April extract → rebuild sales_fact</td></tr>
    <tr><td>2</td><td>UMI PartSales / StD</td><td>Israel LCV channel truth; elasticity</td><td>Mailbox subject hunt + DB ask</td></tr>
    <tr><td>3</td><td>DE / BE / PT / NO / SE sell-out PN×month</td><td>Network SoW</td><td>Ranked asks already drafted</td></tr>
    <tr><td>4</td><td>UTI PartSales 2025-02…07 (+ Jul 2026)</td><td>UTI YoY / elasticity</td><td>Human Save from Online Archive or chase UTI</td></tr>
    <tr><td>5</td><td>ITUK StD CY2026 YTD</td><td>Dealer leakage refresh</td><td>Duncan ask (draft exists)</td></tr>
    <tr><td>6</td><td>Emit long CSVs for ITUK/UTI/Greece</td><td>Stable adapters</td><td>Run existing builders from raw</td></tr>
    <tr><td>7</td><td>LCV claims Dec 2025+</td><td>Warranty Intelligence</td><td>Warranty export refresh</td></tr>
    <tr><td>8</td><td>IML air:oil ratio + ITUK brake evidence</td><td>Quotable capture €</td><td>IML / ITUK data drop</td></tr>
    <tr><td>9</td><td>IMIT LCV SCR cutoffs</td><td>Generation-weighted intervals</td><td>Chassis/reg-year map</td></tr>
    <tr><td>10</td><td>N35 PMS PN registry</td><td>N35 capture</td><td>ISZJ / catalogue work</td></tr>
    <tr><td>11</td><td>EPC-validated supersessions</td><td>Stop €2.48M blind billed-on-old</td><td>EPC join programme</td></tr>
    <tr><td>12</td><td>Signed list-to-pocket validation</td><td>Quotable leakage</td><td>Join QA on history lists</td></tr>
    <tr><td>13</td><td>Network fill / lost-sales</td><td>Ops KPI beyond ITUK leakage</td><td>New extract family</td></tr>
    <tr><td>14</td><td>VIN ITUK/UTI + AT/MT</td><td>Parc cohorts beyond JP</td><td>VIN packs</td></tr>
    <tr><td>15</td><td>Fresh IAM scrape with visible as-of</td><td>Honest Mode A competitor packs</td><td>Scheduler + labels</td></tr>
    <tr><td>16</td><td>Sort 90_INBOX → numbered folders</td><td>Wire landed gold (Gina margin, IDS, PMS)</td><td>Manifest §0 discipline</td></tr>
  </tbody>
</table>

<div class="chart-box" style="height:340px;"><canvas id="cUnlock" role="img" aria-label="Missing data unlock ranking"></canvas></div>

<!-- ===================== 07 EMAILS ===================== -->
<h2 class="sec page" id="s07"><span class="no">07</span> Emails &amp; mailbox</h2>
<p>Live COM probe 2026-08-25 on default store <strong>jerome.van.der.pluym@isuzu-e.com</strong>.
Also present: shared stores <strong>Sales</strong> and <strong>Parts</strong> (G0b gated — not scanned for content processing).</p>

<div class="kpi-row">
  <div class="kpi"><div class="lbl">Inbox items</div><div class="val">23,406</div></div>
  <div class="kpi"><div class="lbl">Sent items</div><div class="val">4,030</div></div>
  <div class="kpi"><div class="lbl">G0a interactions</div><div class="val">9,001</div><div class="note">kept of ~31.5k seen</div></div>
  <div class="kpi"><div class="lbl">Commitments</div><div class="val">926</div></div>
  <div class="kpi"><div class="lbl">Stakeholders</div><div class="val">203</div></div>
</div>

<div class="chart-box" style="height:280px;"><canvas id="cMail" role="img" aria-label="Mail subject hit counts"></canvas></div>

<h3>Mail families that feed sales analyses</h3>
<table>
  <thead><tr><th>Family</th><th>Sender / pattern</th><th>Cadence</th><th>On disk?</th><th>Gap</th></tr></thead>
  <tbody>
    <tr><td>UTI PartSales (live)</td><td>noreply2@uti.co.il</td><td>Monthly 1st</td><td>Aug–Nov 2025, Jan–Jun 2026</td><td>2025 Feb–Jul; Jul 2026+</td></tr>
    <tr><td>UTI PartSales (legacy)</td><td>sap4@ / sap4u@ / sap4uti@</td><td>2020–22</td><td>0 attachments via COM</td><td>Online Archive not in profile</td></tr>
    <tr><td>ITUK Sales to Dealers</td><td>Duncan / ITUK ad hoc</td><td>Annual-ish</td><td>CY2025 only</td><td>CY2026</td></tr>
    <tr><td>Ireland Harris StD</td><td>john.cummins@harrisgroup.ie</td><td>On ask</td><td>2025 + 2026 YTD Jul</td><td>ongoing cadence</td></tr>
    <tr><td>IUK Monthly Demand</td><td>IUK</td><td>Monthly</td><td>2025 + 2026→Jul</td><td>keep current</td></tr>
    <tr><td>Greece Petros</td><td>Petros</td><td>Ad hoc</td><td>CY2025</td><td>2026</td></tr>
    <tr><td>UMI sell-out</td><td>expected PartSales-like</td><td>—</td><td><span class="tag tag-miss">NONE</span></td><td>never filed</td></tr>
    <tr><td>Gina Z2SDAB42 margin</td><td>Gina Van Moere</td><td>~monthly</td><td>Jun/Jul 2026 pulled</td><td>not in pipeline</td></tr>
    <tr><td>Eucon</td><td>various</td><td>sporadic</td><td>body extracts + 2 zips</td><td>mailbox thin (2 Sent hits)</td></tr>
    <tr><td>PMS / intervals / Suzuki</td><td>various</td><td>project</td><td>134+27+19 in INBOX</td><td>sort owed</td></tr>
    <tr><td>G0a interaction facts</td><td>own mailbox MAPI</td><td>on run</td><td>17_interactions</td><td>pre-mid-2025 local cache empty</td></tr>
  </tbody>
</table>

<h3>Process failures (stop repeating)</h3>
<ol>
  <li><strong>Live-sender-only hunts</strong> miss archive senders (sap4*) — exhausting-data-sources skill’s known failure mode.</li>
  <li><strong>COM paints server hits</strong> but cannot save uncached Online Archive attachments.</li>
  <li><strong>No scheduled mailbox intake</strong> in AUTOMATION_REGISTER / RUNBOOK_MONTHLY_REFRESH — sell-out still manual scripts.</li>
  <li><strong>G0a ≠ attachment hunting</strong> — interaction facts store no bodies/atts; PartSales still needs a separate conveyor.</li>
  <li><strong>Split trees</strong> — scan logs under <code>02_dashboards\Data\</code> vs canonical raw under <code>01_data\</code>.</li>
  <li><strong>Wrong-grain first grabs</strong> (e.g. Rik margin PC aggregate before Gina PN masterdata).</li>
  <li><strong>Shared Sales/Parts</strong> are the highest-value corpus and highest privacy load — blocked until G0b + works council.</li>
</ol>

<div class="callout amber">
  <strong>Best practice conveyor:</strong> monthly scheduled intake for UTIPartSales + Gina Z2SDAB42 + Ireland StD
  (subject + size filters; Inbox/Sent). Human Save Attachments from the Outlook view that shows sap4*/Online Archive.
  Subject sweeps for UMI/DE/BE/PT → file → _registry.yaml → rebuild. Unify scan logs under 01_data.
</div>

<!-- ===================== 08 NOT DOING ===================== -->
<h2 class="sec page" id="s08"><span class="no">08</span> What we’re not doing</h2>
<p>Methods and products — not just datasets. Ranked by value for sales decisions.</p>

<div class="chart-box" style="height:360px;"><canvas id="cNotDoing" role="img" aria-label="What we are not doing"></canvas></div>

<table>
  <thead><tr><th>#</th><th>Missing capability</th><th>Why it matters</th><th>Blocker</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>Network-wide dealer sell-out / share of wallet</td><td>Channel truth for every DB meeting</td><td>Data coverage</td></tr>
    <tr><td>2</td><td>True price elasticity (DB→DLR)</td><td>Price moves without volume fiction</td><td>Sell-out coverage</td></tr>
    <tr><td>3</td><td>Fill rate / OTIF / lost-sales €</td><td>Ops + commercial same language</td><td>Extract family (IBX one-off only)</td></tr>
    <tr><td>4</td><td>Stock health / aging as ops KPI</td><td>Replenishment beyond exceptions CSV</td><td>Inventory extracts</td></tr>
    <tr><td>5</td><td>Campaign ROI / attach lift</td><td>Marketing calendar is schedule-only</td><td>Campaign tagging</td></tr>
    <tr><td>6</td><td>P4 as live call list</td><td>Who went quiet → Monday action</td><td>Threshold calibration</td></tr>
    <tr><td>7</td><td>Forecast go-live with owned overrides</td><td>P5 built (WAPE ~49%) but not product</td><td>G1 + governance</td></tr>
    <tr><td>8</td><td>Tender TAM with national portals</td><td>ES/IT/DE + Nordics keys</td><td>Keys / wiring</td></tr>
    <tr><td>9</td><td>Outcome attribution on ledger</td><td>Prove action→€ (co-movement only today)</td><td>Human triage + fresher billing</td></tr>
    <tr><td>10</td><td>Signal→order latency KPI</td><td>Roadmap’s missing retail translation</td><td>P4 + billing horizon</td></tr>
    <tr><td>11</td><td>Stakeholder decision-rights map</td><td>203 contacts ≠ RACI</td><td>Method + G0b for shared mbx</td></tr>
    <tr><td>12</td><td>EPC-validated supersession analytics</td><td>Stop silent billed-on-old</td><td>EPC programme</td></tr>
    <tr><td>13</td><td>Tender win→parts attach loop</td><td>Fleet R&amp;M → aftersales</td><td>Pilot design</td></tr>
    <tr><td>14</td><td>Email→action drafts (P3)</td><td>Cycle-time</td><td>G0b + approved LLM route</td></tr>
  </tbody>
</table>

<div class="callout green">
  <strong>Already world-class-adjacent (do not rebuild):</strong> PMS capture mathematics, GPS SPU, BVP mix,
  early warning / defection, quote discipline (FACTS gate), tender product-fit honesty (null not zero).
</div>

<!-- ===================== 09 SURFACES ===================== -->
<h2 class="sec page" id="s09"><span class="no">09</span> Surfaces catalog</h2>
<p>~273 HTML files under dashboards; the product set is much smaller. Maturity tags below.</p>

<h3>Production</h3>
<ul class="small">
  <li>PRISM Home / Early Warning / GPS / PMS / BVP / Network Intelligence / Decision / ITUK Hub / Review Pack / Data Integrity</li>
  <li>AIM CY2026 billing HTML · Risk Cockpit · Monthly Sales Tracker · Part Groups · Competitiveness</li>
  <li>Fleet: UIO v19 HTML, GPS HTML, ZEV Golden Window, Plan 2030</li>
  <li>IDS dealer compare packs · Tender scrape (weekly) · Aftermarket BI Command Center · Master Hub</li>
</ul>

<h3>Pilot</h3>
<ul class="small">
  <li>Dealer Sell-out (5 DBs) · Price Realization · Warranty · Parc Cohorts · VPACC</li>
  <li>P5 Forecast (built; go-live open) · Pricing Full/History/Engine/IAM · DB→DLR Replenishment</li>
  <li>Action Ledger · Tender PRISM tab · ~18 one-DB Operating Dashboards · IBX fill-rate one-off</li>
</ul>

<h3>Stub / not KPI yet</h3>
<ul class="small">
  <li>P4 Account health (parquet live; draft thresholds; no Mode A widget)</li>
  <li>PMS Marketing Calendar (no ROI) · Master/HTML V4 Supabase live KPIs (creds open)</li>
</ul>

<h3>Abandoned / deferred</h3>
<ul class="small">
  <li>AIM pricing-risk score · db_aftersales_risk · ISZE→DB elasticity quotes</li>
  <li>Fitted oil-filter hazard · gross/SPA on billing · legacy gps_dashboard · Autodoc scrapers</li>
</ul>

<div class="callout red">
  <strong>Duplication risk:</strong> intentional twins (PRISM ↔ bi HTML) are fine if rebuilt together.
  Orphans: stale Master links, CY2025 AIM leftovers, GPS stubs, PartGroups OFFLINE, inbox HTML under dashboards.
  Quote FACTS/PRISM only when decks disagree.
</div>

<div class="chart-box" style="height:260px;"><canvas id="cSurfaces" role="img" aria-label="Surface maturity mix"></canvas></div>

<!-- ===================== 10 OPS MODEL ===================== -->
<h2 class="sec page" id="s10"><span class="no">10</span> Operating model gaps</h2>
<ol>
  <li><strong>Quote gate currently red</strong> — runbook requires 0 fail; today 1 fail + 1 warn.</li>
  <li><strong>INBOX rule violated at scale</strong> — 1,677 files means “sorting owed” is not a footnote; it is the operating model failure.</li>
  <li><strong>Path alias confusion</strong> — runbook aliases (<code>derived\</code> / <code>_INBOX\</code>) vs numbered folders create dual mental models.</li>
  <li><strong>Mail governance</strong> — G0a complete; G0b (shared Sales/Parts + LLM) blocks the highest-value corpus.</li>
  <li><strong>Decision→action</strong> — ledger built, triage empty, outcomes empty by design until humans edit decisions CSV.</li>
  <li><strong>Billing horizon</strong> — 2026-03-31 blocks measurable outcomes; fresher extract is an ops act, not a model act.</li>
  <li><strong>Scheduler hygiene</strong> — retired job folders still on disk; LiveStateAudit exists to catch drift — read it.</li>
  <li><strong>Multi-UI drift</strong> — Streamlit :8503 is canonical; HTML twins + meeting decks + Evidence freeze intent must be enforced.</li>
  <li><strong>IDS Pull scorecard blank</strong> — process cadence without measurement.</li>
  <li><strong>No mailbox intake job</strong> — every sell-out month is a hero hunt.</li>
</ol>

<div class="chart-box" style="height:280px;"><canvas id="cLedger" role="img" aria-label="Action ledger adapter composition"></canvas></div>
<p class="muted">Ledger adapter in-counts (2026-08-25): revision_exception_queue dominates (20,572). Triage must filter to Book B / leakage / defection — not browse 23k rows.</p>

<!-- ===================== 11 ANTI-PATTERNS ===================== -->
<h2 class="sec page" id="s11"><span class="no">11</span> Anti-patterns already visible</h2>
<table>
  <thead><tr><th>Anti-pattern</th><th>Evidence</th><th>Fix</th></tr></thead>
  <tbody>
    <tr><td>Orphan / stub HTML left discoverable</td><td>Cleanup plan · Master stale links</td><td>Retire or unlink</td></tr>
    <tr><td>Four UI stacks → KPI drift</td><td>PRISM / HTML / decks / gpt_safe</td><td>FACTS wins; twins rebuild together</td></tr>
    <tr><td>Root dumps vs INBOX rule</td><td>DATA_MANIFEST §0</td><td>Empty INBOX; no root drops</td></tr>
    <tr><td>Obsolete capture quotes</td><td>FACTS DO NOT QUOTE list</td><td>Delete from memory/decks</td></tr>
    <tr><td>ITUK lane conflation</td><td>IML 22,389 vs PRISM 23,068</td><td>Label every slide</td></tr>
    <tr><td>Shipping scores after null science</td><td>AIM; oil λ</td><td>Keep killed</td></tr>
    <tr><td>Quoting leakage before validation</td><td>OS map</td><td>Internal only</td></tr>
    <tr><td>Hero KPIs from tiny subsets</td><td>Tender €1,488 / 3 rows</td><td>Always show n</td></tr>
    <tr><td>Assume green gate while fail open</td><td>verify 2026-08-25</td><td>Fix or withhold</td></tr>
    <tr><td>Ledger obesity without triage</td><td>23k / 0 outcomes</td><td>Monday ritual</td></tr>
    <tr><td>Historical tender headlines as current</td><td>god-tier P3 PARTIAL</td><td>Align release notes</td></tr>
    <tr><td>Paired-basket mix traps</td><td>design uses whole-book mix</td><td>Keep discipline</td></tr>
    <tr><td>Flag H CR/RE exclusion unlabelled</td><td>FACTS</td><td>Always say judgment call</td></tr>
  </tbody>
</table>

<!-- ===================== 12 NINETY DAYS ===================== -->
<h2 class="sec page" id="s12"><span class="no">12</span> 90-day plan — earn Level 4</h2>
<p>Ten bets. Each is completable without CRM, Graph consent, or inventing denominators.</p>
<ol>
  <li><strong>Permanent green quote gate</strong> — clear raw_cy2025 fail; delete or quarantine stale UIO v17.</li>
  <li><strong>Refresh sales_fact</strong> past 2026-03-31 (ingest Q1FY2027 + latest month).</li>
  <li><strong>Weekly ledger triage</strong> — Book B / leakage / defection only → action_ledger_decisions.csv; never invent realised_eur.</li>
  <li><strong>P4 threshold calibration</strong> then thin Mode A widget (or PRISM internal).</li>
  <li><strong>One more large-DB sell-out</strong> on long schema — prefer UMI.</li>
  <li><strong>Sign off list-to-pocket or keep leakage internal</strong> — stop the half-quote.</li>
  <li><strong>IML air:oil + ITUK brake evidence</strong> — lock or explicitly provisional-label.</li>
  <li><strong>Tender honesty pass</strong> — release notes = live 211/186 / €1,488; Nordics keys if available.</li>
  <li><strong>IAM vintage labels</strong> on Mode A competitor packs.</li>
  <li><strong>Empty INBOX</strong> — sort Gina margin, IDS packs, PMS pulls; fix runbook paths; add monthly mailbox intake skill.</li>
</ol>

<div class="callout">
  Success criterion for day 90: verify 0 fail; sales_fact as-of ≥ latest closed month; ≥1 ledger outcome cohort with billing window closed;
  ≥6 DBs on sell-out long schema; INBOX &lt; 50 files.
</div>

<!-- ===================== 13 TWELVE MONTHS ===================== -->
<h2 class="sec page" id="s13"><span class="no">13</span> 12-month plan — approach Level 5</h2>
<ol>
  <li>Network sell-out + fill as standard DB product (not a hero project).</li>
  <li>Resume DB→DLR elasticity only after coverage threshold.</li>
  <li>Order-rate × parc forecast v0 + WAPE baseline with owned overrides.</li>
  <li>EPC supersession programme with IML/ISZJ.</li>
  <li>LCV generation-weighted intervals (IMIT cutoffs).</li>
  <li>N35 PMS registry.</li>
  <li>VIN ITUK/UTI + AT/MT map.</li>
  <li>Decision-rights map from stakeholder_dim (+ G0b if approved).</li>
  <li>Tender→IDS dealer→parts attach pilot.</li>
  <li>PIC Pull scorecard live.</li>
</ol>
<p><strong>Off critical path:</strong> CRM, Graph admin consent, live ERP write-back.</p>
<p><strong>Don’t bet:</strong> new AIM scores; invent CY GPS%; tender GPS floor as market potential; IDS correlation revival; gross/SPA re-ask.</p>

<!-- ===================== 14 MATRIX ===================== -->
<h2 class="sec page" id="s14"><span class="no">14</span> Prioritized bets matrix</h2>
<table class="matrix">
  <thead><tr><th>Bet</th><th>Impact</th><th>Effort</th><th>Dependency</th><th>Do when</th></tr></thead>
  <tbody>
    <tr><td>Fix verify + refresh sales_fact</td><td class="g">Critical</td><td class="g">Low–Med</td><td class="n">SAP extract</td><td class="g">Week 1</td></tr>
    <tr><td>Monday ledger triage ritual</td><td class="g">Critical</td><td class="g">Low</td><td class="n">None</td><td class="g">Week 1</td></tr>
    <tr><td>Sort INBOX / wire Gina</td><td class="a">High</td><td class="a">Med</td><td class="n">Time</td><td class="g">Weeks 1–3</td></tr>
    <tr><td>UMI sell-out</td><td class="g">Critical</td><td class="a">Med</td><td class="a">DB / mail</td><td class="a">Month 1–2</td></tr>
    <tr><td>P4 calibrate + widget</td><td class="a">High</td><td class="a">Med</td><td class="n">Calibration</td><td class="a">Month 1–2</td></tr>
    <tr><td>List-to-pocket validation</td><td class="a">High</td><td class="a">Med</td><td class="n">History lists</td><td class="a">Month 2</td></tr>
    <tr><td>DE/BE/PT sell-out</td><td class="g">Critical</td><td class="r">High</td><td class="a">DB asks</td><td class="a">Q4–Q1</td></tr>
    <tr><td>Fill / lost-sales product</td><td class="a">High</td><td class="r">High</td><td class="r">New extracts</td><td class="r">H1</td></tr>
    <tr><td>Campaign ROI</td><td class="a">Med–High</td><td class="r">High</td><td class="a">Tagging</td><td class="r">H1</td></tr>
    <tr><td>Forecast go-live</td><td class="a">Med–High</td><td class="a">Med</td><td class="a">G1</td><td class="a">After billing fresh</td></tr>
    <tr><td>G0b shared mail + LLM</td><td class="a">High</td><td class="r">Org</td><td class="r">Works council</td><td class="r">When approved</td></tr>
    <tr><td>More dashboard shells</td><td class="r">Low</td><td class="g">Low</td><td class="n">—</td><td class="r">Do not</td></tr>
  </tbody>
</table>

<!-- ===================== 15 APPENDIX A ===================== -->
<h2 class="sec page" id="s15"><span class="no">15</span> Appendix A — evidence paths</h2>
<ul class="small">
  <li>Workspace index — <code>C:\Users\jerom\Desktop\claude\ISZE\INDEX.md</code></li>
  <li>FACTS — <code>...\ISZE\FACTS.md</code></li>
  <li>Roadmap — <code>...\00_docs\ISZE_ROADMAP.md</code></li>
  <li>AI sales intelligence — <code>...\00_docs\roadmaps\ai_sales_intelligence.md</code></li>
  <li>OS data map — <code>...\00_docs\ISZE_OS_DATA_MAP.yaml</code></li>
  <li>Data manifest — <code>...\01_data\DATA_MANIFEST.md</code></li>
  <li>Verify — <code>...\01_data\00_derived\_verification_report.md</code></li>
  <li>Metrics snapshot — <code>...\01_data\00_derived\metrics_snapshot.json</code></li>
  <li>Sell-out registry — <code>...\01_data\12_raw\dealer_sales\_registry.yaml</code></li>
  <li>Interactions — <code>...\01_data\17_interactions\</code></li>
  <li>G0a scope — <code>...\00_docs\G0A_LOCAL_MAIL_SCOPE.md</code></li>
  <li>Action ledger review — <code>...\01_data\00_derived\ACTION_LEDGER_REVIEW_20260825.md</code></li>
  <li>Tender god-tier — <code>...\04_tools\ISZE_Tender_Monitor_Install\_GODTIER_CHECKLIST.md</code></li>
  <li>Automation register — <code>...\00_docs\AUTOMATION_REGISTER.md</code></li>
  <li>PRISM — <code>...\03_analytics\Isuzu\prism\</code></li>
  <li>This report folder — <code>...\09_meetings\ISZE_Full_Project_Audit_20260825\</code></li>
</ul>

<!-- ===================== 16 APPENDIX B ===================== -->
<h2 class="sec page" id="s16"><span class="no">16</span> Appendix B — live mail subject hits</h2>
<p>Restrict on default Inbox + Sent only (2026-08-25). Count only; no bodies downloaded.</p>
<table>
  <thead><tr><th>Family</th><th>Inbox</th><th>Sent</th><th>Total</th></tr></thead>
  <tbody>
    <tr><td>UTIPartSales / PartSales</td><td>11</td><td>12</td><td>23</td></tr>
    <tr><td>Sales to Dealer</td><td>18</td><td>16</td><td>34</td></tr>
    <tr><td>Kickback</td><td>24</td><td>17</td><td>41</td></tr>
    <tr><td>GPS (noisy)</td><td>29</td><td>38</td><td>67</td></tr>
    <tr><td>Eucon</td><td>0</td><td>2</td><td>2</td></tr>
    <tr><td>PMS</td><td>137</td><td>48</td><td>185</td></tr>
  </tbody>
</table>
<p class="muted">Not searched: Sales/Parts stores, Online Archive, deep subfolders beyond Inbox/Sent roots.</p>

<!-- ===================== 17 APPENDIX C ===================== -->
<h2 class="sec page" id="s17"><span class="no">17</span> Appendix C — INBOX composition (top)</h2>
<table>
  <thead><tr><th>Subfolder</th><th>Files</th><th>Role</th></tr></thead>
  <tbody>
    <tr><td>IDS_2026</td><td>970</td><td>Dealer eval packs — sort to 08_Distributor / IDS</td></tr>
    <tr><td>pms_intervals_mail_pull</td><td>134</td><td>Service interval sources</td></tr>
    <tr><td>margin_analysis_mail_pull</td><td>53</td><td>Includes Gina Z2SDAB42 — wire to pricing</td></tr>
    <tr><td>_ireland_sales_mail_20260813</td><td>53</td><td>Already partially filed to 12_raw</td></tr>
    <tr><td>UTI_PartSales_mail_20260813</td><td>50</td><td>Canonical months → 12_raw\UTI</td></tr>
    <tr><td>tomoe_ids_mail_pull</td><td>36</td><td>IDS correspondence</td></tr>
    <tr><td>dealer_sales_mail_20260813</td><td>25</td><td>Multi-DB hunt residue</td></tr>
    <tr><td>suzuki_pms_mail_pull (+ transcript)</td><td>46</td><td>PMS programme</td></tr>
    <tr><td>UTI_PartSales_mail_sap4_20260813</td><td>21</td><td>Misnamed — recent noreply-era, not 2020–22</td></tr>
    <tr><td>warranty_audit_2026-07-27</td><td>23</td><td>Warranty QA</td></tr>
  </tbody>
</table>
<p>Steady-state target per DATA_MANIFEST §0: <strong>empty INBOX</strong>.</p>

<!-- ===================== 18 CLOSED DOORS ===================== -->
<h2 class="sec page" id="s18"><span class="no">18</span> Appendix D — closed doors</h2>
<ul>
  <li>Gross / SPA / condition on billing extract — cannot provide; net-only forever.</li>
  <li>AIM pricing-risk 0–100 — null backtest; do not ship a replacement score onto pages 7/16.</li>
  <li>Fitted oil-filter λ replacing bucketed constants — null holdouts; leave constants.</li>
  <li>ISZE→DB elasticity as quotable product — wrong grain.</li>
  <li>IDS→sales correlation models — scan failed; closed.</li>
  <li>Invent CY GPS % or tender expected revenue.</li>
  <li>Auto-send outbound mail — architecturally excluded.</li>
  <li>Psychometric profiling of named individuals — never.</li>
</ul>

<!-- ===================== 19 QUOTE ===================== -->
<h2 class="sec page" id="s19"><span class="no">19</span> Appendix E — quote discipline</h2>
<ul>
  <li>FACTS.md wins over decks, memory, GPT files, and this report if they drift.</li>
  <li>ITUK PMS has two correct lanes (IML v7 vs PRISM network) — never quote one without labelling.</li>
  <li>Ledger €22.1M is sum of mixed-basis source cells — not one wallet.</li>
  <li>Tender GPS €1,488 is addressable-if-won on 3 sized rows — not market potential.</li>
  <li>Account health thresholds are draft until Jerome calibrates — not a KPI.</li>
  <li>Do not quote leakage € until list-to-pocket joins are validated.</li>
  <li>Flag H CR/RE exclusion (~€1.65M) is a judgment call, not ERP-confirmed.</li>
</ul>

<!-- ===================== 20 CHECKLIST ===================== -->
<h2 class="sec page" id="s20"><span class="no">20</span> Appendix F — operator checklist (one page)</h2>
<table>
  <thead><tr><th>When</th><th>Do</th><th>Done when</th></tr></thead>
  <tbody>
    <tr><td>Every Monday</td><td>Triage top Book B / leakage / defection into decisions CSV</td><td>≥5 rows ACTIONED or REJECTED with reason</td></tr>
    <tr><td>Every month</td><td>Pull UTIPartSales + Ireland StD + Gina margin; file from INBOX</td><td>Registry updated; INBOX empty of new drops</td></tr>
    <tr><td>Every month</td><td>SAP billing extract → rebuild sales_fact → verify</td><td>0 fail; metrics_snapshot refreshed</td></tr>
    <tr><td>Every month</td><td>UIO staleness + IAM scrape as-of labels</td><td>Alerts clear or owned</td></tr>
    <tr><td>Every quarter</td><td>Sell-out coverage ask for next missing DB</td><td>One new long CSV family</td></tr>
    <tr><td>Before any external deck</td><td>Read FACTS + green verify</td><td>Numbers match snapshot</td></tr>
    <tr><td>Never</td><td>Invent realised €, capture denominators, or CY GPS%</td><td>—</td></tr>
  </tbody>
</table>

<div class="callout" style="margin-top:8mm;">
  <strong>Closing line.</strong> ISZE already has the hard part: a real analytical OS with integrity culture.
  Becoming the best project that exists is now an operating problem — fresher billing, network sell-out,
  sorted INBOX, and a ledger that closes loops — not a dashboard problem.
</div>

<p class="muted" style="margin-top:6mm;">
  Bronnen: FACTS.md · verification 2026-08-25 · metrics_snapshot 2026-08-17 · action_ledger meta 2026-08-25 ·
  dealer_sales _registry.yaml · G0a interaction meta 2026-08-12 · live Outlook COM 2026-08-25 ·
  ISZE_ROADMAP · ai_sales_intelligence · ISZE_OS_DATA_MAP · Tender god-tier checklist · DATA_MANIFEST.
  Indicatief audit — geen vervanging van FACTS voor externe citatie.
</p>

</div><!-- wrap -->

<script>
__CHART_JS__
</script>
<script>
(function(){
  var ink='#52514e', grid='#e1e0d9';
  var navy='#1a2b4a', terr='#c0552d', blue='#2a78d6', grey='#888780', green='#1d9e75', amber='#eda100', red='#e24b4a';

  var axisTips={
    'Spine integrity':'Spine on PRISM is production-grade. Not the commercial blocker.',
    'Freshness':'Billing through Jun 2026; Jul–Aug SAP extract still missing.',
    'Sell-out coverage':'5 DBs only. UMI + DE/BE/PT/Nordics missing — SoW/elasticity blocked.',
    'Price honesty':'Lists landed; list-to-pocket joins not signed off.',
    'Mail→action':'G0a live; PartSales/StD intake still manual.',
    'Ops loop':'Ledger built; 0 outcomes until Monday triage closes loops.',
    'Tender honesty':'Thin sized set + incomplete portals — not market potential.',
    'Quote gate':'Verify green 116/0/0; keep process bar for external decks.'
  };
  new Chart(document.getElementById('cScore'),{type:'radar',
    data:{labels:['Spine integrity','Freshness','Sell-out coverage','Price honesty','Mail→action','Ops loop','Tender honesty','Quote gate'],
      datasets:[
        {label:'Today',data:[90,58,28,55,48,22,45,82],
          backgroundColor:'rgba(42,120,214,0.14)',borderColor:blue,pointBackgroundColor:blue,
          pointRadius:4,pointHoverRadius:6,borderWidth:2.5},
        {label:'Best-in-class target',data:[95,90,90,85,85,90,85,95],
          backgroundColor:'transparent',borderColor:terr,pointBackgroundColor:terr,
          pointRadius:3,pointHoverRadius:5,borderWidth:2.5,borderDash:[6,4]}
      ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{position:'bottom',labels:{boxWidth:12,font:{size:11},color:ink}},
        tooltip:{callbacks:{
          title:function(items){return items[0].label;},
          label:function(ctx){
            var tip=axisTips[ctx.label]||'';
            return ctx.dataset.label+': '+ctx.raw+'/100 — '+tip;
          }
        }}
      },
      scales:{r:{min:0,max:100,
        ticks:{stepSize:25,color:ink,backdropColor:'transparent',showLabelBackdrop:false,font:{size:9},
          callback:function(v){return (v===0||v===50||v===100)?v:'';}},
        grid:{color:function(c){return c.tick&&c.tick.value===100?'rgba(192,85,45,0.35)':grid;}},
        angleLines:{color:grid},
        pointLabels:{font:{size:10},color:navy}}}}});

  new Chart(document.getElementById('cMaturity'),{type:'bar',
    data:{labels:['L1 Archive','L2 Reporting','L3 Analytical OS','L4 Decision OS','L5 Closed-loop'],
      datasets:[{data:[100,100,92,45,8],
        backgroundColor:[green,green,green,amber,red],borderRadius:4,barThickness:22}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},title:{display:true,text:'Capability readiness by level (honest %)',color:navy,font:{family:'Georgia',size:13}}},
      scales:{x:{max:100,grid:{color:grid},ticks:{color:ink}},y:{grid:{display:false},ticks:{color:ink}}}}});

  new Chart(document.getElementById('cGaps'),{type:'bar',
    data:{labels:['Billing freshness','UMI sell-out','DE/BE/PT sell-out','UTI Feb–Jul hole','Long CSV builders','LCV warranty Dec+','Verify config','INBOX sort','List-to-pocket','PMS factors'],
      datasets:[{label:'Unlock value (1–10)',data:[10,9,9,8,7,7,8,8,7,7],
        backgroundColor:[terr,terr,terr,blue,blue,grey,terr,blue,blue,grey],borderRadius:4,barThickness:16}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},title:{display:true,text:'Top unlock priorities',color:navy,font:{family:'Georgia',size:13}}},
      scales:{x:{max:10,grid:{color:grid},ticks:{color:ink}},y:{grid:{display:false},ticks:{color:ink,font:{size:9}}}}}});

  new Chart(document.getElementById('cFolders'),{type:'bar',
    data:{labels:['90_INBOX','00_derived','01_Pricing','03_PMS','91_build','92_archive','14_dashboards','12_raw','11_planning','others'],
      datasets:[{data:[1677,285,181,43,55,40,32,28,22,186],
        backgroundColor:[terr,navy,blue,grey,grey,grey,blue,green,amber,grey],borderRadius:3,barThickness:18}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},title:{display:true,text:'Files by 01_data folder',color:navy,font:{family:'Georgia',size:13}}},
      scales:{x:{grid:{color:grid},ticks:{color:ink}},y:{grid:{display:false},ticks:{color:ink,font:{size:9}}}}}});

  new Chart(document.getElementById('cSellout'),{type:'doughnut',
    data:{labels:['ITUK','IUK','Ireland','Greece','UTI (partial)','UMI missing','Other DBs missing'],
      datasets:[{data:[1,1,1,1,1,1,12],
        backgroundColor:[green,green,green,green,amber,red,grey],borderWidth:2,borderColor:'#fff'}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'right',labels:{boxWidth:10,font:{size:10}}},
        title:{display:true,text:'Sell-out coverage (illustrative DB slots)',color:navy,font:{family:'Georgia',size:13}}}}});

  new Chart(document.getElementById('cUnlock'),{type:'bar',
    data:{labels:['SAP fresh extract','UMI StD','DE/BE/PT sell-out','UTI hole fill','ITUK CY2026','Long CSVs','LCV warranty','IML factors','SCR cutoffs','N35 registry','EPC super','List-pocket','Fill/lost','VIN packs','IAM as-of','INBOX sort'],
      datasets:[{data:[10,9,9,8,7,7,6,7,6,6,7,7,8,5,5,8],
        backgroundColor:function(c){var v=c.raw;return v>=9?terr:(v>=7?blue:grey);},borderRadius:3,barThickness:14}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},title:{display:true,text:'Missing-data unlock score (1–10)',color:navy,font:{family:'Georgia',size:13}}},
      scales:{x:{max:10,grid:{color:grid},ticks:{color:ink}},y:{grid:{display:false},ticks:{color:ink,font:{size:8.5}}}}}});

  new Chart(document.getElementById('cMail'),{type:'bar',
    data:{labels:['PMS','GPS','Kickback','Sales to Dealer','UTIPartSales','Eucon'],
      datasets:[{label:'Inbox+Sent hits',data:[185,67,41,34,23,2],
        backgroundColor:[navy,blue,blue,green,terr,grey],borderRadius:4,barThickness:22}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},title:{display:true,text:'Live subject hits (default store)',color:navy,font:{family:'Georgia',size:13}}},
      scales:{x:{grid:{color:grid},ticks:{color:ink}},y:{grid:{display:false},ticks:{color:ink}}}}});

  new Chart(document.getElementById('cNotDoing'),{type:'bar',
    data:{labels:['Network sell-out/SoW','DB→DLR elasticity','Fill/OTIF/lost sales','Stock aging KPI','Campaign ROI','P4 live call list','Forecast go-live','Tender national portals','Ledger outcomes','Signal→order KPI','Decision-rights map','EPC supersession','Tender→parts attach','Email→action (P3)'],
      datasets:[{label:'Priority',data:[10,9,9,8,8,8,7,7,10,8,6,7,6,5],
        backgroundColor:[terr,terr,terr,blue,blue,blue,amber,amber,terr,blue,grey,blue,grey,grey],borderRadius:3,barThickness:13}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},title:{display:true,text:'What we are not doing — priority',color:navy,font:{family:'Georgia',size:13}}},
      scales:{x:{max:10,grid:{color:grid},ticks:{color:ink}},y:{grid:{display:false},ticks:{color:ink,font:{size:8.5}}}}}});

  new Chart(document.getElementById('cSurfaces'),{type:'doughnut',
    data:{labels:['Production','Pilot','Stub','Abandoned/deferred'],
      datasets:[{data:[14,12,3,6],backgroundColor:[green,blue,amber,grey],borderWidth:2,borderColor:'#fff'}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'right',labels:{boxWidth:10}},
        title:{display:true,text:'Major surface maturity (counts)',color:navy,font:{family:'Georgia',size:13}}}}});

  new Chart(document.getElementById('cLedger'),{type:'bar',
    data:{labels:['revision_exception','replenishment','Book B top500','defection','ITUK leakage','leakage Monday','no_PR00','early_warning','acct_health'],
      datasets:[{data:[20572,1595,500,265,260,40,31,19,16],
        backgroundColor:[terr,blue,navy,red,amber,amber,grey,grey,green],borderRadius:3,barThickness:16}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},title:{display:true,text:'Action ledger adapter row counts',color:navy,font:{family:'Georgia',size:13}}},
      scales:{x:{type:'logarithmic',min:10,max:50000,grid:{color:grid},
        ticks:{color:ink,callback:function(v){return [10,100,1000,10000].indexOf(v)>=0?v.toLocaleString('en-GB'):'';}}},
        y:{grid:{display:false},ticks:{color:ink,font:{size:9}}}}}});
})();
</script>
</body>
</html>
"""

html = HTML.replace("__CHART_JS__", CHART)
out_html = OUT / "ISZE_Full_Project_Audit_20260825.html"
out_html.write_text(html, encoding="utf-8")
print("Wrote", out_html, "bytes", out_html.stat().st_size)

# CDN check
import re
srcs = re.findall(r'(?:src|href)=["\'](https?://[^"\']+)', html)
print("external src/href count:", len(srcs))
if srcs:
    print(srcs[:5])
