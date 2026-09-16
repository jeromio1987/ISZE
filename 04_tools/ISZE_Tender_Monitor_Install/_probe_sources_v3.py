"""Throwaway live probe for Phase 0 audit — GET every source URL. Do not wire into the run."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import requests

SOURCES = [
    ("UK Find a Tender", "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages", "GET", {"limit": 1}),
    ("TED search", "https://api.ted.europa.eu/v3/notices/search", "POST", None),
    ("TED detail sample", "https://api.ted.europa.eu/v3/notices/123456-2026", "GET", None),
    ("Israel RSS", "https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml", "GET", None),
    ("Doffin Public search", "https://dof-notices-prod-api.azure-api.net/public/v2/search", "GET", {"numHitsPerPage": 1, "page": 1}),
    ("HILMA AVP Notices", "https://hns-hilma-prod-apim.azure-api.net/avp/Notices", "GET", None),
    ("Contracts Finder OCDS", "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search", "GET", {"limit": 1}),
    ("DTVP RSS", "https://www.dtvp.de/Center/company/public/procurement/rss", "GET", None),
    ("Vergabe.NRW", "https://www.vergabe.nrw.de/VMPSatellite/satellite.vm", "GET", {"METHOD": "searchPublicProcurement"}),
    ("TenderNed RSS", "https://www.tenderned.nl/papi/tenderned-rs-tns/rss/laatste-publicatie.rss", "GET", None),
    ("Belgium RSS supplier", "https://www.publicprocurement.be/supplier/feed/rss", "GET", None),
    ("Belgium RSS en", "https://www.publicprocurement.be/en/rss", "GET", None),
]

TED_PAYLOAD = {
    "query": "PD>=20260801",
    "fields": ["ND", "TI"],
    "limit": 1,
    "paginationMode": "ITERATION",
}


def sniff(body: bytes) -> dict:
    head = body[:6000].lower()
    text200 = body[:200]
    try:
        preview = text200.decode("utf-8", errors="replace").replace("\n", " ").replace("\r", " ")
    except Exception:
        preview = repr(text200)
    return {
        "has_item": b"<item" in head,
        "has_entry": b"<entry" in head,
        "has_html": b"<html" in head or b"<!doctype html" in head,
        "has_json_obj": body[:1] in (b"{", b"[") or b'"releases"' in head or b'"notices"' in head,
        "preview_200": preview,
    }


def main() -> None:
    out = []
    session = requests.Session()
    session.headers.update({"User-Agent": "ISZE-TenderAudit/0.1 (phase0 probe)"})
    for name, url, method, params in SOURCES:
        row = {
            "name": name,
            "url": url,
            "method": method,
            "status": None,
            "content_type": None,
            "bytes": None,
            "error": None,
        }
        try:
            if method == "POST":
                r = session.post(url, json=TED_PAYLOAD, timeout=30)
            else:
                headers = {"Accept": "application/rss+xml, application/atom+xml, application/json, */*"}
                r = session.get(url, params=params, timeout=30, headers=headers)
            row["status"] = r.status_code
            row["content_type"] = r.headers.get("Content-Type", "")
            body = r.content or b""
            row["bytes"] = len(body)
            row.update(sniff(body))
        except Exception as exc:
            row["error"] = str(exc)
        out.append(row)
        status = row["status"] if row["status"] is not None else "ERR"
        print(f"{name}: {status} {row.get('bytes')}B ctype={row.get('content_type')} item={row.get('has_item')} entry={row.get('has_entry')} html={row.get('has_html')}")

    path = __file__.replace("_probe_sources_v3.py", "_probe_sources_v3_results.json")
    payload = {"probed_at": datetime.now(timezone.utc).isoformat(), "results": out}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
    sys.exit(0)
