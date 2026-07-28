⚠ GENERATED 2026-07-27 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# ISZE SCRAPER HEALTH REPORT — 2026-07-27

**Prior real run: 2026-07-19** (the 2026-07-26 file timestamps on this report/manual-review/diff were a bulk touch, not a regenerate — content was still the 07-19 text). This is the first run under the 2026-07-24 allowlist auto-apply policy. No auto-apply was needed this run — nothing diagnosed was a string-only URL/selector bug.

## Verifier

| Check | Result | Evidence |
|-------|--------|----------|
| Tender JSON ≤14d | PASS | `tender_data.json` `generated_at`: 2026-07-21T05:06:05Z (6 days old) |
| KS CSV ≤14d | PASS | Mid-refresh at check time (Monday 07:00 scheduled run `ISZE_PMS_IAM_Refresh`), 119/300 rows written by 07:08:36, 0 errors so far. Prior complete file was 2026-07-26 (manual run, 300/300, 0 errors). |
| Auto-apply compile | N/A | No auto-applies this run (nothing needed patching). Ran `py_compile` read-only on all 5 allowlisted scripts as a diagnostic sanity check — all 5 OK. |
| Allowlist scope | PASS | No Edits made this run — nothing outside or inside the allowlist was touched. |

| Scraper | Status | Last output | Action |
|---------|--------|-------------|--------|
| Tender | 🟢 Fresh (6 days) | `tender_data.json` generated 2026-07-21T05:06:05Z. Israel RSS and Belgium RSS still fail every run (unchanged since 2026-06-28) — partial, not total, data loss. | none (propose-only scope; carried-forward manual review) |
| Competitive pricing (KS pipeline) | 🟢 Fresh overall, with one exception | See breakdown below — 4 of 5 sources fresh and clean; Mekonomen's data is still inside the 14-day window but the scraper itself is confirmed broken. | none auto-applied — see manual review |

### KS pipeline breakdown

| Source | File | Status | Note |
|--------|------|--------|------|
| KS International | `ks_results.csv` | 🟢 Fresh — refreshing now | Monday 07:00 scheduled run in progress at time of this check (119/300 rows, 0 errors so far). Prior full run 2026-07-26: 300/300, 0 errors. |
| Tranzparts (UK) | `tranzparts_results.csv` | 🟢 Fresh (<1 day) | Refreshed 2026-07-26 21:50 — 20 priced products, 0 errors. |
| T&M Commercials (UK) | `tmc_results.csv` | 🟢 Fresh (<1 day) | Refreshed 2026-07-26 21:50 — 38 priced products, 0 errors. |
| Auto 365 (Israel) | `auto365_results.csv` | 🟢 Fresh (<1 day) | Refreshed 2026-07-26 21:52 — 204 priced products, 0 errors. |
| Mekonomen | `mekonomen_results.csv` | 🟢 data (11 days) / 🔴 scraper broken | Playwright browser executable missing — crashed on 2026-07-26 21:xx attempt (full traceback in manual review). Pipeline correctly kept the last-good file rather than overwriting with empty data. Data will breach the 14-day window ~2026-07-30 if not fixed. |

## Auto-applied this run
None. No allowlisted script had a URL/selector/XPath bug — KS/Tranzparts/TMC/Auto365 ran with 0 errors, and Mekonomen's failure is an environment issue (missing browser binary), not a string fix, so it doesn't qualify even though the file is on the allowlist.

## Proposed (not applied)
None new — see `proposed_patch.diff`. Israel RSS and Belgium RSS fixes remain suggested-but-untested (unchanged since 2026-06-28, still need a live-feed smoke test this job can't perform without web access).

## Manual review
See `manual_review_required.md` — full detail on all items. Summary:
- **Item 1 (new, time-sensitive):** Mekonomen — Playwright browser executable missing. Fix is a `playwright install` + possible `PLAYWRIGHT_BROWSERS_PATH` check, not a code patch.
- **Item 2 (new):** `ISZE_PMS_IAM_Refresh` scheduled task was interrupted (`0xC000013A`) last Monday (2026-07-20); today's run was still in progress when this check completed — unconfirmed whether it finished cleanly.
- **Items 3–5 (carried forward, unchanged since 2026-06-28):** Israel RSS undefined-entity parse error, Belgium RSS non-XML response, Doffin/HILMA API keys unset (informational only).
- **Item 6 (new, minor):** `tender_monitor_log.txt` doesn't cover the 2026-07-21 publish that's actually live.
- **Resolved since 2026-07-19:** prior Items 10a/10b (KS refresh-path ambiguity, Task Scheduler import unverified) are both now confirmed — `refresh_and_check_drift.py` runs all five scrapers as one unit, and `ISZE_PMS_IAM_Refresh` is confirmed registered and live.

## Waiting on Jerome
1. **Mekonomen scraper is broken** (missing Playwright browser) — run `C:\Python314\python.exe -m playwright install chromium`; if it fails again, check for a `PLAYWRIGHT_BROWSERS_PATH` env var pointing at a Cursor sandbox temp folder. Data goes stale ~2026-07-30 if untouched. (manual_review_required.md Item 1)
2. **Check Task Scheduler settings for `ISZE_PMS_IAM_Refresh`** — last week's run was interrupted mid-way; today's run was still going when I checked. Worth confirming "run whether logged on or not" / wake-on-run settings, and separately confirming today's run actually finished (glance at `_logs/refresh_2026-07-27.log` — should end with a drift-check summary, not cut off mid-scrape). (Item 2)
3. **Israel RSS / Belgium RSS in `tender_scraper_v3.py`** — unchanged since 2026-06-28, still returning zero results every run. Suggested fixes are on file (Items 3–4) but need a live-feed test I can't run.
