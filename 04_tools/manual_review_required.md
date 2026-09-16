⚠ GENERATED 2026-08-23 by isze-scraper-healthcheck-autofix — review applied_patches_log.md for any auto-applies.

# Manual review required — 2026-08-23

Everything on the auto-apply allowlist (KS, Tranzparts, TMC, Mekonomen, Auto365) refreshed cleanly on 2026-08-17 with 0 errors and no ≥15% price drift (`_logs/refresh_2026-08-17.log`). Nothing on the allowlist needed a fix this run. One item below, on `tender_scraper_v3.py` (propose-only, out of allowlist scope regardless of confidence).

## Item 1 — Israel RSS feed: second XML defect after the 2026-08-11 fix

**File:** `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py`, `fetch_israel()` (line ~727)
**Status:** Partially fixed, still broken.

Background: the 2026-08-09 healthcheck found `fetch_israel()` failing with `undefined entity: line 11, column 0` — mr.gov.il's feed embeds HTML entities (`&nbsp;`, `&laquo;`, etc.) that aren't valid bare XML. Jerome applied a fix interactively on 2026-08-11 (entity-sanitizing regex + retry, see `applied_patches_log.md`), and that fix is confirmed live in the current file.

Evidence the fix is only partial — production log `tender_monitor_log.txt`, run started `17/08/2026 07:30:01`:
```
[IL] Fetching Israel government tenders RSS...
[IL] Error: mismatched tag: line 53, column 2
```
This is a *different* error than the one fixed on 2026-08-11 ("undefined entity" → "mismatched tag"). Reading the current code, this is expected behavior given how the fix was written: the retry block does `except ET.ParseError: ... root = ET.fromstring(sanitized)` — that inner `ET.fromstring(sanitized)` is not itself wrapped, so if the sanitized XML *still* has a structural problem (like an unclosed/mismatched tag, which entity-escaping doesn't fix), it raises a fresh `ET.ParseError` that falls through to the outer `except Exception as exc: print(f"[IL] Error: {exc}")` — which is exactly the message seen. Net effect: Israel has returned 0 tenders in every run checked (including today's), before and after the Aug 11 fix — the entity problem is resolved but a second, unrelated malformation in the same feed is now the blocker.

**Why no diff is proposed:** this job has no web access and cannot fetch `https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml` to see what's actually at line 53 of the raw response. Guessing at a `recover=True` lxml parser swap or a broader regex without seeing the real malformed tag risks silently dropping or corrupting entries. `tender_scraper_v3.py` is propose-only for this skill regardless of confidence, so even a good guess would only go in `proposed_patch.diff`, not get applied — better to flag it for someone with live feed access.

**Suggested next step (for a human or a session with web access):** curl/fetch the raw feed, `diff` it against what the entity-sanitizer outputs, find the actual line-53 tag mismatch, then either fix the source feed handling or fall back to a lenient parser (e.g. `lxml.etree.XMLParser(recover=True)`) for this one source.

## Item 2 — Belgium RSS (unchanged from 2026-08-09)

**File:** same, `fetch_belgium` region.
**Status:** unchanged — still 0 results, still no fix possible from here.

```
[BEL] RSS parse error: syntax error: line 1, column 0
[BE] https://www.publicprocurement.be/supplier/feed/rss: 0 matches
[BEL] RSS parse error: syntax error: line 1, column 0
[BE] https://www.publicprocurement.be/en/rss: 0 matches
```
Both candidate URLs return non-XML content — dead/moved endpoints, not a parse bug. TED continues to cover above-threshold Belgian contracts, so this is a coverage gap for below-threshold BE only. Needs live web research to find the current feed URL (no confirmed free public RSS exists as of the 2026-08-11 research noted in `applied_patches_log.md`).
