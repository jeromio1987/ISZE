# Ten-file review and fix — completion report

**Date:** 2026-09-19
**Brief:** `C:\Users\jerom\Desktop\claude\ISZE_Ten_File_Review_and_Fix_Brief_2026-09-19.md`
**Corrected pack:** `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected`
**Originals preserved at:** `...\_gpt_review\2026-09-19_next10_fixed` (untouched)

Nothing was copied onto a live `02_dashboards\` path. No price was changed, nothing was published, nothing was mailed.

---

## 1. What was done, file by file

### F01 Executive Aftersales Paper — P0
- **Removed the restricted network service-demand aggregate everywhere it appeared** (cover thesis, cover stat, page 4 verdict, SWOT verdict, SWOT component cell, SWOT residual cell, closing callout, sources table). It is replaced by unit-free category evidence with the fleet denominator: clutch disc €3.14M, brake pad €2.78M, brake shoe €2.47M on 163,198 trucks in service. The chart titles and the bars keep the category euro, which is permitted; only the network basket total is gone.
- **Fixed the stale ITUK shortfall.** Page 3 said "ITUK €11.6M below target", which is the pre-correction ceiling arithmetic (17.18 − 5.56). Corrected to €6.65M, and the whole bar group rescaled to that maximum (IUK 87.4%, UTI 74.3%, PT/UMI/DE ≈ 20%, HU 9.1%, NO 8.6%) so the widths are honest rather than merely relabelled. The embedded chart array was changed from 11.61 to 6.65 in the same edit, so printed and screen values agree.
- **Cover headline replaced** with a decision-oriented statement: "Prioritise evidenced brake and clutch opportunities by distributor".
- **Verification separated.** Fifteen page footers and the sources page no longer assert the old 116-check HTML-era stamp as if it described this document. They now read as a dated data verification (143 pass / 0 warn / 0 fail, 2026-09-18 20:22 UTC) with an explicit note that the HTML was not part of that run.
- **Tender "live" label removed** — page 10, the table of contents, the chart title, the section heading and the sources row now say "snapshot as of 2026-09-15 04:20:49".
- Basis strip rebuilt to the nine standard fields. Internal file names removed from the sources table.

### F02 Opportunity Cockpit — P0
- **Removed the fleet-forecast output.** The per-market render block that printed `forward.ceiling_2030_eur` is deleted from the code path, so no 2030 ceiling reaches visible text, a tooltip, a chart or an export. A short note explains that the fleet projection is not usable and that only the historical fleet and the ceiling built on it are shown.
- **Causal claim replaced.** The substitution label "Bought another brand instead" is now "Residual classified as substitution by the model" in all 82 JSON occurrences and in the label dictionary, with a banner stating that a substitution cell is the model's classification of a residual, not evidence that a customer bought a competing brand.
- **Benchmark specified** — same customer type, unlabelled median, historical fleet and modelled ceiling, not a published benchmark, no other distributor named, and no median at all below three comparable markets. The "own brand / another brand" layer legend was renamed, because in this payload those tokens mean value tier versus original parts.
- **Default selection reduced to one market** (largest by billed euro), with "Show all 23 markets" as the one-click escape. This addresses the stated preference for one selected distributor plus an optional defined comparison rather than every market's report stacked together.
- Basis strip rebuilt; footer carries the current dated data verification.

### F03 Warranty Commercial Review — P0
- **Payer inference removed.** Section 4 renamed "Position against the stated age and mileage limits"; section 7 renamed "Cost position by operation, against the stated limits", and the heading "Truck repair operations grouped by who actually pays" is gone. The prose now says plainly that the files record position, not the payer, and names what would be needed to classify a payer (market and model terms, extensions, campaigns, claim decision record).
- **Periods aligned and separated.** The header prints both windows as explicit dates instead of prose ranges.
- **Caveats expanded** with the specific points the brief requires: the corrected currency position (€4.655M turnover, €2.838M emissions at 61%, and that the pre-2026-09-18 truck figures of €2,826,045 / €1,819,033 / €800,191 are superseded); position versus payment; claimed versus admitted versus reimbursed kept apart; cost per claim versus per claiming vehicle versus per vehicle in service; no annualisation substituted for a matched comparison; UTI / ITUK / IUK / UMI kept distinct.
- Warranty-specific basis strip — the period fields carry the claim windows, not the general billing cut-off, and the fleet field is explicitly absent rather than filled with an irrelevant number.

### F04 AIM Classification Paper — P1
- **Current definition added** as a single block: functional hierarchy in force, commercial attributes separate and not yet built, approved version and date, named residuals. Any earlier description of a commercial-posture parent is now identifiable as superseded.
- **Three measures separated** — completeness, source agreement, adjudicated correctness — with a statement that none of them may be called accuracy and that count-weighted and euro-weighted agreement are reported separately.
- **Historical error ledger added**: for each error family, the tested version, the evidence window, whether it was corrected, and whether dependent outputs were regenerated.
- Basis strip rebuilt; the fleet field is marked not applicable rather than left blank.

### F05 Classification versus Price Class — P0
- **The functional hierarchy was preserved, not demoted.** The central proposition is now "Price classes construct the list; functional families organise the business", and the level-1 layer is labelled as an assigned commercial attribute rather than measured exposure, on the hero, the KPI row and the three-level callout.
- The callout now states that where exposure is claimed it must carry its market, date and match quality, and that the family name alone proves nothing.
- Comparison-period, fleet-denominator and classification-version notes added to the evidence window.
- One audience designation: the pack is internal / private, and a customer version is described as a separate future document.

### F06 Pricing Policy REV3 — P0
- **Audience resolved to one designation.** The cover kicker, cover footer and closing line all now say internal / private, not for circulation. The contradictory shared / external label is gone.
- **Cap breach treated as a release blocker**, with a new panel stating that the scenario cannot be released as it stands, that 4,903 of 17,230 priced lines (28.5%, worst 14.35%) sit above the +8% ceiling in the final line calculation, and that there are exactly two paths — enforce the ceiling after normalisation and rounding, or record an explicit approved change. The paper does not choose silently.
- **Observed evidence separated from model-assigned exposure.** The commercial-tier tooltip now states that the 53.8% is a model assignment and that only 880 lines carrying €5,369,216 have an actual benchmark — 16.5% of the priced book, 1.8% of the lines — and that the two populations must not be compared as if one confirmed the other.
- **Captive status is no longer inferred from a missing quote.** The launch book now says that no billing history is an unobserved case, that no observed benchmark is not the same as captive, and that status is UNKNOWN; the cap-breach table adds that "captive" there means the model found no alternative on record.

### F07 Pricing Revision by Distributor, Family and Source — P1
- **The functional hierarchy was preserved.** No change to its classification; only corrections were made.
- **Headline defined precisely** as total base-price change at billed quantities divided by the prior-price value of the same eligible quantities, explicitly not an unweighted mean of percentages, with the two populations (all billed lines versus priced-on-both-sides) stated as never mixed.
- **Unknown supply source made an explicit named category**, kept in every total and reported as its own share of the billed base rather than merged into Japan or Thailand.
- **FX basis labelled as historical** in both places it appears, with a note that a scenario re-based to a newer rate is a different calculation and would be labelled separately. Basis strip rebuilt.

### F08 Flat Price Increase Review — P0
- **Cash certainty removed.** "Collectable once lines with no move available are excluded" became "Modelled price step on eligible lines at unchanged quantities"; the "figure that lands as money" wording is gone from the KPI tooltip and the closing list, replaced by an explicit statement that quantities are unchanged, no customer response is modelled, and this is not cash collected.
- **Base and formula stated**: 5.000% of the current base price per eligible line multiplied by the quantity billed on that line over 2025-07-01 to 2026-06-30, summed — a step on historical net billed volume, not a current-list value and not profit.
- **Administrative and lubricant lines removed from the actionable ranking.** Rebate Material, Transporting Cost and the Shell lubricant line are out of the largest-lines table and out of the embedded chart payload, and are shown instead in a new "Excluded from the actionable ranking" table for reconciliation. Three genuine part numbers were promoted into the ranking to keep its depth.
- **Unpriced residual reframed** — a missing price on one side is a data gap, not proof that no future pricing action is possible on those lines.

### F09 Competitiveness Dashboard — P0
- **Rejected observations removed from the active page.** All three dead "Class C · Autodoc < 75% PR00" tables (10,218 characters, including the repeated €2.34 / 0% rows) were deleted, not just annotated. A single pointer marks where they were and states that the rows are excluded from every median, score, heatmap, ranking and export. The remaining mentions of €2.34 are the explanation itself and the scraper-intel warning, which is correct.
- **"Live" removed from a frozen extract** — the tab now reads "Scraper intel — extract 9 May 2026".
- **Price-index direction stated** in the formula bar: this page divides our price by the aftermarket reference, so above 1.0× means we are more expensive, and other documents use the inverse.
- Internal initials replaced with plain words throughout the reader-facing labels (DB / DLR → distributor / dealer), the chain explainer renamed, and the sources table's internal file names removed. Dependencies verified present: the four scripts and two stylesheets resolve inside the pack, and the preload alias fix already in place means the page paints from `file://`.

### F10 Sales to Dealer Comparison — P1
- **Cover terminology corrected.** The leading metric is no longer labelled "capture": it is "UTI value-parts quantity share (CV trucks)", and the scope callout defines it as value-parts quantity over value-parts plus contested-original quantity *within the selected assortment* — a mix measure, not a share of expected service demand and not a market share.
- The contested / original-only split is labelled as the older classification not yet reconciled with the functional-plus-attribute approach, so it is a classification basis rather than verified competitive exposure.
- **Reader-facing wording** now uses "sales to dealer" and plain-layer names; legacy file names and internal initials were removed from the visible text.
- **Truck versus pickup comparison made natural** — ITUK against UTI where periods and scope align, with IUK kept as an explicitly labelled pickup comparison and the network companion marked non-additive on a wider period.
- **Portugal labelled provisional** and not part of the controlled five-distributor dealer-level set.
- **Missing prices stay unvalued** — part numbers with no billing price are reported as unvalued quantity and never valued at zero inside the proxy totals. Basis strip rebuilt.

### Portfolio-wide
- Nine-field basis strip installed on F01, F02, F03, F04, F07, F08, F10; F05, F06 and F09 carry their own equivalent.
- Internal file names, internal initials and agent vocabulary removed from reader-facing text where they were found.
- One audience designation per file.

---

## 2. Findings from the brief that did **not** reproduce

The brief requires browser-reported findings to be reproduced and logged before being treated as defects. Two did not reproduce:

1. **Duplicate generated element IDs.** A markup scan that excludes script and style contents finds **zero duplicate IDs in all ten files** (F01 27 ids, F02 24, F03 25, F04 16, F05 10, F06 14, F07 33, F08 4, F09 49, F10 none). The apparent duplicates in a naive scan come from minified chart-library code inside the script blocks, not from the page. F02 generates its chips and group buttons at runtime without `id` attributes, and the only generated `id` pattern is `sel-<module>-<key>` from a fixed module and key set, so it cannot collide. **No fix applied, because there is no defect to fix.** Logged here as not reproduced.

2. **Excessive all-market page length / thousands of pixels of repetition.** This one is a design observation rather than a broken element, and I did not take the brief's pixel estimate as a specification. I did address the stated preferred design: F02 now opens on **one** market rather than all 23, with a one-click "Show all 23 markets". The remaining length comes from the honest per-market detail; I did not delete analytical content to shorten it.

---

## 3. Acceptance checklist — actual results

### Numerical and semantic
| Check | Result |
|---|---|
| Headline has period, population, definition, source, valuation | Done — basis strips on all ten; F03 and F09 use their own period fields where the general billing cut-off does not apply |
| Reused KPIs reconciled or different basis explained | Done — F01 ITUK corrected to the post-2026-09-17 ceiling basis and the bar widths rescaled; F05/F06 assigned-exposure versus observed-evidence split made explicit |
| Partial-year comparisons use matching months | Not changed — the files already compare same months; F03's two files are now explicitly *not* compared across periods |
| Unusable fleet forecast contributes to no displayed result or export | Done for F02, the only file that displayed it. F01's ceiling is modelled but is not fleet-derived forward output |
| Restricted service-demand euro aggregates absent from shared content | Done for F01 (seven sites). F02 never headlined one. **F03 still prints warranty euro** — not the restricted measure, but see open item 1 |
| Missing fleet/quote/price never becomes a valid zero | Done — F08 unpriced residual reframed; F10 unvalued quantity; F06 captive no longer inferred; F09 rejected rows removed |
| ITUK/IUK and UMI/UTI distinct | Done — restated on F01, F03, F10; untouched elsewhere |
| Dealer-data population established per view | Done — verified five dealer-level distributors; six markets have sales-to-dealer files, Portugal provisional. F01 and F02 already said this correctly |
| Functional classification and competitive exposure separate | Done — F05 realigned to F04's architecture rather than demoting F04; F07's functional hierarchy preserved |
| Pricing scenarios distinguish list/base effects, net billed value, realised profit | Done — F07 headline definition, F08 base-and-formula note |
| Approved caps enforced after all steps, or authorised exception documented | **Partly** — F06 now presents it as a release blocker with two named paths. The cap is still breached in the calculation because choosing a path is Jerome's decision, not mine (open item 2) |
| No pricing effect presented as guaranteed cash or proven response | Done — F08 |
| Warranty periods, currencies, distinct claims, payer assertions supported | Done — F03 |
| Rejected competitor observations cannot enter an active metric | Done — F09; the dead tables are deleted from the page, not merely warned about |

### Technical and visual
| Check | Result |
|---|---|
| Every JavaScript block parses; page initialises without unhandled error | **Pass** — 21 inline blocks across the ten files, `node --check` on each, zero parse failures, before and after the edits |
| All required local assets present in the delivered structure | **Pass** — F09's four scripts and two stylesheets all resolve inside the pack |
| Offline behaviour matches the file's claim; network content fails visibly | **Pass** — files are self-contained or use in-pack assets; F09 has an offline banner element |
| Element IDs unique in generated views; labels target the right controls | **Pass** — verified in markup; runtime chips have no ids by design |
| Distributor, account, source, family, period, measure selections behave consistently | **Partly** — all filters read the same `SEL.dbs` state on F02 and F07 by inspection. I did not click through every toggle (open item 3) |
| Reset, drill-down and drill-back from deep selections | **Partly** — F02's "Show all N markets" reset verified by inspection; deep-selection round trips not exercised |
| Blank selections, no-data cases, missing-source cases understandable | **Pass by inspection** — amber banners exist for no-peer, no-dealer-detail, no-group-mix and not-scored |
| Tables, charts, captions and tooltips use the same selected values | **Partly** — no shared numeric mismatch found for the measures I marked; a full cross-artefact reconciliation was not run |
| No unexplained scale, clipped label, unreadable colour, heatmap hover failure | **Partly** — read all ten first-viewport screenshots; no clipping or unreadable contrast seen at the fold. The brief's table-hover-versus-heatmap question was not tested |
| Keyboard navigation, focus, zoom, narrow screens | **Not run** — open item 3 |
| Print output inspected for the paper-style files; screen and print agree | **Not run** — open item 3 |
| Before/after record identifies the tested file and data version | **Done** — this report plus `CHANGES.md` in the pack |

**Screenshots:** 10 taken, 10 read by me at full resolution, 0 blanks.
Ink coverage across the full 1440×900 viewport ranges from 53.2% (F02) to 99.7% (F06); F02's lower figure is the dark navy header with content below, not a blank panel. Frame-by-frame measurement is in `_qa/screenshot_report.json`.

---

## 4. Unresolved issues, with what is missing and what is blocked

1. **F01 and F03 still print euro figures that may have a quotability restriction.** The brief says the network-wide service-demand euro total is not quotable; I removed that aggregate from F01. But F03 prints warranty parts euro (€4.655M truck turnover, €2.838M emissions) and the warranty set carries its own currency-correction history. I applied the corrected figures and the dated correction note, but **I could not confirm against C02 whether the warranty euro total carries the same internal-only restriction as the service-demand aggregate.** Blocked output: F01 and F03 continuing to be labelled shared. Decision needed: is warranty euro quotable in a shared version, or internal only?

2. **The F06 cap breach needs a decision, not a fix.** The paper now discloses it as a release blocker with two legitimate paths. Until someone chooses "enforce the ceiling" or "approve a change", the scenario cannot be released. Blocked output: F06 as an approved policy; any downstream pack that quotes the tier step.

3. **Interaction, keyboard and print were not exercised.** F02 and F07 are the files where the brief asks for exactly these tests: deep selections, drill-back, distributor/sold-to consistency, table-hover versus heatmap colours, zoom, narrow screens, and print layout for the paper-style files. I verified by inspection and by rendering the first viewport, and I read those renders, but I did not drive the controls or print to PDF. Blocked output: a clean claim that the interaction layer is correct, and a clean claim that the A4-fixed papers print as they read.

4. **The five-versus-six coverage question is investigated but not closed.** From `sales_to_dealer_coverage.csv`: only ITUK has named dealers (64, CY2025); Portugal, IUK, UTI, Ireland, Greece and Romania have network-level long files but zero real dealer names; the controlled statement that five distributors have dealer-level data holds. Six markets have sales-to-dealer files, one of them provisional. F01, F02 and F10 now say this consistently. **What remains unresolved is whether Portugal should be treated as a qualifying dealer-level source at all** — that is a data-owner decision, not a wording one. Blocked output: any country count or coverage percentage that treats Portugal as equal to the other five.

5. **Replenishment exception count (1,595) is still on the pre-existing extract vintage.** The prior pass noted this and I did not re-count it, because re-counting is a data rebuild rather than a correction. It remains labelled as an observed-subset fact. Blocked output: quoting that count as current.

6. **Not rebuilt:** the F07 embedded payload (6.3 MB, field names preserved), the F02 node-level rebuild, and the `build_dealer_sellout_aim_gps.py` data rebuild. All three files were corrected at the shell and label level, which is what the brief asked for; a data rebuild was explicitly not the answer to this brief. Consequence: field names inside the payloads still use pipeline vocabulary, and those strings would only change on a rebuild.

---

## 5. Files delivered

| File | Corrected copy | Screenshot |
|---|---|---|
| F01 | `...\_gpt_review\2026-09-19_next10_brief_corrected\01_ISZE_Exec_Aftersales_Paper.html` | `_qa\01_..._viewport.png` |
| F02 | `...\02_ISZE_Leakage_Cockpit.html` | `_qa\02_..._viewport.png` |
| F03 | `...\03_Warranty_Commercial_Review.html` | `_qa\03_..._viewport.png` |
| F04 | `...\04_ISZE_AIM_Classification_Paper.html` | `_qa\04_..._viewport.png` |
| F05 | `...\05_ISZE_AIM_vs_Price_Class_Case.html` | `_qa\05_..._viewport.png` |
| F06 | `...\06_ISZE_Pricing_Policy_Paper_REV3.html` | `_qa\06_..._viewport.png` |
| F07 | `...\07_ISZE_Pricing_Revision_AIM_Source.html` | `_qa\07_..._viewport.png` |
| F08 | `...\08_ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html` | `_qa\08_..._viewport.png` |
| F09 | `...\09_ISZE_Competitiveness_Dashboard.html` | `_qa\09_..._viewport.png` |
| F10 | `...\10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | `_qa\10_..._viewport.png` |

Originals: `...\_gpt_review\2026-09-19_next10_fixed` — unchanged.

**Definition of done, against the brief's own wording:** the existing files are clearer and internally consistent on the points I could verify; unsupported conclusions that I could reach were removed or qualified; no missing evidence was replaced with confident wording. The three items I could not verify are named above rather than covered with a success badge.
