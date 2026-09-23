# Data and metric contract | proposed R1 test basis

**Status:** Draft definitions for local validation. Not a declaration that the underlying source files pass. A05-A08 remain evidence-dependent.

## Source contract

Each source records `source_id`, exact path, checksum, source revision if available, extraction/build time, original data cutoff, row grain, commercial level, raw/canonical keys, unit, signed-value convention, currency, tax/price basis, reporting clock, complete periods, population, permission/export scope, supersession and known omissions. Date a file was copied is not its data coverage.

Use separate facts for ISZE billing, distributor-to-dealer purchasing and IDS assessments. Keep model inputs/outputs and price references separate from observed transactions. A downstream amount valued using an ISZE average remains a downstream reference valuation, not an ISZE invoice or dealer transaction value.

## Metric definitions and constraints

| Metric | Definition | Required eligibility and display | Prohibited interpretation |
|---|---|---|---|
| Recorded sales-to-dealer quantity | Sum signed quantities for the declared account/part/period population | Defined grain; consistent units; monthly observations only; annual controls separate | Parts installed, services completed, retail turnover |
| Purchasing change | Difference or percentage change across like-for-like complete periods for the same observed population | Comparable source completeness, units, classifications and account treatment; flag zero baseline rather than infinite growth | Dealer failure, workshop inactivity or loss to competitors |
| Reference-price valuation | Sum of eligible quantity x dated reference price with documented unit/pack/currency conversion | Price identifier, basis/date, valued/unvalued population and signed returns visible | Dealer invoicing, actual savings, realised gross profit |
| Actual ISZE billing | Recorded net commercial value from the scoped billing source under its documented credit/tax/currency convention | Distributor, exact period, complete/partial status and ledger treatment | Dealer revenue or a second amount to add to downstream sales |
| Genuine/BVP category mix | Share of a stated eligible family/population on one documented measurement basis | Keep unknown classification visible; choose comparable unit groups or stated financial basis; handle zero/negative denominators explicitly | Market share or proof that every part in a category is interchangeable |
| Part-level alternative comparison | Matched Genuine/BVP pair or relation with documented application and common unit/pack/price basis | Match evidence, validity, source, limitations and unresolved state | AIM category membership as fitment approval |
| Replenishment comparison | Aligned upstream/downstream quantities or common-basis reference values shown separately | Same part population, period, signed convention and coverage; stock/transfers/other sources stated as unknown if missing | Measured inventory movement, leakage or lost revenue |
| Expected service demand / GPS/PMS context | Existing model at its supported market/family/band grain with pinned inputs | Model vintage, fleet/service/price assumptions and excluded scope visible | Dealer-level demand or recoverable revenue from allocated market totals |
| Dealer self-assessment result | Recorded IDS result for a declared assessed population and available detail | Assessment round/version; date unknown when not supplied; scoring denominator and exclusions | Distributor audit, commercial performance or improvement across an unobserved second round |
| Action completion | Recorded action status and evidence of completion/review | Owner, scope, due/review dates, shared visibility and linked source snapshot | Causal sales improvement or proof of dealer compliance |
| DLOD support | Verified approved/paid support from its own source, separately from requested support | Case/history type, amount basis, timing and status | Incremental profit or a won customer inferred from rebate value |
| Tender opportunity | An eligible notice with source, relevance, publication/deadline/check time and status | Coverage and freshness; vehicle/chassis/parts/R&M distinction | Aftersales revenue, probability or pipeline euros from notice count |

Do not aggregate different physical units into a service count or a like-for-like mix. A reported raw total across part numbers may be a control total only; label it as reported item quantities and use family/unit-compatible analyses for interpretation. If credits make a denominator zero or negative, do not render a conventional positive share without a defined treatment.

## Fields requiring explicit quarantine

`uio_units` and `sellout_spu_eur` cannot be used at dealer level until their denominator lineage is established. A national fleet copied into each row or allocated by sales share is not dealer fleet.

`contested_bvp_capture` is unresolved until the eligible product set, paired relationships and denominator are documented. Rename any retained display to its actual meaning; no market-capture claim from own-network purchasing.

`l12m_billed_eur` from the AIM file is excluded from the classification projection. Its own population and billing period are not inherited from a selected dealer's facts. Inclusion in a permitted internal portfolio view would require a separate scoped source and explicit measure, never an accidental classification join.

## Identity contract

A commercial account, dealer organisation, physical site, service territory and IDS assessment are separate entities. A link records the relation type, evidence, validity, reviewer and approval state. Validating an address does not establish responsibility for an IDS site. Normalised or fuzzy name matches are candidates only. Unknown links do not erase measured commercial activity.

A multi-site account's quantities remain at account level. Do not duplicate them across site markers. A country or IDS submission cohort does not assign a distributor. ITUK/IUK and UMI/UTI remain separate. UTI does not enter a comparator for the IDS round it did not join.

## Coverage and period contract

CY2025 is historical. Source inventory must separately identify a current recurring dealer feed before a current-month promise. Network totals in 2023/2024/2026 are not a dealer history. Do not allocate those totals backwards or forwards into the CY2025 dealer panel.

A month is complete only with source-backed coverage evidence. No usable observation is `unknown` or `missing_source`, not zero. A confirmed zero requires a source/population definition that makes absence meaningful. Classification absence is `unclassified`; price absence is `unpriced`; identity absence is `unmapped` or `unapproved`, with distinct explanations.

## Tonnage v2 contract

Preserve exclusive-applicability purchasing, modelled expected demand by band and market actuals as distinct views. Pool shared-band/multi-family applicability without allocation. Respect `single_band_only` and the correct `sums_to_n_series_total == "yes"` population; `also_fits_band` is non-additive. Repeated market actuals cannot be summed across bands or divided by one band's expectation to produce band service coverage. Do not add CY and FY.

Read the v2 correction evidence before a regression check. A blocked or stale model remains blocked/stale; no repeated v1 complaint or rebuild without a reproduced need and explicit authorisation.

## Evidence and export contract

Any displayed/exported number retains source version, population, period, basis and exclusions. Use a classification-only dictionary unless further attributes have been explicitly approved. Customer payloads must be scoped before delivery, not merely filtered visually. Return packages use aggregate reconciliations and synthetic examples; private dealer crosswalks and named-detail files remain in the authorised local boundary.

## Financial evaluation, later

Predeclare the supported action, affected population, comparison period and relevant support/cost treatment. Review observed purchasing and ISZE gross profit separately from timing, stock changes, price effects and displacement. Reconcile rebates/support already included in the ledger before adding separate costs. Avoid counting time savings as cash unless there is a documented realised saving, and do not count the same benefit again as contribution.

A before/after view is a monitoring tool. A causal claim requires a defensible comparison and assessment of competing explanations. This package computes no financial return and certifies no commercial outcome.
