# Feedback for Cursor: tonnage evidence and AIM comparison

**Review date:** 20 September 2026.  
**Basis:** the uploaded tonnage pack, principally metadata dated 19 September 2026; billing ends on 30 June 2026.  
**Audience:** internal implementation and data review. Not a distributor-facing paper.  
**Scope:** correct and reconcile the tonnage evidence. Do not redesign the atlas, replace the existing billing basis, or build a second dashboard as part of this correction.

## Decision

Keep the tonnage idea, but do not connect the current pack unchanged to band-level performance comparisons. It contains useful part-applicability evidence and a separate model of expected service demand. Those do not yet form one reconciled measure of actual spending by truck weight.

The objective is a defensible comparison between ITUK (UK trucks) and UTI (Israel trucks), with other distributors available separately. IUK (UK light commercial) and UMI (Israel light commercial) must not be blended into those accounts.

The numerical findings below are independent checks of the supplied files, not replacement commercial KPIs or confirmation that the wider verification process passes. Source claims, review findings and proposed changes are distinguished. No source files or HTML files were changed for this feedback.

## Correct the additive billing denominator

**Source claim:** section 3c of `00_START_HERE_tonnage_and_unique_parts.md` presents an exclusive-band share of roughly 11% for the 2025 calendar-labelled rows.

**Recomputed finding:** the denominator includes the alternative `also_fits_band` views. Those repeat purchasing already included elsewhere. On the uploaded snapshot, across the represented distributors and selected tagged N-series service parts:

| Calendar-labelled 2025 reconciliation | EUR |
|---|---:|
| Exclusive-band purchasing | 385,665.74 |
| Disjoint tagged purchasing total | 1,212,326.17 |
| Additional nonadditive applicability views | 2,176,726.04 |
| Incorrect all-membership sum | 3,389,052.21 |

The exclusive share is **31.812% of that tagged source**, not 11.4%. This is an internal source-coverage calculation, not a share of the entire ISZE portfolio, a service-cover percentage, a sales opportunity, or a fleet-normalised result. The rows retain their individual completeness flags. There is no fleet denominator in this calculation.

**Required correction:** select one reporting clock and period before calculating either side. For the current extract, the additive partition is `sums_to_n_series_total == "yes"`: `single_band_only`, `pooled_all_bands`, and `series_unresolved`. The exclusive numerator is `membership == "single_band_only"` within that same selection. Exclude `also_fits_band` from totals, but retain it as explicitly nonadditive applicability information. Do not add calendar-year and fiscal-year representations of the same transactions.

For the calendar representation across January 2023-June 2026, the additive partition totals EUR 4,305,333.64, matching the metadata's tagged total. This establishes arithmetic reconciliation at that scope only.

**Acceptance:** demonstrate exclusive + pooled + unresolved = tagged purchasing for each distributor and period. Also show the bridge from the tagged scope to its parent service-parts population, including excluded or unplaced records. Do not call the tagged total all N-series parts billing without that bridge.

Sources: `nseries_tonnage_evolution.csv`; `nseries_tonnage_evolution.meta.json` (`tie_out`, `rules`); main brief sections 3c and 4.

## Reconcile the part populations before quoting coverage

**Source claim:** the broad candidate count is presented as though it describes the same universe as the service worklist.

**Recomputed finding:** the tables do not establish that relationship. On their stored all-market, January 2023-June 2026 reference amounts:

| Source population | Distinct part numbers | Stored EUR |
|---|---:|---:|
| Service worklist | 835 | 20,647,862.76 |
| Broad tonnage candidate table | 297 | 23,703,784.82 |
| One-band candidates in that candidate table | 143 | 7,468,416.51 |
| Exclusive parts in the service-category summary | 34 | 733,218.76 |

Matching `tonnage_capable_part_numbers.csv.pn` to `epc_decode_worklist.csv.part_number` as strings finds **91 common part numbers**; **206 candidates are outside that service worklist**. These are population diagnostics, not findings about fleet demand.

The candidate table has one row per distinct part. Its higher euro total cannot be explained merely by saying that a part fits several bands. Scope and billing-basis differences require a bridge. The category-summary population also cannot replace the strict N-series population without reconciliation.

**Required correction:** identify the authoritative service universe, document why each candidate is included or excluded, and reconcile the euro basis, dates and treatment of credits. Retain identifiers as strings. Do not describe 143 candidates as 143 of the 835 service parts until the set relationship actually holds.

**Acceptance:** return counts and euros for the intersection and both unmatched sets, with reasons. The service-family summary must reproduce the approved underlying part population. Reconcile the published headline, body tables and metadata to that same population.

Sources: `tonnage_capable_part_numbers.csv`; `epc_decode_worklist.csv` and metadata; `tonnage_capable_categories.csv`; main brief sections 1 and 3a.

## Resolve contradictory weight assignments with evidence

**Verified example:** fuel filter `5876100940` is exclusive to `5.5t` in `tonnage_capable_part_numbers.csv` but is assigned `3.5t_N35` in `epc_decode_nseries_banded.csv`, with NKR given as the model-code evidence. Both rows carry EUR 5,514.47 on their all-year reference basis. This is a classification conflict, not rounding.

The same candidate-5.5-t versus strict-3.5-t conflict occurs for:

`5876100230`, `5876100940`, `5876101070`, `8943604181`, `8973102750`, `8980374800`.

The candidate table contains 16 exclusive 5.5 t parts, carrying EUR 16,833.98 on its all-year reference basis. The strict, in-scope N-series mapping has no exclusive 5.5 t records. Accordingly, the broad statement that none exist anywhere is not supported by the pack as a whole. Nor is the candidate assignment automatically correct.

**Required correction:** document the authoritative mapping and evidence for each conflict. The approved assignment must retain source, applicability scope, effective mapping version, confidence and unresolved reason. Preserve the original claim and correction in the review history. Do not choose whichever table makes a desired result look complete.

Use whole model-code tokens; preserve the existing protection against confusing `TF*` with `F*`. Record shared applicability as shared, not as an allocation. A conflict must be visible and must prevent that record being used as an approved exclusive assignment until resolved.

**Acceptance:** the same approved part cannot be exclusive to incompatible weight bands in two outputs. Keep the broader 5.5 t conclusion qualified to the approved population.

Sources: the two mapping CSVs; `series_to_tonnage.csv`; main brief section 3b; `nseries_tonnage_evolution.meta.json` (`band_split_single_versus_shared`, `rules`).

## Separate purchasing, expected demand and attributed gaps

The supplied `pms_tonnage_model.csv` repeats market actuals beside band-level expected demand. Every record marks `actual_is_market_level = True`. Those actuals are not band purchases.

**Required correction:** keep these distinct in both data and interface:

- **Recorded purchasing attributed through validated exclusive applicability.** These are distributor purchases of selected parts, not observed service events or proven vehicle end use.
- **Expected service demand by band.** This is modelled from fleet, mileage, service schedule and category assumptions.
- **Market-level actual purchasing.** This remains market-level even when displayed alongside a band expectation.

Never sum repeated market actuals down the band rows or allocate them using fleet or expected-demand shares. Do not calculate band service cover by dividing a whole-market actual by a band expectation.

The model also contains `gap_eur_band_share`. Audit its calculation explicitly. A market gap distributed by expected-demand weights is a modelled allocation, not observed missing band purchases. It must not become a measured band leakage figure, a colour-coded performance ranking, or an externally totalled service-gap amount.

Even with an exclusive-parts numerator, a service-cover percentage needs the matching expected demand for exactly that supported service scope. A narrow subset of part purchases cannot be divided by all category demand and described as total service cover.

**Acceptance:** no band-level actual, rate or gap can be obtained merely by renaming or proportioning a market-level field. Label measured inputs and modelled quantities separately.

Sources: `pms_tonnage_model.csv`; `pms_tonnage_model.meta.json`, limits; main brief section 6.

## Correct the interval explanation and resolve mileage ownership

**Source claim:** lowering the N35 expected-service frequency is said to reduce oil-filter cover.

**Review finding:** with fixed actual units and scope, `cover = actual / expected`; reducing expected units increases cover. A reduction in cover requires some other change that must be stated. Do not retain the current directional explanation or manufacture a replacement rate.

There is also an ownership conflict inside the narrative: section 5 associates 14,494 km/year with ITUK N35, while section 8 and the short brief label it IUK N35. Treat that as a provenance question, not permission to move mileage evidence between distributors. Record the observation period and the vehicle sample behind the adopted figure.

**Required correction:** provide the before/after actual units, fleet scope, mileage, service interval, expected units and reporting basis for any proposed ITUK change. Keep the existing external ITUK standard and internal network method separate. Do not rebase either silently or combine their cover percentages into a ranking. Any common-basis scenario is a separately labelled proposal requiring approval.

**Acceptance:** a fixed-numerator test must show that lowering expected demand raises cover. Every mileage input must resolve to a distributor, vehicle scope, period and evidence source.

Sources: main brief sections 5 and 8; short brief section 'What to ignore'; `02_NUMBERS_AND_HOW_THEY_ARE_BUILT.md`, service-cover definition and ITUK dual-basis explanation.

## Establish a usable fleet denominator without overclaiming warranty evidence

The demand model holds a **2025E** band fleet across years. That is a fixed estimated denominator, not an annual measured fleet series. The wider project context also rules out using the current fleet forecast beyond 2025.

A possible future measure is:

> Selected exclusive-parts billing per truck in the supported weight band.

It requires a matching distributor, period, band definition and fleet reference. It is not total spend per truck by tonnage. A fixed 2025 estimate could be displayed as an explicitly fixed-reference diagnostic, but not as historical measured spending per vehicle. Keep estimated fleet inputs visibly labelled. Zero or missing denominators must return an unavailable result with a reason, not zero or infinity.

The model's absence of a UTI 3.5 t fleet is justified in its metadata by the absence of certain model codes in warranty VINs. That establishes absence from the cited warranty sample, not necessarily from the entire fleet in service. Warranty is not a complete fleet census or a record of scheduled maintenance.

The uploaded 2025 evolution also records purchases in UTI's 3.5 t exclusive group while the model supplies no corresponding band fleet. Investigate the source assignment and commercial scope; do not invent a fleet count, delete the purchases, or infer the vehicles actually serviced.

Portugal is a route to inspect, not a verified solution to both sides of the ratio. The referenced per-VIN registration workbook and Portugal study were not supplied here. Registration data may establish the denominator. Full observed purchasing by band also needs vehicle-linked parts records or an audited distributor-provided split at a compatible sales level and period. Sales to dealer cannot silently replace ISZE-to-distributor billing.

**Acceptance:** each rate exposes its numerator scope, denominator value, fleet date, measured/estimated status and source. Fleet counts reconcile by distributor; unknown or unsupported bands remain visible.

Sources: `pms_tonnage_model.meta.json`; `uio_ld_n35_share.csv`; `nseries_tonnage_evolution.csv`; main brief sections 3d, 6 and 7; short brief section C; project context file 03, fleet caveats.

## Clarify time coverage before enabling trends

For the uploaded 2025 calendar-labelled evolution rows, `months_in_period` has values of 3, 10 and 12 for ITUK, and 2, 9, 10 and 12 for UTI. A blanket description of all non-ITUK 2025 rows as eleven months does not describe the file.

**Open question, not a confirmed code defect:** does `months_in_period` count months in the available source extract, or months with purchases of the selected parts? The source-generating code was not supplied for this review. A part bought in only a few months can still belong to a complete annual source.

**Required correction:** establish the calculation and separate source coverage from purchasing activity. Until resolved, retain the supplied completeness and comparability flags; do not silently override them or infer missing files from no purchases.

January-June 2026 stays separate from complete years. A prior-year half-year comparison needs the same months, source coverage, billing exclusions and mapped part universe on both sides. Do not double a half-year amount or apply a full-year expected-service denominator to it without an explicit approved method.

**Acceptance:** incomplete or mismatched periods cannot display a like-for-like growth rate. A known complete source with no activity must remain distinguishable from an unavailable source.

Sources: `nseries_tonnage_evolution.csv`, period fields and `comparable_to_previous`; main brief section 7.

## Make ITUK-UTI comparisons comparable, not simply clickable

The supplied groups do not contain a separate 10 t band. The broad 7.5 t grouping cannot establish the requested distinction between an ITUK fleet mix and a UTI 7.5-10 t mix. Do not relabel it as a precise vehicle-weight distribution.

Obtain the approved band definitions and fleet evidence before refining the grouping. Preserve measured gross-vehicle-weight data separately from broad applicability classes. Do not infer a finer fleet split from a coarse part-to-model association.

For a fair purchasing comparison, define a common, validated eligible part basket for both selected distributors and show the coverage outside it. Do not use only the intersection of positive purchases: that would remove genuine non-purchasing observations. Zero is valid only where source completeness establishes it; missing records remain unknown. Keep the full selected-family view available alongside any common-basket view.

Differences in billed euros still reflect price, purchasing mix and stocking decisions, not only service volumes. Do not describe the residual as competitive leakage or customer demand without the additional evidence needed for that claim.

**Acceptance:** both sides expose the same measure, time basis, eligibility rules and coverage status. Where bases differ, show the values descriptively and state the difference rather than produce a performance winner.

Sources: `nseries_tonnage_evolution.meta.json`, bands; `pms_tonnage_model.meta.json`; project context on distributor purchases. Common-basket handling is a proposed comparison rule, not an existing field in the pack.

## Define the minimum data needed for the existing Compare view

`nseries_tonnage_evolution.csv` has no category or part-number field. Its aggregates cannot supply the requested detailed drill-down by themselves.

Request the existing data owner's approved monthly aggregate at:

`distributor x reporting month x service category x part number`

It needs recorded billed EUR, units, explicit sales level, billing-exclusion basis and source-coverage status. Join only to a reconciled, versioned part-applicability mapping. That mapping needs approved band membership, exclusive/shared/unresolved/conflicting status, evidence and effective scope. Keep the fleet references and maintenance assumptions separate from the actual-billing table.

For shared parts, preserve a one-to-many applicability relationship, but count the purchasing once in the pooled total. Do not expand the accounting total through that relationship.

After approval, integrate this into the existing Compare view:

`Selected distributors -> weight band -> family -> category -> validated parts`

Keep both distributors, period, pinned part and portfolio overview selected throughout. Shared and unresolved purchasing must remain visible beside the attributable slice. Back returns to the same comparison. Do not provide a click target implying detailed commercial data where only a broad total or catalogue examples are available.

ZKK mapping remains unavailable unless the approved mapping is actually supplied. Part examples must remain labelled examples until a complete approved list exists. Preserve the existing half-year tile, denominator disclosure and red/blue/white design; no further graphic redesign is requested in this correction.

**Acceptance:** child totals reconcile to parents on the same basis; cross-band browsing does not duplicate purchasing; missing detailed data produces a clear explanation rather than invented allocations.

Sources: evolution CSV header; supplied part mappings. The monthly aggregate and navigation requirements are proposed implementation requirements, not a claim that those files were supplied.

## Return evidence of correction, not only a pass count

The supplied 20 September narrative reports that the wider verification process is not green and names `lost_sales.billed_ties_to_parts_base` as the failure. The live `_verification_report.json` was not supplied here, so its current contents have not been independently inspected. The tonnage arithmetic tie-out does not clear that failure or the population and mapping issues above.

Please return:

- A corrected main brief and short brief, with a change log identifying source corrections versus unresolved questions.
- The part-population bridge and the resolved mapping conflicts, with evidence and any exceptions still withheld.
- Reconciled additive billing at the required detail, and separately documented fleet and interval inputs.
- A current verification summary that distinguishes arithmetic, definition, coverage and interface checks, with the remaining limitations visible.

Use the existing review materials in `AIM_Cursor_Handoff_v2.1/review/` as reproducibility aids, not as an authority that can override source evidence. The review's source totals and set intersections were independently checked again for this feedback.

Minimum tests before enabling new band-level rates:

- One reporting clock and one disjoint accounting partition reproduce each parent total.
- Published population counts come from the approved set, and category totals reproduce the part list.
- Conflicting assignments cannot enter exclusive-band totals as approved records.
- Market actuals are never replicated into measured band actuals or band service cover.
- A lower expected denominator raises cover when actual units are fixed.
- Every fleet-normalised result has a compatible, nonzero, dated denominator; estimates remain labelled.
- Half-year, incomplete-source and missing-basket cases cannot masquerade as full-year like-for-like comparisons.
- Interface drill-down retains the comparison and overview and reconciles without allocating shared purchases.

Keep source diagnostics internal. Do not distribute new tonnage performance claims while the relevant reconciliation and approval conditions remain unresolved. Do not attach raw billing lines or a full price list. Correct the evidence first; activate the weight-band comparison only for the scope the corrected evidence actually supports.
