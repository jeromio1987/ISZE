#!/usr/bin/env python3
"""HTTP-only probe HU / IE / SE — no browser, no Nordics. Honest BLOCKED/DARK evidence."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
OUT = HERE / "_overnight_hu_ie_se_block.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def hit(s: requests.Session, name: str, url: str, **kw) -> dict:
    try:
        r = s.request(kw.pop("method", "GET"), url, timeout=45, allow_redirects=True, **kw)
        text = r.text or ""
        return {
            "name": name,
            "http": r.status_code,
            "bytes": len(r.content or b""),
            "final": str(r.url),
            "jsonish": (r.headers.get("content-type") or "").lower().find("json") >= 0
            or text[:1] in ("{", "["),
            "loginish": bool(re.search(r"login|sign.?in|mitid|sso|authenticate", text[:3000], re.I)),
            "preview": text[:180].replace("\n", " "),
        }
    except Exception as e:
        return {"name": name, "error": str(e)}


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "*/*"})
    probes = []
    # HU EKR — Angular SPA; look for any public JSON
    probes.append(hit(s, "HU_ekr_home", "https://ekr.gov.hu/"))
    probes.append(hit(s, "HU_ekr_api", "https://ekr.gov.hu/api/notice/search?q=jarmu"))
    probes.append(hit(s, "HU_kozbeszerzes_rss", "https://www.kozbeszerzes.hu/ertesito/rss"))
    # IE eTenders
    probes.append(hit(s, "IE_home", "https://www.etenders.gov.ie/epps/home.do"))
    probes.append(
        hit(
            s,
            "IE_search_truck",
            "https://www.etenders.gov.ie/epps/quickSearchAction.do?searchType=cft&keyword=truck",
        )
    )
    probes.append(hit(s, "IE_rss", "https://www.etenders.gov.ie/epps/cft/listContractNoticesRSS.do"))
    # SE — no single national free API; check open data hints only
    probes.append(hit(s, "SE_uhmd", "https://www.upphandlingsmyndigheten.se/"))
    probes.append(
        hit(
            s,
            "SE_dataportal",
            "https://www.dataportal.se/api/datasets?q=upphandling&limit=5",
        )
    )
    probes.append(hit(s, "SE_kommers", "https://www.kommersannons.se/"))

    verdict = {
        "HU": {
            "status": "BLOCKED",
            "why": "EKR is login/SPA shell; no free public list/API confirmed this pass",
            "unblock": "Operator EKR registration + API docs, or licensed aggregator",
        },
        "IE": {
            "status": "BLOCKED",
            "why": "eTenders HTML/search returns pages but no stable machine list/RSS (RSS 500); parse brittle",
            "unblock": "OGP structured feed or HTML parser with session cookies after manual confirm",
        },
        "SE": {
            "status": "BLOCKED",
            "why": "No single state gazette — commercial annonsdatabaser (TendSign/Mercell/e-Avrop) are the channel",
            "unblock": "Paid multi-platform monitoring or UHM open-data dump if published",
        },
    }
    out = {
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "note": "HTTP-only; no browser; Nordics not touched",
        "probes": probes,
        "verdict": verdict,
    }
    # Soft upgrades if something unexpectedly worked
    for p in probes:
        if p.get("name", "").startswith("HU") and p.get("jsonish") and p.get("http") == 200 and p.get("bytes", 0) > 500:
            if p["preview"][:1] in ("{", "["):
                verdict["HU"]["status"] = "CODE_READY"
                verdict["HU"]["why"] = f"JSON-ish hit on {p['name']}"
        if p.get("name") == "IE_rss" and p.get("http") == 200 and "<item" in (p.get("preview") or "").lower():
            verdict["IE"]["status"] = "CODE_READY"
            verdict["IE"]["why"] = "RSS item feed reachable"
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(verdict, indent=2))
    print("Wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
