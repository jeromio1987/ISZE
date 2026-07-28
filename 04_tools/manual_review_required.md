⚠ GENERATED 2026-07-27 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# Manual Review Required — 2026-07-27

**Resolved since 2026-07-19 (closing these out):**

| Item | Status |
|------|--------|
| 10a — KS pipeline refresh mechanism unclear | ✅ Confirmed: `refresh_and_check_drift.py` runs all five scrapers (KS/Tranzparts/TMC/Mekonomen/Auto365) as one unit. Verified from the 2026-07-26 manual run log (all five sections present sequentially in one log file) and `AUTOMATION_REGISTER.md`, which confirms `ISZE_PMS_IAM_Refresh` **is** this combined refresh. |
| 10b — Task Scheduler import unverifiable | ✅ Confirmed registered: `AUTOMATION_REGISTER.md` shows `ISZE_PMS_IAM_Refresh` as live (Weekly Mon 07:00), with real last-run-result history. It is imported, not just sitting as an XML file. |

**Still open, unchanged since 2026-06-28 (Items 3–5 below) — carried forward again.**
**New this run: Items 1, 2, 6.**

---

## Item 1 (NEW, high priority) — Mekonomen scraper: Playwright browser executable missing

**What happened:** Your manual refresh run 2026-07-26 ~21:28–21:52 (`_logs/refresh_manual_2026-07-26_2128.log`) shows KS, Tranzparts, TMC, and Auto365 all completed cleanly (0 errors). Mekonomen crashed:

```
File "...\04_tools\autodoc_scraper\mekonomen_scraper.py", line 264, in run
    browser = pw.chromium.launch(...)
playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at
C:\Users\jerom\AppData\Local\Temp\cursor-sandbox-cache\6bf1de55922f023df5f525ff28390a22\playwright\chromium_headless_shell-1208\chrome-headless-shell-win64\chrome-headless-shell.exe
Looks like Playwright was just installed or updated. Please run:
    playwright install
```

The pipeline's own safety net worked as designed: it detected zero rows, did **not** overwrite `mekonomen_results.csv`, and restored the good file from `mekonomen_results.csv.pre_reset.bak`. No data was lost — but the scraper itself is currently non-functional, and this is not something `isze-scraper-healthcheck-autofix` can fix: it's a missing browser binary, not a URL/selector bug, so it fails the auto-apply gate ("string updates only") even though `mekonomen_scraper.py` is on the allowlist. No diff is proposed for this reason — there's no line of code to change.

**Why this happened (inference, not confirmed — I can't inspect your environment variables from here):** the failed path (`AppData\Local\Temp\cursor-sandbox-cache\...`) is not Playwright's normal cache location (normally `AppData\Local\ms-playwright\...`). This looks like a `PLAYWRIGHT_BROWSERS_PATH` environment variable pointing at a Cursor IDE sandbox temp folder, which then got cleared (temp cleanup or reboot), taking the browser binary with it.

**Suggested fix (for you to run, not auto-applied):**
1. Run `C:\Python314\python.exe -m playwright install chromium` — this is the exact interpreter the scraper traceback shows, so installing from it ensures the binary lands where the script will actually look.
2. If that doesn't stick (i.e., it fails again next run), check `PLAYWRIGHT_BROWSERS_PATH` in your user/system environment variables — if it points into a Cursor temp/sandbox folder, either unset it or repoint it somewhere persistent (e.g. the Playwright default), then reinstall.

**Time sensitivity:** `mekonomen_results.csv` is currently 11 days old (2026-07-16) — still inside the 14-day freshness window, but will breach it around **2026-07-30** if not fixed before then. The next scheduled attempt is next Monday (2026-08-03) unless you run it manually sooner.

---

## Item 2 (NEW) — `ISZE_PMS_IAM_Refresh` scheduled task: interrupted-run pattern

Per `AUTOMATION_REGISTER.md`, the previous scheduled run of this task (2026-07-20, weekly Mon 07:00) ended with result **`0xC000013A`** (interrupted) — nobody noticed until you ran the full pipeline manually by hand on 2026-07-26 evening. Today's scheduled run (2026-07-27 07:00) was **in progress at the time of this health check** (07:00–07:09, KS leg at row 119/300 when last observed) — I have no way to confirm from here whether it completed or was interrupted again.

`0xC000013A` (`STATUS_CONTROL_C_EXIT`) most commonly shows up on scheduled tasks configured to run only in an interactive/logged-on session, when the session ends mid-run (sleep, lock, logoff) before the task finishes. Worth a two-minute check in Task Scheduler: does `ISZE_PMS_IAM_Refresh` have "Run whether user is logged on or not" and "Wake the computer to run this task" set? If it's set to logged-on-only and your machine sleeps or locks around 07:00–07:20, that would explain both the 07-20 interruption and would put today's run at the same risk. This is a guess based on the symptom, not a confirmed root cause — I can't inspect Task Scheduler settings from here.

**No patch proposed** — this is a scheduler/power-settings question, not a code bug.

---

## Item 3 — Israel RSS: undefined XML entity — still occurring, unchanged since 2026-06-28

**Fresh evidence this run:** `tender_data.json` (generated 2026-07-21T05:06:05Z, still the latest publish) shows `"No Israel results found": 1` in `source_counts`, consistent with the same failure mode logged 2026-07-20: `[IL] Error: undefined entity: line 11, column 0`.

**Root cause (unchanged):** `fetch_israel()` in `tender_scraper_v3.py` (~line 727) uses `ET.fromstring()`, a strict XML parser, against the `mr.gov.il` RSS feed, which embeds HTML entities (`&nbsp;`, `&laquo;`, etc.) that aren't valid XML.

**Suggested approaches (unchanged, still not diffed — needs a live-feed smoke test this job can't run without web access):**
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

## Item 4 — Belgium RSS: non-XML response — still occurring, unchanged since 2026-06-28

**Fresh evidence this run:** `tender_data.json` source_counts shows `"No Belgium RSS results — TED covers above-threshold BE": 1`, same failure mode logged 2026-07-20 on both URL candidates:
```
[BEL] RSS parse error: syntax error: line 1, column 0
[BE] https://www.publicprocurement.be/supplier/feed/rss: 0 matches
[BEL] RSS parse error: syntax error: line 1, column 0
[BE] https://www.publicprocurement.be/en/rss: 0 matches
```
TED (BEL) still covers above-threshold Belgium contracts — partial, not total, loss for that market.

**Suggested check (unchanged):** open either URL directly in a browser to see if it now redirects to a login/error page; if the URL has moved, update `BELGIUM_RSS_CANDIDATES` in `tender_scraper_v3.py` (~line 1048). A defensive Content-Type check before parsing was also suggested previously — still valid, still not diffed.

---

## Item 5 — Doffin/HILMA API keys unset — informational, unchanged

`DOFFIN_API_KEY` / `HILMA_API_KEY` empty, skipped gracefully (`source_counts` shows both "No results — add ... API key" entries in the 2026-07-21 JSON). Not a bug. No action needed unless Nordic coverage becomes a priority.

---

## Item 6 (NEW, minor) — `tender_monitor_log.txt` doesn't reflect the latest publish

`tender_monitor_log.txt` on disk stops at the 2026-07-20 07:35 run. But the live `tender_data.json` was republished 2026-07-21 07:06 (per its own `generated_at` and the `tender_data.backup_20260721_0706.json` snapshot) — a run that isn't reflected in the log file at all. Data-wise this is fine (2026-07-21 is the fresher of the two, and it's what I checked freshness against), but it means I can't fully audit console output for that specific run — I'm relying on the JSON's own `source_counts` instead, which is sufficient for Items 3–5 above but is a narrower view than a full log. Not urgent, just flagging the gap in case you want the two publish paths to log consistently.

---

*End of manual_review_required.md — 2026-07-27*
