#!/usr/bin/env python3
"""Why do service.bund DE rows fail the Isuzu gate?"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from isze_core_v3 import normalize_raw_row, row_passes_isuzu_selection_gate
from tender_scraper_v3 import fetch_germany

session = requests.Session()
from_dt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
rows = fetch_germany(session, from_dt)
print("raw bund", len(rows))
kept = 0
for r in rows:
    title = str(r.get("Title") or "")[:90]
    norm = normalize_raw_row(dict(r), "🇩🇪 DE")
    ok = row_passes_isuzu_selection_gate(norm)
    if ok:
        kept += 1
    print(
        f" keep={ok} seg={norm.get('product_segment')} "
        f"fleet={norm.get('fleet_size')} title={title}"
    )
    print("  buyer=", str(norm.get("buyer") or r.get("Buyer") or "")[:70])
    print("  cpv=", norm.get("cpv") or r.get("CPV Code"))
print("kept", kept, "/", len(rows))
