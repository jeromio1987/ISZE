# Data integrity — open issues

**Updated:** 2026-07-23

Pipeline verification: **green** (see `_verification_report.md`). Items below are **source gaps** or **known limitations**, not build failures.

## Cannot fix without new source data

| ID | Issue | Impact | Action owner |
|---|---|---|---|
| **UMI-WARR** | Israel LCV absent from `Warranty_LCV_2025.xlsx` (`DistributorName` has no Israel/UMI rows) | UMI ex-warranty GPS overstated; `warranty_data_gap=true` | ISZJ claim export / warranty team |
| **CV-BLANK** | CV warranty `Sheet4` has €314K under blank country bucket | Ireland/Portugal CV warranty are lower bounds | Source file cleanup in claim pivot |
| **IRE-CV** | Ireland CV warranty 82% price-map coverage | CV component undercounted | Accept or re-price from ITUK map |
| **PT-CV** | Portugal CV warranty 52% price-map coverage | CV component undercounted | Same as above |

## Out of PMS/GPS exercise scope (by design)

| Market | Why |
|---|---|
| UKRAINE, ARMENIA, KAZAKHSTAN, PALESTINE | Bill parts but not in 18-db GPS-base / PMS parc config |
| MIDI (FR, IT, ES…) | LCV warranty in file but not separate GPS calculator rows |

## Dashboard / feed staleness (monitor)

| Item | Status |
|---|---|
| `tender_data.json` | Refresh via `04_tools/ISZE_Tender_Monitor_Install/publish_tender.ps1` when tenders needed |
| `metrics_snapshot.json` | Run `build_metrics_snapshot.py` after pipeline post-verify |
| Competitiveness IAM scrape | No data-as-of stamp — scrape may be stale |
| Streamlit `pages/2_GPS.py` | Live calc without warranty toggle — use GPS v9 HTML or Evidence `/gps` |

## Fixed this session

- GPS warranty wired into `gps_spu_by_distributor.csv` + `isze_data.json`
- PMS per-DB summary for 18 distributors
- Broken `v11` UIO links → `v18`
- Superseded GPS HTML → redirect to v9
- UIO v17 → redirect to v18 (full file in `Dashboards/_archive/`)
