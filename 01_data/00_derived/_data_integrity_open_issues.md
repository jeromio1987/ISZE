# Data integrity — open issues

**Updated:** 2026-08-18

Pipeline verification: **green** (see `_verification_report.md`). Items below are **source gaps** or **known limitations**, not build failures.

Jerome warranty rule locked **2026-07-27** (`01_data/90_INBOX/warranty_audit_2026-07-27/SANITY.md`): skip PARTNBR `0` / `0000000000` (labour, not parts); do not chase price-map for no-PN rows; no multi-month blackout on high-volume DBs → not “data missing” for GPS CY2025 parts warranty.

## Cannot fix without new source data

| ID | Issue | Period | Impact | Action owner |
|---|---|---|---|---|
| **LCV-DEC** | `Warranty_LCV_2025.xlsx` last claim month is **November 2025** (IUK 2024-11 → 2025-11; Portugal LCV 2025-01 → 2025-11) | **December 2025 onward** | Full-CY LCV from *this* file is incomplete by one month at the end. GPS CY2025 used the extract as-is. | Next LCV claim-assessment export |

## Closed — do not re-open as GPS gaps

| ID | What it looked like | What it actually is | Period |
|---|---|---|---|
| **UMI-WARR** | Israel LCV absent from `Warranty_LCV_2025.xlsx` | **Resolved 2026-07-03.** Dedicated file `UMI warranty data 202301 - 202605 (1).xlsx` spans **2022-12-18 → 2026-05-17**; CY2025 Jan–Dec continuous (€1,791,020). Do not use the LCV workbook for UMI. | CY2025 complete |
| **CV-BLANK** | Sheet4 €314k “blank country” | **Parse artifact (2026-07-27).** PARTNBR `0` sorts before real PNs under each country. Line-level 3,083 blank-PN rows = labour (PARTAMT €0, LBRAMT €110,995). Skip. Find the euros on `DATA WITHOUT MIDI`, valid PN only. | CY2025 BILLYMD; Nov–Dec 2025 CV in sister `CV Warranty.xlsx` sheet `10_25-12_2025` (2025-09-18 → 2025-12-17) |
| **IRE-CV / PT-CV** | 82% / 52% price-map | Not missing claims. Optional valuation — 1 Ireland + 42 Portugal **real** PNs unpriced (labour/no-PN skip). | CY2025 CV |

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
| Competitiveness IAM scrape | No data-as-of stamp — scrape may be stale. PartsPool Autodoc DE/NO is 2026-03-29, not Eucon UK 2023. |
| Streamlit `pages/2_GPS.py` | Live calc without warranty toggle — use GPS v9 HTML or Evidence `/gps` |
| Streamlit `pages/10_Data_Integrity.py` | **DI-2 / DI-8 refreshed 2026-08-18** — canonical UIO is v19; AIM CY2026 dashboard shipped 2026-07-02. Duplicate-path cross-check and country-pack vintage labels remain. |

## Fixed this session

- GPS warranty wired into `gps_spu_by_distributor.csv` + `isze_data.json`
- PMS per-DB summary for 18 distributors
- Broken `v11` UIO links → `v18`
- Superseded GPS HTML → redirect to v9
- UIO v17 → redirect to v18 (full file in `Dashboards/_archive/`)
