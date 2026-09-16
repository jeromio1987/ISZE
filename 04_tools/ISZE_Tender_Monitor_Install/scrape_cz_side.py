#!/usr/bin/env python3
"""Focused CZ scrape → isuzu_tenders_v3_cz.xlsx (does not overwrite main)."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openpyxl

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SIDE = HERE / "isuzu_tenders_v3_cz.xlsx"


def main() -> None:
    from national_fetchers_cz import fetch_czechia_vvz
    from source_health import load_health, persist_and_report, record_source_result
    from tender_scraper_v3 import EXPORT_HEADERS, LOOKBACK_DAYS, normalize_batch

    from_dt = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    raw = fetch_czechia_vvz(from_dt=from_dt)
    gated = normalize_batch(raw, "CZ-VVZ")
    print(f"[CZ] raw={len(raw)} gated={len(gated)}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Czechia VVZ"
    ws.append(list(EXPORT_HEADERS))
    for row in gated:
        ws.append([row.get(h, "") for h in EXPORT_HEADERS])
    wb.save(SIDE)
    print(f"Wrote {SIDE}")

    health = load_health()
    record_source_result(health, "Czechia VVZ", len(raw), None if raw else "zero matches")
    persist_and_report(health)
    print(f"Health: Czechia VVZ last_count={len(raw)} status=OK")


if __name__ == "__main__":
    main()
