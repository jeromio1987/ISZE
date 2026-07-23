⚠ REQUIRES JEROME REVIEW — DO NOT AUTO-APPLY. Generated 2026-07-19 by isze-scraper-healthcheck-autofix.

# Manual Review Required — 2026-07-19

**Resolved since 2026-07-12 (closing these out):**

| Item | Status |
|------|--------|
| 1 — Tender Task Scheduler dead path | ✅ Confirmed working — two clean automated runs 2026-07-16 (10:56, 13:33), fresh JSON both times |
| 5 — KS / competitive pricing scheduler | ✅ `ISZE_ScraperRefresh_WeeklyTask.xml` exists, next trigger 2026-07-26 21:00. See new Item 10 below — one thing worth a quick check. |
| 6 — Autodoc/Oscaro scope | Closed 2026-07-14, unchanged. |
| 7 — `01_data\dashboards` junction I/O error | Closed — you verified 2026-07-16 it's a sandbox mount artifact, not a real break. |
| 8 — Stale `Tools\` path in docs | Closed 2026-07-14, unchanged. |
| Hunk 2 — Autodoc £2.00 artifact | Applied 2026-07-14, unchanged. |

**Still open: Items 2, 3, 9 (unchanged since 2026-06-28) — carried forward below.**
**New this run: Item 10.**

---

## Item 2 — Israel RSS: undefined XML entity — still occurring, unchanged since 2026-06-28

**Fresh evidence this run:** `tender_monitor_log.txt` shows the identical error on both 2026-07-16 runs: `[IL] Error: undefined entity: line 11, column 0`. Zero Israel tenders captured on either run.

**Root cause (unchanged):** `fetch_israel()` in `tender_scraper_v3.py` (~line 727) uses `ET.fromstring()`, a strict XML parser, against the `mr.gov.il` RSS feed, which embeds HTML entities (`&nbsp;`, `&laquo;`, etc.) that aren't valid XML.

**Suggested approaches (unchanged from 2026-07-12, still not diffed — need a live-feed smoke test this job can't run):**
```python
try:
    root = ET.fromstring(resp.content)
except ET.ParseError:
    from lxml import etree as lxml_ET
    root = lxml_ET.fromstring(resp.content, parser=lxml_ET.XMLParser(recover=True))
```
or, without a new dependency:
```python
import re as _re
content = _re.sub(rb'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)(\w+);', rb'&amp;\1;', resp.content)
root = ET.fromstring(content)
```

---

## Item 3 — Belgium RSS: non-XML response — still occurring, unchanged since 2026-06-28

**Fresh evidence this run:** Both 2026-07-16 runs show the same failure on both URL candidates:
```
[BEL] RSS parse error: syntax error: line 1, column 0
[BE] https://www.publicprocurement.be/supplier/feed/rss: 0 matches
[BEL] RSS parse error: syntax error: line 1, column 0
[BE] https://www.publicprocurement.be/en/rss: 0 matches
```
TED (BEL) still covers above-threshold Belgium contracts, so this is partial, not total, loss for that market — same as before.

**Suggested check (unchanged):** open either URL directly in a browser to see if it now redirects to a login/error page; if the URL has moved, update `BELGIUM_RSS_CANDIDATES` in `tender_scraper_v3.py` (~line 1048). A defensive Content-Type check before parsing was also suggested previously — still valid, still not diffed (same reasoning as Item 2: needs a live test).

---

## Item 9 — Doffin/HILMA API keys unset — informational, unchanged

`DOFFIN_API_KEY` / `HILMA_API_KEY` empty, skipped gracefully in both 2026-07-16 runs (`[Doffin] No API key set — skipping.` / `[HILMA] No API key set — skipping.`). Not a bug. No action needed unless Nordic coverage becomes a priority.

---

## Item 10 (NEW) — KS pipeline: refresh path and Task Scheduler import unverified

Two small things worth a look, neither urgent since output is currently fresh:

**a) Refresh mechanism unclear for this cycle.** `ks_results.csv` and `mekonomen_results.csv` are both dated 2026-07-16 17:10, but `tranzparts_results.csv`, `tmc_results.csv`, and `auto365_results.csv` are dated 2026-07-13 — three days earlier. If `refresh_and_check_drift.py` (the wrapper that's supposed to run all five) had executed as one unit on 2026-07-16, all five would share that timestamp. There's also no `_logs\refresh_2026-07-16.log` — the only log present is `refresh_2026-07-13.log`. Best read: the 2026-07-16 KS/Mekonomen update came from a manual/direct run of those two scrapers individually, not from the wrapper. Not a problem today (everything's within the 14-day window), but if the wrapper genuinely hasn't run since 2026-07-13, Tranzparts/TMC/Auto365 will drift out of freshness on their own schedule rather than together.

**b) Task Scheduler import unverifiable from this environment.** `ISZE_ScraperRefresh_WeeklyTask.xml` exists on disk (dated 2026-07-19, next trigger 2026-07-26 21:00 per its `<DaysOfWeek><Sunday/>` recurrence), but this job has no way to check whether it's actually been imported into Windows Task Scheduler versus just sitting as a file — same caveat that applied to the Tender Monitor task before you manually re-imported it on 2026-07-14. Worth a 10-second check: Task Scheduler → confirm "ISZE Competitive Pricing Refresh" (or similar) is present, enabled, and has a sensible "Last Run Result."

**No patch proposed for either — both are informational/verification items, not code bugs.**

---

*End of manual_review_required.md — 2026-07-19*
