# PROMPT — one-distributor operating dashboard (ISZE)

Copy everything below the line into the powerful model. Fill `TARGET_DB` first.

---

You are building a **single-distributor operating dashboard** for Jerome (ISZE parts). This is not a network cockpit, not a PowerPoint clone, and not a table dump. It is one HTML file a colleague can open offline and use in a DB meeting.

Jerome already has GPS/PMS slide packs from the last two weeks, IDS dealer compares, SaTy/fill-rate work, Outlook scans, and sales-review minutes. Your job is to **assemble those into one chart-first HTML for ONE distributor**, with honest gaps called out — never invented.

After you finish, your pack comes back to Cursor (local workspace agent) for visual hardening, Chart.js inlining, and `OPEN_*.cmd`. So: **research + numbers + a real first HTML**, not a slide outline.

---

## 0. Fill this before you start

```
TARGET_DB        = ________          # PRISM distributor_code, e.g. UMI, UTI, IBX/BELGIUM, HUNGARY, IRELAND, IUK, ITUK, PORTUGAL, GREECE, GERMANY
SOLD_TO          = ________          # SAP sold-to from distributor_dimension.csv
DISPLAY_NAME     = ________          # customer-facing name
AUDIENCE         = internal          # this build is ISZE-internal unless Jerome says otherwise
AS_OF            = 2026-08-14
```

**Recommended first run:** `UMI` (Universal Motors Israel Ltd, sold_to **1797**, LCV). Jerome’s live example: **all 29 Israel LCV dealers scored 0/18 on IDS Section E (Vehicle Sales)** — country average 0%, network average ~73%. That is a real finding, not a rumour. Verify it in `ISZE\02_dashboards\ids\IDS_2026_dealer_compare_Israel_LCV.html` before quoting.

If Jerome names a different DB, swap the code. Never blend **UTI (1799, CV)** with **UMI (1797, LCV)** — same payer 1797, split is at sold_to. The UMI Aug 2026 deck failed by blending UTI. Do not repeat that.

---

## 1. What “done” looks like

One self-contained HTML:

`C:\Users\jerom\Desktop\claude\ISZE\09_meetings\<TARGET_DB>_Operating_Dashboard_2026\<TARGET_DB>_Operating_Dashboard.html`

Plus a sibling:

`DATA_INTEGRITY.md` — every missing, conflicting, or unsigned number, written as a ping to Jerome (short, numbered, actionable).

Plus:

`OPEN_<TARGET_DB>_Operating_Dashboard.cmd` that does `start "" "%~dp0<file>.html"`

**Chart-first.** If a section is only a table, you failed that section. One detail table per section is allowed *under* the chart.

Visual bar to beat (open these; do not copy the composable desk):

| File | Why it is the bar |
|------|-------------------|
| `ISZE\02_dashboards\pricing\ISZE_Pricing_Engine_Readiness_Dashboard.html` | Hero KPIs, sticky tabs, **inline SVG**, navy/terracotta/paper |
| `ISZE\02_dashboards\fleet\ISZE_FY2026_YearEnd_Review.html` | Plotly local, meeting pack |
| `ISZE\02_dashboards\fleet\ISZE_GPS_Dashboard.html` | Heatmap / traffic lights — **different extract; do not copy its GPS% as signed** |
| `ISZE\09_meetings\HUNGARY_Sales_Review_2026\MODE_B_DEEP_DIVE.md` | Narrative quality for GPS/PMS/warranty (Hungary only — do not paste Hungary numbers onto TARGET_DB) |
| `ISZE\09_meetings\IBX_Sales_Review_2026\IBX_SaTy_Fill_Rate_Dashboard.html` | SaTy + fill-rate *shape* — **it loads Chart.js from a CDN. Do not copy that. Charts will be blank offline.** |
| `ISZE\02_dashboards\ids\IDS_2026_dealer_compare_*.html` | Dealer IDS heatmaps |

**Do not use** `ISZE\02_dashboards\_composable\dist\isze_cockpit.internal.html` as the visual model. It is a picker/spine, not a meeting screen.

---

## 2. Hard bans (breaking any of these = broken delivery)

1. **No CDN.** No `cdn.jsdelivr`, no Google Fonts, no Plotly CDN. Inline Chart.js from `ISZE\02_dashboards\_ui\chart.umd.min.js` (strip `sourceMappingURL`) **or** use inline SVG. Verify: zero `<script src="https://` and zero `<link href="https://` except clickable booking/docs links Jerome actually needs.
2. **No invented numbers.** No GPS%, occupancy, “lost sales €”, capture %, or order-mix % that you cannot point to a derived file + filter. Missing → empty state + ping in `DATA_INTEGRITY.md`.
3. **Do not load** `ISZE\01_data\raw\sales\*.XLSX` into chat. Use derived CSV/parquet/JSON only.
4. **No filenames in the visible body.** Sources live in one grey footer. Jerome hates pipeline names on screen.
5. **Do not mix grains unlabelled.** Calendar year ≠ fiscal year (ISZE FY = Apr–Mar). GPS spend is FY in `gps_pure_sales_*`. PMS capture is complete-CY. Wallet waterfall is CY. If a toggle switches grain, the number must come from a real file for that grain — **never convert FY↔CY by 9/12**.
6. **Do not compute GPS%** unless UIO for that DB/year is **signed**. Canonical UIO is V19 workbook for history; V20/forecast is not approved. Unsigned UIO → show **euros only**, label “no GPS%”.
7. **BVP is not leakage.** Genuine + Best Value are both inside the authorised channel. Aftermarket walk-out is a different number. Never add them.
8. **BVP mix ≠ PMS capture ≠ GPS wallet.** Three siblings. Never mash into one “lost sales” euro.
9. **Turkey (AIOS) and MIDI Europe are not ISZE distributors.** Drop them.
10. **ITUK PMS has two lanes.** IML v7 (external, 22,389 UIO, 1.25×/yr) vs PRISM network league. Never quote one as the other. Read `ISZE\00_docs\ITUK_PRISM_LANE_BRIDGE.md` if TARGET_DB is ITUK.
11. **Warranty rides commercial orders** in ERP (no warranty document type). Commercial/ex-warranty views must use `warranty_raw_grain.csv` PN exclusion + the existing heuristic in `ISZE\04_tools\db_sales_review\common.py`. Label residual warranty as a limitation.
12. **White text on pale backgrounds is forbidden** (KAMLIJN bug). Navy headers → paper/white text. Paper rows → ink `#222`.
13. **Every derived KPI** gets a CSS hover tooltip (`data-tip`): formula, snapshot date, what is **not** included. Navy panel, paper text, terracotta accent.
14. **House colours:** navy `#15233c` / `#1a2b4a`, terracotta `#c0552d`, paper `#f7f4ee`, Georgia headings, Segoe UI body. Green `#1d9e75` = good, amber `#eda100` = watch, red `#b23b3b` = bad. Colour means something.
15. **Charts:** no overlapping labels, bar thickness ≥18px, ≤6 axis ticks, round memorable ticks. If Chart.js still overlaps after two tries → inline SVG.
16. **Do not write to Downloads or `.cursor`.** Only under `C:\Users\jerom\Desktop\claude\`.
17. **Do not edit `07_deploy/`.**
18. **Customer-facing Mode A** never shows internal colleague names, old-vs-corrected number tables, or file paths. This dashboard is internal, but still: no “Claude guessed”.
19. **Power BI / accounting wins** when Jerome has supplied a cut (`db_profiles.yaml` `pbi:`). Do not keep a derived billing number “for comparison” on the hero.
20. **Crossref is incomplete.** `genuine_bvp_crossref.csv` missing a BVP does **not** prove none exists. Label “no BVP in crossref” vs “no BVP in catalog”. SPA only when ISZE would actually SPA that PN.

---

## 3. Dashboard sections (in this order)

Sticky tab bar. Each tab is a room. Hero strip stays visible.

### A. Cover / hero

- Distributor name, scope (CV / LCV / MIXED), region, sold-to.
- Four hero numbers **with grain labelled on the chip**:
  1. GPS-eligible parts € (FY, include-warranty default) from `gps_pure_sales_2026-08-13_v2.csv`
  2. Same € **ex-warranty** (toggle, not a second competing headline)
  3. PMS capture (CY, only if this DB is in PMS — 18 of 22 network DBs; CIS + Palestine have none)
  4. Wallet ceiling vs captured vs addressable gap (CY, `wallet_waterfall.csv`) — **ceiling, not a forecast**
- Toggles: **FY / CY** (only where both exist), **warranty in / out**.
- One sentence: what this dashboard is for (operating the account this quarter).

### B. GPS + PMS (the commercial spine)

Clone the *thinking* of the recent DB packs (Hungary Mode B, Portugal/IUK sales-review blueprint), not their numbers.

Must show:

- Spend over years (FY bars). FY2023 partial; FY2026 other-excl €0 where that flag exists.
- Wallet identity CY: theoretical wallet → captured (genuine + BVP) → addressable uncaptured.
- PMS categories that have a real interval (oil/fuel confirmed; air provisional; urea/blower caveats). **Do not chart “PMS capture over time” from a file whose UIO is frozen across years** — read `DB_SALES_REVIEW_BLUEPRINT.md` trap.
- Genuine vs BVP **inside captured demand**. Ask: is genuine declining because BVP is growing (value-tier switch) or because the euro left the channel?
- Include/exclude warranty on the GPS euro. Hungary lesson: FY GPS% can look fine while ex-warranty GPS is much weaker — **only if UIO is signed**. If UIO unsigned, show the two euro series, no %.

Recent packs to mine (do not copy slides into HTML):

- `ISZE\09_meetings\HUNGARY_Sales_Review_2026\`
- `ISZE\09_meetings\UMI_Sales_Review_2026\` (read the retro: UTI blend failure)
- `ISZE\09_meetings\IBX_Sales_Review_2026\`
- `ISZE\09_meetings\PORTUGAL_Sales_Review_2026\`
- `ISZE\09_meetings\IUK_Sales_Review_2026\`
- `ISZE\09_meetings\IRELAND_Sales_Review_2026\`
- `ISZE\09_meetings\ISD_Sales_Review_2026\`
- `ISZE\09_meetings\PETROS_Sales_Review_2026\`
- `ISZE\04_tools\ppt_template_v2\DB_SALES_REVIEW_BLUEPRINT.md`
- `ISZE\04_tools\db_sales_review\db_profiles.yaml` + `preflight.py --db <KEY>`

### C. Order pattern (SaTy) — 80/20 guideline

Guideline Jerome wants on screen: **~80% stock orders (SOR) / ~20% rush-class (VOR / RUSH / SVOR)**.

If rush-class share of **coded €** is materially above ~20% in the latest complete months, show a terracotta remark:

> We want the majority of demand on stock orders (~80/20). High urgency share usually means the dealer network is running on ISZE as a same-day warehouse. That is expensive for both sides and it hides true replenishment demand.

Must also try:

- **Weekly cadence:** do they order on a stable weekday / week-of-month? Chart order (or billing) dates by weekday and by ISO week. If the grain is monthly only, say so — do not fake weekly.
- **Fill rate** if a KPI Master / Individual Fill Rate series exists for this DB. IBX had a digitized series; others may be N/D from Apr 2025 in KPI Master — ping Jerome.
- SaTy coverage is uneven (IUK ~35% coded in Q1 FY27 export). Always show **% of € that has a SaTy code**. If coverage <70%, the 80/20 remark is **amber**, not a verdict.

Sources:

- `ISZE\01_data\00_derived\q1fy2027_export_with_saty.csv`
- `ISZE\01_data\00_derived\sales_fact.parquet` (SaTy on older months)
- `ISZE\01_data\00_derived\rush_order_share_by_db_q1fy2027.png` (network context only)
- `ISZE\09_meetings\IBX_Sales_Review_2026\IBX_SaTy_Fill_Rate_Dashboard.html` (method, not CDN)

### D. Lost-sales tracker (define it; do not invent a third metric)

Three **separate** lanes. Never summed into one “lost €”.

| Lane | Meaning | Source idea |
|------|---------|-------------|
| **GPS gap** | Wallet ceiling − captured. Addressable uncaptured. Not a booked loss. | `wallet_waterfall.csv` |
| **PMS gap** | Expected service qty − actual, by category, genuine vs BVP. | `pms_capture_by_db_year.csv` / `pms_summary_by_db.csv` — ITUK uses IML v7 if TARGET_DB=ITUK |
| **Street / IAM** | Aftermarket price pressure on the parts we actually sell | Eucon / price survey + billing top PNs |

Tracker UI: rank **the parts and categories where we believe we do the business** (top billed € for this DB, last complete CY + YTD), then for each:

- In PMS basket? Y/N
- Genuine declining / BVP growing / both down
- IAM price vs ISZE vs BVP (if a BVP exists in crossref)
- If no BVP in crossref → **SPA candidate** (not “create SPA now”)

Limit to a working set (top ~30 PNs by €, plus PMS core filters/brakes/clutch). Jerome said: track the parts we think we sell — not the whole catalog.

### E. Aftermarket prices × BVP × SPA

For the working-set PNs:

- ISZE price (PR00 / price file 2026)
- IAM / Eucon where a match exists
- BVP alternative from `genuine_bvp_crossref.csv` (incomplete — see ban 20)
- SPA status if a SPA file exists for this DB (`01_data\01_Pricing\`, UTI SPA files, NOx optimizer notes)

Rule of work Jerome already uses: **if IAM undercuts genuine and there is a BVP, push BVP; if there is no BVP, SPA is the lever** — on high-potential PNs, with management approval (ISD/IUK/Petros minutes). Do not list 400 PNs.

### F. Emails — open issues

Scan Jerome’s mailbox evidence already in the workspace before inventing a COM hunt:

- `ISZE\01_data\90_INBOX\outlook_*.json` (dealer-sales hunt, UTI sap4 hunt, 2026-08-13)
- `ISZE\05_memory\briefs\`
- Meeting folders under `ISZE\09_meetings\<DB>_Sales_Review_2026\`

Then, if you have Outlook/Composio access, search last 90 days for TARGET_DB name, sold-to, and known contacts from minutes (`05_memory\briefs\sales_reviews_Koen_2026-08-05_06.md` lists Koen circuit contacts).

Section layout: table of **open / waiting-on-them / waiting-on-us**, with date, person, one-line issue. No email bodies pasted. If you cannot access mail, say so in `DATA_INTEGRITY.md` and use minutes + INBOX JSON only.

### G. Latest meeting minutes

If a minutes file exists, extract **still-open** actions only.

Known minutes (Aug 2026 circuit):

| DB | File |
|----|------|
| Portugal | `09_meetings\PORTUGAL_Sales_Review_2026\MINUTES_ISZE_Astara_Portugal_2026-07-29.md` |
| ISD | `09_meetings\ISD_Sales_Review_2026\NOTES_MINUTES_2026-08-05.md` |
| Petros | `09_meetings\PETROS_Sales_Review_2026\NOTES_MINUTES_2026-08-06.md` |
| IUK | `09_meetings\IUK_Sales_Review_2026\NOTES_MINUTES_2026-08-06.md` |
| Ireland | `09_meetings\IRELAND_Sales_Review_2026\NOTES_MINUTES_2026-08-06.md` |

If TARGET_DB has no minutes: empty state + ping. Do not recycle another DB’s actions.

### H. IDS — dealer standard

Country pack + rollup:

- `ISZE\02_dashboards\ids\IDS_2026_dealer_compare_<Country>.html`
- `ISZE\09_meetings\IDS_2026_Country_Packs_v1.4\`
- `ISZE\09_meetings\IDS_2026_DB_Feedback_Sheet_v0.4\`

Must show:

- Country vs network on sections A–E
- **Section-level holes** — if a whole section was not participated (Israel LCV Section E = 0/18 on all 29 dealers), that is the headline, not a grey 0% bar that looks like “they scored zero because they are bad”. Label **did not participate / not scored**.
- Parts-relevant: Section D (Parts & Accessories) vs Section C (Service)
- Bottom dealers vs country average (heatmap). 5+ dealers = matrix, not 29 separate cards.

### I. Data integrity

On-page strip (not a dump): traffic lights for coverage.

Examples that are already true in this workspace (re-verify for TARGET_DB):

- PMS: 18/22 network DBs — Ukraine, Armenia, Kazakhstan, Palestine have no PMS rows
- Wallet waterfall: same 18-market hole for CIS/Palestine
- GPS v2 drops non-network: IMG, MIDI, TR, IMIO, Sverige2
- SaTy coded share uneven
- Warranty Dec-2025 missing in FY26 monthly
- UIO V19 2026+ forecast is the broken flat decay — don’t use it as a live fleet
- IUK Apr–Jun 2026 SAP extract was ~35% of Power BI — never cut PN movers on a thin extract
- Sales-to-dealer registry is only IRELAND, ITUK, IUK, UTI, GREECE

### J. What they should send us (sales-to-dealer is the #1 ask)

Jerome’s priority: **sales-to-dealer (DB → dealer)**. Dealers do not really overstock; StD is real demand and it feeds replenishment.

Canonical schema: `ISZE\01_data\12_raw\dealer_sales\DEALER_SELL_OUT.md`  
Registry: `ISZE\01_data\12_raw\dealer_sales\_registry.yaml`

Ask card (what’s in it for them, not a data dump):

- Monthly StD: invoice date, part number, quantity. EUR optional. Dealer dimension if they have it (ITUK does; IUK/Ireland/Greece often network-PN only).
- IUK rule: **do not ask IUK for EUR** — UK value from ITUK.
- Do not force one Excel layout; we adapt.
- If they already send it, show the last month received and the hole (e.g. UTI CY2025 Feb–Jul still thin despite sap4 hunt).

Also useful, secondary: updated UIO, KPI/SPI monthly, SPA candidate list, fill-rate series.

Standing rule: every new StD file → `01_data\90_INBOX\` → `12_raw\dealer_sales\<DB>\` → long CSV → **wire second layer** (`build_dealer_sellout_aim_gps.py`). Do not leave it “filed but unwired”.

---

## 4. Data map (read these; do not paste secrets)

Workspace root: `C:\Users\jerom\Desktop\claude\`  
ISZE: `C:\Users\jerom\Desktop\claude\ISZE\`

| Need | Path |
|------|------|
| Dimension / sold-to | `01_data\00_derived\distributor_dimension.csv` |
| GPS euros (canonical numerator) | `01_data\00_derived\gps_pure_sales_2026-08-13_v2.csv` |
| GPS SPU (unsigned % risk) | `01_data\00_derived\gps_spu_by_distributor.csv` |
| Wallet CY | `01_data\00_derived\wallet_waterfall.csv` |
| Mix genuine/BVP | `01_data\00_derived\mix_genuine_bvp_by_group.csv` |
| PMS | `01_data\00_derived\pms_summary_by_db.csv`, `pms_capture_by_db_year.csv` |
| BVP crossref | `01_data\00_derived\genuine_bvp_crossref.csv` |
| Warranty | `01_data\00_derived\warranty_raw_grain.csv`, `warranty_fy26_monthly.csv` |
| SaTy | `01_data\00_derived\q1fy2027_export_with_saty.csv` |
| Facts / GPS-PMS definitions | `ISZE\FACTS.md`, `03_analytics\Isuzu\prism\docs\metric_dictionary.md` |
| Integrity flags | `03_analytics\Isuzu\prism\docs\DATA_INTEGRITY_FLAGS_2026-05-28.md` |
| Pricing raw map | `01_data\01_Pricing\PRICING_DATA.md` |
| Eucon UK/ITUK 2023 | `01_data\01_Pricing\_raw\` (do not dump line-level into the HTML body) |
| StD | `01_data\12_raw\dealer_sales\` |
| IDS | `02_dashboards\ids\` |
| Chart.js local | `02_dashboards\_ui\chart.umd.min.js` |
| House style | `C:\Users\jerom\.claude\skills\visueel-rapport\references\house_style.md` |
| Visueel-rapport skill | `C:\Users\jerom\.claude\skills\visueel-rapport\SKILL.md` |

Line-level billing is 🔒. Aggregate in the HTML. Never paste customer-line extracts into the prompt reply.

---

## 5. Integrity protocol (do this before drawing)

1. Run / read preflight if a profile exists: `python ISZE\04_tools\db_sales_review\preflight.py --db <KEY>`
2. Confirm TARGET_DB is `network_db` in `distributor_dimension.csv`.
3. List every source you will quote with: file, grain, last date, row count for this DB, coverage holes.
4. Reconcile GPS euro (v2) vs wallet captured vs PMS revenue — they **will not match**. Write one sentence why (different baskets). If they match by accident, you probably double-counted.
5. Warranty in vs out: two numbers, same FY, labelled.
6. StD vs ISZE billing: StD is not GPS. Do not compute a fake “dealer GPS%”.
7. Double-check every hero number by re-filtering the CSV. Jerome will spot a 10% miss. Portugal/IUK decks took many correction rounds; `DB_SALES_REVIEW_BLUEPRINT.md` exists so you don’t repeat them.
8. Anything you cannot verify → `DATA_INTEGRITY.md` ping, and an on-page empty state. **A pretty chart with a wrong number is worse than no chart.**

---

## 6. HTML craft

- One file, self-contained. Payload as JSON in a `<script type="application/json">` then render.
- Sticky tabs. Hero on navy. Paper body.
- Controls: FY/CY, warranty in/out, (optional) commercial vs all.
- Tooltips on every derived chip.
- Footer: human-language sources + as-of date. No csv filenames in the rooms.
- `OPEN_*.cmd` beside the HTML.
- Language: English UI (ISZE meeting language) unless the DB pack is already Dutch-only.

---

## 7. What you hand back (for Cursor to finish)

Return:

1. Path of the HTML + `DATA_INTEGRITY.md` + `.cmd`
2. Hero numbers with grain and source (five lines max)
3. The integrity pings, numbered, that Jerome must answer
4. What you did **not** find (weekly orders, fill rate, minutes, StD, Section E participation)
5. Explicit statement: Chart.js is inlined / SVG used; no CDN; you visually checked charts with a local open — or you could not, and Cursor must

Do **not** add more distributors. Do **not** rebuild the network cockpit. Do **not** invent a GPS%.

Start by filling TARGET_DB, reading `distributor_dimension.csv` for that row, then `DATA_INTEGRITY.md` as a living list while you work — write the HTML last, when the numbers have survived the double-check.
