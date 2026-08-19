"""
ISZE Tender Collector v3

Key changes versus v2:
- Surgical CPV list: removed 34100000 (too broad), removed all 34144xxx special-vehicle
  subcodes (firefighting, refuse, ambulance, armoured). Added targeted codes only.
- TED query now filters by ISZE target country list — no more Moldova, Serbia, Iceland.
- TED detail fetch: for each matched notice, fetches the full notice detail to get
  deadline, estimated value, description, buyer type, procedure type. This fixes the
  85% missing-deadline and 99% missing-value problem.
- cpv_is_excluded() gate applied before any row is normalized or scored.
- Rate limit handling improved with configurable delay.

Run:
  python tender_scraper_v3.py
Then:
  python build_dashboard_v2.py --input /path/to/isuzu_tenders_v3.xlsx
"""

from __future__ import annotations

import ast
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# Windows fix: force UTF-8 output so emoji + special chars don't crash cmd.exe
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import openpyxl
import requests

from isze_core_v3 import (
    EXCLUDED_CPV_PREFIXES,
    ISZE_TARGET_MARKETS,
    classify_lifecycle,
    cpv_is_excluded,
    extract_fleet_size,
    extract_text,
    normalize_raw_row,
    parse_number,
    score_legacy,
)

LOOKBACK_DAYS = 30
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "isuzu_tenders_v3.xlsx")
DOFFIN_API_KEY = ""
HILMA_API_KEY = ""
UK_STAGES = "planning,tender,award"

# v3: fetch full TED detail for matched notices (fixes missing deadline/value)
TED_FETCH_DETAIL = False  # Detail API requires auth — disabled Apr 2026
# Delay between TED detail calls in seconds — stay well within rate limits.
# TED public API allows ~3 req/sec; 0.4s is conservative but safe.
TED_DETAIL_DELAY = 0.4

# ---------------------------------------------------------------------------
# v3: Surgical CPV list
# Removed: 34100000 (parent — too broad, returns firefighting/refuse/ambulance)
#          34120000 (buses), 34114000 (special purpose — too ambiguous at parent level)
# Added:   34111000 (estate cars), 34136200 (panel vans) as supplementary
# ---------------------------------------------------------------------------
CPV_CODES = [
    "34131000",  # Pickups — D-Max core
    "34113000",  # 4WD vehicles
    "34136000",  # Vans
    "34130000",  # Motor vehicles for goods transport (lorries/rigids)
    "34136200",  # Panel vans
    "50110000",  # Repair and maintenance of motor vehicles
    "50112000",  # Repair of cars
    "50116000",  # Repair of specific vehicle parts
    "50111000",  # Vehicle fleet management and repair services
]

# v3: ISZE's active markets for TED country filter
TED_TARGET_COUNTRIES = [
    "GBR", "IRL", "POL", "PRT", "GRC", "ISR",
    "DEU", "FRA", "ESP", "ITA", "NLD", "BEL",
    "DNK", "SWE", "NOR", "FIN", "ROU", "HUN",
    "CZE", "SVK", "BGR", "HRV", "AUT", "LVA",
    "LTU", "EST", "SVN",
]

KEYWORDS = [
    "vehicle", "van", "truck", "pickup", "pick-up", "4x4", "chassis cab", "tipper",
    "dropside", "crew cab", "double cab", "flatbed", "box van", "fleet", "lcv",
    "goods vehicle", "commercial vehicle", "motor vehicle", "light goods",
    "municipal vehicle", "service vehicle", "pool vehicle", "road maintenance",
    "public works vehicle", "isuzu", "d-max", "d max", "dmax", "n-series", "n series",
    "f-series", "f series", "pickup truck", "pick up truck", "4x4 vehicle",
    "off-road vehicle", "all-terrain vehicle", "utility vehicle", "light utility",
    "single cab", "extra cab", "light truck", "medium truck", "rigid truck",
    "3.5 tonne", "3.5t ", "5 tonne", "7.5 tonne", "7.5t ",
    "12 tonne", "12t ", "tipper truck", "tipping truck",
    "maintenance", "repair", "fleet management", "spare parts", "service contract",
]
KEYWORDS_HE = ["רכב", "משאית", "טנדר", "כלי רכב", "רכב שטח", "רכב מסחרי", "צי רכבים"]

EXPORT_HEADERS = [
    "Source", "Source Notice ID", "Lifecycle", "Notice Type", "Procedure Type", "Buyer Type",
    "Score", "FleetSize", "Title", "Buyer", "CPV Code", "CPV Desc", "Description",
    "Est. Value", "Currency", "Published", "Published Date", "Deadline", "Deadline Date",
    "Country", "Country Code", "URL", "Fit Score", "Win Score", "Economic Score",
    "Decision", "Evidence Score", "Evidence Label", "Suggested Owner", "Suggested Status",
    "Suggested Next Action",
]


def match_keywords(text: str, keywords: List[str]) -> bool:
    hay = (text or "").lower()
    return any(k.lower() in hay for k in keywords)


def safe_get(d: Dict[str, Any], path: List[Any], default: Any = "") -> Any:
    cur: Any = d
    for part in path:
        if isinstance(cur, list):
            try:
                cur = cur[part]
                continue
            except Exception:
                return default
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur if cur not in (None, "") else default


# 2026-07-14: backoff lengthened per Jerome's decision (option "wait longer" over
# API key / accept-partial-coverage) for UK Find a Tender 429s — see DECISIONS.md.
# Old schedule (4 tries, 5/10/15/20s) was too fast for FaT's limiter. New schedule
# is slower but should clear the block reliably; a run that hits 429 repeatedly
# on every page can now take several extra minutes, which is the accepted trade-off.
RATE_LIMIT_BACKOFF_SCHEDULE = [30, 60, 90, 120, 180, 240]


def get_with_retry(session: requests.Session, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 6):
    for attempt in range(max_retries):
        try:
            r = session.get(url, params=params, timeout=30)
            if r.status_code == 429:
                wait = RATE_LIMIT_BACKOFF_SCHEDULE[min(attempt, len(RATE_LIMIT_BACKOFF_SCHEDULE) - 1)]
                print(f"  Rate limited — waiting {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except Exception:
            time.sleep(2 + attempt * 2)
    return None


def post_with_retry(session: requests.Session, url: str, payload: Dict[str, Any], max_retries: int = 6):
    for attempt in range(max_retries):
        try:
            r = session.post(url, json=payload, timeout=30)
            if r.status_code == 429:
                wait = RATE_LIMIT_BACKOFF_SCHEDULE[min(attempt, len(RATE_LIMIT_BACKOFF_SCHEDULE) - 1)]
                print(f"  Rate limited — waiting {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except Exception:
            time.sleep(2 + attempt * 2)
    return None


def flatten_for_export(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Source": row.get("Source", ""),
        "Source Notice ID": row.get("Source Notice ID", ""),
        "Lifecycle": row.get("Lifecycle", ""),
        "Notice Type": row.get("Notice Type", ""),
        "Procedure Type": row.get("Procedure Type", ""),
        "Buyer Type": row.get("Buyer Type", ""),
        "Score": row.get("Score", ""),
        "FleetSize": row.get("FleetSize", ""),
        "Title": row.get("Title", ""),
        "Buyer": row.get("Buyer", ""),
        "CPV Code": row.get("CPV Code", ""),
        "CPV Desc": row.get("CPV Desc", ""),
        "Description": row.get("Description", ""),
        "Est. Value": row.get("Est. Value", ""),
        "Currency": row.get("Currency", ""),
        "Published": row.get("Published", ""),
        "Published Date": row.get("Published Date", ""),
        "Deadline": row.get("Deadline", ""),
        "Deadline Date": row.get("Deadline Date", ""),
        "Country": row.get("Country", ""),
        "Country Code": row.get("Country Code", ""),
        "URL": row.get("URL", ""),
        "Fit Score": row.get("fit_score", ""),
        "Win Score": row.get("win_score", ""),
        "Economic Score": row.get("econ_score", ""),
        "Decision": row.get("decision", ""),
        "Evidence Score": row.get("evidence_score", ""),
        "Evidence Label": row.get("evidence_label", ""),
        "Suggested Owner": row.get("owner_suggested", ""),
        "Suggested Status": row.get("status_suggested", ""),
        "Suggested Next Action": row.get("next_action_suggested", ""),
    }


def normalize_batch(rows: List[Dict[str, Any]], source_label: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        row.setdefault("Source", source_label)
        # v3: skip before scoring if CPV is in exclusion list
        cpv = str(row.get("CPV Code", "") or "")
        if cpv_is_excluded(cpv):
            continue
        norm = normalize_raw_row(row, source_label)
        out.append(flatten_for_export(norm))
    return out


# ---------------------------------------------------------------------------
# UK (unchanged logic, import from v3 core)
# ---------------------------------------------------------------------------

def first_cpv_from_release(rel: Dict[str, Any]) -> Dict[str, str]:
    tender = rel.get("tender", {}) or {}
    direct = safe_get(tender, ["classification"], {})
    if isinstance(direct, dict) and direct.get("id"):
        return {"id": str(direct.get("id", "")), "description": str(direct.get("description", ""))}
    for award in rel.get("awards", []) or []:
        for item in award.get("items", []) or []:
            for cls in item.get("additionalClassifications", []) or []:
                if cls.get("scheme") == "CPV":
                    return {"id": str(cls.get("id", "")), "description": str(cls.get("description", ""))}
    return {"id": "", "description": ""}


def uk_notice_type(rel: Dict[str, Any]) -> str:
    tags = rel.get("tag", []) or []
    contracts = rel.get("contracts", []) or []
    for c in contracts:
        for doc in c.get("documents", []) or []:
            if doc.get("noticeType"):
                return str(doc.get("noticeType"))
    return ", ".join(str(t) for t in tags)


def uk_buyer_type(rel: Dict[str, Any]) -> str:
    buyer_id = safe_get(rel, ["buyer", "id"])
    for party in rel.get("parties", []) or []:
        if party.get("id") == buyer_id:
            classes = safe_get(party, ["details", "classifications"], [])
            if isinstance(classes, list):
                for cls in classes:
                    if cls.get("description"):
                        return str(cls.get("description"))
    return ""


def uk_country(rel: Dict[str, Any]) -> str:
    buyer_id = safe_get(rel, ["buyer", "id"])
    for party in rel.get("parties", []) or []:
        if party.get("id") == buyer_id:
            return safe_get(party, ["address", "countryName"], "United Kingdom")
    return "United Kingdom"


def fetch_uk(session: requests.Session, from_dt: datetime, to_dt: datetime) -> List[Dict[str, Any]]:
    print("\n[UK] Fetching from Find a Tender...")
    base_url = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages"
    all_releases: List[Dict[str, Any]] = []
    cursor = None
    page = 0

    # Find a Tender API: 'stages' is the correct parameter name.
    # Stage values: planning, tender, award — use comma-separated string.
    # If the API returns 0 releases we retry without the stages filter as a fallback
    # (the API behaviour has changed over time for this parameter).
    def _build_params(cursor_val):
        p = {
            "updatedFrom": from_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "updatedTo": to_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "stages": UK_STAGES,
            "limit": 100,
        }
        if cursor_val:
            p["cursor"] = cursor_val
        return p

    while page < 60:
        params = _build_params(cursor)
        resp = get_with_retry(session, base_url, params=params)
        if not resp:
            print(f"[UK] Request failed (page {page+1}). Stopping UK fetch.")
            break

        if resp.status_code != 200:
            print(f"[UK] HTTP {resp.status_code}: {resp.text[:200]}")
            # If stages parameter is rejected, retry without it once
            if page == 0 and resp.status_code in (400, 422):
                print("[UK] Retrying without stages filter...")
                params.pop("stages", None)
                resp = get_with_retry(session, base_url, params=params)
                if not resp or resp.status_code != 200:
                    print("[UK] Retry also failed — skipping UK source.")
                    break
            else:
                break

        try:
            pkg = resp.json()
        except Exception as exc:
            print(f"[UK] JSON decode error: {exc}")
            break

        # Diagnostic: log top-level keys on first page
        if page == 0:
            print(f"  [UK] API response keys: {list(pkg.keys())[:6]}")

        releases = pkg.get("releases", []) or []
        all_releases.extend(releases)
        print(f"  Page {page + 1}: {len(releases)} releases (total: {len(all_releases)})")

        # If first page returns 0, try without stages filter
        if page == 0 and len(releases) == 0:
            print("[UK] Zero releases on page 1 with stages filter — retrying without it...")
            params_no_stage = {k: v for k, v in params.items() if k != "stages"}
            resp2 = get_with_retry(session, base_url, params=params_no_stage)
            if resp2 and resp2.status_code == 200:
                try:
                    pkg2 = resp2.json()
                    releases2 = pkg2.get("releases", []) or []
                    print(f"  [UK] Without stages filter: {len(releases2)} releases")
                    if releases2:
                        all_releases.extend(releases2)
                        # Continue pagination using this fallback approach
                        next_url2 = safe_get(pkg2, ["links", "next"], None)
                        if next_url2 and "cursor=" in next_url2:
                            cursor = next_url2.split("cursor=")[-1]
                            page += 1
                            time.sleep(0.5)
                            continue
                        break
                except Exception:
                    pass
            break

        next_url = safe_get(pkg, ["links", "next"], None)
        if next_url and "cursor=" in next_url:
            cursor = next_url.split("cursor=")[-1]
        else:
            break
        page += 1
        time.sleep(0.5)

    print(f"[UK] Total fetched: {len(all_releases)}")

    results: List[Dict[str, Any]] = []
    excluded_cpv = 0
    for rel in all_releases:
        tender = rel.get("tender", {}) or {}
        title = extract_text(tender.get("title"))
        description = extract_text(tender.get("description"))
        cpv = first_cpv_from_release(rel)

        # v3: CPV exclusion gate
        if cpv_is_excluded(cpv.get("id", "")):
            excluded_cpv += 1
            continue

        blob = " ".join([title, description, cpv.get("description", "")])
        if not match_keywords(blob, KEYWORDS):
            continue

        value = safe_get(tender, ["value", "amount"]) or safe_get(tender, ["value", "amountGross"])
        if not value:
            contracts = rel.get("contracts", []) or []
            if contracts:
                value = safe_get(contracts[0], ["value", "amount"]) or safe_get(contracts[0], ["value", "amountGross"])

        tags = rel.get("tag", []) or []
        lifecycle = classify_lifecycle(blob, " ".join(str(t) for t in tags))
        notice_url = ""
        for c in rel.get("contracts", []) or []:
            for doc in c.get("documents", []) or []:
                notice_url = doc.get("url") or notice_url
                if notice_url:
                    break
            if notice_url:
                break
        notice_url = notice_url or f"https://www.find-tender.service.gov.uk/Notice/{rel.get('id','')}"

        results.append({
            "Source": "🇬🇧 UK",
            "Source Notice ID": str(rel.get("id", "")),
            "Lifecycle": lifecycle,
            "Notice Type": uk_notice_type(rel),
            "Procedure Type": extract_text(tender.get("procurementMethodDetails") or tender.get("procurementMethod")),
            "Buyer Type": uk_buyer_type(rel),
            "Score": score_legacy(title, parse_number(value)),
            "FleetSize": extract_fleet_size(title),
            "Title": title,
            "Buyer": safe_get(rel, ["buyer", "name"]),
            "CPV Code": cpv.get("id", ""),
            "CPV Desc": cpv.get("description", ""),
            "Description": description,
            "Est. Value": value,
            "Currency": safe_get(tender, ["value", "currency"]) or safe_get(rel, ["contracts", 0, "value", "currency"]),
            "Published": str(rel.get("date") or ""),
            "Deadline": safe_get(tender, ["tenderPeriod", "endDate"]),
            "Country": uk_country(rel),
            "Country Code": "GBR",
            "URL": notice_url,
        })

    print(f"[UK] Matches: {len(results)} (excluded {excluded_cpv} by CPV gate)")
    return results


# ---------------------------------------------------------------------------
# TED v3: surgical CPV list + country filter + full detail fetch
# ---------------------------------------------------------------------------

def _ted_detail_fields(notice: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract enriched fields from a full TED notice detail response.

    TED API v3 notice structure varies by notice type (Contract Notice, Prior
    Information Notice, Award Notice, etc.) and has changed between API versions.
    We try multiple known paths and take the first non-empty value.
    """
    out: Dict[str, Any] = {}

    def _first(*candidates):
        for c in candidates:
            if c and c not in ("", "None"):
                return c
        return ""

    # --- Deadline ---
    # TED v3 stores submission deadlines in several possible locations depending
    # on notice form type (F02, F01, eForms, etc.)
    procurement = notice.get("procurement", {}) or {}
    tender_period = procurement.get("tenderPeriod", {}) or {}
    lots = notice.get("lots", []) or []
    first_lot = lots[0] if lots else {}
    lot_tender_period = first_lot.get("tenderPeriod", {}) or {}

    # eForms path (most common in 2024-2025 notices)
    eforms = notice.get("noticeBody", {}) or {}

    out["Deadline"] = _first(
        # eForms fields
        eforms.get("submissionDeadlineDateTime"),
        eforms.get("tenderSubmissionDeadlineDate"),
        # Classic TED v3 paths
        tender_period.get("endDate"),
        tender_period.get("dueDate"),
        lot_tender_period.get("endDate"),
        lot_tender_period.get("dueDate"),
        notice.get("submissionDeadline"),
        notice.get("submissionDeadlineDate"),
        notice.get("submissionDeadlineDateTime"),
        procurement.get("submissionDeadline"),
        # Sometimes present directly on the notice root (legacy XML→JSON)
        notice.get("DT"),
        notice.get("dt"),
    )

    # --- Estimated value ---
    def _extract_value(obj):
        if obj is None:
            return "", ""
        if isinstance(obj, (int, float)):
            return obj, ""
        if isinstance(obj, dict):
            amt = obj.get("amount") or obj.get("amountGross") or obj.get("value")
            ccy = obj.get("currency", "")
            return (amt, ccy) if amt else ("", ccy)
        return "", ""

    val, ccy = "", ""
    for candidate in [
        procurement.get("estimatedValue"),
        procurement.get("value"),
        eforms.get("estimatedOverallContractValue"),
        eforms.get("estimatedValue"),
        notice.get("estimatedValue"),
        notice.get("TV"),  # legacy XML→JSON field
    ]:
        if candidate:
            val, ccy = _extract_value(candidate)
            if val:
                break

    # Fallback: look inside lots
    if not val and lots:
        for lot in lots:
            lot_val, lot_ccy = _extract_value(
                lot.get("estimatedValue") or lot.get("value")
            )
            if lot_val:
                val, ccy = lot_val, lot_ccy
                break

    out["Est. Value"] = val
    out["Currency"] = ccy

    # --- Description ---
    out["Description"] = extract_text(
        _first(
            eforms.get("shortDescription"),
            procurement.get("description"),
            notice.get("description"),
            notice.get("OD"),
        )
    )

    # --- Buyer type ---
    buyer_raw = notice.get("buyer", {}) or {}
    contracting_body = eforms.get("contractingBody", {}) or {}
    out["Buyer Type"] = extract_text(
        _first(
            contracting_body.get("mainActivityDescription"),
            contracting_body.get("caActivityCode"),
            buyer_raw.get("mainActivity"),
            buyer_raw.get("buyerType"),
        )
    )

    # --- Procedure type ---
    out["Procedure Type"] = extract_text(
        _first(
            eforms.get("procedureCode"),
            eforms.get("procedure"),
            procurement.get("procurementMethod"),
            procurement.get("procedureType"),
            notice.get("procedureType"),
            notice.get("PR"),
        )
    )

    # --- CPV description ---
    # Try multiple locations; classification items from procurement are most reliable
    for cpv_src in [
        procurement.get("classification"),
        eforms.get("cpvAdditional"),
        notice.get("classification"),
    ]:
        if not cpv_src:
            continue
        items = [cpv_src] if isinstance(cpv_src, dict) else (cpv_src if isinstance(cpv_src, list) else [])
        for item in items:
            desc = extract_text(item.get("description") if isinstance(item, dict) else "")
            if desc:
                out["CPV Desc"] = desc
                break
        if out.get("CPV Desc"):
            break

    return out


def fetch_ted_detail(session: requests.Session, notice_id: str) -> Dict[str, Any]:
    """Fetch full notice detail from TED API v3 with proper error surfacing."""
    url = f"https://api.ted.europa.eu/v3/notices/{notice_id}"
    try:
        resp = get_with_retry(session, url)
        if resp is None:
            print(f"    [TED detail] {notice_id}: request failed after retries")
            return {}
        if resp.status_code == 404:
            return {}  # notice not found — silent
        if resp.status_code != 200:
            print(f"    [TED detail] {notice_id}: HTTP {resp.status_code}")
            return {}
        data = resp.json()
        # Detail may be nested under "notice" or returned at root
        notice = data.get("notice", data)
        result = _ted_detail_fields(notice)
        if not result.get("Deadline"):
            # Log once every 20 calls so we can diagnose without flooding output
            if hasattr(fetch_ted_detail, "_no_dl_count"):
                fetch_ted_detail._no_dl_count += 1
            else:
                fetch_ted_detail._no_dl_count = 1
            if fetch_ted_detail._no_dl_count <= 3:
                print(f"    [TED detail] {notice_id}: no deadline found — top-level keys: {list(notice.keys())[:8]}")
        return result
    except Exception as exc:
        print(f"    [TED detail] {notice_id}: exception — {exc}")
    return {}


def fetch_ted(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    print("\n[TED] Fetching from TED Europa (v3 — surgical CPV + country filter)...")
    url = "https://api.ted.europa.eu/v3/notices/search"
    date_from = from_dt.strftime("%Y%m%d")

    # v3: only query ISZE target CPV codes
    cpv_block = " OR ".join([f"PC={c}" for c in CPV_CODES])

    # v3: restrict to ISZE target markets
    country_block = " OR ".join([f"CY={c}" for c in TED_TARGET_COUNTRIES])

    query = f"({cpv_block}) AND ({country_block}) AND PD>={date_from}"
    print(f"  Query: {query}")

    all_notices: List[Dict[str, Any]] = []
    next_token = None
    while True:
        payload = {
            "query": query,
            "fields": ["ND", "TI", "PD", "DD", "CY", "PC", "AU"],
            "limit": 100,
            "paginationMode": "ITERATION",
        }
        if next_token:
            payload["iterationNextToken"] = next_token
        try:
            resp = session.post(url, json=payload, timeout=30)
            print(f"  Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"  TED error: {resp.text[:300]}")
                break
            data = resp.json()
            notices = data.get("notices", []) or []
            if not notices:
                break
            all_notices.extend(notices)
            print(f"  Fetched {len(notices)} (running total: {len(all_notices)})")
            next_token = data.get("iterationNextToken")
            if not next_token:
                break
            time.sleep(0.5)
        except Exception as exc:
            print(f"  TED exception: {exc}")
            break

    print(f"[TED] Total fetched: {len(all_notices)} — applying keyword + CPV exclusion filter...")

    results: List[Dict[str, Any]] = []
    excluded_cpv = 0
    keyword_misses = 0

    for n in all_notices:
        # v3: CPV exclusion gate before any work
        cpv_raw = extract_text(n.get("PC", ""))
        if cpv_is_excluded(cpv_raw):
            excluded_cpv += 1
            continue

        title_raw = n.get("TI", {})
        if isinstance(title_raw, str):
            try:
                title_raw = ast.literal_eval(title_raw)
            except Exception:
                pass
        title = extract_text(title_raw)

        if not match_keywords(title, KEYWORDS):
            keyword_misses += 1
            continue

        country = extract_text(n.get("CY", ""))
        buyer_raw = n.get("AU", "")
        if isinstance(buyer_raw, str):
            try:
                buyer_raw = ast.literal_eval(buyer_raw)
            except Exception:
                pass
        buyer = extract_text(buyer_raw)
        notice_id = str(n.get("ND", ""))

        row: Dict[str, Any] = {
            "Source": "🇪🇺 EU",
            "Source Notice ID": notice_id,
            "Lifecycle": classify_lifecycle(title, ""),
            "Notice Type": "",
            "Procedure Type": "",
            "Buyer Type": "",
            "Score": score_legacy(title),
            "FleetSize": extract_fleet_size(title),
            "Title": title,
            "Buyer": buyer,
            "CPV Code": cpv_raw,
            "CPV Desc": "",
            "Description": "",
            "Est. Value": "",
            "Currency": "",
            "Published": str(n.get("PD", "")),
            "Deadline": str(n.get("DD", "")),
            "Country": country,
            "Country Code": country,
            "URL": f"https://ted.europa.eu/en/notice/-/detail/{notice_id}",
        }

        # v3: fetch full detail to populate deadline, value, description
        if TED_FETCH_DETAIL and notice_id:
            detail = fetch_ted_detail(session, notice_id)
            for field, val in detail.items():
                if val and not row.get(field):
                    row[field] = val
            time.sleep(TED_DETAIL_DELAY)

        results.append(row)

    got_deadline = sum(1 for r in results if r.get("Deadline"))
    got_value = sum(1 for r in results if r.get("Est. Value"))
    print(f"[TED] Keyword matches: {len(results)}")
    print(f"  Excluded by CPV gate:   {excluded_cpv}")
    print(f"  Excluded by keyword:    {keyword_misses}")
    print(f"  Detail fetch results:   deadline={got_deadline}/{len(results)} ({100*got_deadline//max(len(results),1)}%) | value={got_value}/{len(results)} ({100*got_value//max(len(results),1)}%)")
    if got_deadline == 0 and len(results) > 0 and TED_FETCH_DETAIL:
        print("  ⚠ Zero deadlines retrieved — TED API structure may have changed.")
        print("  ⚠ Check the diagnostic output above for 'top-level keys' to update _ted_detail_fields().")
    return results


# ---------------------------------------------------------------------------
# Israel RSS (unchanged)
# ---------------------------------------------------------------------------

def fetch_israel(session: requests.Session) -> List[Dict[str, Any]]:
    print("\n[IL] Fetching Israel government tenders RSS...")
    url = "https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml"
    try:
        resp = get_with_retry(session, url)
        if not resp:
            print("[IL] Failed to fetch RSS.")
            return []
        raw = resp.content
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            # mr.gov.il embeds HTML entities (e.g. &nbsp;, &laquo;) that are not
            # valid bare XML entities. Escape anything that isn't a standard or
            # numeric XML entity, then retry once before giving up (falls through
            # to the except-Exception handler below if this also fails).
            import re
            sanitized = re.sub(
                rb"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)(\w+);",
                rb"&amp;\1;",
                raw,
            )
            root = ET.fromstring(sanitized)
        results: List[Dict[str, Any]] = []
        for item in root.findall(".//item"):
            title = extract_text(item.findtext("title"))
            link = extract_text(item.findtext("link"))
            pub_date = extract_text(item.findtext("pubDate"))
            if not match_keywords(title, KEYWORDS + KEYWORDS_HE):
                continue
            results.append({
                "Source": "🇮🇱 Israel",
                "Source Notice ID": link.rstrip("/").split("/")[-1],
                "Lifecycle": classify_lifecycle(title, ""),
                "Notice Type": "",
                "Procedure Type": "",
                "Buyer Type": "",
                "Score": score_legacy(title),
                "FleetSize": extract_fleet_size(title),
                "Title": title,
                "Buyer": "",
                "CPV Code": "",
                "CPV Desc": "",
                "Description": "",
                "Est. Value": "",
                "Currency": "",
                "Published": pub_date,
                "Deadline": "",
                "Country": "Israel",
                "Country Code": "ISR",
                "URL": link,
            })
        print(f"[IL] Matches: {len(results)}")
        return results
    except Exception as exc:
        print(f"[IL] Error: {exc}")
        return []


# ---------------------------------------------------------------------------
# Doffin (unchanged logic, uses v3 exclusion gate)
# ---------------------------------------------------------------------------

def fetch_doffin(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    if not DOFFIN_API_KEY:
        print("\n[Doffin] No API key set — skipping.")
        return []

    print("\n[Doffin] Fetching from Doffin (Norway)...")
    base_url = "https://betaapi.doffin.no/public/v2/notices"
    headers = {"Ocp-Apim-Subscription-Key": DOFFIN_API_KEY}
    date_from = from_dt.strftime("%Y-%m-%d")
    search_terms = " OR ".join(["vehicle", "truck", "van", "fleet", "pickup", "commercial vehicle", "maintenance"])
    results: List[Dict[str, Any]] = []
    page = 1
    limit = 100

    while True:
        params = {
            "searchString": search_terms,
            "publishedFrom": date_from,
            "limit": limit,
            "offset": (page - 1) * limit,
        }
        try:
            resp = session.get(base_url, headers=headers, params=params, timeout=30)
            print(f"  Page {page} – Status: {resp.status_code}")
            if resp.status_code == 401:
                print("  [Doffin] Invalid API key.")
                break
            if resp.status_code != 200:
                print(f"  [Doffin] Error: {resp.text[:300]}")
                break
            data = resp.json()
            notices = data.get("notices", data.get("items", data if isinstance(data, list) else []))
            if not notices:
                break
            for n in notices:
                title = extract_text(n.get("title") or n.get("noticeTitle"))
                cpv_code = extract_text(n.get("cpvCode") or n.get("cpv"))
                # v3: CPV exclusion gate
                if cpv_is_excluded(cpv_code):
                    continue
                cpv_desc = extract_text(n.get("cpvDescription"))
                desc = extract_text(n.get("description"))
                blob = " ".join([title, cpv_desc, desc])
                if not match_keywords(blob, KEYWORDS):
                    continue
                val = n.get("estimatedValue", n.get("value", ""))
                results.append({
                    "Source": "🇳🇴 Norway",
                    "Source Notice ID": str(n.get("id", "")),
                    "Lifecycle": classify_lifecycle(blob, extract_text(n.get("noticeType"))),
                    "Notice Type": extract_text(n.get("noticeType")),
                    "Procedure Type": extract_text(n.get("procedureType")),
                    "Buyer Type": "",
                    "Score": score_legacy(title, parse_number(val)),
                    "FleetSize": extract_fleet_size(title),
                    "Title": title,
                    "Buyer": extract_text(n.get("contractingAuthority") or n.get("buyer")),
                    "CPV Code": cpv_code,
                    "CPV Desc": cpv_desc,
                    "Description": desc,
                    "Est. Value": val,
                    "Currency": "NOK",
                    "Published": extract_text(n.get("publishedDate") or n.get("publicationDate")),
                    "Deadline": extract_text(n.get("deadline") or n.get("submissionDeadline")),
                    "Country": "Norway",
                    "Country Code": "NOR",
                    "URL": extract_text(n.get("url") or n.get("noticeUrl") or f"https://www.doffin.no/notices/{n.get('id','')}"),
                })
            if len(notices) < limit:
                break
            page += 1
            time.sleep(0.5)
        except Exception as exc:
            print(f"  [Doffin] Exception on page {page}: {exc}")
            break
    print(f"[Doffin] Total: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# HILMA (unchanged logic, uses v3 exclusion gate)
# ---------------------------------------------------------------------------

def fetch_hilma(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    if not HILMA_API_KEY:
        print("\n[HILMA] No API key set — skipping.")
        return []

    print("\n[HILMA] Fetching from HILMA (Finland)...")
    base_url = "https://hns-hilma-prod-apim.azure-api.net/avp/hilmatenders/"
    headers = {"Ocp-Apim-Subscription-Key": HILMA_API_KEY}
    params = {
        "CPV": ";".join(CPV_CODES),
        "publishedFrom": from_dt.strftime("%Y-%m-%d"),
    }
    try:
        resp = session.get(base_url, headers=headers, params=params, timeout=30)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 401:
            print("  [HILMA] Invalid API key.")
            return []
        if resp.status_code != 200:
            print(f"  [HILMA] Error: {resp.text[:300]}")
            return []
        data = resp.json()
        notices = data if isinstance(data, list) else data.get("tenders", data.get("notices", []))
        print(f"[HILMA] Got {len(notices)} notices")
        results: List[Dict[str, Any]] = []
        for n in notices:
            title = extract_text(n.get("name") or n.get("title"))
            cpv_code = extract_text(n.get("cpv"))
            if cpv_is_excluded(cpv_code):
                continue
            desc = extract_text(n.get("description"))
            blob = " ".join([title, desc])
            if not match_keywords(blob, KEYWORDS):
                continue
            results.append({
                "Source": "🇫🇮 Finland",
                "Source Notice ID": str(n.get("id", "")),
                "Lifecycle": classify_lifecycle(blob, extract_text(n.get("noticeType"))),
                "Notice Type": extract_text(n.get("noticeType")),
                "Procedure Type": extract_text(n.get("procedureType")),
                "Buyer Type": "",
                "Score": score_legacy(title),
                "FleetSize": extract_fleet_size(title),
                "Title": title,
                "Buyer": extract_text(n.get("organisation") or n.get("organization")),
                "CPV Code": cpv_code,
                "CPV Desc": "",
                "Description": desc,
                "Est. Value": "",
                "Currency": "EUR",
                "Published": extract_text(n.get("entrydate") or n.get("publishedDate")),
                "Deadline": extract_text(n.get("tenderdate") or n.get("deadline")),
                "Country": "Finland",
                "Country Code": "FIN",
                "URL": extract_text(n.get("url")),
            })
        print(f"[HILMA] Matches: {len(results)}")
        return results
    except Exception as exc:
        print(f"[HILMA] Error: {exc}")
        return []


# ---------------------------------------------------------------------------
# Contracts Finder UK (second UK source — lower-value contracts not on FaT)
# ---------------------------------------------------------------------------
# Free REST API, no key required. Covers contracts typically £10k–£100k:
# fleet maintenance for smaller councils, police forces, NHS trusts, etc.
# API docs: https://www.contractsfinder.service.gov.uk/apidocumentation

CF_SEARCH_TERMS = [
    "vehicle maintenance", "fleet maintenance", "vehicle repair", "fleet repair",
    "repair and maintenance", "vehicle service", "fleet management",
    "pickup", "van maintenance", "truck maintenance", "commercial vehicle",
    "light commercial", "LCV", "fleet contract", "isuzu",
]

def fetch_contracts_finder(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    # OCDS Search API (the old PublicSearch/Search POST endpoint was retired → 404).
    # GET /Published/Notices/OCDS/Search returns OCDS releases; cursor-paginated via links.next.
    print("\n[CF] Fetching from Contracts Finder (UK lower-value, OCDS API)...")
    base_url = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"
    results: List[Dict[str, Any]] = []
    seen_ids: set = set()
    published_from = from_dt.strftime("%Y-%m-%d")

    for term in CF_SEARCH_TERMS[:8]:  # top 8 terms cover ~90% of targets
        url = base_url
        params = {"publishedFrom": published_from, "keyword": term, "limit": 100}
        added = 0
        pages = 0
        try:
            while url and pages < 5:  # cap pagination per term
                resp = session.get(url, params=params if pages == 0 else None,
                                    timeout=30, headers={"Accept": "application/json"})
                # CF OCDS API is rate-limited — back off and retry on 429.
                retries = 0
                while resp.status_code == 429 and retries < 4:
                    wait = int(resp.headers.get("Retry-After", 0) or 0) or (5 * (retries + 1))
                    print(f"  [CF] '{term}': 429 rate-limited — waiting {wait}s")
                    time.sleep(wait)
                    resp = session.get(url, params=params if pages == 0 else None,
                                       timeout=30, headers={"Accept": "application/json"})
                    retries += 1
                if resp.status_code != 200:
                    print(f"  [CF] '{term}': HTTP {resp.status_code}")
                    break
                data = resp.json()
                releases = data.get("releases", [])
                if not releases:
                    break
                for rel in releases:
                    nid = str(rel.get("id") or rel.get("ocid") or "")
                    if not nid or nid in seen_ids:
                        continue
                    seen_ids.add(nid)
                    tender = rel.get("tender", {}) or {}
                    title = extract_text(tender.get("title") or "")
                    desc = extract_text(tender.get("description") or "")
                    blob = f"{title} {desc}".lower()
                    if not match_keywords(blob, KEYWORDS):
                        continue
                    buyer = extract_text((rel.get("buyer") or {}).get("name") or "")
                    cls = tender.get("classification") or {}
                    cpv_code = extract_text(cls.get("id") or "")
                    cpv_desc = extract_text(cls.get("description") or "")
                    val_obj = tender.get("value") or {}
                    val = val_obj.get("amount") or ""
                    deadline = extract_text((tender.get("tenderPeriod") or {}).get("endDate") or "")
                    notice_type = extract_text(
                        tender.get("status") or tender.get("procurementMethodDetails") or ""
                    )
                    results.append({
                        "Source": "🇬🇧 UK-CF",
                        "Source Notice ID": nid,
                        "Lifecycle": classify_lifecycle(blob, notice_type),
                        "Notice Type": notice_type,
                        "Procedure Type": extract_text(tender.get("procurementMethodDetails") or ""),
                        "Buyer Type": extract_text(tender.get("mainProcurementCategory") or ""),
                        "Score": score_legacy(title, parse_number(val)),
                        "FleetSize": extract_fleet_size(title),
                        "Title": title,
                        "Buyer": buyer,
                        "CPV Code": cpv_code,
                        "CPV Desc": cpv_desc,
                        "Description": desc[:500],
                        "Est. Value": val,
                        "Currency": extract_text(val_obj.get("currency") or "GBP"),
                        "Published": extract_text(rel.get("date") or ""),
                        "Deadline": deadline,
                        "Country": "United Kingdom",
                        "Country Code": "GBR",
                        "URL": f"https://www.contractsfinder.service.gov.uk/notice/{rel.get('id', nid)}",
                    })
                    added += 1
                url = (data.get("links") or {}).get("next")
                pages += 1
                time.sleep(1.0)
            if added:
                print(f"  [CF] '{term}': {added} new matches")
            time.sleep(1.5)  # pace between search terms to avoid 429
        except Exception as exc:
            print(f"  [CF] '{term}': exception — {exc}")
            continue

    print(f"[CF] Total unique matches: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# Germany national portals (below EU threshold)
# ---------------------------------------------------------------------------
# Germany routes most below-threshold fleet/vehicle tenders through national
# platforms, NOT TED. TED covers DEU above ~€215k — that's why we see only
# 4 German results vs 62 Romanian ones.
#
# DTVP (Deutsches Vergabeportal) is the largest German multi-state aggregator.
# CORRECTION (researched 2026-08-11, see manual_review_required.md 2026-08-09
# Item 5): DTVP does NOT offer a free/anonymous public RSS feed — the URL
# below 404s every run and, per dtvp.de's own tenderer pages, the automated
# e-mail notification service requires a paid "Professional Edition or
# higher" subscription (from EUR49/month); basic search is free but
# web-only, no feed. TED (DEU) still covers above-threshold German
# contracts. This is a real, structural gap for below-threshold DE
# coverage, not a URL typo — fixing it means either a paid DTVP
# subscription or manual portal registration, not a code change.
#
# Vergabe.NRW covers North-Rhine Westphalia (18M people), Germany's most
# populous state, via a public search interface.
# URL: https://www.vergabe.nrw.de
#
# Both are attempted; failures are logged and skipped gracefully.
# ---------------------------------------------------------------------------

GERMANY_SEARCH_TERMS_DE = [
    "fahrzeugwartung", "fuhrparkwartung", "fuhrpark", "nutzfahrzeuge",
    "fahrzeuginstandhaltung", "kfz-wartung", "fahrzeugreparatur",
    "flottenwartung", "flottenmanagement", "pickup", "pritschenwagen",
    "leichte nutzfahrzeuge", "lkw wartung", "fahrzeuginstandsetzung",
]

DTVP_RSS_URL = "https://www.dtvp.de/Center/company/public/procurement/rss"
NRW_SEARCH_URL = "https://www.vergabe.nrw.de/VMPSatellite/satellite.vm"
TENDERNED_RSS_URL = "https://www.tenderned.nl/papi/tenderned-rs-tns/rss/laatste-publicatie.rss"
# CORRECTION (researched 2026-08-11, see manual_review_required.md 2026-08-09
# Item 4): both candidates below return non-XML (HTML error/redirect) pages,
# not malformed XML — per BOSA's own e-Procurement documentation, Belgium's
# "e-Notification" module has never exposed a public/anonymous RSS feed.
# The only notification mechanism is a free personal account on
# publicprocurement.be with a CPV/region-based search profile, which sends
# daily results by e-mail — there is no URL fix available here, only an
# account-based alternative outside this script's scope. TED (BEL) still
# covers above-threshold Belgian contracts. Kept as a best-effort probe in
# case Belgium adds a public feed later; failures are cheap and logged.
BELGIUM_RSS_CANDIDATES = [
    "https://www.publicprocurement.be/supplier/feed/rss",
    "https://www.publicprocurement.be/en/rss",
]


def _parse_procurement_rss(
    content: str,
    *,
    source_label: str,
    country: str,
    country_code: str,
    currency: str = "EUR",
) -> List[Dict[str, Any]]:
    """Parse RSS/Atom XML → list of raw row dicts (shared by DE/BE/NL feeds)."""
    rows = []
    try:
        root = ET.fromstring(content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        # Try Atom feed first, fall back to RSS2
        items = root.findall(".//atom:entry", ns) or root.findall(".//item")
        for item in items:
            def _t(tag: str, default: str = "") -> str:
                el = item.find(tag) or item.find(f"atom:{tag}", ns)
                return (el.text or "").strip() if el is not None else default

            title = _t("title")
            description = _t("description") or _t("summary")
            published = _t("pubDate") or _t("atom:published", ns) or _t("published")
            link = _t("link")
            if not link:
                link_el = item.find("atom:link", ns)
                if link_el is not None:
                    link = link_el.get("href", "")

            blob = f"{title} {description}".lower()
            if not match_keywords(blob, KEYWORDS):
                continue

            # Check CPV if present in description
            cpv_raw = ""
            if "cpv" in blob or "34131" in blob or "50110" in blob:
                import re
                m = re.search(r"\b(3[0-9]{7}|5[0-9]{7})\b", description)
                if m:
                    cpv_raw = m.group(0)

            rows.append({
                "Source": source_label,
                "Source Notice ID": link.split("/")[-1] if link else title[:40],
                "Lifecycle": classify_lifecycle(blob, ""),
                "Notice Type": "",
                "Procedure Type": "",
                "Buyer Type": "",
                "Score": score_legacy(title, None),
                "FleetSize": extract_fleet_size(title),
                "Title": title,
                "Buyer": "",
                "CPV Code": cpv_raw,
                "CPV Desc": "",
                "Description": description[:500],
                "Est. Value": "",
                "Currency": currency,
                "Published": published,
                "Deadline": "",
                "Country": country,
                "Country Code": country_code,
                "URL": link,
            })
    except ET.ParseError as e:
        print(f"  [{country_code}] RSS parse error: {e}")
    return rows


def _parse_dtvp_rss(content: str) -> List[Dict[str, Any]]:
    return _parse_procurement_rss(
        content,
        source_label="🇩🇪 DE",
        country="Germany",
        country_code="DEU",
    )


def fetch_netherlands(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    """TenderNed latest publications RSS (Netherlands)."""
    print("\n[NL] Fetching from TenderNed RSS...")
    try:
        resp = session.get(
            TENDERNED_RSS_URL,
            timeout=25,
            headers={"Accept": "application/rss+xml, application/atom+xml, */*"},
        )
        if resp.status_code != 200:
            print(f"  [NL] HTTP {resp.status_code}")
            return []
        rows = _parse_procurement_rss(
            resp.text,
            source_label="🇳🇱 NL",
            country="Netherlands",
            country_code="NLD",
        )
        print(f"[NL] TenderNed: {len(rows)} keyword matches")
        return rows
    except Exception as exc:
        print(f"  [NL] failed: {exc}")
        return []


def fetch_belgium(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    """Belgium federal / e-Procurement RSS (best-effort)."""
    print("\n[BE] Fetching from Belgium procurement RSS...")
    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for url in BELGIUM_RSS_CANDIDATES:
        try:
            resp = session.get(url, timeout=20, headers={"Accept": "application/rss+xml, */*"})
            if resp.status_code != 200:
                print(f"  [BE] {url}: HTTP {resp.status_code}")
                continue
            rows = _parse_procurement_rss(
                resp.text,
                source_label="🇧🇪 BE",
                country="Belgium",
                country_code="BEL",
            )
            for row in rows:
                uid = row.get("URL") or row.get("Title", "")
                if uid and uid not in seen:
                    seen.add(uid)
                    results.append(row)
            print(f"  [BE] {url}: {len(rows)} matches")
        except Exception as exc:
            print(f"  [BE] {url}: {exc}")
    print(f"[BE] Total Belgium RSS: {len(results)}")
    if not results:
        print("[BE] Note: TED (BEL) still covers above-threshold BE contracts.")
    return results


def fetch_germany(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    """Scrape German national procurement portals for below-threshold vehicle tenders."""
    print("\n[DE] Fetching from Germany national portals (DTVP)...")
    results: List[Dict[str, Any]] = []
    seen_ids: set = set()

    # --- DTVP RSS ---
    try:
        resp = session.get(DTVP_RSS_URL, timeout=20, headers={"Accept": "application/rss+xml, application/atom+xml, */*"})
        if resp.status_code == 200:
            rows = _parse_dtvp_rss(resp.text)
            for r in rows:
                uid = r.get("Source Notice ID", "") or r.get("URL", "")
                if uid and uid not in seen_ids:
                    seen_ids.add(uid)
                    results.append(r)
            print(f"  [DE] DTVP RSS: {len(rows)} matches")
        else:
            print(f"  [DE] DTVP RSS: HTTP {resp.status_code} — portal may require browser access")
    except Exception as e:
        print(f"  [DE] DTVP RSS: failed ({e})")
        print(f"  [DE] Note: DTVP and German state portals often require browser access.")
        print(f"  [DE] TED (DEU) already covers above-threshold DE contracts (≥€215k).")
        print(f"  [DE] For below-threshold: consider requesting DTVP API access at dtvp.de")

    # --- NRW keyword search (HTML fallback, best-effort) ---
    # NRW publishes a public tender search — we try one keyword and parse results
    try:
        params = {
            "METHOD": "searchPublicProcurement",
            "SEARCHRESULT.ORDERBY": "DATEMODIFIED",
            "searchCriteria.freetext": "Fahrzeug",
            "searchCriteria.publicationDateFrom": from_dt.strftime("%d.%m.%Y"),
        }
        resp2 = session.get(NRW_SEARCH_URL, params=params, timeout=20)
        if resp2.status_code == 200 and "Fahrzeug" in resp2.text:
            # HTML parse is fragile; just log the count for now
            import re
            titles = re.findall(r'<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>', resp2.text)
            matched = [t.strip() for t in titles if match_keywords(t.lower(), KEYWORDS)]
            if matched:
                print(f"  [DE] NRW portal: {len(matched)} possible matches — manual review recommended")
                print(f"  [DE] NRW URL: {NRW_SEARCH_URL}")
        else:
            print(f"  [DE] NRW portal: HTTP {resp2.status_code} — skipping")
    except Exception as e:
        print(f"  [DE] NRW portal: failed ({e}) — skipping")

    print(f"[DE] Total Germany national results: {len(results)}")
    if not results:
        print(f"[DE] Coverage note: TED (DEU) covers above-threshold German contracts.")
        print(f"[DE] Below-threshold German tenders need portal registration (DTVP, Vergabe.NRW, Bavaria).")
    return results

def save_to_excel(
    uk_rows: List[Dict[str, Any]],
    il_rows: List[Dict[str, Any]],
    ted_rows: List[Dict[str, Any]],
    doffin_rows: List[Dict[str, Any]],
    hilma_rows: List[Dict[str, Any]],
    cf_rows: List[Dict[str, Any]],
    de_rows: List[Dict[str, Any]],
    be_rows: List[Dict[str, Any]],
    nl_rows: List[Dict[str, Any]],
    filename: str,
) -> None:
    wb = openpyxl.Workbook()

    def write_sheet(ws, rows: List[Dict[str, Any]], empty_msg: str) -> None:
        ws.append(EXPORT_HEADERS)
        if rows:
            for row in rows:
                ws.append([row.get(h, "") for h in EXPORT_HEADERS])
        else:
            ws.append([empty_msg])

    ws_uk = wb.active
    ws_uk.title = "UK Tenders"
    write_sheet(ws_uk, normalize_batch(uk_rows, "🇬🇧 UK"), "No UK results found")

    ws_cf = wb.create_sheet("UK Contracts Finder")
    write_sheet(ws_cf, normalize_batch(cf_rows, "🇬🇧 UK-CF"), "No Contracts Finder results — check API availability")

    ws_ted = wb.create_sheet("EU TED Tenders")
    write_sheet(ws_ted, normalize_batch(ted_rows, "🇪🇺 EU"), "No TED results found")

    ws_de = wb.create_sheet("Germany National")
    write_sheet(ws_de, normalize_batch(de_rows, "🇩🇪 DE"), "No DE national results — DTVP portal may require browser access. TED covers DE above-threshold contracts.")

    ws_doffin = wb.create_sheet("Norway Doffin")
    write_sheet(ws_doffin, normalize_batch(doffin_rows, "🇳🇴 Norway"), "No results — add DOFFIN_API_KEY (free) at top of script")

    ws_hilma = wb.create_sheet("Finland HILMA")
    write_sheet(ws_hilma, normalize_batch(hilma_rows, "🇫🇮 Finland"), "No results — add HILMA_API_KEY (free) at top of script")

    ws_il = wb.create_sheet("Israel Tenders")
    write_sheet(ws_il, normalize_batch(il_rows, "🇮🇱 Israel"), "No Israel results found")

    ws_be = wb.create_sheet("Belgium")
    write_sheet(ws_be, normalize_batch(be_rows, "🇧🇪 BE"), "No Belgium RSS results — TED covers above-threshold BE")

    ws_nl = wb.create_sheet("Netherlands")
    write_sheet(ws_nl, normalize_batch(nl_rows, "🇳🇱 NL"), "No TenderNed RSS results — check tenderned.nl feed")

    wb.save(filename)
    print(f"\n✓ Saved: {filename}")
    print(f"  UK (Find a Tender): {len(uk_rows)}")
    print(f"  UK (Contracts Finder): {len(cf_rows)}")
    print(f"  TED EU:   {len(ted_rows)}")
    print(f"  Germany:  {len(de_rows)} (national portals) + included in TED above-threshold")
    print(f"  Norway:   {len(doffin_rows)}")
    print(f"  Finland:  {len(hilma_rows)}")
    print(f"  Israel:   {len(il_rows)}")
    print(f"  Belgium:  {len(be_rows)}")
    print(f"  Netherlands: {len(nl_rows)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  ISZE TENDER MONITOR v3")
    print(f"  Last {LOOKBACK_DAYS} days | Markets: UK, EU/TED, DE, BE, NL, Norway, Finland, Israel")
    print(f"  CPV codes: {len(CPV_CODES)} (surgical — ISZE targets only)")
    print(f"  TED country filter: {len(TED_TARGET_COUNTRIES)} markets")
    print(f"  TED detail fetch: {'ON' if TED_FETCH_DETAIL else 'OFF'}")
    print("=" * 60)

    now = datetime.now(timezone.utc)
    from_dt = now - timedelta(days=LOOKBACK_DAYS)

    with requests.Session() as session:
        uk_rows = fetch_uk(session, from_dt, now)
        cf_rows = fetch_contracts_finder(session, from_dt)
        ted_rows = fetch_ted(session, from_dt)
        de_rows = fetch_germany(session, from_dt)
        be_rows = fetch_belgium(session, from_dt)
        nl_rows = fetch_netherlands(session, from_dt)
        doffin_rows = fetch_doffin(session, from_dt)
        hilma_rows = fetch_hilma(session, from_dt)
        il_rows = fetch_israel(session)

    save_to_excel(
        uk_rows, il_rows, ted_rows, doffin_rows, hilma_rows, cf_rows, de_rows, be_rows, nl_rows, OUTPUT_FILE
    )
    print("\nDone.")
    print("=" * 60)


if __name__ == "__main__":
    main()
