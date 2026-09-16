# Phase 1 — Denmark udbud.dk (MitUdbud soegning)

**Status:** LIVE (2026-08-25 overnight)  
**Not-for-us:** ON · no invented notices

## Endpoint

- `POST https://udbud.dk/soegning/public/soegeresultat`
- Body schema (`SoegningQueryDto`):
  - `fritekstQuery` (string)
  - `pagineringDto`: `{ aktuelSide >= 1, maksElementer >= 1, sorteringFelt, retning }`
  - `filterDto`: empty arrays OK
  - `udbudStatusFilter`: `AKTIV`
- Response: `resultatElementDtoList[]` with top-level `noticeId` + `dataDa` (titel, ordregiver, cpvKode, publiceringsdato DD-MM-YYYY, tidsfrister[])

## Wiring (standalone — avoid sibling scraper collisions)

| Piece | Path |
|---|---|
| Fetcher | `national_fetchers_dk.py` |
| Focused scrape | `scrape_dk_side.py` → `isuzu_tenders_v3_dk.xlsx` |
| Merge | `merge_dk_into_main.py` → sheet `Denmark udbud` |
| Gate | Nordic truck stems in `isze_core_v3.py` (`lastbil` / `lastebil` / `akslet` / `tippelad`) |

## Yield (this pass)

- Keyword search **lastbil**-first: **6** unique pre-gate → **4** gated → **4** merged
- Passenger el-bil / legetøj / bare køretøj correctly dropped

## Commands

```bat
python scrape_dk_side.py
python merge_dk_into_main.py
python build_dashboard_v4.py
```
