⚠ GENERATED 2026-08-30 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# ISZE SCRAPER HEALTH REPORT — 2026-08-30

## Verifier
| Check | Result | Evidence |
|-------|--------|----------|
| Tender JSON ≤14d | PASS | `01_data/14_dashboards/tender_data.json` meta.generated_at = 2026-08-25T17:09:55Z → 5.1 days old |
| KS CSV ≤14d | PASS | `04_tools/autodoc_scraper/ks_results.csv` mtime = 2026-08-24 07:20 → 6.5 days old |
| Auto-apply compile | N/A | No allowlisted files edited this run — nothing to compile (all 5 allowlisted scrapers `py_compile` clean as a read-only sanity check anyway: PASS) |
| Allowlist scope | PASS | No Edit calls made this run |

| Scraper | Status | Last output | Action |
|---------|--------|-------------|--------|
| Tender | 🟢 | Weekly run started 24/08/2026 07:30:00, finished 07:33:32 (`tender_monitor_log.txt`); `tender_data.json` itself shows a newer internal `generated_at` of 2026-08-25T17:09:55Z — see note below | none — see Manual review for Israel/Belgium sources |
| KS pipeline (KS/Tranzparts/TMC/Mekonomen/Auto365) | 🟢 | 2026-08-24 07:00–08:42 (`_logs/refresh_2026-08-24.log`) — 0 errors, no price moves ≥15% | none |

**Note on file timestamps:** the ISZE repo was git-checked-out on 2026-08-26 17:57, which resets the OS mtime on every git-tracked file (including `tender_monitor_log.txt` and `tender_data.json`) to the checkout time regardless of when the content was actually produced. Raw `ls` mtimes on tracked files are therefore not reliable evidence of freshness this run — I used the content-embedded timestamps instead (`meta.generated_at` in the JSON, and the `Modified:`/`Done:` lines inside the log). `ks_results.csv` and the other allowlisted CSVs are gitignored (not tracked), so their mtimes are trustworthy as-is. Flagging this as an assumption: I'm treating the JSON's internal `generated_at` (Aug 25, 17:09 UTC) as the true last-publish time even though it postdates the last run logged in `tender_monitor_log.txt` (Aug 24, 07:33) — the gap suggests a manual/interactive rebuild happened outside the scheduled weekly task and didn't write to that log. Either date is well inside the 14-day window, so this doesn't change the PASS verdict, but it's worth Jerome knowing the log and the published file aren't perfectly in sync.

## Auto-applied this run
None.

## Proposed (not applied)
None. No new issues found on the allowlisted scrapers (KS, Tranzparts, TMC, Mekonomen, Auto365) — all five ran clean on 2026-08-24 with 0 errors and no drift, and all five still `py_compile` clean. `proposed_patch.diff` is unchanged from the 2026-08-23 run (still documents why no diff exists).

## Manual review
See `manual_review_required.md` — unchanged from 2026-08-23, both items still open:
1. Israel tender feed (mr.gov.il): still failing with a second XML defect ("mismatched tag: line 53, column 2") after the 2026-08-11 entity-sanitization fix. Confirmed still present in the 2026-08-24 07:30 production run. No web access from this job to inspect the raw feed further.
2. Belgium RSS (publicprocurement.be): still 0 results, both candidate endpoints return non-XML. Unchanged, no new information this run.

## Waiting on Jerome
1. Israel tender feed (mr.gov.il) — needs someone with browser/web access to pull the raw feed and find the actual malformed tag near line 53 before a real patch can be written.
2. Belgium RSS endpoints (publicprocurement.be) — still needs the correct current feed URL; TED continues to cover above-threshold BE contracts meanwhile.
3. FYI only, no action needed: `tender_data.json`'s internal `generated_at` (Aug 25, 17:09 UTC) is newer than the last logged scheduled run in `tender_monitor_log.txt` (Aug 24, 07:33) — looks like a manual rebuild happened outside the weekly scheduled task. Worth confirming that's expected.
