#!/usr/bin/env python3
"""Bulgaria CAIS EOP national open-data — daily OCDS JSON on storage.eop.bg.

Free public files (no login). Importable or runnable alone. Does not invent notices.
"""
from __future__ import annotations

import re
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BG_STORAGE_TMPL = "https://storage.eop.bg/open-data-{day}/"
BG_NOTICE_TMPL = "https://app.eop.bg/today/{tid}"

# Goods vehicles + R&M (same family as other national fetchers)
BG_CPV_PREFIXES = ("3410", "3411", "3413", "3414", "5011")

# Tight Bulgarian / EN vehicle vocabulary (avoid bare "автомобил" / road works)
BG_KW = (
    "камион",
    "пикап",
    "пикъп",
    "шаси",
    "isuzu",
    "d-max",
    "d max",
    "n-series",
    "n series",
    "товарен автомобил",
    "товарни автомобил",
    "лек товарен",
    "бордов",
    "самосвал",
    "автовоз",
    "ремарке",
    "седелен",
    "pickup",
    "pick-up",
    "chassis",
    "truck",
    "lcv",
    "van ",
    "автопарк",
    "служебните автомобили",
    "техническо обслужване на служебн",
    "извънгаранционен ремонт",
)

# Noise that should not pass on keyword alone without CPV
BG_NOISE = re.compile(
    r"(?i)строител|реконструкц|благоустрой|пътн\w*\s+настилка|асфалт|"
    r"водопровод|канализац|озеленяв|сградо|софтуер|информационн\w*\s+систем",
)


def _cpvs_from_tender(tender: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    clas = tender.get("classification") or {}
    if isinstance(clas, dict) and clas.get("id"):
        out.append(str(clas["id"]))
    for it in tender.get("items") or []:
        if not isinstance(it, dict):
            continue
        c = it.get("classification") or {}
        if isinstance(c, dict) and c.get("id"):
            out.append(str(c["id"]))
        for ac in it.get("additionalClassifications") or []:
            if isinstance(ac, dict) and ac.get("id"):
                out.append(str(ac["id"]))
    return out


def _cpv_ok(cpvs: List[str]) -> bool:
    return any(any(c.startswith(p) for p in BG_CPV_PREFIXES) for c in cpvs)


def _kw_ok(blob: str) -> bool:
    b = (blob or "").lower()
    if not any(k in b for k in BG_KW):
        return False
    if BG_NOISE.search(b) and not any(
        k in b for k in ("камион", "пикап", "шаси", "isuzu", "pickup", "truck", "автопарк", "служебните автомобили")
    ):
        return False
    return True


def _buyer_name(rel: Dict[str, Any]) -> str:
    parties = rel.get("parties") or []
    buyer = rel.get("buyer") or {}
    bid = buyer.get("id") if isinstance(buyer, dict) else None
    for p in parties:
        if not isinstance(p, dict):
            continue
        roles = p.get("roles") or []
        if "buyer" in roles or (bid and p.get("id") == bid):
            return str(p.get("name") or "").strip()
    for p in parties:
        if isinstance(p, dict) and p.get("name"):
            return str(p.get("name")).strip()
    return ""


def _parse_dt(raw: Any) -> Optional[datetime]:
    if not raw:
        return None
    s = str(raw).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(s.replace("Z", "+00:00") if fmt.endswith("%z") and s.endswith("Z") else s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    # truncate fractional / timezone mess
    m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", s)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _list_bucket_keys(session: requests.Session, day: str, headers: Dict[str, str]) -> Tuple[int, List[str]]:
    url = BG_STORAGE_TMPL.format(day=day)
    resp = session.get(url, headers=headers, timeout=45)
    if resp.status_code != 200:
        return resp.status_code, []
    keys = re.findall(r"<Key>([^<]+)</Key>", resp.text)
    return 200, keys


def _pick_ocds_key(keys: List[str]) -> Optional[str]:
    for k in keys:
        if "OCDS" in k.upper():
            return k
    for k in keys:
        if "обявления" in k.lower():
            return k
    return None


def _value_currency(tender: Dict[str, Any]) -> Tuple[Any, str]:
    val = tender.get("value") or {}
    if isinstance(val, dict):
        return val.get("amount", ""), str(val.get("currency") or "BGN")
    return "", "BGN"


def fetch_bulgaria_eop(
    session: Optional[requests.Session] = None,
    from_dt: Optional[datetime] = None,
    *,
    max_days: int = 32,
) -> List[Dict[str, Any]]:
    """National BG notices via CAIS EOP daily OCDS open-data bundles."""
    print("\n[BG EOP] Fetching CAIS EOP OCDS open-data (vehicle CPV/keyword)...")
    own = session is None
    session = session or requests.Session()
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    cutoff = from_dt or (datetime.now(timezone.utc) - timedelta(days=30))
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }
    days_ok = 0
    days_miss = 0
    scanned = 0
    try:
        for d in range(0, max_days):
            day = (datetime.now(timezone.utc) - timedelta(days=d)).strftime("%Y-%m-%d")
            # stop if bucket day is before cutoff date (calendar)
            day_dt = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if day_dt + timedelta(days=1) < cutoff:
                break
            status, keys = _list_bucket_keys(session, day, headers)
            if status != 200 or not keys:
                days_miss += 1
                if status == 403:
                    # today's bundle often appears next morning
                    continue
                continue
            ocds_key = _pick_ocds_key(keys)
            if not ocds_key:
                days_miss += 1
                continue
            file_url = BG_STORAGE_TMPL.format(day=day) + urllib.parse.quote(ocds_key)
            resp = session.get(file_url, headers=headers, timeout=180)
            if resp.status_code != 200:
                print(f"  [BG] {day}: file HTTP {resp.status_code}")
                days_miss += 1
                continue
            try:
                pkg = resp.json()
            except Exception as exc:
                print(f"  [BG] {day}: JSON fail {exc}")
                days_miss += 1
                continue
            releases = pkg.get("releases") if isinstance(pkg, dict) else None
            if not isinstance(releases, list):
                days_miss += 1
                continue
            days_ok += 1
            day_hits = 0
            for rel in releases:
                if not isinstance(rel, dict):
                    continue
                scanned += 1
                tender = rel.get("tender") or {}
                if not isinstance(tender, dict):
                    continue
                title = str(tender.get("title") or "").strip()
                desc = str(tender.get("description") or "").strip()
                blob = f"{title} {desc}"
                cpvs = _cpvs_from_tender(tender)
                if not (_cpv_ok(cpvs) or _kw_ok(blob)):
                    continue
                pub = _parse_dt(rel.get("date") or tender.get("datePublished") or pkg.get("publishedDate"))
                if pub and pub < cutoff:
                    continue
                tid = str(tender.get("id") or "").strip()
                ocid = str(rel.get("ocid") or "").strip()
                nid = tid or ocid
                if not nid or nid in seen:
                    continue
                seen.add(nid)
                # deadline
                tender_period = tender.get("tenderPeriod") or {}
                deadline = ""
                if isinstance(tender_period, dict):
                    end = tender_period.get("endDate")
                    if end:
                        deadline = str(end)[:10]
                amount, currency = _value_currency(tender)
                buyer = _buyer_name(rel)
                cpv = cpvs[0] if cpvs else ""
                results.append(
                    {
                        "Source": "🇧🇬 BG-EOP",
                        "Source Notice ID": nid,
                        "Lifecycle": "Opportunity",
                        "Notice Type": ",".join(str(t) for t in (rel.get("tag") or [])[:4]),
                        "Procedure Type": str(tender.get("procurementMethod") or tender.get("procurementMethodDetails") or ""),
                        "Buyer Type": "",
                        "Score": "",
                        "FleetSize": "",
                        "Title": title,
                        "Buyer": buyer,
                        "CPV Code": cpv,
                        "CPV Desc": "",
                        "Description": (desc or title)[:2000],
                        "Est. Value": amount,
                        "Currency": currency,
                        "Published": pub.strftime("%Y-%m-%d") if pub else day,
                        "Deadline": deadline,
                        "Country": "Bulgaria",
                        "Country Code": "BGR",
                        "URL": BG_NOTICE_TMPL.format(tid=tid) if tid else f"https://app.eop.bg/today",
                    }
                )
                day_hits += 1
            print(f"  [BG] {day}: releases={len(releases)} hits+={day_hits}")
        print(f"[BG EOP] Matches: {len(results)} (days_ok={days_ok} miss={days_miss} scanned≈{scanned})")
    finally:
        if own:
            session.close()
    return results


if __name__ == "__main__":
    rows = fetch_bulgaria_eop()
    print("sample:", (rows[0]["Title"][:80] if rows else None))
