#!/usr/bin/env python3
"""Focused IE scrape → isuzu_tenders_v3_ie.xlsx (does not overwrite main)."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openpyxl

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SIDE = HERE / "isuzu_tenders_v3_ie.xlsx"


def main() -> None:
    import national_fetchers_ie as ie_national
    from source_health import load_health, persist_and_report, record_source_result
    from tender_scraper_v3 import EXPORT_HEADERS, LOOKBACK_DAYS, normalize_batch

    from_dt = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    raw = ie_national.fetch_ireland_etenders(from_dt=from_dt)
    gated = normalize_batch(raw, "🇮🇪 IE-eTenders")
    print(f"[IE] raw={len(raw)} gated={len(gated)}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ireland eTenders"
    ws.append(list(EXPORT_HEADERS))
    for row in gated:
        ws.append([row.get(h, "") for h in EXPORT_HEADERS])
    wb.save(SIDE)
    print(f"Wrote {SIDE}")

    health = load_health()
    record_source_result(
        health,
        "Ireland eTenders",
        len(raw),
        ie_national.LAST_ERROR if ie_national.LAST_ERROR else (None if raw else "zero matches"),
    )
    persist_and_report(health)
    print(f"Health: Ireland eTenders last_count={len(raw)} err={ie_national.LAST_ERROR}")


if __name__ == "__main__":
    main()
