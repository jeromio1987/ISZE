#!/usr/bin/env python3
"""Hit DK soegning-prefixed public search endpoints."""
from __future__ import annotations

import json
from pathlib import Path

import requests

s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 Chrome/128",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://udbud.dk",
        "Referer": "https://udbud.dk/soeg",
    }
)
bodies = [
    {"fritekst": "køretøj", "page": 0, "size": 25},
    {"searchText": "lastebil", "pageNumber": 0, "pageSize": 25},
    {"query": "køretøj"},
    {"fritekstSoegning": "køretøj", "side": 0, "antal": 25},
]
urls = [
    "https://udbud.dk/soegning/public/soegeresultat",
    "https://udbud.dk/soegning/soegeresultat",
    "https://udbud.dk/public/soegeresultat",
    "https://udbud.dk/soegning/api/public/soegeresultat",
]
out = {}
for url in urls:
    for method in ("GET", "POST", "PUT"):
        for i, body in enumerate(bodies[:2] if method != "GET" else [{}]):
            try:
                if method == "GET":
                    r = s.get(url, params={"fritekst": "køretøj", "page": 0}, timeout=20)
                elif method == "POST":
                    r = s.post(url, json=body, timeout=20)
                else:
                    r = s.put(url, json=body, timeout=20)
                ct = (r.headers.get("content-type") or "")[:50]
                print(method, r.status_code, ct, len(r.content), url.split(".dk")[-1], r.text[:100].replace("\n", " "))
                key = f"{method} {url} b{i}"
                out[key] = {"http": r.status_code, "ct": ct, "len": len(r.content), "snip": r.text[:200]}
                if r.status_code == 200 and "json" in ct and len(r.content) > 20:
                    print("  HIT JSON")
                    try:
                        j = r.json()
                        out[key]["sample"] = str(j)[:300]
                    except Exception:
                        pass
            except Exception as e:
                print("ERR", method, url, e)

Path("_overnight_dk_soegeresultat.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
