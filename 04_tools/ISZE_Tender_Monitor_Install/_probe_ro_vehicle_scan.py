"""Find RO SEAP body params that actually filter; scan page for vehicle hits."""
from __future__ import annotations

import json
import re
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

# Try CPV-related field names
trials = []
for body in [
    {"pageSize": 20, "pageIndex": 0, "cpvCode": "34130000"},
    {"pageSize": 20, "pageIndex": 0, "cpvCodes": ["34130000", "34131000"]},
    {"pageSize": 20, "pageIndex": 0, "cpvCodeAndName": "3413"},
    {"pageSize": 20, "pageIndex": 0, "contractObjectName": "autovehicul"},
    {"pageSize": 20, "pageIndex": 0, "startPublicationDate": "2026-08-01", "endPublicationDate": "2026-08-25", "sysNoticeTypeIds": [2]},
]:
    r = s.post(URL, json=body, timeout=40)
    data = r.json() if r.content else {}
    items = data.get("items") or []
    titles = [(it.get("cpvCodeAndName") or "")[:60] for it in items[:3]]
    trials.append({"body": body, "total": data.get("total"), "n": len(items), "titles": titles})
    print("total", data.get("total"), "body", body, "cpv_sample", titles)

# Client-side scan first N pages for vehicle CPV/keywords
KW = (
    "autovehicul", "autoutilitara", "autoutilitară", "camion", "pickup", "pick-up",
    "vehicul", "flota", "flotă", "chassis", "isuzu", "d-max", "utilitara", "utilitară",
    "întreținere auto", "intretinere auto", "reparatii auto", "reparații auto",
    "autoturism", "microbuz",  # may noise — gate later
)
CPV_RE = re.compile(r"\b(3413|34113|34136|5011)\d*")
hits = []
seen = set()
for page in range(0, 15):
    body = {
        "pageSize": 100,
        "pageIndex": page,
        "startPublicationDate": "2026-07-26",
        "endPublicationDate": "2026-08-25",
    }
    r = s.post(URL, json=body, timeout=45)
    data = r.json() if r.content else {}
    items = data.get("items") or []
    if page == 0:
        print("scan total", data.get("total"))
    if not items:
        break
    for it in items:
        nid = it.get("cNoticeId") or it.get("noticeId")
        if nid in seen:
            continue
        title = (it.get("contractTitle") or "").lower()
        cpv = (it.get("cpvCodeAndName") or "")
        blob = f"{title} {cpv.lower()}"
        if CPV_RE.search(cpv) or any(k in blob for k in KW):
            # skip obvious works-only if no vehicle stem
            if not CPV_RE.search(cpv) and not any(
                k in blob for k in ("autovehicul", "camion", "pickup", "autoutilit", "vehicul", "flot", "isuzu", "chassis")
            ):
                continue
            seen.add(nid)
            hits.append(
                {
                    "id": nid,
                    "title": (it.get("contractTitle") or "")[:100],
                    "cpv": cpv[:80],
                    "buyer": (it.get("contractingAuthorityNameAndFN") or "")[:80],
                    "pub": it.get("noticeStateDate"),
                }
            )
print("vehicle-ish hits in 15 pages", len(hits))
for h in hits[:20]:
    print("-", h["cpv"][:40], "|", h["title"][:70])

Path("_probe_ro_vehicle_scan.json").write_text(
    json.dumps({"trials": trials, "hits": hits}, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
