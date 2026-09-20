# ISZE state packet

**Updated:** 2026-09-20 — AIM residual top-N by L12M (`residual_topn_20260920`)

## AIM residual Other/review — highest euro (2026-09-20)

Top-100 still-open by L12M; applied **42** clear leaves · **EUR 198,714** · stamp `residual_topn_20260920`.
Still-open after: **EUR 84,540** (catalog Other still 9,459 / EUR 717k until classification rebuild).
Gate **PASS** 18/18. Backup `aim_master_v2.csv.bak_pre_residual_topn_20260920_054954`.
Worklist: `01_data/90_INBOX/AIM_residual_Other_review_topN_by_L12M_20260920.csv`.

Prior same day: EQ overnight **384** PROPOSE_PATCH (`eq_session_20260919`). Attribute layer on hold. No shared HTML. No commit.

---

**Prior update:** 2026-09-19 — boardroom: MapChart banned; Europe footprint uses IDS ~564-dealer map

**Boardroom maps:** never `mapchart.net` / yellow-blue clip-art. Footprint slide uses
`01_data/90_INBOX/data_join_questions/assets/ids_europe_dealer_network_564.png` (from
`02_dashboards/ids/_qa_map_triple/master_map_live_tiles.png`). Rule gate:
`.cursor/rules/isze-boardroom-deck-process.mdc` — PNG export + image-Read per slide before done.

## Built (2026-09-19) — PMS family evolution v2, forms 2 / 8 / 10 with both percentages

**Page:** `02_dashboards/sales/ISZE_PMS_Family_Evolution_v2.html` (+ `OPEN_ISZE_PMS_Family_Evolution_v2.cmd`,
CRLF, cmd-only). Rebuilt from `_build/build_family_evolution_v2.py`, then verified independently here.
Default is **form 2** (two columns and the difference), with 8 and 10 one click away on the same rows.

**The point of the page, on the real ITUK book — N-series truck, CY2023 → CY2025:**

| | first year | second year | change |
|---|---|---|---|
| Billed euro | 727,731 | 753,204 | **+3.5%** |
| Vehicles in service (workbook's own count) | 19,559 | 22,191 | +13.46% |
| Euro per vehicle | 37.207 | 33.942 | **−8.78%** |

They disagree, and that is the finding: `(1 + 0.0350) ÷ (1 − 0.0878) = 1.1346`, which is the fleet
ratio `22,191 ÷ 19,559`. Every form prints both percentages, so a euro move cannot be read without the
fleet move beside it. Read on the rendered page, not from the build.

**Verified here, not taken from the builder's word:** `verify_derived_pipeline.py` 153 pass / 1 warn /
0 fail · `ship_gate_check.ps1` → `SHIP_GATE_OK` · page gate `QA PASS` (decomposition identity holds to
**EUR 0.0000**) · receipt `ISZE_PMS_Family_Evolution_v2.SHIP_RECEIPT.json` (mtime 15:40 covers the page
at 15:38). Both percentages confirmed as rendered table headers (`Change in billed euro`, `Change in
euro per vehicle`, `Fleet this period`, `Fleet last period`, `Fleet change`), 18 customer options, no
console error, nothing fetched, no CDN.

**Two harness limits, found while checking:** form 8's canvases read `0x0` after a switch while the
page shows their bars (see the canvas section above — the check is now bar-colour pixels on the
composited screenshot, `_build/qa_forms_painted_v2.py`), and form 8's fleet switch is asserted only on
the comparison-year bar because the current-year denominator **is** the 2025 estimate and cannot move.

## Error register updated

`01_data/90_INBOX/ISZE_Agent_Error_Register_2026-09-18_19_v2.xlsx` — **28 rows, 12 Critical, 10 High,
6 Medium, 10 root causes**. E27 (the fleet in the denominator, 9 of his turns against the 4 a reply
gave), E28 (a capability reported missing without testing it), R9 (a count answered from memory) and
R10 (a limit asserted from one bad test). Totals are derived from the rows. Gates:
`_qa_error_register.py`, `_fix_register_mojibake.py`.

## Excel on this machine

Office 16 ClickToRun is installed (`Root\Office16\EXCEL.EXE`, 16.0.20326.20144; resolved via the App
Paths registry key). The excel connector reads a workbook, cell by cell and structurally, **without
Excel on PATH** — that is how the register above was read back. Only COM recalculation needs Excel
(`EXCEL_ENABLE_COM=true`, off). `shutil.which('EXCEL.EXE')` returns None for ClickToRun: **not** a
test for Excel.

## Pricing stack — where it stands (2026-09-19)

**The move is the weighted increase of all prices, measured.** Not a formula. Jerome: *"you need to
look at the weighted increase of all prices not the formula."*

| Measure | Weighted increase |
|---|---:|
| Whole priced book | **+5.9616%** |
| Japan (IML) | **+6.2081%** |
| Thailand (IMIT) | **+6.3088%** |
| PR00 | +5.9211% |
| UTI | +5.5808% |
| UMI | +5.6370% |
| CIS | +4.8455% |

All four markets inside 4–6%. Recipe `in_scope == True` AND `unpriced_reason IS NULL`, 47,617 rows,
reproducing the published 5.9616% exactly.

**What it replaced.** A factor chain — `(1+revision) × (163.7/178.5) × (0.673/0.620)` — that
multiplied by a rate and a discount **already in force**. It put Thailand at −2.45%, a reduction,
against the measured +6.31%. The exchange rate is corporate and applied; a "pass-through dial" was
invented and has been removed from every artefact.

**What the base price is.** The IML Export Base Price is built up from IML's own costs; our purchase
price is a discount **off** it — 62% vehicle parts, 73.5% industrial engines (Hayakawa, 10 Nov 2025).
So the base carries a margin that is not ours, and the class letter sets ours on top.

**Artefacts.** Workbook `01_data/01_Pricing/ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx` with a
sibling launcher; write-up `01_data/90_INBOX/PRICING_STACK_APPLIED_2026-09-19.md`; roadmap
`00_docs/roadmaps/pricing.md` (hub item 16). Receipt regenerated 12:52 to cover the current file.

**NOT VERIFIED:** that Excel opens it and that it scrolls. No Excel or COM on this machine. The two
mechanical causes of the earlier scroll failure were removed and are asserted in the receipt.

**Open from this session:** the industrial-engine discount rate (config applies the vehicle-parts rate
to everything Japanese); IML's "around 3%" against our measured 5.9616%; the override rows; the
no-source-label rows (1,801 rows, 9.2% of weight, +3.06%).

**Error register:** `01_data/90_INBOX/ISZE_Agent_Error_Register_2026-09-18_19_v2.xlsx` — **28 rows,
12 Critical, 10 High, 6 Medium, 9 root causes**. Updated 19 Sep with **E27** (the fleet must sit in
the denominator; his own turns on it counted from the transcript at 9, not the 4 a reply gave) and
**E28** (a capability reported missing without testing it), plus **R9**. Severity totals and the
register total are now derived from the rows, not typed — typed totals were wrong twice on 19 Sep.
Row heights derive from the longest cell, so a long evidence entry cannot clip. Two defects found
and fixed while doing this: corrupted dashes in E11's text (UTF-8 read as cp1252), and five error
rows that had counter-measure text but no row on the Counter-measures sheet. Gates:
`_qa_error_register.py` (28 rows, no clipping, totals reconcile, every error has a counter measure)
and `_fix_register_mojibake.py` (zero corrupted sequences).

**Excel on this machine — read/write works, and it was wrongly reported missing.** Office 16
ClickToRun is installed at `C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE`
(16.0.20326.20144; the App Paths registry key resolves it). The excel connector opens a workbook,
returns any cell or sheet, runs structural render checks and exports — that is how the register
above was read back. **A workbook can therefore be read, cell-level checked and exported with no
Excel on the machine at all.** The one thing that needs Excel itself is driving COM to recalculate
(`EXCEL_ENABLE_COM=true`, currently off). `shutil.which('EXCEL.EXE')` returns None for a ClickToRun
install because Office is not on PATH — do not use it to test for Excel.

## CV warranty — "LD" weight class and the parts wallet (2026-09-18)

**The `LD` label is not a weight class.** It reads 6.5/7.5 t in Israel and 3.5 t in most of Europe,
and the same token drives the parts-wallet rate per market. Israel's `LD` row was **priced
correctly all along** (€739, the 7.5 t rate) — the label was the defect, not the number. Two
independent sources confirm the market holds no 3.5 t Isuzu truck: the CV warranty VIN register
(2,360 VINs, Dec 2023 → Mar 2026: NPR75 895, FRR90 817, FSR90 627, zero NLR/NMR/NKR) and the
Ministry of Transport band table, whose smallest class is 6.5–7.5 t.

| Item | Path |
|------|------|
| Workbook (relabelled; numbers untouched) | `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx` — note in **B92** of `1.UIO Overview`, Changelog V19-5..V19-7 |
| Pre-edit backup | `06_uio/_Archive/ISUZU_UIO_Overview_2026_backup_before_ld_relabel_20260918.xlsx` |
| Evidence note | `01_data/90_INBOX/_ld_weight_class_and_wallet_correction_20260918.md` |
| Per-market split table | `03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv` |
| ITUK mileage question (draft, not sent) | `09_meetings/ITUK_MILEAGE_QUESTION_2026-09-18.md` |

**Applied, not proposed.** (1) The workbook is relabelled — every chart, image, formula and numeric
cell is byte-identical to the prior revision, verified by comparing zip parts. (2) PRISM now splits
the collapsed `LD` row **per market**, not just the UK (`data_prep.py`). (3) The JP VIN register
tonnage decode is fixed: it read the number in the chassis code as a tonnage, so NLR 3.5 t trucks
were recorded at 8.7 t and both FRR90 and FSR90 at 9.0 t. Rebuilt: **19,545 t over 3,238 trucks,
6.04 t average** (was 26,689 t / 8.24 t). New `gvw_t_source` column.

Measured 2025E target-wallet effect of the split: **PORTUGAL ×0.801, MALTA ×0.895, IRELAND ×0.979,
BELGIUM ×0.981, GERMANY ×0.982, CYPRUS ×0.993. ISRAEL and ITUK deliberately unchanged.** Germany is
**22%** 3.5 t on the Helwig parc bands and Malta **37%** — `V20_SPEC` §Problem 6 listed both as
"0% — no change", corrected in that file. Portugal's GPS percentage rises about a quarter.

**Then the shares themselves were audited (2026-09-18, later).** Every row of the share file was
recomputed from the source it names. **IRELAND was wrong: 0.063 → 0.3089.** It was tagged `simi_bands`
but carried the JP VIN register number (36/570). The SIMI parc basis is **464 of 1,502** at 2025;
flow basis 663/1,963 = 0.3377. **BELGIUM 0.918 → 0.8571** (NLR 42 of 49). **PORTUGAL 0.620 →
0.6899** (1,299 of 1,883 N-series; the old row divided by all 2,111 rows). **MALTA and CYPRUS marked
`unmeasured`, rates held** — both rested on reading NMR88 as an N35, but NMR88 is 9.5 t and Cyprus
holds zero 3.5 t. Germany, Greece, ITUK and UTI confirmed. Target wallet (computed, waterfall **not**
rebuilt because it is locked): Ireland €935,912 → €856,281, Portugal €2,446,187 → €2,377,877,
network −0.46%. Verifier 143 pass / 0 fail. Audit: `01_data/00_derived/n35_share_audit_20260918.csv`.

**Two mistakes made and fixed during the pass, recorded so the next agent does not repeat them:**
a zero share initially *deleted* Israel's 6,059 trucks instead of passing them through (would have
dropped UTI's ceiling by €8.3M); and the workbook note was first put in **D7**, which the loader
reads as the model field, so a paragraph became a model name. Both caught and corrected before
leaving this session. Backup taken before the workbook edit.

**Nothing published, no mail sent, no price moved.** PRISM suite green (71 passed).

### Warranty commercial datasets (2026-09-18) — folder + workbook, with a currency correction

**`01_data/00_derived/warranty_commercial/`** — 13 CSVs, a 13-sheet workbook, a README and an
`OPEN_*.cmd`, all regenerable from `01_data/91_build/build_warranty_commercial_datasets.py`. One file
per commercial question, all markets inside each file. Excel pre-delivery check **OK, issues=0**.

**A currency error was found and corrected in doing this.** The truck claim file's `CRNCY` column
carries two tokens: `EUR GBP` means the amount is in **pounds** (UK — 11,956 lines, the largest book
in the file) and `JPY EUR` means **yen** (Italy, Spain, France, Switzerland and others). The earlier
note summed that column raw, mixing three currencies. Corrected: truck parts turnover **€4.66M** (not
€2.83M), emissions **€2.84M = 61%** (not €1.82M = 64%), truck steering gear **~€1.15M** (not
€800k). The D-Max figures were already normalised and are unaffected. Every euro in the new folder is
normalised first (EUR as-is, GBP ×1.12, JPY ÷163.7) and `warranty_cv_currency_audit.csv` shows the
working per market.

### Warranty data — what else it carries (2026-09-18, read-only)

A third pass over the claim files with a commercial lens. **Findings and limits:
`01_data/90_INBOX/_warranty_data_what_else_it_carries_20260918.md`.** Nothing was built or published.

- **The claim files hold no maintenance.** Oil filter 8 CV lines / 2 LCV, air element 0 / 2, brake pad 0 / 33.
  A consumable is not a defect and is not claimed, so **measured replacement intervals cannot come from
  warranty** — the `air_filter: 0.5` factor needs dealer repair-order data or a parts basket.
- **The single dominating line is the power steering gear**: €800,177 on 329 D-Max claims at €2,432 a
  truck, present in 22 of 30 markets, failing at 2.7 years — inside warranty. On trucks €800,191 on 329
  claims, same per-claim cost. One part family, both fleets, ~€1.6M.
- **42% of D-Max parts turnover sits outside the 3-year / 100,000 km limits**, and overwhelmingly on age
  rather than distance. Per market it runs from **25% (Sweden) to 68% (Norway)** — a loyalty decision
  per book, not a technical one.
- **Settlement rates diverge 3.7×**: Belgium recovers 47% of claimed parts, Poland 173%.
- **`PARTNBR2` is empty on all 33,416 CV lines**, which settles the 33,416-vs-16,480 question — the line
  count is the true claim count and 16,480 was a double-count.
- **Dealer code `V19010` carries 36% of all CV claim lines.**
- **The UK duty-cycle story is downgraded, not confirmed.** Sweden replaces the steering gear sooner
  (17,008 km vs UK 29,624) and the 25th-percentile claim odometer is 526 km in Sweden against 12,112 km
  in the UK, so the near-zero readings are a booking convention. The clean UK issue remains the mileage
  assumption (in `ISZE_ROADMAP.md` B11), not duty cycle.

## Delegator watch + the +5% review (2026-09-17 late evening)

Three things, all new files. Nothing existing was overwritten.

**A 20-minute AIM watch is armed and detect-only.** Windows task `ISZE_DelegatorWatch_20min` ticks every
20 minutes, fingerprints five AIM and pricing-base files, and writes a row to a shared agent board only
when a fingerprint actually moves. It wakes no agent, rebuilds nothing, and refuses to write any locked
pricing deliverable. Agents cannot ping each other — Cursor has no such tool — so the board is the
substitute: each agent reads it at the start of a run and appends a row at the end.

| Item | Path |
|------|------|
| Script / launcher | `04_tools\workspace\isze_delegator_watch.ps1` · `run_delegator_watch.cmd` |
| Self-test (15 assertions, all pass) | `04_tools\workspace\_test_delegator_watch.ps1` |
| Board / state | `00_docs\agent\DELEGATOR_BOARD.md` · `DELEGATOR_STATE.json` |
| Change procedure / rule | `00_docs\agent\DELEGATOR_REFRESH_HOWTO.md` · `.cursor\rules\isze-delegator-board.mdc` |
| Task XML | `04_tools\workspace\ISZE_DelegatorWatch_20minTask.xml` |

**A +5% flat increase is computed as a paper exercise on new dated files.** On the in-scope L12M base
(EUR 34,993,609.39 billed over 48,653 lines, 15,872 part numbers): **+5% = EUR 1,749,680.47**. The filed
revision on the same base is EUR 1,652,140.71 at 5.9616% published — two separate proposals, never added.

**The step ties out; the published rate does not.** Recomputed on the file, the quantity-weighted move is
5.9787% across all in-scope lines and 6.2347% across priced rows only; the published 5.9616% implies a
denominator of about EUR 27.71M that no column reproduces. The page claims the step, not the rate.
1,647 lines carrying EUR 4.48M (12.81% of billed) cannot move at all — no base price on one side.

| Item | Path |
|------|------|
| Workbook | `01_data\01_Pricing\Price_Increase_5pct_Flat_REVIEW_2026-09-17.xlsx` |
| HTML + receipt | `02_dashboards\pricing\ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html` (+ `.SHIP_RECEIPT.json`) |
| Launcher | `02_dashboards\pricing\OPEN_ISZE_Price_Increase_5pct_Flat_REVIEW.cmd` |
| Builder / verifier | `02_dashboards\pricing\_build\price_5pct_review_2026-09-17\` |

Gates: verifier **57 pass / 0 warn / 0 fail, `SHIP_GATE_OK`**; `excel_pre_delivery_check.py` 0 issues;
4 charts painted in real Chrome at 2 widths, no console errors, 19 PNGs on disk of which 6 were
image-read at full size. **Nothing published, nothing mailed, no live list touched.**

**Two things waiting on Jerome** (in `DECISIONS.md` 2026-09-17): whether IML re-bases the list at the new
SPA rate of 172.6 rather than the engine's 163.7 — a re-base cuts euro cost about 5.2%, roughly the whole
increase — and whether the +5% is flat across the book or follows the AIM priority ranking.

**Locked read-only (Jerome, 2026-09-17).** The shipped revision pack and page, the AIM priority list, and
anything already under `01_data\00_derived\` — plus `03_analytics\isze_pricing\config.yaml`, whose FX fork
stays open. New work goes to new dated files. Procedure: `00_docs\agent\DELEGATOR_REFRESH_HOWTO.md`.

## AIM classification — paper rebuilt on 18 Sep master (2026-09-18)

Shared paper refreshed from live `aim_master_v2.csv` (**165,213** rows, **2,417** `gap_auto_20260918`)
and `aim_pn_classification_v2.csv` (catalogue **7 / 27 / 176 · 164,667**). Hero no longer prints 164,667.
Builder for the refresh: `01_data\91_build\rebuild_aim_classification_paper.py`.
Two-axes lock and attribute-layer hold from 17 Sep still stand.

| Item | Path |
|------|------|
| Gate | `01_data\00_derived\aim_classification_gate.json` |
| v2 + meta | `01_data\00_derived\aim_pn_classification_v2.csv` |
| Focus CSVs | `01_data\00_derived\aim_catalog_focus_filters.csv` (+ matrix / brake / priceclass) |
| Paper + OPEN | `02_dashboards\sales\ISZE_AIM_Classification_Paper.html` · `OPEN_ISZE_AIM_Classification_Paper.cmd` |
| Receipt | `02_dashboards\sales\ISZE_AIM_Classification_Paper.SHIP_RECEIPT.json` |

Still open: Axis B scoring build; EQ column fill; Other/review residual needs figure majority
(~9.5k PNs); gasket/harness/pipe home. **Attribute layer: on hold (roadmap)** — Jerome 2026-09-17;
do not build; not proceed; attributes-before-levels stays recommended when resumed.

## Price revision — AIM source pack rebuilt on 18 Sep master (2026-09-18)

Cube → Excel → HTML rebuilt after the master gap fill. **Step EUR 1,652,140.71 / weighted 5.9616%** still
ties. Not-on-AIM in-scope euro **EUR 6,883,707.71 → EUR 1,660,928.43** (spine coverage **80.33% → 95.25%**).
Excel COM Checks sheet: diff 0. Customer-first drill unchanged.

| Item | Path |
|------|------|
| HTML + OPEN | `02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html` · `OPEN_Pricing_Revision_AIM_Source.cmd` |
| Excel + OPEN | `01_data\01_Pricing\Pricing_Revision_AIM_Source_Analysis.xlsx` · `OPEN_Pricing_Revision_AIM_Source_Analysis.cmd` |
| Receipts | `…AIM_Source.SHIP_RECEIPT.json` · `…AIM_Source_Analysis.SHIP_RECEIPT.json` |

## Price revision — AIM source analysis shipped (2026-09-17)

Two deliverables, both verified: an Excel workbook and a self-contained HTML page, built on the
**price-revision weight base** (`01_data\00_derived\price_bp_weighted_compare_pn.csv`,
`in_scope == True`), window 1 Jul 2025 to 30 Jun 2026 — **48,653 in-scope lines over 15,872 part
numbers, EUR 34,993,609.39 billed**.

**The headline ties out to the published revision: step EUR 1,652,140.71 and weighted increase
5.9616%**, both verified by recalculating through Excel with zero formula errors.

The analysis is on the **AIM spine** (`aim_l1_fixed` / `aim_l2_fixed` / `aim_l3` from
`aim_master_v2.csv`), with **source of supply** as J (Japan through IML) or T (Thailand through
IMIT), which is what was asked for. Coverage is named, not hidden: AIM level 1 covers 80.3% of
in-scope euro, level 3 is filled on 80.3%, source of supply is held on 93.6%; the remainders
appear as explicit buckets.

| Item | Path |
|------|------|
| Excel workbook (11 sheets, live formulas over a 48,653-row data sheet) | `01_data\01_Pricing\Pricing_Revision_AIM_Source_Analysis.xlsx` |
| HTML (self-contained: data and Chart.js inlined) · launcher | `02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html` · `OPEN_Pricing_Revision_AIM_Source.cmd` |

Sheets: DB summary, DB × AIM L1/L2/L3, TH-JP source, Source × AIM L1, Customer, Top movers,
PN data, Checks. An FX cell on Checks revalues the whole file. The HTML has a distributor
dropdown, a source filter, a weighted % / step EUR / billed EUR metric switch, and click-to-drill
L1 → L2 → L3. No CDN and no server needed.

Prior step pack (upload of the new base price) remains at
`02_dashboards\pricing\ISZE_Price_BP_Weighted_Compare.html` and
`01_data\00_derived\price_bp_weighted_compare_{pn,customer}.csv`.

**Prior pass on the step pack (2026-09-17, same day).** The "what this comparison does not cover"
table now names each bucket and its owner instead of three anonymous totals (the lubricant bucket
as UMI's engine oil, 7 PNs, sold-to 1797), and the ranked table carries a Description sourced from
the text as billed in SAP. A latent defect was closed while doing it — three of six Checks rows
returned an Excel error instead of OK because their Expected cells held formatted text and one
tolerance was too tight at `ROUND(...,3)`. Gates: Excel recalculated via COM, 6/6 reconcile checks
OK; `excel_pre_delivery_check.py` passed; HTML verifier 44/44 checks OK; render QA read at 4 widths
(0 blank canvas, 0 clipped, 0 white-on-pale, 0 console errors).

**Israel split — resolved and still the rule.** `sold_to_sap` is the key (1797 = UMI, 1799 = UTI).
The `sold_to` NAME column was relabelled 2026-04-01 and now reads UNIVERSAL MOTORS ISRAEL LTD for
both codes, so it can never split them.

Next: the pricing spec is at `00_docs\ISZE_Pricing_Spec_v1.md` (v1, 2026-08-05) with the engine at
`03_analytics\isze_pricing\`. Phase 2 (FX) and phase 3 (price playing) build on step 1.

## Air filter — handoff for the next agent (2026-09-17)

**Read `01_data\00_derived\HANDOFF_AIR_FILTER_AND_FOCUS_CUT.md` before touching air filter or the
Focus cut.** It is the working brief for the next agent and these are its fixed points.

- Use `aim_catalog_focus_filters.csv` on the **`catalog_full`** basis, not `pr00_catalog_only`.
  The literal restriction looks like 13% of in-scope euro and drops the air-filter leaf entirely,
  because `aim_source` is a precedence label for which vocabulary won `aim_l1`, not a completeness
  flag for the catalogue columns. `catalog_full` ties out to the shipped pricing comparison.
- The `ACL` → air-cleaner classification patch **landed** on 2026-09-17 at 19:50. The air-filter
  leaf is now **EUR 796,783.16 on 40 part numbers** for the 12 months to 2026-06-30, and **all 22
  in-scope markets bill air filtration** (smallest is Palestine at EUR 574).
- Two older claims are **withdrawn** — delete them if they reappear: that the leaf was "a network
  number in name only at EUR 28,469", and that some markets showed "real zeros". Both were side
  effects of the misfile.
- The catalogue tree and the AIM spine place the same 40 part numbers differently; do not put a
  catalogue-tree filter total beside an AIM-spine total without saying which is which.

## Open items (2026-09-17)

**Decisions waiting on Jerome are tracked separately** in `01_data\90_INBOX\DECISIONS_AWAITING_JEROME_2026-09-19.json` (readable `.md` twin in the same folder, read by the stop hook) — 20 open, 3 decided on 2026-09-19. The entries below are data-item gaps, not those decisions.

- **12 air-cleaner elements are misfiled on the AIM spine** — sitting in
  `Cleaning Chemicals > Cleaner` while their own descriptions read `FILTER; AIR CLEANER` or
  `ELEMENT; AIR CLEANER`. Worth **EUR 124,951.56** on the 12-month in-scope base (step EUR 674.42).
  Same class of error the `ACL` patch fixed on the catalogue tree, still live on AIM. **Recorded,
  deliberately not fixed** — the AIM workbook and the classifier are PRISM-owned, and moving 12
  part numbers would change the pack's families underneath the reader.
- **Country of origin is a separate, already-built field** (`country_of_origin`, more than 40
  countries) and was deliberately not used. A study that wants origin rather than supplying entity
  reads a different column and is a rebuild.
- **Dealer level cannot be built from this pricing file.** It carries the sold-to account only,
  25 of them, which is what the revision was run on. The billing data has no dealer key.

## PRISM parts base (2026-09-17) — closed

The "two published values" question is **answered, and it was not two numbers**.
`€103.57M` and `€112.09M` are the same method at two cut-off dates (2026-03-31 vs 2026-06-30);
the difference is the Apr–Jun 2026 billing wired in on 2026-08-25.

Chasing it exposed a **live leak**, now fixed: on 2026-09-03 the SAP sold-to map sent four
non-part entities to a code (`NON_PARTS`) that was never in `EXCLUDED_CODES`, so 9 CY2026 rows /
**€180,715.11** of service fees and demurrage entered the parts base. A recompute read
€112,270,022 against the published €112,089,307; after the fix it returns **€112,089,307.0 exactly**.

| Item | Path |
|------|------|
| Bridge + fix record | `FACTS.md` §4.1 · `DECISIONS.md` 2026-09-17 |
| Fix sites | `03_analytics\Isuzu\prism\modules\data_prep.py` (`EXCLUDED_CODES`) · `modules\sales_loader.py` (`NON_PART_LINE_KIND`) |
| Derived bridge keys | `scripts\build_metrics_snapshot.py` → `sales.parts_base_data_through`, `sales.parts_base_through_prior_quarter_eur` |
| Anchors | `prism\data\facts_anchor.yaml` (both cut-offs) |
| New open flag | `01_data\00_derived\_data_integrity_open_issues.md` → **CR/RE-FY26** |

Verify: **116 pass / 0 warn / 0 fail**; facts-drift **ALIGNED**. CY2025 untouched, so 51.1% never moved.

## Built (2026-09-16 workspace remediation)

Nine reports only, all on disk and unchanged: audit refresh, execution brief, security, Alps PR
land, mypens PR land, VC gaps C.1–C.2, Tier1 consolidation refresh, inventory. Index:
`docs\WORKSPACE_AUDIT_REFRESH_2026-09-16.md` · `docs\CONSOLIDATION_TIER1_REFRESH_2026-09-16.md` ·
`docs\WORKSPACE_INVENTORY.md`.

## Open / blocked

| Item | Status |
|------|--------|
| ISZE PRs | **All 8 merged** — see `docs\_wsA_ISZE_report.md`. Local dirty tree left uncommitted; both IDS stashes dropped |
| C.3 myPENS CI | **Done** — workflows on mypens `main` (`1476ccc`); see `docs\_wsC3_mypens_ci_report.md` |
| E truth audit | **Done** — `docs\TRUTH_AUDIT_2026-09-16.md` (4 confirmed disagreements; fig_key = date drift only) |
| Old GitHub PAT | Skipped per Jerome 2026-09-16, files left; residual local-disk risk only |
| Private health `.gitignore` | Proposal written in `_wsB`; awaiting confirm before use |
| cairn / pebble | Awaiting Jerome: version / park / reclaim |
| Tier1 delete 210 files (~222 MB) | **Done** — 210 deleted / 221.9 MB; sign-off log `docs\_tier1_delete_receipt.json` |
| Alps `.gitignore` `export_*.csv` | Done on disk, **not committed** |
| AIM spine misfile (12 air-cleaner elements) | **Open, recorded not fixed** — see Open items above |
| Retire orphaned UTI artifacts | **Still open, needs Jerome** |
| Roll out remaining 15 leakage packs | **Open** — and decide whether packs go to distributors (no mail sent) |

## CV warranty mileage validation (2026-09-16)

| Item | Path |
|------|------|
| Validation note | `01_data\90_INBOX\_cv_warranty_mileage_validation.md` |
| Derived table | `01_data\00_derived\warranty_cv_km_age_by_market.csv` |
| Fleet/age companion (parallel worker) | `01_data\90_INBOX\_market_fleet_profile_workup.md`, `_market_fleet_profile_design.md` |

**Headline:** the PRISM mileage assumption is confirmed for UTI (measured 51,680 vs assumed 50,000) and contradicted for ITUK (measured 16,688 vs assumed 50,000). The global `annual_km_yr: 20000` is structurally wrong — mileage tracks truck weight class (N35 12,165 / N75 35,217 / F-series 45,630), a 3.7× spread. Open question: whether ITUK's 50,000 or the UK warranty VIN sample is the wrong one. **Awaiting Jerome before any PRISM rebuild.**

## Built (aftersales KPI — 2026-09-16 evening)

| Item | Path |
|------|------|
| KPI questions board (15 live views) | `02_dashboards\sales\ISZE_PMS_Family_Compare.html` + `OPEN_ISZE_PMS_Family_Compare.cmd` |
| Graph lab (design only) | `02_dashboards\_design\kpi_graph_lab\OPEN_KPI_Graph_Lab.cmd` |
| Graph proposal | `01_data\90_INBOX\_kpi_graph_design_proposal.md` |
| **BPR 2.0 deck (40 slides, all charts in)** | `09_meetings\Business_Performance_Review_2026\ISZE_Business_Performance_Review_2026.pptx` + `OPEN_Business_Performance_Review.cmd` |
| BPR builders + charts | same folder — `build_numbers.py`, `build_kpi_numbers.py`, `build_core_charts.py`, `build_leakage_charts.py`, `build_aim_prism_ids_charts.py`, `build_ids_charts.py`, `build_bpr_deck.py` |
| BPR QA (geometry preview + structural) | same folder — `_qa_preview.py`, `_qa_deck.py`, `_qa\slides\` |
| Car park V19 vs V20 (both chapters) | `02_dashboards\fleet\ISZE_UIO_Car_Park_V19_V20.html` + `OPEN_ISZE_UIO_Car_Park_V19_V20.cmd` |
| **Distributor leakage cockpit (internal, 11 panels)** | `02_dashboards\sales\ISZE_Leakage_Cockpit.html` + `OPEN_ISZE_Leakage_Cockpit.cmd` |
| **Sales performance review packs (customer, 10 panels)** | `02_dashboards\sales\leakage_packs\ISZE_Sales_Performance_Review_{ITUK,SWEDEN,BELGIUM}.html` |
| **GPS/PMS truth + alignment reports (read-only)** | `00_docs\GPS_PMS_TRUTH_REPORT_20260917.md` · `00_docs\GPS_PMS_ALIGNMENT_20260917.md` |

## GPS / PMS alignment — GPS root cause FIXED, downstream rebuilt 2026-09-17

GPS re-split complete and **every page that derives from the ceiling rebuilt**. ITUK 32.4% →
**45.6%**, ITUK ceiling €17.18M → **€12.21M**, network anchor 51.1% → **55.7%** (wallet €60.22M →
€55.25M). Only ITUK moved; the other 17 markets are unchanged.

**Rebuilt on the corrected anchor:**
| Artifact | Shows now |
|---|---|
| `sales\ISZE_Exec_Aftersales_Paper.html` | 55.7% · €30.76M / €55.25M · 40% flat €250 |
| `ops\ISZE_OS_Console.html` | 55.7% cover · €55.25M ceiling · €24.54M uncaptured |
| `hub\ISZE_OS_Hub.html` | 55.67% cover · ceiling €55,253,312 |
| `_composable\dist\isze_cockpit.internal.html` | ceiling €12,212,051 |

Ceiling figures in the paper and console are now **derived at build time** from
`wallet_waterfall.csv` rather than typed literals — that was why they went stale within an hour of
the split. `SHIP_GATE_OK`; exec-paper gate PASS; hub guard OK.

**Two pre-existing breaks found while sweeping (not caused by the split):**
1. **RESOLVED 2026-09-17** — `02_dashboards\_composable\build.mjs` no longer reads the archived
   `gps_pure_sales_2026-08-13.csv`. The fallback now points at the live `_v2.csv` sibling. (The
   module already declared the correct file, so this was a landmine, not an active break.)
2. **RETIRED 2026-09-17 (Jerome decision)** — `md_pack\ISZE_MD_Pack_Capture_FY27_FY28.html` had no
   builder and showed the superseded 51.1% / €60.22M. Its three hub links and the `md_pack`
   manifest family were removed; hub rebuilt and `HUB_GUARD_OK`. The file itself is left on disk,
   unreferenced.

**Still open, needs Jerome:** retire the orphaned UTI artifacts.

**Resolved 2026-09-17 (Jerome decisions):**
- **Addressable 70 vs 100 — keep 100%.** The percentage scales modelled expected demand only
  (`pms_engine.py:333`), so at 70% every capture figure rises 43% (ITUK oil filter 65.9% → 94.2%).
  It does not touch GPS. Evidence argues for 100%: three ITUK families already exceed modelled
  demand (oil filter 116.4%, fuel filter 157.0%, brake rotor 197.7%) — the denominator is too
  small, not too big. The knob is `services_per_year` on wear parts, not the fleet share.
- **Clutch population — cannot be measured.** The VIN register carries `transmission` /
  `transmission_source` / `transmission_confidence` columns but every row is `unknown` / `none`:
  `build_vin_register.py` states Europe JAA VINs encode series/GVW/wheelbase/serial, not
  transmission, and refuses to invent AT/MT. Duncan's VIN list has no transmission column either.
  The 10,549 was 22,389 × 0.47, a convention, not a count. PRISM prices clutch on the full 23,068;
  publish clutch as an **upper bound** until a VIN decode or a market answer arrives.
- **GPS dashboard — already composition-based, not a flat rate.** Its €11.84M is DVLA vintage
  (22,389) priced by model mix: 10,900 N35 × €296 + 10,684 N75-class × €739 + 805 F × €887 =
  €11,835,911. Same method as the rebuilt ceiling; it differs only by fleet vintage and, for
  Ireland / Portugal / UTI, by a real composition difference (Ireland +€435K, Portugal −€442K,
  UTI −€756K, Germany +€396K). See `00_docs/GPS_PMS_ALIGNMENT_20260917.md` §6.

**Fixed alongside:** forked `gps_dashboard/modules/pms_engine.py` marked deprecated;
`capture_recovery_model.csv` no longer partial-year; `metrics_snapshot.json` provenance corrected;
`gps_master.csv` flat rate carries a quotation block; reconciliation prints PARTIAL not PASS when
hard checks are skipped.

## Prior built (unchanged)

| Item | Path |
|------|------|
| Exec aftersales paper | `02_dashboards\sales\ISZE_Exec_Aftersales_Paper.html` |
| Command Center | `02_dashboards\sales\ISZE_Aftermarket_BI_Command_Center.html` |
| Distributor leakage cockpit | `02_dashboards\sales\ISZE_Leakage_Cockpit.html` |
| Customer packs (3 pilot markets) | `02_dashboards\sales\leakage_packs\` |

## Distributor leakage tool (2026-09-16)

Internal cockpit + per-distributor customer packs from one shared data file; pilot packs for ITUK
(critical), SWEDEN (mid), BELGIUM (strong). Gates: `verify.py` 45 checks and `qa_leakage_tool.py`
44 rendered checks in real Chrome, both exit 0. The customer build strips other markets, dealer
names and internal registers, and fails if any other market code appears. All year comparisons
are like for like (same months each year plus an average month) — this corrected a headline that
read −58% where the true movement was +34.2%. Part numbers to act on are included per market.
Build chain: `02_dashboards\_build\leakage\` — `extract.py`, `build.mjs`, `verify.py`,
`qa_leakage_tool.py`.
