#!/usr/bin/env python3
"""Probe PT Base4 public search endpoints without token (honest CODE_READY if blocked)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 Chrome/128",
        "Accept": "application/json, text/html, */*",
    }
)
out = {}
# Legacy base2 REST (often still open with Range header)
cands = [
    ("GET", "https://www.base.gov.pt/base2/rest/anuncios", {"headers": {"Range": "0-19"}}),
    ("GET", "https://www.base.gov.pt/base2/rest/contratos", {"headers": {"Range": "0-19"}}),
    ("GET", "https://www.base.gov.pt/Base4/pt/resultados/", {"params": {"type": "anuncios", "query": "veiculo"}}),
    ("POST", "https://www.base.gov.pt/Base4/pt/resultados/", {"json": {"type": "anuncios", "query": "camion"}}),
    ("GET", "https://www.base.gov.pt/APIBase2/GetAnuncios", {}),
    ("GET", "https://dados.gov.pt/api/1/datasets/?q=contratos+publicos&page_size=5", {}),
]
for method, url, kw in cands:
    try:
        if method == "GET":
            r = s.get(url, timeout=25, **kw)
        else:
            r = s.post(url, timeout=25, **kw)
        out[url] = {
            "http": r.status_code,
            "ct": (r.headers.get("content-type") or "")[:60],
            "len": len(r.content),
            "snip": r.text[:180].replace("\n", " "),
        }
        print(method, r.status_code, out[url]["ct"], out[url]["len"], url[:70])
    except Exception as e:
        out[url] = {"error": str(e)}
        print(method, "ERR", url[:70], e)

Path("_overnight_pt_probe.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("wrote _overnight_pt_probe.json")
