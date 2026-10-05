# Comparison framework

This is the agreed evaluation scope, not a completed scorecard. Do not count missing evidence as failure of a system. Evidence from an exported report is not automatically evidence about the underlying classification.

| Criterion | Identical test for ZKK and AIM | Decision relevance |
|---|---|---|
| Reconciliation | Join each scheme to identical monthly/distributor/part inputs; reconcile all sales and quantities, retaining unknowns. Test for duplicate joins. | Prevents a mapping from creating or losing sales. |
| Coverage | Measure classified share by billed euro, active references and distributor, on the same period and denominator. Separate unknown, not applicable and unresolved. | Shows where findings represent the business. |
| Accuracy | Compare assignments with approved technical/application evidence on a stratified sample, including high-value and ambiguous parts. Test inconsistent replacement chains. | A fully populated but wrong code is not accurate. |
| Hierarchy and coherence | Review definitions and parent/child rules. Test whether families group parts that support a consistent commercial interpretation. | More categories need to improve decisions, not merely expand reports. |
| Sales and growth explanation | Show L12 and prior L12 sales, EUR movement, comparable quantities and price components; compare equal detail levels. | Establishes whether the classification explains the movement. |
| Hidden movements | Identify category totals masking gains and losses; show which segmentation exposes them and whether the other scheme can do the same. | Tests incremental insight rather than visual detail. |
| Distributor relevance | Apply the same family/market profiles; account for application, fleet scope, commercial terms and data coverage. | Supports distributor-specific action without misleading national averages. |
| Purchasing continuity | Compare continuing, newly active, reactivated and no-current-purchase combinations; validate replacements before interpretation. | Distinguishes a real range change from a reference change. |
| Original/value-parts analysis | Test whether both can join comparable alternatives without double counting; distinguish quantity from EUR share and product mix from market share. | Supports competitive range strategy. |
| Downstream compatibility | Give both schemes the same sales-to-dealer records; retain missing periods and separate valuation bases. | Prevents stocking changes being mistaken for end-demand changes. |
| Pricing and profit | Evaluate analytical support with historical costs, terms and SPA identifiers when present; otherwise judge design only. | Measures decision support, not assumed margin improvement. |
| Commercial actionability | Trace each proposed action to distributor, family/part, supporting evidence, validation need and profit assumptions. Avoid double-counting opportunities. | Tests whether analysis leads to a specific defensible intervention. |
| Stability | Apply fixed-version mappings to both periods; separately inspect as-recorded versions and category migrations. | Prevents reclassification appearing as growth. |
| Governance and auditability | Establish owners, source evidence, confidence, review state, overrides, effective dates and change history. | Enables traceable, controlled use. |
| Usability | Compare like-for-like tasks, clarity, drill-down and review time using actual evidence where available. | A complex model must be usable by the people acting on it. |
| Maintenance effort | Compare update cadence, unresolved records, exceptions, manual work and operating dependencies. | Tests sustainability rather than category count. |

## Required common measures

L12 and prior-L12 EUR, EUR change, percentage change when denominator is positive, growth contribution, part-level quantities, weighted gross margin and gross profit when costs exist, average billed prices for continuing distributor-part pairs, active references/families, monthly purchasing breadth, top-part concentration, and matched-quarter movement. Fleet-normalised measures require a valid period-aligned denominator.

## Recommended display

Use one shared sales control table, side-by-side ZKK and AIM category tables, an EUR-weighted crosswalk, common-mapped and all-sales coverage, a small set of concrete before/after insights, the criterion verdict table, and a final recommendation. Separate classification-only performance from additional application/data capabilities.

## Numerical definitions

For a continuing distributor-part combination, let q0,p0 be prior quantity and average price and q1,p1 be current quantity and average price. Quantity contribution is (q1-q0)*p0. Billed-price contribution is q1*(p1-p0). The interaction belongs to price under this convention. Entry/exit sales complete the reconciliation. A missing or non-positive quantity makes this decomposition unsuitable for that combination and must be handled explicitly.

Gross margin, when available, is total gross profit / total sales, never the simple mean of line margins. Periods with no positive base do not receive a misleading growth percentage. Quantity totals across unlike parts are not end-demand measures.
