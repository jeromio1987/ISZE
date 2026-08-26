# -*- coding: utf-8 -*-
"""Expand audit HTML with Part II deep-dive chapters."""
from pathlib import Path
import re

html_path = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\ISZE_Full_Project_Audit_20260825\ISZE_Full_Project_Audit_20260825.html")
html = html_path.read_text(encoding="utf-8")

toc_extra = """
  <li><a href="#s21">Part II — Billing &amp; sales_fact deep dive</a></li>
  <li><a href="#s22">Part II — Pricing, Eucon &amp; pocket price</a></li>
  <li><a href="#s23">Part II — PMS / GPS / BVP deep dive</a></li>
  <li><a href="#s24">Part II — Warranty &amp; parc / VIN</a></li>
  <li><a href="#s25">Part II — Per-distributor gap cards</a></li>
  <li><a href="#s26">Part II — Tender &amp; fleet R&amp;M</a></li>
  <li><a href="#s27">Part II — Action Ledger operating design</a></li>
  <li><a href="#s28">Part II — Mail G0a/G0b programme detail</a></li>
  <li><a href="#s29">Part II — Automation &amp; monthly refresh</a></li>
  <li><a href="#s30">Part II — PRISM surface-by-surface</a></li>
  <li><a href="#s31">Part II — HTML / Master Hub debt</a></li>
  <li><a href="#s32">Part II — Week-by-week 90-day calendar</a></li>
  <li><a href="#s33">Part II — Analysis recipes that become possible</a></li>
  <li><a href="#s34">Part II — Risks if we do nothing</a></li>
  <li><a href="#s35">Part II — Decision log recommendations</a></li>
"""

old_toc_end = '  <li><a href="#s20">Appendix F — one-page operator checklist</a></li>\n</ol>'
new_toc_end = '  <li><a href="#s20">Appendix F — one-page operator checklist</a></li>\n' + toc_extra + '</ol>'
if old_toc_end not in html:
    raise SystemExit("TOC marker missing")
html = html.replace(old_toc_end, new_toc_end)

part2 = r'''
<h2 class="sec page" id="s21"><span class="no">21</span> Billing &amp; sales_fact deep dive</h2>
<p>The entire analytical OS hangs on one parquet. Treat it as production infrastructure, not a file.</p>
<table>
  <thead><tr><th>Property</th><th>Value</th><th>Implication</th></tr></thead>
  <tbody>
    <tr><td>Rows</td><td>477,505</td><td>Stable vs verify expectation (Δ 0%)</td></tr>
    <tr><td>Date span</td><td>2023-01-03 → 2026-03-31</td><td>Five months of 2026 calendar missing from KPIs</td></tr>
    <tr><td>fig_key coverage</td><td>98.6%</td><td>Above 90% gate — keep</td></tr>
    <tr><td>SaTy coverage</td><td>100%</td><td>Above 95% gate — keep</td></tr>
    <tr><td>UNMAPPED distributors</td><td>4 rows (0.00%)</td><td>Map is healthy</td></tr>
    <tr><td>Raw total €</td><td>108,816,956</td><td>Includes internal/excluded/credits</td></tr>
    <tr><td>GPS-facing €</td><td>105,002,413</td><td>After exclusions + CR/RE</td></tr>
    <tr><td>Parts base €</td><td>103,573,715</td><td>The attribution target</td></tr>
  </tbody>
</table>
<h3>Raw ahead of fact</h3>
<ul>
  <li>CY2023-2024, CY2024-2025, sales_2026tillApril — wired into historical builds.</li>
  <li>Q1FY2027.XLSX (2026-07-05, 6.2 MB) — on disk, ahead of sales_fact. Not yet in the parquet horizon.</li>
  <li>Intermediate cy202*_*.csv (~75 MB, June) look orphaned relative to Aug rebuilds.</li>
</ul>
<div class="callout red">
  <strong>Analysis that is currently lying by omission:</strong> any CY2026 YTD, FY2026 close, GPS SPU 2026, capture trajectory 2026,
  ledger realised-€ windows, and “who went quiet since April” stories. Fixing billing freshness is the highest-ROI engineering hour in the programme.
</div>
<h3>Config fail explained</h3>
<p>Verify expects a flag/file named like CY2025.XLSX. Disk has the more-complete CY2024-2025.XLSX.
This is contract drift, not a missing year of sales. Still: the gate is red, so external quoting must wait or the check must be updated deliberately.</p>

<h2 class="sec page" id="s22"><span class="no">22</span> Pricing, Eucon &amp; pocket price</h2>
<p>ISZE already rejected the fantasy of gross/SPA columns. The surviving path is dated lists + net billing.</p>
<ul>
  <li>PR00 + ZPR1 history for 2023/2024/2025 landed 2026-08-11 under 01_Pricing/history/ plus 2026 current lists.</li>
  <li>Catalogue PR00 coverage raised to <strong>98.2%</strong> after Spec C4 SAP pull (residual admin non-PN + parked UMI Shell + 24 PN / €67k ZPR1-path hardware).</li>
  <li>Supersession billed-on-old: <strong>925 PN / €2.48M</strong> on IE40 map — not EPC-validated. Do not treat as confirmed leakage.</li>
  <li>Eucon 2023 OEM+IAM survey raw sits beside PartsPool scrape dated <strong>2026-03-29</strong>. Mode A packs must show vintage labels or they mislead.</li>
  <li>Gina Z2SDAB42 margin masterdata (Jun/Jul 2026, ~24–29 MB) was pulled into INBOX — not yet a pipeline citizen.</li>
  <li>Rik Cornille monthly margin (~0.2 MB) is PC aggregate — wrong grain for PN work.</li>
</ul>
<div class="callout amber">
  Year-matched list-to-pocket is <strong>possible but not validated</strong>. Until joins are checked, “leakage €” stays internal.
  Shipping an unvalidated leakage number into a DB meeting would be an integrity failure, not a win.
</div>
<h3>Analyses that become best-in-class once validated</h3>
<ol>
  <li>List→pocket realisation by DB × year (page 21 already scaffolds this).</li>
  <li>ZPR1 vs PR00 payer gaps as revision candidates.</li>
  <li>PN enquiry queues tied to Book B revision exceptions (already 20,572 exception rows — triage, don’t expand blindly).</li>
  <li>Competitor gap packs with honest as-of dates (Eucon 2023 ≠ PartsPool Mar 2026).</li>
</ol>

<h2 class="sec page" id="s23"><span class="no">23</span> PMS / GPS / BVP deep dive</h2>
<h3>PMS — two ITUK lanes (never conflate)</h3>
<table>
  <thead><tr><th>Lane</th><th>UIO</th><th>Service freq</th><th>Oil-filter story</th><th>Use for</th></tr></thead>
  <tbody>
    <tr><td>IML v7 (Model B)</td><td>22,389 DVLA</td><td>1.25×/yr filters</td><td>35.1% cover · €2.04M 5-cat gap</td><td>External ITUK decks</td></tr>
    <tr><td>PRISM network</td><td>23,068 bucketed</td><td>bucketed constants</td><td>2025 total capture uncapped 116%</td><td>Network league / PRISM</td></tr>
  </tbody>
</table>
<p>Open science: air:oil provisional 0.5 factor (Flag C); ITUK brake 0.4 vs 0.8 pending data; LCV SCR cutoffs missing for generation weighting.
Closed science (keep closed): fitted oil-filter λ; AIM pricing-risk score.</p>
<h3>GPS</h3>
<ul>
  <li>Canonical calculator v9; SPU traffic lights green ≥ €150 / amber €50–150 / red &lt; €50.</li>
  <li>Two documented billing bases (Kosha vs full GPS-clean) — do not cross-compare without labelling.</li>
  <li>Kickback + stretch pilots exist; treat as planning artefacts, not FACTS.</li>
</ul>
<h3>BVP</h3>
<ul>
  <li>Crossref ~547 pairs; PMS-flagged ~496 in P0; addressable basket 2,272 rows across 22 distributors.</li>
  <li>BVP has <strong>no</strong> capture rate — mix only. Quoting “BVP capture %” is a category error.</li>
</ul>

<h2 class="sec page" id="s24"><span class="no">24</span> Warranty &amp; parc / VIN</h2>
<ul>
  <li>CV + LCV 2025 warranty workbooks wired; <strong>LCV ends Nov 2025</strong> — Dec+ claims missing (OS integrity LCV-DEC).</li>
  <li>UMI warranty extract covers 2023-01 → 2026-05 — richer than LCV book; keep entity separate from UTI.</li>
  <li>UIO v19 canonical; stale v17 under prism triggers verify warn — delete or quarantine.</li>
  <li>JP VIN register supports rolling-60m PMS cohort (page 22) — ex ITUK/UTI until packs land; AT/MT unknown until ISZJ map.</li>
  <li>Do not merge IML 22,389 with PRISM 23,068 “to be tidy” — they answer different questions.</li>
</ul>

<h2 class="sec page" id="s25"><span class="no">25</span> Per-distributor gap cards</h2>
<p>Not every DB needs the same ask. Prioritise by billing weight × missing channel truth.</p>
<table>
  <thead><tr><th>DB</th><th>Spine</th><th>Sell-out</th><th>Next ask</th></tr></thead>
  <tbody>
    <tr><td>ITUK</td><td>Strong (IML+PRISM)</td><td>CY2025 StD; no CY2026</td><td>CY2026 Sales to Dealers YTD</td></tr>
    <tr><td>IUK</td><td>GPS/PMS live</td><td>Demand 2025+2026YTD</td><td>Keep monthly; never blend with ITUK</td></tr>
    <tr><td>Ireland</td><td>Live</td><td>Harris StD 2025+YTD</td><td>Cadence + BO if useful</td></tr>
    <tr><td>UTI 1799</td><td>Live</td><td>PartSales with Feb–Jul 2025 hole</td><td>Archive months + Jul 2026 job</td></tr>
    <tr><td>UMI 1797</td><td>Live (≠ UTI)</td><td><strong>None</strong></td><td>PartSales/StD family — top unlock</td></tr>
    <tr><td>Greece</td><td>Live</td><td>Petros 2025 qty</td><td>2026 + long CSV emit</td></tr>
    <tr><td>Germany / Belgium / Portugal</td><td>Billing yes</td><td>None</td><td>PN×month qty ask</td></tr>
    <tr><td>Nordics</td><td>Billing yes</td><td>None</td><td>Sell-out + tender keys</td></tr>
    <tr><td>Armenia / Kazakhstan / Palestine</td><td>Thin mail</td><td>None</td><td>Contact domains still thin in G0a history</td></tr>
  </tbody>
</table>
<div class="callout">
  <strong>Rule:</strong> never blend UMI 1797 with UTI 1799. payer_code 1797 appears on both sides of history — join on sold_to_sap via distributor_dimension.
</div>

<h2 class="sec page" id="s26"><span class="no">26</span> Tender &amp; fleet R&amp;M</h2>
<p>Live (2026-08-25): <strong>211</strong> notices · <strong>186</strong> opportunities · GPS-sized <strong>3</strong> · addressable GPS floor <strong>€1,488.22</strong>.
Product-fit gate removed passenger/SEND noise; CPV 60… = 0. Nordics AWAITING_KEY; some RSS/DTVP retired honestly.</p>
<ul>
  <li>God-tier engine checks mostly PASS; paper P3 PARTIAL — historical headlines still floating in notes.</li>
  <li>Never present €1,488 as “market potential” — it is addressable-if-won on three truck-sized rows.</li>
  <li>National portal map incomplete (ES/IT/DE and others) — coverage dark map exists; wire next, don’t invent GPS for FR/PL/ES without SPU.</li>
  <li>IDS dealer linkage: 113/186 assigned; DE unmapped — attach pilot is the L5 move, not another scrape vanity metric.</li>
</ul>

<h2 class="sec page" id="s27"><span class="no">27</span> Action Ledger — operating design</h2>
<p>Built 2026-08-25: 23,236 open · 0 rejects · 0 outcomes · billing horizon 2026-03-31.
Data-sufficiency verdict already says: sufficient to build; insufficient for measurable outcomes past horizon.</p>
<h3>How not to drown</h3>
<ol>
  <li>Default view = Book B top + leakage Monday + defection + account_health flagged (≈821 rows of signal, not 20k exceptions).</li>
  <li>revision_exception_queue (20,572) is a warehouse — sample by €, don’t weekly-browse.</li>
  <li>Edit only action_ledger_decisions.csv; never invent realised_eur.</li>
  <li>After billing refresh past horizon, re-run outcome measurement — that is when L4 becomes real.</li>
</ol>
<table>
  <thead><tr><th>Top open themes (by € examples)</th><th>Example stake</th><th>Source family</th></tr></thead>
  <tbody>
    <tr><td>Book B PN 8983767550 across IUK/Greece/Ireland</td><td>~€640k L12M each line</td><td>revision_book_b_top_review</td></tr>
    <tr><td>IUK leakage annualised</td><td>€447k–€573k</td><td>leakage_monday_actions</td></tr>
    <tr><td>Catalogue gap 550047337</td><td>€434k CY2025</td><td>no_pr00_gap</td></tr>
    <tr><td>ITUK fuel_filter defection</td><td>€233k trailing 12M</td><td>defection_alerts</td></tr>
  </tbody>
</table>

<h2 class="sec page" id="s28"><span class="no">28</span> Mail G0a / G0b programme detail</h2>
<p>G0a authorized 2026-08-12: own mailbox only; derived fields only; no bodies/subjects stored; 24-month retention; DSAR runbook exists.</p>
<ul>
  <li>Collector saw 31,532 · kept 9,490 · stored 9,001 rows · 17 DBs · commitments 926 · stakeholders 203.</li>
  <li>Local cache gap: months before ~2025-07 show seen 0 on collect log — Online Archive sync required before historical re-collect helps.</li>
  <li>Account health parquet exists with draft thresholds — not a KPI until calibrated.</li>
  <li>G0b would unlock shared Sales/Parts + LLM enrichment + drafts — requires works-council / LIA / approved LLM route (B1b).</li>
  <li>Kill rule already written: if no approved LLM route, P2b/P3/P6 die; programme still runs P1+P2a+P4+P5.</li>
</ul>
<div class="callout amber">
  COM has a shelf life: New Outlook is installed and does not support COM. Isolate collector behind one interface; keep derived store as the durable asset.
</div>

<h2 class="sec page" id="s29"><span class="no">29</span> Automation &amp; monthly refresh</h2>
<table>
  <thead><tr><th>Job</th><th>Status</th><th>Gap vs best</th></tr></thead>
  <tbody>
    <tr><td>ISZE Tender Monitor</td><td>Live weekly</td><td>Align release notes to live counts</td></tr>
    <tr><td>ISZE_PMS_IAM_Refresh</td><td>Live (had interrupt history)</td><td>Visible as-of on packs</td></tr>
    <tr><td>LiveStateAudit</td><td>Live</td><td>Act on drift briefs</td></tr>
    <tr><td>Dashboard freshness / UIO stale / memory review</td><td>Active skills</td><td>Keep</td></tr>
    <tr><td>Mailbox attachment intake</td><td><strong>Missing</strong></td><td>Add CHEAP monthly skill</td></tr>
    <tr><td>sales_fact rebuild on new SAP drop</td><td>Manual</td><td>Runbook step with verify gate</td></tr>
    <tr><td>Discount scanner</td><td>Not registered (personal)</td><td>Out of ISZE critical path</td></tr>
  </tbody>
</table>
<p>Monthly refresh runbook requires green verify before numbers move. Today that bar is failed — treat as a stop-ship for external decks until cleared.</p>

<h2 class="sec page" id="s30"><span class="no">30</span> PRISM surface-by-surface</h2>
<table>
  <thead><tr><th>Surface</th><th>Job</th><th>Maturity</th><th>Next</th></tr></thead>
  <tbody>
    <tr><td>Home / Early Warning</td><td>Who needs attention</td><td>Prod</td><td>Keep; feed ledger Monday</td></tr>
    <tr><td>GPS</td><td>Wallet SPU</td><td>Prod</td><td>Fresher billing</td></tr>
    <tr><td>PMS</td><td>Capture</td><td>Prod</td><td>Lock open factors</td></tr>
    <tr><td>BVP / Mix</td><td>Substitution</td><td>Prod</td><td>EPC supersession later</td></tr>
    <tr><td>Network Intelligence</td><td>Merged league</td><td>Prod</td><td>Avoid clone pages</td></tr>
    <tr><td>Decision Models</td><td>Waterfall / runway</td><td>Prod</td><td>Label bases</td></tr>
    <tr><td>Warranty / Realization / Parc / Sell-out / VPACC</td><td>20–24</td><td>Pilot→Prod</td><td>Sell-out coverage; LCV Dec+</td></tr>
    <tr><td>Forecast</td><td>P5</td><td>Pilot</td><td>G1 + overrides</td></tr>
    <tr><td>Internal shelf</td><td>Leakage/elasticity/scrape</td><td>Gated</td><td>Stay internal until validated</td></tr>
    <tr><td>Data Integrity</td><td>Flags</td><td>Prod</td><td>Keep as conscience</td></tr>
  </tbody>
</table>

<h2 class="sec page" id="s31"><span class="no">31</span> HTML / Master Hub debt</h2>
<ul>
  <li>~273 HTML files; many IDS fiches / inbox mirrors — not products.</li>
  <li>Intentional twins in 02_dashboards/bi/ must rebuild with PRISM 20–23.</li>
  <li>Master Dashboard stale links to old Isuzu/Projects paths — audit and regenerate manifest.</li>
  <li>Supabase V4 live KPIs still blocked on schema/creds — do not half-ship.</li>
  <li>Rule: edit 02_dashboards/ only; never deploy tree as source of truth.</li>
</ul>

<h2 class="sec page" id="s32"><span class="no">32</span> Week-by-week 90-day calendar</h2>
<table>
  <thead><tr><th>Week</th><th>Focus</th><th>Exit check</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>Verify config fix · sales_fact rebuild plan · Monday ledger ritual start</td><td>0 fail OR owned waiver; ≥5 decisions rows</td></tr>
    <tr><td>2</td><td>Ingest latest SAP · rebuild derived · refresh metrics_snapshot</td><td>Horizon ≥ latest closed month</td></tr>
    <tr><td>3–4</td><td>INBOX sort wave 1 (Gina, UTI residue, Ireland, PMS intervals)</td><td>INBOX &lt; 400 files</td></tr>
    <tr><td>5–6</td><td>UMI sell-out ask + hunt · emit long CSVs ITUK/UTI/Greece</td><td>UMI filed or chase dated; 3 long CSVs exist</td></tr>
    <tr><td>7–8</td><td>P4 calibration workshop · thin widget · IAM vintage labels</td><td>Thresholds signed; labels shipped</td></tr>
    <tr><td>9–10</td><td>List-to-pocket validation OR explicit “internal only” decision</td><td>Written decision in DECISIONS.md</td></tr>
    <tr><td>11</td><td>Tender notes aligned · Nordics keys if available · portal wire ES/IT/DE</td><td>P3 PARTIAL cleared</td></tr>
    <tr><td>12–13</td><td>IML air:oil / brake evidence · second sell-out DB · INBOX &lt; 50</td><td>90-day success criteria met</td></tr>
  </tbody>
</table>

<h2 class="sec page" id="s33"><span class="no">33</span> Analysis recipes that become possible</h2>
<p>Once the unlocks land, these are the “best sales analyses on everything” — concrete recipes, not slogans.</p>
<ol>
  <li><strong>Network share of wallet:</strong> sell-out € / (UIO × target SPU) by DB × month.</li>
  <li><strong>Capture × leakage joint:</strong> PMS under-capture and dealer leakage on the same PN family.</li>
  <li><strong>Price move simulator (DB→DLR):</strong> elasticity only after ≥N DBs × 24 months sell-out.</li>
  <li><strong>Lost sales €</strong> from fill failures × list/net proxy.</li>
  <li><strong>Campaign lift:</strong> tagged promo windows vs attach baseline on wear categories.</li>
  <li><strong>Quiet account radar:</strong> P4 RED ∩ declining capture_trajectory ∩ open commitments missed.</li>
  <li><strong>Revision Book B sprint:</strong> top € exceptions with realisation gap and competitor vintage.</li>
  <li><strong>Tender attach:</strong> won notice → IDS dealer → expected PMS basket.</li>
  <li><strong>Warranty-to-parts:</strong> claim PN → genuine/BVP availability → capture miss.</li>
  <li><strong>Forecast vs actual QBR:</strong> P5 with owned overrides, WAPE tracked, no silent re-fit.</li>
</ol>

<h2 class="sec page" id="s34"><span class="no">34</span> Risks if we do nothing</h2>
<ul>
  <li><strong>Credibility risk:</strong> quoting 2026 numbers from a Mar-31 fact table in autumn meetings.</li>
  <li><strong>Opportunity rot:</strong> 23k ledger rows age into noise; staff stop trusting the OS.</li>
  <li><strong>Channel blindness:</strong> competitors with dealer sell-out will out-negotiate on price and stock.</li>
  <li><strong>Mail cliff:</strong> New Outlook kills COM; without derived store discipline, G0a dies with the collector.</li>
  <li><strong>Integrity theatre:</strong> beautiful dashboards on stale/unsorted INBOX teach the organisation the wrong lesson.</li>
  <li><strong>Science relapse:</strong> pressure to “just ship a score” after AIM null — resist; the kill was correct.</li>
</ul>

<h2 class="sec page" id="s35"><span class="no">35</span> Decision log recommendations</h2>
<p>Propose these as explicit DECISIONS.md entries (do not silently assume):</p>
<ol>
  <li>Verify check raw_cy2025 remapped to CY2024-2025.XLSX (or dual-accept) — with owner + date.</li>
  <li>Sales_fact refresh cadence = within 5 working days of month close.</li>
  <li>Monday ledger ritual is mandatory for VP Sales analytics time (30–45 min).</li>
  <li>UMI sell-out is the next coverage priority over any new HTML.</li>
  <li>Leakage € remains Mode B until list-to-pocket signed.</li>
  <li>No new AIM-like composite score in 2026 without a pre-registered backtest plan.</li>
  <li>Mailbox intake skill added to AUTOMATION_REGISTER (CHEAP tier).</li>
  <li>G0b remains blocked until works-council step — no “quiet” shared-mailbox processing.</li>
</ol>
<div class="callout green">
  <strong>Final reinforcement.</strong> The path to “best project that exists” is operational excellence on truth:
  current billing, network sell-out, empty INBOX, green gate, ledger outcomes.
  Everything else is either already strong or correctly closed.
</div>
'''

marker = "</div><!-- wrap -->"
if marker not in html:
    raise SystemExit("wrap marker missing")
if 'id="s21"' in html:
    print("already expanded")
else:
    html = html.replace(marker, part2 + "\n" + marker)
    html_path.write_text(html, encoding="utf-8")
    print("wrote", html_path.stat().st_size)

print("https src", len(re.findall(r'(?:src|href)=["\']https?://', html)))
