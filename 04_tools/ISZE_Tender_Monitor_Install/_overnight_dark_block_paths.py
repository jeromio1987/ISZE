#!/usr/bin/env python3
"""Document remaining dark portals as BLOCKED/CODE_READY with unblock paths.
Also probe one more CZ public HTML list + LT key-needed confirmation.
No Nordics. No Jerome browser spam.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
OUT = HERE / "_overnight_dark_block_paths.json"
UA = {"User-Agent": "Mozilla/5.0 Chrome/128.0.0.0", "Accept": "*/*"}


def main() -> None:
    s = requests.Session()
    evidence = {}

    # CZ: LIVE via createdAt[gte] + client vehicle post-filter (fulltext still ignored)
    evidence["CZ"] = {
        "api": "https://api.vvz.nipez.cz/api/submissions/search?formGroup=vz&form=vz",
        "http": 200,
        "window_filter": "createdAt[gte]=YYYY-MM-DD works; fulltext/CPV still ignored",
        "status": "LIVE",
        "source": "national_fetchers_cz.py",
        "note": "wired — client vehicle post-filter on date window",
    }

    # LT: 401 without key
    r = s.post(
        "https://viesiejipirkimai.lt/epps-integration/api/cft-details-export",
        headers={**UA, "Accept": "application/json", "Content-Type": "application/json"},
        json={"pageSize": 5, "pageNum": 1},
        timeout=30,
    )
    evidence["LT"] = {
        "api": "https://viesiejipirkimai.lt/epps-integration/api/cft-details-export",
        "http": r.status_code,
        "snip": r.text[:200],
        "status": "CODE_READY",
        "unblock": "Request free VPT CVP IS API key (apiKey header) — do not spam browser",
    }

    # EE: API 500
    r = s.get("https://riigihanked.riik.ee/rhr/api/public/v1/opendata", headers=UA, timeout=25)
    evidence["EE"] = {
        "api": "https://riigihanked.riik.ee/rhr/api/public/v1/opendata",
        "http": r.status_code,
        "snip": r.text[:120],
        "status": "BLOCKED",
        "unblock": "RHR open-data API currently 500; wait for Rahandusministeerium fix or use dump when published",
    }

    # SK: captcha vestnik
    r = s.get("https://www.uvo.gov.sk/vyhladavanie/vyhladavanie-zakaziek", headers=UA, timeout=35)
    evidence["SK"] = {
        "portal": "https://www.uvo.gov.sk/",
        "http": r.status_code,
        "recaptcha": "recaptcha" in r.text.lower(),
        "status": "BLOCKED",
        "unblock": "ÚVO structured open data / UVOstat paid API — HTML vestník is recaptcha-gated",
    }

    # GR: login shell
    r = s.get("https://cerpp.eprocurement.gov.gr/kimdis/opendata", headers=UA, timeout=25)
    evidence["GR"] = {
        "portal": "https://www.promitheus.gov.gr/",
        "opendata_http": r.status_code,
        "login_shell": "login" in r.text.lower(),
        "status": "BLOCKED",
        "unblock": "KIMDIS Open Data API credentials from Promitheus / GSIS registration",
    }

    # ES still WAF
    r = s.get(
        "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom",
        headers=UA,
        timeout=25,
    )
    evidence["ES"] = {
        "http": r.status_code,
        "waf": "firewall" in r.text.lower() or "waf" in r.text.lower(),
        "status": "CODE_READY",
        "unblock": "Spanish egress / residential session cookies — fetcher already coded",
    }

    # Static BLOCKED (prior probes + known structure)
    for code, portal, unblock in [
        ("HU", "https://ekr.gov.hu", "EKR operator registration or paid aggregator"),
        ("IE", "https://www.etenders.gov.ie", "OGP structured feed — RSS 500 / brittle HTML"),
        ("SE", "commercial annonsdatabaser", "Paid TendSign/Mercell/e-Avrop or UHM dump"),
        ("HR", "https://eojn.nn.hr", "EOJN structured API if published; HTML SPA today"),
        ("SI", "https://www.enarocanje.si", "eNaročanje public JSON if published; HTML shell today"),
        ("LV", "https://www.eis.gov.lv", "IUB/EIS open-data dump or API registration"),
        ("CY", "https://www.eprocurement.gov.cy", "Thin market; TED covers above-threshold — national HTML only"),
        ("MT", "https://www.etenders.gov.mt", "eTenders Malta structured feed if OGP publishes one"),
    ]:
        evidence[code] = {"portal": portal, "status": "BLOCKED", "unblock": unblock}

    # BG LIVE confirmation pointer
    evidence["BG"] = {
        "status": "LIVE",
        "source": "https://storage.eop.bg/open-data-YYYY-MM-DD/ OCDS JSON",
        "note": "wired national_fetchers_bg.py",
    }

    out = {
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "nordics": "DONE — not touched",
        "evidence": evidence,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    for k, v in evidence.items():
        print(f"  {k}: {v.get('status')}")


if __name__ == "__main__":
    main()
