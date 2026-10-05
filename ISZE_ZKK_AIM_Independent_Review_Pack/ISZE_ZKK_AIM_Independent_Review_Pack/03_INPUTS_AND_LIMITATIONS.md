# Inputs, limitations and omissions

## Available in this package

The two L12 billing periods are provided as monthly distributor-part aggregates and a complete two-period distributor-part table, with a separate part-label table. These reproduce the earlier workbook's explicit operational billing basis, not a finance-approved revenue control. The original generated workbook and cached-value CSV exports are included.

Also included are source-supplied family/original/value mix, AIM-labelled annual mix, sales-to-dealer coverage and valuation summaries, historical fleet, mileage, aggregate warranty evidence, target-spend summaries and the five context documents. Original filenames and legacy field labels are retained unless the manifest identifies a screened copy.

## Essential to the exact two-system L12 classification test, but absent here

* Actual part-number-to-ZKK assignments, category dictionary/hierarchy, rule definitions and mapping version/effective dates.
* Actual part-number-to-AIM assignments, category dictionary/hierarchy, commercial axes, rule definitions and mapping version/effective dates.
* Mapping source/approval, exception and override history, and validation evidence for evaluating accuracy rather than merely completeness.

The supplied part labels and catalogue keys are not those mappings. Selected annual family aggregates cannot reconstruct a unique part-level assignment. Empty templates in `inputs_required/` only specify convenient input columns. There is no need for another raw billing upload to perform the same-population comparison once actual mappings are available.

## Inputs for extended tests, also absent

Historical costs and dated SPA identifiers are needed for actual profit/SPA evaluation. Inventory movements and availability history are needed to validate stock and supply explanations. Approved replacement chains and vehicle application improve purchasing-continuity interpretation. Period-aligned fleet/service assumptions are needed for an L12 expected-demand comparison. Actual usage logs, owner/process evidence and maintenance records are needed to measure usability and operating effort.

Do not make these optional inputs a reason to postpone the entire system review. Assess what the documented systems demonstrably support, and identify which additional tests they affect.

## Prior analysis is not a completed comparison

The previous workbook's ZKK/AIM result was not computed. Its comments and inferred findings are material for independent review, not ground truth. The later conversational recommendation favouring complementary use was not based on a complete empirical head-to-head. This package does not prescribe a winner.

The workbook reconciles internally but differs from published annual/distributor summary figures. Its Reconciliation sheet preserves that problem. The new aggregates replicate this provisional basis so that the next model can test classification fairly; they do not repair or replace the official figures.

## Inventory and access boundaries

The handover was built from files actually mounted in this conversation. Semantic Project search returned an access error during packaging; mounted bytes and direct known-file reads were used. No access to the user's complete local workspace was obtained. Absence from this package does not mean absence from the ISZE workspace.

## Intentionally omitted or screened

Raw invoice-line billing and full price lists are not redistributed under the project handling rules. The full raw warranty file and full merged sales-to-dealer source are not necessary for this package; aggregate evidence and the existing ITUK part-level comparison are included instead. This limits rechecking of source selection outside the original workspace.

The tender/account/gap combined file and screenshot previews are omitted as not necessary for this system-comparison handover. No hidden workbook, full pricing database, restricted action-euro register or unverified mapping is included.

The explicitly restricted strategic-background section in business context was removed. The explicitly restricted network service-demand euro total in the metric context was removed. The fleet export excludes rows flagged as forecast. The service-family export blanks euro-gap values not explicitly flagged quotable. Transformations are recorded in `MANIFEST.json`; other source summaries are unchanged.

## Important source distinctions to test, not silently correct

The context documents and exports have known tensions about cut-off dates, return treatment, fleet bases, source-channel terminology, annual comparisons, and family populations. Preserve and explain these differences. Do not assume identically labelled categories have identical membership, or that an arithmetic check validates the commercial interpretation.

Do not equate a quantity valuation with observed euro turnover, a modelled target with measured demand, a dealer share of national sales with dealer effectiveness, or an original/value mix ratio with share of competitors' sales.
