⚠ GENERATED 2026-08-09 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# Manual Review Required — 2026-08-09

**Status vs. 2026-08-02 report:**

| Item | Status |
|------|--------|
| Old #2 — `ISZE_PMS_IAM_Refresh` scheduler interruption pattern | Still unconfirmed — folded into new Item 1 below, with a fresh (and more concrete) data point |
| Old #3 — Israel RSS undefined entity | Unchanged failure, but now has a real proposed fix — see Item 3 below + `proposed_patch.diff` |
| Old #4 — Belgium RSS non-XML response | Unchanged — see Item 4 below |
| Old #5 — Doffin/HILMA API keys unset | Unchanged, informational — see Item 5 below |
| Old #7 — `scrape_asof.json` not updated by 08-01 refresh | Clarified this run, not just carried forward — see Item 6 below |

**New this run:** Item 2 (drift-history baseline bug) and Item 5 (DE DTVP — real but low-priority, wasn't tracked as its own item before).

---

## Item 1 — Weekly refresh timing: this week's cycle hadn't landed as of this healthcheck (carries old Item 2)

**What I found:** `ISZE_ScraperRefresh_WeeklyTask.xml` documents a Sunday 21:00 trigger, with the healthcheck meant to follow at 22:00. This run started ~22:04 CEST on Sunday 2026-08-09. As of that time, the newest competitive-pricing output on disk was still 2026-08-03 (last Sunday) — no CSV, snapshot, or log dated 2026-08-09 exists. I found no `.pre_reset.bak` or other evidence of a run currently in progress either.

**Worth noting, not just "it's late":** actual historical run timestamps don't match a clean "Sunday 21:00" pattern at all — completions cluster Saturday night through Monday morning (2026-07-09 Thu, 07-13 Mon, 07-20 Mon, 07-26 Sun evening *manual*, 07-27 Mon, 08-01 Sat, 08-03 Mon). That's consistent with either normal jitter, a timezone mismatch between the stored `StartBoundary` and the machine's actual clock, or the live Windows Task Scheduler entry having drifted from what's in this XML file (editing the XML in the repo doesn't re-import it into Task Scheduler by itself). I can't tell which from this sandbox.

**Not urgent today** — the pipeline is still comfortably 🟢 fresh (6.6 days, well under the 14-day threshold), and this may simply resolve itself later tonight or by morning. But this is the second run in a row flagging scheduler-timing uncertainty (last report's Item 2 raised the same question about `ISZE_PMS_IAM_Refresh` after the 2026-07-20 `0xC000013A` interruption), and I still can't confirm from here whether `ISZE_PMS_IAM_Refresh` and `ISZE_ScraperRefresh_WeeklyTask` are the same task under two informal names or genuinely different tasks.

**No patch proposed** — Task Scheduler isn't inspectable from this sandbox.

---

## Item 2 (NEW) — `refresh_and_check_drift.py`: drift alert is comparing against a stale, two-runs-back baseline

**What I found:** `_snapshots/drift_history.csv` logged the *same* TMC `fuel_filter` move — `32.74 → 27.32 (-16.6%, flagged)` — on both 2026-08-01 *and* 2026-08-03. The raw `tmc_results.csv` shows the price has actually been flat at 27.32 (£23.35 → converted) since 08-01; nothing moved between 08-01 and 08-03. So the 08-03 flag is a false repeat, not a second real move.

**Root cause (traced in `refresh_and_check_drift.py`, not on the auto-apply allowlist — this is diagnosis only):**
- `main()` (lines 189–192) snapshots each CSV's **current on-disk content into a folder named after today's date** *before* that day's scraper runs. So a folder named e.g. `2026-08-03` actually contains 2026-08-01's output (whatever was on disk right before today's scrape overwrote it) — the folder name is one cycle ahead of its contents.
- `_latest_prior_snapshot()` (lines 106–114) then searches for the most recent folder with a name *strictly less than* today's date to use as the comparison baseline. Because today's own (mislabeled) snapshot is excluded by that `<` filter, it falls through to the *previous* dated folder — which, by the same off-by-one, actually holds data from *two* runs back.
- Net effect: every run's "old" price is one full cycle further back than intended. A real move gets flagged correctly the first time it's detected, then gets flagged *again* on the next run (comparing against the pre-move baseline a second time) even though the price has already stabilized.

**Impact:** false-repeat drift flags (alert-fatigue risk), not a data-quality problem — the underlying scraped prices in the CSVs themselves are correct. Could also mask a genuine second move in the same direction by making it look like "more of the same already-seen change."

**Fix sketch (not diffed — this file is explicitly do-not-edit scope, even for proposals):** either (a) snapshot *after* each scraper runs instead of before, so the folder name matches its contents, or (b) keep snapshotting before but change `_latest_prior_snapshot`'s filter to `<=` and skip the just-created same-day snapshot by identity rather than by date comparison. Either is a small, self-contained change — flagging for you or a future coding session to apply deliberately.

---

## Item 3 — Israel RSS: undefined XML entity — unchanged, now has a proposed fix

**Fresh evidence this run:** `tender_data.json` (generated 2026-08-03T05:33:29Z) still shows `"No Israel results found": 1` in `source_counts` — same failure mode as every prior run, and `tender_monitor_log.txt` still logs `[IL] Error: undefined entity: line 11, column 0`.

**Root cause (unchanged):** `fetch_israel()` in `tender_scraper_v3.py` (line 735) calls `ET.fromstring()` directly against the `mr.gov.il` RSS feed, which embeds HTML entities (`&nbsp;`, `&laquo;`, etc.) that aren't valid bare XML.

**This run, unlike the last two:** I wrote an actual diff — see `proposed_patch.diff`. It wraps the parse in a fallback that escapes non-standard entities and retries once, falling through to the existing `except Exception` handler (same as today) if that still fails. Still untested against the live feed (no web access here) — review and test before applying.

---

## Item 4 — Belgium RSS: non-XML response — still occurring, unchanged since 2026-06-28

**Fresh evidence this run:** `tender_data.json` source_counts still shows `"No Belgium RSS results — TED covers above-threshold BE": 1`. Log detail: `[BEL] RSS parse error: syntax error: line 1, column 0` for both candidate URLs — that error signature (column 0) means the response isn't XML at all (most likely an HTML error/redirect page), not malformed XML.

**Why no diff this time either:** I traced this one level deeper than prior runs — `_parse_procurement_rss()` (the shared DE/BE/NL parser, line 1062) already catches `ET.ParseError` cleanly and returns no rows; it's not crashing or misbehaving. The Netherlands feed uses the exact same shared parser and works fine (25 matches), so the parser itself isn't the problem. This is specifically "both `BELGIUM_RSS_CANDIDATES` URLs are dead or moved" — the only real fix is finding the correct current feed URL, which needs a browser/live lookup this job doesn't have access to. A defensive content-type check would make the failure log cleaner but wouldn't recover any data, so I didn't bother proposing it as a diff.

**No patch proposed.** TED (BEL) still covers above-threshold Belgium contracts, so this is partial, not total, loss for that market.

---

## Item 5 (NEW, low priority) — Germany DTVP portal: 404 on every run

**What I found:** Every run I can see in `tender_monitor_log.txt` (back to at least 2026-07-13) logs `[DE] DTVP RSS: HTTP 404 — portal may require browser access` and `[DE] NRW portal: HTTP 404 — skipping`. This is consistent and long-standing, not a new regression — it just hadn't been called out as its own tracked item before (it's separate from the Doffin/HILMA API-key gap below).

**Why no patch:** the code already documents the likely cause (`DTVP_RSS_URL`, line 1053, with comments noting DTVP typically requires browser/session access, not a plain RSS fetch) and already has a fallback message pointing at "TED covers DE above-threshold contracts" — same treatment as Belgium. A 404 on what's supposed to be a public RSS endpoint isn't a one-line URL fix; it likely needs either a different (authenticated) API path or accepting this as a below-threshold coverage gap.

**No action needed unless below-threshold German tender coverage becomes a priority** — informational only, same tier as Item 6 below.

---

## Item 6 — Doffin/HILMA API keys unset — informational, unchanged

`DOFFIN_API_KEY` / `HILMA_API_KEY` still empty, still skipped gracefully. Not a bug. No action needed unless Nordic coverage becomes a priority.

---

## Item 7 — `scrape_asof.json`: confirmed orphaned (clarifies old Item 7)

**Last run's open question:** "I can't find where `scrape_asof.json` is written." **This run, I confirmed it:** nothing in the current codebase writes it — `grep -r "scrape_asof"` across all `.py`/`.bat`/`.ps1`/`.xml` files in the live tree (excluding an old git worktree) returns zero hits outside the file itself. Its one and only known write was the 2026-07-26 manual run (`refresh_manual_2026-07-26_2128.log`, itself run by hand). It's now 12+ days stale and has been silently skipped by *two* consecutive automated refreshes (08-01 and 08-03) without anything erroring.

**Conclusion:** this isn't a "gap in the pipeline" — it's a one-off leftover from a manual process that was never wired into `refresh_and_check_drift.py`. Safe to ignore. I haven't deleted it (not my call, and it's outside this job's allowed outputs) — worth a two-minute look only if some other tool or dashboard reads it for freshness instead of checking the CSVs directly; otherwise fine to delete whenever you're tidying up.

---

*End of manual_review_required.md — 2026-08-09*
