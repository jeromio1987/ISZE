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

import argparse
import ast
import csv
import io
import json
import os
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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
    row_passes_isuzu_selection_gate,
    score_legacy,
)
from source_health import (
    load_health,
    persist_and_report,
    record_source_result,
    record_source_status,
    validate_feed,
)

LOOKBACK_DAYS = 30
_SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = str(_SCRIPT_DIR / "isuzu_tenders_v3.xlsx")
UK_STAGES = "planning,tender,award"

# Last-error bag for honest source_health (fetchers stay list-returning).
LAST_FETCH_ERRORS: Dict[str, Optional[str]] = {}


def _load_local_env() -> None:
    """Load Install-folder secrets into os.environ without overwriting existing vars.

    Looks for (first hit wins per key): ``nordics_api_keys.env``, ``isze_secrets.env``,
    ``.env.local``, ``.env``. Never commit those files — see ``nordics_api_keys.env.example``.
    """
    for name in ("nordics_api_keys.env", "isze_secrets.env", ".env.local", ".env"):
        path = _SCRIPT_DIR / name
        if not path.is_file():
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
        except OSError:
            continue


_load_local_env()
from nordics_keys import (
    DOFFIN_SEARCH_URL,
    HILMA_NOTICES_URL,
    get_doffin_key,
    get_hilma_key,
    missing_key_banner,
)

# v3: TED detail enrichment (fleet / deadline / value on matched notices).
# Default OFF so weekly bat does not hammer TED. Enable with:
#   set ISZE_TED_FETCH_DETAIL=1
# Cap keeps CF/TED rate-limit safe (batch of gated/matched IDs only).
#   set ISZE_TED_DETAIL_CAP=40
def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


TED_FETCH_DETAIL = _env_bool("ISZE_TED_FETCH_DETAIL", False)
try:
    TED_DETAIL_CAP = max(0, int(os.environ.get("ISZE_TED_DETAIL_CAP") or "40"))
except ValueError:
    TED_DETAIL_CAP = 40
# Delay between TED detail calls — stay well under ~3 req/sec public guidance.
TED_DETAIL_DELAY = float(os.environ.get("ISZE_TED_DETAIL_DELAY") or "0.5")

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
    "50114000",  # Repair and maintenance services of trucks (Phase 1 widen)
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
    "CYP", "MLT",  # Phase 1: EU members previously omitted — above-threshold via TED
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
    "Suggested Next Action", "Aftersales Tags", "Aftersales Summary", "R&M Contract",
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
        "Aftersales Tags": ", ".join(row.get("aftersales_tags") or []),
        "Aftersales Summary": row.get("aftersales_summary") or "",
        "R&M Contract": "YES" if row.get("rm_contract") else "",
    }


def normalize_batch(rows: List[Dict[str, Any]], source_label: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        row.setdefault("Source", source_label)
        # v3: skip before scoring if CPV is in exclusion list
        cpv = str(row.get("CPV Code", "") or "")
        if cpv_is_excluded(cpv):
            continue
        # v4: Isuzu commercial gate (LCV / core CPV; drop SEND/passenger/transport noise)
        if not row_passes_isuzu_selection_gate(row):
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
        if resp.status_code == 400 and "Authorization" in (resp.text or ""):
            print(
                f"    [TED detail] {notice_id}: HTTP 400 — detail endpoint needs Authorization "
                f"(list search stays public). Set TED API key before enabling ISZE_TED_FETCH_DETAIL."
            )
            return {}
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
        results.append(row)

    # Detail enrichment AFTER list filter — capped batch only (never every TED hit).
    # Prefer rows missing deadline / value / fleet so the cap spends on sizing quality.
    detail_attempted = 0
    detail_ok = 0
    if TED_FETCH_DETAIL and TED_DETAIL_CAP > 0 and results:
        need = []
        have = []
        for r in results:
            if not r.get("Source Notice ID"):
                continue
            thin = (not r.get("Deadline")) or (not r.get("Est. Value")) or (not r.get("FleetSize"))
            (need if thin else have).append(r)
        enrich_queue = (need + have)[:TED_DETAIL_CAP]
        print(
            f"  [TED detail] ON — enriching {len(enrich_queue)}/{len(results)} "
            f"matched (cap={TED_DETAIL_CAP}, delay={TED_DETAIL_DELAY}s)"
        )
        for r in enrich_queue:
            notice_id = str(r.get("Source Notice ID") or "")
            detail_attempted += 1
            detail = fetch_ted_detail(session, notice_id)
            if detail:
                detail_ok += 1
                for field, val in detail.items():
                    if val and not r.get(field):
                        r[field] = val
                # Re-run fleet extract on description if title had none
                if not r.get("FleetSize") and r.get("Description"):
                    fs = extract_fleet_size(str(r.get("Description") or ""))
                    if fs:
                        r["FleetSize"] = fs
            time.sleep(TED_DETAIL_DELAY)

    got_deadline = sum(1 for r in results if r.get("Deadline"))
    got_value = sum(1 for r in results if r.get("Est. Value"))
    got_fleet = sum(1 for r in results if r.get("FleetSize"))
    print(f"[TED] Keyword matches: {len(results)}")
    print(f"  Excluded by CPV gate:   {excluded_cpv}")
    print(f"  Excluded by keyword:    {keyword_misses}")
    print(
        f"  Detail fetch: attempted={detail_attempted} ok={detail_ok} "
        f"(cap={TED_DETAIL_CAP if TED_FETCH_DETAIL else 0})"
    )
    print(
        f"  After list(+detail): deadline={got_deadline}/{len(results)} "
        f"({100 * got_deadline // max(len(results), 1)}%) | "
        f"value={got_value}/{len(results)} ({100 * got_value // max(len(results), 1)}%) | "
        f"fleet={got_fleet}/{len(results)} ({100 * got_fleet // max(len(results), 1)}%)"
    )
    if got_deadline == 0 and len(results) > 0 and TED_FETCH_DETAIL and detail_attempted:
        print("  ⚠ Zero deadlines retrieved — TED API structure may have changed.")
        print("  ⚠ Check the diagnostic output above for 'top-level keys' to update _ted_detail_fields().")
    return results


# ---------------------------------------------------------------------------
# Israel — live mr.gov.il (RSS dead; CKAN frozen Feb 2021 = secondary only)
# ---------------------------------------------------------------------------

ISRAEL_AC_URL = "https://mr.gov.il/ilgstorefront/he/search/autocomplete/SearchBox"
ISRAEL_HTML_SEARCH_URL = "https://mr.gov.il/ilgstorefront/he/search/"
ISRAEL_BASE = "https://mr.gov.il/ilgstorefront/he"
ISRAEL_DATASTORE_RESOURCE = "7038b3e6-a74d-442e-b16b-466c8196124a"
ISRAEL_DATASTORE_URL = "https://data.gov.il/api/3/action/datastore_search"
# Prefer short distinct Hebrew vehicle / R&M terms (autocomplete is term-scoped).
ISRAEL_LIVE_TERMS = ["רכב", "טנדר", "משאית", "תחזוקה", "צי רכב", "רכב מסחרי"]
ISRAEL_SEARCH_TERMS = ISRAEL_LIVE_TERMS + KEYWORDS_HE  # CKAN secondary only


def _parse_il_date(raw: str) -> str:
    """Convert IL date strings (DD.MM.YYYY / DD/MM/YYYY[ HH:MM]) to ISO date; empty if unparseable."""
    text = (raw or "").strip()
    if not text:
        return ""
    # Drop trailing time for date-only ISO; keep parseable.
    for fmt in ("%d.%m.%Y %H:%M", "%d/%m/%Y %H:%M", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:16].strip(), fmt).date().isoformat()
        except ValueError:
            continue
    # Fallback: first 10 chars as DD.MM.YYYY / DD/MM/YYYY
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def _il_notice_row(
    *,
    nid: str,
    title: str,
    url: str,
    deadline: str = "",
    published: str = "",
    buyer: str = "",
    status: str = "",
    description: str = "",
) -> Dict[str, Any]:
    return {
        "Source": "🇮🇱 Israel",
        "Source Notice ID": nid,
        "Lifecycle": classify_lifecycle(title, status),
        "Notice Type": "",
        "Procedure Type": "",
        "Buyer Type": "",
        "Score": score_legacy(title),
        "FleetSize": extract_fleet_size(title),
        "Title": title,
        "Buyer": buyer,
        "CPV Code": "",
        "CPV Desc": "",
        "Description": description or title,
        "Est. Value": "",
        "Currency": "ILS",
        "Published": published,
        "Deadline": deadline,
        "Country": "Israel",
        "Country Code": "ISR",
        "URL": url,
    }


def _fetch_israel_autocomplete(session: requests.Session, seen: set) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Primary live source: mr.gov.il SearchBox JSON."""
    rows: List[Dict[str, Any]] = []
    last_err: Optional[str] = None
    ok_once = False
    for term in ISRAEL_LIVE_TERMS:
        try:
            resp = session.get(ISRAEL_AC_URL, params={"term": term}, timeout=30)
            err = validate_feed("Israel AC", resp, expect_feed=False, expect_json=True, min_bytes=20)
            if err:
                last_err = err
                print(f"  [IL] AC '{term}': BROKEN — {err}")
                continue
            if resp.status_code != 200:
                last_err = f"HTTP {resp.status_code}"
                print(f"  [IL] AC '{term}': HTTP {resp.status_code}")
                continue
            ok_once = True
            products = (resp.json() or {}).get("products") or []
            added = 0
            for p in products:
                title = extract_text(p.get("publishmentName") or "")
                if not title:
                    continue
                if not match_keywords(title, KEYWORDS + KEYWORDS_HE):
                    continue
                path = str(p.get("url") or "")
                if not path:
                    continue
                if path.startswith("http"):
                    url = path
                else:
                    url = ISRAEL_BASE + (path if path.startswith("/") else "/" + path)
                nid = path.rstrip("/").split("/")[-1] or str(p.get("processNumber") or url)
                if nid in seen:
                    continue
                seen.add(nid)
                deadline = _parse_il_date(str(p.get("submittingDate") or ""))
                published = _parse_il_date(str(p.get("firstNewspaperPublicationDay") or ""))
                buyer = extract_text(p.get("officeName") or "")
                status = extract_text(p.get("status") or "")
                rows.append(
                    _il_notice_row(
                        nid=nid,
                        title=title,
                        url=url,
                        deadline=deadline,
                        published=published,
                        buyer=buyer,
                        status=status,
                        description=extract_text(p.get("processNumber") or ""),
                    )
                )
                added += 1
            print(f"  [IL] AC '{term}': {added} new (products={len(products)})")
            time.sleep(0.25)
        except Exception as exc:
            last_err = str(exc)
            print(f"  [IL] AC '{term}': {exc}")
    if not ok_once and last_err:
        return rows, last_err
    return rows, None


def _fetch_israel_html(session: requests.Session, seen: set) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Broader live listing via server-rendered .result-container cards."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return [], "bs4 not installed — HTML scrape skipped"

    rows: List[Dict[str, Any]] = []
    last_err: Optional[str] = None
    # One page of tender results + one vehicle-keyword page.
    urls = [
        f"{ISRAEL_HTML_SEARCH_URL}?s=TENDER",
        f"{ISRAEL_HTML_SEARCH_URL}?s=TENDER&q=%D7%A8%D7%9B%D7%91",  # רכב
    ]
    for url in urls:
        try:
            resp = session.get(url, timeout=60)
            if resp.status_code != 200:
                last_err = f"HTTP {resp.status_code}"
                print(f"  [IL] HTML {url}: HTTP {resp.status_code}")
                continue
            body = resp.content or b""
            if len(body) < 500 or b"<html" not in body[:2000].lower() and b"<!doctype" not in body[:2000].lower():
                # Still try parse — some responses are large HTML without early doctype match
                pass
            soup = BeautifulSoup(resp.text, "html.parser")
            boxes = soup.select(".result-container")
            if not boxes:
                last_err = "no .result-container cards"
                print(f"  [IL] HTML: no result cards")
                continue
            added = 0
            for box in boxes:
                a = box.select_one("a[href*='/p/']")
                if not a:
                    continue
                title = extract_text(a.get_text(" ", strip=True))
                if not title or not match_keywords(title, KEYWORDS + KEYWORDS_HE):
                    continue
                href = a.get("href") or ""
                if href.startswith("/"):
                    link = "https://mr.gov.il" + href
                elif href.startswith("http"):
                    link = href
                else:
                    link = ISRAEL_BASE + "/" + href.lstrip("/")
                nid = href.rstrip("/").split("/")[-1] or link
                if nid in seen:
                    continue
                text = box.get_text(" ", strip=True)
                deadline = ""
                m = re.search(
                    r"מועד אחרון להגשה:\s*([0-9]{1,2}[./][0-9]{1,2}[./][0-9]{2,4}(?:\s+[0-9:]+)?)",
                    text,
                )
                if m:
                    deadline = _parse_il_date(m.group(1))
                buyer = ""
                m2 = re.search(r"שם המפרסם:\s*([^\n|]+)", text)
                if m2:
                    buyer = extract_text(m2.group(1))
                status_el = box.select_one("span.status")
                status = extract_text(status_el.get_text(" ", strip=True) if status_el else "")
                seen.add(nid)
                rows.append(
                    _il_notice_row(
                        nid=nid,
                        title=title,
                        url=link,
                        deadline=deadline,
                        buyer=buyer,
                        status=status,
                    )
                )
                added += 1
            print(f"  [IL] HTML: {added} keyword matches ({len(boxes)} cards)")
            time.sleep(0.4)
        except Exception as exc:
            last_err = str(exc)
            print(f"  [IL] HTML: {exc}")
    return rows, last_err if not rows else None


def _fetch_israel_ckan_secondary(session: requests.Session, seen: set) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Frozen Feb 2021 datastore — only when live sources yield nothing."""
    print("  [IL] CKAN secondary (data.gov.il — frozen ~2021) …")
    results: List[Dict[str, Any]] = []
    pub_floor = datetime.now(timezone.utc) - timedelta(days=365)
    today = datetime.now(timezone.utc).date()
    probe = get_with_retry(
        session,
        ISRAEL_DATASTORE_URL,
        params={"resource_id": ISRAEL_DATASTORE_RESOURCE, "limit": 1},
    )
    health_error = validate_feed("Israel CKAN", probe, expect_feed=False, expect_json=True, min_bytes=50)
    if health_error:
        print(f"  [IL] CKAN BROKEN: {health_error}")
        return results, health_error

    for term in ISRAEL_SEARCH_TERMS:
        try:
            resp = session.get(
                ISRAEL_DATASTORE_URL,
                params={"resource_id": ISRAEL_DATASTORE_RESOURCE, "q": term, "limit": 100},
                timeout=45,
            )
            if resp.status_code != 200:
                continue
            records = (resp.json().get("result") or {}).get("records") or []
            added = 0
            for rec in records:
                title = extract_text(rec.get("שם הליך") or rec.get("title") or "")
                if not title:
                    continue
                pub = _parse_il_date(str(rec.get("תאריך פרסום") or ""))
                deadline = _parse_il_date(str(rec.get("תאריך אחרון להגשת השגות") or ""))
                status = extract_text(rec.get("סטטוס") or "")
                keep = False
                try:
                    if pub:
                        pub_dt = datetime.fromisoformat(pub).replace(tzinfo=timezone.utc)
                        if pub_dt >= pub_floor:
                            keep = True
                    if deadline:
                        dl = datetime.fromisoformat(deadline).date()
                        if dl >= today:
                            keep = True
                except Exception:
                    keep = bool(pub or deadline)
                if status in ("פורסם", "פתוח", "פתוחה", "בתוקף"):
                    keep = True
                if not keep:
                    continue
                nid = str(rec.get("מספר פרסום") or rec.get("_id") or "")
                if not nid or nid in seen:
                    continue
                if not match_keywords(title, KEYWORDS + KEYWORDS_HE):
                    continue
                seen.add(nid)
                buyer = extract_text(rec.get("שם המשרד") or "")
                unit = extract_text(rec.get("שם יחידה מפרסמת") or "")
                results.append(
                    _il_notice_row(
                        nid=nid,
                        title=title,
                        url=f"https://mr.gov.il/ilgstorefront/he/search/?q={nid}",
                        deadline=deadline,
                        published=pub,
                        buyer=" / ".join(x for x in [buyer, unit] if x),
                        status=status,
                        description=extract_text(rec.get("נושאים") or ""),
                    )
                )
                added += 1
            if added:
                print(f"  [IL] CKAN '{term}': {added} new")
            time.sleep(0.25)
        except Exception as exc:
            print(f"  [IL] CKAN '{term}': {exc}")
            continue
    return results, None if results else "CKAN secondary returned 0 in-window matches (datastore frozen ~2021)"


def fetch_israel(session: requests.Session) -> List[Dict[str, Any]]:
    """Live Israel tenders via mr.gov.il autocomplete (+ HTML); CKAN only if live fails."""
    print("\n[IL] Fetching Israel tenders via mr.gov.il (live)…")
    results: List[Dict[str, Any]] = []
    seen: set = set()
    live_err: Optional[str] = None

    ac_rows, ac_err = _fetch_israel_autocomplete(session, seen)
    results.extend(ac_rows)
    html_rows, html_err = _fetch_israel_html(session, seen)
    results.extend(html_rows)

    if results:
        live_err = None
        print(f"[IL] Live matches: {len(results)} (AC={len(ac_rows)}, HTML={len(html_rows)})")
        LAST_FETCH_ERRORS["Israel mr.gov.il"] = None
        LAST_FETCH_ERRORS["Israel data.gov.il"] = "demoted — live mr.gov.il succeeded; CKAN frozen Feb 2021"
        LAST_FETCH_ERRORS["Israel RSS"] = "RETIRED — HTML SPA shell, 0 <item>; live = Israel mr.gov.il"
        return results

    live_err = ac_err or html_err or "live sources returned 0"
    print(f"[IL] Live returned 0 — falling back to CKAN secondary ({live_err})")
    ckan_rows, ckan_err = _fetch_israel_ckan_secondary(session, seen)
    results.extend(ckan_rows)
    if results:
        LAST_FETCH_ERRORS["Israel mr.gov.il"] = live_err
        LAST_FETCH_ERRORS["Israel data.gov.il"] = None
    else:
        LAST_FETCH_ERRORS["Israel mr.gov.il"] = live_err
        LAST_FETCH_ERRORS["Israel data.gov.il"] = ckan_err or "zero matches"
    LAST_FETCH_ERRORS["Israel RSS"] = "RETIRED — HTML SPA shell, 0 <item>; live = Israel mr.gov.il"
    print(f"[IL] Matches: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# IEC Israel — Electric Company (חברת החשמל)
# Domestic supplier tenders: iec.co.il (GEO_BLOCKED from abroad).
# International list: global-iec.com/activeTenders.html (HTML, no public RSS/API).
# ---------------------------------------------------------------------------

IEC_DOMESTIC_URL = (
    "https://www.iec.co.il/content/suppliers/tenders-and-decisions/tenders/active-tenders"
)
IEC_GLOBAL_URL = "https://www.global-iec.com/activeTenders.html"
IEC_VEHICLE_TERMS = [
    # English vehicle / fleet (exclude bare maintenance/repair — industrial false positives)
    "vehicle",
    "van",
    "truck",
    "pickup",
    "pick-up",
    "4x4",
    "chassis cab",
    "fleet",
    "lcv",
    "goods vehicle",
    "commercial vehicle",
    "motor vehicle",
    "leasing",
    "automobile",
    "passenger car",
    "fleet vehicle",
    "isuzu",
    "d-max",
    "n-series",
    # Hebrew
    "רכב",
    "משאית",
    "טנדר",
    "כלי רכב",
    "רכב שטח",
    "רכב מסחרי",
    "צי רכבים",
    "צי רכב",
    "ליסינג",
    "מכונית",
    "מכוניות",
]


def _iec_geo_blocked(resp) -> bool:
    """True when IEC returns the abroad Access Denied / geo wall."""
    if resp is None:
        return False
    text = resp.text or ""
    low = text.lower()
    if "access denied" in low and ("iec" in low or "חברת החשמל" in text or "access-denied" in low):
        return True
    if "blocked from outside" in low or "חסום לגלישה מחו" in text:
        return True
    return False


def _probe_iec_domestic(session: requests.Session) -> str:
    """Return last_error string for domestic portal health (never invent notices)."""
    try:
        resp = session.get(IEC_DOMESTIC_URL, timeout=45, allow_redirects=True)
        if _iec_geo_blocked(resp):
            return (
                "GEO_BLOCKED — iec.co.il domestic supplier tenders (Access Denied from outside "
                "Israel). Vehicle / leasing packs live here, not on global-iec. Abroad pointer: "
                + IEC_GLOBAL_URL
            )
        if resp.status_code >= 400:
            return f"HTTP {resp.status_code} on domestic active-tenders"
        # Unexpected: page reachable from this IP — still no HTML list contract we trust yet
        return (
            f"domestic reachable (HTTP {resp.status_code}, {len(resp.content or b'')} bytes) "
            "but no public RSS/API; HTML scrape not wired for domestic SPA"
        )
    except Exception as exc:
        return f"domestic probe failed: {exc}"


def _parse_iec_global_items(html: str) -> List[Dict[str, Any]]:
    """Parse server-rendered .active-tenders-item cards on global-iec.com."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".active-tenders-item")
    rows: List[Dict[str, Any]] = []
    for item in items:
        title_el = item.select_one(".active-tenders-item-title, .active-tenders-item-info-title")
        title = extract_text(title_el.get_text(" ", strip=True) if title_el else "")
        desc_el = item.select_one(
            ".active-tenders-item-info-description-text, .active-tenders-item-info-description"
        )
        desc = extract_text(desc_el.get_text(" ", strip=True) if desc_el else "")
        blob = item.get_text(" ", strip=True)
        nid = ""
        m = re.search(r"Tender Number[:\s]*([A-Za-z0-9\-]+)", blob, re.I)
        if m:
            nid = m.group(1).strip()
        if not title:
            # First meaningful chunk before "Tender Number"
            pre = re.split(r"Tender Number", blob, maxsplit=1, flags=re.I)[0]
            title = extract_text(pre)[:240]
        pub = ""
        m = re.search(r"Publication date[:\s]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})", blob, re.I)
        if m:
            pub = _parse_il_date(m.group(1).replace("/", "."))
        deadline = ""
        m = re.search(
            r"Deadline for submission[:\s]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4}(?:\s+[0-9:]+)?)",
            blob,
            re.I,
        )
        if m:
            deadline = _parse_il_date(m.group(1).replace("/", "."))
        if not nid and not title:
            continue
        rows.append(
            {
                "nid": nid or title[:40],
                "title": title,
                "description": desc,
                "published": pub,
                "deadline": deadline,
                "blob": blob,
            }
        )
    return rows


def fetch_iec_israel(session: requests.Session) -> List[Dict[str, Any]]:
    """Fetch IEC international tenders; probe domestic geo wall. Vehicle-keyword survivors only."""
    print("\n[IEC] Electric Company of Israel — domestic probe + global-iec HTML…")
    domestic_err = _probe_iec_domestic(session)
    LAST_FETCH_ERRORS["IEC iec.co.il domestic"] = domestic_err
    print(f"  [IEC] domestic: {domestic_err[:120]}…")

    results: List[Dict[str, Any]] = []
    try:
        resp = session.get(IEC_GLOBAL_URL, timeout=60)
        if _iec_geo_blocked(resp):
            msg = "GEO_BLOCKED — global-iec activeTenders also denied from this IP"
            LAST_FETCH_ERRORS["IEC global-iec.com"] = msg
            print(f"  [IEC] global: {msg}")
            return results
        if resp.status_code != 200:
            msg = f"HTTP {resp.status_code}"
            LAST_FETCH_ERRORS["IEC global-iec.com"] = msg
            print(f"  [IEC] global: {msg}")
            return results
        # No RSS/API — guessed paths 403; this is HTML list only.
        if b"<rss" in (resp.content or b"")[:2000].lower():
            pass  # unexpected feed — still parse items below
        parsed = _parse_iec_global_items(resp.text)
        if not parsed:
            msg = "HTML OK but 0 .active-tenders-item cards parsed"
            LAST_FETCH_ERRORS["IEC global-iec.com"] = msg
            print(f"  [IEC] global: {msg}")
            return results

        vehicle_n = 0
        for p in parsed:
            hay = f"{p['title']} {p['description']} {p['blob']}"
            if not match_keywords(hay, IEC_VEHICLE_TERMS):
                continue
            vehicle_n += 1
            results.append(
                {
                    "Source": "🇮🇱 IEC Israel",
                    "Source Notice ID": p["nid"],
                    "Lifecycle": classify_lifecycle(p["title"], ""),
                    "Notice Type": "",
                    "Procedure Type": "",
                    "Buyer Type": "",
                    "Score": score_legacy(p["title"]),
                    "FleetSize": extract_fleet_size(p["title"] + " " + p["description"]),
                    "Title": p["title"],
                    "Buyer": "Israel Electric Corporation (IEC) / חברת החשמל",
                    "CPV Code": "",
                    "CPV Desc": "",
                    "Description": (p["description"] or p["title"])[:800],
                    "Est. Value": "",
                    "Currency": "ILS",
                    "Published": p["published"],
                    "Deadline": p["deadline"],
                    "Country": "Israel",
                    "Country Code": "ISR",
                    "URL": IEC_GLOBAL_URL + "#" + p["nid"],
                }
            )
        # Endpoint healthy when cards parse — vehicle survivors may be 0 (not a broken feed).
        LAST_FETCH_ERRORS["IEC global-iec.com"] = None
        LAST_FETCH_ERRORS["IEC global-iec.com raw_count"] = str(len(parsed))
        print(
            f"  [IEC] global: {len(parsed)} international tenders parsed; "
            f"{vehicle_n} vehicle-keyword hits → {len(results)} rows"
        )
        if vehicle_n == 0:
            print(
                "  [IEC] No vehicle/fleet/leasing hits on international list "
                "(UMI chase likely on GEO_BLOCKED domestic portal)."
            )
    except Exception as exc:
        LAST_FETCH_ERRORS["IEC global-iec.com"] = str(exc)
        print(f"  [IEC] global: {exc}")
    print(f"[IEC] Vehicle-keyword matches: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# Doffin — Public API v2 search (Azure APIM; keys via nordics_keys)
# ---------------------------------------------------------------------------

def _doffin_buyer_name(n: Dict[str, Any]) -> str:
    buyer = n.get("buyer") or n.get("contractingAuthority")
    if isinstance(buyer, list):
        names = []
        for b in buyer:
            if isinstance(b, dict):
                names.append(extract_text(b.get("name") or b.get("organisationName")))
            else:
                names.append(extract_text(b))
        return ", ".join(x for x in names if x)
    if isinstance(buyer, dict):
        return extract_text(buyer.get("name") or buyer.get("organisationName"))
    return extract_text(buyer)


def _doffin_cpv(n: Dict[str, Any]) -> str:
    codes = n.get("cpvCodes") or n.get("cpvCode") or n.get("cpv")
    if isinstance(codes, list):
        parts = []
        for c in codes:
            if isinstance(c, dict):
                parts.append(extract_text(c.get("code") or c.get("id") or c.get("cpvCode")))
            else:
                parts.append(extract_text(c))
        return ";".join(x for x in parts if x)
    return extract_text(codes)


def _doffin_value(n: Dict[str, Any]) -> Tuple[Any, str]:
    val = n.get("estimatedValue") or n.get("value")
    if isinstance(val, dict):
        return val.get("amount", ""), extract_text(val.get("currencyCode") or "NOK") or "NOK"
    return (val if val not in (None, "") else ""), "NOK"


def fetch_doffin(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    key = get_doffin_key()
    if not key:
        print(missing_key_banner("doffin"))
        LAST_FETCH_ERRORS["Norway Doffin"] = (
            "AWAITING_KEY — set ISZE_DOFFIN_API_KEY in nordics_api_keys.env (see NORDICS_API_KEYS.md)"
        )
        return []

    print("\n[Doffin] Fetching from Doffin Public API (Norway)...")
    print(f"  GET {DOFFIN_SEARCH_URL}")
    headers = {"Ocp-Apim-Subscription-Key": key, "Accept": "application/json"}
    date_from = from_dt.strftime("%Y-%m-%d")
    # Public search does NOT honour English OR-chains (returns 0). Use NO stems one-by-one.
    search_terms = [
        "kjøretøy",
        "lastebil",
        "pickup",
        "varebil",
        "chassis",
        "vedlikehold kjøretøy",
        "truck",
        "isuzu",
    ]
    keywords_no = [
        "kjøretøy", "kjoretoy", "lastebil", "varebil", "pickup", "pick-up",
        "chassis", "tipp", "flak", "nyttebil", "isuzu", "d-max", "d max",
        "vedlikehold", "reparasjon", "fleet", "truck", "vehicle",
    ]
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    limit = 100
    last_err: Optional[str] = None

    for term in search_terms:
        page = 1
        while page <= 5:
            params = {
                "searchString": term,
                "issueDateFrom": date_from,
                "numHitsPerPage": str(limit),
                "page": str(page),
            }
            try:
                resp = session.get(DOFFIN_SEARCH_URL, headers=headers, params=params, timeout=30)
                print(f"  [{term}] page {page} – Status: {resp.status_code}")
                if resp.status_code == 401:
                    print("  [Doffin] Invalid API key (401). Re-copy Primary key from the Public API portal.")
                    LAST_FETCH_ERRORS["Norway Doffin"] = "HTTP 401 invalid subscription key"
                    return []
                if resp.status_code != 200:
                    print(f"  [Doffin] Error: {resp.text[:300]}")
                    last_err = f"HTTP {resp.status_code}"
                    break
                data = resp.json()
                if isinstance(data, list):
                    notices = data
                else:
                    notices = data.get("hits") or data.get("notices") or data.get("items") or []
                if not notices:
                    break
                for n in notices:
                    if not isinstance(n, dict):
                        continue
                    title = extract_text(n.get("heading") or n.get("title") or n.get("noticeTitle"))
                    cpv_code = _doffin_cpv(n)
                    if cpv_is_excluded(cpv_code):
                        continue
                    cpv_desc = extract_text(n.get("cpvDescription"))
                    desc = extract_text(n.get("description") or n.get("shortDescription"))
                    types = n.get("allTypes")
                    notice_type = extract_text(
                        n.get("noticeType")
                        or (", ".join(types) if isinstance(types, list) else n.get("type"))
                    )
                    blob = " ".join([title, cpv_desc, desc, notice_type])
                    if not match_keywords(blob, KEYWORDS + keywords_no):
                        continue
                    nid = str(n.get("id") or n.get("noticeId") or n.get("doffinId") or "")
                    if nid and nid in seen:
                        continue
                    if nid:
                        seen.add(nid)
                    val, currency = _doffin_value(n)
                    url = extract_text(
                        n.get("doffinClassicUrl") or n.get("url") or n.get("noticeUrl")
                        or (f"https://www.doffin.no/notices/{nid}" if nid else "")
                    )
                    results.append({
                        "Source": "🇳🇴 Norway",
                        "Source Notice ID": nid,
                        "Lifecycle": classify_lifecycle(blob, notice_type),
                        "Notice Type": notice_type,
                        "Procedure Type": extract_text(n.get("procedureType")),
                        "Buyer Type": "",
                        "Score": score_legacy(title, parse_number(val)),
                        "FleetSize": extract_fleet_size(title, desc),
                        "Title": title,
                        "Buyer": _doffin_buyer_name(n),
                        "CPV Code": cpv_code,
                        "CPV Desc": cpv_desc,
                        "Description": desc,
                        "Est. Value": val,
                        "Currency": currency,
                        "Published": extract_text(
                            n.get("issueDate") or n.get("publicationDate") or n.get("publishedDate")
                        ),
                        "Deadline": extract_text(n.get("deadline") or n.get("submissionDeadline")),
                        "Country": "Norway",
                        "Country Code": "NOR",
                        "URL": url,
                    })
                if len(notices) < limit:
                    break
                page += 1
                time.sleep(0.35)
            except Exception as exc:
                print(f"  [Doffin] Exception on [{term}] page {page}: {exc}")
                last_err = str(exc)
                break
        time.sleep(0.2)

    LAST_FETCH_ERRORS["Norway Doffin"] = None if results else (last_err or "zero vehicle-ish rows (key OK)")
    print(f"[Doffin] Total unique: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# HILMA — AVP Notices (Azure APIM; keys via nordics_keys)
# ---------------------------------------------------------------------------

def fetch_hilma(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    key = get_hilma_key()
    if not key:
        print(missing_key_banner("hilma"))
        LAST_FETCH_ERRORS["Finland HILMA"] = (
            "AWAITING_KEY — set ISZE_HILMA_API_KEY in nordics_api_keys.env (see NORDICS_API_KEYS.md)"
        )
        return []

    # Prod host is api.hankintailmoitukset.fi — Azure Search over eForms index.
    print("\n[HILMA] Fetching from HILMA AVP Search (Finland)...")
    print(f"  POST {HILMA_NOTICES_URL}")
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    published = from_dt.strftime("%Y-%m-%dT00:00:00Z")
    search_terms = (
        "ajoneuvo* OR huolto* OR korjaus* OR kuljetus* OR pakettiauto* OR "
        "kuorma-auto* OR fleet OR vehicle* OR maintenance OR pickup OR van OR "
        "truck OR isuzu"
    )
    body = {
        "search": search_terms,
        "filter": f"datePublished ge {published}",
        "top": 100,
        "count": True,
        "orderby": "datePublished desc",
        "searchMode": "any",
    }
    try:
        resp = session.post(HILMA_NOTICES_URL, headers=headers, json=body, timeout=60)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 401:
            print("  [HILMA] Invalid API key (401). Confirm AVP-Read subscription Primary key.")
            LAST_FETCH_ERRORS["Finland HILMA"] = "HTTP 401 invalid subscription key"
            return []
        if resp.status_code != 200:
            print(f"  [HILMA] Error: {resp.text[:300]}")
            LAST_FETCH_ERRORS["Finland HILMA"] = f"HTTP {resp.status_code}"
            return []
        data = resp.json() if resp.content else {}
        notices = data.get("value") if isinstance(data, dict) else []
        if not isinstance(notices, list):
            notices = []
        print(
            f"[HILMA] Got {len(notices)} notices "
            f"(odata.count={data.get('@odata.count') if isinstance(data, dict) else '?'})"
        )
        results: List[Dict[str, Any]] = []
        for n in notices:
            if not isinstance(n, dict):
                continue
            title = extract_text(
                n.get("titleFi")
                or n.get("titleEn")
                or n.get("titleSv")
                or n.get("titleOther")
                or n.get("title")
                or n.get("name")
            )
            cpv_raw = n.get("cpvCodes") or n.get("cpv") or n.get("CPV")
            if isinstance(cpv_raw, list):
                cpv_code = ";".join(extract_text(c) for c in cpv_raw if c)
            else:
                cpv_code = extract_text(cpv_raw)
            if cpv_is_excluded(cpv_code):
                continue
            desc = extract_text(
                n.get("descriptionFi")
                or n.get("descriptionEn")
                or n.get("descriptionSv")
                or n.get("description")
            )
            blob = " ".join([title, desc])
            if not match_keywords(blob, KEYWORDS):
                continue
            nid = str(n.get("noticeId") or n.get("id") or "")
            buyer = extract_text(
                n.get("organisationNameFi")
                or n.get("organisationNameEn")
                or n.get("organisationNameSv")
                or n.get("organisationNameOther")
            )
            url = ""
            if nid and str(nid).isdigit():
                url = f"https://www.hankintailmoitukset.fi/fi/public/procurement/{nid}/"
            results.append({
                "Source": "🇫🇮 Finland",
                "Source Notice ID": nid,
                "Lifecycle": classify_lifecycle(
                    blob, extract_text(n.get("mainType") or n.get("type") or n.get("noticeType"))
                ),
                "Notice Type": extract_text(n.get("mainType") or n.get("type")),
                "Procedure Type": extract_text(n.get("procedureType")),
                "Buyer Type": extract_text(n.get("organisationType")),
                "Score": score_legacy(title),
                "FleetSize": extract_fleet_size(title),
                "Title": title,
                "Buyer": buyer,
                "CPV Code": cpv_code,
                "CPV Desc": "",
                "Description": desc,
                "Est. Value": n.get("noticeResultTotalAmount") or n.get("estimatedValue") or "",
                "Currency": extract_text(
                    n.get("noticeResultTotalAmountCurrency") or "EUR"
                ) or "EUR",
                "Published": extract_text(n.get("datePublished") or n.get("publishedDate")),
                "Deadline": extract_text(
                    n.get("tendersOrRequestsToParticipateDueDate")
                    or n.get("deadline")
                    or n.get("tenderdate")
                ),
                "Country": "Finland",
                "Country Code": "FIN",
                "URL": url,
            })
        print(f"[HILMA] Matches: {len(results)}")
        return results
    except Exception as exc:
        print(f"[HILMA] Error: {exc}")
        LAST_FETCH_ERRORS["Finland HILMA"] = str(exc)
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
# Substring matches for service.bund RSS (German titles; avoid bare "wartung").
KEYWORDS_DE = [
    "fahrzeug", "fuhrpark", "nutzfahrzeug", "pritschenwagen", "flottenmanagement",
    "flottenwartung", "fahrzeugwartung", "fahrzeuginstandhaltung", "fahrzeuginstandsetzung",
    "fahrzeugreparatur", "kfz-wartung", "lkw", "nkw", "lieferwagen", "transporter",
    "bestelwagen", "pickup", "pick-up", "chassis", "d-max", "isuzu",
]

# Free national feed (works). DTVP anonymous RSS 404s — retired; TED covers above-threshold DEU.
SERVICE_BUND_RSS_URL = (
    "https://www.service.bund.de/SiteGlobals/Functions/RSSFeed/RSSGenerator_Ausschreibungen.xml"
)
DTVP_RSS_URL = "https://www.dtvp.de/Center/company/public/procurement/rss"
NRW_SEARCH_URL = "https://www.vergabe.nrw.de/VMPSatellite/satellite.vm"
TENDERNED_RSS_URL = "https://www.tenderned.nl/papi/tenderned-rs-tns/rss/laatste-publicatie.rss"
# Belgium RSS is a Vue SPA shell (no <item>) — retired. Live path: Keycloak + SEA search API.
BELGIUM_RSS_CANDIDATES = [
    "https://www.publicprocurement.be/supplier/feed/rss",
    "https://www.publicprocurement.be/en/rss",
]
BELGIUM_ENV_CONFIG_URL = "https://www.publicprocurement.be/env.config.js"
BELGIUM_TOKEN_URL = (
    "https://www.publicprocurement.be/auth/realms/supplier/protocol/openid-connect/token"
)
BELGIUM_SEARCH_URL = "https://www.publicprocurement.be/api/sea/search/publications"
BELGIUM_PUB_BASE = "https://www.publicprocurement.be/en/publication-workspaces/"
# NL/FR/EN vehicle terms for below-threshold BDA search (CPV list is primary filter).
BELGIUM_SEARCH_TERMS = ["voertuig", "véhicule", "vehicle", "camion", "bestelwagen", "pickup"]


def _be_pick_lang_text(items: Any, prefer: Tuple[str, ...] = ("EN", "NL", "FR", "DE")) -> str:
    if not isinstance(items, list):
        return extract_text(items or "")
    by_lang = {}
    for it in items:
        if isinstance(it, dict) and it.get("text"):
            by_lang[str(it.get("language") or "").upper()] = str(it["text"])
    for lang in prefer:
        if lang in by_lang:
            return extract_text(by_lang[lang])
    if by_lang:
        return extract_text(next(iter(by_lang.values())))
    return ""


def _be_load_spa_client_credentials(session: requests.Session) -> Tuple[str, str, Optional[str]]:
    """Resolve client_id/secret: env first, else public SPA env.config.js (never hardcode in git).

    The SPA publishes ``VITE_AUTH_CLIENTID=frontend-public`` and ``VITE_AUTH_CLIENTSECRET``
    at ``/env.config.js``. Prefer ``ISZE_BE_CLIENT_ID`` / ``ISZE_BE_CLIENT_SECRET`` in
    ``isze_secrets.env``. Longer-term: BOSA partner onboarding for a dedicated client.
    """
    cid = (os.environ.get("ISZE_BE_CLIENT_ID") or "").strip()
    secret = (os.environ.get("ISZE_BE_CLIENT_SECRET") or "").strip()
    if cid and secret:
        return cid, secret, None
    try:
        resp = session.get(BELGIUM_ENV_CONFIG_URL, timeout=30)
        if resp.status_code != 200:
            return cid or "frontend-public", secret, f"env.config.js HTTP {resp.status_code}"
        text = resp.text or ""
        m_id = re.search(r"VITE_AUTH_CLIENTID\s*[:=]\s*['\"]([^'\"]+)", text)
        m_sec = re.search(r"VITE_AUTH_CLIENTSECRET\s*[:=]\s*['\"]([^'\"]+)", text)
        if m_id:
            cid = cid or m_id.group(1).strip()
        if m_sec:
            secret = secret or m_sec.group(1).strip()
        if not secret:
            return cid or "frontend-public", "", "VITE_AUTH_CLIENTSECRET missing from env.config.js"
        return cid or "frontend-public", secret, None
    except Exception as exc:
        return cid or "frontend-public", secret, f"env.config.js fetch failed: {exc}"


def _be_get_token(session: requests.Session, client_id: str, client_secret: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        resp = session.post(
            BELGIUM_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=30,
            headers={"Accept": "application/json"},
        )
        if resp.status_code != 200:
            return None, f"token HTTP {resp.status_code}: {(resp.text or '')[:180]}"
        token = (resp.json() or {}).get("access_token")
        if not token:
            return None, "token response missing access_token"
        return str(token), None
    except Exception as exc:
        return None, str(exc)


def _be_pub_to_row(pub: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    dossier = pub.get("dossier") or {}
    title = _be_pick_lang_text(dossier.get("titles") or pub.get("titles") or [])
    if not title:
        return None
    desc = _be_pick_lang_text(dossier.get("descriptions") or [])
    org = pub.get("organisation") or {}
    buyer = _be_pick_lang_text(org.get("organisationNames") or [])
    ws = str(pub.get("publicationWorkspaceId") or "").strip()
    ref = str(pub.get("referenceNumber") or dossier.get("referenceNumber") or ws or title)
    url = BELGIUM_PUB_BASE + ws if ws else "https://www.publicprocurement.be/"
    cpv_main = pub.get("cpvMainCode") or {}
    cpv_code = str(cpv_main.get("code") or "").split("-")[0]
    cpv_desc = _be_pick_lang_text(cpv_main.get("descriptions") or [])
    deadline_raw = str(pub.get("vaultSubmissionDeadline") or "")
    deadline = deadline_raw[:19] if deadline_raw else ""
    published = str(pub.get("publicationDate") or pub.get("dispatchDate") or "")
    if cpv_code and cpv_is_excluded(cpv_code):
        return None
    return {
        "Source": "🇧🇪 BE",
        "Source Notice ID": ref,
        "Lifecycle": classify_lifecycle(title, str(pub.get("publicationType") or "")),
        "Notice Type": str(pub.get("publicationType") or ""),
        "Procedure Type": str(dossier.get("procurementProcedureType") or ""),
        "Buyer Type": "",
        "Score": score_legacy(title + " " + desc),
        "FleetSize": extract_fleet_size(title + " " + desc),
        "Title": title,
        "Buyer": buyer,
        "CPV Code": cpv_code,
        "CPV Desc": cpv_desc,
        "Description": desc[:2000] if desc else title,
        "Est. Value": "",
        "Currency": "EUR",
        "Published": published,
        "Deadline": deadline,
        "Country": "Belgium",
        "Country Code": "BEL",
        "URL": url,
    }


def fetch_belgium(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    """Belgium BDA notices via Keycloak client_credentials + POST /api/sea/search/publications.

    RSS candidates are SPA shells — RETIRED (live SEA is primary).
    """
    print("\n[BE] Fetching from publicprocurement.be SEA API…")
    LAST_FETCH_ERRORS["Belgium RSS"] = "RETIRED — HTML SPA shell; live source is Belgium publicprocurement.be SEA"

    client_id, client_secret, cred_err = _be_load_spa_client_credentials(session)
    if not client_secret:
        msg = cred_err or "ISZE_BE_CLIENT_SECRET not set and SPA config unavailable"
        print(f"[BE] BROKEN — {msg}")
        LAST_FETCH_ERRORS["Belgium publicprocurement.be"] = msg
        return []

    token, tok_err = _be_get_token(session, client_id, client_secret)
    if not token:
        msg = tok_err or "auth failed"
        print(f"[BE] BROKEN — {msg}")
        LAST_FETCH_ERRORS["Belgium publicprocurement.be"] = msg
        return []

    results: List[Dict[str, Any]] = []
    seen: set = set()
    last_err: Optional[str] = None
    date_from = from_dt.strftime("%Y-%m-%d")
    # Query once with CPV filter + active deadline; then term sweeps without forcing empty CPV miss.
    query_specs: List[Dict[str, Any]] = [
        {"terms": "", "cpvCodes": list(CPV_CODES), "label": "CPV+deadline"},
    ]
    for term in BELGIUM_SEARCH_TERMS:
        query_specs.append({"terms": term, "cpvCodes": list(CPV_CODES), "label": f"term={term}"})

    for spec in query_specs:
        page = 1
        page_size = 50
        while page <= 10:
            headers = {
                "Authorization": f"Bearer {token}",
                "BelGov-Trace-Id": str(uuid.uuid4()),
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            body = {
                "terms": spec["terms"],
                "cpvCodes": spec["cpvCodes"],
                "withActiveSubmissionDeadline": True,
                "publicationDateFrom": date_from,
                "page": page,
                "pageSize": page_size,
                "order": "DESC",
            }
            try:
                resp = session.post(BELGIUM_SEARCH_URL, headers=headers, json=body, timeout=45)
                if resp.status_code in (401, 403):
                    # refresh token once
                    token, tok_err = _be_get_token(session, client_id, client_secret)
                    if not token:
                        last_err = tok_err or f"HTTP {resp.status_code}"
                        break
                    headers["Authorization"] = f"Bearer {token}"
                    headers["BelGov-Trace-Id"] = str(uuid.uuid4())
                    resp = session.post(BELGIUM_SEARCH_URL, headers=headers, json=body, timeout=45)
                err = validate_feed("Belgium SEA", resp, expect_feed=False, expect_json=True, min_bytes=20)
                if err:
                    last_err = err
                    print(f"  [BE] {spec['label']} p{page}: BROKEN — {err}")
                    break
                if resp.status_code != 200:
                    last_err = f"HTTP {resp.status_code}"
                    print(f"  [BE] {spec['label']} p{page}: HTTP {resp.status_code}")
                    break
                payload = resp.json() or {}
                pubs = payload.get("publications") or []
                total = payload.get("totalCount")
                added = 0
                for pub in pubs:
                    if not isinstance(pub, dict):
                        continue
                    row = _be_pub_to_row(pub)
                    if not row:
                        continue
                    # Keyword gate when CPV-only query may still pull adjacent services
                    blob = f"{row.get('Title','')} {row.get('Description','')} {row.get('CPV Desc','')}"
                    if not match_keywords(blob, KEYWORDS + BELGIUM_SEARCH_TERMS):
                        # Keep if CPV is in surgical list (already filtered by API)
                        cpv = str(row.get("CPV Code") or "")
                        if cpv not in CPV_CODES and not any(cpv.startswith(c[:6]) for c in CPV_CODES):
                            continue
                    uid = row.get("Source Notice ID") or row.get("URL") or ""
                    if not uid or uid in seen:
                        continue
                    seen.add(uid)
                    results.append(row)
                    added += 1
                print(
                    f"  [BE] {spec['label']} p{page}: +{added} "
                    f"(page={len(pubs)}, totalCount={total})"
                )
                if not pubs or len(pubs) < page_size:
                    break
                if isinstance(total, int) and page * page_size >= total:
                    break
                page += 1
                time.sleep(0.35)
            except Exception as exc:
                last_err = str(exc)
                print(f"  [BE] {spec['label']} p{page}: {exc}")
                break
        time.sleep(0.2)

    print(f"[BE] Total Belgium SEA: {len(results)}")
    if results:
        LAST_FETCH_ERRORS["Belgium publicprocurement.be"] = None
    else:
        LAST_FETCH_ERRORS["Belgium publicprocurement.be"] = last_err or "zero publications matched"
        print("[BE] Note: TED (BEL) still covers above-threshold BE contracts.")
    return results


def fetch_belgium_rss_probe(session: requests.Session) -> None:
    """Confirm RSS remains a SPA shell; always mark RETIRED (not BROKEN)."""
    for url in BELGIUM_RSS_CANDIDATES[:1]:
        try:
            resp = session.get(url, timeout=15, headers={"Accept": "application/rss+xml, */*"})
            err = validate_feed("Belgium RSS", resp, expect_feed=True, min_bytes=500)
            if err:
                LAST_FETCH_ERRORS["Belgium RSS"] = (
                    "RETIRED — HTML SPA shell; live source is Belgium publicprocurement.be SEA"
                )
            else:
                LAST_FETCH_ERRORS["Belgium RSS"] = "unexpected: RSS returned items — review"
        except Exception as exc:
            LAST_FETCH_ERRORS["Belgium RSS"] = f"RETIRED — probe failed ({exc}); live = SEA API"


def _parse_procurement_rss(
    content: str,
    *,
    source_label: str,
    country: str,
    country_code: str,
    currency: str = "EUR",
    extra_keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Parse RSS/Atom XML → list of raw row dicts (shared by DE/BE/NL feeds)."""
    rows = []
    kw = list(KEYWORDS) + list(extra_keywords or [])
    try:
        root = ET.fromstring(content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        # Try Atom feed first, fall back to RSS2
        items = root.findall(".//atom:entry", ns) or root.findall(".//item")
        for item in items:
            def _t(tag: str, default: str = "") -> str:
                # Do NOT use `el or …` — ElementTree Elements with only text
                # are falsy (no child nodes), which wiped every RSS title.
                el = item.find(tag)
                if el is None:
                    el = item.find(f"atom:{tag}", ns)
                return (el.text or "").strip() if el is not None else default

            title = _t("title")
            description = _t("description") or _t("summary")
            published = _t("pubDate") or _t("published")
            link = _t("link")
            if not link:
                link_el = item.find("atom:link", ns)
                if link_el is not None:
                    link = link_el.get("href", "") or ""
                # RSS <link> text already handled by _t("link")

            blob = f"{title} {description}".lower()
            if not match_keywords(blob, kw):
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


def _parse_germany_rss(content: str, *, source_label: str = "🇩🇪 DE") -> List[Dict[str, Any]]:
    return _parse_procurement_rss(
        content,
        source_label=source_label,
        country="Germany",
        country_code="DEU",
        extra_keywords=KEYWORDS_DE + GERMANY_SEARCH_TERMS_DE,
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
        err = validate_feed("Netherlands", resp, expect_feed=True, min_bytes=500)
        if err:
            print(f"  [NL] BROKEN — {err}")
            return []
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


def fetch_germany(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    """German national supplemental feed via service.bund RSS.

    DTVP anonymous RSS returns 404 (paid Professional Edition for alerts) — RETIRED.
    TED (DEU) covers above-threshold. service.bund is the free national/supplemental path.
    """
    print("\n[DE] Fetching Germany national feed (service.bund RSS)…")
    results: List[Dict[str, Any]] = []
    seen_ids: set = set()
    LAST_FETCH_ERRORS["Germany DTVP/NRW"] = (
        "RETIRED — TED-only honesty for DTVP (no free feed); use TED DEU + Germany service.bund"
    )
    LAST_FETCH_ERRORS["Germany service.bund"] = None

    try:
        resp = session.get(
            SERVICE_BUND_RSS_URL,
            timeout=40,
            headers={"Accept": "application/rss+xml, application/xml, text/xml, */*"},
        )
        err = validate_feed("Germany service.bund", resp, expect_feed=True, min_bytes=500)
        if err:
            print(f"  [DE] service.bund BROKEN — {err}")
            LAST_FETCH_ERRORS["Germany service.bund"] = err
        elif resp.status_code != 200:
            print(f"  [DE] service.bund HTTP {resp.status_code}")
            LAST_FETCH_ERRORS["Germany service.bund"] = f"HTTP {resp.status_code}"
        else:
            rows = _parse_germany_rss(resp.text, source_label="🇩🇪 DE")
            for r in rows:
                uid = r.get("Source Notice ID", "") or r.get("URL", "")
                if uid and uid not in seen_ids:
                    seen_ids.add(uid)
                    results.append(r)
            print(f"  [DE] service.bund RSS: {len(rows)} keyword matches (of feed items)")
            if not rows:
                LAST_FETCH_ERRORS["Germany service.bund"] = None  # feed OK, zero vehicle hits this window
    except Exception as exc:
        print(f"  [DE] service.bund failed: {exc}")
        LAST_FETCH_ERRORS["Germany service.bund"] = str(exc)

    # DTVP probe kept only so we can confirm still 404 — never primary.
    try:
        resp_dtvp = session.get(
            DTVP_RSS_URL,
            timeout=15,
            headers={"Accept": "application/rss+xml, */*"},
        )
        if resp_dtvp.status_code == 200 and b"<item" in (resp_dtvp.content or b"")[:8000].lower():
            print("  [DE] NOTE: DTVP RSS unexpectedly returned items — review before re-enabling")
            LAST_FETCH_ERRORS["Germany DTVP/NRW"] = (
                "unexpected: DTVP RSS returned items — review (still marked RETIRED)"
            )
        else:
            print(f"  [DE] DTVP RSS still unavailable (HTTP {resp_dtvp.status_code}) — RETIRED (TED-only)")
    except Exception as exc:
        print(f"  [DE] DTVP probe skipped: {exc}")

    print(f"[DE] Total Germany national results: {len(results)}")
    if not results:
        print("[DE] Coverage note: TED (DEU) covers above-threshold German contracts.")
    return results


# ---------------------------------------------------------------------------
# Germany oeffentlichevergabe.de Open Data (BKMS / Bekanntmachungsservice)
# ---------------------------------------------------------------------------
DE_OV_EXPORT_URL = "https://oeffentlichevergabe.de/api/notice-exports"
DE_OV_NOTICE_URL = "https://oeffentlichevergabe.de/ui/de/notice/{nid}"
# Strong vehicle stems — bare construction "Fahrzeug*" noise still hits Isuzu gate downstream.
DE_OV_VEHICLE_STEMS = (
    "fahrzeug",
    "fuhrpark",
    "nutzfahrzeug",
    "pritschen",
    "flotten",
    "lieferwagen",
    "transporter",
    "bestelwagen",
    "pickup",
    "pick-up",
    "chassis",
    "isuzu",
    "d-max",
    "lkw",
    "nkw",
    "kfz-",
    "kastenwagen",
    "kipper",
    "abrollkipper",
    "sattelzug",
    "lastkraft",
)
# CPV prefixes beyond surgical list — goods transport / LCV / fleet R&M (not 34144 fire/refuse parent).
DE_OV_CPV_PREFIXES = (
    "3413",  # goods vehicles / pickups / tippers / vans
    "34113",  # 4WD
    "34136",  # vans
    "5011",  # motor vehicle repair / fleet R&M
)


def _de_ov_cpv_hit(code: str) -> bool:
    code = (code or "").strip()
    # eForms CSV sometimes emits "34130000-7" / truncated "45"
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


def _de_ov_norm_cpv(code: str) -> str:
    code = (code or "").strip()
    if "-" in code:
        code = code.split("-", 1)[0].strip()
    m = re.match(r"^(\d{8})", code)
    return m.group(1) if m else code


def _de_ov_read_csv_table(zf: zipfile.ZipFile, name: str) -> List[Dict[str, str]]:
    if name not in zf.namelist():
        return []
    text = zf.read(name).decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


def _de_ov_months_covering(from_dt: datetime, now: datetime) -> List[str]:
    """YYYY-MM months that may contain notices published on/after from_dt (Berlin days)."""
    months: List[str] = []
    # Export excludes today — walk calendar months from from_dt through yesterday.
    end = (now - timedelta(days=1)).date()
    cur = from_dt.date().replace(day=1)
    while cur <= end:
        months.append(cur.strftime("%Y-%m"))
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return months


def _de_ov_parse_csv_zip(
    body: bytes,
    *,
    cutoff: str,
    seen: Set[str],
) -> Tuple[List[Dict[str, Any]], int, int]:
    """Parse one OV csv.zip into pre-gate rows. Returns (rows, notices_scanned, vehicle_hits)."""
    results: List[Dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        notices = {
            (r["noticeIdentifier"], r["noticeVersion"]): r
            for r in _de_ov_read_csv_table(zf, "notice.csv")
            if r.get("noticeIdentifier")
        }
        purpose_rows = _de_ov_read_csv_table(zf, "purpose.csv")
        class_rows = _de_ov_read_csv_table(zf, "classification.csv")
        org_rows = _de_ov_read_csv_table(zf, "organisation.csv")
        result_rows = _de_ov_read_csv_table(zf, "noticeResult.csv")

    # Best title/desc/value per notice (prefer notice-level purpose, else first lot).
    purpose_by: Dict[Tuple[str, str], Dict[str, str]] = {}
    for p in purpose_rows:
        key = (p.get("noticeIdentifier") or "", p.get("noticeVersion") or "")
        if not key[0]:
            continue
        lot = (p.get("lotIdentifier") or "").strip()
        existing = purpose_by.get(key)
        if existing and existing.get("_lot") == "" and lot:
            continue  # keep notice-level
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
            code = _de_ov_norm_cpv(code or "")
            if not code:
                continue
            if key not in cpv_by:
                cpv_by[key] = code
            if _de_ov_cpv_hit(code):
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
        if "buyer" in role or "buyer" in (o.get("organisationRole") or "") or role in ("", "buyer"):
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

    kw_list = KEYWORDS_DE + GERMANY_SEARCH_TERMS_DE + KEYWORDS
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
        kw_ok = stem_ok and match_keywords(blob, kw_list)
        # Keyword-only keep only when CPV is missing or already vehicle-family (34*/501*).
        # Drops education/research/construction that mention "Fahrzeug*" in prose.
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
        results.append(
            {
                "Source": "🇩🇪 DE-OV",
                "Source Notice ID": nid,
                "Lifecycle": "",
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
                "CPV Code": _de_ov_norm_cpv(cpv_by.get(key, "")),
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


def fetch_germany_ov(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    """National DE notices via oeffentlichevergabe Bekanntmachungsservice Open Data CSV ZIPs.

    Endpoint: GET /api/notice-exports?pubMonth=YYYY-MM&format=csv.zip
    (pubDay also works; today/future days are rejected by the API.)
    """
    print("\n[DE OV] Fetching oeffentlichevergabe Open Data (csv.zip, vehicle CPV/keyword)...")
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    now = datetime.now(timezone.utc)
    cutoff = from_dt.strftime("%Y-%m-%d")
    months = _de_ov_months_covering(from_dt, now)
    LAST_FETCH_ERRORS["Germany oeffentlichevergabe"] = None
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ISZE-TenderMonitor/3.0)",
        "Accept": "application/vnd.bekanntmachungsservice.csv.zip+zip, application/zip, */*",
    }
    total_scanned = 0
    try:
        if not months:
            LAST_FETCH_ERRORS["Germany oeffentlichevergabe"] = "no exportable months in lookback"
            print("  [DE OV] no months to fetch")
            return []
        for month in months:
            params = {"pubMonth": month, "format": "csv.zip"}
            try:
                resp = session.get(DE_OV_EXPORT_URL, params=params, headers=headers, timeout=180)
            except Exception as exc:
                LAST_FETCH_ERRORS["Germany oeffentlichevergabe"] = str(exc)
                print(f"  [DE OV] {month}: {exc}")
                continue
            body = resp.content or b""
            if resp.status_code != 200:
                msg = f"HTTP {resp.status_code} month={month}"
                LAST_FETCH_ERRORS["Germany oeffentlichevergabe"] = msg
                print(f"  [DE OV] {month}: {msg} {(body[:120] or b'').decode('utf-8', errors='replace')}")
                continue
            if body[:2] != b"PK":
                LAST_FETCH_ERRORS["Germany oeffentlichevergabe"] = (
                    f"non-ZIP response month={month} ({len(body)} bytes)"
                )
                print(f"  [DE OV] {month}: non-ZIP body")
                continue
            rows, scanned, hits = _de_ov_parse_csv_zip(body, cutoff=cutoff, seen=seen)
            total_scanned += scanned
            results.extend(rows)
            print(f"  [DE OV] {month}: scanned≈{scanned} vehicle-ish +{hits} (zip {len(body)} bytes)")
            LAST_FETCH_ERRORS["Germany oeffentlichevergabe"] = None
        print(f"[DE OV] Unique matches: {len(results)} (scanned≈{total_scanned} across {months})")
        if not results and not LAST_FETCH_ERRORS.get("Germany oeffentlichevergabe"):
            # Feed OK, zero vehicle hits this window — still OK health.
            LAST_FETCH_ERRORS["Germany oeffentlichevergabe"] = None
    except Exception as exc:
        LAST_FETCH_ERRORS["Germany oeffentlichevergabe"] = str(exc)
        print(f"  [DE OV] exception: {exc}")
    return results


# ---------------------------------------------------------------------------
# France BOAMP (below-threshold national) — OpenDataSoft public API
# ---------------------------------------------------------------------------
BOAMP_RECORDS_URL = (
    "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"
)
# Keep keyword filter tight — product-fit gate still applies downstream.
BOAMP_WHERE = (
    "objet like '%vehicule%' OR objet like '%camion%' OR objet like '%utilitaire%' "
    "OR objet like '%fourgon%' OR objet like '%pickup%' OR objet like '%pick-up%' "
    "OR objet like '%chassis%' OR objet like '%benne%'"
)


def fetch_france_boamp(session: requests.Session, from_dt: datetime, limit: int = 80) -> List[Dict[str, Any]]:
    """National FR notices via BOAMP ODS (includes below-threshold). Not in weekly bat yet."""
    print("\n[FR BOAMP] Fetching OpenDataSoft records (vehicle/objet filter)...")
    results: List[Dict[str, Any]] = []
    params = {
        "limit": min(limit, 100),
        "where": BOAMP_WHERE,
        "order_by": "-dateparution",
    }
    try:
        resp = session.get(BOAMP_RECORDS_URL, params=params, timeout=40)
        if resp.status_code != 200:
            msg = f"HTTP {resp.status_code}"
            LAST_FETCH_ERRORS["France BOAMP"] = msg
            print(f"  [FR BOAMP] FAIL {msg}")
            return []
        data = resp.json()
        rows = data.get("results") or []
        print(f"  [FR BOAMP] API total_count≈{data.get('total_count')} · page={len(rows)}")
        for row in rows:
            title = str(row.get("objet") or "").strip()
            if not title:
                continue
            pub = str(row.get("dateparution") or "")[:10]
            if pub and pub < from_dt.strftime("%Y-%m-%d"):
                continue
            nid = str(row.get("idweb") or row.get("id") or "")
            deadline = str(row.get("datelimitereponse") or "")
            buyer = str(row.get("nomacheteur") or "")
            url = f"https://www.boamp.fr/pages/avis/?q=idweb:{nid}" if nid else "https://www.boamp.fr/"
            results.append(
                {
                    "Source": "🇫🇷 FR-BOAMP",
                    "Source Notice ID": nid,
                    "Lifecycle": classify_lifecycle(title, ""),
                    "Notice Type": str(row.get("nature_libelle") or ""),
                    "Procedure Type": str(row.get("procedure_libelle") or ""),
                    "Buyer Type": "",
                    "Score": score_legacy(title),
                    "FleetSize": extract_fleet_size(title),
                    "Title": title,
                    "Buyer": buyer,
                    "CPV Code": "",
                    "CPV Desc": "",
                    "Description": title,
                    "Est. Value": "",
                    "Currency": "EUR",
                    "Published": pub,
                    "Deadline": deadline,
                    "Country": "France",
                    "Country Code": "FRA",
                    "URL": url,
                }
            )
        LAST_FETCH_ERRORS["France BOAMP"] = None if results else "zero vehicle-ish rows in lookback window"
        print(f"[FR BOAMP] Matches in lookback: {len(results)}")
    except Exception as exc:
        LAST_FETCH_ERRORS["France BOAMP"] = str(exc)
        print(f"  [FR BOAMP] exception: {exc}")
    return results


# ---------------------------------------------------------------------------
# Poland BZP / e-Zamówienia (below-threshold national) — mo-board API
# ---------------------------------------------------------------------------
PL_BZP_NOTICE_URL = "https://ezamowienia.gov.pl/mo-board/api/v1/notice"
# Goods-vehicle CPVs (surgical — same family as TED list; gate still applies).
PL_BZP_CPVS = ["34131000", "34130000", "34136000", "34136200", "34113000", "50114000", "50110000"]


def fetch_poland_bzp(session: requests.Session, from_dt: datetime, page_size: int = 20) -> List[Dict[str, Any]]:
    """National PL notices via e-Zamówienia BZP API (isTenderAmountBelowEU often true)."""
    print("\n[PL BZP] Fetching e-Zamówienia notices (CPV filter)...")
    results: List[Dict[str, Any]] = []
    seen: set = set()
    date_from = from_dt.date().isoformat()
    date_to = datetime.now(timezone.utc).date().isoformat()
    try:
        for cpv in PL_BZP_CPVS:
            params = {
                "PageSize": page_size,
                "PageNumber": 1,
                "NoticeType": "ContractNotice",
                "PublicationDateFrom": date_from,
                "PublicationDateTo": date_to,
                "CpvCode": cpv,
            }
            resp = session.get(PL_BZP_NOTICE_URL, params=params, timeout=40)
            if resp.status_code != 200:
                print(f"  [PL BZP] CPV {cpv}: HTTP {resp.status_code}")
                continue
            try:
                rows = resp.json()
            except Exception:
                rows = []
            if not isinstance(rows, list):
                rows = []
            print(f"  [PL BZP] CPV {cpv}: {len(rows)} rows")
            for row in rows:
                nid = str(row.get("noticeNumber") or row.get("bzpNumber") or "")
                if not nid or nid in seen:
                    continue
                seen.add(nid)
                title = str(row.get("orderObject") or "").strip()
                if not title:
                    continue
                below = row.get("isTenderAmountBelowEU")
                results.append(
                    {
                        "Source": "🇵🇱 PL-BZP",
                        "Source Notice ID": nid,
                        "Lifecycle": classify_lifecycle(title, ""),
                        "Notice Type": str(row.get("noticeType") or ""),
                        "Procedure Type": str(row.get("tenderType") or ""),
                        "Buyer Type": str(row.get("clientType") or ""),
                        "Score": score_legacy(title),
                        "FleetSize": extract_fleet_size(title),
                        "Title": title,
                        "Buyer": str(row.get("organizationName") or ""),
                        "CPV Code": str(row.get("cpvCode") or ""),
                        "CPV Desc": "",
                        "Description": title + (f" [belowEU={below}]" if below is not None else ""),
                        "Est. Value": "",
                        "Currency": "PLN",
                        "Published": str(row.get("publicationDate") or "")[:10],
                        "Deadline": str(row.get("submittingOffersDate") or ""),
                        "Country": "Poland",
                        "Country Code": "POL",
                        "URL": f"https://ezamowienia.gov.pl/mp-client/search/list/{row.get('objectId') or ''}",
                    }
                )
            time.sleep(0.3)
        LAST_FETCH_ERRORS["Poland BZP"] = None if results else "zero CPV matches in lookback"
        print(f"[PL BZP] Unique matches: {len(results)}")
    except Exception as exc:
        LAST_FETCH_ERRORS["Poland BZP"] = str(exc)
        print(f"  [PL BZP] exception: {exc}")
    return results


# ---------------------------------------------------------------------------
# Spain PLACSP (below-threshold national) — Atom / open-data syndication
# ---------------------------------------------------------------------------
# Official Atom + monthly ZIP paths (Hacienda / OpenPLACSP docs).
# 2026-08-25: some runners WAF-denied Atom/ZIP → CODE_READY.
# 2026-09-14 retry: Atom HTTP 200 (~770 KB, not WAF) from this runner — treat as LIVE
# when fetch_spain_placsp returns keyword rows. Keep WAF detector for other egress.
ES_PLACSP_ATOM_URLS = [
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom",
    "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom",
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_1044/PlataformasAgregadasSinMenores.atom",
]
KEYWORDS_ES = [
    "vehiculo", "vehículo", "vehiculos", "vehículos", "camion", "camión", "camiones",
    "furgon", "furgón", "furgoneta", "pickup", "pick-up", "pick up", "todoterreno",
    "4x4", "chasis", "chassis", "caja abierta", "volquete", "flota", "parque movil",
    "parque móvil", "isuzu", "d-max", "d max", "utilitario", "comerciales",
    "mantenimiento de vehiculos", "mantenimiento de vehículos", "taller",
]


def _placsp_waf_body(body: bytes) -> bool:
    head = (body or b"")[:800].lower()
    return (
        b"web application firewall" in head
        or b"has denied your transaction" in head
        or (b"<html" in head and b"denied" in head)
    )


def fetch_spain_placsp(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    """National ES notices via PLACSP Atom syndication (vehicle keyword gate).

    Returns rows when Atom XML is reachable. On WAF deny, records CODE_READY and [].
    """
    print("\n[ES PLACSP] Fetching Atom syndication (vehicle keyword filter)...")
    results: List[Dict[str, Any]] = []
    last_err: Optional[str] = None
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/atom+xml, application/xml, text/xml, */*",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": (
            "https://www.hacienda.gob.es/es-ES/GobiernoAbierto/"
            "Datos%20Abiertos/Paginas/LicitacionesAgregacion.aspx"
        ),
    }
    try:
        for url in ES_PLACSP_ATOM_URLS:
            try:
                resp = session.get(url, headers=headers, timeout=45)
            except Exception as exc:
                last_err = str(exc)
                print(f"  [ES PLACSP] {url.split('/')[-1]}: {exc}")
                continue
            body = resp.content or b""
            if _placsp_waf_body(body):
                last_err = (
                    "WAF_BLOCKED — PLACSP Atom/ZIP denied from this runner "
                    "(contrataciondelestado.es / contrataciondelsectorpublico.gob.es); "
                    "official syndication still documented — CODE_READY"
                )
                print(f"  [ES PLACSP] {url.split('/')[-1]}: WAF deny (HTTP {resp.status_code})")
                continue
            err = validate_feed("Spain PLACSP", resp, expect_feed=True, min_bytes=200)
            if err:
                last_err = err
                print(f"  [ES PLACSP] {url.split('/')[-1]}: {err}")
                continue
            rows = _parse_procurement_rss(
                resp.text,
                source_label="🇪🇸 ES-PLACSP",
                country="Spain",
                country_code="ESP",
                extra_keywords=KEYWORDS_ES,
            )
            # Lookback filter on published when parseable
            cutoff = from_dt.strftime("%Y-%m-%d")
            kept = []
            for r in rows:
                pub = str(r.get("Published") or "")[:10]
                if pub and pub < cutoff:
                    continue
                kept.append(r)
            print(f"  [ES PLACSP] {url.split('/')[-1]}: {len(kept)} keyword matches")
            results.extend(kept)
            if kept:
                last_err = None
        # Dedupe by URL across Atom variants (estado vs sectorpublico vs aggregated)
        seen: set[str] = set()
        uniq: List[Dict[str, Any]] = []
        for r in results:
            key = str(r.get("URL") or r.get("url") or r.get("Title") or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            uniq.append(r)
        results = uniq
        if results:
            LAST_FETCH_ERRORS["Spain PLACSP"] = None
        else:
            LAST_FETCH_ERRORS["Spain PLACSP"] = last_err or "zero vehicle-ish Atom rows"
        print(f"[ES PLACSP] Matches: {len(results)}")
    except Exception as exc:
        LAST_FETCH_ERRORS["Spain PLACSP"] = str(exc)
        print(f"  [ES PLACSP] exception: {exc}")
    return results


# ---------------------------------------------------------------------------
# Italy PNCP / Pubblicità a valore legale (below-threshold national)
# ---------------------------------------------------------------------------
IT_PNCP_AVVISI_URL = "https://pubblicitalegale.anticorruzione.it/api/v0/avvisi"
# Bandi / avvisi di indizione sheet codes used by the SPA home counters.
IT_PNCP_CODICE_SCHEDA = "1,3,5a,5b,6,8b,10"
KEYWORDS_IT = [
    "autocarro", "autocarri", "automezzo", "automezzi", "autoveicol",
    "camion", "furgone", "furgoni", "pickup", "pick-up", "pick up",
    "veicoli commerciali", "veicolo commerciale", "veicoli", "veicolo",
    "parco auto", "parco mezzi", "parco automezzi", "parco autovetture",
    "noleggio veicoli", "noleggio auto", "noleggio automez",
    "chassis", "cassone", "cabina", "isuzu", "d-max", "d max",
    "manutenzione", "riparazione", "officina", "flotta",
]
# High-noise Italian terms that match KEYWORDS_IT substrings but are not CV buys.
IT_PNCP_NOISE = [
    "telaio pieghevole", "carrozzina", "studio del traffico", "fluidificazione del traffic",
    "autorimessa", "strati bituminosi", "pneumatici", "ventilatore",
]


def _it_pncp_walk_text(obj: Any, out: List[str], depth: int = 0) -> None:
    if depth > 8:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if isinstance(v, (str, int, float)) and any(
                x in lk
                for x in (
                    "titolo",
                    "descr",
                    "oggetto",
                    "cpv",
                    "cig",
                    "denominazione",
                    "valore",
                    "importo",
                )
            ):
                out.append(str(v))
            else:
                _it_pncp_walk_text(v, out, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:40]:
            _it_pncp_walk_text(item, out, depth + 1)


def _it_pncp_extract_list_fields(row: Dict[str, Any]) -> Dict[str, str]:
    title = ""
    desc = ""
    buyer = ""
    cpv = ""
    value = ""
    url = ""
    for t in row.get("templates") or []:
        tmpl = (t.get("template") or {}) if isinstance(t, dict) else {}
        meta = tmpl.get("metadata") or {}
        if meta.get("titolo"):
            title = str(meta.get("titolo") or "")
        if meta.get("descrizione"):
            desc = str(meta.get("descrizione") or "")
        for sec in tmpl.get("sections") or []:
            fields = (sec.get("fields") or {}) if isinstance(sec, dict) else {}
            for sa in fields.get("soggetti_sa") or []:
                if isinstance(sa, dict) and sa.get("denominazione_amministrazione"):
                    buyer = str(sa.get("denominazione_amministrazione") or buyer)
            for item in sec.get("items") or []:
                if not isinstance(item, dict):
                    continue
                if item.get("cpv") and not cpv:
                    raw = str(item.get("cpv") or "")
                    m = re.search(r"\b([0-9]{8})\b", raw)
                    cpv = m.group(1) if m else raw[:80]
                if item.get("valore_complessivo_stimato") not in (None, "") and not value:
                    value = str(item.get("valore_complessivo_stimato"))
                if item.get("descrizione") and not title:
                    title = str(item.get("descrizione") or "")
    blob_parts: List[str] = []
    _it_pncp_walk_text(row, blob_parts)
    blob = " ".join(blob_parts)
    if not title:
        title = (desc or blob)[:240]
    return {
        "title": title.strip(),
        "description": (desc or title).strip(),
        "buyer": buyer.strip(),
        "cpv": cpv.strip(),
        "value": value.strip(),
        "url": url,
        "blob": blob.lower(),
    }


def _it_pncp_enrich_detail(session: requests.Session, nid: str) -> Dict[str, str]:
    """Optional detail fetch for numeric CPV + procedure URL."""
    out = {"cpv": "", "url": "", "buyer": "", "value": ""}
    try:
        resp = session.get(
            f"{IT_PNCP_AVVISI_URL}/{nid}",
            headers={
                "Accept": "application/json",
                "Referer": "https://pubblicitalegale.anticorruzione.it/",
                "User-Agent": "Mozilla/5.0 (compatible; ISZE-TenderMonitor/3.0)",
            },
            timeout=30,
        )
        if resp.status_code != 200 or not (resp.content or b"").startswith((b"{", b"[")):
            return out
        data = resp.json() or {}
        fields = _it_pncp_extract_list_fields(data)
        out["cpv"] = fields["cpv"]
        out["buyer"] = fields["buyer"]
        out["value"] = fields["value"]
        # Prefer first https link in detail JSON (often buyer platform notice).
        for m in re.finditer(r"https?://[^\s\"'\\]+", json.dumps(data, ensure_ascii=False)):
            link = m.group(0).rstrip(".,);")
            if "anticorruzione" in link:
                continue
            out["url"] = link
            break
        if not out["url"]:
            out["url"] = f"https://pubblicitalegale.anticorruzione.it/dettaglio-avviso/{nid}"
        # Numeric CPV from full detail dump if list field was descriptive only.
        if out["cpv"] and not re.fullmatch(r"[0-9]{8}", out["cpv"]):
            nums = re.findall(r"\b(34[0-9]{6}|50[0-9]{6})\b", json.dumps(data))
            if nums:
                out["cpv"] = nums[0]
    except Exception:
        pass
    return out


def fetch_italy_pncp(
    session: requests.Session,
    from_dt: datetime,
    *,
    page_size: int = 100,
    max_pages: int = 20,
) -> List[Dict[str, Any]]:
    """National IT notices via PNCP Pubblicità a valore legale public JSON API."""
    print("\n[IT PNCP] Fetching pubblicitalegale avvisi (vehicle keyword filter)...")
    results: List[Dict[str, Any]] = []
    seen: set = set()
    date_from = from_dt.strftime("%d/%m/%Y")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Referer": "https://pubblicitalegale.anticorruzione.it/",
        "Origin": "https://pubblicitalegale.anticorruzione.it",
    }
    try:
        total_scanned = 0
        for page in range(max_pages):
            params = {
                "dataPubblicazioneStart": date_from,
                "page": page,
                "size": page_size,
                "codiceScheda": IT_PNCP_CODICE_SCHEDA,
                "sortField": "dataPubblicazione",
                "sortDirection": "DESC",
            }
            resp = session.get(IT_PNCP_AVVISI_URL, params=params, headers=headers, timeout=45)
            if resp.status_code != 200:
                msg = f"HTTP {resp.status_code}"
                LAST_FETCH_ERRORS["Italy PNCP"] = msg
                print(f"  [IT PNCP] page {page}: {msg}")
                break
            if not (resp.content or b"").startswith((b"{", b"[")):
                LAST_FETCH_ERRORS["Italy PNCP"] = "non-JSON response (portal/WAF?)"
                print("  [IT PNCP] non-JSON response")
                break
            data = resp.json() or {}
            content = data.get("content") or []
            if page == 0:
                print(f"  [IT PNCP] API totalElements≈{data.get('totalElements')}")
            if not content:
                break
            total_scanned += len(content)
            page_hits = 0
            for row in content:
                nid = str(row.get("idAvviso") or "")
                if not nid or nid in seen:
                    continue
                fields = _it_pncp_extract_list_fields(row)
                blob = f"{fields['title']} {fields['description']} {fields['blob']}".lower()
                if any(n in blob for n in IT_PNCP_NOISE):
                    continue
                if not match_keywords(blob, KEYWORDS_IT + KEYWORDS):
                    continue
                # Require a vehicle-ish stem so broad 'manutenzione' alone does not pass.
                vehicle_stems = (
                    "autocar", "automez", "autoveicol", "camion", "furgon", "pickup",
                    "pick-up", "pick up", "veicol", "parco auto", "parco mezzi",
                    "parco automez", "noleggio auto", "noleggio veicol", "isuzu",
                    "d-max", "chassis", "cassone", "4x4",
                )
                if not any(s in blob for s in vehicle_stems):
                    continue
                seen.add(nid)
                page_hits += 1
                detail = _it_pncp_enrich_detail(session, nid)
                cpv = detail.get("cpv") or fields["cpv"]
                buyer = detail.get("buyer") or fields["buyer"]
                value = detail.get("value") or fields["value"]
                url = detail.get("url") or (
                    f"https://pubblicitalegale.anticorruzione.it/dettaglio-avviso/{nid}"
                )
                title = fields["title"] or fields["description"][:200]
                pub = str(row.get("dataPubblicazione") or "")[:10]
                deadline = str(row.get("dataScadenza") or "")
                results.append(
                    {
                        "Source": "🇮🇹 IT-PNCP",
                        "Source Notice ID": nid,
                        "Lifecycle": classify_lifecycle(title, str(row.get("tipologia") or "")),
                        "Notice Type": str(row.get("tipologia") or ""),
                        "Procedure Type": str(row.get("codiceScheda") or ""),
                        "Buyer Type": "",
                        "Score": score_legacy(title),
                        "FleetSize": extract_fleet_size(title + " " + fields["description"]),
                        "Title": title,
                        "Buyer": buyer,
                        "CPV Code": cpv if re.fullmatch(r"[0-9]{8}", cpv or "") else "",
                        "CPV Desc": "" if re.fullmatch(r"[0-9]{8}", cpv or "") else (cpv or ""),
                        "Description": fields["description"][:500],
                        "Est. Value": value,
                        "Currency": "EUR",
                        "Published": pub,
                        "Deadline": deadline,
                        "Country": "Italy",
                        "Country Code": "ITA",
                        "URL": url,
                    }
                )
                time.sleep(0.15)
            print(f"  [IT PNCP] page {page}: scanned={len(content)} hits+={page_hits}")
            if data.get("last"):
                break
            time.sleep(0.25)
        LAST_FETCH_ERRORS["Italy PNCP"] = (
            None if results else f"zero vehicle-ish rows in {total_scanned} scanned notices"
        )
        print(f"[IT PNCP] Unique matches: {len(results)} (scanned≈{total_scanned})")
    except Exception as exc:
        LAST_FETCH_ERRORS["Italy PNCP"] = str(exc)
        print(f"  [IT PNCP] exception: {exc}")
    return results


# ---------------------------------------------------------------------------
# Romania SEAP / e-licitatie (below-threshold national) — public JSON API
# ---------------------------------------------------------------------------
RO_SEAP_LIST_URL = "https://www.e-licitatie.ro/api-pub/NoticeCommon/GetCNoticeList/"
RO_SEAP_NOTICE_URL = "https://www.e-licitatie.ro/pub/notices/c-notice/{cid}/view"
KEYWORDS_RO = [
    "autovehicul", "autovehicule", "autoutilitara", "autoutilitară", "autoutilitare",
    "camion", "camioane", "camioneta", "camionetă", "camionete", "autocamionet",
    "pickup", "pick-up", "vehicul", "vehicule", "flota", "flotă", "parcul auto",
    "chassis", "isuzu", "d-max", "d max", "basculant", "utilitara", "utilitară",
    "întreținere auto", "intretinere auto", "reparatii auto", "reparații auto",
    "reparare auto", "service auto", "n-series",
]
# Stems that must appear for keyword-only keeps (avoid toolkits / insurance noise).
RO_VEHICLE_STEMS = (
    "autovehicul", "autoutilit", "camion", "pickup", "pick-up", "vehicul",
    "flot", "chassis", "isuzu", "d-max", "basculant", "autocamion",
)
RO_CPV_PREFIXES = ("3413", "34113", "34136", "34134", "34144", "5011")


def _ro_cpv_code(cpv_field: str) -> str:
    m = re.search(r"\b(\d{8})\b", cpv_field or "")
    return m.group(1) if m else ""


def _ro_cpv_hit(cpv_field: str) -> bool:
    code = _ro_cpv_code(cpv_field)
    if not code:
        return False
    if code in CPV_CODES:
        return True
    for c in CPV_CODES:
        if len(c) >= 6 and code.startswith(c[:6]):
            return True
    return any(code.startswith(p) for p in RO_CPV_PREFIXES)


def fetch_romania_seap(
    session: requests.Session,
    from_dt: datetime,
    *,
    page_size: int = 100,
    max_pages: int = 25,
) -> List[Dict[str, Any]]:
    """National RO notices via e-licitatie public NoticeCommon JSON (client-side vehicle filter).

    API ignores most query filters — paginate by publication date window and filter locally.
    """
    print("\n[RO SEAP] Fetching e-licitatie NoticeCommon list (vehicle CPV/keyword)...")
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    LAST_FETCH_ERRORS["Romania SEAP"] = None
    cutoff = from_dt.strftime("%Y-%m-%d")
    end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://www.e-licitatie.ro",
        "Referer": "https://www.e-licitatie.ro/pub/notices/c-notice/list/0/1",
    }
    try:
        total_scanned = 0
        for page in range(max_pages):
            body = {
                "pageSize": page_size,
                "pageIndex": page,
                "startPublicationDate": cutoff,
                "endPublicationDate": end,
            }
            resp = session.post(RO_SEAP_LIST_URL, json=body, headers=headers, timeout=45)
            if resp.status_code != 200:
                msg = f"HTTP {resp.status_code}"
                LAST_FETCH_ERRORS["Romania SEAP"] = msg
                print(f"  [RO SEAP] page {page}: {msg}")
                break
            if not (resp.content or b"").startswith((b"{", b"[")):
                LAST_FETCH_ERRORS["Romania SEAP"] = "non-JSON response"
                print("  [RO SEAP] non-JSON response")
                break
            data = resp.json() or {}
            items = data.get("items") or []
            if page == 0:
                print(f"  [RO SEAP] API total≈{data.get('total')}")
            if not items:
                break
            total_scanned += len(items)
            page_hits = 0
            for it in items:
                cid = str(it.get("cNoticeId") or it.get("noticeId") or "")
                if not cid or cid in seen:
                    continue
                title = str(it.get("contractTitle") or "").strip()
                cpv_raw = str(it.get("cpvCodeAndName") or "")
                buyer = str(it.get("contractingAuthorityNameAndFN") or "")
                # Strip leading CUI / numeric prefix from buyer
                buyer = re.sub(r"^\d+\s*-\s*", "", buyer).strip()
                blob = f"{title} {cpv_raw} {buyer}".lower()
                cpv_ok = _ro_cpv_hit(cpv_raw)
                stem_ok = any(s in blob for s in RO_VEHICLE_STEMS)
                kw_ok = stem_ok and match_keywords(blob, KEYWORDS_RO + KEYWORDS)
                if not cpv_ok and not kw_ok:
                    continue
                # Hard skip postal/courier utilitare here — not-for-us also catches downstream
                if re.search(r"(?i)\bpo[sș]ta\b|courier|curierat", blob) and (
                    "utilitar" in blob or "van" in blob or "34136" in cpv_raw
                ):
                    continue
                seen.add(cid)
                page_hits += 1
                pub = str(it.get("noticeStateDate") or "")[:10]
                deadline = str(it.get("maxTenderReceiptDeadline") or it.get("minTenderReceiptDeadline") or "")[:10]
                value = it.get("estimatedValueRon")
                value_s = "" if value in (None, "") else str(value)
                cpv = _ro_cpv_code(cpv_raw)
                results.append(
                    {
                        "Source": "🇷🇴 RO-SEAP",
                        "Source Notice ID": str(it.get("noticeNo") or cid),
                        "Lifecycle": "",
                        "Notice Type": str((it.get("sysProcedureType") or {}).get("text") or ""),
                        "Procedure Type": str((it.get("sysAcquisitionContractType") or {}).get("text") or ""),
                        "Buyer Type": "",
                        "Score": "",
                        "FleetSize": "",
                        "Title": title or cid,
                        "Buyer": buyer,
                        "Country": "Romania",
                        "Country Code": "ROU",
                        "Published": pub,
                        "Deadline": deadline,
                        "Value": value_s,
                        "Currency": "RON",
                        "CPV Code": cpv,
                        "CPV Desc": cpv_raw[:120],
                        "URL": RO_SEAP_NOTICE_URL.format(cid=cid),
                        "Description": title[:2000],
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
                        "Reasons": f"ro_cNoticeId={cid}; cpv_hit={cpv_ok}; kw_hit={kw_ok}",
                    }
                )
            print(f"  [RO SEAP] page {page}: scanned={len(items)} hits+={page_hits}")
            if len(items) < page_size:
                break
            time.sleep(0.2)
        LAST_FETCH_ERRORS["Romania SEAP"] = (
            None if results else f"zero vehicle-ish rows in {total_scanned} scanned notices"
        )
        print(f"[RO SEAP] Unique matches: {len(results)} (scanned≈{total_scanned})")
    except Exception as exc:
        LAST_FETCH_ERRORS["Romania SEAP"] = str(exc)
        print(f"  [RO SEAP] exception: {exc}")
    return results


# ---------------------------------------------------------------------------
# Austria USP Ausschreibungssuche (Kerndaten aggregator) — public JSON API
# ---------------------------------------------------------------------------
AT_USP_LIST_URL = (
    "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/api/tenderlist"
)
AT_USP_DETAIL_TMPL = (
    "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/"
    "{kind}-detail?object={oid}"
)
# CPV chips available on USP UI that map to vehicles / special vehicles / R&M parents.
AT_USP_CPV_LIST = [
    "34000000",
    "34100000",
    "34130000",
    "34131000",
    "34140000",
    "34144000",
    "34144210",
    "50110000",
    "50114000",
]
KEYWORDS_AT = [
    "lkw", "nkw", "nutzfahrzeug", "pritsche", "fahrgestell", "pickup", "pick-up",
    "kipper", "lastwagen", "isuzu", "d-max", "d max", "elektrofahrzeug",
    "betriebsfahrzeug", "dienstfahrzeug", "müllsammel", "muellsammel",
    "rahmenvereinbarung fahrzeug", "lieferung von elektro", "man tgs", "man tgl",
]


def fetch_austria_usp(
    session: requests.Session,
    from_dt: datetime,
    *,
    page_size: int = 100,
    max_pages: int = 20,
) -> List[Dict[str, Any]]:
    """National AT notices via USP Ausschreibungssuche DataTables JSON (CPV-filtered).

    Server-side search[value] is ignored; use cpvList + fromdate/todate, then
    client keyword / noise gate downstream.
    """
    print("\n[AT USP] Fetching Ausschreibungssuche tenderlist (vehicle CPV window)...")
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    LAST_FETCH_ERRORS["Austria USP"] = None
    cutoff = from_dt.strftime("%Y-%m-%d")
    end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": (
            "https://ausschreibungen.usp.gv.at/at.gv.bmdw.eproc-p/public/tenderlist"
        ),
    }
    try:
        total_scanned = 0
        for page in range(max_pages):
            params: List[Tuple[str, Any]] = [
                ("draw", page + 1),
                ("start", page * page_size),
                ("length", page_size),
                ("orderColumn", 2),
                ("orderDir", "desc"),
                ("fromdate", cutoff),
                ("todate", end),
            ]
            for cpv in AT_USP_CPV_LIST:
                params.append(("cpvList", cpv))
            resp = session.get(AT_USP_LIST_URL, params=params, headers=headers, timeout=45)
            if resp.status_code != 200:
                msg = f"HTTP {resp.status_code}"
                LAST_FETCH_ERRORS["Austria USP"] = msg
                print(f"  [AT USP] page {page}: {msg}")
                break
            if not (resp.content or b"").startswith((b"{", b"[")):
                LAST_FETCH_ERRORS["Austria USP"] = "non-JSON response"
                print("  [AT USP] non-JSON response")
                break
            data = resp.json() or {}
            items = data.get("data") or []
            if page == 0:
                print(f"  [AT USP] API filtered≈{data.get('recordsFiltered')}")
            if not items:
                break
            total_scanned += len(items)
            page_hits = 0
            stop_old = False
            for it in items:
                if not isinstance(it, list) or len(it) < 5:
                    continue
                title = str(it[0] or "").strip()
                buyer = str(it[1] or "").strip()
                pub = str(it[2] or "")[:10]
                deadline = str(it[3] or "")[:10] if it[3] else ""
                oid = str(it[4] or "").strip()
                is_notice = bool(it[5]) if len(it) > 5 else False
                if pub and pub < cutoff:
                    stop_old = True
                    continue
                if not oid or oid in seen:
                    continue
                blob = f"{title} {buyer}".lower()
                # CPV list already scopes; still require a light vehicle/fleet stem
                # so pure non-vehicle chips under 34000000 don't flood the desk.
                if not match_keywords(blob, KEYWORDS_AT + KEYWORDS_DE + KEYWORDS):
                    # Keep generic goods titles from CPV-only when clearly a vehicle buy
                    if not re.search(
                        r"(?i)\bfahrzeug|lkw|nkw|elektro|transporter|pritsche|"
                        r"kipper|m[uü]ll|pickup|nutz",
                        blob,
                    ):
                        continue
                seen.add(oid)
                page_hits += 1
                kind = "notice" if is_notice else "tender"
                results.append(
                    {
                        "Source": "🇦🇹 AT-USP",
                        "Source Notice ID": oid,
                        "Title": title,
                        "Buyer": buyer,
                        "Published": pub,
                        "Deadline": deadline,
                        "Country": "Austria",
                        "Country Code": "AUT",
                        "URL": AT_USP_DETAIL_TMPL.format(kind=kind, oid=oid),
                        "Description": title,
                        "CPV Code": "",
                        "CPV Desc": "",
                    }
                )
            print(f"  [AT USP] page {page}: scanned={len(items)} hits+={page_hits}")
            if stop_old or len(items) < page_size:
                break
            time.sleep(0.55)  # USP client rate-limits pagination ~500ms
        LAST_FETCH_ERRORS["Austria USP"] = (
            None if results else f"zero vehicle-ish rows in {total_scanned} scanned notices"
        )
        print(f"[AT USP] Unique matches: {len(results)} (scanned≈{total_scanned})")
    except Exception as exc:
        LAST_FETCH_ERRORS["Austria USP"] = str(exc)
        print(f"  [AT USP] exception: {exc}")
    return results


# ---------------------------------------------------------------------------
# Portugal BASE — dados.gov.pt open JSON (anúncios) — no IMPIC token needed
# ---------------------------------------------------------------------------
PT_DADOS_ANUNCIOS_META = (
    "https://dados.gov.pt/api/1/datasets/"
    "contratos-publicos-portal-base-impic-anuncios-de-2012-a-2026/"
)
# Tight CV / fleet R&M / parts — not bare "manutenção" (IT systems noise).
PT_CORE_RE = re.compile(
    r"(?i)"
    r"(?:aquisi[cç][aã]o|fornecimento|aluguer|loca[cç][aã]o|leasing|frota)"
    r".{0,50}"
    r"(?:ve[ií]culo|viatura|cami[aã]o|pickup|pick-up|chassi|chassis|"
    r"autocarro comercial|ligeiro(?:s)? de mercadorias)"
    r"|"
    r"(?:ve[ií]culo|viatura|cami[aã]o|pickup|chassi).{0,40}"
    r"(?:ligeiro|pesado|comercial|todo.?o.?terreno|basculante|caixa)"
    r"|"
    r"isuzu|d-max|d max|"
    r"manuten[cç][aã]o (?:de )?(?:ve[ií]culo|viatura|frota|autom[oó]vel)|"
    r"assist[eê]ncia (?:t[eé]cnica )?(?:de )?(?:ve[ií]culo|viatura)|"
    r"oficina (?:de )?ve[ií]culo|"
    r"pe[cç]as (?:para )?(?:ve[ií]culo|viatura)|"
    r"repara[cç][aã]o de (?:ve[ií]culo|viatura)|"
    r"parque (?:de )?viatura|frota (?:de )?(?:ve[ií]culo|viatura|autom)"
)
PT_NOISE_RE = re.compile(
    r"(?i)e-?learning|avac|jardim|floreira|software|plataforma digital|"
    r"transporte de alunos|seguro|motociclo(?!.*(?:ve[ií]culo|viatura|cami))"
)
KEYWORDS_PT = [
    "veículo", "veiculo", "viatura", "viaturas", "camião", "camiao", "camiões",
    "pickup", "pick-up", "chassis", "chassi", "frota", "isuzu", "d-max",
    "ligeiro de mercadorias", "pesado", "basculante", "manutenção de viaturas",
    "manutencao de viaturas", "manutenção de veículos", "peças para viaturas",
]


def _pt_parse_pub(s: str) -> Optional[datetime]:
    try:
        d, m, y = str(s).strip().split("/")
        return datetime(int(y), int(m), int(d), tzinfo=timezone.utc)
    except Exception:
        return None


def _pt_cpv(raw: Any) -> str:
    if isinstance(raw, list):
        text = ";".join(str(x) for x in raw if x)
    else:
        text = str(raw or "")
    codes = re.findall(r"\b(\d{8})\b", text)
    return ";".join(codes[:6])


def fetch_portugal_base(session: requests.Session, from_dt: datetime) -> List[Dict[str, Any]]:
    """National PT anúncios via dados.gov.pt BASE JSON dump (free; no APIBase2 token)."""
    print("\n[PT BASE] Fetching dados.gov anúncios JSON (vehicle/fleet keyword)...")
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    LAST_FETCH_ERRORS["Portugal BASE"] = None
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }
    try:
        meta = session.get(PT_DADOS_ANUNCIOS_META, headers=headers, timeout=60)
        if meta.status_code != 200:
            LAST_FETCH_ERRORS["Portugal BASE"] = f"meta HTTP {meta.status_code}"
            print(f"  [PT BASE] meta HTTP {meta.status_code}")
            return []
        resources = (meta.json() or {}).get("resources") or []
        years_needed = {from_dt.year, datetime.now(timezone.utc).year}
        year_urls: Dict[int, str] = {}
        for res in resources:
            title = str(res.get("title") or "")
            m = re.search(r"anuncios(\d{4})\.json", title, flags=re.I)
            if not m:
                continue
            y = int(m.group(1))
            if y in years_needed and res.get("url"):
                year_urls[y] = res["url"]
        if not year_urls:
            LAST_FETCH_ERRORS["Portugal BASE"] = "no anunciosYYYY.json resources on dados.gov"
            print("  [PT BASE] no year JSON resources found")
            return []
        scanned = 0
        for y in sorted(year_urls):
            url = year_urls[y]
            print(f"  [PT BASE] downloading anuncios{y}.json …")
            resp = session.get(url, headers=headers, timeout=180)
            if resp.status_code != 200:
                print(f"  [PT BASE] year {y}: HTTP {resp.status_code}")
                continue
            try:
                rows = resp.json()
            except Exception as exc:
                print(f"  [PT BASE] year {y}: JSON parse fail {exc}")
                continue
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                scanned += 1
                pub_dt = _pt_parse_pub(str(row.get("dataPublicacao") or ""))
                if pub_dt and pub_dt < from_dt:
                    continue
                title = extract_text(row.get("descricaoAnuncio"))
                buyer = extract_text(row.get("designacaoEntidade"))
                cpv = _pt_cpv(row.get("CPVs"))
                tipos = extract_text(row.get("tiposContrato"))
                blob = " ".join([title, tipos, cpv, extract_text(row.get("modeloAnuncio"))])
                if not PT_CORE_RE.search(blob):
                    continue
                if PT_NOISE_RE.search(blob) and not re.search(
                    r"(?i)(?:aquisi[cç].{0,30}(?:ve[ií]culo|viatura|cami)|frota|isuzu|pickup|chassi|pesado)",
                    blob,
                ):
                    continue
                if cpv_is_excluded(cpv):
                    continue
                nid = str(row.get("IdIncm") or row.get("nAnuncio") or "")
                if nid and nid in seen:
                    continue
                if nid:
                    seen.add(nid)
                deadline = extract_text(row.get("DataLimitePropostas") or row.get("PrazoPropostas"))
                link = extract_text(row.get("url") or row.get("PecasProcedimento"))
                if not link and nid:
                    link = f"https://www.base.gov.pt/Base4/pt/detalhe/?type=anuncios&id={nid}"
                val = row.get("PrecoBase") or ""
                results.append(
                    {
                        "Source": "🇵🇹 PT-BASE",
                        "Source Notice ID": nid or str(row.get("nAnuncio") or ""),
                        "Lifecycle": classify_lifecycle(blob, extract_text(row.get("tipoActo"))),
                        "Notice Type": extract_text(row.get("tipoActo") or row.get("modeloAnuncio")),
                        "Procedure Type": "",
                        "Buyer Type": "",
                        "Score": score_legacy(title, parse_number(val)),
                        "FleetSize": extract_fleet_size(title),
                        "Title": title,
                        "Buyer": buyer,
                        "CPV Code": cpv,
                        "CPV Desc": "",
                        "Description": title,
                        "Est. Value": val,
                        "Currency": "EUR",
                        "Published": pub_dt.strftime("%Y-%m-%d") if pub_dt else extract_text(row.get("dataPublicacao")),
                        "Deadline": deadline,
                        "Country": "Portugal",
                        "Country Code": "PRT",
                        "URL": link,
                    }
                )
        LAST_FETCH_ERRORS["Portugal BASE"] = (
            None if results else f"zero vehicle-ish rows in {scanned} scanned anúncios"
        )
        print(f"[PT BASE] Matches: {len(results)} (scanned≈{scanned})")
    except Exception as exc:
        LAST_FETCH_ERRORS["Portugal BASE"] = str(exc)
        print(f"  [PT BASE] exception: {exc}")
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
    fr_rows: Optional[List[Dict[str, Any]]] = None,
    pl_rows: Optional[List[Dict[str, Any]]] = None,
    iec_rows: Optional[List[Dict[str, Any]]] = None,
    es_rows: Optional[List[Dict[str, Any]]] = None,
    it_rows: Optional[List[Dict[str, Any]]] = None,
    de_ov_rows: Optional[List[Dict[str, Any]]] = None,
    ro_rows: Optional[List[Dict[str, Any]]] = None,
    at_rows: Optional[List[Dict[str, Any]]] = None,
    pt_rows: Optional[List[Dict[str, Any]]] = None,
) -> None:
    wb = openpyxl.Workbook()

    def write_sheet(ws, rows: List[Dict[str, Any]], empty_msg: str) -> None:
        ws.append(EXPORT_HEADERS)
        if rows:
            for row in rows:
                ws.append([row.get(h, "") for h in EXPORT_HEADERS])
        # Phase 1: do NOT write placeholder text as a fake notice row.
        # empty_msg retained for API compat / logging only.
        _ = empty_msg

    ws_uk = wb.active
    ws_uk.title = "UK Tenders"
    write_sheet(ws_uk, normalize_batch(uk_rows, "🇬🇧 UK"), "No UK results found")

    ws_cf = wb.create_sheet("UK Contracts Finder")
    write_sheet(ws_cf, normalize_batch(cf_rows, "🇬🇧 UK-CF"), "No Contracts Finder results — check API availability")

    ws_ted = wb.create_sheet("EU TED Tenders")
    write_sheet(ws_ted, normalize_batch(ted_rows, "🇪🇺 EU"), "No TED results found")

    ws_de = wb.create_sheet("Germany National")
    write_sheet(ws_de, normalize_batch(de_rows, "🇩🇪 DE"), "No DE national results — DTVP portal may require browser access. TED covers DE above-threshold contracts.")

    de_ov_rows = de_ov_rows or []
    ws_de_ov = wb.create_sheet("Germany OV")
    write_sheet(
        ws_de_ov,
        normalize_batch(de_ov_rows, "🇩🇪 DE-OV"),
        "No DE oeffentlichevergabe Open Data vehicle matches",
    )

    ws_doffin = wb.create_sheet("Norway Doffin")
    write_sheet(
        ws_doffin,
        normalize_batch(doffin_rows, "🇳🇴 Norway"),
        "No results — set ISZE_DOFFIN_API_KEY in nordics_api_keys.env (see NORDICS_API_KEYS.md)",
    )

    ws_hilma = wb.create_sheet("Finland HILMA")
    write_sheet(
        ws_hilma,
        normalize_batch(hilma_rows, "🇫🇮 Finland"),
        "No results — set ISZE_HILMA_API_KEY in nordics_api_keys.env (see NORDICS_API_KEYS.md)",
    )

    ws_il = wb.create_sheet("Israel Tenders")
    write_sheet(ws_il, normalize_batch(il_rows, "🇮🇱 Israel"), "No Israel results found")

    iec_rows = iec_rows or []
    ws_iec = wb.create_sheet("IEC Israel")
    write_sheet(
        ws_iec,
        normalize_batch(iec_rows, "🇮🇱 IEC Israel"),
        "No IEC vehicle-keyword hits — domestic portal may be GEO_BLOCKED",
    )

    ws_be = wb.create_sheet("Belgium")
    write_sheet(ws_be, normalize_batch(be_rows, "🇧🇪 BE"), "No Belgium SEA API results — TED covers above-threshold BE")

    ws_nl = wb.create_sheet("Netherlands")
    write_sheet(ws_nl, normalize_batch(nl_rows, "🇳🇱 NL"), "No TenderNed RSS results — check tenderned.nl feed")

    fr_rows = fr_rows or []
    pl_rows = pl_rows or []
    es_rows = es_rows or []
    it_rows = it_rows or []
    if fr_rows is not None:
        ws_fr = wb.create_sheet("France BOAMP")
        write_sheet(ws_fr, normalize_batch(fr_rows, "🇫🇷 FR-BOAMP"), "No FR BOAMP results")
    if pl_rows is not None:
        ws_pl = wb.create_sheet("Poland BZP")
        write_sheet(ws_pl, normalize_batch(pl_rows, "🇵🇱 PL-BZP"), "No PL BZP results")
    if es_rows is not None:
        ws_es = wb.create_sheet("Spain PLACSP")
        write_sheet(ws_es, normalize_batch(es_rows, "🇪🇸 ES-PLACSP"), "No ES PLACSP results")
    if it_rows is not None:
        ws_it = wb.create_sheet("Italy PNCP")
        write_sheet(ws_it, normalize_batch(it_rows, "🇮🇹 IT-PNCP"), "No IT PNCP results")
    ro_rows = ro_rows or []
    if ro_rows is not None:
        ws_ro = wb.create_sheet("Romania SEAP")
        write_sheet(ws_ro, normalize_batch(ro_rows, "🇷🇴 RO-SEAP"), "No RO SEAP results")
    at_rows = at_rows or []
    if at_rows is not None:
        ws_at = wb.create_sheet("Austria USP")
        write_sheet(ws_at, normalize_batch(at_rows, "🇦🇹 AT-USP"), "No AT USP results")
    pt_rows = pt_rows or []
    if pt_rows is not None:
        ws_pt = wb.create_sheet("Portugal BASE")
        write_sheet(ws_pt, normalize_batch(pt_rows, "🇵🇹 PT-BASE"), "No PT BASE results")

    wb.save(filename)
    print(f"\n✓ Saved: {filename}")
    print(f"  UK (Find a Tender): {len(uk_rows)}")
    print(f"  UK (Contracts Finder): {len(cf_rows)}")
    print(f"  TED EU:   {len(ted_rows)}")
    print(f"  Germany:  {len(de_rows)} (service.bund) + {len(de_ov_rows)} (oeffentlichevergabe) + TED above-threshold")
    print(f"  Norway:   {len(doffin_rows)}")
    print(f"  Finland:  {len(hilma_rows)}")
    print(f"  Israel:   {len(il_rows)}")
    print(f"  IEC Israel: {len(iec_rows)}")
    print(f"  Belgium:  {len(be_rows)}")
    print(f"  Netherlands: {len(nl_rows)}")
    print(f"  France BOAMP: {len(fr_rows)}")
    print(f"  Poland BZP: {len(pl_rows)}")
    print(f"  Spain PLACSP: {len(es_rows)}")
    print(f"  Italy PNCP: {len(it_rows)}")
    print(f"  Romania SEAP: {len(ro_rows)}")
    print(f"  Austria USP: {len(at_rows)}")
    print(f"  Portugal BASE: {len(pt_rows)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _record_iec_health(health: dict, iec_rows: List) -> None:
    domestic_err = LAST_FETCH_ERRORS.get("IEC iec.co.il domestic")
    record_source_status(
        health,
        "IEC iec.co.il domestic",
        "SKIPPED",
        count=0,
        last_error=domestic_err
        or "GEO_BLOCKED — domestic supplier tenders not reachable from abroad",
        note="vehicle/leasing tenders for UMI chase live here; abroad use IEC global-iec.com",
    )
    global_err = LAST_FETCH_ERRORS.get("IEC global-iec.com")
    raw = LAST_FETCH_ERRORS.get("IEC global-iec.com raw_count")
    try:
        raw_n = int(raw) if raw else 0
    except ValueError:
        raw_n = 0
    if global_err:
        record_source_result(health, "IEC global-iec.com", 0, global_err)
    else:
        # Count = parsed international cards (endpoint alive). Vehicle survivors tracked in note.
        record_source_status(
            health,
            "IEC global-iec.com",
            "OK" if raw_n > 0 else "SUSPECT",
            count=raw_n,
            last_error=None,
            note=(
                f"HTML list only (no RSS/API). Vehicle-keyword + Isuzu-gate survivors this run: "
                f"{len(iec_rows)}. Domestic vehicle packs remain on GEO_BLOCKED iec.co.il."
            ),
        )


def _record_be_il_health(
    health: dict,
    be_rows: Optional[List] = None,
    il_rows: Optional[List] = None,
) -> None:
    if be_rows is not None:
        be_err = LAST_FETCH_ERRORS.get("Belgium publicprocurement.be")
        if be_rows:
            record_source_result(health, "Belgium publicprocurement.be", len(be_rows), None)
        else:
            record_source_result(
                health,
                "Belgium publicprocurement.be",
                0,
                be_err or "zero publications matched",
            )
        # RSS is retired — never BROKEN when live SEA is the primary path
        record_source_status(
            health,
            "Belgium RSS",
            "RETIRED",
            count=0,
            last_error=LAST_FETCH_ERRORS.get("Belgium RSS")
            or "RETIRED — HTML SPA; live = Belgium publicprocurement.be SEA",
            note="ignored; replacement OK when Belgium publicprocurement.be is OK",
        )

    if il_rows is None:
        return

    il_live_err = LAST_FETCH_ERRORS.get("Israel mr.gov.il")
    ckan_note = LAST_FETCH_ERRORS.get("Israel data.gov.il")

    if not il_live_err and il_rows:
        record_source_result(health, "Israel mr.gov.il", len(il_rows), None)
        record_source_status(
            health,
            "Israel data.gov.il",
            "SUSPECT",
            count=0,
            last_error=ckan_note or "demoted — live mr.gov.il succeeded; CKAN frozen Feb 2021",
            note="secondary only; datastore frozen Feb 2021 — not competing with live OK",
        )
    elif il_live_err and il_rows:
        record_source_result(health, "Israel mr.gov.il", 0, il_live_err)
        record_source_status(
            health,
            "Israel data.gov.il",
            "SUSPECT",
            count=len(il_rows),
            last_error=None,
            note="secondary fallback used (live failed); CKAN frozen Feb 2021",
        )
    else:
        record_source_result(
            health,
            "Israel mr.gov.il",
            0,
            il_live_err or "zero live matches",
        )
        record_source_status(
            health,
            "Israel data.gov.il",
            "SUSPECT",
            count=0,
            last_error=ckan_note or "demoted — prefer mr.gov.il; CKAN frozen Feb 2021",
            note="CKAN frozen Feb 2021 — secondary only",
        )

    record_source_status(
        health,
        "Israel RSS",
        "RETIRED",
        count=0,
        last_error=LAST_FETCH_ERRORS.get("Israel RSS")
        or "RETIRED — HTML SPA shell, 0 <item>; live = Israel mr.gov.il",
        note="ignored; replacement OK when Israel mr.gov.il is OK",
    )


def _awaiting_key_msg(source: str) -> str:
    if source == "doffin":
        return (
            "AWAITING_KEY — set ISZE_DOFFIN_API_KEY in nordics_api_keys.env "
            "(see NORDICS_API_KEYS.md); not a broken endpoint"
        )
    return (
        "AWAITING_KEY — set ISZE_HILMA_API_KEY in nordics_api_keys.env "
        "(see NORDICS_API_KEYS.md); not a broken endpoint"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="ISZE Tender Monitor v3")
    parser.add_argument(
        "--only",
        default="",
        help="Comma-separated source subset: bel,isr,iec,fr,pl,es,it,de,ov,ro,at,pt,nordics (skip TED/UK/etc)",
    )
    args = parser.parse_args()
    only = {x.strip().lower() for x in args.only.split(",") if x.strip()}
    focused = bool(only)

    print("=" * 60)
    print("  ISZE TENDER MONITOR v3")
    if focused:
        print(f"  FOCUSED scrape: {', '.join(sorted(only))}")
    print(
        f"  Last {LOOKBACK_DAYS} days | Markets: UK, EU/TED, DE(+OV), BE, NL, FR, PL, ES, IT, RO, "
        "Norway, Finland, Israel, IEC"
    )
    print(f"  CPV codes: {len(CPV_CODES)} (surgical — ISZE targets only)")
    print(f"  TED country filter: {len(TED_TARGET_COUNTRIES)} markets (incl. CYP, MLT)")
    print(
        f"  TED detail fetch: {'ON' if TED_FETCH_DETAIL else 'OFF'} "
        f"(cap={TED_DETAIL_CAP}, delay={TED_DETAIL_DELAY}s; set ISZE_TED_FETCH_DETAIL=1 to enable)"
    )
    print("=" * 60)

    now = datetime.now(timezone.utc)
    from_dt = now - timedelta(days=LOOKBACK_DAYS)
    health = load_health()

    uk_rows: List[Dict[str, Any]] = []
    cf_rows: List[Dict[str, Any]] = []
    ted_rows: List[Dict[str, Any]] = []
    de_rows: List[Dict[str, Any]] = []
    de_ov_rows: List[Dict[str, Any]] = []
    be_rows: List[Dict[str, Any]] = []
    nl_rows: List[Dict[str, Any]] = []
    doffin_rows: List[Dict[str, Any]] = []
    hilma_rows: List[Dict[str, Any]] = []
    il_rows: List[Dict[str, Any]] = []
    iec_rows: List[Dict[str, Any]] = []
    fr_rows: List[Dict[str, Any]] = []
    pl_rows: List[Dict[str, Any]] = []
    es_rows: List[Dict[str, Any]] = []
    it_rows: List[Dict[str, Any]] = []
    ro_rows: List[Dict[str, Any]] = []
    at_rows: List[Dict[str, Any]] = []
    pt_rows: List[Dict[str, Any]] = []

    run_all = not focused
    run_be = run_all or ("bel" in only or "be" in only or "belgium" in only)
    run_il = run_all or ("isr" in only or "il" in only or "israel" in only)
    run_iec = run_all or ("iec" in only or "umi" in only)
    run_de = run_all or ("de" in only or "germany" in only or "bund" in only)
    run_de_ov = run_all or (
        "ov" in only
        or "de-ov" in only
        or "bkms" in only
        or "oeffentlichevergabe" in only
        or "de" in only
        or "germany" in only
    )
    run_nordics = run_all or (
        "nordics" in only or "doffin" in only or "hilma" in only or "no" in only or "fi" in only
    )
    # FR/PL/ES/IT/RO/AT national below-threshold — weekly bat + --only …
    run_fr = run_all or ("fr" in only or "france" in only or "boamp" in only)
    run_pl = run_all or ("pl" in only or "poland" in only or "bzp" in only)
    run_es = run_all or ("es" in only or "spain" in only or "placsp" in only)
    run_it = run_all or ("it" in only or "italy" in only or "pncp" in only)
    run_ro = run_all or ("ro" in only or "romania" in only or "seap" in only)
    run_at = run_all or ("at" in only or "austria" in only or "usp" in only)
    run_pt = run_all or ("pt" in only or "portugal" in only or "base" in only)
    if "frpl" in only or "below" in only:
        run_fr = True
        run_pl = True
    if "med" in only or "esit" in only:
        run_es = True
        run_it = True
    # --only ov → OV only (not bund); --only de → both
    if focused and ("ov" in only or "de-ov" in only or "bkms" in only or "oeffentlichevergabe" in only):
        if "de" not in only and "germany" not in only and "bund" not in only:
            run_de = False

    with requests.Session() as session:
        session.headers.setdefault(
            "User-Agent",
            "Mozilla/5.0 (compatible; ISZE-TenderMonitor/3.0; +internal)",
        )

        if run_all:
            uk_rows = fetch_uk(session, from_dt, now)
            record_source_result(health, "UK Find a Tender", len(uk_rows), None if uk_rows is not None else "failed")

            cf_rows = fetch_contracts_finder(session, from_dt)
            record_source_result(health, "UK Contracts Finder", len(cf_rows), None)

            ted_rows = fetch_ted(session, from_dt)
            record_source_result(health, "TED Europa", len(ted_rows), None if ted_rows else "zero TED results")

            nl_rows = fetch_netherlands(session, from_dt)
            record_source_result(health, "Netherlands TenderNed", len(nl_rows), None if nl_rows else "zero matches")

        if run_de:
            de_rows = fetch_germany(session, from_dt)
            bund_err = LAST_FETCH_ERRORS.get("Germany service.bund")
            record_source_result(health, "Germany service.bund", len(de_rows), bund_err)
            record_source_status(
                health,
                "Germany DTVP/NRW",
                "RETIRED",
                count=0,
                last_error=LAST_FETCH_ERRORS.get("Germany DTVP/NRW")
                or "RETIRED — TED-only + service.bund + oeffentlichevergabe; DTVP no free public feed",
                note="not an active fetcher; paid DTVP Professional Edition would be needed for that portal",
            )

        if run_de_ov:
            de_ov_rows = fetch_germany_ov(session, from_dt)
            record_source_result(
                health,
                "Germany oeffentlichevergabe",
                len(de_ov_rows),
                LAST_FETCH_ERRORS.get("Germany oeffentlichevergabe"),
            )
            if not run_de:
                record_source_status(
                    health,
                    "Germany DTVP/NRW",
                    "RETIRED",
                    count=0,
                    last_error=LAST_FETCH_ERRORS.get("Germany DTVP/NRW")
                    or "RETIRED — TED-only + service.bund + oeffentlichevergabe; DTVP no free public feed",
                    note="not an active fetcher; paid DTVP Professional Edition would be needed for that portal",
                )

        if run_nordics:
            doffin_rows = fetch_doffin(session, from_dt)
            if not get_doffin_key():
                record_source_status(
                    health,
                    "Norway Doffin",
                    "AWAITING_KEY",
                    count=0,
                    last_error=_awaiting_key_msg("doffin"),
                    note="create nordics_api_keys.env from example; see NORDICS_API_KEYS.md",
                )
            else:
                err = LAST_FETCH_ERRORS.get("Norway Doffin")
                record_source_result(health, "Norway Doffin", len(doffin_rows), err)

            hilma_rows = fetch_hilma(session, from_dt)
            if not get_hilma_key():
                record_source_status(
                    health,
                    "Finland HILMA",
                    "AWAITING_KEY",
                    count=0,
                    last_error=_awaiting_key_msg("hilma"),
                    note="create nordics_api_keys.env from example; see NORDICS_API_KEYS.md",
                )
            else:
                err = LAST_FETCH_ERRORS.get("Finland HILMA")
                # 403 with a key = wrong product / not AVP-Read — CODE_READY, not BROKEN vanity.
                if err and "403" in str(err):
                    record_source_status(
                        health,
                        "Finland HILMA",
                        "CODE_READY",
                        count=0,
                        last_error=(
                            "HTTP 403 Forbidden — key present but AVP-Read product not authorized. "
                            "Re-subscribe AVP-Read on hns-hilma-prod-apim.developer.azure-api.net "
                            "and paste Primary key into nordics_api_keys.env"
                        ),
                        note="fetcher ready; unblock = correct AVP-Read subscription key",
                    )
                else:
                    record_source_result(health, "Finland HILMA", len(hilma_rows), err)

        if run_be:
            be_rows = fetch_belgium(session, from_dt)
            fetch_belgium_rss_probe(session)

        if run_il:
            il_rows = fetch_israel(session)

        if run_iec:
            iec_rows = fetch_iec_israel(session)
            _record_iec_health(health, iec_rows)

        if run_fr:
            fr_rows = fetch_france_boamp(session, from_dt)
            record_source_result(
                health, "France BOAMP", len(fr_rows), LAST_FETCH_ERRORS.get("France BOAMP")
            )

        if run_pl:
            pl_rows = fetch_poland_bzp(session, from_dt)
            record_source_result(
                health, "Poland BZP", len(pl_rows), LAST_FETCH_ERRORS.get("Poland BZP")
            )

        if run_es:
            es_rows = fetch_spain_placsp(session, from_dt)
            es_err = LAST_FETCH_ERRORS.get("Spain PLACSP")
            if es_err and "WAF_BLOCKED" in es_err:
                record_source_status(
                    health,
                    "Spain PLACSP",
                    "CODE_READY",
                    count=0,
                    last_error=es_err,
                    note=(
                        "Official Atom/ZIP syndication documented; this runner is WAF-denied. "
                        "Not BROKEN — retry when egress/session allows."
                    ),
                )
            else:
                record_source_result(health, "Spain PLACSP", len(es_rows), es_err)

        if run_it:
            it_rows = fetch_italy_pncp(session, from_dt)
            record_source_result(
                health, "Italy PNCP", len(it_rows), LAST_FETCH_ERRORS.get("Italy PNCP")
            )

        if run_ro:
            ro_rows = fetch_romania_seap(session, from_dt)
            record_source_result(
                health, "Romania SEAP", len(ro_rows), LAST_FETCH_ERRORS.get("Romania SEAP")
            )

        if run_at:
            at_rows = fetch_austria_usp(session, from_dt)
            record_source_result(
                health, "Austria USP", len(at_rows), LAST_FETCH_ERRORS.get("Austria USP")
            )

        if run_pt:
            pt_rows = fetch_portugal_base(session, from_dt)
            record_source_result(
                health, "Portugal BASE", len(pt_rows), LAST_FETCH_ERRORS.get("Portugal BASE")
            )

        if run_be or run_il:
            _record_be_il_health(
                health,
                be_rows if run_be else None,
                il_rows if run_il else None,
            )

    if focused:
        # Do not overwrite the full workbook — write a focused side file.
        if run_pt and not (
            run_be or run_il or run_fr or run_pl or run_es or run_it or run_de or run_de_ov
            or run_ro or run_at or run_nordics or run_iec
        ):
            focused_out = str(_SCRIPT_DIR / "isuzu_tenders_v3_pt.xlsx")
        elif run_iec and not (run_be or run_il or run_fr or run_pl or run_es or run_it or run_de or run_de_ov or run_ro or run_at or run_nordics or run_pt):
            focused_out = str(_SCRIPT_DIR / "isuzu_tenders_v3_iec.xlsx")
        elif run_nordics and not (run_at or run_ro or run_de or run_de_ov or run_es or run_it or run_fr or run_pl or run_pt):
            focused_out = str(_SCRIPT_DIR / "isuzu_tenders_v3_nordics.xlsx")
        elif run_at and not (run_ro or run_de or run_de_ov or run_es or run_it or run_fr or run_pl or run_nordics or run_pt):
            focused_out = str(_SCRIPT_DIR / "isuzu_tenders_v3_at.xlsx")
        elif run_ro and not (run_de or run_de_ov or run_es or run_it or run_fr or run_pl or run_at or run_nordics or run_pt):
            focused_out = str(_SCRIPT_DIR / "isuzu_tenders_v3_ro.xlsx")
        elif run_de or run_de_ov:
            focused_out = str(_SCRIPT_DIR / "isuzu_tenders_v3_de.xlsx")
        elif run_es or run_it:
            focused_out = str(_SCRIPT_DIR / "isuzu_tenders_v3_es_it.xlsx")
        elif run_fr or run_pl:
            focused_out = str(_SCRIPT_DIR / "isuzu_tenders_v3_fr_pl.xlsx")
        else:
            focused_out = str(_SCRIPT_DIR / "isuzu_tenders_v3_bel_isr.xlsx")
        save_to_excel(
            uk_rows,
            il_rows,
            ted_rows,
            doffin_rows,
            hilma_rows,
            cf_rows,
            de_rows,
            be_rows,
            nl_rows,
            focused_out,
            fr_rows=fr_rows,
            pl_rows=pl_rows,
            iec_rows=iec_rows,
            es_rows=es_rows,
            it_rows=it_rows,
            de_ov_rows=de_ov_rows,
            ro_rows=ro_rows,
            at_rows=at_rows,
            pt_rows=pt_rows,
        )
    else:
        save_to_excel(
            uk_rows,
            il_rows,
            ted_rows,
            doffin_rows,
            hilma_rows,
            cf_rows,
            de_rows,
            be_rows,
            nl_rows,
            OUTPUT_FILE,
            fr_rows=fr_rows,
            pl_rows=pl_rows,
            iec_rows=iec_rows,
            es_rows=es_rows,
            it_rows=it_rows,
            de_ov_rows=de_ov_rows,
            ro_rows=ro_rows,
            at_rows=at_rows,
            pt_rows=pt_rows,
        )
    persist_and_report(health)
    print("\nDone.")
    print("=" * 60)


if __name__ == "__main__":
    main()
