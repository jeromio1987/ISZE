"""Inspect one RO SEAP notice item field map."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://www.e-licitatie.ro",
        "Referer": "https://www.e-licitatie.ro/pub/notices/c-notice/list/0/1",
    }
)
URL = "https://www.e-licitatie.ro/api-pub/NoticeCommon/GetCNoticeList/"
body = {
    "pageSize": 50,
    "pageIndex": 0,
    "startPublicationDate": "2026-07-26",
    "endPublicationDate": "2026-08-25",
    "title": "autovehicul",
}
r = s.post(URL, json=body, timeout=45)
data = r.json()
items = data.get("items") or []
print("total", data.get("total"), "page", len(items))
if items:
    print("keys", list(items[0].keys()))
    print(json.dumps(items[0], indent=2, ensure_ascii=False)[:1500])
# also try Romanian vehicle stems as title filter
for term in ["camion", "autoutilitara", "pickup", "vehicul", "flotă", "flota", "întreținere auto", "reparatii auto"]:
    b = dict(body)
    b["title"] = term
    b["pageSize"] = 5
    rr = s.post(URL, json=b, timeout=45)
    dd = rr.json() if rr.content else {}
    print(term, "total", dd.get("total"), "n", len(dd.get("items") or []))

Path("_probe_ro_sample.json").write_text(
    json.dumps({"total": data.get("total"), "sample": items[:3]}, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
