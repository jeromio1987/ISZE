#!/usr/bin/env python3
"""Probe offenevergaben.at for free CSV/JSON AT Kerndaten."""
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
out = {}

urls = [
    "https://offenevergaben.at/",
    "https://offenevergaben.at/auftraege",
    "https://offenevergaben.at/suche",
    "https://offenevergaben.at/api",
    "https://offenevergaben.at/api/tenders",
    "https://offenevergaben.at/api/contracts",
    "https://offenevergaben.at/data",
    "https://offenevergaben.at/download",
    "https://offenevergaben.at/export",
    "https://cdn.offenevergaben.at/",
    "https://offenevergaben.at/static/data/contracts.csv",
    "https://raw.githubusercontent.com/finf/offenevergaben/master/README.md",
]

for u in urls:
    try:
        r = s.get(u, timeout=25)
        out[u] = {
            "http": r.status_code,
            "len": len(r.content),
            "ct": (r.headers.get("content-type") or "")[:60],
            "snip": r.text[:200].replace("\n", " "),
        }
        print(u, r.status_code, len(r.content), out[u]["ct"])
        if r.status_code == 200 and "html" in out[u]["ct"]:
            links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
            interesting = [
                x
                for x in links
                if re.search(r"csv|json|api|download|export|data|\.zip", x, re.I)
            ]
            if interesting:
                out[u]["interesting"] = list(dict.fromkeys(interesting))[:30]
                print("  interesting", out[u]["interesting"][:10])
    except Exception as e:
        out[u] = {"error": str(e)}
        print(u, "ERR", e)

# Also try data.europa.eu harvest of AT Ausschreibung
eu = [
    "https://data.europa.eu/api/hub/search/search?q=ausschreibung%20austria&limit=5",
    "https://data.europa.eu/api/hub/search/search?q=kerndaten%20vergabe&limit=5",
    "https://www.data.gv.at/katalog/dataset?tags=Ausschreibung",
]
for u in eu:
    try:
        r = s.get(u, timeout=25)
        out[u] = {"http": r.status_code, "len": len(r.content), "snip": r.text[:180].replace("\n", " ")}
        print("EU/AT", r.status_code, u[:70], out[u]["snip"][:80])
        if r.status_code == 200 and "json" in (r.headers.get("content-type") or ""):
            try:
                j = r.json()
                out[u]["keys"] = list(j.keys())[:10]
            except Exception:
                pass
    except Exception as e:
        out[u] = {"error": str(e)}

Path("_overnight_at_offenevergaben.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("wrote _overnight_at_offenevergaben.json")
