# -*- coding: utf-8 -*-
"""Deep probe Belgium /api/* and Israel HTML last resort."""
import json
import re
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,nl;q=0.8,fr;q=0.7",
        "Origin": "https://www.publicprocurement.be",
        "Referer": "https://www.publicprocurement.be/en/search",
    }
)

# 1) Fetch SPA and extract every /api/... string from inline + linked JS
r = s.get("https://www.publicprocurement.be/en", timeout=45)
print("SPA", r.status_code, len(r.content))
print(r.text)
# The shell might load JS dynamically; look for chunk manifests
# Try known webpack/vite patterns
js_candidates = []
for path in [
    "/assets/index.js",
    "/static/js/main.js",
    "/js/app.js",
    "/en/assets/index.js",
]:
    jr = s.get("https://www.publicprocurement.be" + path, timeout=20)
    print("try", path, jr.status_code, len(jr.content), jr.headers.get("content-type"))
    if jr.status_code == 200 and len(jr.content) > 5000:
        js_candidates.append((path, jr.text))

# From earlier probe: a 1592-byte response had abs APIs — find which URL
raw = json.loads(Path(__file__).with_name("_phase1_probe_raw.json").read_text(encoding="utf-8"))
for row in raw:
    if row.get("abs_apis"):
        print("FROM RAW", row.get("name"), row.get("url"), "abs", row["abs_apis"])
        # re-fetch that JS
        try:
            jr = s.get(row["url"], timeout=45)
            text = jr.text
            # extract richer patterns
            for pat in [
                r"/api/[a-zA-Z0-9_./?=&%-]+",
                r"https://[^\"'\s]+api[^\"'\s]*",
                r"[\"'](sea|dos|pub|notice|search|publication)[^\"']*[\"']",
            ]:
                hits = sorted(set(re.findall(pat, text)))[:40]
                if hits:
                    print("  pat", pat[:40], "->", hits[:20])
        except Exception as e:
            print("  err", e)

# 2) Probe /api/sea with POST and common payloads
sea_paths = [
    "https://www.publicprocurement.be/api/sea/",
    "https://www.publicprocurement.be/api/sea/search",
    "https://www.publicprocurement.be/api/sea/notices",
    "https://www.publicprocurement.be/api/sea/v1/search",
    "https://www.publicprocurement.be/api/sea/publications",
    "https://www.publicprocurement.be/api/sea/publications/search",
    "https://www.publicprocurement.be/api/dos/",
    "https://www.publicprocurement.be/api/dos/search",
    "https://www.publicprocurement.be/api/dos/dossiers",
    "https://www.publicprocurement.be/api/pub/",
    "https://www.publicprocurement.be/api/pub/publications",
    "https://www.publicprocurement.be/api/pub/search",
    "https://www.publicprocurement.be/api/apb/",
    "https://www.publicprocurement.be/api/apb/health",
    "https://www.publicprocurement.be/api/apb/version",
    "https://www.publicprocurement.be/api/cfg/",
    "https://www.publicprocurement.be/api/cfg/config",
    "https://www.publicprocurement.be/api/cfg/public",
    "https://www.publicprocurement.be/api/loc/",
    "https://www.publicprocurement.be/api/loc/languages",
    "https://www.publicprocurement.be/api/int/",
    "https://www.publicprocurement.be/api/aud/",
]

payloads = [
    None,
    {},
    {"page": 0, "size": 10},
    {"query": "", "page": 0, "size": 10},
    {"cpv": ["34131000"], "page": 0, "size": 5},
    {"freeText": "vehicle", "page": 0, "size": 5},
    {"keywords": "voertuig"},
]

results = []
for url in sea_paths:
    for method in ("GET", "POST", "OPTIONS"):
        try:
            if method == "GET":
                rr = s.get(url, timeout=25)
            elif method == "OPTIONS":
                rr = s.options(url, timeout=25)
            else:
                rr = s.post(url, json={"page": 0, "size": 5}, timeout=25)
            body = rr.content
            ct = rr.headers.get("Content-Type", "")
            preview = body[:200]
            is_json = "json" in ct.lower()
            j = None
            if is_json:
                try:
                    j = rr.json()
                except Exception:
                    pass
            interesting = rr.status_code not in (404,) or is_json
            # skip pure SPA shells
            if len(body) == 1196 and not is_json:
                continue
            row = {
                "url": url,
                "method": method,
                "status": rr.status_code,
                "bytes": len(body),
                "ct": ct,
                "allow": rr.headers.get("Allow"),
                "preview": preview.decode("utf-8", errors="replace"),
            }
            if j is not None:
                row["json_keys"] = list(j.keys()) if isinstance(j, dict) else type(j).__name__
                row["json"] = j
            results.append(row)
            print(
                f"{method:7} {rr.status_code} {len(body):6} {ct[:40]:40} {url}"
            )
            if j:
                print("   ", json.dumps(j, ensure_ascii=False)[:300])
        except Exception as e:
            print(method, url, "ERR", e)

# Try POST sea/search with more payloads
for path in [
    "/api/sea/search",
    "/api/sea/publications/search",
    "/api/sea/v1/publications/search",
    "/api/dos/dossiers/search",
]:
    for payload in payloads[1:]:
        url = "https://www.publicprocurement.be" + path
        try:
            rr = s.post(url, json=payload, timeout=25)
            if len(rr.content) == 1196:
                continue
            print(
                "POST",
                rr.status_code,
                len(rr.content),
                path,
                "payload",
                payload,
                rr.text[:200],
            )
        except Exception as e:
            print("ERR", path, e)

# OAuth / auth endpoints
for url in [
    "https://www.publicprocurement.be/oauth/token",
    "https://www.publicprocurement.be/auth/realms/eprocurement",
    "https://idp.publicprocurement.be/",
    "https://login.publicprocurement.be/",
    "https://my.publicprocurement.be/",
    "https://bosa.belgium.be/nl/services/helpdesk-e-procurement",
]:
    try:
        rr = s.get(url, timeout=25, allow_redirects=True)
        print("AUTH", url, "->", rr.url, rr.status_code, len(rr.content), rr.headers.get("content-type"))
    except Exception as e:
        print("AUTH ERR", url, e)

Path(__file__).with_name("_phase1_be_api_probe.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
)
print("wrote be api probe", len(results))
