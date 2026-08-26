⚠ GENERATED 2026-08-23 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# ISZE SCRAPER HEALTH REPORT — 2026-08-23

## Verifier
| Check | Result | Evidence |
|-------|--------|----------|
| Tender JSON ≤14d | PASS | `01_data/14_dashboards/tender_data.json` meta.generated_at = 2026-08-17T05:33:38Z → 6.6 days old |
| KS CSV ≤14d | PASS | `04_tools/autodoc_scraper/ks_results.csv` mtime = 2026-08-17 07:21 → 6.6 days old |
| Auto-apply compile | N/A | No allowlisted files edited this run — nothing to compile |
| Allowlist scope | PASS | No Edit calls made this run |

| Scraper | Status | Last output | Action |
|---------|--------|-------------|--------|
| Tender | 🟢 | 2026-08-17 07:33 (`tender_monitor_log.txt`, run started 07:30:01) | none — see Manual review for Israel source |
| KS pipeline (KS/Tranzparts/TMC/Mekonomen/Auto365) | 🟢 | 2026-08-17 07:21–08:43 (`_logs/refresh_2026-08-17.log`) | none |

## Auto-applied this run
None.

## Proposed (not applied)
None. The `proposed_patch.diff` and `manual_review_required.md` from the 2026-08-09 run were both resolved interactively on 2026-08-11 (see `applied_patches_log.md`) — the Israel "undefined entity" parse fix and the `refresh_and_check_drift.py` off-by-one fix are both live in the current files. Both files have been overwritten this run to reflect current state rather than leaving stale content.

## Manual review
See `manual_review_required.md`. Summary: the 2026-08-11 Israel RSS fix (entity sanitization) worked — the "undefined entity" error is gone — but the live feed now fails on a **different** XML malformation ("mismatched tag: line 53, column 2"), confirmed in the 2026-08-17 07:30 production run (`tender_monitor_log.txt`). Israel still returns 0 tenders. Not auto-fixable from here: this job has no web access to inspect the live feed, and `tender_scraper_v3.py` is propose-only regardless of confidence. Belgium RSS (0 results, endpoint returns non-XML) is the same pre-existing, already-documented gap from the 2026-08-09 report — no change.

## Waiting on Jerome
1. Israel tender feed (mr.gov.il) has a second XML defect (mismatched tag near line 53) that survived the Aug 11 entity fix — needs someone with browser/web access to pull the raw feed and diagnose the actual malformed tag before a real patch can be written.
2. Belgium RSS endpoints (publicprocurement.be) still return non-XML/empty — still needs the correct current feed URL (unchanged from 2026-08-09 finding); TED continues to cover above-threshold BE contracts in the meantime.
3. Everything else (KS + 4 allowlisted competitive scrapers, Tender's UK/TED/NL sources) is healthy — no action needed.
