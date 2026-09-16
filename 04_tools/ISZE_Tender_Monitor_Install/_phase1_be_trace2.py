# -*- coding: utf-8 -*-
"""Belgium auth with public client secret + BelGov-Trace-Id + BDA path mine."""
import json
import os
import re
import sys
import uuid

import requests

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept": "application/json",
        "Origin": "https://www.publicprocurement.be",
        "Referer": "https://www.publicprocurement.be/en/bda",
    }
)

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
    print("grant", "secret" in data, r.status_code, r.text[:200])
    if r.status_code == 200:
        token = r.json()["access_token"]
        break

if not token:
    raise SystemExit("no token")

hdr = {
    "Authorization": f"Bearer {token}",
    "BelGov-Trace-Id": str(uuid.uuid4()),
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Mine BDAQuickSearch deeply
for url in [
    "https://www.publicprocurement.be/assets/BDAQuickSearch-V4qYdZ2W.js",
    "https://www.publicprocurement.be/assets/EnterpriseSearchPage-D1_4tEYF.js",
]:
    text = s.get(url, timeout=30).text
    print("\n===", url.split("/")[-1], "len", len(text), "===")
    # print full small files
    if len(text) < 20000:
        print(text)

# Search big bundle for axios/fetch path templates related to BDA
big = s.get("https://www.publicprocurement.be/assets/700-CuWTD8Ia.js", timeout=120).text

# Find strings containing bda and http methods nearby
patterns = [
    r"[\"'`]([^\"'`]{0,40}bda[^\"'`]{0,80})[\"'`]",
    r"[\"'`]([^\"'`]{0,40}enterprise-search[^\"'`]{0,80})[\"'`]",
    r"[\"'`]([^\"'`]{0,40}EnterpriseSearch[^\"'`]{0,80})[\"'`]",
    r"searchApi[^,]{0,100}",
    r"SEARCH[^,]{0,80}ENDPOINT[^,]{0,80}",
    r"dos/[^\"'`]{1,80}",
    r"sea/[^\"'`]{1,80}",
]
found = set()
for pat in patterns:
    for m in re.findall(pat, big, flags=re.I):
        if isinstance(m, str) and 3 < len(m) < 120:
            found.add(m)
print("\nFOUND strings:")
for f in sorted(found):
    print(" ", f)

# Look for OpenAPI via quarkus
for path in [
    "/api/sea/q/swagger-ui/",
    "/api/sea/q/openapi",
    "/api/sea/q/swagger",
    "/q/openapi",
    "/api/dos/q/openapi",
    "/api/cfg/q/openapi",
]:
    r = s.get("https://www.publicprocurement.be" + path, headers=hdr, timeout=20)
    print("OPENAPI", r.status_code, len(r.content), path, r.text[:100].replace("\n", " "))

# Systematic probe under /api/sea/ and /api/dos/ with auth+trace
bases = [
    "https://www.publicprocurement.be/api/sea",
    "https://www.publicprocurement.be/api/dos",
    "https://www.publicprocurement.be/api/cfg",
    "https://www.publicprocurement.be/api/lex",
    "https://www.publicprocurement.be/api/loc",
    "https://www.publicprocurement.be/api/aud",
    "https://www.publicprocurement.be/api/apb",
    "https://www.publicprocurement.be/api/int",
]
suffixes = [
    "",
    "/",
    "/health",
    "/q/health",
    "/q/openapi",
    "/v1",
    "/v1/",
    "/public",
    "/public/",
    # BDA / search guesses from UI labels
    "/bda",
    "/bda/",
    "/bda/search",
    "/bda/publications",
    "/bda/results",
    "/search",
    "/search/",
    "/search/bda",
    "/search/enterprise",
    "/enterprise-search",
    "/enterprise/search",
    "/publications",
    "/publications/search",
    "/publication-workspaces",
    "/publication-workspaces/search",
    "/dossiers",
    "/dossiers/search",
    "/notices",
    "/notices/search",
]

interesting = []
for base in bases:
    for suf in suffixes:
        url = base + suf
        for method in ("GET", "POST"):
            try:
                if method == "GET":
                    r = s.get(url, headers={**hdr, "BelGov-Trace-Id": str(uuid.uuid4())}, timeout=15, params={"page": 0, "size": 5})
                else:
                    r = s.post(
                        url,
                        headers={**hdr, "BelGov-Trace-Id": str(uuid.uuid4())},
                        timeout=15,
                        json={
                            "page": 0,
                            "size": 5,
                            "query": "voertuig",
                            "freeText": "voertuig",
                            "keywords": "voertuig",
                            "cpvCodes": ["34131000"],
                        },
                    )
                # skip empty SPA
                if len(r.content) == 1196:
                    continue
                # skip pure 404 noise unless non-standard body
                body = r.text
                if r.status_code == 404 and "NOT_FOUND" in body and len(r.content) < 200:
                    continue
                if r.status_code == 500 and len(r.content) < 100:
                    continue
                row = {
                    "method": method,
                    "url": url,
                    "status": r.status_code,
                    "bytes": len(r.content),
                    "preview": body[:400],
                }
                interesting.append(row)
                print(f"{method} {r.status_code} {len(r.content):6} {url}")
                print(" ", body[:250].replace("\n", " "))
                if r.status_code == 200:
                    try:
                        j = r.json()
                        print("  JSON type", type(j).__name__, (list(j.keys())[:15] if isinstance(j, dict) else len(j)))
                    except Exception:
                        pass
            except Exception as e:
                print("ERR", method, url, type(e).__name__)

print("\nInteresting count", len(interesting))
# save
with open("_phase1_be_working.json", "w", encoding="utf-8") as f:
    json.dump(interesting, f, ensure_ascii=False, indent=2)
