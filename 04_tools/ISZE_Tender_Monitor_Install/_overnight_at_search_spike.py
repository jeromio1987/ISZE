#!/usr/bin/env python3
"""Spike AT USP tenderlist search params before wiring fetcher."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/api/tenderlist"
UA = {
    "User-Agent": "Mozilla/5.0 Chrome/128",
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist",
}
s = requests.Session()
s.headers.update(UA)

terms = ["LKW", "Fahrzeug", "Nutzfahrzeug", "Pickup", "Instandhaltung Fahrzeug", "Pritsche"]
out = {}
for term in terms:
    params = {
        "draw": 1,
        "start": 0,
        "length": 25,
        "search[value]": term,
        "search[regex]": "false",
        "order[0][column]": 2,
        "order[0][dir]": "desc",
    }
    r = s.get(API, params=params, timeout=40)
    j = r.json()
    data = j.get("data") or []
    print(term, "filtered=", j.get("recordsFiltered"), "page=", len(data))
    titles = [row[0] for row in data[:5] if isinstance(row, list) and row]
    for t in titles:
        print("  ", (t or "")[:90])
    out[term] = {
        "filtered": j.get("recordsFiltered"),
        "page": len(data),
        "titles": titles,
        "sample_row": data[0] if data else None,
    }

Path("_overnight_at_search_spike.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("wrote _overnight_at_search_spike.json")
