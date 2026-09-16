# -*- coding: utf-8 -*-
"""Call Belgium BDA search: POST /api/sea/search/publications"""
import json
import re
import sys
import uuid

import requests

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0"

# Extract getPublications body from bundle
big = s.get("https://www.publicprocurement.be/assets/700-CuWTD8Ia.js", timeout=120).text
i = big.find("getPublications(){return")
print("getPublications idx", i)
print(big[i : i + 1800])

# Token
token_url = "https://www.publicprocurement.be/auth/realms/supplier/protocol/openid-connect/token"
tr = s.post(
    token_url,
    data={"grant_type": "client_credentials", "client_id": "frontend-public"},
    timeout=30,
)
print("\ntoken", tr.status_code)
token = tr.json()["access_token"]

hdr = {
    "Authorization": f"Bearer {token}",
    "BelGov-Trace-Id": str(uuid.uuid4()),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Accept-Language": "en",
    "Origin": "https://www.publicprocurement.be",
    "Referer": "https://www.publicprocurement.be/en/bda",
}

urls = [
    "https://www.publicprocurement.be/api/sea/search/publications",
    "https://www.publicprocurement.be/api/sea/search/enterprises",
]

# Try several payload shapes inferred from UI filters
payloads = [
    {},
    {"page": 1, "pageSize": 5},
    {"terms": "voertuig", "page": 1, "pageSize": 5},
    {
        "terms": "voertuig",
        "cpvCodes": ["34131000", "50110000"],
        "page": 1,
        "pageSize": 5,
        "withActiveSubmissionDeadline": True,
    },
    {
        "query": "voertuig",
        "cpvCodes": ["34131000"],
        "page": 1,
        "size": 5,
    },
]

# Also try GET with query params for enterprises (JS uses GET)
print("\n=== GET enterprises ===")
r = s.get(
    "https://www.publicprocurement.be/api/sea/search/enterprises",
    headers=hdr,
    params={
        "visibility": "PUBLIC",
        "terms": "garage",
        "cpvCodes": "50110000",
        "page": 1,
        "pageSize": 5,
        "collapsePolicy": "BY_SIMILAR_COUNTRY_AND_ENTERPRISE_NUMBER",
    },
    timeout=30,
)
print(r.status_code, len(r.content), r.headers.get("content-type"))
print(r.text[:800])

print("\n=== POST publications ===")
for payload in payloads:
    hdr["BelGov-Trace-Id"] = str(uuid.uuid4())
    # try as JSON body
    r = s.post(
        "https://www.publicprocurement.be/api/sea/search/publications",
        headers=hdr,
        json=payload,
        timeout=30,
    )
    print("JSON body", payload, "->", r.status_code, len(r.content))
    print(" ", r.text[:500])
    if r.status_code == 200:
        j = r.json()
        print(" KEYS", list(j.keys()) if isinstance(j, dict) else type(j))
        break

    # try as query params with empty body
    hdr["BelGov-Trace-Id"] = str(uuid.uuid4())
    r = s.post(
        "https://www.publicprocurement.be/api/sea/search/publications",
        headers=hdr,
        params=payload if payload else None,
        json={},
        timeout=30,
    )
    print("params+empty", payload, "->", r.status_code, len(r.content))
    print(" ", r.text[:500])
    if r.status_code == 200:
        j = r.json()
        print(" KEYS", list(j.keys()) if isinstance(j, dict) else type(j))
        # sample
        for key in ("publications", "content", "results", "items", "data"):
            if isinstance(j, dict) and j.get(key):
                sample = j[key][0] if isinstance(j[key], list) else j[key]
                print(" SAMPLE", json.dumps(sample, ensure_ascii=False)[:800])
        break

# Also GET publications?
r = s.get(
    "https://www.publicprocurement.be/api/sea/search/publications",
    headers={**hdr, "BelGov-Trace-Id": str(uuid.uuid4())},
    params={"terms": "voertuig", "page": 1, "pageSize": 5},
    timeout=30,
)
print("\nGET publications", r.status_code, len(r.content), r.text[:400])
