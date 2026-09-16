# IRELAND — Harris Group sales-to-dealer

**Distributor code:** `IRELAND` (Isuzu Ireland / Harris Group — **not** IUK, **not** IMIE)  
**Canonical raw:** `IRELAND_Sales_to_Dealer_2025_2026YTD_Jul.xlsx`  
**SHA256:** `0142039F462B55BFC9F94655181440BEFB51BA1AAAFFB768CE1E9D360A676BED`

## Source email

| Field | Value |
|-------|-------|
| **Received** | 2026-08-13 13:07 (Inbox) |
| **From** | John Cummins `<john.cummins@harrisgroup.ie>` |
| **To** | Jerome Van Der Pluym; Koen Matheussen |
| **Subject** | `RE: Business review` |
| **Native attachment** | `XT - 2026-08-13T114222.149.xlsx` |
| **Body** | “Hi Jerome, See attached.” — reply to Jerome’s 2026-08-10 ask for **sales to dealer from Jan 2025 till 31/07/2026** |

Outlook hunt artefacts: `01_data/90_INBOX/_ireland_sales_mail_20260813/`  
(scan JSON + saved attachments; BO-overview weekly mails are **backorders**, not StD).

## What it is

Line-level **DB → dealer despatch / invoice** extract from Harris.  
No dealer name column → treat as **network PN** after aggregation.  
**Qty only** — no EUR / value columns.

## Native columns

`Item ordered`, `Item supplied`, `Description`, `Orig qty`, `Qty ordrd`, `Qty suppld`,  
`InvoiceDate`, `OrderDate`, `DespatchDate`.

## Normalize rules

- PN = **Item supplied** (actual ship code; ~2.7k lines have ordered ≠ supplied).  
- qty = **Qty suppld** (zero-supplied lines dropped).  
- Period from **InvoiceDate**.  
- Adapter: `01_data/91_build/normalize_dealer_sellout_ireland.py`

## Coverage (source lines)

| | |
|--|--|
| Lines | 42,762 |
| Invoice span | **2025-01-06 → 2026-07-31** (all months present) |
| Qty supplied sum | **80,716** |
| Qty ordered sum | 81,248 |
| Zero-supplied lines | 331 (excluded from long CSV) |

## Normalized outputs

- `01_data/00_derived/dealer_sellout_long_IRELAND_CY2025.csv`
- `01_data/00_derived/dealer_sellout_long_IRELAND_CY2026YTD.csv`

## Caveats

- **≠ IUK** (UK LCV Monthly Demand) and **≠ IMIE** (Isuzu Motors Intl Europe vehicle arm).  
- No dealer split — cannot rank dealers.  
- Vehicle scope unknown (Ireland mixed CV/LCV).  
- Not wired into AIM/GPS sell-out HTML rebuilds until Jerome asks.
