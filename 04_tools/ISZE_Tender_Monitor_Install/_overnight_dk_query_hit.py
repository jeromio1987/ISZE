#!/usr/bin/env python3
"""Discover SoegningQueryDto fields and fetch DK vehicle notices."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

js = Path("_overnight_dk_main.js").read_text(encoding="utf-8")
# nearby DTO field names
for needle in ["fritekst", "pagineringDto", "SoegningQuery", "cpv", "udbudsform"]:
    idxs = [m.start() for m in re.finditer(needle, js, flags=re.I)]
    print(needle, "hits", len(idxs))
    if idxs:
        i = idxs[0]
        print(js[i : i + 400].replace("\n", " ")[:400])
        print("---")

s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 Chrome/128",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://udbud.dk",
        "Referer": "https://udbud.dk/soeg",
    }
)
URL = "https://udbud.dk/soegning/public/soegeresultat"

bodies = [
    {
        "fritekst": "køretøj",
        "pagineringDto": {"aktuelSide": 1, "maksElementer": 25},
    },
    {
        "fritekstSoegning": "lastebil",
        "pagineringDto": {"aktuelSide": 1, "maksElementer": 25},
    },
    {
        "soegeOrd": "køretøj",
        "pagineringDto": {"aktuelSide": 1, "maksElementer": 25},
    },
    {
        "fritekst": "varebil OR lastebil OR pickup",
        "pagineringDto": {"aktuelSide": 1, "maksElementer": 50},
    },
]

out = {}
for i, body in enumerate(bodies):
    r = s.post(URL, json=body, timeout=30)
    print(i, r.status_code, len(r.content), r.text[:220].replace("\n", " "))
    rec = {"http": r.status_code, "len": len(r.content), "snip": r.text[:400]}
    if r.status_code == 200:
        try:
            j = r.json()
            rec["keys"] = list(j.keys()) if isinstance(j, dict) else type(j).__name__
            # try find list
            for k in ("resultater", "results", "content", "items", "soegeresultater", "data"):
                if isinstance(j, dict) and k in j:
                    rec["n"] = len(j[k]) if isinstance(j[k], list) else j[k]
                    if isinstance(j[k], list) and j[k]:
                        rec["sample0"] = j[k][0]
            print("  keys", rec.get("keys"), "n", rec.get("n"))
        except Exception as e:
            rec["json_err"] = str(e)
    out[str(i)] = rec

Path("_overnight_dk_query_hit.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("wrote _overnight_dk_query_hit.json")
