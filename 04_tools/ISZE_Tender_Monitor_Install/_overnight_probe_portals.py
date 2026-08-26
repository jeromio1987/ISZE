#!/usr/bin/env python3
"""Overnight feasibility probes for DARK national portals — no invented feeds."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, application/xml, text/html, */*",
}


def get(url: str, **kw):
    try:
        r = requests.get(url, headers=UA, timeout=kw.pop("timeout", 25), allow_redirects=True, **kw)
        return {
            "http": r.status_code,
            "len": len(r.content or b""),
            "ct": (r.headers.get("content-type") or "")[:80],
            "snip": (r.text or "")[:220].replace("\n", " "),
            "url": url,
        }
    except Exception as exc:
        return {"error": str(exc), "url": url}


def main() -> None:
    out: dict = {"probed_at": datetime.now(timezone.utc).isoformat(), "results": {}}

    # Austria — CKAN / USP / Kerndaten
    at_urls = [
        "https://www.data.gv.at/api/3/action/package_search?q=kerndaten&rows=10",
        "https://www.data.gv.at/api/3/action/package_search?q=ausschreibung&rows=5",
        "https://www.data.gv.at/katalog/api/3/action/package_search?q=kerndaten&rows=5",
        "https://data.gv.at/api/3/action/package_search?q=kerndaten&rows=5",
        "https://ausschreibungen.usp.gv.at/",
        "https://www.usp.gv.at/suche/ausschreibungen.html",
        "https://www.data.gv.at/suche/?type=dataset&q=kerndaten+vergabe",
    ]
    for u in at_urls:
        key = "AT_" + u.split("//", 1)[-1][:60].replace("/", "_")
        out["results"][key] = get(u)
        print(key, out["results"][key].get("http") or out["results"][key].get("error"))

    # If CKAN works, list dataset titles + resource URLs
    for k, v in list(out["results"].items()):
        if v.get("http") != 200 or "application/json" not in (v.get("ct") or ""):
            continue
        try:
            r = requests.get(v["url"], headers=UA, timeout=25)
            data = r.json()
            results = (data.get("result") or {}).get("results") or []
            packs = []
            for p in results[:8]:
                res = []
                for rr in (p.get("resources") or [])[:4]:
                    res.append(
                        {
                            "format": rr.get("format"),
                            "url": rr.get("url"),
                            "name": rr.get("name"),
                        }
                    )
                packs.append({"title": p.get("title"), "name": p.get("name"), "resources": res})
            out["results"][k]["packages"] = packs
            print("  packages", len(packs), [p["title"] for p in packs][:3])
        except Exception as exc:
            out["results"][k]["parse_err"] = str(exc)

    # Denmark udbud.dk
    dk = get("https://udbud.dk")
    out["results"]["DK_udbud_home"] = dk
    if dk.get("http") == 200:
        text = requests.get("https://udbud.dk", headers=UA, timeout=25).text
        apis = re.findall(r"https?://[^\s\"']+(?:api|graphql)[^\s\"']*", text, flags=re.I)
        paths = re.findall(r"[\"'](/[^\"']*api[^\"']*)[\"']", text, flags=re.I)
        out["results"]["DK_udbud_home"]["api_links"] = list(dict.fromkeys(apis))[:20]
        out["results"]["DK_udbud_home"]["api_paths"] = list(dict.fromkeys(paths))[:20]
        print("DK api_links", out["results"]["DK_udbud_home"]["api_links"][:5])
        print("DK api_paths", out["results"]["DK_udbud_home"]["api_paths"][:5])
        for path in list(dict.fromkeys(paths))[:8]:
            if path.startswith("http"):
                u = path
            else:
                u = "https://udbud.dk" + path
            out["results"]["DK_path_" + path[:40]] = get(u)

    for u in [
        "https://api.udbud.dk/v1/notices",
        "https://udbud.dk/api/notice/search",
        "https://udbud.dk/api/search",
        "https://www.udbud.dk/api/search",
    ]:
        out["results"]["DK_" + u.split("//")[-1][:50]] = get(u)

    # Ireland eTenders
    ie_urls = [
        "https://www.etenders.gov.ie",
        "https://www.etenders.gov.ie/epps/home.do",
        "https://www.etenders.gov.ie/epps/cft/prepareSearchCFTSDO.do",
        "https://www.etenders.gov.ie/epps/cft/listContractNotices.do",
    ]
    for u in ie_urls:
        out["results"]["IE_" + u.split("//")[-1][:50]] = get(u)
        print("IE", out["results"]["IE_" + u.split("//")[-1][:50]].get("http"))

    # Hungary EKR — look for public search endpoint
    hu = get("https://ekr.gov.hu")
    out["results"]["HU_ekr_home"] = hu
    if hu.get("http") == 200:
        text = requests.get("https://ekr.gov.hu", headers=UA, timeout=25).text
        links = re.findall(r"https?://[^\s\"']+(?:api|rss|atom|ocds)[^\s\"']*", text, flags=re.I)
        out["results"]["HU_ekr_home"]["api_links"] = list(dict.fromkeys(links))[:15]
        print("HU links", out["results"]["HU_ekr_home"]["api_links"][:5])

    # Portugal legacy REST (may reset)
    for u in [
        "https://www.base.gov.pt/base2/rest/anuncios",
        "https://www.base.gov.pt/Base4/pt/pesquisa/",
        "https://www.base.gov.pt/Base4/pt/resultados/",
    ]:
        out["results"]["PT_" + u.split("//")[-1][:50]] = get(u, timeout=20)

    # Spain PLACSP recheck
    es_u = (
        "https://contrataciondelestado.es/sindicacion/sindicacion_643/"
        "licitacionesPerfilesContratanteCompleto3.atom"
    )
    es = get(es_u)
    body = ""
    try:
        body = requests.get(es_u, headers=UA, timeout=25).text
    except Exception:
        pass
    es["waf"] = "firewall" in body.lower() or "denied" in body.lower()
    out["results"]["ES_PLACSP_atom_retry"] = es

    path = HERE / "_overnight_portal_probes.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", path)


if __name__ == "__main__":
    main()
