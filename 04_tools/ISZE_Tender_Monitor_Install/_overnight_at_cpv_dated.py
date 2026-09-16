#!/usr/bin/env python3
"""Confirm AT USP fromdate/todate + multi-CPV before wiring."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

API = "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/api/tenderlist"
s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 Chrome/128",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist",
    }
)
cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
cpvs = [
    "34100000",
    "34130000",
    "34131000",
    "34140000",
    "34144000",
    "34144210",
    "50110000",
    "50114000",
    "34000000",
]
# requests encodes list as repeated keys
params = [
    ("draw", 1),
    ("start", 0),
    ("length", 100),
    ("orderColumn", 2),
    ("orderDir", "desc"),
    ("fromdate", cutoff),
    ("todate", today),
]
for c in cpvs:
    params.append(("cpvList", c))

r = s.get(API, params=params, timeout=45)
j = r.json()
print("filtered", j.get("recordsFiltered"), "page", len(j.get("data") or []))
for row in (j.get("data") or [])[:15]:
    print(row[2], (row[0] or "")[:85], "|", (row[1] or "")[:40])

Path("_overnight_at_cpv_dated.json").write_text(
    json.dumps(
        {
            "filtered": j.get("recordsFiltered"),
            "titles": [(r[0], r[2], r[1]) for r in (j.get("data") or [])[:40]],
        },
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
