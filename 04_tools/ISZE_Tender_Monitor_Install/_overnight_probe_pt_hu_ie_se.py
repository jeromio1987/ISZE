#!/usr/bin/env python3
"""Probe PT / HU / IE / SE national portals — evidence only, no invented notices."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36"
out: dict = {}


def probe(name: str, method: str, url: str, **kw):
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json, text/html, */*"})
    try:
        r = s.request(method, url, timeout=25, **kw)
        snip = (r.text or "")[:400].replace("\n", " ")
        rec = {
            "http": r.status_code,
            "ctype": r.headers.get("Content-Type", ""),
            "len": len(r.content or b""),
            "snip": snip,
            "is_html": "<html" in snip.lower() or "just a moment" in snip.lower() or "cloudflare" in snip.lower(),
        }
        print(f"[{name}] {r.status_code} len={rec['len']} html={rec['is_html']} {snip[:120]}")
        out[name] = rec
    except Exception as e:
        print(f"[{name}] EXC {e}")
        out[name] = {"error": str(e)}


# Portugal BASE / dados.gov / base.gov.pt
probe("PT_base_gov", "GET", "https://www.base.gov.pt/Base4/pt/pesquisa/")
probe("PT_base2_api", "GET", "https://www.base.gov.pt/apiBase2/search")
probe("PT_dados_ckan", "GET", "https://dados.gov.pt/api/3/action/package_search?q=contratos+publicos&rows=3")

# Hungary EKR
probe("HU_ekr_home", "GET", "https://ekr.gov.hu/")
probe(
    "HU_ekr_search",
    "GET",
    "https://ekr.gov.hu/portal/kozbeszerzes/eljarasok",
)

# Ireland eTenders
probe("IE_etenders", "GET", "https://www.etenders.gov.ie/")
probe(
    "IE_etenders_search",
    "GET",
    "https://www.etenders.gov.ie/epps/quickSearchAction.do",
)

# Sweden — fragmented; try TendSign public / Opic / upphandlingsmyndigheten
probe("SE_uhmynd", "GET", "https://www.upphandlingsmyndigheten.se/")
probe(
    "SE_opic_api",
    "GET",
    "https://www.opic.com/api/",
)
probe(
    "SE_tendsign_pub",
    "GET",
    "https://tendsign.com/publicprocurement.aspx",
)

path = HERE / "_overnight_pt_hu_ie_se_probe.json"
path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"wrote {path}")
