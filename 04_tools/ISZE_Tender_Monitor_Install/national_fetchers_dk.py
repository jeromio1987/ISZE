#!/usr/bin/env python3
"""Denmark udbud.dk national search — standalone fetcher (MitUdbud soegning API).

Importable by tender_scraper_v3 or runnable alone. Does not invent notices.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DK_SOEG_URL = "https://udbud.dk/soegning/public/soegeresultat"
DK_NOTICE_TMPL = "https://udbud.dk/udbud/{nid}"

KEYWORDS_DK = [
    "køretøj", "koretoj", "lastebil", "varebil", "pickup", "pick-up",
    "chassis", "tippelad", "lastbil", "isuzu", "d-max", "d max",
    "vedligehold", "reparation", "flåde", "flotte", "truck", "n-series",
    "akslet", "godsvogn", "lastvogn", "pritsche",
]

# CPV chips for goods vehicles / R&M (string codes as returned by portal)
DK_CPV_PREFIXES = ("3410", "3413", "3414", "5011", "3400")


def _match(blob: str) -> bool:
    b = (blob or "").lower()
    return any(k in b for k in KEYWORDS_DK)


def _cpv_ok(cpv: str) -> bool:
    c = (cpv or "").strip()
    if not c:
        return False
    return any(c.startswith(p) for p in DK_CPV_PREFIXES)


def fetch_denmark_udbud(
    session: Optional[requests.Session] = None,
    from_dt: Optional[datetime] = None,
    *,
    page_size: int = 50,
    max_pages: int = 8,
) -> List[Dict[str, Any]]:
    """National DK notices via udbud.dk MitUdbud public soegeresultat POST."""
    print("\n[DK udbud] Fetching MitUdbud soegeresultat (vehicle keyword/CPV)...")
    own = session is None
    session = session or requests.Session()
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    cutoff = (from_dt or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    # Lookback: portal returns DD-MM-YYYY; we filter client-side after fetch.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://udbud.dk",
        "Referer": "https://udbud.dk/soeg",
    }
    terms = [
        "lastbil",
        "lastebil",
        "tippelad",
        "varebil",
        "pickup",
        "chassis",
        "akslet",
        "køretøj lastbil",
        "vedligehold lastbil",
    ]
    try:
        for term in terms:
            for page in range(1, max_pages + 1):
                body = {
                    "fritekstQuery": term,
                    "pagineringDto": {
                        "aktuelSide": page,
                        "maksElementer": page_size,
                        "sorteringFelt": "PUBLIKATION_DATO",
                        "retning": "Desc",
                    },
                    "filterDto": {
                        "formularType": [],
                        "opgaveType": [],
                        "procedureType": [],
                        "smvVenligType": [],
                    },
                    "udbudStatusFilter": "AKTIV",
                }
                resp = session.post(DK_SOEG_URL, json=body, headers=headers, timeout=45)
                if resp.status_code != 200:
                    print(f"  [DK] [{term}] page {page}: HTTP {resp.status_code}")
                    break
                data = resp.json() or {}
                items = data.get("resultatElementDtoList") or []
                total = data.get("totaltAntalResultater")
                if page == 1:
                    print(f"  [DK] [{term}] total≈{total}")
                if not items:
                    break
                page_hits = 0
                stop_old = False
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    da = it.get("dataDa") or {}
                    if not isinstance(da, dict):
                        da = {}
                    title = str(da.get("titel") or "").strip()
                    buyer = str(da.get("ordregiver") or "").strip()
                    cpv = str(da.get("cpvKode") or "").strip()
                    cpv_t = str(da.get("cpvTitel") or "").strip()
                    desc = str(da.get("beskrivelse") or title).strip()
                    pub_raw = str(da.get("publiceringsdato") or "").strip()
                    # DD-MM-YYYY → YYYY-MM-DD
                    pub = ""
                    if len(pub_raw) == 10 and pub_raw[2] == "-":
                        d, m, y = pub_raw.split("-")
                        pub = f"{y}-{m}-{d}"
                    else:
                        pub = pub_raw[:10]
                    if pub and pub < cutoff:
                        stop_old = True
                        continue
                    nid = str(
                        it.get("noticeId")
                        or it.get("noticePublicationNumber")
                        or da.get("udbudsId")
                        or ""
                    ).strip()
                    if not nid:
                        nid = f"{pub}|{title[:60]}"
                    if nid in seen:
                        continue
                    blob = f"{title} {buyer} {cpv} {cpv_t} {desc}".lower()
                    if not _cpv_ok(cpv) and not _match(blob):
                        continue
                    seen.add(nid)
                    page_hits += 1
                    deadline = ""
                    frists = da.get("tidsfrister") or []
                    if isinstance(frists, list) and frists:
                        deadline = str(frists[0])[:10]
                    else:
                        deadline_raw = str(da.get("tilbudsfrist") or da.get("deadline") or "")
                        if len(deadline_raw) == 10 and deadline_raw[2] == "-":
                            d, m, y = deadline_raw.split("-")
                            deadline = f"{y}-{m}-{d}"
                        else:
                            deadline = deadline_raw[:10]
                    results.append(
                        {
                            "Source": "🇩🇰 DK-udbud",
                            "Source Notice ID": nid,
                            "Title": title,
                            "Buyer": buyer,
                            "Published": pub,
                            "Deadline": deadline,
                            "Country": "Denmark",
                            "Country Code": "DNK",
                            "CPV Code": cpv,
                            "CPV Desc": cpv_t,
                            "Description": desc[:2000] if desc else title,
                            "URL": DK_NOTICE_TMPL.format(nid=nid)
                            if nid and "|" not in nid
                            else "https://udbud.dk/soeg",
                            "Value": da.get("anslaaetVaerdi") or "",
                            "Currency": da.get("anslaaetVaerdiValuta") or "",
                        }
                    )
                print(f"  [DK] [{term}] page {page}: scanned={len(items)} hits+={page_hits}")
                if stop_old or len(items) < page_size:
                    break
                time.sleep(0.35)
            time.sleep(0.2)
        print(f"[DK udbud] Unique matches: {len(results)}")
    finally:
        if own:
            session.close()
    return results


if __name__ == "__main__":
    from datetime import timedelta

    rows = fetch_denmark_udbud(from_dt=datetime.now(timezone.utc) - timedelta(days=30))
    for r in rows[:8]:
        print("-", r.get("Published"), (r.get("Title") or "")[:80])
    print("total", len(rows))
