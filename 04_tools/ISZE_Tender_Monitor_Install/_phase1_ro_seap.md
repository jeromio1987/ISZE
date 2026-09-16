# Phase 1 — Romania SEAP / e-licitatie (overnight)

**Date:** 2026-08-25  
**Install:** `C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\`  
**Constraint:** Isuzu gate + **not-for-us** (postal utilitare out). Null ≠ 0. No invented notices.

---

## Verdict

| Portal | Result |
|---|---|
| **SEAP e-licitatie** `api-pub/NoticeCommon/GetCNoticeList` | **LIVE** |

API ignores title/CPV query fields — paginate by `startPublicationDate`/`endPublicationDate` and filter client-side.

---

## Counts

| Metric | Count |
|---|---:|
| API window notices | ≈2243 |
| Pre-gate vehicle CPV/keyword | **147** |
| Post-normalize / Isuzu + not-for-us | **13** |
| Merged into main | **13** |

### Main after merge

| Metric | Value |
|---|---:|
| Notices | **262** |
| Opportunities | **237** |
| Stated fleet pickup/truck | **163** (unchanged — RO rows no new extract-heavy fleets) |
| Aftersales | **45** |
| `lcv_van` on desk | **3** (parts-only) |

---

## Wiring

- `fetch_romania_seap` · `--only ro` · `merge_ro_into_main.py`
- Health: **Romania SEAP OK 147**
- Side: `isuzu_tenders_v3_ro.xlsx`
