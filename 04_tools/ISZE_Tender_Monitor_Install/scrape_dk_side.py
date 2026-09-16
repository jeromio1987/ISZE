#!/usr/bin/env python3
"""Focused DK scrape → isuzu_tenders_v3_dk.xlsx (does not overwrite main).

Standalone so sibling full-market edits to tender_scraper_v3.py do not collide.
Uses the same normalize_batch / gate path as other national sheets.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openpyxl

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SIDE = HERE / "isuzu_tenders_v3_dk.xlsx"


def main() -> None:
    from national_fetchers_dk import fetch_denmark_udbud
    from source_health import load_health, persist_and_report, record_source_result
    from tender_scraper_v3 import EXPORT_HEADERS, LOOKBACK_DAYS, normalize_batch

    from_dt = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    raw = fetch_denmark_udbud(from_dt=from_dt)
    gated = normalize_batch(raw, "DK-udbud")
    print(f"[DK] raw={len(raw)} gated={len(gated)}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Denmark udbud"
    ws.append(list(EXPORT_HEADERS))
    for row in gated:
        ws.append([row.get(h, "") for h in EXPORT_HEADERS])
    wb.save(SIDE)
    print(f"Wrote {SIDE}")

    health = load_health()
    record_source_result(health, "Denmark udbud.dk", len(raw), None if raw else "zero matches")
    persist_and_report(health)
    print(f"Health: Denmark udbud.dk last_count={len(raw)}")


if __name__ == "__main__":
    main()
