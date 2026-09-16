#!/usr/bin/env python3
"""Standalone DK udbud.dk probe — finds SPA API without editing tender_scraper_v3 yet."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 Chrome/128", "Accept": "*/*"}
s = requests.Session()
s.headers.update(UA)
out = {"assets": [], "apis": []}

r = s.get("https://udbud.dk/", timeout=30)
print("home", r.status_code, len(r.content))
# Angular/Vite assets
assets = re.findall(r'src="(.*?\.js[^"]*)"', r.text)
out["assets"] = assets[:30]
print("assets", assets[:10])

api_hits = []
for a in assets[:15]:
    url = a if a.startswith("http") else ("https://udbud.dk" + (a if a.startswith("/") else "/" + a))
    try:
        js = s.get(url, timeout=40).text
    except Exception as e:
        print("asset ERR", url, e)
        continue
    # look for api hosts / paths
    for m in re.findall(r"https?://[a-zA-Z0-9._/-]*(?:api|udbud|mitudbud|erhvervsstyrelse)[a-zA-Z0-9._/-]*", js):
        api_hits.append(m)
    for m in re.findall(r"[\"'](/api/[^\"']+)[\"']", js):
        api_hits.append(m)
    for m in re.findall(r"[\"'](https?://[^\"']+graphql[^\"']*)[\"']", js, flags=re.I):
        api_hits.append(m)

api_hits = list(dict.fromkeys(api_hits))
out["apis"] = api_hits[:80]
print("api hits", len(api_hits))
for u in api_hits[:25]:
    print(" ", u)

# Try promising endpoints
for u in api_hits[:20]:
    if not u.startswith("http"):
        u = "https://udbud.dk" + u
    if any(x in u.lower() for x in ("google", "facebook", "sentry", "datadog", "cdn.")):
        continue
    try:
        rr = s.get(u, timeout=20, headers={"Accept": "application/json"})
        ct = (rr.headers.get("content-type") or "")[:50]
        print("GET", rr.status_code, ct, len(rr.content), u[:100])
        out.setdefault("gets", []).append(
            {"url": u, "http": rr.status_code, "ct": ct, "len": len(rr.content), "snip": rr.text[:120]}
        )
    except Exception as e:
        print("GET ERR", u[:80], e)

# Also try KFST / erhvervsstyrelsen open data
for u in [
    "https://udbud.dk/api/notices",
    "https://udbud.dk/api/v1/notices",
    "https://api.udbud.dk/api/notices",
    "https://gateway.pipeworx.io/udbud-dk/mcp",
]:
    try:
        rr = s.get(u, timeout=20)
        print("extra", rr.status_code, len(rr.content), u)
    except Exception as e:
        print("extra ERR", u, e)

Path("_overnight_dk_spa_probe.json").write_text(json.dumps(out, indent=2, ensure_ascii=False)[:500000], encoding="utf-8")
print("wrote _overnight_dk_spa_probe.json")
