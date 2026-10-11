# P04 — Reconciliation of sales to dealer with billing

> Read `00_START_HERE.md` first. Needs P02. Plan mode, then build.

## Goal
Each month, per distributor: what ISZE **billed**, how much of that is **warranty**, and what was **sold to dealers** in the same months, valued at ISZE's own billed average price per part. The stock movement after warranty is stock, never lost sales.

## Why
Without it a decline looks like lost business. Example in the workspace: Isuzu UK pickup FY2026, billed €5,951,968, warranty €1,335,647, sales to dealer €5,983,188 — not a decline. Rules: `00_docs/ISZE_BI_FRAMEWORK.md` §1 L5, `.cursor/rules/isze-pms-sales-is-sales.mdc`, `isze-israel-uti-umi.mdc`.

## Read first
`03_analytics/Isuzu/prism/scripts/build_billed_vs_std_warranty_fy.py` (the pattern), `01_data/00_derived/billed_vs_std_warranty_fy2026.csv`, `distributor_warranty_expense_fiscal.csv`, `ISZE_BI_FRAMEWORK.md`.

## Build
`04_tools/partner_intake/reconcile.py` + CLI `reconcile --distributor X --months 2027-04..2027-06`.
- Inputs: canonical long CSV (quantities), `sales_fact.parquet` (billing, parts only, credit notes/transport/rebate excluded as in the pipeline), warranty from the fiscal warranty CSV. **Do not read raw billing extracts.**
- Value each part's sold quantity at the distributor's median billed unit price in the same fiscal year; parts without a billed price stay **quantity-only and are reported as uncovered** (never valued at zero silently).
- Output three lines (billed, warranty, sales to dealer), the stock movement, the share of sales-to-dealer quantity with no billed price, and the months covered. Warranty is **not** pro-rated when the sales-to-dealer file covers fewer months than billing: compare the **same months** and say so.
- Tolerance and "uncovered share" thresholds in config. Output CSV + Markdown.
- Never blend UTI/UMI or IUK/ITUK. Fiscal-year helpers from `03_analytics/Isuzu/prism/modules/fiscal.py`.

## Acceptance tests
1. Reproduce the Isuzu UK pickup FY2026 line above from the existing derived files (billed, warranty, sales to dealer) to the euro.
2. A synthetic case with known totals reproduces to the euro, including a part with no billed price (reported as uncovered, not valued).
3. A distributor with 9 months of sales to dealer is compared with the same 9 months of billing; warranty is shown in full and a note says it is not pro-rated.
4. Output never contains a piece-count headline.
5. PRISM suite passes; no derived file used as input is modified.

## Return packet
Reproduction table, uncovered-share per distributor on real derived files (aggregate numbers only), open questions.
