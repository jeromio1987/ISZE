#!/usr/bin/env python3
"""Probe AT USP tenderlist + HU EKR + IE eTenders for free machine paths."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
}
s = requests.Session()
s.headers.update(UA)
out = {"probed_at": datetime.now(timezone.utc).isoformat(), "results": {}}


def probe(name: str, url: str, method: str = "GET", **kw):
    try:
        if method == "POST":
            r = s.post(url, timeout=25, **kw)
        else:
            r = s.get(url, timeout=25, **kw)
        ct = (r.headers.get("content-type") or "")[:80]
        snip = (r.text or "")[:220].replace("\n", " ")
        rec = {
            "http": r.status_code,
            "ct": ct,
            "len": len(r.content or b""),
            "final": str(r.url),
            "snip": snip,
            "jsonish": "json" in ct.lower() or snip.strip()[:1] in "{[",
        }
        if rec["jsonish"]:
            try:
                j = r.json()
                rec["json_type"] = type(j).__name__
                if isinstance(j, dict):
                    rec["keys"] = list(j.keys())[:20]
                elif isinstance(j, list):
                    rec["n"] = len(j)
            except Exception as e:
                rec["json_err"] = str(e)
        out["results"][name] = rec
        print(name, rec["http"], rec["ct"], rec["len"], "jsonish=", rec["jsonish"])
        return r
    except Exception as e:
        out["results"][name] = {"error": str(e), "url": url}
        print(name, "ERR", e)
        return None


# AT USP tenderlist (redirect target from overnight probe)
r = probe(
    "AT_tenderlist",
    "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist",
)
if r is not None and r.status_code == 200:
    text = r.text
    scripts = re.findall(r'src=["\']([^"\']+)["\']', text)
    apis = [
        x
        for x in scripts
        + re.findall(r'["\'](/[^"\']*(?:api|rest|search|tender)[^"\']*)["\']', text, flags=re.I)
        if re.search(r"api|rest|search|tender|json", x, re.I)
    ]
    out["results"]["AT_tenderlist"]["scripts"] = scripts[:25]
    out["results"]["AT_tenderlist"]["apiish"] = list(dict.fromkeys(apis))[:30]
    print(" AT scripts", scripts[:8])
    print(" AT apiish", out["results"]["AT_tenderlist"]["apiish"][:12])
    # follow relative API guesses under same host
    for path in [
        "/at.gv.bmdw.eproc-p/public/api/tenders",
        "/at.gv.bmdw.eproc-p/public/rest/tenders",
        "/at.gv.bmdw.eproc-p/public/tenderlist/data",
        "/at.gv.bmdw.eproc-p/public/search",
    ]:
        probe("AT_" + path.split("/")[-1], "https://ausschreibungen.usp.gv.at" + path)

# Known Kerndaten / auftrag.at
for name, url in [
    ("AT_auftrag", "https://www.auftrag.at/"),
    ("AT_offenevergaben_downloads", "https://offenevergaben.at/downloads"),
    ("AT_datagv_tag", "https://www.data.gv.at/suche/?searchterm=&tagFilter_sub%5B%5D=Ausschreibung"),
]:
    probe(name, url)

# HU EKR
r = probe("HU_ekr", "https://ekr.gov.hu")
if r is not None:
    text = r.text
    apis = re.findall(r'["\']([^"\']*(?:api|ocds|notice|search)[^"\']*)["\']', text, flags=re.I)
    out["results"]["HU_ekr"]["apiish"] = list(dict.fromkeys(apis))[:40]
    print(" HU apiish", out["results"]["HU_ekr"]["apiish"][:15])
    for u in list(dict.fromkeys(apis))[:8]:
        if u.startswith("http") and "google" not in u and "font" not in u:
            probe("HU_follow_" + u.split("/")[-1][:30], u)
        elif u.startswith("/") and "api" in u.lower():
            probe("HU_path_" + u.split("/")[-1][:30], "https://ekr.gov.hu" + u)

# IE eTenders / OCDS guesses
for name, url in [
    ("IE_home", "https://www.etenders.gov.ie"),
    ("IE_ocds", "https://www.etenders.gov.ie/epps/ocds/releasePackage"),
    ("IE_search", "https://www.etenders.gov.ie/epps/cft/prepareSearchCFTS.do"),
]:
    probe(name, url)

# PT Base4 search POST-ish
probe(
    "PT_base4_search",
    "https://www.base.gov.pt/Base4/pt/resultados/",
    params={"type": "contratos", "query": "veiculo"},
)

path = Path("_overnight_at_hu_ie_probe.json")
path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("wrote", path)
