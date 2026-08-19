# Applied patches log — scraper healthcheck

Append-only. Each auto-apply from `isze-scraper-healthcheck-autofix` adds a dated block.

Format:
```
## YYYY-MM-DD
- file: <basename>
- change: <one line>
- verifier: py_compile PASS
```

## 2026-08-11
- file: tender_scraper_v3.py
- change: fetch_israel() — wrap ET.fromstring() in a fallback that sanitizes non-standard XML entities (mr.gov.il embeds &nbsp;/&laquo; etc.) and retries once before falling through to the existing except-Exception handler. Untested against the live feed.
- change: corrected the DTVP and BELGIUM_RSS_CANDIDATES comment blocks — both were documented as free/anonymous public feeds; researched 2026-08-11 and confirmed neither exists at no cost (DTVP requires a paid Professional-Edition-or-higher subscription from EUR49/mo for automated alerts; Belgium's e-Notification has no public RSS, only account-based e-mail search profiles). No functional change, comments only.
- mode: interactive, Jerome-approved (not the unattended isze-scraper-healthcheck-autofix skill — this file is propose-only for that skill; applied here at Jerome's explicit "proceed with all fixes" instruction after reviewing the 2026-08-09 health report)
- verifier: py_compile PASS. Backup at tender_scraper_v3.py.bak_20260811.

## 2026-08-11
- file: refresh_and_check_drift.py
- change: fixed the drift-baseline off-by-one diagnosed in manual_review_required.md (2026-08-09 Item 2). prior_paths[csv_name] now uses _snapshot_existing()'s return value directly instead of the separate _latest_prior_snapshot() lookup, which excluded the snapshot just written (dated `stamp`) and so always landed one cycle further back than intended. _latest_prior_snapshot() itself is left in place, unused, in case it's wanted for something else later.
- mode: interactive, Jerome-approved (this file is normally "wrapper, do not edit" even for the scheduled healthcheck skill — edited here directly at Jerome's request after full diagnosis; not a healthcheck auto-apply)
- verifier: py_compile PASS. Logic verified with a standalone synthetic test (temp dir, 3 simulated runs, confirmed NEW logic selects the immediately-prior run's data vs. OLD logic selecting two-runs-back) before touching the real file. Backup at refresh_and_check_drift.py.bak_20260811.
