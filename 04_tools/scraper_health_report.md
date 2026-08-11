⚠ GENERATED 2026-08-09 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# ISZE SCRAPER HEALTH REPORT — 2026-08-09

**Prior run: 2026-08-02.** Good news / real news, in that order: everything monitored is still comfortably fresh and nothing needed a code auto-apply this run. But two things are worth your attention beyond the routine check — this week's scheduled refresh hadn't landed as of this run (not urgent, just later than expected), and I traced a genuine logic bug in the drift-alert baseline that's been double-flagging the same TMC price move since 2026-08-01. Details below; nothing was Edited on disk.

## Verifier

| Check | Result | Evidence |
|-------|--------|----------|
| Tender JSON ≤14d | PASS | `tender_data.json` (`01_data/14_dashboards/`, canonical path per `paths.yaml`) `meta.generated_at`: 2026-08-03T05:33:29.90Z (~6.6 days old) |
| KS CSV ≤14d | PASS | `ks_results.csv` mtime 2026-08-03 07:20 (~6.6 days old). All four other pipeline CSVs (Tranzparts, TMC, Mekonomen, Auto365) refreshed the same morning, cross-confirmed by `_snapshots/2026-08-03/`, matching `drift_history.csv` entries, and `_logs/refresh_2026-08-03.log` (300/300 PNs, 0 errors). |
| Auto-apply compile | N/A | No auto-applies this run — nothing diagnosed on the allowlist was a URL/selector/XPath bug. Ran `py_compile` read-only on all 5 allowlisted scripts plus `tender_scraper_v3.py` as a sanity check anyway — all 6 OK. |
| Allowlist scope | PASS | No Edits made this run — nothing outside or inside the allowlist was touched. |

| Scraper | Status | Last output | Action |
|---------|--------|-------------|--------|
| Tender | 🟢 Fresh (~6.6 days) | `tender_data.json` generated 2026-08-03T05:33:29Z — 747 raw notices, 664 opportunities, 7 in the action queue. Israel/Belgium/DE gaps unchanged (see manual review). | Israel: new fix proposed (`proposed_patch.diff`). Belgium/DE: propose-only, no code fix available — manual review only. |
| Competitive pricing (KS pipeline) | 🟢 Fresh, all 5 sources (~6.6 days) | All five CSVs + `drift_history.csv` refreshed clean 2026-08-03, 0 errors logged. | none — nothing to patch |

### KS pipeline breakdown

| Source | File | Status | Note |
|--------|------|--------|------|
| KS International | `ks_results.csv` | 🟢 Fresh (~6.6 days) | 300/300 PNs processed, 0 errors (log says so explicitly). Mostly `no results` per-PN — expected for parts KS doesn't stock, not an error. |
| Tranzparts (UK) | `tranzparts_results.csv` | 🟢 Fresh (~6.6 days) | Refreshed 2026-08-03 07:20, no drift ≥15%. |
| T&M Commercials (UK) | `tmc_results.csv` | 🟢 Fresh (~6.6 days) | Refreshed 2026-08-03 07:20. Drift check re-flagged `fuel_filter` at -16.6% — **this is a false repeat, not a new move** (see Item 2 in manual review: the underlying price has been flat at £27.32 since 08-01, the drift script's baseline logic is comparing against a stale two-runs-back reference). |
| Mekonomen | `mekonomen_results.csv` | 🟢 Fresh (~6.6 days) | Refreshed 2026-08-03 08:40, no drift ≥15%. Last run's Playwright issue remains resolved. |
| Auto 365 (Israel) | `auto365_results.csv` | 🟢 Fresh (~6.6 days) | Refreshed 2026-08-03 08:41, no drift ≥15%. |

## Auto-applied this run
None. Nothing diagnosed on the allowlisted scripts was a URL/selector/XPath bug — all five ran clean, produced full row counts, and compiled fine as-is.

## Proposed (not applied)
One new diff this run: **Israel RSS undefined-entity fix** for `fetch_israel()` in `tender_scraper_v3.py` — see `proposed_patch.diff`. Untested against the live `mr.gov.il` feed (no web access from this job); please review and test before applying. Belgium RSS remains without a proposed fix — root cause is dead/moved candidate URLs, not parseable XML, so there's nothing to diff without a live lookup for the correct current endpoint.

## Manual review
See `manual_review_required.md` for full detail. Summary:
- **Item 1 (scheduler timing):** this week's competitive-pricing refresh hadn't landed as of this run (22:04 CEST Sun 2026-08-09) — last completed run is still 2026-08-03. Not urgent (6.6 days, well under the 14-day threshold), but the second run in a row flagging scheduler-timing uncertainty; actual historical run times don't cleanly match the documented "Sunday 21:00" trigger.
- **Item 2 (NEW):** `refresh_and_check_drift.py`'s drift-history baseline has an off-by-one — it's comparing each run against data from *two* runs back instead of one, because snapshots are taken before that day's scrape but filed under that day's date. Confirmed by tracing the code (lines 106–114 and 189–192) against the TMC `fuel_filter` false-repeat flag. This file is do-not-edit scope even for proposals, so this is diagnosis-only — fix sketch is in the manual review doc.
- **Item 3 (Israel RSS):** unchanged failure, but now has an actual proposed diff (see above).
- **Item 4 (Belgium RSS):** unchanged, no fix possible without a live URL lookup.
- **Item 5 (NEW, low priority):** Germany DTVP portal 404s on every run, long-standing, not previously tracked as its own item. TED still covers above-threshold DE contracts.
- **Item 6 (Doffin/HILMA):** unchanged, informational only.
- **Item 7 (`scrape_asof.json`):** clarified this run — confirmed orphaned (no script in the repo writes it anymore), not a live pipeline gap. Safe to ignore.

## Waiting on Jerome
1. **This week's refresh timing** — no 2026-08-09 output yet as of this run (last completed: 08-03). Not urgent, but worth 2 minutes in Task Scheduler to confirm `ISZE_ScraperRefresh_WeeklyTask` (and whether it's the same task as `ISZE_PMS_IAM_Refresh` from the last report) is actually enabled and firing — actual run timestamps haven't matched a clean weekly pattern for a while now. (Item 1)
2. **New: drift-alert baseline bug in `refresh_and_check_drift.py`** — real logic bug, not a data problem, traced to a specific off-by-one in the snapshot/comparison code. Do-not-edit file, so I've only diagnosed it, not patched it — see Item 2 for the fix sketch when you're ready to apply it. (Item 2)
3. **Belgium RSS** — both candidate URLs in `tender_scraper_v3.py` are dead or moved (non-XML responses). No code fix possible without the correct current feed URL. (Item 4)
4. **Israel RSS** — first real proposed diff in a while, in `proposed_patch.diff`. Please review and test against the live feed before applying — I can't test it from here. (Item 3)
5. **Low priority / FYI only:** Germany DTVP portal 404s every run (TED covers above-threshold DE), and `scrape_asof.json` is confirmed orphaned and safe to ignore or delete. No action needed on either. (Items 5, 7)
