#!/usr/bin/env python3
"""Czech VVZ national search — api.vvz.nipez.cz submissions/search (public).

Public list ignores fulltext/CPV, but API Platform date filter works:
  createdAt[gte]=YYYY-MM-DD + order[createdAt]=desc
Client-side vehicle keyword gate on title/blob. Does not invent notices.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CZ_SEARCH = "https://api.vvz.nipez.cz/api/submissions/search"
CZ_NOTICE_TMPL = "https://vvz.nipez.cz/vyhledat-formular/{sid}"

# Tight CV / LCV / R&M Czech + EN — NEVER bare "dodávka" (matches every supply notice).
CZ_TIGHT = (
    "nákladní automobil",
    "nakladni automobil",
    "nákladního automobil",
    "nakladniho automobil",
    "nákladní vozidl",
    "nakladni vozidl",
    "nákladního vozidl",
    "nakladniho vozidl",
    "nákladní dopravy",
    "nakladni dopravy",
    "lehkých užitkových",
    "lehke uzitkove",
    "lehkych uzitkovych",
    "užitkového vozidl",
    "uzitkoveho vozidl",
    "užitkové vozidl",
    "uzitkove vozidl",
    "užitkových vozidel",
    "uzitkovych vozidel",
    "motorových vozidel",
    "motorovych vozidel",
    "služební automobil",
    "sluzebni automobil",
    "služebních automobil",
    "sluzebnich automobil",
    "vozový park",
    "vozovy park",
    "servis vozidel",
    "oprava vozidel",
    "opravy vozidel",
    "údržba vozidel",
    "udrzba vozidel",
    "údržba automobil",
    "udrzba automobil",
    "servis automobil",
    "oprava automobil",
    "podvozek",
    "podvozku",
    "pickup",
    "pick-up",
    "pick up",
    "isuzu",
    "d-max",
    "d max",
    "n-series",
    "n series",
    "valník",
    "valnik",
    "sklápěč",
    "sklapec",
    "sklápěcí",
    "kamion",
    "kamión",
    "chassis",
    "truck",
    "lcv",
    "cisternov",
    "nástavba",
    "nastavba",
    "nosič nástaveb",
    "nosic nastaveb",
    "přípojné vozidl",
    "pripojne vozidl",
    "přívěs",
    "prives",
    "návěs",
    "naves",
    "terénní automobil",
    "terenni automobil",
    "4x4",
    "off-road",
)

# Single tokens that are vehicle-ish but need noise guard
CZ_TOKEN = (
    "nákladní",
    "nakladni",
    "užitkov",
    "uzitkov",
)

# Vehicle nouns — alone only if no construction/IT noise
CZ_VEHICLE_NOUN = (
    "automobil",
    "vozidel",
    "vozidla",
    "vozidlo",
    "vozidy",
)

NOISE_RE = re.compile(
    r"(?i)("
    r"stavebn|rekonstrukc|silnic|asfalt|vodovod|kanaliz|softwar|informa[cč]n|"
    r"n[aá]bytek|mobili[aá][rř]|potravin|l[eé][cč]iv|zdravotn|[uú]klid|"
    r"endoskop|analyz[aá]tor|autokl[aá]v|reg[aá]lov|u[cč]eben|ICT|"
    r"kolejov|tramvaj|železni[cč]|zeleznic|MHD|preference vozidel|"
    r"osobn[ií]ho automobilu s plug-in|hybridn[ií]m pohonem"
    r")"
)

CPV_PREFIXES = ("3410", "3411", "3413", "3414", "5011")


def _cpv_ok(cpv: str) -> bool:
    c = (cpv or "").strip()
    return bool(c) and any(c.startswith(p) for p in CPV_PREFIXES)


def _vehicle_hit(blob: str) -> bool:
    b = (blob or "").lower()
    if not b:
        return False
    if any(t in b for t in CZ_TIGHT):
        return True
    if any(t in b for t in CZ_TOKEN) and any(n in b for n in CZ_VEHICLE_NOUN):
        return True
    if any(n in b for n in CZ_VEHICLE_NOUN):
        if NOISE_RE.search(b):
            return False
        # bare automobil / vozidlo without cargo/utility context — drop
        if any(t in b for t in CZ_TOKEN + ("podvozek", "podvozku", "fleet", "leasing")):
            return True
        return False
    return False


def _dig(obj: Any, *keys: str, default: Any = "") -> Any:
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur if cur is not None else default


def _buyer_from_data(data: Dict[str, Any]) -> str:
    z = data.get("zadavatele")
    if isinstance(z, list) and z:
        first = z[0]
        if isinstance(first, dict):
            return str(first.get("nazev") or "").strip()
    return str(
        _dig(data, "nazevZadavatele")
        or _dig(data, "organizationName")
        or _dig(data, "zadavatel", "nazev")
        or ""
    ).strip()


def _cpv_from_data(data: Dict[str, Any]) -> str:
    for key in ("cpv", "hlavniCpv", "mainCpv", "kodCpv", "BT-262-Lot"):
        v = data.get(key)
        if v:
            return str(v).strip()
    codes = data.get("cpvCodes")
    if isinstance(codes, list) and codes:
        return str(codes[0] or "").strip()
    # nested scan (rare)
    blob = json.dumps(data, ensure_ascii=False)
    m = re.search(r"\b(341\d{5}|5011\d{3})\b", blob)
    return m.group(1) if m else ""


def _row_from_item(it: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    data = it.get("data") if isinstance(it.get("data"), dict) else {}
    if not isinstance(data, dict):
        data = {}
    if data.get("zakazkaZrusena") is True:
        return None
    wf = str(it.get("workflowPlaceCode") or "")
    if wf in ("STORNOVANO", "ZNEPLATNENO", "SMAZANO"):
        return None

    title = str(
        data.get("nazevZakazky")
        or data.get("title")
        or it.get("name")
        or ""
    ).strip()
    buyer = _buyer_from_data(data) or str(_dig(it, "organization", "name") or "").strip()
    cpv = _cpv_from_data(data)
    sid = str(it.get("id") or it.get("uuid") or data.get("id") or "").strip()
    pub = str(
        data.get("datumUverejneniVvz")
        or it.get("datePublished")
        or it.get("createdAt")
        or ""
    )[:10]
    deadline = str(
        data.get("lhutaProPodaniNabidek")
        or data.get("deadline")
        or ""
    )[:10]
    blob = f"{title} {buyer} {cpv} {json.dumps(data, ensure_ascii=False)[:2000]}"
    if not (_cpv_ok(cpv) or _vehicle_hit(blob)):
        return None
    url = CZ_NOTICE_TMPL.format(sid=sid) if sid else "https://vvz.nipez.cz/"
    return {
        "Source": "🇨🇿 CZ-VVZ",
        "Source Notice ID": sid,
        "Lifecycle": "Opportunity",
        "Notice Type": str(data.get("druhFormulare") or it.get("form") or "vz"),
        "Procedure Type": "",
        "Buyer Type": "",
        "Score": "",
        "FleetSize": "",
        "Title": title or f"VVZ submission {sid}",
        "Buyer": buyer,
        "CPV Code": cpv,
        "CPV Desc": "",
        "Description": title,
        "Est. Value": data.get("predpokladanaHodnota") or data.get("estimatedValue") or "",
        "Currency": "CZK",
        "Published": pub,
        "Deadline": deadline,
        "Country": "Czechia",
        "Country Code": "CZE",
        "URL": url,
        "variableId": it.get("variableId") or data.get("evCisloZakazkyVvz") or "",
    }


def fetch_czechia_vvz(
    session: Optional[requests.Session] = None,
    from_dt: Optional[datetime] = None,
    *,
    page_size: int = 50,
    max_pages: int = 150,
) -> List[Dict[str, Any]]:
    """National CZ notices via VVZ public search + client vehicle gate."""
    print("\n[CZ VVZ] Fetching api.vvz.nipez.cz (createdAt[gte] + vehicle post-filter)...")
    own = session is None
    session = session or requests.Session()
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    if from_dt is None:
        from_dt = datetime.now(timezone.utc) - timedelta(days=30)
    if from_dt.tzinfo is None:
        from_dt = from_dt.replace(tzinfo=timezone.utc)
    since = from_dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://vvz.nipez.cz",
        "Referer": "https://vvz.nipez.cz/",
    }
    try:
        scanned = 0
        for page in range(1, max_pages + 1):
            params = {
                "formGroup": "vz",
                "form": "vz",
                "page": page,
                "limit": page_size,
                "createdAt[gte]": since,
                "order[createdAt]": "desc",
                "workflowPlace": "UVEREJNENO_VVZ",
            }
            resp = session.get(CZ_SEARCH, params=params, headers=headers, timeout=45)
            if resp.status_code != 200:
                print(f"  [CZ] page {page}: HTTP {resp.status_code} {resp.text[:120]}")
                break
            try:
                items = resp.json()
            except Exception:
                break
            if not isinstance(items, list):
                items = []
            if page == 1:
                total = resp.headers.get("X-Total-Count") or "?"
                print(f"  [CZ] window since={since} total≈{total} page_size={page_size}")
            if not items:
                break
            scanned += len(items)
            page_hits = 0
            oldest_on_page: Optional[datetime] = None
            for it in items:
                if not isinstance(it, dict):
                    continue
                created_s = str(it.get("createdAt") or "")
                try:
                    created = datetime.fromisoformat(created_s.replace("Z", "+00:00"))
                    if oldest_on_page is None or created < oldest_on_page:
                        oldest_on_page = created
                    if created < from_dt:
                        continue
                except ValueError:
                    pass
                row = _row_from_item(it)
                if not row:
                    continue
                nid = row["Source Notice ID"]
                if nid and nid in seen:
                    continue
                if nid:
                    seen.add(nid)
                results.append(row)
                page_hits += 1
            if page % 20 == 0 or page_hits:
                print(f"  [CZ] page {page} scanned={scanned} hits={len(results)}")
            if len(items) < page_size:
                break
            if oldest_on_page is not None and oldest_on_page < from_dt:
                break
            time.sleep(0.12)
        print(f"[CZ VVZ] Matches: {len(results)} (scanned {scanned})")
    finally:
        if own:
            session.close()
    return results


if __name__ == "__main__":
    rows = fetch_czechia_vvz()
    print("n", len(rows))
    for r in rows[:12]:
        print("-", (r.get("Published") or "")[:10], (r.get("Title") or "")[:90])
