#!/usr/bin/env python3
"""Fast AT downloads probe — short timeouts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 Chrome/128"
out = {}

r = s.get("https://offenevergaben.at/downloads", timeout=20)
print("downloads", r.status_code, len(r.content))
links = list(dict.fromkeys(re.findall(r'href=["\']([^"\']+)["\']', r.text)))
out["links"] = links
for L in links:
    if re.search(r"csv|json|zip|xml|tsv|download|export|\.gz", L, re.I):
        print(" DATA", L)

# europa distributions URLs only (no heavy download)
r = s.get(
    "https://data.europa.eu/api/hub/search/search",
    params={"q": 'title:"Ausschreibungen laut BVergG"', "limit": 5},
    timeout=20,
)
print("europa", r.status_code)
try:
    results = ((r.json().get("result") or {}).get("results") or [])
except Exception:
    results = []
for p in results:
    title = p.get("title")
    if isinstance(title, dict):
        title = title.get("en") or title.get("de") or str(title)
    print(" pack", title)
    for d in (p.get("distributions") or [])[:4]:
        au = d.get("access_url") or d.get("download_url")
        if isinstance(au, list):
            au = au[0] if au else None
        fmt = d.get("format")
        if isinstance(fmt, dict):
            fmt = fmt.get("id")
        print("  ", fmt, au)

# USP search page — look for XHR endpoint in embedded JS
r = s.get("https://www.usp.gv.at/suche/ausschreibungen.html", timeout=20)
print("usp search", r.status_code, len(r.content))
for m in re.findall(r["\"'](https?://[^\"']+|/[a-zA-Z0-9_./-]*api[^\"']*)[\"']"], r.text)[:20]:
    print(" usp", m)
scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', r.text)
out["usp_scripts"] = scripts[:20]
print(" scripts", scripts[:10])

Path("_overnight_at_downloads.json").write_text(json.dumps(out, indent=2, ensure_ascii=False)[:200000], encoding="utf-8")
