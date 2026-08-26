# -*- coding: utf-8 -*-
"""Belgium working publications search with stable auth."""
import json
import os
import sys
import uuid

import requests

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"

token_url = "https://www.publicprocurement.be/auth/realms/supplier/protocol/openid-connect/token"
CLIENT_ID = "frontend-public"
# Public front-end value from https://www.publicprocurement.be/env.config.js.
# Kept out of git: set BE_BOSA_CLIENT_SECRET in the environment.
CLIENT_SECRET = os.environ.get("BE_BOSA_CLIENT_SECRET", "")

token = None
attempts = [{"grant_type": "client_credentials", "client_id": CLIENT_ID}]
if CLIENT_SECRET:
    attempts.insert(
        0,
        {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
    )
else:
    print("BE_BOSA_CLIENT_SECRET unset - trying the no-secret public grant only")
for data in attempts:
    r = s.post(token_url, data=data, timeout=30)
    print("auth", r.status_code, "secret=" + str("client_secret" in data), r.text[:180])
    if r.status_code == 200:
        token = r.json()["access_token"]
        break
if not token:
    raise SystemExit("auth failed")

hdr = {
    "Authorization": f"Bearer {token}",
    "BelGov-Trace-Id": str(uuid.uuid4()),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Accept-Language": "nl",
    "Origin": "https://www.publicprocurement.be",
    "Referer": "https://www.publicprocurement.be/nl/bda",
}

url = "https://www.publicprocurement.be/api/sea/search/publications"
payload = {
    "terms": "voertuig",
    "cpvCodes": ["34131000", "34113000", "34136000", "34130000", "50110000", "50112000", "50116000", "50111000"],
    "withActiveSubmissionDeadline": True,
    "page": 1,
    "pageSize": 5,
}
r = s.post(url, headers=hdr, json=payload, timeout=45)
print("POST", r.status_code, len(r.content), r.headers.get("content-type"))
print(r.text[:1500])

if r.status_code == 200:
    j = r.json()
    print("keys", list(j.keys()))
    pubs = j.get("publications") or []
    print("n", len(pubs), "total", j.get("totalCount"))
    for p in pubs[:2]:
        print(json.dumps(p, ensure_ascii=False)[:1000])
else:
    # retry without deadline filter / with empty terms
    for payload2 in [
        {"page": 1, "pageSize": 5},
        {"terms": "", "page": 1, "pageSize": 5},
        {"cpvCodes": ["50110000"], "page": 1, "pageSize": 5},
        {"terms": "voertuig", "page": 1, "pageSize": 5},
    ]:
        hdr["BelGov-Trace-Id"] = str(uuid.uuid4())
        r = s.post(url, headers=hdr, json=payload2, timeout=45)
        print("retry", payload2, "->", r.status_code, len(r.content), r.text[:300])
        if r.status_code == 200:
            j = r.json()
            pubs = j.get("publications") or []
            print("OK keys", list(j.keys()), "n", len(pubs), "total", j.get("totalCount"))
            if pubs:
                print(json.dumps(pubs[0], ensure_ascii=False)[:1200])
            break
