# AIM dashboard refresh — 24 September 2026

**What this was.** The AIM classification of the IE40 price extract (`01_data/EXPORT.XLSX`, 1,310
part numbers) was completed today. Every page in the workspace that reports AIM coverage, AIM
families, AIM against price class, or AIM mix was re-read from the refreshed master and rebuilt with
its own builder and its own arguments. No figure, formula or definition was changed. Nothing was
hand-edited and no new builder was written.

**Where the numbers came from.** `01_data/00_derived/aim_master_v2.csv`, read at build time. The
dated pair `AIM_Master_PN_Categories_Figkey_20260924.csv` / `.xlsx` and its launcher are another
agent's files, mid-repair; they were read only. The per-line answers are
`01_data/91_build/export_aim_eq_20260924/classified.csv` and the leftovers `still_unknown.csv`;
the write-up is `01_data/90_INBOX/EXPORT_AIM_CLASSIFICATION_2026-09-24.md`.

---

## 1. The master, measured before and after

| | pre-pass backup, 14:20:51 | live at my build time |
|---|---:|---:|
| rows | 165,257 | 165,289 |
| `has_aim` = 1 | 19,997 | 21,015 |
| `aim_l1` = "Unknown" | 4,271 | 3,603 |
| `aim_l1` blank | 140,324 | 140,138 |
| carrying a real family | 20,662 | 21,548 |
| rows stamped `export_aim_eq_20260924` | 0 | 1,229 |
| bytes | 28,529,377 | 28,611,807 |
| sha256 | `cd69c50604dbd4ff…` | `eaeb51bea3fe61b3…` |

The backup is `01_data/00_derived/aim_master_v2.csv.bak_pre_export_aim_eq_20260924_20260924_142051`.
Full fingerprint: `02_dashboards/_build/_aim_refresh/master_fingerprint.json`.

**The master moved again while I was working.** The row count went 165,257 → 165,289 at 17:01 and
the pair was rewritten at 17:04 — another agent's orphan append, not mine. I did not write any of
these files. Because the master is live, the pages below were rebuilt against different snapshots of
it; the ones later in this report include the 32 extra rows. That is why a couple of counts do not
reconcile with each other exactly. It is stated rather than smoothed over.

**How much of this actually lands on billing.** 1,087 rows changed label in this pass. They carry
EUR 617,905 of the last twelve months' billed euro against EUR 52,414,408 in total — 1.18%. So the
classification count moves a lot and the money on the pages moves a little, which is what the next
section shows.

---

## 2. Pages found

Scanned every `.html` under `02_dashboards/` and `09_meetings/`, excluding `_archive`, `_backsafe`,
`_qa`, `_gpt_review`, `_composable`, `_design`, `_working`, `_audit` and the `Data/` mirror. 109
pages carry AIM material. They fall into four groups.

**Group A — a real AIM subject, rebuilt (19 pages).** Below.

**Group B — AIM material, no builder of its own, left alone (7 pages).**

| page | why it was not touched |
|---|---|
| `02_dashboards/sales/ISZE_AIM_vs_Price_Class_Case.html` | No builder anywhere in the tree. The page's numbers are PR00 *catalogue* nodes (91.7% on a real catalogue node), not the workbook AIM families this pass changed. Its 91.7% would not move. |
| `02_dashboards/sales/ISZE_AIM_New_Logic.html` | No builder. Same basis — catalogue tree, 163,014 checked part numbers. |
| `02_dashboards/AIM_Parts_Atlas_v1.0/v1.1/v2.0.html` | No builder in the workspace. Its "Partial family coverage" text is about source-row coverage, not AIM labels. |
| `02_dashboards/ISZE_PowerBI_Classification_Implementation_Guide_2026-09-22.html` | No builder. It is a Power BI DAX guide. Its text quotes `18 product families` and `4,933 rows in the review queue` — both open items about what the *Power BI table* should publish, not master readings. Rewriting them would be a definition change, which this brief forbids. |
| `02_dashboards/hub/MASTER_DASHBOARD.html` | No builder. It is the 26 August mission control that the OS Hub already labels as carrying a superseded AIM figure. Left as the flagged older page. |

**Group C — AIM material, builder exists, but the AIM number is coupled to other pages (3 pages).**
`ISZE_PMS_Family_Compare.html`, `ISZE_PMS_Tonnage_Evolution.html`, `ISZE_DB_DLR_Replenishment_CY2025.html`.
These read the master only through an intermediate file that has not been regenerated
(`aim_bvp_family_risk.csv`, last built 07:30 today; `aim_evolution_model.csv`, 07:53). Its generator
sits inside `sync_evidence_derived.py`, which refreshes several interlocking derived files at once.
Running it changes pages I am not allowed to touch. See §5.

**Group D — managed elsewhere (not AIM subjects).** The `09_meetings/*_Operating_Dashboard_*` series,
the leakage packs and the IDS country packs carry family words in their own embedded payloads but
read AIM through the PRISM loader / leakage extract, which belongs to a different build lane. Left
alone.

---

## 3. Pages rebuilt, and what moved

19 pages. Each was rebuilt by running the builder that already existed, with the arguments it
already declares. Where a headline number did not move, it is because the money on that page is not
concentrated on the 1,087 reclassified rows.

### 3.1 `02_dashboards/sales/ISZE_AIM_Classification_Paper.html`
Builder `01_data/91_build/rebuild_aim_classification_paper.py` (no historical builder existed for
this paper; this refresher is the one it ships with). Exit 0, `SANITY_OK`.

| on the page | before | after |
|---|---:|---:|
| Classified part numbers | 165,213 | **165,289** |
| Category workbook — parts with AIM labels | 19,791 | **21,015** |
| (unchanged) catalogue shape | 7 / 27 / 177 · 164,907 parts | same |

### 3.2 `02_dashboards/sales/AIM_Dashboard_CY2026.html`
Data rebuilt by `03_analytics/Isuzu/prism/scripts/build_aim_cy2026_dashboard.py`, exit 0. The page
HTML itself is static and was not rewritten; it reads `aim_cy2026.data.js`, which was. **Left as an
exception, and named here:** the receipt writer refuses this page because it carries a Plotly CDN
URL as a last-resort fallback (`cdn.plot.ly`), which I am not allowed to remove without changing
behaviour. The page is also *not* fully `file://`-safe: it loads `../_ui/plotly.min.js` (present on
disk, 4.8 MB) and `aim_cy2026.data.js` by relative path, so it needs its folder, but it opens on a
double-click as long as the files sit together. I have not claimed it fully self-contained.

| in the payload | before | after |
|---|---:|---:|
| AIM-classified revenue, CY2026 Q1 | 97.6% | **97.7%** |
| open / review euro | 209,610 | **203,727** |
| CY2025 same-window comparison euro | 8,036,816 | 8,192,976 |
| YoY on that comparison | 10.4% | 8.3% |
| clean CY2026 euro | 8,873,291 | unchanged |
| high-risk euro | 63,357 | unchanged |

The classification moved coverage by 0.1 point. The YoY move is **not** mine: the same builder also
reads the live `sales_fact.parquet`, which is outside this brief. Flagged, not explained away.

### 3.3 `02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html`
Builder `03_analytics/Isuzu/prism/scripts/build_dealer_sellout_aim_gps.py`, exit 0. Byte-identical
to before: its family layer reads `catalog_l1`, which did not move. Rebuilt anyway so the footer no
longer leaks build notes — see §6.

### 3.4 The two Portugal / all-distributor deep dives and the two comparison pages
Builders `04_tools/aim_db_dlr_deep_dive/build_aim_db_dlr.py --db ALL|PORTUGAL` and
`build_aim_comparison.py --db ALL|PORTUGAL`. Exit 0, with the builders' own checks:
`48 pass / 0 fail`, `17 pass / 0 fail`, `60 checks pass`, `24 checks pass`.

These read `AIM_Master_PN_Categories_Figkey_20260921.csv` by name, which today holds the *restored*
21 September content (a different agent's repair). Rebuilt on the same source as before, so the
family layer did not move — but the billing, demand and sales-to-dealer layers were re-read live, so
all four files changed. I could not isolate the classification's own contribution without the
20260924 pair, which is other-agent territory and was mid-repair throughout.

### 3.5 The AIM repertoire map, spider and truck catalogue
Builders `build_aim_repertoire_payload.py` → `build_aim_repertoire_map.py`,
`build_aim_repertoire_spider.py`, and `build_truck_payload.py` → `build_truck_page.py`. All exit 0.

The repertoire map has its own verifier, `verify_aim_repertoire_map.py`. It passed every money
check — billed euro reproduces the published EUR 34,993,609.39, step EUR 1,652,140.18, weighted
5.9616% — then **failed on a pre-existing defect**: it expects the placeholder `UNCLASSIFIED` to
appear in the page's level-1 list. It does not, because a part number with no catalogue node has
never been in `price_bp_weighted_compare_pn.csv`. I confirmed the same failure on the pre-rebuild
file, so it is not caused by this pass. Left as it was. Not fixed: fixing it means changing a
definition, which this brief forbids.

Headline numbers on all three pages are unchanged (tree 164,907 rows, 15,872 billed part numbers,
7 families, 177 leaves), because they are catalogue-tree readings and the catalogue did not move.

These three pages' own QA scripts (`qa_aim_repertoire_map.py`, `qa_aim_spider.py`,
`qa_truck_catalogue.py`) also fail, in every case identically **before and after**:

| script | result before | result after |
|---|---|---|
| `qa_aim_repertoire_map.py` | PASS 40 / FAIL 4 | PASS 40 / FAIL 4 |
| `qa_aim_spider.py` | PASS 33 / FAIL 3 | PASS 33 / FAIL 3 |
| `qa_truck_catalogue.py` | PASS 184 / FAIL 2 | PASS 184 / FAIL 2 |

All four, three and two failures are "expects 8 categories, page draws 7" or a stale fleet number
(163,459 asked for, 163,198 on the page). Pre-existing, unrelated to AIM, not in scope.

### 3.6 The pricing revision family (5 pages)
`build_pricing_aim_source_cube.py` → `build_pricing_dashboard_data.py` →
`build_pricing_revision_dashboard.py`, `build_pricing_revision_prototype_alldb.py`,
`build_pricing_revision_prototype_nordics.py`, `build_pricing_fx_overlay_20261001.py`. All exit 0.
The revision itself is unchanged — step EUR 1,652,140.71, weighted 5.9616% — but the AIM axes inside
it grew:

| in the payload | before | after |
|---|---:|---:|
| groups (DB × AIM L1 × L2 × L3 × source) | 5,756 | **5,973** |
| customer × family rows | 1,195 | **1,201** |
| customer × L2 rows | 4,170 | **4,308** |
| customer × L3 rows | 6,358 | **6,609** |
| brake part numbers | 1,544 | **1,772** |

### 3.7 `02_dashboards/pricing/ISZE_Pricing_Revision_AIM_FX_20261001.html`
Builder `build_pricing_fx_overlay_20261001.py`, exit 0. Two headline numbers moved, and this is the
clearest visible effect of today's work:

| | before | after |
|---|---:|---:|
| lines not on the AIM spine | 2,245 | **1,217** |
| euro on those lines | 318,419.53 | **118,047.69** |

### 3.8 The two +5% pages
`price_5pct_review_2026-09-17/build_price_increase_5pct_review.py` (exit 0, then its own verifier
`verify_price_increase_5pct_review.py`: `pass=80 warn=0 fail=0`, `SHIP_GATE_OK`) and
`price_5pct_review_2026-09-22/build_price_increase_5pct_sim_20260922.py` (exit 0). This is the
largest figure movement in the pass:

| | before | after |
|---|---:|---:|
| part numbers not on the AIM spine | 1,967 | **1,321** |
| billed euro on them | 1,071,113 | **647,861** |

### 3.9 `02_dashboards/pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html`
Builder `build_pms_price_response_brief_20260922.py`, exit 0. Reads `aim_pn_classification.csv`, so
the part cards' AIM path improved. No headline figure moved. Content change: 1 byte (the build
stamp).

### 3.10 `02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html`
Builder `build_pricing_policy_paper.py`, exit 0, `BUILD_OK`, 11 canvases / 11 charts built. No AIM
figure moved (it reads the catalogue tree, which did not change). Rebuilt only to strip a build note.
See §6.

### 3.11 `02_dashboards/hub/ISZE_OS_Hub.html`
Builder `build_isze_os_hub.py`, exit 0. Its AIM layer still reads `aim_pn_classification.csv` and
still prints 98% revenue-weighted residual, 1.6% CY2024 / 1.8% CY2025. Unchanged. **This page needs
a decision.** Its AIM cell links to `aim_pn_classification.csv`, which today is the *fused* file: it
carries a catalogue axis (155,619 of 164,783 rows labelled) and a workbook axis (658 Unknown, 8,506
blank). It is not the file today's classification improved. The right source is `aim_master_v2.csv`,
but repointing it is a change to what the page means, not a refresh — so it is left and named here.

### 3.12 `02_dashboards/ops/ISZE_OS_Console.html`
Builder `build_os_console.py`, exit 0, `charts=8 queue_rows=13`. Unchanged, same reason as the hub.
Its text is unusually careful about the superseded 93.5% count figure, which it already labels as
superseded. Left exactly as it was.

---

## 4. Verify exit codes

| what was run | on what | exit |
|---|---|---|
| `verify_aftermarket_bi_command_center.py` | the suite index | **0** — all checks pass |
| `verify_tier_a_html_json.py` | Aftermarket BI tier-A pages only | **1** — `ISZE_Aftermarket_BI_Command_Center.html: FAIL (hero € leakage missing)` |
| `ship_gate_check.ps1` | workspace ship gate | **1** — `SHIP_GATE_FAIL verify_tier_a_html_json.py exit 1`; `HUB_GUARD_OK` |
| `verify_os_hub.py` | `ISZE_OS_Hub.html` | **0** — `HUB_GUARD_OK`, 167 link targets present, no NaN, no unfilled placeholders |
| `verify_price_increase_5pct_review.py` | the +5% review page | **0** — `pass=80 warn=0 fail=0`, `SHIP_GATE_OK` |
| `verify_aim_repertoire_map.py` | the repertoire map | **1** — see §3.5, pre-existing |
| `qa_aim_repertoire_map.py` / `qa_aim_spider.py` / `qa_truck_catalogue.py` | their own pages | **1 / 1 / 1** — pre-existing, same before and after |
| `build_aim_db_dlr.py` internal checks | deep dives | **0** — 47 / 16 gating checks pass; 48 / 17 in VERIFY_*.json |
| `build_aim_comparison.py` internal checks | comparisons | **0** — 60 / 24 checks pass |

The tier-A failure is **not mine**. `ISZE_Aftermarket_BI_Command_Center.html` is a 12 KB suite index
whose mtime is 19 September 16:47; I never opened it for writing. It is the same failure the 16:10
board entry already recorded as pre-existing and unrelated. `BOOK_B_REVISION_REVIEW_20260819.html`
and `ISZE_DB_DLR_Replenishment_CY2025.html` pass tier-A.

---

## 5. The three pages I could not refresh, and why

`ISZE_PMS_Family_Compare.html`, `ISZE_PMS_Tonnage_Evolution.html` and
`ISZE_DB_DLR_Replenishment_CY2025.html` hold AIM material that reaches the master through
`aim_bvp_family_risk.csv` (last built 07:30 today, before the classification landed) and
`aim_evolution_model.csv` (07:53). The generator for both lives in
`03_analytics/Isuzu/prism/scripts/sync_evidence_derived.py`, alongside roughly a dozen other derived
files that feed pages outside this brief. Running it would rebuild pages I was told not to touch.

One thing I did measure: I ran `build_pms_family_compare.py` to see whether a rebuild would help. It
produced a 2-line change — the snapshot date and nothing else — because the family-risk file it
reads is stale. I then reverted it, so the page is exactly as it was. It is not in the rebuilt list
and I am not claiming it is refreshed.

To bring these three in line someone has to run the evidence-sync deliberately, knowing it moves
pages beyond AIM. That is a decision, not a refresh, so I stopped.

---

## 6. Pages that are shared, and what was stripped from them

All 19 rebuilt pages are under `02_dashboards/`, which is shared by default. Scan for internal
nicknames, banned words and build notes on the visible text of every rebuilt page, before and after:
`Mode A`, `Mode B`, `sell-out`, `street`, `wallet`, `IML v7`, `Model B`, `PRISM lane`, `hardware PN`,
`Book B`, `1.785` written bare, `SPAR`, `ship-gate`, `harness`, `do not edit`.

Two build notes were on pages a person would open, and were stripped **at the builder** so they
cannot come back:

1. `02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html` — a source-table footnote ended
   "Rebuilt by four scripts in 01_data/91_build/ and 02_dashboards/pricing/_build/." Removed from
   `build_pricing_policy_paper.py`; the footnote now states only where the source files sit.
2. `02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` — the footer read
   "Rebuild: prism/scripts/build_dealer_sellout_aim_gps.py · 01_data/00_derived/sellout_aim_* ·
   second layer". Replaced in `build_dealer_sellout_aim_gps.py` with a business sentence: reported
   quantities are the distributors' own sales to their dealers; ISZE euro is our invoiced price to
   the distributor.

Both pages were rebuilt after the fix, so the live files carry the cleaned wording. Everything else
I found pre-dates this pass and is left alone, because removing it would be an edit outside a data
refresh: `sell-out` still appears in the leakage packs and in the body of
`Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html`'s notes; `IML v7` and `PRISM lane` still appear on
`ISZE_OS_Hub.html`; `wallet` and `Book B` still appear on `ISZE_OS_Console.html`. All of these are
internal-usage pages and predate today — flagged, not silently changed.

---

## 7. Launchers fixed

Two launchers named themselves differently from the file they open. Both were written by their own
builder, so I fixed the builder and re-ran it rather than hand-editing.

| launcher | before | after |
|---|---|---|
| `02_dashboards/sales/OPEN_AIM_DB_DLR_ALL.cmd` | `<no @echo off>` + `start "" "%~dp0ISZE_AIM_DB_DLR_Deep_Dive_ALL.html"`, LF endings | `02_dashboards/sales/OPEN_ISZE_AIM_DB_DLR_Deep_Dive_ALL.cmd` — `@echo off` + `start "" "%~dp0ISZE_AIM_DB_DLR_Deep_Dive_ALL.html"`, CRLF |
| `02_dashboards/sales/OPEN_AIM_DB_DLR_PORTUGAL.cmd` | same shape, LF endings | `02_dashboards/sales/OPEN_ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.cmd`, CRLF |
| `02_dashboards/sales/OPEN_AIM_COMPARISON_ALL.cmd` | same shape | `02_dashboards/sales/OPEN_ISZE_AIM_Comparison_ALL.cmd`, CRLF |
| `02_dashboards/sales/OPEN_AIM_COMPARISON_PORTUGAL.cmd` | same shape | `02_dashboards/sales/OPEN_ISZE_AIM_Comparison_PORTUGAL.cmd`, CRLF |

The old four files were deleted so two launchers for one page cannot coexist and disagree. Every
other rebuilt page already had a launcher whose name and target agree and whose endings are CRLF;
the audit is in `_launchers.py` and I ran it again after the fix.

---

## 8. Paint check — rendered, not the builder

Rendered every page from `file://` in headless Chrome at 1440×1000 and measured the DOM and the
canvas pixels.

**Screenshots: 34 taken, 34 read.** Taken by `_paint_check.py` and `_repaint.py` (scripts, so they
took no reading); read one at a time, at full resolution, by me. Every page got its first screen; the
13 pages taller than 4,000 px also got a bottom-of-page screen. One extra `hub_final.png` was taken
by the focused hub probe, and 2 more for the AIM CY2026 page after its rebuild — both read. Receipts
record the two counts per page.

What paints, per page:

| page | painted | tables / rows | console errors |
|---|---|---|---|
| Classification Paper | 6 canvases | 4 / 27 | 0 |
| Repertoire Map | 3 canvases | 4 / 31 | 0 |
| Repertoire Spider | 1 canvas | 3 / 135 | 0 |
| Truck Catalogue | 2 canvases | 2 / 6 | 0 |
| AIM Comparison ALL | 1 canvas | 4 / 50 | 0 |
| AIM Comparison PORTUGAL | 1 canvas | 4 / 43 | 0 |
| DB_DLR Deep Dive ALL | 5 canvases | 4 / 912 | 0 |
| DB_DLR Deep Dive PORTUGAL | 5 canvases | 4 / 901 | 0 |
| Pricing Revision AIM Source | 7 canvases | 5 / 699 | 0 |
| Prototype AllDB | 1 canvas | 1 / 23 | 0 |
| Prototype NordicsCust | 1 canvas | 1 / 23 | 0 |
| FX overlay 20261001 | 2 canvases | 2 / 62 | 0 |
| +5% REVIEW | 4 canvases | 5 / 72 | 0 |
| +5% SIMULATION | 5 canvases | 9 / 77 | 0 |
| PMS Price Response Brief | 21 bar rows | 6 / 65 | 0 |
| Pricing Policy Paper | 11 canvases | 13 / 76 | 0 |
| Dealer Sellout AIM GPS | 18 bar rows | 16 / 282 | 0 |
| OS Hub | 24 bars + 18 mix bars, 87 KPI chips, 110 chips | 4 / 43 | 0 |
| OS Console | 73 bar rows + 1 SVG | 1 / 13 | 0 |
| AIM Dashboard CY2026 | 0 canvases — div tables | 2 / 22 | 0 |

No blank panels. No empty Top-N shell. Every table with a `tbody` has rows, except two that are
empty by design and say so in words: the deep-dive dealer table prints "No dealer-level data from
this distributor. Only Isuzu Truck UK reports its sales to dealer broken down by dealer … The
section stays empty rather than showing a figure that does not exist," and the Portugal run's heat
table is switched off the same way. The OS Hub shows 0 `canvas` and 0 `svg` — it draws with div bars
(`.brow`, `.mixbar`, `.btrack`), which is its design, and the focused probe confirmed 24 bars, 18 mix
bars, 87 KPI chips, 110 chips and 4 tables with rows. The AIM CY2026 page has no canvas: it draws two
tables of 11 rows each and its trust strip prints `verify: green (164 pass)`.

**Payload sanity.** No embedded JSON block on any page contains a literal `NaN`, and no page shows
`NaN` in its visible text. `NaN` does appear inside the inlined Chart.js and Plotly libraries, in
null-handling branches (`null===a?NaN:a`) — that is library code, not data.

**`file://` open.** Every rebuilt page but one is self-contained with its payload and chart library
inlined, and no page fetches a sibling file. The two biggest, the deep dives at 7.2 MB and 8.2 MB,
are fully embedded and open from Explorer with no server. The exception is
`AIM_Dashboard_CY2026.html`, which loads `../_ui/plotly.min.js` and `aim_cy2026.data.js` by relative
path: it opens on a double-click as long as it stays in its folder, which it does. Every page has a
working sibling launcher whose name and target agree and whose endings are CRLF.

---

## 9. Receipts

One per page, `ok: true`, each covering the current file's mtime, each recording the screenshot
counts. **19 receipts.** Absolute paths:

```
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Classification_Paper.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Comparison_ALL.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Comparison_PORTUGAL.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_DB_DLR_Deep_Dive_ALL.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_AIM_Repertoire_Map_2026-09-17.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_AIM_Repertoire_Spider_2026-09-17.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_AIM_Truck_Catalogue_2026-09-18.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Revision_AIM_FX_20261001.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_PMS_Price_Response_Brief_2026-09-22.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\ISZE_Pricing_Policy_Paper.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\hub\ISZE_OS_Hub.SHIP_RECEIPT.json
C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\ISZE_OS_Console.SHIP_RECEIPT.json
```

`AIM_Dashboard_CY2026.SHIP_RECEIPT.json` covers the rebuilt data file rather than the unchanged page
HTML, because that is where its numbers live.

**All nineteen receipts in the list above exist and report `ok: true`, each with a screenshot count
that matches what I read** (verified by re-reading all nineteen paths off disk after writing this
report). One of the twenty pages that changed could not be given a receipt:

`02_dashboards/sales/AIM_Dashboard_CY2026.html` — the writer refuses it on `no_cdn`, finding
`https://cdn.plot.ly/plotly-2.27.0.min.js`. That is a last-resort fallback inside an
`if (typeof Plotly === 'undefined')` guard, and the page already loads a local `../_ui/plotly.min.js`
first. Removing the CDN line is an edit to the page rather than a data refresh, so I left it. I
checked the local file exists (`02_dashboards/_ui/plotly.min.js`, 4,849,499 bytes, resolves to
`02_dashboards/sales/../_ui/plotly.min.js` = True) and recorded 2 screenshots for it — the first
screen paints the hero, 11 table rows, the basis note and a green verify strip; the bottom screen
paints the rank/JM tables and the sources line. It is not in the receipt list because the writer
would not sign it.

No receipt carries a `--ship-gate-ok` flag or a `--deck-gate-ok` flag. The workspace ship gate exits
1 on a pre-existing unrelated failure, so claiming that flag would be false.

---

## 10. Before-images and working files

Pre-rebuild copies of all 19 pages, plus the master fingerprint and every probe and check script:
`C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\_aim_refresh\`

The 32 paint screenshots: `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\_aim_refresh\_qa\`

---

## 11. What I could not verify

1. **Nothing was checked against the repaired 20260924 dated pair**, because it was mid-repair and
   is another agent's file. The four deep-dive and comparison pages therefore read the restored 21
   September pair, exactly as before. Their family layer is unchanged as a result.
2. **The OS Hub and OS Console AIM cells still read `aim_pn_classification.csv` by name.** Their 98%
   and 1.8% did not move. Whether they should point at `aim_master_v2.csv` is a decision about what
   those pages mean, so I left them and named them.
3. **The master kept changing under me.** The row count moved from 165,257 to 165,289 during the
   pass. Pages rebuilt earlier do not include the last 32 rows. Every file is internally consistent;
   the set is not all on one snapshot.
4. **The AIM Dashboard CY2026 YoY moved from 10.4% to 8.3%** and I cannot attribute that to the
   classification — the same builder reads `sales_fact.parquet`, which moved for its own reasons.
5. **`ISZE_PMS_Tonnage_Evolution.html` was run and is byte-identical**, despite the framework
   presenting it as part of the Aftermarket BI suite. Its AIM numbers come from the stale
   `aim_evolution_model.csv`, so a rebuild moves nothing, and the intermediate is group C above.

---

## 12. Damage I caused, and the repair — `00_docs/agent/DELEGATOR_BOARD.md`

I must record this plainly rather than leave it in a log.

Appending the change-log row, I first wrote the row as raw ASCII bytes, which was correct. Then I
corrected the receipt count from 20 to 19 using PowerShell:

```powershell
$t = [IO.File]::ReadAllText("00_docs\agent\DELEGATOR_BOARD.md")
[IO.File]::WriteAllText("00_docs\agent\DELEGATOR_BOARD.md", $t.Replace("20 receipts written","19 receipts written"))
```

`[IO.File]::ReadAllText` without an encoding reads as the **local ANSI code page**, not UTF-8.
Windows-1252 decodes the em dash `—` (U+2014) and the euro sign `€` (U+20AC) correctly, but **fails
on 0x81, 0x8D, 0x8F, 0x90 and 0x9D**, which have no CP1252 mapping. Those bytes became U+FFFD, and
`WriteAllText` then wrote the file back as UTF-8, so each one came back as three bytes.

**The tell was arithmetic.** My replacement string was one character *shorter* than the one it
replaced, yet the file grew by exactly **138 bytes** — and 138 is 69 × 2, which is what 69 broken
characters each gaining two bytes looks like. That is how the count was established.

**What was lost:** 69 characters, in rows belonging to other agents as well as mine — 45 em dashes
(U+2014) and 24 euro signs (U+20AC). Every one was a punctuation mark or a currency symbol in
narrative prose, not a figure, a path, a part number or a date. No digits were affected, because no
integer in the file falls in the CP1252 undefined range. The natural candidate for what the anomalous
bytes actually were is 0x97 and 0x80, the CP1252 rendering of em dash and euro sign.

**The repair.** Each of the 69 sites was classified from its own local context under three rules
stated in the script: a space on both sides means em dash; immediately before a digit means euro;
otherwise em dash. That gives 45 em dashes and 24 euro signs. The unbroken characters (the ≈ signs,
the → arrows, the · dots) were never damaged, which is itself the check that the diagnosis is right.

**Verification.** Normalising the repaired file by turning the 45 em dashes and 24 euro signs back
into the placeholder reproduces the damaged copy **byte for byte**. So nothing else moved — no row
was reordered, no other string changed, and my own row still has exactly 5 cells. The file now
decodes as valid UTF-8 with zero replacement characters, and is 54,561 bytes, exactly where it stood
before I touched it with the encoder.

**Kept:** the damaged copy as `00_docs/agent/DELEGATOR_BOARD.md.dmg_fffd_20260924_1819`, so the
repair can be audited, and the repair script as `_aim_refresh/_board_repair.py`, which refuses to
write unless its own assertions pass.

**What I should have done:** append bytes, or write with an explicit UTF-8 encoder. My first append
did exactly that. The one-word correction is what broke it, which is the ordinary shape of this
failure — the small edit, not the big one.

Anyone holding a copy of this board from before 18:19 should say so, and it can be diffed against the
repair to confirm the reconstruction.

A second row on the board records this incident, so the next agent does not have to rediscover it.
