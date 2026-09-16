#!/usr/bin/env python3
"""Deeper PT BASE / IE eTenders / HU EKR API hunt — evidence JSON only."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36"
s = requests.Session()
s.headers.update({"User-Agent": UA, "Accept": "*/*"})
out = {}


def hit(name, method, url, **kw):
    try:
        r = s.request(method, url, timeout=25, **kw)
        snip = (r.text or "")[:350].replace("\n", " ")
        rec = {
            "http": r.status_code,
            "len": len(r.content or b""),
            "ctype": (r.headers.get("Content-Type") or "")[:80],
            "snip": snip,
        }
        print(f"[{name}] {r.status_code} {rec['len']} {snip[:100]}")
        out[name] = rec
        return r
    except Exception as e:
        print(f"[{name}] EXC {e}")
        out[name] = {"error": str(e)}
        return None


# PT — dados.gov package list + base.gov Base4 ajax patterns
hit("PT_dados_package_list", "GET", "https://dados.gov.pt/api/3/action/package_list?limit=5")
hit(
    "PT_dados_search_contratos",
    "GET",
    "https://dados.gov.pt/api/3/action/package_search?q=base.gov&rows=5",
)
hit("PT_base4_resultados", "GET", "https://www.base.gov.pt/Base4/pt/resultados/")
hit(
    "PT_base4_ajax",
    "POST",
    "https://www.base.gov.pt/Base4/pt/resultados/",
    data={"type": "search_contratos", "query": "veiculo", "page": "0"},
    headers={"X-Requested-With": "XMLHttpRequest", "Referer": "https://www.base.gov.pt/Base4/pt/pesquisa/"},
)
# common Base4 endpoints seen in prior docs
for path in (
    "/Base4/pt/api/SearchContracts",
    "/Base4/pt/api/contratos",
    "/apiBase2/RestService.svc/getAnuncios",
    "/apiBase2/RestService.svc/getContratos",
):
    hit(f"PT_path_{path[-30:]}", "GET", f"https://www.base.gov.pt{path}")

# IE — eTenders / ePPS API sniff from homepage scripts
r = hit("IE_home", "GET", "https://www.etenders.gov.ie/")
if r and r.text:
    apis = sorted(set(re.findall(r"https?://[^\"'\s]+(?:api|epps|search)[^\"'\s]*", r.text, flags=re.I)))[:20]
    out["IE_urls_in_html"] = apis
    print("IE urls", len(apis), apis[:8])
hit(
    "IE_epps_ctm",
    "GET",
    "https://www.etenders.gov.ie/epps/home.do",
)
hit(
    "IE_search_json",
    "GET",
    "https://www.etenders.gov.ie/epps/cft/prepareSearchCFTS.do",
)

# HU — look for REST under ekr.gov.hu
r = hit("HU_home", "GET", "https://ekr.gov.hu/")
if r and r.text:
    apis = sorted(set(re.findall(r"[\"'](/[^\"']*(?:api|rest|search)[^\"']*)[\"']", r.text, flags=re.I)))[:30]
    out["HU_paths"] = apis
    print("HU paths", apis[:12])
    for p in apis[:8]:
        if p.startswith("http"):
            hit(f"HU_{p[-40:]}", "GET", p)
        else:
            hit(f"HU_{p[-40:]}", "GET", f"https://ekr.gov.hu{p}")

path = HERE / "_overnight_pt_ie_hu_deep.json"
path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("wrote", path)
