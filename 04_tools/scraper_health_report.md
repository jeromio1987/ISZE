⚠ GENERATED 2026-10-04 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# ISZE SCRAPER HEALTH REPORT — 2026-10-04

## Verifier
| Check | Result | Evidence |
|-------|--------|----------|
| Tender JSON ≤14d | PASS | `01_data\14_dashboards\tender_data.json` meta.generated_at = 2026-09-28T05:51:57Z (~6 days old) |
| KS CSV ≤14d | PASS | `04_tools\autodoc_scraper\ks_results.csv` mtime 2026-09-28 05:20 (~6 days old) |
| Auto-apply compile | N/A | No patches applied — nothing Edit'd |
| Allowlist scope | PASS | No files Edit'd this run |

| Scraper | Status | Last output | Action |
|---------|--------|-------------|--------|
| Tender | 🟢 | tender_data.json — 2026-09-28 (~6d) | none |
| KS pipeline | 🟢 | ks_results.csv — 2026-09-28 (~6d) | none |
| Tranzparts | 🟢 | 2026-09-22 (~12d, inside 14d window; watch) | none |
| TMC | 🟢 | 2026-09-28 (~6d) | none |
| Mekonomen | 🟢 | 2026-09-21 (~13d, inside 14d window; watch) | none |
| Auto365 | 🟢 | 2026-09-21 (~13d, inside 14d window; watch) | none |

## Auto-applied this run
None.

## Proposed (not applied)
None.

## Manual review
None new. Note: `01_data\dashboards` is still a dangling link (I/O error); live data is at `01_data\14_dashboards` (not in scope). Existing `manual_review_required.md` left untouched.

## Waiting on Jerome
1. Nothing blocking. Mekonomen/Auto365 CSVs (21 Sep) and Tranzparts (22 Sep) will cross the 14-day window on 5–6 Oct if the weekly refresh doesn't update them (the 28 Sep refresh only touched KS/TMC).
