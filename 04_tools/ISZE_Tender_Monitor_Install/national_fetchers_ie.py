"""Ireland eTenders national notices via data.gov.ie OGP CSV (no API key).

Official dataset: Contract Notices Published on eTenders
https://data.gov.ie/dataset/contract-notices-published-on-etenders
CSV: https://assets.gov.ie/static/documents/4d482e0e/Public_Procurement_Opendata_Dataset.csv

eTenders HTML/RSS stays brittle (RSS 500). This path is the public quarterly dump.
Does not invent notices. Hungary EKR / Sweden commercial portals are not wired here.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IE_CSV_URL = (
    "https://assets.gov.ie/static/documents/4d482e0e/Public_Procurement_Opendata_Dataset.csv"
)
IE_CKAN = (
    "https://data.gov.ie/api/3/action/package_show?id=contract-notices-published-on-etenders"
)
IE_NOTICE_TMPL = "https://www.etenders.gov.ie/epps/cft/prepareViewCfTWS.do?resourceId={nid}"

# Align with tender_scraper_v3 surgical CPV (no 34100000 catch-all).
IE_CPV_PREFIXES = (
    "3413",  # goods vehicles
    "3414",
    "34131",
    "34133",
    "34134",
    "34136",
    "5011",  # R&M / fleet
    "50114",
)
KEYWORDS_IE = [
    "truck",
    "pickup",
    "pick-up",
    "chassis",
    "tipper",
    "dropside",
    "isuzu",
    "d-max",
    "n-series",
    "goods vehicle",
    "commercial vehicle",
    "fleet vehicle",
    "7.5 tonne",
    "7.5t",
    "rigid",
    "crew cab",
    "double cab",
]

LAST_ERROR: Optional[str] = None


def _cpv_ok(cpv: str) -> bool:
    c = (cpv or "").strip().replace(" ", "")
    if not c:
        return False
    return any(c.startswith(p) for p in IE_CPV_PREFIXES)


def _kw_ok(blob: str) -> bool:
    b = (blob or "").lower()
    return any(k in b for k in KEYWORDS_IE)


def _parse_ie_date(raw: object) -> Optional[datetime]:
    s = str(raw or "").strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:10], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def rows_from_etenders_frame(
    df: pd.DataFrame,
    from_dt: datetime,
) -> List[Dict[str, Any]]:
    """Pure filter used by tests and the live fetcher."""
    colmap = {str(c).strip(): c for c in df.columns}

    def col(*names: str) -> Optional[str]:
        for n in names:
            if n in colmap:
                return colmap[n]
        for k, orig in colmap.items():
            for n in names:
                if n.lower() in k.lower():
                    return orig
        return None

    c_id = col("Tender ID")
    c_title = col("Tender/Contract Name")
    c_buyer = col("Contracting Authority", "Name of Client Contracting Authority")
    c_pub = col("Notice Published Date / Contract Created Date")
    c_cpv = col("Main Cpv Code")
    c_cpv_desc = col("Main Cpv Code Description")
    c_url = col("TED Notice Link")
    c_deadline = col("Tender Submission Deadline")
    c_val = col("Sum of Notice Estimated Value")

    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    cutoff = from_dt
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)

    # Quarterly dump can lag the scraper's 30-day window (file currently ends 2026-06-30).
    pubs = []
    if c_pub:
        for raw in df[c_pub].head(5000):
            p = _parse_ie_date(raw)
            if p is not None:
                pubs.append(p)
    if pubs:
        latest = max(pubs)
        if latest < cutoff:
            cutoff = latest.replace(tzinfo=timezone.utc) - timedelta(days=90)

    for _, r in df.iterrows():
        title = str(r.get(c_title) or "").strip() if c_title else ""
        cpv = str(r.get(c_cpv) or "").strip() if c_cpv else ""
        cpv_desc = str(r.get(c_cpv_desc) or "").strip() if c_cpv_desc else ""
        blob = " ".join([title, cpv, cpv_desc])
        if not (_cpv_ok(cpv) or _kw_ok(blob)):
            continue
        pub = _parse_ie_date(r.get(c_pub) if c_pub else None)
        if pub is not None and pub < cutoff:
            continue
        nid = str(r.get(c_id) or "").strip() if c_id else ""
        key = nid or title.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        url = str(r.get(c_url) or "").strip() if c_url else ""
        if not url or url.lower() in ("nan", "none"):
            url = IE_NOTICE_TMPL.format(nid=nid) if nid else ""
        val = r.get(c_val) if c_val else ""
        deadline = r.get(c_deadline) if c_deadline else ""
        buyer = str(r.get(c_buyer) or "").strip() if c_buyer else ""
        results.append(
            {
                "Source": "🇮🇪 IE-eTenders",
                "Source Notice ID": nid,
                "Lifecycle": "",
                "Notice Type": "",
                "Procedure Type": "",
                "Buyer Type": "",
                "Score": "",
                "FleetSize": "",
                "Title": title,
                "Buyer": buyer,
                "CPV Code": cpv,
                "CPV Desc": cpv_desc,
                "Description": title,
                "Est. Value": val if pd.notna(val) else "",
                "Currency": "EUR",
                "Published": pub.strftime("%Y-%m-%d") if pub else "",
                "Deadline": "" if deadline is None or (isinstance(deadline, float) and pd.isna(deadline)) else str(deadline),
                "Country": "Ireland",
                "Country Code": "IRL",
                "URL": url,
            }
        )
    return results


def fetch_ireland_etenders(
    session: Optional[requests.Session] = None,
    from_dt: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """National IE notices from the OGP open-data CSV (vehicle CPV/keyword)."""
    global LAST_ERROR
    LAST_ERROR = None
    print("\n[IE eTenders] Fetching OGP open-data CSV (vehicle CPV/keyword)...")
    own = session is None
    session = session or requests.Session()
    cutoff = from_dt or datetime.now(timezone.utc)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/csv,application/json,*/*",
    }
    csv_url = IE_CSV_URL
    try:
        meta = session.get(IE_CKAN, headers=headers, timeout=45)
        if meta.status_code == 200:
            resources = ((meta.json() or {}).get("result") or {}).get("resources") or []
            for res in resources:
                u = str(res.get("url") or res.get("download_url") or "").strip()
                if u.lower().endswith(".csv"):
                    csv_url = u
                    break
        print(f"  [IE eTenders] CSV {csv_url}")
        resp = session.get(csv_url, headers=headers, timeout=180)
        if resp.status_code != 200:
            LAST_ERROR = f"CSV HTTP {resp.status_code}"
            print(f"  [IE eTenders] {LAST_ERROR}")
            return []
        from io import BytesIO

        df = pd.read_csv(BytesIO(resp.content), low_memory=False, encoding="cp1252")
        rows = rows_from_etenders_frame(df, cutoff)
        LAST_ERROR = None if rows else f"zero vehicle-ish rows in {len(df)} CSV lines"
        print(f"[IE eTenders] Matches: {len(rows)} (scanned={len(df)})")
        return rows
    except Exception as exc:
        LAST_ERROR = str(exc)
        print(f"  [IE eTenders] exception: {exc}")
        return []
    finally:
        if own:
            session.close()
