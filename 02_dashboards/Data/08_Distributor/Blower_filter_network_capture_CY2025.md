# Blower / cabin filter capture — network check (CY2025)

**Filed:** 2026-07-26 · Updated same day: factor **0.25 → 1.0** (Jerome)  
**Related:** `03_analytics/Isuzu/prism/docs/pms_service_intervals.md` · `data/pms_capture_assumptions.yaml`  
**Portugal km:** `01_data/08_Distributor/Portugal_annual_km_mileage.md`

## Factor decision (locked)

**Wrong:** `blower_filter: 0.25` (implicit ~once / 100k cabin assumption).  
**Correct (PRISM network, all DBs):** `blower_filter: 1.0` — **same as oil / fuel / urea** (one element per addressable service).

- Source of the old 0.25: modelling placeholder only — not IML, not ITUK measured, not IMG mileage.
- **ITUK pilot / Model B lane:** unchanged (do not touch `pms-pilot` / IML v7 ITUK artefacts).

After pipeline rebuild, expected blower qty rises ~4× vs the 0.25 model; capture % falls accordingly. Numbers in the table below are the **pre-fix** CY2025 snapshot (0.25 denominator) kept for history.

## Pre-fix snapshot (CY2025 total, factor 0.25) — historical

| DB | Capture | Actual qty | Expected qty |
|----|--------:|-----------:|-------------:|
| ROMANIA | 608% | 570 | 94 |
| SWEDEN | 500% | 3,694 | 739 |
| FINLAND | 489% | 515 | 105 |
| CYPRUS | 384% | 775 | 202 |
| ICELAND | 377% | 134 | 36 |
| NORWAY | 353% | 2,450 | 694 |
| GREECE | 269% | 882 | 327 |
| BELGIUM | 263% | 2,211 | 839 |
| DENMARK | 261% | 194 | 74 |
| HUNGARY | 255% | 832 | 327 |
| MALTA | 251% | 228 | 91 |
| **PORTUGAL** | **231%** | **1,456** | **631** |
| GERMANY | 138% | 1,659 | 1,206 |
| IRELAND | 108% | 205 | 189 |
| IUK | 105% | 8,790 | 8,362 |
| **UMI** | **4%** | **130** | **3,245** |
| ITUK | 0% | 0 | 1,959 |
| UTI | 0% | 0 | 904 |

**15 of 18 DBs > 100%** under 0.25 — denominator artefact, not Portugal overselling.

## Portugal km (filed)

- **IMOTORS LDA ≈ 22,742 km/yr** (IMG `EU Mileage.xlsx`, 1,596 VINs)  
- Files: `EU_Mileage_by_country_IMG_2020-11_to_2026-06.xlsx`, `Portugal_annual_km_mileage.md`  
- Scope: LCV VIN sample — not N75 R&M confirmation
