# P05 — Quarterly eligibility and discount proposal

> Read `00_START_HERE.md` first. Needs P02, P04. Plan mode, then build.

## Goal
Every quarter: apply the level-1 gates to each distributor, write an eligibility table with evidence, and compute a **proposed** credit per eligible distributor. Nothing is posted anywhere; people decide and post.

## Read first
Spec §9 (gates G1–G7), §10 (discount proposal). `Excellence_Partner_ROI_Model_2026-10-09.xlsx` sheets Inputs and Design_variants (the arithmetic of the hybrid designs). White paper chapters 5.2, 5.3, 5.6, 5.7.

## Build
`04_tools/partner_intake/eligibility.py`, `discount.py`, config `partner_program.yaml` sections `gates`, `levels`, `designs`.
- Gate results per distributor and quarter: `ELIGIBLE`, `NOT_ELIGIBLE` (failing gates listed), `MANUAL_REVIEW`, `EXEMPT` (reason). G6 is `NOT_APPLICABLE` when no IDS round was planned for that distributor — never a failure. A single late file (≤5 days) is tolerated once per year, configurable.
- `overrides.csv` (distributor, quarter, decision, reason, approver, date) is read last and is the only way to change a result; every override is shown in the output.
- Discount proposal from `sales_fact.parquet` stock-order (SaTy `SOR`) lines of the quarter; warranty lines excluded behind a config switch (default exclude; **open decision**, record it in the return packet); base capped at 120% of the trailing four-quarter average (config).
- Designs selectable by config: `deck_flat`, `growth_only`, `hybrid_small` (default), `hybrid_bigger`, `tiered`. Hybrid = flat rate on the base plus a **marginal** bonus per growth band (each band's rate applies only to the stock orders inside the band), growth measured against the same quarter last year. Use the rates in the ROI model's Inputs sheet as defaults.
- Output `eligibility_<FY>Q<n>.csv` + `.md` and `discount_proposal_<FY>Q<n>.csv` with the arithmetic per distributor (base, cap applied, flat part, each band, total). Recommended route: credit note; no invoice-condition output unless config says so.

## Acceptance tests
1. Fixture with three distributors: one eligible, one failing G1, one with no IDS round planned → results and failing-gate lists asserted.
2. Override changes a result and is visible in the output.
3. Hybrid arithmetic: a fixture with known stock orders and growth in each band reproduces the expected credit to the cent; marginal (not cliff) behaviour asserted by testing growth just below and just above a band limit.
4. Cap at 120% applies and is shown.
5. Cross-check: an `expected_cost(plan)` helper that uses the same method as the model (growth of each distributor normally distributed, mean = planned growth 5%, spread 13.8%) reproduces the model's Year-3 `hybrid_small` cost (Design_variants, about €295k) within 1%. This checks the arithmetic, not a forecast.
6. UTI/UMI and IUK/ITUK are separate rows. CIS markets excluded.
7. No file is written outside `01_data/00_derived/partner_intake/`.

## Out of scope
SAP posting, mail, invoice conditions, level-2 scoring (a later prompt).

## Return packet
The two output files for the fixture, the open decision on warranty, anything where the model and the spec disagree.
