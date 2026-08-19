# IUK — Monthly Demand (sales-to-dealer qty)

**Distributor code:** `IUK` (UK LCV / D-Max — **not** ITUK CV trucks)  
**Canonical raw:** `IUK_Monthly_Demand_2025_2026YTD_July.xlsx`  
**Received:** 2026-08-12 (dropped at `01_data/` root as `IUK Monthly Demand - July 2026 - Copy.xlsx`; re-filed here).  
Mailbox copy 2026-08-11 Inbox (`Re: Sales to dealer data` / `IUK Monthly Demand - July 2026.xlsx`) is **SHA-identical** — not re-filed.

## What it is

Network-level **part × month quantity** demand / sell-out style report from IUK.  
No dealer split. Vehicle scope treated as **D-MAX / LCV**.

**EUR — locked (Jerome 2026-08-12):** IUK is **qty-only by design**. Do **not** ask IUK for € / value. UK sell-out **value** comes from **ITUK only** (CV). Keep `qty_only` flag permanently.

## Sheets

| Sheet | Period | Notes |
|-------|--------|-------|
| `2025 - Complete` | CY2025 Jan–Dec | Full calendar year |
| `2026 - To July end` | CY2026 Jan–Jul | Partial year (`partial_year`); Aug–Dec are zero placeholders |

## Native columns

`Part Number`, `Desc`, `JAN`…`DEC`, `Average` / `Monthly Average`, `Total` / `Yearly Total`.  
`Total` = sum of active month columns (checked 2026-08-12). Average columns are **not** ingested.

## Normalized outputs

- `01_data/00_derived/dealer_sellout_long_IUK_CY2025.csv`
- `01_data/00_derived/dealer_sellout_long_IUK_CY2026YTD.csv`

Adapter: `01_data/91_build/normalize_dealer_sellout_iuk.py`

## Caveats

- Filename says **Monthly Demand** — treat as DB→DLR qty layer for analytics; confirm with Jerome if any rows are forecast rather than sold.
- Do **not** blend with ITUK sell-out (`Sales to Dealers_ITUK_CY2025.xlsx`).
- Missing EUR is **not a gap** — see locked note above.
- Not yet wired into ITUK/UTI AIM-GPS HTML rebuilds (same status as GREECE/Petros) until Jerome asks.
