#!/usr/bin/env python3
"""Dig into AT USP / data.gv.at for a free machine-readable notice path."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,*/*",
}


def main() -> None:
    s = requests.Session()
    s.headers.update(UA)
    out = {}

    # USP ausschreibungen landing
    for u in [
        "https://ausschreibungen.usp.gv.at/",
        "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public",
        "https://ausschreibungen.usp.gv.at/at.gv.bmf.eproc-p/public",
    ]:
        r = s.get(u, timeout=30)
        out[u] = {"http": r.status_code, "len": len(r.content), "snip": r.text[:300].replace("\n", " ")}
        # extract script src / api hints
        srcs = re.findall(r'src=["\']([^"\']+)["\']', r.text)[:20]
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', r.text)[:30]
        apis = [x for x in srcs + hrefs if re.search(r"api|json|ocds|kerndata|graphql", x, re.I)]
        out[u]["apiish"] = apis[:20]
        print(u, r.status_code, "apiish", apis[:8])

    # data.gv.at HTML search — pull dataset links
    r = s.get("https://www.data.gv.at/suche/?type=dataset&q=kerndaten+vergabe", timeout=30)
    links = re.findall(r'href=["\']([^"\']*dataset[^"\']*)["\']', r.text, flags=re.I)
    links = list(dict.fromkeys(links))[:40]
    out["datagv_search_links"] = links
    print("datagv links", len(links), links[:10])

    # try CKAN alternate hosts used by AT
    for u in [
        "https://www.data.gv.at/katalog/api/3/action/status_show",
        "https://ckan.data.gv.at/api/3/action/package_search?q=kerndaten&rows=5",
        "https://www.data.gv.at/api/action/package_search?q=kerndaten&rows=5",
        "https://opendata.wien.gv.at/api/3/action/package_search?q=vergabe&rows=3",
    ]:
        try:
            r = s.get(u, timeout=25)
            print("ckan", r.status_code, u, r.text[:120].replace("\n", " "))
            out[u] = {"http": r.status_code, "snip": r.text[:200]}
            if r.status_code == 200 and "json" in (r.headers.get("content-type") or ""):
                try:
                    j = r.json()
                    res = (j.get("result") or {}).get("results") or []
                    out[u]["titles"] = [p.get("title") for p in res[:5]]
                except Exception:
                    pass
        except Exception as e:
            print("ckan ERR", u, e)
            out[u] = {"error": str(e)}

    # Try USP search query endpoints common to Angular apps
    for u in [
        "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/api/search",
        "https://ausschreibungen.usp.gv.at/api/search",
        "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/rest/ausschreibungen",
    ]:
        try:
            r = s.get(u, timeout=20)
            print("usp api", r.status_code, u, r.text[:100].replace("\n", " "))
            out[u] = {"http": r.status_code, "snip": r.text[:150]}
        except Exception as e:
            out[u] = {"error": str(e)}

    Path("_overnight_at_dig.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote _overnight_at_dig.json")


if __name__ == "__main__":
    main()
