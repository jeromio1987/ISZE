#!/usr/bin/env python3
"""Hit DK /soegning/ and bekendtgoerelse list endpoints discovered in SPA JS."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

js = Path("_overnight_dk_main.js").read_text(encoding="utf-8")
# extract axios.get(`/bekendt...`) paths
paths = list(
    dict.fromkeys(
        re.findall(r"axios\$1\.(?:get|post)\(`(/[^`]+)`", js)
        + re.findall(r"axios\$1\.(?:get|post)\([\"'](/[^\"']+)[\"']", js)
        + re.findall(r"\.(?:get|post)\(`(/[^`]+)`", js)
    )
)
print("axios paths", len(paths))
for p in paths:
    if any(x in p.lower() for x in ("soeg", "bekendt", "udbud", "notice", "search", "annonce")):
        print(" ", p[:140])

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
out = {}
candidates = [
    ("GET", "https://udbud.dk/soegning/"),
    ("POST", "https://udbud.dk/soegning/"),
    ("GET", "https://udbud.dk/soegning/soeg"),
    ("POST", "https://udbud.dk/soegning/soeg"),
    ("GET", "https://udbud.dk/soegning/api/soeg"),
    ("POST", "https://udbud.dk/soegning/api/soeg"),
    ("GET", "https://udbud.dk/udbud/bekendtgoerelser"),
    ("GET", "https://udbud.dk/bekendtgoerelse"),
]

# add extracted paths
for p in paths:
    if "${" in p:
        continue
    if any(x in p.lower() for x in ("soeg", "bekendt", "hentall")):
        candidates.append(("GET", "https://udbud.dk" + p.split("?")[0]))
        candidates.append(("POST", "https://udbud.dk" + p.split("?")[0]))

seen = set()
for method, url in candidates:
    key = (method, url)
    if key in seen:
        continue
    seen.add(key)
    try:
        if method == "GET":
            r = s.get(url, timeout=20, params={"q": "køretøj", "page": 1})
        else:
            r = s.post(
                url,
                json={
                    "fritekst": "køretøj",
                    "query": "køretøj",
                    "page": 0,
                    "pageSize": 25,
                    "searchText": "lastebil",
                },
                timeout=20,
            )
        ct = (r.headers.get("content-type") or "")[:50]
        snip = r.text[:160].replace("\n", " ")
        print(method, r.status_code, ct, len(r.content), url[-70:], snip[:80])
        out[f"{method} {url}"] = {
            "http": r.status_code,
            "ct": ct,
            "len": len(r.content),
            "snip": snip,
        }
        if r.status_code == 200 and "json" in ct and len(r.content) > 50:
            try:
                j = r.json()
                out[f"{method} {url}"]["keys"] = list(j.keys()) if isinstance(j, dict) else type(j).__name__
            except Exception:
                pass
    except Exception as e:
        print("ERR", method, url[-50:], e)

Path("_overnight_dk_soegning.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("wrote _overnight_dk_soegning.json")
