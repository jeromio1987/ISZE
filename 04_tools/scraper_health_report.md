⚠ GENERATED 2026-10-18 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# ISZE SCRAPER HEALTH REPORT — 2026-10-18

## Verifier
| Check | Result | Evidence |
|-------|--------|----------|
| Tender JSON ≤14d | FAIL (unverifiable) | `01_data/dashboards` (symlink) returns "Input/output error" in this sandbox; tender_data.json could not be read, so `meta.generated_at` is unknown. No other copy found. Indirect: tender_price_context.meta.json built_at 2026-10-02 (16d, derived file, not proof). |
| KS CSV ≤14d | PASS | ks_results.csv modified 2026-10-12 05:12 (6 days); tmc_results.csv 2026-10-12 |
| Auto-apply compile | N/A | No edits made. Read-only py_compile of all 5 allowlisted scrapers: OK |
| Allowlist scope | PASS | No Edit attempted anywhere |

| Scraper | Status | Last output | Action |
|---------|--------|-------------|--------|
| Tender | 🟠 unknown (access error, not a confirmed stale) | unreadable | none (propose-only; nothing to patch) |
| KS pipeline | 🟢 | ks 2026-10-12, tmc 2026-10-12 | none |
| Tranzparts | 🟠 info | 2026-09-22 (26d) | none — not in primary 14d check; wrapper last run (10-12) refreshed only KS+TMC |
| Mekonomen / Auto365 | 🟠 info | 2026-09-21 | none — deliberately skipped (robots disallow, per scrape_asof.json) |

Weekly refresh logs present through 2026-10-12; a 2026-10-19 run is expected tomorrow.

## Auto-applied this run
None

## Proposed (not applied)
None

## Manual review
None new.

## Waiting on Jerome
1. Tender JSON freshness could not be checked: the `01_data/dashboards` link is unreadable from the cloud sandbox. Please confirm `meta.generated_at` in tender_data.json is within 14 days (or check the local tender scheduled task).
2. Tranzparts last refreshed 2026-09-22; confirm whether it should be in the weekly wrapper run.
