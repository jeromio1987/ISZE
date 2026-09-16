# -*- coding: utf-8 -*-
"""Mine Belgium SPA JS for API base URLs; probe discovered endpoints."""
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
        "Accept": "*/*",
        "Referer": "https://www.publicprocurement.be/en/search",
        "Origin": "https://www.publicprocurement.be",
    }
)

assets = [
    "https://www.publicprocurement.be/env.config.js",
    "https://www.publicprocurement.be/assets/public-BavE7Iut.js",
    "https://www.publicprocurement.be/assets/vue-runtime-cUEWE1Gv.js",
    "https://www.publicprocurement.be/assets/uppy-CXjNk1D9.js",
    "https://www.publicprocurement.be/assets/700-CuWTD8Ia.js",
]

all_text = ""
for url in assets:
    r = s.get(url, timeout=60)
    print(f"ASSET {r.status_code} {len(r.content):8} {url}")
    print("  preview:", r.text[:300].replace("\n", " "))
    text = r.text
    all_text += "\n" + text
    # save env.config fully
    if "env.config" in url:
        print("ENV FULL:\n", text)

# Extract API-ish strings
patterns = {
    "abs_https": r"https://[a-zA-Z0-9._:-]+/[a-zA-Z0-9._/?=&%-]*",
    "api_paths": r"/api/[a-zA-Z0-9_./?=&%-]+",
    "sea_paths": r"[\"'`]/api/sea[^\"'`]*)[\"'`]",
    "dos_paths": r"[\"'`]/api/dos[^\"'`]*)[\"'`]",
    "base_urls": r"[\"'`](https?://[^\"'`]*(?:api|bosa|procurement|enot)[^\"'`]*)[\"'`]",
    "v1_paths": r"[\"'`](/[a-zA-Z0-9_./-]*v1/[a-zA-Z0-9_./-]*)[\"'`]",
}
extracted = {}
for name, pat in patterns.items():
    hits = sorted(set(re.findall(pat, all_text)))
    extracted[name] = hits
    print(f"\n=== {name} ({len(hits)}) ===")
    for h in hits[:60]:
        print(" ", h)

# Also look for oauth / keycloak / clientId
oauth = sorted(
    set(
        re.findall(
            r"[\"'`][^\"'`]*(?:oauth|keycloak|clientId|client_id|token_endpoint|authServer)[^\"'`]{0,80}[\"'`]",
            all_text,
            flags=re.I,
        )
    )
)
print("\n=== oauth-ish ===")
for h in oauth[:40]:
    print(" ", h[:200])

# Probe env-derived + extracted API paths
probe_urls = []
for h in extracted.get("api_paths") or []:
    if not h.startswith("http"):
        probe_urls.append("https://www.publicprocurement.be" + h.split("?")[0])
for h in extracted.get("base_urls") or []:
    if "publicprocurement" in h or "bosa" in h or "api" in h:
        probe_urls.append(h.split("?")[0])

# dedupe
seen = set()
uniq = []
for u in probe_urls:
    if u not in seen and len(u) < 200:
        seen.add(u)
        uniq.append(u)

print(f"\nProbing {len(uniq)} URLs...")
results = []
for url in uniq[:80]:
    for method, kwargs in [
        ("GET", {}),
        ("POST", {"json": {"page": 0, "size": 5, "pageSize": 5}}),
    ]:
        try:
            if method == "GET":
                rr = s.get(url, timeout=25)
            else:
                rr = s.post(url, timeout=25, **kwargs)
            body = rr.content
            if len(body) == 1196 and "json" not in (rr.headers.get("Content-Type") or ""):
                continue  # SPA shell
            ct = rr.headers.get("Content-Type", "")
            row = {
                "method": method,
                "url": url,
                "status": rr.status_code,
                "bytes": len(body),
                "ct": ct,
                "preview": body[:250].decode("utf-8", errors="replace"),
            }
            try:
                j = rr.json()
                row["json"] = j
            except Exception:
                pass
            results.append(row)
            print(f"{method} {rr.status_code} {len(body):6} {ct[:35]:35} {url}")
            if "json" in row:
                print("  ", json.dumps(row["json"], ensure_ascii=False)[:250])
        except Exception as e:
            print(method, url, "ERR", type(e).__name__, e)

Path(__file__).with_name("_phase1_be_js_mine.json").write_text(
    json.dumps({"extracted": extracted, "oauth": oauth[:50], "probes": results}, ensure_ascii=False, indent=2, default=str),
    encoding="utf-8",
)
print("done", len(results), "interesting probes")
