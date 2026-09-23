# Pack status (C04)

inspected_at: 2026-09-21T06:43:45Z

## ITUK dealer + PRISM pack
path: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ITUK_dealer_sales_and_PRISM_2026-09-21`
status: **present** (built 2026-09-21, 20 files per START_HERE)
commercial_level: distributor_to_dealer for sales files; documentation/code extracts for PRISM half
named_dealers: yes on CY2025 detail and dealer aggregates
euro_basis: reference valuation at ISZE billed average where stated in pack notes — not dealer invoice
IDS_join: not solved in this pack (name map still an open Jerome decision)
privacy: real UK dealer names — **excluded from R0 ZIP**

## Tonnage pack v2
path: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920`
status: **present** (v2 corrections dated 2026-09-20/21)
entry: `00_READ_ME_FIRST.md`, correction log, evidence of correction
rule reminder: exclusive band numerator via single_band_only / sums_to_n_series_total; also_fits_band non-additive
pipeline note in correction log: verifier green with 2 warns after stale-model distinction; model not rebuilt

## Superseded
- Tonnage v1 feedback pack referenced by correction log — quarantine from active use; not deleted
- AIM figkey Excel 20260920 superseded for PBI by CSV/XLSX 20260921

## Not exported into R0
- `01_ITUK_sales_to_dealer_CY2025.csv` and other named-dealer detail
- PRISM concatenated source py files (bulk code; cite live paths instead)
- Raw `01_data/raw/sales/*`
