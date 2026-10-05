# CHANGES — corrected next10 pack

Corrected copies of the ten numbered HTML files, made against
`ISZE_Ten_File_Review_and_Fix_Brief_2026-09-19.md`.

Originals are preserved unchanged in `..\2026-09-19_next10_fixed`.

Nothing here was copied onto a live `02_dashboards\` path. No price changed, nothing was published, nothing was mailed.

| # | File | Priority | What changed | Left open |
|---|---|---|---|---|
| 1 | `01_ISZE_Exec_Aftersales_Paper.html` | P0 | Restricted network aggregate removed at 7 sites; stale ITUK shortfall €11.6M → €6.65M with bars and chart array rescaled; cover headline replaced with a decision statement; 15 footers and the sources page now separate the dated data verification from HTML testing; tender "live" → dated snapshot; basis strip; internal file names removed | Warranty-euro quotability (see report item 1); replenishment count vintage |
| 2 | `02_ISZE_Leakage_Cockpit.html` | P0 | 2030 fleet-forecast render deleted; substitution labels reframed as a model classification (82 sites); benchmark specified; default selection reduced to one market with a one-click show-all; basis strip; current data verification in footer | Interaction and print not exercised (report item 3) |
| 3 | `03_Warranty_Commercial_Review.html` | P0 | Payer inference removed (sections 4 and 7 renamed, prose corrected); both claim windows printed as explicit dates and explicitly not compared; currency correction stated with the superseded figures named; claimed/admitted/reimbursed kept apart; rate definitions separated; entity rules restated; warranty-specific basis strip | Cross-period comparison still declined rather than matched (no shared period exists) |
| 4 | `04_ISZE_AIM_Classification_Paper.html` | P1 | Single current definition added; completeness / source agreement / adjudicated correctness separated and never called accuracy; historical error ledger with version, window, corrected, regenerated; basis strip | Residuals remain open by design |
| 5 | `05_ISZE_AIM_vs_Price_Class_Case.html` | P0 | Proposition changed to "price classes construct the list; functional families organise the business"; level 1 labelled an assigned commercial attribute; exposure must carry market and date; one audience designation | Coverage figures not re-derived from source |
| 6 | `06_ISZE_Pricing_Policy_Paper_REV3.html` | P0 | Audience resolved to internal / private; cap breach presented as a release blocker with two named paths; observed benchmark coverage (880 lines, €5.369M, 16.5%) separated from the model-assigned 53.8% tier; captive no longer inferred from a missing quote | Cap path needs a decision (report item 2) |
| 7 | `07_ISZE_Pricing_Revision_AIM_Source.html` | P1 | Headline defined as total change over prior-price value of the same eligible quantities, not a mean of percentages; total billed and priced-on-both-sides never mixed; unknown supply source an explicit named category; historical FX basis labelled in both places; basis strip | Deep interaction and selector consistency not exercised |
| 8 | `08_ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html` | P0 | Cash certainty removed ("collectable" / "lands as money"); base and formula stated; rebate, transport and lubricant lines out of the actionable ranking and into a reconciliation table; unpriced residual reframed as a data gap | Volumes and discounts remain unmodelled by design |
| 9 | `09_ISZE_Competitiveness_Dashboard.html` | P0 | Three dead Class C tables deleted (10,218 chars of €2.34 / 0% rows) and excluded from every metric and export; "live" removed from a frozen extract; price-index direction stated; internal initials and file names removed from reader-facing labels | Heatmap hover versus table-hover not tested; print not tested |
| 10 | `10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | P1 | Leading metric renamed to a quantity share within the selected assortment and defined; old contested/original split labelled as a classification basis; ITUK-versus-UTI natural truck comparison with IUK a labelled pickup comparison; Portugal provisional; missing prices unvalued; basis strip | Portugal's status as a qualifying dealer-level source is a data-owner decision |

## Verification run on this pack

- 21 inline JavaScript blocks checked with `node --check`: 0 parse failures.
- Markup element ids: 0 duplicates in all ten files.
- F09 local assets: 4 scripts and 2 stylesheets all present.
- Rendering: 10 screenshots taken, 10 read at full resolution, 0 blank or near-blank pages.
- Banned-language sweep on visible text only, after excluding script and style content.

## Two browser findings that did not reproduce

- **Duplicate generated element ids:** not present. A scan excluding script and style content finds zero duplicate ids across all ten files; the apparent duplicates came from minified chart-library code, and F02's runtime chips carry no ids.
- **Excessive all-market page length:** treated as a design observation, not a defect. The stated preference for one selected distributor is now the default on F02.
