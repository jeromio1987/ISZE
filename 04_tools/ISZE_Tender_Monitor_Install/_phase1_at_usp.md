# Phase 1 — Austria USP Ausschreibungssuche

**Date:** 2026-08-25 ~19:32  
**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`

## Verdict

| Metric | Count |
|---|---:|
| API filtered (vehicle CPV window /30d) | **34** |
| Client keyword keepers | **23** |
| Post-normalize / gate (side) | **4** |
| Merged into main | **4** |

## Endpoint

- `GET https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/api/tenderlist`
- Params: `cpvList` (repeated), `fromdate`, `todate`, DataTables paging
- Text `search[value]` **ignored** by server (same honesty as RO)
- Detail: `tender-detail?object=` / `notice-detail?object=` from row[5]

## Wiring

- `fetch_austria_usp` · `--only at` · weekly bat via `run_all`
- `merge_at_into_main.py` · health **Austria USP OK 23**

## Gate honesty

Many CPV hits are Feuerwehr / Kastenwagen — dropped by noise + not-for-us. Keepers are real CV / fleet-shaped rows only.
