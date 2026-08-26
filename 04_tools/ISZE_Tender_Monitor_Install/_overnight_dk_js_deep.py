#!/usr/bin/env python3
"""Deep-scan udbud.dk main JS for notice search endpoints."""
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
js = s.get("https://udbud.dk/assets/js/main-81174094.js", timeout=60).text
print("js len", len(js))
Path("_overnight_dk_main.js").write_text(js, encoding="utf-8")

patterns = [
    r"[\"'](/[^\"']*(?:notice|udbud|search|procurement|annonce)[^\"']*)[\"']",
    r"https?://[^\"'\s]+(?:notice|search|api)[^\"'\s]*",
    r"baseUrl[^,]{0,80}",
    r"apiUrl[^,]{0,80}",
    r"environment\.[a-zA-Z]+",
]
found = {}
for pat in patterns:
    hits = list(dict.fromkeys(re.findall(pat, js, flags=re.I)))[:40]
    found[pat[:40]] = hits
    print(pat[:40], "n=", len(hits))
    for h in hits[:12]:
        print("  ", h[:120])

# Try POST/GET candidates from path hits
cands = []
for hits in found.values():
    for h in hits:
        if h.startswith("/") and any(
            x in h.lower() for x in ("notice", "search", "udbud", "annonce", "api")
        ):
            cands.append("https://udbud.dk" + h.split("?")[0])
cands = list(dict.fromkeys(cands))[:30]
print("cands", cands)
results = []
for u in cands:
    for method in ("GET", "POST"):
        try:
            if method == "GET":
                r = s.get(u, timeout=15, headers={"Accept": "application/json"})
            else:
                r = s.post(
                    u,
                    json={"query": "køretøj", "page": 1, "pageSize": 10},
                    timeout=15,
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                )
            ct = (r.headers.get("content-type") or "")[:40]
            if r.status_code not in (404, 405) or "json" in ct:
                print(method, r.status_code, ct, len(r.content), u[:90])
                results.append({"m": method, "u": u, "http": r.status_code, "ct": ct, "snip": r.text[:150]})
        except Exception as e:
            pass

Path("_overnight_dk_js_deep.json").write_text(
    json.dumps({"found": found, "results": results}, indent=2, ensure_ascii=False)[:400000],
    encoding="utf-8",
)
print("wrote _overnight_dk_js_deep.json")
