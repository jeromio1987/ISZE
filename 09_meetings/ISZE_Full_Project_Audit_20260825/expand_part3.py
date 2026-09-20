# -*- coding: utf-8 -*-
from pathlib import Path
import re

html_path = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\ISZE_Full_Project_Audit_20260825\ISZE_Full_Project_Audit_20260825.html")
html = html_path.read_text(encoding="utf-8")
if 'id="s36"' in html:
    raise SystemExit("already has part3")

toc_extra = """
  <li><a href="#s36">Part III — Full dataset catalog (spine)</a></li>
  <li><a href="#s37">Part III — Mail hunt chronology</a></li>
  <li><a href="#s38">Part III — INBOX triage playbook</a></li>
  <li><a href="#s39">Part III — Competitive benchmark (OEM aftersales)</a></li>
  <li><a href="#s40">Part III — Meeting / deck hygiene</a></li>
  <li><a href="#s41">Part III — People &amp; cadence model</a></li>
  <li><a href="#s42">Part III — Measurement plan for L4→L5</a></li>
  <li><a href="#s43">Part III — What to stop building</a></li>
  <li><a href="#s44">Part III — First 10 decisions this week</a></li>
  <li><a href="#s45">Part III — Glossary of programme terms</a></li>
"""
old = '  <li><a href="#s35">Part II — Decision log recommendations</a></li>\n</ol>'
new = '  <li><a href="#s35">Part II — Decision log recommendations</a></li>\n' + toc_extra + '</ol>'
if old not in html:
    # try after expand may have different ending
    old = '  <li><a href="#s35">Part II — Decision log recommendations</a></li>\n'
    if old not in html:
        raise SystemExit("toc s35 missing")
    html = html.replace(old, old + toc_extra)
else:
    html = html.replace(old, new)

part3 = r'''
<h2 class="sec page" id="s36"><span class="no">36</span> Full dataset catalog (spine)</h2>
<p>Compact catalog of load-bearing assets. Full folder walk: 2,527 files / ~2.2 GB under 01_data.</p>
<table>
  <thead><tr><th>Domain</th><th>Canonical asset</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>Billing</td><td>sales_fact.parquet (477,505)</td><td>Active · horizon stale</td></tr>
    <tr><td>Billing raw</td><td>12_raw/sales CY23–25 + sales_2026tillApril + Q1FY2027</td><td>Q1FY2027 ahead of fact</td></tr>
    <tr><td>UIO</td><td>06_uio/_CURRENT ISUZU_UIO_Overview_2026 (v19)</td><td>Active</td></tr>
    <tr><td>VIN</td><td>07_UIO/vin/VIN_register</td><td>Partial (JP)</td></tr>
    <tr><td>PMS</td><td>pms_capture_by_db_year · opportunity_matrix</td><td>Active</td></tr>
    <tr><td>GPS</td><td>gps_spu_by_distributor · Calculator v9</td><td>Active</td></tr>
    <tr><td>BVP</td><td>genuine_bvp_crossref · mix tables · catalog</td><td>Active</td></tr>
    <tr><td>Pricing</td><td>PR00/ZPR1 history + 2026 · Eucon · PartsPool</td><td>Active · vintage risk</td></tr>
    <tr><td>Sell-out</td><td>12_raw/dealer_sales (5 DBs)</td><td>Partial</td></tr>
    <tr><td>Warranty</td><td>CV/LCV 2025 · UMI to 2026-05</td><td>LCV Dec+ missing</td></tr>
    <tr><td>Tender</td><td>tender_data.json · v4 engine</td><td>Active</td></tr>
    <tr><td>Planning</td><td>VPACC July · KPI Master · BP FY27</td><td>Active</td></tr>
    <tr><td>Ops</td><td>action_ledger · ids_dealer_network</td><td>Active · 0 outcomes</td></tr>
    <tr><td>Mail facts</td><td>17_interactions (G0a)</td><td>Active local</td></tr>
    <tr><td>Staging</td><td>90_INBOX 1,677 files</td><td>Sorting owed</td></tr>
  </tbody>
</table>

<h2 class="sec page" id="s37"><span class="no">37</span> Mail hunt chronology</h2>
<table>
  <thead><tr><th>Date</th><th>Hunt</th><th>Result</th></tr></thead>
  <tbody>
    <tr><td>2026-08-09</td><td>Greece Petros sell-out</td><td>Filed CY2025 qties</td></tr>
    <tr><td>2026-08-12</td><td>G0a MAPI collect (own mbx)</td><td>9,001 interactions · 926 commitments</td></tr>
    <tr><td>2026-08-12</td><td>IUK Monthly Demand</td><td>2025 + 2026→Jul filed</td></tr>
    <tr><td>2026-08-13</td><td>UTI noreply2 PartSales</td><td>Aug–Nov 2025 + Jan–Jun 2026 filed; Feb–Jul 2025 still missing</td></tr>
    <tr><td>2026-08-13</td><td>UTI sap4* archive</td><td>0 attachments (uncached Online Archive)</td></tr>
    <tr><td>2026-08-13</td><td>Ireland Harris StD</td><td>2025 + 2026 YTD Jul filed</td></tr>
    <tr><td>2026-08-13</td><td>Dealer sales multi-subject scan</td><td>Logs under dashboards Data tree</td></tr>
    <tr><td>2026-08-19</td><td>P4 account health build</td><td>Draft thresholds · ops triage 16</td></tr>
    <tr><td>2026-08-25</td><td>Gina Z2SDAB42 margin</td><td>Jun/Jul pulled; not piped</td></tr>
    <tr><td>2026-08-25</td><td>This audit COM probe</td><td>Stores Sales/Parts/personal; subject hit table</td></tr>
  </tbody>
</table>
<p>Pattern: heroic hunts work; conveyor does not exist. Convert chronology into AUTOMATION_REGISTER entries.</p>

<h2 class="sec page" id="s38"><span class="no">38</span> INBOX triage playbook</h2>
<ol>
  <li><strong>IDS_2026 (970)</strong> → 08_Distributor / IDS packs; archive duplicates.</li>
  <li><strong>pms_intervals_mail_pull (134)</strong> → 03_PMS/service_schedules or pdf_text; keep one canonical set.</li>
  <li><strong>margin_analysis_mail_pull (53)</strong> → wire Gina to 01_Pricing/_raw; discard wrong-grain Rik copies from pipeline.</li>
  <li><strong>UTI / Ireland / dealer_sales mail folders</strong> → confirm 12_raw already has canonical; archive hunt residue.</li>
  <li><strong>suzuki / APL / tomoe</strong> → meetings or PMS programme folders.</li>
  <li><strong>Loose scripts (dg_*.py)</strong> → 91_build or delete.</li>
  <li><strong>Root loose PPTX/XLSX in INBOX</strong> → 09_meetings or 11_planning.</li>
</ol>
<div class="callout">Target: empty INBOX. Non-empty INBOX = explicit debt on the weekly open-loops brief.</div>

<h2 class="sec page" id="s39"><span class="no">39</span> Competitive benchmark (OEM aftersales)</h2>
<p>What “best in class” OEM aftersales analytics typically instrument — mapped to ISZE:</p>
<table>
  <thead><tr><th>Capability</th><th>Typical OEM bar</th><th>ISZE today</th></tr></thead>
  <tbody>
    <tr><td>Wholesale sell-in</td><td>Live ERP</td><td>Periodic SAP extract (strong enough)</td></tr>
    <tr><td>Dealer sell-out</td><td>Network monthly</td><td>5 DBs partial</td></tr>
    <tr><td>Parc-based demand</td><td>UIO × intervals</td><td>Strong (PMS)</td></tr>
    <tr><td>Capture / loyalty</td><td>Genuine share</td><td>Strong (PMS+BVP)</td></tr>
    <tr><td>Price waterfall</td><td>List/SPA/net</td><td>Net + lists only (SPA closed)</td></tr>
    <tr><td>Fill / OTIF / lost sales</td><td>Standard ops KPI</td><td>Mostly missing</td></tr>
    <tr><td>Campaign ROI</td><td>Tagged lifts</td><td>Calendar only</td></tr>
    <tr><td>Tender / fleet R&amp;M</td><td>Varies</td><td>Honest early engine</td></tr>
    <tr><td>Closed-loop actions</td><td>CRM + outcomes</td><td>Ledger built, empty outcomes</td></tr>
    <tr><td>Quote integrity</td><td>Often weak</td><td><strong>ISZE strength</strong></td></tr>
  </tbody>
</table>
<p>ISZE’s unfair advantage is integrity culture + capture maths. The deficit is dealer-channel economics and closed loop — exactly where this audit points.</p>

<h2 class="sec page" id="s40"><span class="no">40</span> Meeting / deck hygiene</h2>
<ul>
  <li>09_meetings holds European Conference packs, IDS country packs, operating dashboards, draft emails — valuable, but not the number authority.</li>
  <li>Every external slide must cite FACTS lane (IML vs PRISM) when ITUK capture appears.</li>
  <li>Draft email JSON packs for IDS countries exist — useful for outreach, not for metrics.</li>
  <li>Do not paste line-level billing into decks or GPT (🔒 rule).</li>
  <li>When a meeting pack disagrees with FACTS, fix the pack — never “average” the two.</li>
</ul>

<h2 class="sec page" id="s41"><span class="no">41</span> People &amp; cadence model</h2>
<table>
  <thead><tr><th>Cadence</th><th>Owner role</th><th>Artefact</th></tr></thead>
  <tbody>
    <tr><td>Daily (as needed)</td><td>You + agent</td><td>INBOX zero; hunt only when subject new</td></tr>
    <tr><td>Monday 30–45 min</td><td>VP Sales analytics</td><td>Ledger triage → decisions.csv</td></tr>
    <tr><td>Weekly</td><td>Scheduler</td><td>Tender · IAM refresh · open-loops · LiveStateAudit</td></tr>
    <tr><td>Month +5d</td><td>You / SAP export</td><td>Billing extract → sales_fact → green verify</td></tr>
    <tr><td>Month +7d</td><td>You / DBs</td><td>PartSales/StD intake for covered DBs</td></tr>
    <tr><td>Quarterly</td><td>You</td><td>One new sell-out DB; factor science review</td></tr>
    <tr><td>Before every DB review</td><td>You</td><td>FACTS + green gate + pack rebuild</td></tr>
  </tbody>
</table>

<h2 class="sec page" id="s42"><span class="no">42</span> Measurement plan for L4→L5</h2>
<table>
  <thead><tr><th>Metric</th><th>Definition</th><th>Target 90d</th><th>Target 12m</th></tr></thead>
  <tbody>
    <tr><td>Verify fails</td><td>count fail in _verification_report</td><td>0</td><td>0</td></tr>
    <tr><td>Billing lag</td><td>days from month-end to sales_fact max date</td><td>≤10</td><td>≤5</td></tr>
    <tr><td>INBOX files</td><td>count under 90_INBOX</td><td>&lt;50</td><td>0 steady-state</td></tr>
    <tr><td>Sell-out DBs</td><td>DBs with long CSV ≥1 full CY</td><td>≥6</td><td>≥12</td></tr>
    <tr><td>Ledger outcomes</td><td>ACTIONED with realised window closed</td><td>≥20</td><td>≥200</td></tr>
    <tr><td>P4 calibrated</td><td>signed thresholds</td><td>Yes</td><td>Yes + reviewed</td></tr>
    <tr><td>External quote incidents</td><td>wrong-lane / stale / invented</td><td>0</td><td>0</td></tr>
  </tbody>
</table>

<h2 class="sec page" id="s43"><span class="no">43</span> What to stop building</h2>
<ul>
  <li>New dashboard shells without a new data contract.</li>
  <li>Composite 0–100 “risk scores” without pre-registered backtests.</li>
  <li>ISZE→DB elasticity charts for shared.</li>
  <li>Re-asking SAP for gross/SPA/condition columns.</li>
  <li>Cloning Data Integrity / Early Warning into yet another HTML.</li>
  <li>Expanding revision_exception_queue UI before Monday triage exists.</li>
  <li>Quiet processing of shared Sales/Parts mailboxes before G0b.</li>
  <li>Treating tender GPS floor as TAM storytelling.</li>
</ul>

<h2 class="sec page" id="s44"><span class="no">44</span> First 10 decisions this week</h2>
<ol>
  <li>Remap or fix raw_cy2025 verify check.</li>
  <li>Schedule SAP extract pull for latest closed month.</li>
  <li>Block 45 minutes Monday for ledger triage (Book B + leakage + defection only).</li>
  <li>Assign INBOX sort owner for IDS_2026 (970 files).</li>
  <li>Draft UMI sell-out ask (mirror UTI PartSales language).</li>
  <li>Emit long CSVs for ITUK / UTI / Greece from existing raw.</li>
  <li>Quarantine prism UIO_v17.xlsx.</li>
  <li>Label shared competitor packs with Eucon 2023 vs PartsPool 2026-03 vintages.</li>
  <li>Write DECISIONS entry: leakage € stays internal until list-to-pocket signed.</li>
  <li>Add “mailbox intake” stub to AUTOMATION_REGISTER (even if script lands next week).</li>
</ol>

<h2 class="sec page" id="s45"><span class="no">45</span> Glossary of programme terms</h2>
<table>
  <thead><tr><th>Term</th><th>Meaning</th></tr></thead>
  <tbody>
    <tr><td>ISZE</td><td>Isuzu Europe aftersales analytics workspace / programme</td></tr>
    <tr><td>DB</td><td>Distributor (ISZE customer)</td></tr>
    <tr><td>DLR</td><td>Dealer</td></tr>
    <tr><td>PMS</td><td>Parts Marketing Strategy — capture of expected service demand</td></tr>
    <tr><td>GPS</td><td>Genuine Parts Sales — wallet / spend-per-unit framing</td></tr>
    <tr><td>SPU</td><td>Spend per UIO unit</td></tr>
    <tr><td>BVP</td><td>Best Value Parts (alternative line) — mix, not capture</td></tr>
    <tr><td>UIO</td><td>Units in operation (parc)</td></tr>
    <tr><td>PR00 / ZPR1</td><td>Price list families</td></tr>
    <tr><td>AIM</td><td>Former pricing-risk ambition — score killed after null backtest</td></tr>
    <tr><td>G0a / G0b</td><td>Mail governance gates (local own mbx vs shared+LLM)</td></tr>
    <tr><td>P4</td><td>Account-health / who-went-quiet signals</td></tr>
    <tr><td>P5</td><td>Forecast track</td></tr>
    <tr><td>P8</td><td>Action Ledger pipeline</td></tr>
    <tr><td>shared / internal</td><td>External-shareable vs internal-only surfaces</td></tr>
    <tr><td>FACTS</td><td>Single narrative authority for headline numbers</td></tr>
  </tbody>
</table>

<div class="callout" style="margin-top:6mm;">
  End of Part III. Combined with Parts I–II this audit is the operating map from L3.7 → L4 → L5.
  Re-read the cover verdict before starting any new HTML project.
</div>
'''

html = html.replace("</div><!-- wrap -->", part3 + "\n</div><!-- wrap -->")
html_path.write_text(html, encoding="utf-8")
print("bytes", html_path.stat().st_size)
print("https", len(re.findall(r'(?:src|href)=["\']https?://', html)))
