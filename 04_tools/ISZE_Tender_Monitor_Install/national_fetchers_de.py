#!/usr/bin/env python3
"""Germany oeffentlichevergabe.de Open Data — BKMS notice-exports csv.zip.

National DE publication hub (below-threshold + TED mirrors). Free Open Data API.
Importable by tender_scraper_v3 or runnable alone.
"""
from __future__ import annotations

import csv
import io
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from isze_core_v3 import classify_lifecycle, lifecycle_from_notice_type
except ImportError:  # pragma: no cover
    def classify_lifecycle(text: str, notice_type: str = "") -> str:  # type: ignore
        return ""

    def lifecycle_from_notice_type(notice_type: str) -> str:  # type: ignore
        return ""

DE_OV_EXPORT_URL = "https://oeffentlichevergabe.de/api/notice-exports"
DE_OV_NOTICE_URL = "https://oeffentlichevergabe.de/ui/de/notice/{nid}"

CPV_CODES = [
    "34131000", "34113000", "34136000", "34130000", "34136200",
    "50110000", "50112000", "50114000", "50116000", "50111000",
]

DE_OV_VEHICLE_STEMS = (
    "fahrzeug", "fuhrpark", "nutzfahrzeug", "pritschen", "flotten",
    "lieferwagen", "transporter", "bestelwagen", "pickup", "pick-up",
    "chassis", "isuzu", "d-max", "lkw", "nkw", "kfz-", "kastenwagen",
    "kipper", "abrollkipper", "sattelzug", "lastkraft",
)
DE_OV_CPV_PREFIXES = ("3413", "34113", "34136", "5011")

KEYWORDS_DE = [
    "fahrzeug", "fuhrpark", "nutzfahrzeug", "lkw", "nkw", "transporter",
    "lieferwagen", "pritsche", "pickup", "pick-up", "chassis", "isuzu",
    "d-max", "flotten", "kfz", "lastkraft",
]


def _cpv_hit(code: str) -> bool:
    code = (code or "").strip()
    if "-" in code:
        code = code.split("-", 1)[0].strip()
    if not code or not code[0].isdigit() or len(code) < 4:
        return False
    if code in CPV_CODES:
        return True
    for c in CPV_CODES:
        if len(c) >= 6 and code.startswith(c[:6]):
            return True
    return any(code.startswith(p) for p in DE_OV_CPV_PREFIXES)


def _norm_cpv(code: str) -> str:
    code = (code or "").strip()
    if "-" in code:
        code = code.split("-", 1)[0].strip()
    m = re.match(r"^(\d{8})", code)
    return m.group(1) if m else code


def _read_csv_table(zf: zipfile.ZipFile, name: str) -> List[Dict[str, str]]:
    if name not in zf.namelist():
        return []
    text = zf.read(name).decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


def _months_covering(from_dt: datetime, now: datetime) -> List[str]:
    months: List[str] = []
    end = (now - timedelta(days=1)).date()
    cur = from_dt.date().replace(day=1)
    while cur <= end:
        months.append(cur.strftime("%Y-%m"))
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return months


def _match_kw(blob: str, kws: List[str]) -> bool:
    b = (blob or "").lower()
    return any(k.lower() in b for k in kws)


def parse_csv_zip(
    body: bytes,
    *,
    cutoff: str,
    seen: Set[str],
) -> Tuple[List[Dict[str, Any]], int, int]:
    results: List[Dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        notices = {
            (r["noticeIdentifier"], r["noticeVersion"]): r
            for r in _read_csv_table(zf, "notice.csv")
            if r.get("noticeIdentifier")
        }
        purpose_rows = _read_csv_table(zf, "purpose.csv")
        class_rows = _read_csv_table(zf, "classification.csv")
        org_rows = _read_csv_table(zf, "organisation.csv")
        result_rows = _read_csv_table(zf, "noticeResult.csv")

    purpose_by: Dict[Tuple[str, str], Dict[str, str]] = {}
    for p in purpose_rows:
        key = (p.get("noticeIdentifier") or "", p.get("noticeVersion") or "")
        if not key[0]:
            continue
        lot = (p.get("lotIdentifier") or "").strip()
        existing = purpose_by.get(key)
        if existing and existing.get("_lot") == "" and lot:
            continue
        if existing and existing.get("_lot") != "" and lot and existing.get("title"):
            continue
        purpose_by[key] = {
            "title": (p.get("title") or "").strip(),
            "description": (p.get("description") or "").strip(),
            "value": (p.get("estimatedValue") or "").strip(),
            "currency": (p.get("estimatedValueCurrency") or "EUR").strip(),
            "_lot": lot,
        }

    cpv_by: Dict[Tuple[str, str], str] = {}
    cpv_hit_keys: Set[Tuple[str, str]] = set()
    for c in class_rows:
        key = (c.get("noticeIdentifier") or "", c.get("noticeVersion") or "")
        if not key[0]:
            continue
        codes = [c.get("mainClassificationCode") or ""]
        add = c.get("additionalClassificationCodes") or ""
        if add:
            codes.extend(re.split(r"[;,\s]+", add))
        for code in codes:
            code = _norm_cpv(code or "")
            if not code:
                continue
            if key not in cpv_by:
                cpv_by[key] = code
            if _cpv_hit(code):
                cpv_hit_keys.add(key)
                cpv_by[key] = code
                break

    buyer_by: Dict[Tuple[str, str], str] = {}
    for o in org_rows:
        key = (o.get("noticeIdentifier") or "", o.get("noticeVersion") or "")
        if not key[0] or key in buyer_by:
            continue
        role = (o.get("organisationRole") or "").lower()
        name = (o.get("organisationName") or "").strip()
        if not name:
            continue
        if "buyer" in role or role in ("", "buyer"):
            buyer_by[key] = name
        elif key not in buyer_by:
            buyer_by[key] = name

    value_by: Dict[Tuple[str, str], Tuple[str, str]] = {}
    for nr in result_rows:
        key = (nr.get("noticeIdentifier") or "", nr.get("noticeVersion") or "")
        val = (nr.get("noticeValue") or nr.get("noticeFrameworkValue") or "").strip()
        cur = (
            nr.get("noticeValueCurrency")
            or nr.get("noticeFrameworkValueCurrency")
            or "EUR"
        ).strip()
        if key[0] and val:
            value_by[key] = (val, cur)

    scanned = 0
    for key, notice in notices.items():
        scanned += 1
        nid, ver = key
        pub = str(notice.get("publicationDate") or "")
        pub_day = pub[:10]
        if pub_day and pub_day < cutoff:
            continue
        purpose = purpose_by.get(key) or {}
        title = purpose.get("title") or ""
        desc = purpose.get("description") or ""
        blob = f"{title} {desc}".lower()
        cpv_code = cpv_by.get(key, "")
        cpv_ok = key in cpv_hit_keys
        stem_ok = any(s in blob for s in DE_OV_VEHICLE_STEMS)
        kw_ok = stem_ok and _match_kw(blob, KEYWORDS_DE)
        cpv_family_ok = bool(cpv_code) and (
            cpv_code.startswith("34") or cpv_code.startswith("501")
        )
        if not cpv_ok and not (kw_ok and (not cpv_code or cpv_family_ok)):
            continue
        if nid in seen:
            continue
        seen.add(nid)

        value = purpose.get("value") or ""
        currency = purpose.get("currency") or "EUR"
        if not value and key in value_by:
            value, currency = value_by[key]

        ntype = notice.get("noticeType") or notice.get("formType") or ""
        nform = notice.get("formType") or ""
        lifecycle = (
            lifecycle_from_notice_type(nform)
            or lifecycle_from_notice_type(ntype)
            or classify_lifecycle(f"{title} {desc}", ntype)
        )
        results.append(
            {
                "Source": "🇩🇪 DE-OV",
                "Source Notice ID": nid,
                "Lifecycle": lifecycle,
                "Notice Type": ntype,
                "Procedure Type": "",
                "Buyer Type": "",
                "Score": "",
                "FleetSize": "",
                "Title": title or nid,
                "Buyer": buyer_by.get(key, ""),
                "Country": "Germany",
                "Country Code": "DEU",
                "Published": pub_day,
                "Deadline": "",
                "Value": value,
                "Currency": currency,
                "CPV Code": _norm_cpv(cpv_by.get(key, "")),
                "CPV Desc": "",
                "URL": DE_OV_NOTICE_URL.format(nid=nid),
                "Description": (desc or title)[:2000],
                "Fit Score": "",
                "Win Score": "",
                "Econ Score": "",
                "Decision": "",
                "Evidence Score": "",
                "Evidence Label": "",
                "Suggested Owner": "",
                "Suggested Status": "",
                "Days to Deadline": "",
                "Urgency": "",
                "Reasons": f"ov_ver={ver}; cpv_hit={cpv_ok}; kw_hit={kw_ok}",
            }
        )
    return results, scanned, len(results)


def fetch_germany_ov(
    session: Optional[requests.Session] = None,
    from_dt: Optional[datetime] = None,
    *,
    errors: Optional[Dict[str, Optional[str]]] = None,
) -> List[Dict[str, Any]]:
    """National DE notices via oeffentlichevergabe Bekanntmachungsservice Open Data CSV ZIPs."""
    print("\n[DE OV] Fetching oeffentlichevergabe Open Data (csv.zip, vehicle CPV/keyword)...")
    own = session is None
    session = session or requests.Session()
    from_dt = from_dt or datetime.now(timezone.utc)
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    now = datetime.now(timezone.utc)
    cutoff = from_dt.strftime("%Y-%m-%d")
    months = _months_covering(from_dt, now)
    last_err: Optional[str] = None
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ISZE-TenderMonitor/3.0)",
        "Accept": "application/vnd.bekanntmachungsservice.csv.zip+zip, application/zip, */*",
    }
    total_scanned = 0
    try:
        if not months:
            last_err = "no exportable months in lookback"
            print("  [DE OV] no months to fetch")
        else:
            for month in months:
                params = {"pubMonth": month, "format": "csv.zip"}
                try:
                    resp = session.get(
                        DE_OV_EXPORT_URL, params=params, headers=headers, timeout=180
                    )
                except Exception as exc:
                    last_err = str(exc)
                    print(f"  [DE OV] {month}: {exc}")
                    continue
                body = resp.content or b""
                if resp.status_code != 200:
                    last_err = f"HTTP {resp.status_code} month={month}"
                    print(f"  [DE OV] {month}: {last_err}")
                    continue
                if body[:2] != b"PK":
                    last_err = f"non-ZIP response month={month} ({len(body)} bytes)"
                    print(f"  [DE OV] {month}: non-ZIP body")
                    continue
                rows, scanned, hits = parse_csv_zip(body, cutoff=cutoff, seen=seen)
                total_scanned += scanned
                results.extend(rows)
                print(
                    f"  [DE OV] {month}: scanned≈{scanned} vehicle-ish +{hits} "
                    f"(zip {len(body)} bytes)"
                )
                last_err = None
            print(
                f"[DE OV] Unique matches: {len(results)} "
                f"(scanned≈{total_scanned} across {months})"
            )
    except Exception as exc:
        last_err = str(exc)
        print(f"  [DE OV] exception: {exc}")
    finally:
        if own:
            session.close()
    if errors is not None:
        errors["Germany oeffentlichevergabe"] = last_err
    return results


if __name__ == "__main__":
    from datetime import timedelta

    err: Dict[str, Optional[str]] = {}
    lookback = datetime.now(timezone.utc) - timedelta(days=30)
    rows = fetch_germany_ov(from_dt=lookback, errors=err)
    print("error:", err.get("Germany oeffentlichevergabe"), "n=", len(rows))
    for r in rows[:5]:
        print(" -", (r.get("Title") or "")[:100])
