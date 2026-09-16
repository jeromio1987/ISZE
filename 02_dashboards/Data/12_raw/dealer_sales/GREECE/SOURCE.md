# GREECE — Petros sales-to-dealer

**Distributor code:** `GREECE` (PRISM / SAP: PETROS PETROPOULOS)  
**Canonical raw:** `Petros_Parts_Sold_Qties_2025.xlsx`

## Caveats (from Petros)

- Report is **D-MAX parts** sold qty for **calendar 2025**.
- **Column A (`P/No`) is usually the newest part number** (as of 2025 data). Older superseded P/Nos can be **rolled into** the newest code, so they may be “invisible” as separate rows. Flag: `pn_newest_rollup`.
- Quantity only — no dealer split, no EUR.

## Native columns

`P/No`, `Description`, `SUM`, then months `2025-Dec` … `2025-Jan` (newest month first).  
`SUM` = sum of the twelve month columns (checked 2026-08-09: 2,101 rows, all match).

## Normalized output

`01_data/00_derived/dealer_sellout_long_GREECE_CY2025.csv` — one row per PN × month (plus year-total rows with `period_grain=year`).
