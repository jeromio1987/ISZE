#!/usr/bin/env python3
"""Inspect AT USP tenderlist row shape + notice URL pattern."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
r = s.get(
    API,
    params={
        "draw": 1,
        "start": 0,
        "length": 5,
        "order[0][column]": 2,
        "order[0][dir]": "desc",
    },
    timeout=40,
)
j = r.json()
print("keys", j.keys())
print("cols?", j.get("columns") or j.get("header"))
for i, row in enumerate(j.get("data") or []):
    print("--- row", i, "len", len(row) if isinstance(row, list) else type(row))
    print(json.dumps(row, ensure_ascii=False)[:500])

# Try detail pages with UUID from col 4
nid = (j.get("data") or [[]])[0][4] if j.get("data") else None
print("nid", nid)
if nid:
    for u in [
        f"https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tender/{nid}",
        f"https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderdetail/{nid}",
        f"https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/api/tender/{nid}",
        f"https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist?id={nid}",
    ]:
        try:
            rr = s.get(u, timeout=20)
            print(rr.status_code, len(rr.content), u[-80:], rr.headers.get("content-type", "")[:40])
        except Exception as e:
            print("ERR", u, e)

# Look in tenderlist HTML for detail link pattern
html = s.get(
    "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist", timeout=30
).text
import re

for m in re.findall(r"[\"']([^\"']*tender[^\"']{0,80})[\"']", html, flags=re.I)[:40]:
    if "api" in m or "detail" in m or "{" in m or "href" in m.lower():
        print("hint", m[:120])
