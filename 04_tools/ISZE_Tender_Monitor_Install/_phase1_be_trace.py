# -*- coding: utf-8 -*-
"""Belgium: token + BelGov-Trace-Id + mine BDA search endpoints."""
import json
import re
import sys
import uuid
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept": "application/json",
        "Origin": "https://www.publicprocurement.be",
        "Referer": "https://www.publicprocurement.be/en/search",
    }
)

# Token (client_credentials works without secret for frontend-public)
token_url = "https://www.publicprocurement.be/auth/realms/supplier/protocol/openid-connect/token"
tr = s.post(token_url, data={"grant_type": "client_credentials", "client_id": "frontend-public"}, timeout=30)
print("token", tr.status_code)
token = tr.json()["access_token"]

trace = str(uuid.uuid4())
auth_headers = {
    "Authorization": f"Bearer {token}",
    "BelGov-Trace-Id": trace,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Mine BDAQuickSearch and related chunks
chunks = [
    "https://www.publicprocurement.be/assets/BDAQuickSearch-V4qYdZ2W.js",
    "https://www.publicprocurement.be/assets/EnterpriseSearchPage-D1_4tEYF.js",
    "https://www.publicprocurement.be/assets/BDAPage-zYRnW4_e.js",
]
# also find more chunk names from public bundle
pub = s.get("https://www.publicprocurement.be/assets/public-BavE7Iut.js", timeout=30).text
more = re.findall(r'assets/([A-Za-z0-9_-]+\.js)', pub)
print("more chunks", sorted(set(more))[:40])
for name in sorted(set(more)):
    if any(k.lower() in name.lower() for k in ("bda", "search", "enterprise", "publication", "notice")):
        chunks.append(f"https://www.publicprocurement.be/assets/{name}")

all_paths = set()
for url in chunks:
    r = s.get(url, timeout=60)
    print(f"CHUNK {r.status_code} {len(r.content):7} {url.split('/')[-1]}")
    text = r.text
    for pat in [
        r"[\"'`](/api/[^\"'`]{1,160})[\"'`]",
        r"[\"'`](api/[^\"'`]{1,160})[\"'`]",
        r"\.(get|post|put|delete)\([`\"']([^`\"']+)[`\"']",
        r"baseURL[^,]{0,40}",
        r"SEARCH_API[^,]{0,80}",
        r"sea[^\"'`]{0,60}",
    ]:
        hits = re.findall(pat, text, flags=re.I)
        if hits and len(str(hits[0])) < 200:
            # normalize
            for h in hits:
                if isinstance(h, tuple):
                    h = h[-1]
                if isinstance(h, str) and ("/" in h or "api" in h.lower() or "bda" in h.lower() or "search" in h.lower()):
                    if len(h) < 180:
                        all_paths.add(h)

print("\nALL PATH-LIKE:")
for p in sorted(all_paths):
    print(" ", p)

# Also grep 700 chunk for '/bda' and 'enterprise-search' API paths more carefully
big = s.get("https://www.publicprocurement.be/assets/700-CuWTD8Ia.js", timeout=120).text
# Look near VITE_SEARCH or sea endpoint usage
for key in ["api/sea", "/sea/", "enterprise-search", "bda/search", "searchBda", "BdaSearch", "publications:search"]:
    idxs = [m.start() for m in re.finditer(re.escape(key), big, flags=re.I)]
    print(f"key {key}: {len(idxs)} hits")
    for i in idxs[:3]:
        print("  ctx:", big[max(0, i - 80) : i + 120].replace("\n", " "))

# OpenAPI / swagger under api gateways
for url in [
    "https://www.publicprocurement.be/api/sea/q/swagger-ui",
    "https://www.publicprocurement.be/api/sea/swagger",
    "https://www.publicprocurement.be/api/sea/openapi",
    "https://www.publicprocurement.be/api/sea/openapi.json",
    "https://www.publicprocurement.be/api/sea/q/openapi",
    "https://www.publicprocurement.be/api/dos/q/openapi",
    "https://www.publicprocurement.be/api/dos/openapi.json",
    "https://www.publicprocurement.be/api/sea/health",
    "https://www.publicprocurement.be/api/sea/q/health",
    "https://www.publicprocurement.be/api/dos/health",
    "https://www.publicprocurement.be/api/dos/q/health",
]:
    r = s.get(url, headers=auth_headers, timeout=20)
    print("DOC", r.status_code, len(r.content), url, r.text[:120].replace("\n", " "))

# Probe dossiers with trace id + common query params
probe = []
dossier_urls = [
    ("GET", "https://www.publicprocurement.be/api/dos/dossiers", {"page": "0", "size": "5"}),
    ("GET", "https://www.publicprocurement.be/api/dos/dossiers/search", {"page": "0", "size": "5"}),
    ("POST", "https://www.publicprocurement.be/api/dos/dossiers/search", None),
    ("GET", "https://www.publicprocurement.be/api/sea/", None),
    ("GET", "https://www.publicprocurement.be/api/cfg/", None),
    ("GET", "https://www.publicprocurement.be/api/cfg/config", None),
    ("GET", "https://www.publicprocurement.be/api/cfg/public", None),
    ("GET", "https://www.publicprocurement.be/api/lex/", None),
    ("GET", "https://www.publicprocurement.be/api/loc/countries", None),
    ("GET", "https://www.publicprocurement.be/api/loc/languages", None),
]

# Add path candidates that look like API
for p in sorted(all_paths):
    if p.startswith("/api/") or p.startswith("api/"):
        u = p if p.startswith("http") else "https://www.publicprocurement.be/" + p.lstrip("/")
        probe.append(("GET", u.split("?")[0], None))
        probe.append(("POST", u.split("?")[0], None))

for method, url, params in dossier_urls + probe[:40]:
    try:
        if method == "GET":
            r = s.get(url, headers=auth_headers, params=params, timeout=25)
        else:
            r = s.post(
                url,
                headers=auth_headers,
                timeout=25,
                json={
                    "page": 0,
                    "size": 5,
                    "query": "voertuig",
                    "freeText": "voertuig",
                    "cpvCodes": ["34131000", "50110000"],
                },
            )
        body = r.content
        if len(body) == 1196:
            continue
        print(f"{method} {r.status_code} {len(body):6} {url}")
        preview = body[:350].decode("utf-8", errors="replace")
        print(" ", preview)
        try:
            j = r.json()
            # if looks like results
            if isinstance(j, dict) and any(k in j for k in ("content", "results", "items", "data", "hits")):
                print("  KEYS", list(j.keys()))
            if isinstance(j, list) and j:
                print("  list0 keys", list(j[0].keys())[:20] if isinstance(j[0], dict) else type(j[0]))
        except Exception:
            pass
    except Exception as e:
        print("ERR", method, url, e)

# Try quarkus-style paths often used by BE gov
extra = [
    "/api/sea/v1/bda/search",
    "/api/sea/v1/bda",
    "/api/sea/bda/publications",
    "/api/sea/search/bda",
    "/api/sea/search/enterprise",
    "/api/sea/enterprise/search",
    "/api/sea/v1/enterprise-search",
    "/api/sea/v1/search",
    "/api/dos/v1/publication-workspaces",
    "/api/dos/publication-workspaces",
    "/api/dos/v1/publications",
]
for path in extra:
    url = "https://www.publicprocurement.be" + path
    for method in ("GET", "POST"):
        try:
            if method == "GET":
                r = s.get(url, headers=auth_headers, params={"page": 0, "size": 5}, timeout=20)
            else:
                r = s.post(
                    url,
                    headers=auth_headers,
                    json={"page": 0, "size": 5, "query": "voertuig"},
                    timeout=20,
                )
            if len(r.content) == 1196:
                continue
            print(f"EX {method} {r.status_code} {len(r.content):6} {path} {r.text[:200]}")
        except Exception as e:
            print("EX ERR", path, e)

Path(__file__).with_name("_phase1_be_trace_probe.json").write_text(
    json.dumps({"paths": sorted(all_paths)}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
