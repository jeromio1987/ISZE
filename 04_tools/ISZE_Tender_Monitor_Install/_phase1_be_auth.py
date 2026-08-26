# -*- coding: utf-8 -*-
"""Authenticate to BOSA e-Procurement public API and search notices."""
import json
import os
import re
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept": "application/json",
    }
)

AUTH = "https://www.publicprocurement.be/auth"
REALM = "supplier"
CLIENT_ID = "frontend-public"
# Keycloak public-client secret. The portal publishes it in its own front-end
# bundle (https://www.publicprocurement.be/env.config.js), so it is not a
# confidential credential -- but keep it out of git so secret scanners stay quiet.
# Set BE_BOSA_CLIENT_SECRET in the environment, or in the git-ignored
# nordics_api_keys.env alongside this script.
CLIENT_SECRET = os.environ.get("BE_BOSA_CLIENT_SECRET", "")

# Discover OIDC
oidc = s.get(f"{AUTH}/realms/{REALM}/.well-known/openid-configuration", timeout=30)
print("OIDC", oidc.status_code, oidc.headers.get("content-type"))
print(oidc.text[:500] if oidc.status_code == 200 else oidc.text[:200])
oidc_j = oidc.json() if oidc.status_code == 200 else {}
token_url = oidc_j.get("token_endpoint") or f"{AUTH}/realms/{REALM}/protocol/openid-connect/token"
print("token_url", token_url)

# Try client_credentials and password-less public grant variants
token = None
grants = [{"grant_type": "client_credentials", "client_id": CLIENT_ID}]
if CLIENT_SECRET:
    grants.insert(
        0,
        {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
    )
else:
    print("BE_BOSA_CLIENT_SECRET unset - trying the no-secret public grant only")
for grant in grants:
    r = s.post(token_url, data=grant, timeout=30)
    print("GRANT", grant["grant_type"], "secret" in grant, r.status_code, r.text[:300])
    if r.status_code == 200:
        token = r.json().get("access_token")
        print("got token len", len(token or ""))
        break

# Also try device/anonymous patterns if any
if not token and CLIENT_SECRET:
    # Some Keycloak public clients use direct access with scope
    for data in [
        {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "openid",
        },
        {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": "anonymous",
            "password": "anonymous",
        },
    ]:
        r = s.post(token_url, data=data, timeout=30)
        print("ALT", data.get("grant_type"), r.status_code, r.text[:250])
        if r.status_code == 200:
            token = r.json().get("access_token")
            break

# Download search page chunk for endpoint paths
chunks = [
    "https://www.publicprocurement.be/assets/EnterpriseSearchPage-D1_4tEYF.js",
    "https://www.publicprocurement.be/assets/BDAPage-zYRnW4_e.js",
    "https://www.publicprocurement.be/assets/public-BavE7Iut.js",
]
paths = set()
for url in chunks:
    r = s.get(url, timeout=60)
    print("CHUNK", url.split("/")[-1], r.status_code, len(r.content))
    text = r.text
    for m in re.findall(r"[\"'`](/api/sea[^\"'`]{0,120})[\"'`]", text):
        paths.add(m)
    for m in re.findall(r"[\"'`](sea/[^\"'`]{0,120})[\"'`]", text):
        paths.add(m)
    for m in re.findall(r"search[A-Za-z]*\([^)]{0,40}", text):
        pass
    # broader: any path containing notice/publication/search near sea
    for m in re.findall(r"[\"'`]([^\"'`]*(?:notice|publication|bda|search|dossier)[^\"'`]*)[\"'`]", text, flags=re.I):
        if len(m) < 120 and ("/" in m or "sea" in m.lower()):
            paths.add(m)

print("PATH CANDIDATES:")
for p in sorted(paths)[:80]:
    print(" ", p)

# Also mine 700 chunk for sea endpoints (large)
r = s.get("https://www.publicprocurement.be/assets/700-CuWTD8Ia.js", timeout=120)
print("700 chunk", r.status_code, len(r.content))
sea_hits = sorted(set(re.findall(r"[\"'`](/?api/sea[^\"'`]{0,150})[\"'`]", r.text)))
print("sea hits in 700:", len(sea_hits))
for h in sea_hits[:50]:
    print(" ", h)
# also relative service paths
rel = sorted(set(re.findall(r"[\"'`]((?:publications|notices|dossiers|bda)[^\"'`]{0,80})[\"'`]", r.text, flags=re.I)))
print("rel hits sample:")
for h in rel[:40]:
    print(" ", h)

headers = {}
if token:
    headers["Authorization"] = f"Bearer {token}"

# Probe search endpoints with/without auth
candidates = [
    "https://www.publicprocurement.be/api/sea/publications",
    "https://www.publicprocurement.be/api/sea/publications/search",
    "https://www.publicprocurement.be/api/sea/v1/publications",
    "https://www.publicprocurement.be/api/sea/v1/publications/search",
    "https://www.publicprocurement.be/api/sea/public/publications",
    "https://www.publicprocurement.be/api/sea/public/search",
    "https://www.publicprocurement.be/api/sea/search",
    "https://www.publicprocurement.be/api/sea/bda",
    "https://www.publicprocurement.be/api/sea/bda/search",
    "https://www.publicprocurement.be/api/sea/enterprise-search",
    "https://www.publicprocurement.be/api/sea/enterprise/search",
    "https://www.publicprocurement.be/api/dos/public/dossiers",
    "https://www.publicprocurement.be/api/dos/dossiers",
    "https://www.publicprocurement.be/api/dos/v1/dossiers",
]
# add from sea_hits
for h in sea_hits:
    if h.startswith("/"):
        candidates.append("https://www.publicprocurement.be" + h.split("?")[0])
    elif h.startswith("api/"):
        candidates.append("https://www.publicprocurement.be/" + h.split("?")[0])

seen = set()
uniq = []
for u in candidates:
    if u not in seen:
        seen.add(u)
        uniq.append(u)

results = []
for url in uniq:
    for method in ("GET", "POST"):
        for use_auth in (False, True) if token else (False,):
            hdr = dict(headers) if use_auth else {}
            hdr["Accept"] = "application/json"
            hdr["Content-Type"] = "application/json"
            try:
                if method == "GET":
                    rr = s.get(url, headers=hdr, timeout=25, params={"page": 0, "size": 5})
                else:
                    rr = s.post(
                        url,
                        headers=hdr,
                        timeout=25,
                        json={
                            "page": 0,
                            "size": 5,
                            "pageSize": 5,
                            "query": "",
                            "freeText": "voertuig",
                            "cpvCodes": ["34131000"],
                        },
                    )
                body = rr.content
                ct = rr.headers.get("Content-Type", "")
                if len(body) == 1196 and "json" not in ct:
                    continue
                row = {
                    "url": url,
                    "method": method,
                    "auth": use_auth,
                    "status": rr.status_code,
                    "bytes": len(body),
                    "ct": ct,
                    "preview": body[:400].decode("utf-8", errors="replace"),
                }
                try:
                    row["json"] = rr.json()
                except Exception:
                    pass
                results.append(row)
                print(
                    f"{method} auth={use_auth} {rr.status_code} {len(body):6} {url}"
                )
                if row.get("json"):
                    print(" ", json.dumps(row["json"], ensure_ascii=False)[:350])
            except Exception as e:
                print("ERR", method, url, e)

Path(__file__).with_name("_phase1_be_auth_probe.json").write_text(
    json.dumps(
        {
            "got_token": bool(token),
            "sea_hits": sea_hits[:100],
            "results": results,
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)
print("wrote", len(results), "results token=", bool(token))
