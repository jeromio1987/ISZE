⚠ REQUIRES JEROME REVIEW — DO NOT AUTO-APPLY. Generated 2026-07-19 by isze-scraper-healthcheck-autofix.

# ISZE SCRAPER HEALTH REPORT — 2026-07-19

Diagnose-and-propose only. Nothing below has been applied.

**Prior run: 2026-07-12.** Both previously-broken scrapers are now healthy. This is a clean run — no diagnosis, no new patch, one small housekeeping action below.

| Scraper        | Status | Last output | Diagnosis | Artifact |
|----------------|--------|-------------|-----------|----------|
| Tender Scraper | 🟢 Fresh (3 days) | JSON `meta.generated_at`: 2026-07-16T11:36:34Z. Two successful runs that day (10:56 and 13:33). | The 2026-07-12 root-cause fix (dead Task Scheduler path) is confirmed working — the 44-day outage is over. Israel RSS and Belgium RSS still fail on every run (unchanged, see below) — partial, not total, data loss. | None needed |
| Competitive pricing (KS pipeline) | 🟢 Fresh | `ks_results.csv` / `mekonomen_results.csv`: 2026-07-16 (3 days). `tranzparts_results.csv` / `tmc_results.csv` / `auto365_results.csv`: 2026-07-13 (6 days). All within the 14-day weekly window. | Code intact. See housekeeping note below on how ks/mekonomen got refreshed. | None needed |

## Confirmed resolved since last run
- **Tender Scraper outage:** fixed. Two clean automated runs on 2026-07-16, both markets working (UK, TED, NL) and JSON published successfully.
- **Autodoc £2.00 price artifact:** per your 2026-07-14 note in `manual_review_required.md`, already applied to `autodoc_scraper.py`. Not re-checked — Autodoc is out of scope since 2026-07-14 (Cloudflare-blocked, retired).
- **KS scheduler gap:** `ISZE_ScraperRefresh_WeeklyTask.xml` now exists (file dated 2026-07-19, next Sunday trigger 2026-07-26 21:00).

## Proposed changes (NOT applied)
None this run. `proposed_patch.diff` has been overwritten to reflect that its two previous hunks (Tender Monitor XML path, Autodoc price-artifact guard) are both already applied — nothing live to propose.

## Requires manual attention
See `manual_review_required.md` — carried-forward items 2, 3, 9 (Israel RSS, Belgium RSS, Doffin/HILMA keys — all unchanged), plus one new housekeeping item on the KS pipeline refresh path.

## Artifacts written this run
- `scraper_health_report.md` (this file, overwrites 2026-07-12 version)
- `proposed_patch.diff` (overwritten — emptied of stale/applied hunks, nothing new to propose)
- `manual_review_required.md` (overwritten — resolved items closed out, open items 2/3/9 carried forward, one new item added)

## Next steps for Jerome
1. Nothing urgent. Both scrapers are producing fresh output.
2. Israel RSS and Belgium RSS (Items 2–3) are still silently returning zero results every run — worth a look next time you have 20 minutes free, since they've been broken since at least 2026-06-28 with no forward progress (this job still can't test a fix without live web access).
3. Optional: confirm `ISZE_ScraperRefresh_WeeklyTask.xml` is actually imported and enabled in Task Scheduler, not just present on disk (I can't check that from here) — see Item 10 in `manual_review_required.md`.
