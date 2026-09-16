# -*- coding: utf-8 -*-
import json
import re
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")
RAW = Path(__file__).with_name("_phase1_probe_raw.json")
s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
)

# --- TED counts from probe raw ---
data = json.loads(RAW.read_text(encoding="utf-8"))
for row in data:
    name = row.get("name", "")
    if name.startswith("TED_"):
        print(
            name,
            "status",
            row.get("status"),
            "n_notices",
            row.get("n_notices"),
            "totalNoticeCount",
            row.get("totalNoticeCount") or row.get("total"),
            "sample_keys",
            list((row.get("sample") or {}).keys())[:8] if isinstance(row.get("sample"), dict) else None,
        )
        if row.get("notices_sample"):
            n0 = row["notices_sample"][0]
            print("  sample TI:", n0.get("TI") or n0.get("title-eng") or str(n0)[:200])
            print("  sample CY/PD/DD/ND:", n0.get("CY"), n0.get("PD"), n0.get("DD"), n0.get("ND"))
        if row.get("sample") and isinstance(row["sample"], dict) and "ND" in row["sample"]:
            n0 = row["sample"]
            print("  sample ND/CY/PD/DD:", n0.get("ND"), n0.get("CY"), n0.get("PD"), n0.get("DD"))
            print("  TI:", str(n0.get("TI"))[:160])

print("\n=== Israel freshness ===")
for name in ["tenders", "exemptions"]:
    r = s.get(
        "https://data.gov.il/api/3/action/package_show",
        params={"id": name},
        timeout=60,
    )
    p = r.json()["result"]
    print(name, "metadata_modified=", p.get("metadata_modified"))
    for res in p.get("resources") or []:
        print(
            " ",
            res.get("id"),
            "last_modified=",
            res.get("last_modified"),
            "datastore_active=",
            res.get("datastore_active"),
        )

url = "https://data.gov.il/api/3/action/datastore_search"
for q in ["2025", "2026", "2024", "2023", "2022"]:
    r = s.get(
        url,
        params={
            "resource_id": "7038b3e6-a74d-442e-b16b-466c8196124a",
            "q": q,
            "limit": 3,
            "sort": "_id desc",
        },
        timeout=60,
    )
    j = r.json()["result"]
    print("q", q, "total", j["total"])
    for rec in j["records"][:2]:
        print(
            " ",
            rec.get("תאריך פרסום"),
            rec.get("סטטוס"),
            (rec.get("שם הליך") or "")[:70],
        )

sql = 'SELECT * FROM "7038b3e6-a74d-442e-b16b-466c8196124a" ORDER BY _id DESC LIMIT 5'
r = s.get(
    "https://data.gov.il/api/3/action/datastore_search_sql",
    params={"sql": sql},
    timeout=60,
)
print("SQL", r.status_code, r.json().get("success"), r.json().get("error"))
for rec in (r.json().get("result") or {}).get("records") or []:
    print(
        " ",
        rec.get("_id"),
        rec.get("תאריך פרסום"),
        rec.get("סטטוס"),
        (rec.get("שם הליך") or "")[:60],
    )

print("\n=== Belgium SPA deep dive ===")
r = s.get("https://www.publicprocurement.be/en", timeout=45)
print("home", r.status_code, len(r.content), r.headers.get("content-type"))
print(r.text[:900])
scripts = re.findall(r'src=["\']([^"\']+)["\']', r.text)
print("scripts", scripts)

# Try common SPA entrypoints that may return real HTML with hashed bundles
candidates = [
    "https://www.publicprocurement.be/",
    "https://www.publicprocurement.be/index.html",
    "https://www.publicprocurement.be/en/search",
    "https://www.publicprocurement.be/en/supplier",
    "https://www.publicprocurement.be/fr",
    "https://www.publicprocurement.be/nl",
]
for u in candidates:
    rr = s.get(u, timeout=30)
    scripts = re.findall(r'src=["\']([^"\']+)["\']', rr.text)
    links = re.findall(r'href=["\']([^"\']+\.js[^"\']*)["\']', rr.text)
    print(u, rr.status_code, len(rr.content), "scripts", scripts, "js_hrefs", links[:5])
    print("  preview", rr.text[:180].replace("\n", " "))
