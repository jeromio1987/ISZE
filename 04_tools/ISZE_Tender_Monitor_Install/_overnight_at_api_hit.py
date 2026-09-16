#!/usr/bin/env python3
"""Hit AT USP /api/tenderlist + offenevergaben kerndaten CSV dump."""
from __future__ import annotations

import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/csv, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist",
}
s = requests.Session()
s.headers.update(UA)
out = {"probed_at": datetime.now(timezone.utc).isoformat()}

# DataTables typically POSTs with draw/start/length
api = "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/api/tenderlist"
for method, kwargs in [
    ("GET", {"params": {"draw": 1, "start": 0, "length": 50}}),
    (
        "POST",
        {
            "data": {
                "draw": 1,
                "start": 0,
                "length": 50,
                "search[value]": "LKW",
                "search[regex]": "false",
            }
        },
    ),
    (
        "POST",
        {
            "json": {
                "draw": 1,
                "start": 0,
                "length": 50,
                "search": {"value": "Fahrzeug", "regex": False},
            }
        },
    ),
]:
    try:
        if method == "GET":
            r = s.get(api, timeout=40, **kwargs)
        else:
            r = s.post(api, timeout=40, **kwargs)
        ct = (r.headers.get("content-type") or "")[:60]
        print(method, r.status_code, ct, len(r.content), r.text[:180].replace("\n", " "))
        key = f"{method}_{len(out)}"
        out[key] = {
            "http": r.status_code,
            "ct": ct,
            "len": len(r.content),
            "snip": r.text[:400],
        }
        if r.status_code == 200 and "json" in ct:
            j = r.json()
            out[key]["keys"] = list(j.keys()) if isinstance(j, dict) else type(j).__name__
            if isinstance(j, dict):
                data = j.get("data") or j.get("aaData") or []
                out[key]["n_data"] = len(data)
                out[key]["recordsTotal"] = j.get("recordsTotal") or j.get("iTotalRecords")
                print("  records", out[key].get("recordsTotal"), "page", len(data))
                if data:
                    print("  sample0", str(data[0])[:200])
    except Exception as e:
        print(method, "ERR", e)
        out[f"{method}_err"] = str(e)

# Kerndaten dump
csv_url = "https://offenevergaben.at/downloads/kerndaten_dump_daily?format=csv"
r = s.get(csv_url, timeout=60, headers={"Accept": "text/csv, */*"})
print("kerndaten", r.status_code, r.headers.get("content-type"), len(r.content), r.url)
out["kerndaten"] = {
    "http": r.status_code,
    "ct": r.headers.get("content-type"),
    "len": len(r.content),
    "final": str(r.url),
    "snip": r.text[:300].replace("\n", " "),
}
# If HTML login wall, note it; if CSV, count vehicle-ish rows
if r.status_code == 200 and ("csv" in (r.headers.get("content-type") or "") or r.text[:50].count(";") + r.text[:50].count(",") > 2):
    try:
        sample = r.text[:200000]
        reader = csv.DictReader(io.StringIO(sample))
        rows = list(reader)
        out["kerndaten"]["cols"] = reader.fieldnames
        out["kerndaten"]["sample_n"] = len(rows)
        print(" csv cols", reader.fieldnames[:12] if reader.fieldnames else None, "rows_in_sample", len(rows))
    except Exception as e:
        out["kerndaten"]["csv_err"] = str(e)

Path("_overnight_at_api_hit.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("wrote _overnight_at_api_hit.json")
