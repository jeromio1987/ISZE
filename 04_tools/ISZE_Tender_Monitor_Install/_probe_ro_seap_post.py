"""Probe RO e-licitatie GetCNoticeList POST for vehicle notices."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://www.e-licitatie.ro",
        "Referer": "https://www.e-licitatie.ro/pub/notices/c-notice/list/0/1",
    }
)

URL = "https://www.e-licitatie.ro/api-pub/NoticeCommon/GetCNoticeList/"
# Try several body shapes seen on SEAP Angular apps
bodies = [
    {
        "pageSize": 20,
        "pageIndex": 0,
        "startPublicationDate": "2026-07-25",
        "endPublicationDate": "2026-08-25",
        "cNoticeSys": None,
        "hasTenderElectronicCatalog": None,
        "isOnlineHelpDesk": None,
        "sortProperties": [],
        "title": "autovehicul",
    },
    {
        "pageSize": 20,
        "pageNumber": 1,
        "publicationDateStart": "2026-07-25T00:00:00.000Z",
        "publicationDateEnd": "2026-08-25T23:59:59.000Z",
        "contractObjectName": "autovehicule",
    },
    {"pageSize": 10, "pageIndex": 0},
    {},
]

results = []
for i, body in enumerate(bodies):
    row = {"i": i, "body_keys": list(body.keys())}
    try:
        r = s.post(URL, json=body, timeout=45)
        row["status"] = r.status_code
        row["bytes"] = len(r.content or b"")
        row["ctype"] = r.headers.get("Content-Type")
        preview = (r.content or b"")[:500]
        row["preview"] = preview.decode("utf-8", errors="replace")
        if (r.content or b"").startswith((b"{", b"[")):
            data = r.json()
            row["top_keys"] = list(data.keys()) if isinstance(data, dict) else type(data).__name__
            items = None
            if isinstance(data, dict):
                for k in ("items", "Items", "data", "Data", "list", "result", "Result"):
                    if isinstance(data.get(k), list):
                        items = data[k]
                        row["items_key"] = k
                        break
                row["total"] = data.get("total") or data.get("Total") or data.get("totalCount")
            if items is not None:
                row["n_items"] = len(items)
                if items:
                    row["sample_keys"] = list(items[0].keys()) if isinstance(items[0], dict) else None
                    row["sample"] = {
                        k: items[0].get(k)
                        for k in list(items[0].keys())[:12]
                    } if isinstance(items[0], dict) else items[0]
    except Exception as exc:
        row["error"] = str(exc)
    results.append(row)
    print(i, row.get("status"), row.get("n_items"), row.get("total"), row.get("error"), (row.get("preview") or "")[:120])

# Also try SearchNoticeCommon endpoints
alts = [
    "https://www.e-licitatie.ro/api-pub/NoticeCommon/GetCNoticeList",
    "https://www.e-licitatie.ro/api-pub/SearchNoticeCommon/GetCNoticeList/",
    "https://www.e-licitatie.ro/api-pub/CNoticeCommon/GetCNoticeList/",
]
for u in alts:
    try:
        r = s.post(u, json={"pageSize": 5, "pageIndex": 0}, timeout=30)
        print("ALT", u, r.status_code, (r.content or b"")[:100])
        results.append({"url": u, "status": r.status_code, "preview": (r.content or b"")[:200].decode("utf-8", errors="replace")})
    except Exception as exc:
        print("ALT ERR", u, exc)
        results.append({"url": u, "error": str(exc)})

path = HERE / "_probe_ro_seap_post.json"
path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print("Wrote", path)
