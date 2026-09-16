# Phase 1 — Germany oeffentlichevergabe Open Data (national)

**Date:** 2026-08-25  
**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Constraint:** Same Isuzu gate + **not-for-us** hard-drop (postal/panel vans out). Null ≠ 0. No invented notices. Criticality labels preserved. Nordics keys separate track.

---

## Verdict

| Portal | Result |
|---|---|
| **#3 oeffentlichevergabe.de Open Data** (BKMS / Bekanntmachungsservice) | **LIVE** |
| service.bund RSS | Still OK (PARTIAL crumb; sheet thin in main) |
| DTVP free RSS | Still **RETIRED** (404 / paid Professional) |

Official Open Data: `GET /api/notice-exports` with `pubMonth` or `pubDay` + `format=csv.zip` (also eForms/OCDS). API rejects today/future `pubDay`.

---

## Pipeline

1. Focused scrape: `python tender_scraper_v3.py --only ov` → `isuzu_tenders_v3_de.xlsx`
2. Merge: `merge_de_into_main.py` — re-gate + dedupe; does not wipe Germany National when side empty
3. Publish: `publish_live_tender_json.ps1`
4. Rebuild: `build_dashboard_v4.py` (criticality hero / six tabs / CV default / Aftersales / IDS / IT PNCP / not-for-us)

---

## Counts (measured 2026-08-25)

### Germany oeffentlichevergabe

| Metric | Count |
|---|---:|
| Months fetched | 2026-07 + 2026-08 csv.zip |
| Notices scanned | ≈44,655 |
| Pre-gate vehicle CPV/keyword | **545** |
| Post-`normalize_batch` / Isuzu + not-for-us gate | **41** |
| Merge re-gate drop | **0** |
| Merged into main (`Germany OV`) | **41** |
| Cross-sheet URL/ID dupes skipped | **0** |

### Main feed (after merge + v4 rebuild)

| Metric | After DE OV |
|---|---:|
| Notices | **249** |
| Opportunities | **224** |
| Stated fleet pickup/truck | **163** (Germany extract-heavy; not market potential) |
| Stated fleet all segments | **176** |
| Aftersales tagged | **42** of 224 |
| `lcv_van` on desk | **3** (parts-only survivors — not postal van buys) |
| Italy PNCP | **2** preserved |
| Spain PLACSP | **0** (CODE_READY / WAF) |

**Honest read:** DE national notice lift is real (545→41 after gate). Stated-fleet hero jumps because several DE notices publish large fleet counts — still **stated in captured notices**, not addressable market. DTVP procedure hosts remain paid.

---

## Wiring

| Piece | Path / flag |
|---|---|
| Fetcher | `fetch_germany_ov` in `tender_scraper_v3.py` |
| Focused | `--only ov` · `--only de` (bund+OV) · `--only de-ov` |
| Merge | `merge_de_into_main.py` |
| Health | `_source_health.json` — **Germany oeffentlichevergabe OK 545** |
| Side xlsx | `isuzu_tenders_v3_de.xlsx` |
| UI notice URL | `https://oeffentlichevergabe.de/ui/de/notice/{uuid}` |

## Endpoint used

- `https://oeffentlichevergabe.de/api/notice-exports?pubMonth=YYYY-MM&format=csv.zip`
- Tables: `notice.csv` + `purpose.csv` + `classification.csv` + `organisation.csv`
- Filter: surgical CPV / 3413·5011 prefixes **or** DE vehicle stems with vehicle-family CPV
- Not used: DTVP RSS (RETIRED)

---

## Criticality + not-for-us preserved

- Hero: **Stated fleet in captured notices (pickup/truck)** — not market potential
- Three layers: ~20k LCV / ~78k CV ≠ CV tenders ≠ stated units
- Six tabs · CV default filter · Aftersales · IDS · IT PNCP
- Postal/courier panel vans hard-dropped (`_NOT_FOR_US_GATE.md`)

---

## Deliverables

- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_phase1_de_national.md` (this file)
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_phase1_de_merge_stats.json`
- `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3_de.xlsx`
- Overnight: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_OVERNIGHT_RUNLOG.md`
