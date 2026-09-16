#!/usr/bin/env python3
import json
import re
from pathlib import Path

import requests

html = requests.get(
    "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=40,
).text
m = re.search(
    r"ajax:\s*function\(data,\s*callback\)\s*\{(.*?)\}\s*,\s*columns",
    html,
    flags=re.S,
)
print("ajax fn", "found" if m else "no", len(m.group(1)) if m else 0)
ajax = m.group(1) if m else ""
Path("_overnight_at_ajax_fn.js").write_text(ajax, encoding="utf-8")
print(ajax[:4000])

cpvs = re.findall(r'id="(cpv[^"]+)"[^>]*value="([^"]+)"', html)
print("cpv inputs", len(cpvs))
for x in cpvs[:40]:
    print(" ", x)
vals = re.findall(r'value="(34\d{6}|501\d{5})"', html)
print("vehicle-ish values", list(dict.fromkeys(vals))[:40])

# Try API with cpvList
API = "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/api/tenderlist"
s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist",
    }
)
# DataTables sends arrays as cpvList[]= or repeated cpvList=
for params in [
    {
        "draw": 1,
        "start": 0,
        "length": 25,
        "orderColumn": 2,
        "orderDir": "desc",
        "cpvList": ["34130000", "34131000", "50110000"],
    },
    {
        "draw": 1,
        "start": 0,
        "length": 25,
        "order[0][column]": 2,
        "order[0][dir]": "desc",
        "cpvList[]": ["34130000", "34131000", "50114000"],
    },
]:
    r = s.get(API, params=params, timeout=40)
    j = r.json()
    print("params style filtered", j.get("recordsFiltered"), "page", len(j.get("data") or []))
    for row in (j.get("data") or [])[:3]:
        print(" ", (row[0] or "")[:90])
