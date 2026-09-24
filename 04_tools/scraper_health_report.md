⚠ GENERATED 2026-09-23 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# ISZE SCRAPER HEALTH REPORT — 2026-09-23

Preflight: PASS (tender_scraper_v3.py, ks_scraper.py, 04_tools\ all present). ISZE_ROOT = default `C:\Users\jerom\Desktop\claude\ISZE`.

## Verifier
| Check | Result | Evidence |
|-------|--------|----------|
| Tender JSON ≤14d | PASS | `01_data\14_dashboards\tender_data.json` meta.generated_at = 2026-09-22T17:24Z (~1 day). 689 raw notices / 619 opportunities |
| KS CSV ≤14d | PASS | `ks_results.csv` mtime 2026-09-22 19:55 (~1 day), 300 rows |
| Auto-apply compile | N/A | No edits made |
| Allowlist scope | PASS | Zero files edited |

| Scraper | Status | Last output | Action |
|---------|--------|-------------|--------|
| Tender | 🟢 | 2026-09-22 | none |
| KS pipeline | 🟢 | ks 2026-09-22 · tmc 09-22 · tranzparts 09-22 · mekonomen 09-21 · auto365 09-21 | none |

## Observations (no patch warranted)
1. **KS hit rate flat at 64 / 300 (21% `ok`, 236 `no_results`)**, identical across snapshots 08-24 → 09-22. This is stable, so the scraper is not broken — it's a limit on how many PNs KS covers. Not a selector problem.
2. **Mekonomen**: 7 / 200 rows priced. Low, but this was already the case before this run.
3. **Mekonomen + Auto365 are now skipped on purpose.** `scrape_asof.json` (09-22) says "skipped robots disallow". Their CSVs are the 09-21 copies. They will pass the 14-day check until ~2026-10-05, then show as stale. The refresh log's "5 of 5 sources fresh" line does not know about the skip, so it will be misleading from next week on.
4. **Task spec path is wrong.** The live tender JSON path in the spec, `01_data\dashboards\`, returns an I/O error. The real path is `01_data\14_dashboards\tender_data.json`. I used the real path.
5. Last refresh log (`_logs\refresh_2026-09-21.log`): 0 errors, no drift, 5/5 sources produced rows. There is no log for the 09-22 manual/top300 run in `_logs\`.

## Auto-applied this run
None.

## Proposed (not applied)
None. No `proposed_patch.diff` was written this run. Any existing file there is from an earlier run.

## Manual review
None.

## Waiting on Jerome
1. Mekonomen and Auto365 are skipped because of robots.txt. Decide whether to formally retire them from monitoring (like Autodoc/Oscaro) or have the drift wrapper mark them "skipped". Otherwise they go 🟠 around 5 Oct.
2. Fix the tender path in the task spec: `01_data\dashboards\` → `01_data\14_dashboards\`.
