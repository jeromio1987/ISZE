# P07 — Internal monitoring page

> Read `00_START_HERE.md` first. Needs P02, P04. Plan mode, then build.

## Goal
One internal page for Jerome: which files are due, received, late or invalid; who sends per-dealer detail; the quarter-end share of stock orders (forward-buying alarm); the order-type shift per distributor and quarter.

## Read first
Spec §12. `Excellence_Partner_White_Paper` chapters 5.7 and 7.3. Pattern for internal pages: `02_dashboards/ops/` and `.cursor/rules/isze-dashboards.mdc`, `isze-html-openable.mdc`.

## Build
`04_tools/partner_intake/monitor.py`, CLI `monitor build`. Self-contained HTML (internal, `02_dashboards/ops/` is the convention but **do not write there**; write to `09_meetings/Excellence_Partner_Program_2026/monitor/` and let Jerome decide).
- Table: distributor × month: due date, received, ON_TIME/LATE, state, errors, warnings, grain (dealer/network).
- Forward-buying alarm: share of stock-order euros booked in the last month of each quarter per distributor, against the network norm (FY2026: 31.8% against 25% if even) and the programme-wide trend. Source: `sales_fact.parquet`, SaTy `SOR`, in-scope distributors.
- Order-type mix per quarter: SOR, VOR, rush, PRD (meaning of PRD is an open question; label it as such).
- Everything labelled with period and source. Internal language allowed, but no invented jargon.

## Acceptance tests
1. Reproduce for FY2026: in-scope stock orders €22.38M of €31.78M (70.4%); quarter-end share 31.8%. Assert both from `sales_fact.parquet`.
2. A late file and an invalid file in the fixture appear in the right cells.
3. Rendered check at 1280 and 390 px with screenshots read.
4. No fetch of sibling files; opens by double-click.

## Return packet
Screenshots, the FY2026 reproduction, open question on PRD.
