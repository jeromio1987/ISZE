"""Phase 1 throwaway: DTVP alternatives + Iceland + Kazakhstan free-source probes."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import requests

SOURCES = [
    # Known-dead (confirm)
    ("DTVP RSS (legacy)", "https://www.dtvp.de/Center/company/public/procurement/rss", "GET", None, None),
    ("Vergabe.NRW satellite", "https://www.vergabe.nrw.de/VMPSatellite/satellite.vm", "GET", {"METHOD": "searchPublicProcurement"}, None),
    # Free Germany candidates
    ("oeffentlichevergabe OpenData swagger", "https://oeffentlichevergabe.de/documentation/swagger-ui/opendata/index.html", "GET", None, None),
    ("oeffentlichevergabe export day sample", "https://www.oeffentlichevergabe.de/api/notice-export", "GET", {"pubDay": "2026-08-20"}, None),
    ("oeffentlichevergabe ui home", "https://oeffentlichevergabe.de/ui/de/", "GET", None, None),
    ("service.bund RSS ausschreibungen", "https://www.service.bund.de/Content/DE/Ausschreibungen/Ausschreibungen.xml", "GET", None, None),
    ("service.bund RSS alt", "https://www.service.bund.de/SiteGlobals/Functions/RSSFeed/RSSGenerator_Ausschreibungen.xml", "GET", None, None),
    ("evergabe-online search", "https://www.evergabe-online.de/search.html", "GET", None, None),
    ("DTVP bieter free search page", "https://www.dtvp.de/Center/company/welcome.do", "GET", None, None),
    ("DTVP public search", "https://www.dtvp.de/Center/company/publicTenders.do", "GET", None, None),
    # Iceland
    ("Rikiskaup home", "https://www.rikiskaup.is/", "GET", None, None),
    ("Rikiskaup utbod", "https://www.rikiskaup.is/utbod/", "GET", None, None),
    ("opentender.is", "https://opentender.eu/is", "GET", None, None),
    ("TED ISL any sample", "https://api.ted.europa.eu/v3/notices/search", "POST", None, {
        "query": "CY=ISL AND PD>=20260601",
        "fields": ["ND", "TI"],
        "limit": 1,
        "paginationMode": "ITERATION",
        "scope": "ACTIVE",
    }),
    # Kazakhstan
    ("goszakup developer ows_v3", "https://www.goszakup.gov.kz/ru/developer/ows_v3", "GET", None, None),
    ("goszakup ows graphql no auth", "https://ows.goszakup.gov.kz/v3/graphql", "POST", None, {
        "query": "{ TrdBuy(limit: 1) { id } }"
    }),
    ("goszakup portal home", "https://www.goszakup.gov.kz/", "GET", None, None),
]


def sniff(body: bytes) -> dict:
    head = body[:8000].lower()
    try:
        preview = body[:220].decode("utf-8", errors="replace").replace("\n", " ").replace("\r", " ")
    except Exception:
        preview = repr(body[:220])
    return {
        "has_item": b"<item" in head,
        "has_entry": b"<entry" in head or b":entry" in head,
        "has_html": b"<html" in head or b"<!doctype html" in head,
        "has_json": body[:1] in (b"{", b"[") or b'"notices"' in head or b'"releases"' in head,
        "has_rss": b"<rss" in head or b"<feed" in head,
        "preview_220": preview,
    }


def main() -> None:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "ISZE-TenderPhase1/0.1 (source feasibility)",
        "Accept": "application/rss+xml, application/atom+xml, application/json, text/html, */*",
    })
    out = []
    for name, url, method, params, json_body in SOURCES:
        row = {"name": name, "url": url, "method": method, "status": None, "content_type": None, "bytes": None, "error": None}
        try:
            if method == "POST":
                r = session.post(url, params=params, json=json_body, timeout=40)
            else:
                r = session.get(url, params=params, timeout=40, allow_redirects=True)
            row["status"] = r.status_code
            row["content_type"] = r.headers.get("Content-Type", "")
            row["final_url"] = str(r.url)
            body = r.content or b""
            row["bytes"] = len(body)
            row.update(sniff(body))
        except Exception as exc:
            row["error"] = str(exc)
        out.append(row)
        print(f"{name}: {row.get('status')} {row.get('bytes')}B ctype={row.get('content_type')} rss={row.get('has_rss')} item={row.get('has_item')} json={row.get('has_json')} html={row.get('has_html')} err={row.get('error')}")

    # Extra: try a few oeffentlichevergabe Open Data path guesses if first export failed
    guesses = [
        "https://www.oeffentlichevergabe.de/api/notice-exports",
        "https://oeffentlichevergabe.de/api/opendata/export",
        "https://www.oeffentlichevergabe.de/opendata/export",
        "https://www.oeffentlichevergabe.de/api/notices",
    ]
    for url in guesses:
        row = {"name": f"guess {url.split('/')[-1]}", "url": url, "method": "GET"}
        try:
            r = session.get(url, params={"pubDay": "2026-08-20"}, timeout=30)
            row.update({"status": r.status_code, "content_type": r.headers.get("Content-Type", ""), "bytes": len(r.content or b""), "final_url": str(r.url)})
            row.update(sniff(r.content or b""))
        except Exception as exc:
            row["error"] = str(exc)
        out.append(row)
        print(f"GUESS {url}: {row.get('status')} {row.get('bytes')}B")

    path = __file__.replace("_phase1_probe_de_is_kz.py", "_phase1_probe_de_is_kz_results.json")
    payload = {"probed_at": datetime.now(timezone.utc).isoformat(), "results": out}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
    sys.exit(0)
