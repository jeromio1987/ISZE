# DRAAIBOEK — ISZE operating dashboard build

**For Cursor.** Sequenced execution plan. Work top to bottom. Every phase has a **GATE** —
do not start the next phase until the gate passes.

Companion docs (read once, before Phase 0):
- `CURSOR_BUILD_ORDERS.md` — the spec: hard bans, room-by-room ledger keys, blacklist
- `09_meetings\UMI_Operating_Dashboard_2026\DATA_INTEGRITY.md` — the 10 open pings

**Core rule that governs the whole build: RENDER, NEVER COMPUTE.** All numbers are in
`NUMBERS_LEDGER.json`. If a figure is missing, extend `build_ledger.py` — never calculate in JS.

**Architecture decision, already made — do not deviate.** You are building **one template plus
one renderer**, not 18 hand-built HTML files:

```
04_tools\db_operating_dashboard\
  template\dashboard.html.j2     one parameterised template
  template\assets\chart.umd.min.js  physical copy, inlined at render time
  render_dashboard.py            --db X  ->  reads ledger + template -> writes HTML + .cmd
```

18 dashboards = one template rendered 18 times. A fix made once propagates to all.

---

## PHASE 0 — Inputs and environment

**Goal:** prove the inputs are good before writing any HTML.

1. Regenerate every ledger:
```bash
python 04_tools\db_operating_dashboard\build_ledger.py --all
```
2. Confirm 18 ledgers exist and each parses as JSON.
3. Copy Chart.js into the template assets folder:
   `02_dashboards\_ui\chart.umd.min.js` → `04_tools\db_operating_dashboard\template\assets\`
4. Verify the copy: **200,807 bytes, 0 occurrences of `sourceMappingURL`**, ends with
   `window.Chart=i` UMD tail. Nothing needs stripping.

**GATE 0** — all true:
- [ ] 18 × `NUMBERS_LEDGER.json` parse without error
- [ ] Chart.js copy byte-identical to source, 0 `sourceMappingURL`
- [ ] `flags` block present in every ledger

If a ledger fails to parse, stop and report — do not patch the JSON by hand.

---

## PHASE 1 — UMI pilot HTML

**Goal:** one complete, correct dashboard for **UMI only**. UMI is the pilot because it is the
best-instrumented DB and it exercises every edge case (negative ex-warranty, frozen PMS UIO,
the 22× BVP trap, empty minutes, empty StD, thin SaTy coverage).

Build in this order. Each step is small and independently checkable.

### 1.1 Shell
Single file. `<script type="application/json" id="payload">` holding the ledger, then inline
Chart.js, then your render code. Sticky tab bar, persistent hero strip, paper body, navy header.
House style tokens as CSS variables: navy `#15233c`/`#1a2b4a`, terracotta `#c0552d`,
paper `#f7f4ee`, line `#d9d3c8`, muted `#6b6256`, ink `#222`, green `#1d9e75`, amber `#eda100`,
red `#b23b3b`. Georgia headings, Segoe UI body.

### 1.2 Tooltip component
`data-tip` → navy panel, paper text, terracotta accent. Reads `tooltip.formula`,
`tooltip.snapshot`, `tooltip.not_included`, `tooltip.warning`. Build this **before** the hero —
every derived chip needs it and retrofitting is painful.

### 1.3 Hero — `hero`, `business_plan`, `plan_tracking`
Four chips, grain on each. Chip 2 (ex-warranty) is a **toggle of chip 1**, not a second
headline. Chip 3 (PMS) **never renders without the network comparator**. Chip 4 is labelled
"ceiling, not a forecast".
Footer of the hero: the D-Max rate and its date, so the denominator is never ambiguous.

### 1.4 Room A — Plan tracking
Waterfall BP → stretch → EXT TARGET with the max-spend ceiling as a reference line.
FY actuals vs EXT TARGET bars (target in terracotta). Bullet gauge target-vs-ceiling.
`bp_match.verdict` renders as a green tick when MATCH.

### 1.5 Room B — GPS spine
**Max two FY lines**: GPS % and GPS % ex-warranty. No calendar-year third series.
Honour `render_rules` exactly:
- FY2023 hatched + labelled partial
- FY2023 has no ex-warranty point
- **FY2024 `ex_warranty_renderable: false` → draw nothing.** Not a zero bar, not a negative bar.
  An explicit "not a valid euro — claim-price vs ISZE-net basis" marker.
- `gps_pct_v31_published` goes in a tooltip only, never as a visible second number

### 1.6 Room C — PMS
Diverging bars, UMI vs network, sorted by revenue gap. Grey the 3 `quotable: false` categories
and exclude them from every euro total. Show `interval_confidence`.
**No time series** — `uio_units` is frozen across all years.

### 1.7 Room D — Genuine vs Best Value
Render `whole_book` (96.3% genuine / 3.7% BVP). If you also show `paired_basket_only`, its
`coverage_pct_of_book` (5.0%) must be **on the chart**. Never present 81.6% as UMI's BVP share.
Best Value is retention — never red, never in an erosion total.

### 1.8 Room E — Order pattern
100% stacked by CY. `PRD` gets its own band (7.5% of CY2025 euros — not stock, not rush).
Q1 FY2027 leads with coded share 65.9% → **amber**.
**The "same-day warehouse" remark must NOT fire for UMI** (rush 20.0 → 12.9 → 10.7%).
Cadence chart titled "ISZE invoicing rhythm".

### 1.9 Room F — Three erosion lanes
Three cards. No total, no shared axis implying addition.
IAM card: print `db_revenue_coverage_pct` (9.2%) on the card. **Obey `SIGN_CONVENTION`** —
positive = ISZE cheaper = green. Use `db_revenue_on_exposed_pns_eur`; never the
`..._NETWORK_LEVEL_DO_NOT_ATTRIBUTE` field.

### 1.10 Room G — Working set
Top 30 PN. Mark the 2 Shell rows distinctly (excluded from the GPS numerator; #1 PN is 12.6%
of CY2025 euros). Honour `warranty_exclusion_warning` — 27 of 30 sit on warranty claim lines,
so show both lenses and label the limitation. Do not apply the binary exclusion.

### 1.11 Room H — IDS
Israel LCV 29 × 5 heatmap. Lead with **Section D (Parts) −17.1pp**, not Section E.
Section E gets a distinct **"not scored / participation to confirm"** fill — never the same red
as a genuine low score. Scoreboard reads **0/27**, prose says 18 questions.

### 1.12 Rooms I and J
Integrity strip from `source.in_green_verification_report` + known holes, linking to
`DATA_INTEGRITY.md`. StD ask card from `empty_states.J_sales_to_dealer.ask_card` — UMI sends
nothing, and UTI's files are **not** Israel coverage.

### 1.13 Empty states
`empty_states.F_emails` and `.G_minutes` render as cards. Never recycle another DB's content.

**GATE 1** — grep and eyeball:
- [ ] `src="https://` → 0 · `href="https://` → 0
- [ ] Opens with the network disabled; every chart draws
- [ ] No csv/parquet filename anywhere in the visible body
- [ ] Every derived chip has a working tooltip
- [ ] No negative bar, no zero-denominator chart
- [ ] Genuine/BVP shows 96.3 / 3.7
- [ ] No "same-day warehouse" remark
- [ ] Section E reads 0/27 and "not scored"
- [ ] No UTI figure anywhere; nothing labelled "Israel"

---

## PHASE 2 — Visual QA

**Goal:** catch what reading the code cannot.

Open the file and **look at every tab at 1280px and at 1920px**. The blueprint's QA pass caught
an agenda overflowing behind a footer, a paragraph repeated on consecutive slides, and a
mis-cased title — none visible from the source.

Check specifically:
- Overlapping axis labels (Chart.js overlapping after two attempts → switch that chart to inline SVG)
- Bar thickness ≥18px, ≤6 axis ticks, round memorable ticks
- **Contrast: no white text on paper, no pale text on pale.** This is the KAMLIJN bug.
- Wide tables/charts scroll inside their own container; the body never scrolls sideways
- Tab switching does not reflow the hero

**GATE 2** — you have personally viewed all tabs at both widths and fixed what you saw.

---

## PHASE 3 — Generalise and render all 18

**Goal:** the pilot becomes a template.

1. Extract the UMI HTML into `template\dashboard.html.j2`. Every literal number, label and
   name becomes a ledger lookup. **Zero hard-coded UMI values may remain** — grep the template
   for `UMI`, `1797`, `Israel`, `18542`, `4635500`, `262.50` and eliminate each.
2. Write `render_dashboard.py --db X` / `--all`: loads the ledger, renders the template, writes
   `<DB>_Operating_Dashboard.html` + `OPEN_<DB>_Operating_Dashboard.cmd`.
3. Handle the structural variants — these are real and will break a naive template:
   - `flags.HAS_V31_FY_SERIES` false (**ITUK, UTI**) → no FY GPS% series. Show euros and the
     Dashboard FY27 figures. **Do not synthesise a series.**
   - `flags.SHOW_GPS_PCT` false (**Ireland, Finland, Iceland**) → suppress every percentage.
   - `sections.pms.available` false (CIS, Palestine) → drop the room.
   - `sections.three_lanes.street_iam.available` false (**UTI**) → empty state.
   - No IDS pack (**Germany, Ireland, Sweden, Finland, Iceland, UTI**) → drop the room entirely.
   - Mixed DBs carry LD/MD/F-Series/LCV segments; pure-LCV DBs carry one. The rate-impact
     block must render both shapes.
4. Render all 18.

**GATE 3**:
- [ ] `render_dashboard.py --all` exits 0, 18 HTML + 18 `.cmd` written
- [ ] Template contains no DB-specific literal
- [ ] Spot-check **4 DBs covering the variants**: UMI (full), **UTI** (no FY series, no IAM, no
      IDS), **IRELAND** (GPS suppressed, no IDS), **GERMANY** (mixed segments, no IDS)
- [ ] Each of the 4 opens offline with 0 CDN references
- [ ] Ireland shows no percentage anywhere

---

## PHASE 4 — Per-DB DATA_INTEGRITY.md

Only UMI has one. Extend `build_ledger.py` to **emit it** rather than hand-writing 17.

Generate from what the ledger already knows: sources with `in_green_verification_report: false`,
`do_not_use` blocks, `DANGER` / `warning` / `critical_warning` strings, failed reconciliation
checks, `available: false` rooms, and the blacklist. Plus the per-DB watch items already in
`04_tools\db_sales_review\db_profiles.yaml`.

**GATE 4** — 18 `DATA_INTEGRITY.md` files, each naming that DB's real holes, no UMI content
leaking into another DB's file.

---

## PHASE 5 — Wire Auto 365 (Israel)

Highest-value data fix. `04_tools\autodoc_scraper\auto365_results.csv` holds **208 priced Israel
rows** and nothing joins them to ISZE part numbers or revenue. The scraper runs weekly and its
output is unused.

1. Inspect the 9 columns; establish the PN key and how it maps to ISZE part numbers.
2. Build a derived join → `01_data\00_derived\iam_israel_price_gap.csv`, same shape as
   `eucon_price_gap.csv` so the existing lane-3 code path picks it up.
3. Feed it into `build_ledger.py` for UMI and UTI only.

Two hard constraints: keep the **sign convention** identical (positive = ISZE cheaper), and
**never** produce a network-level euro that gets attributed to a single DB — that is the bug
already caught once in this build.

**GATE 5** — UMI and UTI IAM coverage rises above its current 9.2% / 0.0%, and the DB-scoped
exposure figure is genuinely DB-scoped.

---

## PHASE 6 — Lost-sales upgrade (only after Jerome says go)

Today the lost-sales view is **gap arithmetic, not a model**: three deterministic lanes, no
propensity, no time-to-churn, no elasticity, no dealer-level defection.

21 green-verified derived tables are unused. Highest value first:

| Table | Adds |
|---|---|
| `defection_alerts.csv` | 25 active alerts — actual churn signal |
| `capture_recovery_model.csv` | what recovery is realistic, not just the gap |
| `substitution_timeline.csv` / `substitution_by_pair_year.csv` | genuine→BVP timing, per pair |
| `part_lifecycle.csv` | supersession vs real loss — kills false "new business" |
| `aim_gps_matrix.csv` / `aim_exposure_by_db_year.csv` | AIM exposure per DB |
| `vor_profile.csv` / `vor_seasonality.csv` | rush behaviour beyond a SaTy share |
| `network_percentile.csv` / `db_benchmark_mix.csv` | proper peer positioning |
| `pms_opportunity_matrix.csv` | prioritised PMS actions |
| `price_premium.csv` | price position without the scraper hit-rate problem |

**Do not start Phase 6 without an explicit go.** It changes what the dashboard claims.

---

## Blocked? Do this

- **Number missing from the ledger** → extend `build_ledger.py`, re-run, continue. Never compute
  in the HTML, never hand-edit the JSON.
- **Number looks wrong** → check `reconciliation.checks` in that ledger, then the `source` stamp
  on the field. Report rather than "correcting" it.
- **Chart will not lay out** → two Chart.js attempts, then inline SVG. Do not shrink fonts below
  the style floor.
- **A source is not in the green verification report** → that is expected for 8 of 14; the
  `in_green_verification_report` flag drives the integrity strip. Not a blocker.
- **You want to add a distributor** → the registry in `build_ledger.py` is the only place.
  Turkey (AIOS) and MIDI Europe are **not** ISZE distributors — never add them.

## Never

Full list in `CURSOR_BUILD_ORDERS.md` §3 and §6. The three that will silently ruin a meeting:

1. **Summing the three erosion lanes** into one "lost sales" euro.
2. **Blending UMI 1797 with UTI 1799**, or labelling either "Israel".
3. **Reading a blacklisted file** — above all `competitiveness_autodoc_risk.csv`, where all 298
   rows carry a £2.00 placeholder as if it were a competitor price.
