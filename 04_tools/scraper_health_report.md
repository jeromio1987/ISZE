⚠ GENERATED 2026-09-27 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# ISZE SCRAPER HEALTH REPORT — 2026-09-27

## Verifier
| Check | Result | Evidence |
|-------|--------|----------|
| Tender JSON ≤14d | PASS | `01_data\14_dashboards\tender_data.json` meta.generated_at = 2026-09-22T17:24:26Z (~5 days old) |
| KS CSV ≤14d | PASS | `04_tools\autodoc_scraper\ks_results.csv` mtime 2026-09-22 17:55 (~5 days old) |
| Auto-apply compile | N/A | No patches met all auto-apply gates this run — nothing was Edit'd |
| Allowlist scope | PASS | No files Edit'd this run (in or out of allowlist) |

| Scraper | Status | Last output | Action |
|---------|--------|-------------|--------|
| Tender | 🟢 | tender_data.json — 2026-09-22T17:24:26Z (~5d) | none |
| KS pipeline (ks) | 🟢 | ks_results.csv — 2026-09-22 17:55 (~5d) | none |
| Tranzparts | 🟢 | tranzparts_results.csv — 2026-09-22 17:28 (~5d) | none |
| TMC | 🟢 | tmc_results.csv — 2026-09-22 17:28 (~5d) | none |
| Mekonomen | 🟢 | mekonomen_results.csv — 2026-09-21 06:42 (~6d) | none |
| Auto365 | 🟢 | auto365_results.csv — 2026-09-21 06:43 (~6d) | none |

## Auto-applied this run
None.

## Proposed (not applied)
None. All monitored outputs are within the 14-day freshness window, so no diagnosis or patching was triggered this run.

## Manual review
None new this run. Note: `01_data\dashboards` and `01_data\Tender` appear to be broken/dangling symlinks (readlink failed, "Input/output error" on ls) — likely stale shortcuts left over from a folder rename to `01_data\14_dashboards` / `01_data\10_Tender`. Not in scope to fix (data path, not an allowlisted scraper script), flagging for awareness only. See existing `manual_review_required.md` for any carried-over items from prior runs (left untouched — nothing new to add).

## Waiting on Jerome
1. Nothing blocking — all monitored scrapers (Tender + KS/Tranzparts/TMC/Mekonomen/Auto365) are fresh (≤6 days old, well inside the 14-day window). No action needed this run.
