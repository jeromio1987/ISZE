#!/usr/bin/env python3
"""Probe Doffin Public search with simpler queries (never print key)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from nordics_keys import DOFFIN_SEARCH_URL, get_doffin_key, reload

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

reload()
key = get_doffin_key()
headers = {"Ocp-Apim-Subscription-Key": key, "Accept": "application/json"}
cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
out = {}

trials = [
    {"searchString": "kjøretøy", "issueDateFrom": cutoff, "numHitsPerPage": "20", "page": "1"},
    {"searchString": "lastebil", "issueDateFrom": cutoff, "numHitsPerPage": "20", "page": "1"},
    {"searchString": "pickup", "issueDateFrom": cutoff, "numHitsPerPage": "20", "page": "1"},
    {"searchString": "truck", "issueDateFrom": cutoff, "numHitsPerPage": "20", "page": "1"},
    {"searchString": "vedlikehold", "issueDateFrom": cutoff, "numHitsPerPage": "20", "page": "1"},
    {"issueDateFrom": cutoff, "numHitsPerPage": "5", "page": "1"},
    {"cpv": "34130000", "issueDateFrom": cutoff, "numHitsPerPage": "20", "page": "1"},
    {"cpvCodes": "34130000", "issueDateFrom": cutoff, "numHitsPerPage": "20", "page": "1"},
]

for i, params in enumerate(trials):
    r = requests.get(DOFFIN_SEARCH_URL, headers=headers, params=params, timeout=40)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text[:200]}
    if isinstance(data, list):
        n = len(data)
        sample = data[0] if data else None
        total = n
    elif isinstance(data, dict):
        notices = data.get("hits") or data.get("notices") or data.get("items") or []
        n = len(notices) if isinstance(notices, list) else 0
        sample = notices[0] if n else None
        total = data.get("total") or data.get("numHits") or data.get("totalHits") or n
        keys = list(data.keys())
    else:
        n, sample, total, keys = 0, None, 0, []
    title = ""
    if isinstance(sample, dict):
        title = str(sample.get("heading") or sample.get("title") or "")[:80]
    print(i, r.status_code, "n=", n, "total=", total, "params=", params, "title=", title)
    out[str(i)] = {
        "params": params,
        "http": r.status_code,
        "n": n,
        "total": total,
        "keys": keys if isinstance(data, dict) else "list",
        "title": title,
    }

Path("_overnight_doffin_probe.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("wrote _overnight_doffin_probe.json")
