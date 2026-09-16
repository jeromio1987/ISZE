#!/usr/bin/env python3
"""Focused BG scrape → isuzu_tenders_v3_bg.xlsx (does not overwrite main)."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openpyxl

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SIDE = HERE / "isuzu_tenders_v3_bg.xlsx"


def main() -> None:
    from national_fetchers_bg import fetch_bulgaria_eop
    from source_health import load_health, persist_and_report, record_source_result
    from tender_scraper_v3 import EXPORT_HEADERS, LOOKBACK_DAYS, normalize_batch

    from_dt = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    raw = fetch_bulgaria_eop(from_dt=from_dt)
    gated = normalize_batch(raw, "BG-EOP")
    print(f"[BG] raw={len(raw)} gated={len(gated)}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bulgaria EOP"
    ws.append(list(EXPORT_HEADERS))
    for row in gated:
        ws.append([row.get(h, "") for h in EXPORT_HEADERS])
    wb.save(SIDE)
    print(f"Wrote {SIDE}")

    health = load_health()
    record_source_result(health, "Bulgaria CAIS EOP", len(raw), None if raw else "zero matches")
    persist_and_report(health)
    print(f"Health: Bulgaria CAIS EOP last_count={len(raw)}")


if __name__ == "__main__":
    main()
