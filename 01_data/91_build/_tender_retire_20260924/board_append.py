"""Append one row to DELEGATOR_BOARD.md, safely.

Several agents have written this file concurrently today and one row was lost in
a race, so: read immediately before writing, append bytes at the end, re-read and
confirm the row survived, and re-append if it did not.

The write is a byte-level append of UTF-8 text with CRLF line endings, which is
what the file already uses. Nothing else in the file is rewritten, so no other
agent's row can be re-encoded or truncated by this script.
"""
from __future__ import annotations

import sys
from pathlib import Path

BOARD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")

ROW = (
    "| 2026-09-24 22:15 | cursor (tender table retirement) | "
    "**The stale flattened tender table is retired: all three remaining readers now read the weekly "
    "live feed, and the disagreement it caused is gone.** The table `01_data/00_derived/tender_pipeline.csv` "
    "(708 rows, last built 29 May 2026) said 400 actionable and 352 R&M. All three readers now say 281 and "
    "279 out of 619, counted from `01_data/14_dashboards/tender_data.json` (feed 2026-09-22T17:24:26Z) "
    "through PRISM's one reader `modules/tender_feed.py` - no second loader was written and that module was "
    "not changed. Reader 1 `scripts/export_tender_pipeline.py` now calls `load_feed()` and prints the feed "
    "date and coverage; its Excel and PDF both run clean on the live feed. Reader 2 "
    "`scripts/sync_evidence_derived.py` no longer copies the table into the Evidence app; it writes "
    "`tender_feed.csv` there from the same loader, with the other 32 files untouched. Reader 3 the Evidence "
    "app's tender page, `sources/prism/tender_pipeline.sql`, used by `pages/tender.md` and "
    "`pages/aim-leakage.md`, now points at `tender_feed.csv`. Before, all three read 708 rows / 400 "
    "actionable / 352 R&M; after, all three read 619 / 281 / 279, the same as the live feed. Reader 1 also "
    "counted 31 rows with a value, 128 with a deadline, 16 with a fleet size and 0 outcomes. Both Evidence "
    "pages were rendered in headless Chrome and read by me: the tender page paints 619 opportunities, "
    "EUR 174,564,002 of published value and 281 actionable, and the aim-leakage tender block paints 619 / 281 "
    "/ 46 per cent parts signal / 45 per cent R&M with a \"value on 31 of 619, deadlines on 128\" line above "
    "it. The retirement is written down in `01_data/00_derived/_SUPERSEDED_tender_pipeline.md`; the table and "
    "`scripts/build_tender_pipeline.py` are both still on disk and neither was deleted. PRISM tests: 13 "
    "failures and 1 collection error, exactly the pre-existing set (risk_cockpit_viz 6, "
    "validate_supersession_epc 6, ui_links 1, fig_key_catalog collection); 91 passed including all 20 page "
    "smoke tests, so nothing was added. "
    "| `03_analytics/Isuzu/prism/scripts/export_tender_pipeline.py`, "
    "`03_analytics/Isuzu/prism/scripts/sync_evidence_derived.py`, "
    "`03_analytics/Isuzu/prism/evidence-app/sources/prism/tender_pipeline.sql`, "
    "`03_analytics/Isuzu/prism/evidence-app/pages/tender.md`, "
    "`03_analytics/Isuzu/prism/evidence-app/pages/aim-leakage.md`, "
    "`03_analytics/Isuzu/prism/evidence-app/data/derived/tender_feed.csv` + `.meta.json` (new), "
    "`01_data/00_derived/_SUPERSEDED_tender_pipeline.md` (new), "
    "`01_data/91_build/_tender_retire_20260924/` (probes and page screenshots), "
    "`01_data/16_exports/PRISM_Tender_Pipeline.xlsx` and `.pdf` (rerun on the live feed) "
    "| Two things are left open. (1) `npm install` was run once in the Evidence app because `node_modules` "
    "was absent and the app could not otherwise be rendered; the 32 files `sync_evidence_derived.py` copies "
    "under `evidence-app/data/derived` were refreshed from their current `01_data` sources in the same run, "
    "so those mirrors now differ from what was committed on 29 May. (2) The old table's own copy at "
    "`evidence-app/data/derived/tender_pipeline.csv` is still on disk and now unread, the work order's "
    "\"do not delete\" applying to it too. No scheduled task, PRISM tender page, `tender_feed.py`, pillar "
    "board or email was touched. |\r\n"
)

MARKER = "cursor (tender table retirement)"


def append() -> int:
    data = BOARD.read_bytes()
    if MARKER.encode("utf-8") in data:
        print("row already present; not appending again")
        return 0
    with BOARD.open("ab") as fh:
        fh.write(ROW.encode("utf-8"))
    return 1


def verify() -> bool:
    text = BOARD.read_text(encoding="utf-8")
    ok = MARKER in text
    rows = [ln for ln in text.splitlines() if ln.startswith("| 2026-")]
    print(f"marker present : {ok}")
    print(f"table rows     : {len(rows)}")
    print(f"file size      : {len(text.encode('utf-8'))} bytes")
    print(f"last row starts: {rows[-1][:80] if rows else '-'}")
    return ok


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    append()
    if not verify():
        print("MISSING after append - re-appending")
        append()
        if not verify():
            print("STILL MISSING")
            sys.exit(1)
    print("OK")
