# Gap assessment — the ten-file HTML base against the tested brief

**Written:** 2026-09-19 (local, UTC+2), read-only pass. No HTML, JSON, CSV or workbook was edited, moved, renamed or deleted.
**Subject (frozen working base):** `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\`
**Briefs compared:** the first brief (`...\ISZE_Ten_File_Review_and_Fix_Brief_2026-09-19.md`) and the tested brief (`...\ISZE_Ten_File_Review_and_Fix_Brief_TESTED_2026-09-19.md`), which governs where they conflict.
**Superseded and used for comparison only:** `2026-09-19_next10_fixed\`, `2026-09-19_next10_STAGED_NOT_LIVE\`.

**Method.** Every finding below was checked by reading the file bytes in the base folder with a script (UTF-8, errors replaced) and grepping line numbers; numbers were recomputed in Python from the embedded payloads and from `01_data\90_INBOX\PPT_GPT_commercial_pack_2026-09-19\` (README read first). Marker `VISIBLE` means the hit is outside `<script>`/`<style>`. Nothing was rendered in a browser by me; anything that needs a render is marked **UNVERIFIED-AT-SOURCE**.

---

## 1. Per-file findings: status and evidence locator

Paths are relative to the base folder unless stated. "L" = line number in the file as read.

### F01 `01_ISZE_Exec_Aftersales_Paper.html` (814 lines)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| Restricted network service-demand euro aggregate absent from visible text | ADDRESSED | No `18.22` / `18,22` anywhere (0 hits). VISIBLE: L126 "the network basket total is not shown because it mixes flagged and unflagged cells"; L250 "The network basket total is not shown… not quotable outside"; sources row L715 "(category cells, quotability-flagged; network total not quoted)". The old €8.39M-of-€18.22M construction is gone. |
| The word "quotable" is gone | PARTLY | Base folder: 1 visible hit — L250 "…so it is not quotable outside." It now denies quotability rather than claims it. Collateral hit: 252 hits in F02, all `"quotable_eur": 0/1` JSON flags. The superseded `_next10_fixed` copy had 4 prose hits, including the old title "The quotable gap is clutch and brake" — that title is gone. |
| ITUK gap €6.65M in visible text | ADDRESSED | L205 `<div class="bar-row">…ITUK…€6.65M below target`. |
| ITUK €6.65M in fallback bars | ADDRESSED | L205 is the fallback `bar-row`; width 100% is the group maximum, consistent with €6.65M leading the group (IUK 87.4%, UTI 74.3%). |
| ITUK €6.65M in the embedded chart array | ADDRESSED | L780–782 `bar('cBelowCeiling', ['ITUK','IUK','UTI','PT','UMI','DE','HU','NO'], [6.65,5.81,4.94,1.34,1.32,1.27,0.60,0.57], …)`. |
| No €11.6M residue | ADDRESSED | 0 hits for `11.6` / `11,6` in the whole file. |
| ITUK €6.65M in the source table | PARTLY | The sources table (L711–729) has no row for the ITUK shortfall. Its nearest row is L714 "55.7% · €30.76M / €55.25M · 40% flat €250". The 6.65M therefore appears with no source-table lineage row. |
| Cover headline is a decision statement | ADDRESSED | L112 `<h1>Prioritise evidenced brake and clutch opportunities by distributor</h1>`. |
| Data-verification dates separated from HTML testing | PARTLY | L709 says the 143/0/0 record "covers the underlying data, not this HTML; the HTML test result for this corrected copy is recorded in the same block below" — but the block below (L731–736) prints a **stale data stamp**: "Pass 116 · fail 0 · generated 2026-08-25T17:19:54Z". No HTML test result or its date appears anywhere in the file. 15 of 16 `footer.pf` elements carry "data verification 143/0/0 · 2026-09-18 20:22 UTC" (footers L189–746). |
| **New defect found (not in either brief)** | STILL PRESENT | L364 visible raw template placeholder: `<td class="n">{ITUK_PCT:.1f}%</td>` in the distributor league table, between Ireland 124.2% and Belgium 86.0%. Byte-identical placeholder exists in `_next10_fixed\01_…html` L364, so it pre-dates this correction pass. |

### F02 `02_ISZE_Leakage_Cockpit.html` (60,708 lines)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| `ceiling_2030_eur` present in embedded JSON (18) | STILL PRESENT (dead payload) | 18 occurrences, each inside a `"forward": {"year": 2030, "ceiling_2030_eur": …, "vs_2024_pct": …, "cum_ceiling_eur": …, "modelled": true}` block. First at L2362–2368 (L2364 = 21,036,884.87). |
| Can any code path render, tooltip or export it? | Determined: no | `.forward` → 0 hits; `["forward"]` / `['forward']` → 0 hits; `ceiling_2030` appears only as the JSON key itself. The one consumer found is `payload.modules.gps.ceiling` (L59473), which reads the **separate** `ceiling` object at L17221–17240 (`ceiling_total_eur: 55253312`), not the forward block. Export paths: `download` 0, `export` 0, `csv` 0, `blob` 0, `JSON.stringify` 0, `window.print` 0. Conclusion: dead payload, unreachable from the page's render, tooltip and export paths. |
| Contradiction created by leaving it in | STILL PRESENT | The basis strip says "Historical trucks in service only — no forward fleet or ceiling shown" (L309), and the meta prose list still includes "the revenue bridge and forward ceiling model" (L726, `source_methods`, never rendered). The visible claim and the payload disagree. |
| Substitution reframed as a model classification | ADDRESSED | "Residual classified as substitution by the model": 1 dictionary entry (L791) + 81 data labels = 82 occurrences; each `gap_types` label carries it (e.g. L46148). "Bought another brand instead": 0 hits. |
| Causal caveat required beside the finding | PARTLY | The label itself is the caveat. I found no separate visible sentence along the lines of "not evidence that a customer bought a competing brand" (searched "not evidence", "competing brand", "classification of a residual": 0 hits each). |
| Duplicate-ID finding real or artefact | PARTLY — real in the rendered DOM, invisible in markup | Markup scan excluding `<script>`/`<style>`: 24 ids, 24 unique, 0 duplicates (same result for all ten files). But `selectControl()` (L626–635) emits `id="sel-${moduleId}-${key}"`, and it is called **inside `block(r)`**, the per-market render function: `selectControl("pms","family",…)` at L59743 inside `block` (defined L59621, returned per market at L59788/L59793) and `selectControl("actions","view",…)` at L60290 inside `block` (L60279/L60300). With N markets selected the DOM therefore holds N identical `id="sel-pms-family"` and N `id="sel-actions-view"`. Default is now one market (L60656–60662, "One market by default rather than every market's full report stacked together… Show all N markets"), so the default view has no duplicates and the earlier tester's 18 counts match an all-markets view. |
| Selection scope explicit | PARTLY | State is deliberately per module, not per market: `SEL.state[moduleId][key]` (L60600–60605, `state: (id,key)=>…` L60586). Changing one service-family control therefore redraws every selected market's panel to the same family — what the tester measured as "changing the second control changed seven market controls". The code comments the panel-level redraw, not the cross-market scope. |
| Benchmark specified | ADDRESSED | L312–316: same customer type, unlabelled median, historical fleet and modelled ceiling, not a published benchmark, no other distributor named, no median below three comparable markets (`peerMin` L705). |
| Default to one market with a defined comparison | ADDRESSED | L60656–60662; "Show all 23 markets" button L60639. |
| Six-markets wording | STILL PRESENT | VISIBLE basis strip L309 "Coverage … sales-to-dealer files, six markets only"; amber banner L59990 "…exists for six markets only". |

### F03 `03_Warranty_Commercial_Review.html` (497 lines)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| Section 4 renamed | ADDRESSED | L105 `<h2 id="sec4">4 – Position against the stated age and mileage limits</h2>`; "who actually pays" 0 hits. |
| Section 7 renamed | ADDRESSED | L158 `<h2 id="sec7">7 – Cost position by operation, against the stated limits</h2>`. |
| Payer inference removed | PARTLY | Prose is corrected: L106–110 "That is a **position against the limits**. It is not a statement of who paid…"; L161 "The files record position, not the payer." But the payer is still named in section 7's own outputs: table `t4` column header L445 `{h:'Who pays', v:r=>r.who_pays}`, and doughnut `c9` (L168, L421–429) sums `DATA.who_pays` by category. The payload retains `who_pays` values "Isuzu — fails well inside warranty" (15), "boundary — price-list and campaign question" (7), "distributor — outside warranty, aftermarket demand" (2) — i.e. the file still classifies funders and charts them. |
| Both claim windows as explicit dates | ADDRESSED | L117 basis strip: "D-Max 1 Apr 2025 – 31 Mar 2026 · trucks 1 Dec 2023 – 31 Mar 2026 (periods differ)". The old prose ranges ("April 2025", "December 2023") no longer appear (0 hits). |
| Annualisation not smuggled in | ADDRESSED | L219–221 "Periods do not match and are not annualised… No annualised figure is substituted for a matched-period comparison, because that would add a fresh assumption." Only other "normalis" hits are currency normalisation (L62, L198). |
| Claimed / admitted / reimbursed distinct | ADDRESSED | L182 heading "Parts claimed versus admitted, by market"; L212–215 "Claimed, admitted and reimbursed are three numbers… None is inferred from another"; recon payload distinguishes them (L233 `'LCV (D-Max) parts claimed EUR' 3548780.40` vs `parts admitted EUR 4303476.20`). |
| Currency correction traceable, superseded figures named | ADDRESSED | L202–208: corrected turnover €4,655,881 with emissions €2,838,570 (61%); pre-2026-09-18 figures €2,826,045 / €1,819,033 / €800,191 explicitly marked "predates that correction and is not valid. Do not add any two of these." |
| Entity rules | ADDRESSED | L222–224 UTI/ITUK/IUK/UMI kept separate. |
| Open contradiction | STILL PRESENT | L117 Audience = "Shared / external — after review", while the base's own `COMPLETION_REPORT.md` open item 1 records that warranty euro quotability for a shared version is unresolved. A shared label is printed while the decision that governs it is open. |

### F04 `04_ISZE_AIM_Classification_Paper.html` (1,456 lines)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| One identifiable current functional classification definition | ADDRESSED | L1131 `<h3>The current definition — one place, one version</h3>`; L1139 Functional hierarchy "**In force** … Axis A identity only"; L1141 "Approved version / date — **Two axes locked 17 September 2026**"; L1134 "Anything earlier in this paper that describes a commercial-posture parent is a description of a superseded design, not the structure in force." |
| Completeness, source agreement, adjudicated correctness separated | ADDRESSED | L1146 "Three measures that are not the same, and are not called accuracy"; L1150–1152 the three rows, each with a "what it does not tell you" column. |
| Never called "accuracy" | ADDRESSED | Only 2 hits for "accuracy", both in the block that refuses the word (L1146 "and are not called accuracy"; L1156 "It is never called accuracy"). |
| Historical error ledger (version, window, corrected, regenerated) | ADDRESSED | L1165–1166 rows carry tested version, 2024–2025 window, corrected yes/no, and whether dependents were regenerated (e.g. L1166 "Other / review" residual: "**No** — suggested classifications exist and have not been reviewed or applied"). |
| Named residuals | ADDRESSED | L1142 "~9.5k part numbers / ~€1.75M" and "object-vs-system 2,272 part numbers / €247k". |
| Fleet denominator consistency | STILL PRESENT (contradiction) | L691 network total 163,459 vs F01's 163,198 (five hits, L106/114/125/250/609). See §Cross-file. |
| Basis strip nine fields | PARTLY | L350 carries Period, Population, Measure, Valuation, Fleet, Coverage, Data status, Audience — 8 fields, no separate HTML-tests field. |

### F05 `05_ISZE_AIM_vs_Price_Class_Case.html` (645 lines)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| Posture→Family→Type proposition replaced | ADDRESSED | L288 exact sentence: "**Price classes construct the list; functional families organise the business.**" |
| Posture language removed elsewhere | PARTLY | L337 "Granularity: posture → family → type."; L355 `<span class="chip">L1 Posture · 7 values</span>`; L332 tree node "Commercial attribute". The new proposition sits beside the old structural vocabulary rather than replacing it. |
| L1 labelled an assigned commercial attribute, not measured exposure | ADDRESSED | L396 "L1 groups the book by an **assigned commercial attribute** — a modelling choice about how exposed a line is to the independent aftermarket, not a measurement of it." |
| Evidence must carry market and date | ADDRESSED | L396 callout plus L399 basis note on the in-scope pricing base. |
| One audience designation | ADDRESSED | L281 "ISZE internal – classification case"; L604 lists limits, one audience. |
| Coverage figures reconciled | PARTLY | Two different catalogue-coverage percentages remain with no reconciling sentence: 91.7% "On a real catalogue node" (L303) / "Real catalogue node" (L557) and 90.6% "of billed euro sits on a governed catalogue node" (L399). No "coverage" label, no denominator shared. |
| Air-filter blind spot not turned into a commercial finding | ADDRESSED | L390 "Air filter · €28k (thin)"; L492 "Air · Thin — anecdote only"; L604 "thin air filter" listed as a kept-visible limit; L479 bar drawn at 5% with €28k. |

### F06 `06_ISZE_Pricing_Policy_Paper_REV3.html` (1,326 lines)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| Cap breach presented as a release blocker | ADDRESSED | L536 `<h2>…section five — Release blocker: the system does not enforce its own ceiling</h2>`; L539 "**This scenario cannot be released as it stands.**"; L540–541 "4,903 of 17,230 priced lines (28.5%), the highest single line being 14.35%"; L242 tooltip states the same; L1014 in the verification table. |
| Two named paths | ADDRESSED | L569 "The cap question is a decision, and it has two legitimate answers"; L570 "Respect the cap" (scale every tier, or hard clamp and re-normalise); L574 "Revise the cap". L581–584 adds "What is not defensible: **Shipping the current state without saying so.**" |
| Observed benchmark coverage separated from model-assigned 53.8% | ADDRESSED | L161–166 tooltip: "the share of the book the **model assigns** … not a count of lines where a competing price was actually observed: only 880 lines carrying €5,369,216 - 16.5% of the priced book by euro, 1.8% of the 47,617 priced lines"; L174–177 repeats it; L163 "The two populations are different and must not be compared as if one confirmed the other." |
| Captive no longer inferred from a missing quote | ADDRESSED | L564–566 "**Captive here means the model found no alternative on record for that line** — an unobserved case. It is not a measured finding that no alternative exists."; L725 launch book "no billing history is an unobserved case". |
| Tier vs market reconciliation printed | ADDRESSED | L408–409 "The tier movements sum to 960,637 euro; the four markets normalise to 960,503. The difference is the per-market normalisation, not a disagreement." |
| **Recompute — tier gains** | CONFIRMED | Payload `tiers.gain` = `[-18663.86, 570990.01, 61282.62, 13906.24, 274178.40, 58944.30]`; sum = **960,637.71**. |
| **Recompute — market gains** | CONFIRMED | Payload `dial.p5` = `[588726.90, 181144.75, 127446.98, 63183.95]`; sum = **960,502.58**; `dial.totals[1]` = 960,502.58. |
| **Recompute — difference** | CONFIRMED | 960,637.71 − 960,502.58 = **€135.13**, exactly as reported in the brief. |
| Audience single designation | ADDRESSED | L143 kicker "internal / private · not for circulation"; L201 "internal / private · not a shared version"; L1088 same. No "shared" label remains. |
| Basis strip | PARTLY | L137 has only 3 fields (Observed, Modelled, Fleet); no Period, Population, Valuation, Coverage, Data status or Audience fields. |

### F07 `07_ISZE_Pricing_Revision_AIM_Source.html` (1,551 lines)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| Headline = total change over prior-price value of the same eligible quantities | ADDRESSED | L124 "It is the **total change in base price at the quantities billed, divided by the prior-price value of those same eligible quantities** — the sum of each eligible line's price change multiplied by the quantity billed on it, over the sum of the prior base price times the same quantities. It is **not an unweighted mean of per-line percentages**…" ("unweighted" 1 hit, in that denial). |
| Two populations never mixed | ADDRESSED | L124 second paragraph "**Two populations, never mixed.** Parts billed covers every in-scope line; the weighted percentage covers only lines priced on both sides of the revision."; KPI tooltip L929–934. |
| Historical FX rate stated | ADDRESSED | Payload `"fx": 163.7`; L926 "valued at 163.7 JPY per EUR. That is the historical rate carried by the filed revision, not a current corporate rate."; L1534 same in the footer. 23 occurrences of 163.7. |
| **FX rate date stated** | STILL PRESENT (omission) | No date for the 163.7 rate anywhere: 0 hits for "rate date", "as of", "as-of", "rate applied". The only dated item is the build date, `D.generated` = `2026-09-18T16:26:52Z`, rendered as "Built 2026-09-18" (L1526–1528). |
| **Revision date stated** | STILL PRESENT (omission) | The basis strip says "revision filed as dated on the page" (L109), and the footer says "revision filed as dated on the page" is not repeated — the page prints no filed-revision date. 0 hits for "revision date". The acceptance criterion "the rate date and revision date are explicit" therefore fails. |
| Unknown supply source an explicit category | ADDRESSED | L940–945 "Share of in-scope parts billed euro where the supplying entity … is recorded. The rest … is an explicit **UNKNOWN SUPPLY SOURCE** category: it is kept in every total and reported as its own share of the billed base, never merged into either Japan or Thailand."; basis strip L109 Coverage field repeats it. |
| Functional hierarchy preserved | ADDRESSED | No classification change made; family selectors intact (L178). |
| Audience | ADDRESSED | L109 basis strip "Audience: Internal / private". |

Note on a literal that looks like a ceiling but is not: `55.253` (3 hits) is a line-level price/quantity cell (`…, 1259.79, 789.4, 844.65, 55.2535`), not the €55.253M ceiling. `60.22` in this file (19 hits) is a price cell ("… 932.71, 825.61, 885.84, 60.226, 932.71"), not a ceiling. Same for `60.22` in F09 (€260.22 clutch-kit price) and in `Data\dashboards\isze_data.preload.js`. The "four ceilings" claim is dealt with in §Cross-file.

### F08 `08_ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html` (321 lines)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| "lands as money" gone | ADDRESSED | 0 hits for "lands as money"; the two "lands" hits are section headings (L163 "Where the +5% lands, by part family", L168 "…by distributor"). |
| "collectable" gone from visible text | PARTLY | L244 retains the row label "In-scope L12M revision base, collectable (movable lines)" in the second-reading table (1 hit for "collectable", 1 for "Collectable"). |
| Headline renamed | ADDRESSED | L71 `<div class="lab">Modelled price step on eligible lines at unchanged quantities</div>` with tooltip L75–78 "…a modelled price step, not cash that has been collected or is guaranteed to be." Banner L67 "Nothing in this page changes a price." |
| Base and formula stated | ADDRESSED | L127–135 "The eligible step is **5.000% of the current base price on each eligible line, multiplied by the quantity billed on that same line over 2025-07-01 to 2026-06-30**, then summed. It is therefore a price step on historical net billed volume: it is not a current-list value, and it is not a net margin or a realised profit." |
| Rebate / transport / lubricant out of the actionable ranking | ADDRESSED | New table L212–223 "Excluded from the actionable ranking" holds `0000REBATE` (€430,030), `0TRANSPORT` (€351,222), `0550047337` Rim R4L15W40 (€394,763); L226–234 "Largest part numbers by +5% euro" is headed "Part numbers only… Administrative and lubricant lines are excluded and shown separately above." |
| …including in the chart data, not only the table | ADDRESSED (recomputed) | Embedded `const P` (L274): `P.top.labels` = `['7552348290','8978808250','8983767550','8983528481','8978808270','8982447940','8975359391','8982878080','8974995480','8975554500','8982705240','7552348280']` — none of the three excluded codes. Nor in `P.l1.labels` or `P.db.labels`. The three codes appear once each in the file, all inside the exclusion table. |
| Eligible-line definition consistent between headline and detail | ADDRESSED | L71–74 headline €1,629,793 on 47,617 lines "93.15% of billed"; L80–85 all-lines €1,749,680 on 48,653 lines, tooltip "whole-base arithmetic and is a separate sensitivity, not the headline". |
| Missing price is a data gap, not proof of no action | ADDRESSED | L117–119 residual €2,397,757 explicitly "not the CY2025 no-list figure of €4.96M, which is a different window and is not used anywhere on this page"; reason table L120–124 splits `no_price_on_one_side` (1,010 lines/€1,110,782) from `rebate_or_non_part_admin` (19 lines/€781,252). |
| Audience | PARTLY | L60 "Internal" badge plus "Review and design - not a price change"; no basis-strip Audience field (L56 carries Scenario/Observed/Modelled/Fleet only). |

### F09 `09_ISZE_Competitiveness_Dashboard.html` (1,689 lines)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| Dead Class C tables deleted, not annotated | ADDRESSED | The repeated €2.34 / 0% table is gone. "2.34" now appears twice only: L478 "<strong>The Autodoc Class C table has been removed from this page.</strong> The scrape is frozen… it returned a minimum of €2.34 against major assemblies and 0% ratios, which are not usable observations." and L1053 the scraper-tab warning. Comparison: the superseded `_next10_fixed` copy carries 76 hits for "2.34" and 5 hits for "Class C" (the three dead tables); the base carries 2 and 3. |
| No such row reaches a median, score, heatmap or export | ADDRESSED | L478 "Those rows are excluded from every median, score, heatmap, ranking and export on this page. The figures are kept out of the decision path entirely rather than shown with a warning beside them." Keyword check: `download` 0, `csv` 0, `blob` 0, `median` 1 (that sentence), no data table contains a €2.34 row. |
| All six local asset references resolve FROM THE BASE FOLDER (it has its own `_ui`) | ADDRESSED — all six resolve | `_ui/chart.umd.min.js` (200,807 B), `_ui/editorial.css`, `_ui/editorial-full.css`, `_ui/editorial-charts.js`, `_ui/isze-shell.js` (5 files in the base's own `_ui`), and `Data/dashboards/isze_data.preload.js` (44,046 B) — all present in the base folder. |
| The nine cross-navigation links | NOT REPRODUCED in the base folder (expected) | `../hub/index.html`, `../hub/MASTER_DASHBOARD.html`, `AIM_Dashboard_CY2026.html`, `ISZE_Competitiveness_Dashboard.html`, `ISZE_Monthly_Sales_Tracker.html`, `../fleet/ITUK_ZEV_Golden_Window_Dashboard.html`, `../fleet/ISUZU_UIO_Dashboard_2026.html`, `../fleet/ISZE_FY2026_YearEnd_Review.html`, `../ops/ISZE_Tender_Monitor_v2.html` — all 9 absent from the flat base folder, all 9 present at the live path `02_dashboards\sales\` (verified by `Test-Path` on all eight distinct targets). This is a folder-placement effect, not a base defect. |
| "live" removed from a frozen extract | ADDRESSED | L377 tab text "Scraper intel — extract 9 May 2026". The remaining 11 "live" hits describe scrape searches ("live search results", "no live DE search") or the high-confidence definition, not a freshness claim. Quote date shown: "Autodoc UK scraped 9 May 2026, GBP × 1.17" (L483). |
| Price-index direction stated | ADDRESSED | L450 "Price chain: list price → distributor (+40%) → dealer (+27.5%) = ×1.785 to the reference dealer price"; L347 basis strip "Reference dealer price = list × 1.40 × 1.275 (price index = shop ÷ reference)". |
| Internal initials / file names in reader-facing labels | PARTLY | L370 header sub-text and L481 "Data sources" still name `IE40`, `PR00`, `ABC code`, `EQ-HIT`, and the repo path fragment `04_tools/autodoc_scraper` (L370). |
| The plotly claim in an earlier report | Documentation error | This file references `_ui/chart.umd.min.js` and contains 0 hits for "plotly" / "Plotly" — it uses Chart.js. `_ui/editorial-charts.js` does contain a `patchPlotly()` function, but it is a palette patcher that returns immediately when `window.Plotly` is undefined, and it also patches Chart.js. The claim that this file references plotly should be struck wherever it appears. |

### F10 `10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` (80 lines, no `<script>`)

| Finding (brief) | Status | Evidence locator |
|---|---|---|
| Metric labels/tooltips now a proxy-value share | ADDRESSED | KPI L59 value 92.3%, label "UTI value-parts share of **proxy value** (CV trucks)", tooltip "Best Value Parts proxy euro as a share of value-parts plus contested-original proxy euro, on CY2025 sales-to-dealer quantities valued at the median ISZE-to-distributor unit price. **A proxy-euro share, not a quantity share or service-demand cover.**" IUK KPI L59 also "proxy value (LCV pickups)". Table L68 column 8 "Value-parts share of proxy value (BVP + contested)". |
| Conflicting "quantity share" wording removed | STILL PRESENT (contradiction) | L58 callout: "…it is **value-parts quantity divided by value-parts plus contested-original quantity** within the selected assortment." That is the tested brief's rejected definition, and it sits directly above the KPI that denies being a quantity share. |
| The word "capture" gone | ADDRESSED | 0 hits for "capture" / "Capture" in the file (the old contested_bvp_capture field is not used in the page). |
| "Best Value Parts" spelled out on first use | PARTLY | The phrase appears at L59 (KPI tooltip) and L58, but no sentence explains what value-parts are; the legend below (L62) switches to "BVP". A reader meets the term with no gloss. |
| No number changed / 92.3% reproduces | ADDRESSED and CONFIRMED | Recomputed from the supplied source: `01_data\90_INBOX\PPT_GPT_commercial_pack_2026-09-19\02_sales_to_dealer\dealer_sellout_aim_mix_2025.csv` (README read first; it warns filenames may say "sellout" — speak "sales to dealer"), entity "UTI (network aggregate)", layer `sellout_db_dlr`, year 2025: `bvp_eur` 288,740.135, `genuine_contested_eur` 23,921.33 → 288,740.135 / 312,661.465 = **0.9234912751 → 92.349%**, i.e. 92.3%. The file's own `contested_bvp_capture` = 0.9234912751400304. The tested brief's conclusion is correct: the leading figure is a proxy-euro share, `bvp_eur / (bvp_eur + genuine_contested_eur)`, not a quantity share. |
| Portugal's status | ADDRESSED | L58 "Portugal is included as **provisional** coverage where the long file exists; it is not part of the controlled five-distributor dealer-level set." Basis strip L56 "Sales to dealer exists for 6 markets; controlled dealer-level coverage is 5 distributors". |
| ITUK companion kept non-additive | ADDRESSED (scope stated, aggregation basis not) | L67 "Duncan 4 Sep 2026 is a network companion on a different scope and date (Customer Name=All, through Aug 2026) and is **not additive** with the dealer files"; table L68 row "ITUK Duncan network companion (All dealers, PN–month thru Aug)" shows 224,587 qty against the CY2025 dealer row's 224,001. The row does not state whether its values are CY2025-filtered or include later months; "through Aug 2026" is the only scope hint. |
| Source basis and coverage note | ADDRESSED | L56 covers Period/Population/Measure/Valuation/Fleet/Coverage/Data status/Audience/Sales-to-dealer; basis strip Data status "Extract generated 2026-09-15; data verification 143/0/0 on 2026-09-18". |

---

## 2. What a correct fix changes, per file

"Wording" = reader-facing text only. "Data label" = text bound to a payload value or rendered control. "Logic" = a code path or number.

| File | Remaining fix | Type |
|---|---|---|
| F01 | Fill or remove the `{ITUK_PCT:.1f}` placeholder at L364; replace or delete the stale "Pass 116 · 2026-08-25" stamp at L733 so the sources page actually carries the HTML test record it promises; add an ITUK-shortfall line to the sources table; decide whether the word "quotable" stays in the refusal sentence. | Data label (placeholder, stamp) + wording |
| F02 | Delete the 18 `forward` blocks (a data rebuild of the embedded payload) or accept them as dead; add the missing visible caveat that a substitution cell is the model's classification and not evidence of a lost customer; make the per-module selection scope explicit in the UI, or give each market its own control ids. | Logic (payload, render state) + wording |
| F03 | Remove the `Who pays` column and the `c9` doughnut, or relabel them as a model classification with the unobserved-case caveat attached; settle the shared/external label once warranty euro quotability is decided. | Logic (fields, chart) + wording |
| F04 | Add the source note for 163,459 so it cannot read as F01's 163,198 with a different value; add the missing HTML-tests field to the basis strip. | Data label + wording |
| F05 | Remove or subordinate the three Posture references (L337, L355, L332); give the 91.7% and 90.6% one reconciling sentence with their denominators. | Wording + data label |
| F06 | Extend the basis strip to the full field set. Cap path is a decision, not an edit. | Wording |
| F07 | Print the FX rate date and the filed-revision date; both are currently missing. | Data label + wording |
| F08 | Replace the word "collectable" in the L244 row label with the modelled-step wording used in the headline; add the Audience field. | Wording |
| F09 | Remove internal codes and the repo path fragment from reader-facing source notes if the file is shared. Everything else checked out. | Wording |
| F10 | Reconcile L58 with L59/L68 (one definition, not two); gloss "Best Value Parts" on first use; state the companion's aggregation window. | Wording |

Nothing above was done. This is a read-only assessment.

---

## 3. Decisions needed from Jerome, not edits

1. **F06 cap path.** Enforce the +8% per-line ceiling after normalisation and rounding, or record an explicit approved change. The paper now discloses the breach as a release blocker with exactly these two options and does not choose. 4,903 of 17,230 priced lines are above the ceiling, worst 14.35%.
2. **Portugal's dealer-level source status.** Is Portugal a qualifying dealer-level source, or provisional-only? The base says both, in different files (F01 "six distributors including Portugal = 60.0%" vs F10 "controlled dealer-level coverage is 5 distributors; Portugal provisional"). The pack's own README supports the narrow reading: named dealer quantity exists for **ITUK 2025 only — 64 dealers**.
3. **Warranty euro quotability.** Does the warranty parts-euro total carry the same internal-only restriction as the network service-demand aggregate? Until decided, F03 should not be labelled shared.
4. **Promotion of the corrected base onto live.** `FROZEN_BASE.md` §3 records that zero of the ten live files equal the base, and nine live files equal the earlier `_next10_fixed` copy. Overwriting live is a publish decision.
5. **F02 dead payload.** Leave the 18 forward/2030 blocks in place as unreachable, or rebuild the payload to remove them? Removing them is a data rebuild, not a wording change.
6. **F07 date pair.** Supply the FX rate date and the filed-revision date so the acceptance criterion can be met; they are not derivable from what is on the page.
7. **F03 payer table and doughnut.** Keep the model's payer classification (relabelled) or drop it? The brief asked for no inferred payer, and the section heading was renamed, but the table column and chart still name funders.
8. **F01 league-table placeholder.** `{ITUK_PCT:.1f}` is visible raw text; either supply the value or delete the cell.
9. **Which verification count is current.** The HTMLs stamp 143 pass / 0 warn / 0 fail (2026-09-18 20:22 UTC); the live report on disk today reads 153 pass / 1 warn / 0 fail (2026-09-19 13:00 UTC) and `metrics_snapshot.json` still carries `verify.pass = 116`. Confirm which is the quotable record before any pack is shared.
10. **F04 fleet label.** Confirm that 163,459 (18 markets with a count, AIM catalogue base) and 163,198 (GPS target-spend base) may both be called "trucks in service 2025", or require the qualifying words.

---

## 4. Blocked items and the exact missing evidence

The tested brief states that claim/currency sources, classification masters, line-level pricing proposals, competitor match evidence and the authority files "were also absent as standalone files". I checked that last claim directly. **Three of the authority files exist on this machine at the standard paths:**

| File | Locator | Content read |
|---|---|---|
| `_verification_report.json` | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_verification_report.json` | `generated_at` 2026-09-19T13:00:24Z; `summary` pass 153 / warn 1 / fail 0, `ok: true`; 154 checks; the single non-pass is `uio_year.historical_gaps` (warn): "DENMARK 2012", "DENMARK 2013" unfilled. A second copy of the same run sits in the pack at `01_data\90_INBOX\PPT_GPT_commercial_pack_2026-09-19\10_calc_support\`. A stale third copy sits at `02_dashboards\Data\00_derived\` with 108 pass, generated 2026-08-18. |
| `metrics_snapshot.json` | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\metrics_snapshot.json` | `as_of` 2026-09-17T13:47:43Z; 55 metrics; includes `waterfall.network.wallet_eur_2025` = 55,253,312, `captured_eur_2025` = 30,756,772, `gps_pct_2025` = 55.7, `sales_fact.rows` = 514,037, `ituk.oil_filter.uio_units` = 23,068 — **and a stale tail block `verify.pass = 116`, `verify.generated = 2026-09-17T05:47:43Z`.** |
| `FACTS.md` | `C:\Users\jerom\Desktop\claude\ISZE\FACTS.md` (21,387 bytes) | Exists; also mirrored at `08_gpt\environment_review_2026-09-19\D_spine\FACTS.md`. |

So the correct statement is: **the three authority files exist; the 143-count record the HTMLs cite does not match the current report on disk (153/1/0), and no file on disk carries a 143-pass record at the same timestamp the HTMLs print.** The HTMLs' 143/0/0 stamp is unverified against a live source file.

Still genuinely missing (no file found in the searched trees):

- **Claim-level and currency sources for F03** — the warranty review's own footer names `01_data/00_derived/warranty_commercial/` and `01_data/06_Warranty/*.xlsx`; reconciliation to those was not possible in this read-only pass beyond the figures already printed inside the file.
- **Classification masters and reviewed labels for F04/F05** — the approved two-axis definition is described in F04; no master file was located under the searched paths to confirm the 17 Sep 2026 lock.
- **Line-level pricing proposals and competitor match evidence for F06/F09** — F06's 880-line benchmark set and F09's scraped comparison rows are only available as aggregates inside the HTMLs.
- **`sales_to_dealer_long_PORTUGAL_CY2025.csv`** — referenced in the base's `FIX_LOG.md` as existing; not present in the commercial pack's `02_sales_to_dealer\` listing (which holds 14 files, none named that). Portugal's qualification cannot be settled from the pack alone.
- **Browser-render evidence** — thrown exceptions, canvas painting, narrow-screen width, keyboard focus. **UNVERIFIED-AT-SOURCE**: I did not render any file. The earlier tester could not open `file://` and used `set_content`, so its F09 "six assets absent / controls throw" verdict was taken from a different delivery context than the base folder, where all six assets resolve.

---

## 5. Where the briefs themselves are wrong or overstated

1. **Tested brief, authority files.** "The authority files `_verification_report.json`, `metrics_snapshot.json` and `FACTS.md` were also absent as standalone files." False on this machine — all three exist at the standard paths and were read (§4). The usable finding behind it survives: the *current* report says 153/1/0, not the 143/0/0 the HTMLs print, and `metrics_snapshot.json` itself still says 116.
2. **Tested brief, F09 dependencies.** "The supplied file references six local assets absent from the supplied directory." True for that standalone test directory, not for the corrected base, which carries its own `_ui` copy and a `Data\dashboards\` copy; all six resolve there. Reporting this against the base would be wrong.
3. **Tested brief, F09 rendering.** "Segment, market and comparison-mode clicks produced null-data exceptions… Opening the scraper view produced `Chart is not defined`." Not verifiable here and contaminated by the environment limit the brief itself records (no `file://`). It should stay marked as environment-dependent, not as an established defect of the file.
4. **First brief, F02 duplicate IDs.** "The default rendered page contained 18 controls with ID `sel-pms-family`." The default is now one market and the markup has no duplicates; the duplicates appear only when more than one market is rendered, from `selectControl()` being emitted inside the per-market `block()`. The brief's instruction to "generate unique IDs" is right in substance; the diagnosis "default rendered page" is not accurate for the corrected base.
5. **First brief, F01 page length.** "Reduce the main management narrative to roughly six pages." Not reproduced as a defect; not assessed here (design preference, not a measurable failure).
6. **Tested brief, F10 metric.** The conclusion is right and I reproduced it (92.3491%). The brief's instruction to rename "if that is the retained measure" was implemented as a new label, but did not require deleting the old explanatory sentence in L58 — which is why the file now states both. That is a gap in the brief's instruction, not in the tester's finding.
7. **Completion report in the base.** It says the HTML test result "is recorded in the same block below" on F01's sources page. There is no HTML test result in that block; the block contains a data stamp dated 2026-08-25 using the superseded 116-count. The statement overstates what the page shows.
8. **Completion report, "15 footers".** Matches measurement: 16 `footer.pf` elements, 15 carrying the 143/0/0 stamp (the 16th is the cover's "shared · English · printable A4" line).

---

## 6. Cross-file contradictions — reproduced or not

Searched the base HTMLs for the literal forms (`63.9M`, `60.22M`, `55.25M`, `55.253M`, `163,459`, `163,198`, `54.4%`, `60.0%`, `75.1%`, `55.7%`) and recomputed from source where possible.

| Claimed contradiction | Reproduced? | Evidence |
|---|---|---|
| **Four ceilings: €63.9M / €60.22M / €55.25M / €55.253M** | NOT REPRODUCED (as four live figures) | €63.9M: 0 literal hits in the base HTMLs. The only near value is `"cum_ceiling_eur": 63836250` (L2687) inside F02's dead forward payload for one distributor. €60.22M: 0 hits as a ceiling; the `60.22` hits in F07/F09 and in `Data\dashboards\isze_data.preload.js` are a part price (€260.22 clutch kit) and a line-level price cell. €55.25M: 6 hits, all F01 (L114/119/198/201/610/714) — the same number as the source. €55.253M: 0 hits in the base HTMLs (3 hits in F07 are a price cell 55.2535). Effective single ceiling: `01_data\...\wallet_waterfall.csv` CY2025 `theoretical_wallet_eur` sums to **55,253,312** (I summed all 18 CY2025 rows), and F02's `ceiling.ceiling_total_eur` = 55,253,312. |
| **Two vehicle counts: 163,459 vs 163,198** | REPRODUCES | F01 uses 163,198 in 5 places (L106, 114, 125, 250, 609); F04 uses 163,459 once, as the network total of a market table (L691), summing only the rows that have a count. I recomputed: `wallet_waterfall.csv` CY2025 `uio_units` sums to **163,198.0**; `01_data\00_derived\aim_catalog_other_filter_meta.json` `network_uio_2025_18_markets` = **163459.0** (also in `aim_catalog_breakdown_NOTES.md`: "The network fleet total is 163,459 trucks across the 18 markets that have a count"). Different collections, identical label, no qualifying note in F04. |
| **Two capture rates** | PARTLY — different measures, not the same number twice | F01's 55.7% is billed ÷ modelled ceiling (30.76/55.25); F04's 0.370 is units ÷ truck; F02 publishes per-market `metric_capture_pct` (e.g. 68.66, 27.08, 39.9) and a 45.6% ITUK GPS rate that matches F01's 45.6%. F03's target-spend table uses its own `target_wallet_eur` values (UTI 8,271,300; ITUK 12,212,051) and recomputes warranty as a share of it (L435–436) — those values equal F02's ceilings, so no arithmetic clash there. |
| **Two sales-to-dealer visibility figures** | REPRODUCES | F01: "Sales-to-dealer files exist for ITUK, IUK, Ireland, UTI, Greece and Portugal = **60.0% of GPS billed euro** (€18.45M of €30.76M)" (L504) and "Six DBs including Portugal = 60.0%" (L577). F10: "Sales to dealer exists for 6 markets; **controlled dealer-level coverage is 5 distributors**" (L56) and "Portugal … is not part of the controlled five-distributor dealer-level set" (L58). Pack README: named dealer quantity "ITUK 2025 only — 64 dealers". |
| **Inconsistent forward-fleet treatment** | PARTLY | Visible text is consistent: F01 "no forward forecast"; F05 "Historical fleet only – no forward forecast quoted"; F06 "Historical only; no forward forecast as a price basis"; F08 and F10 the same. F02's basis strip says "no forward fleet or ceiling shown", yet its payload still carries 18 year-2030 ceiling blocks and its meta list still names "the revenue bridge and forward ceiling model". Visible claim consistent; payload inconsistent. |
| **Israel UTI vs UMI** | NOT REPRODUCED as a fault | F01 L182 "Israel is two distributors — UTI and UMI — always two rows"; F01 L337 keeps ITUK/UTI/UMI/IUK on separate rows; F04 L694 "UTI and UMI are two separate Israel distributors with different fleets and are never blended"; F01 rows carry separate UTI and UMI figures (UTI 40.3% vs UMI 71.6% in F02's payload). No blended "Israel" figure found in the base. |

---

## 7. The two brief findings that reportedly do not reproduce

1. **Duplicate generated element IDs — PARTLY reproduced, and the method matters.**
   *Method:* stripped `<script>…</script>`, `<style>…</style>` and HTML comments from each file, then regex-scanned `id="…"` and counted duplicates. Result: F01 27 ids (27 unique), F02 24 (24), F03 25 (25), F04 16 (16), F05 10 (10), F06 14 (14), F07 33 (33), F08 4 (4), F09 49 (49), F10 0. **Zero duplicates in the static markup of all ten files**, which confirms the base's own claim for the markup.
   *But:* the ids are generated at runtime inside a per-market loop. `selectControl(moduleId, key, …)` (L626–635) emits `id="sel-${moduleId}-${key}"`, and both call sites sit inside `block(r)`, the function rendered once per selected market: `selectControl("pms","family",…)` at L59743, `selectControl("actions","view",…)` at L60290. With more than one market selected, the DOM therefore contains duplicate ids — the effect the earlier tester measured. With the new one-market default, the default view has none. So: not a markup defect, real in the rendered all-markets view.
2. **Excessive all-market page length — NOT REPRODUCED as a defect.**
   *Method:* the base's own docs record the measurement (F02 default desktop document 231,667px in the tested state; 18,377px with ITUK alone) and the corrective action; I verified the corrective action in code (L60656–60662 sets `SEL.dbs = [largest market]` with the comment "One market by default rather than every market's full report stacked together"). I did not render, so the pixel height of the corrected default is **UNVERIFIED-AT-SOURCE**. As a page-length defect it is a design observation, not a code failure, and the "Show all N markets" escape is one click (L60639, L60673).

---

## 8. Confirmation the report file exists

The file exists on disk. Verified by a directory listing of the containing folder, not by the write tool's own success message.

- **Path:** `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\GAP_ASSESSMENT_vs_TESTED_BRIEF_2026-09-19.md`
- **Byte size on disk: 45,707 bytes** (203 lines), verified by `Get-Item` and by a folder listing of `02_dashboards\sales\_gpt_review\`, both run after this section was written. Last write 19/09/2026 19:05:36.
- **Folder:** written inside `02_dashboards\sales\_gpt_review\`, the only folder this pass was allowed to write to. The listing of files changed since 18:30 in that folder shows this report and nothing else. No live file under `02_dashboards\sales\` or `02_dashboards\pricing\`, no staging folder, and no `08_gpt\` content was created, edited, moved, renamed or deleted.
