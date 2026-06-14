"""
TED Tender Scraper v2 — ISZE / Isuzu Europe
Refined keyword filtering + CPV code targeting
Returns high-signal results only, with distributor-awareness dashboard output.

API: TED Europa v3 (POST /v3/notices/search)
Confirmed working: ND, TI, PD, DD, CY, PC, AU, TD fields
Operator: >= works; bracket date ranges fail; country codes ISO alpha-3
"""

import json
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import requests
except ImportError:
    print("Run: pip install requests")
    exit()

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

TED_API_URL = "https://api.ted.europa.eu/v3/notices/search"

# ISZE target markets (ISO alpha-3)
TARGET_COUNTRIES = ["GBR", "IRL", "PRT", "GRC", "POL"]

# CPV codes — refined for commercial/municipal vehicles and parts
# Primary: trucks and commercial vehicles
# Secondary: vehicle maintenance, parts, aftersales
CPV_CODES = {
    # Core vehicle categories
    "34130000": "Motor vehicles for transport of goods",
    "34140000": "Heavy-duty motor vehicles",
    "34144000": "Special-purpose motor vehicles",
    "34144100": "Fire-fighting vehicles",
    "34144200": "Emergency vehicles",
    "34144700": "Utility vehicles",
    "34114000": "Special-purpose vehicles",
    # Parts & maintenance
    "34300000": "Parts and accessories for vehicles",
    "34310000": "Engines and engine parts",
    "34320000": "Mechanical spare parts",
    "50100000": "Repair and maintenance of vehicles",
    "50110000": "Repair and maintenance of motor vehicles",
    "50111000": "Fleet management, repair and maintenance",
    "50112000": "Car repair and maintenance services",
    "50114000": "Repair and maintenance of trucks",
}

# HIGH-SIGNAL keywords — must appear in title/description
# Tier 1: near-certain match (Isuzu or direct competitors)
KEYWORDS_TIER1 = [
    "isuzu",
    "d-max", "dmax",
    "n-series", "n series",
    "npr", "npr-hd",
    "forward",  # Isuzu Forward series
]

# Tier 2: commercial vehicle tenders likely relevant
KEYWORDS_TIER2 = [
    "pickup truck", "pick-up truck", "pick up truck",
    "light commercial vehicle", "lcv",
    "utility vehicle", "ute",
    "4x4 truck", "4wd truck", "4wd pickup",
    "double cab", "single cab",
    "refuse truck", "tipper truck", "tipper lorry",
    "flatbed truck", "dropside truck",
    "crew cab",
    "van and truck", "trucks and vans",
    "municipal vehicle", "municipal fleet",
    "fleet of vehicles", "vehicle fleet",
    "off-road vehicle", "all-terrain vehicle",
    # Parts-specific
    "genuine parts", "oem parts",
    "vehicle parts supply", "spare parts supply",
    "aftersales", "after-sales",
    "fleet maintenance contract",
]

# NOISE FILTERS — exclude if any of these appear (too generic or irrelevant)
KEYWORDS_EXCLUDE = [
    "passenger car",
    "bus",
    "coach",
    "motorcycle",
    "bicycle",
    "railway",
    "aircraft",
    "boat",
    "vessel",
    "ambulance",        # usually specific medical spec, not Isuzu
    "armoured",
    "tank",
    "military",
    "it equipment",
    "software",
    "furniture",
    "cleaning",
    "catering",
]

# Date lookback (days) — how far back to fetch
LOOKBACK_DAYS = 30

# ─────────────────────────────────────────────
# SCORING LOGIC
# ─────────────────────────────────────────────

def score_notice(notice: dict) -> tuple[int, list[str]]:
    """
    Score a notice 0-100 based on relevance to ISZE.
    Returns (score, reasons).
    """
    score = 0
    reasons = []

    title = (notice.get("TI", "") or "").lower()
    description = (notice.get("DS", "") or "").lower()
    combined = title + " " + description

    # Hard exclusion
    for kw in KEYWORDS_EXCLUDE:
        if kw in combined:
            return 0, [f"Excluded: '{kw}' found"]

    # Tier 1 keywords — very high signal
    for kw in KEYWORDS_TIER1:
        if kw in combined:
            score += 40
            reasons.append(f"Tier-1 keyword: '{kw}'")
            break  # one is enough for max tier-1 score

    # Tier 2 keywords — moderate signal
    tier2_hits = []
    for kw in KEYWORDS_TIER2:
        if kw in combined:
            tier2_hits.append(kw)
    if tier2_hits:
        score += min(30, len(tier2_hits) * 10)
        reasons.append(f"Tier-2 keywords: {tier2_hits[:3]}")

    # CPV code match
    cpv_raw = notice.get("PC", "")
    if isinstance(cpv_raw, list):
        cpv_list = cpv_raw
    else:
        cpv_list = [str(cpv_raw)] if cpv_raw else []

    matched_cpvs = [c for c in cpv_list if str(c)[:8] in CPV_CODES]
    if matched_cpvs:
        score += 20
        reasons.append(f"CPV match: {matched_cpvs[:2]}")

    # Country bonus (some markets more strategic)
    country = notice.get("CY", "")
    strategic = {"PRT": 5, "GRC": 5, "POL": 3, "GBR": 3, "IRL": 2}
    score += strategic.get(country, 0)

    # Value range — vehicle fleet tenders tend to be 50k-5M EUR
    try:
        value = float(notice.get("VA", 0) or 0)
        if 50_000 <= value <= 10_000_000:
            score += 10
            reasons.append(f"Value in range: €{value:,.0f}")
    except (ValueError, TypeError):
        pass

    return min(score, 100), reasons


# ─────────────────────────────────────────────
# API FETCH
# ─────────────────────────────────────────────

def build_query(cpv_code: str, countries: list[str], since_date: str) -> str:
    """Build TED v3 query string for one CPV code."""
    country_filter = " OR ".join(f"CY={c}" for c in countries)
    return f"PC={cpv_code} AND ({country_filter}) AND PD>={since_date}"


def fetch_notices(cpv_code: str, countries: list[str], since_date: str, page: int = 1) -> dict:
    payload = {
        "query": build_query(cpv_code, countries, since_date),
        "fields": ["ND", "TI", "PD", "DD", "CY", "PC", "AU", "TD", "VA", "DS"],
        "scope": "ACTIVE",
        "paginationMode": "PAGE_NUMBER",
        "page": page,
        "pageSize": 100,
        "onlyLatestVersions": True,
        "checkQuerySyntax": False,
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    resp = requests.post(TED_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_all_notices(cpv_codes: list[str], countries: list[str], since_date: str) -> list[dict]:
    """Fetch all notices across CPV codes, deduplicate by ND."""
    all_notices = {}
    for cpv in cpv_codes:
        print(f"  Fetching CPV {cpv} ({CPV_CODES.get(cpv, '?')})...")
        try:
            page = 1
            while True:
                data = fetch_notices(cpv, countries, since_date, page)
                notices = data.get("notices", [])
                if not notices:
                    break
                for n in notices:
                    nd = n.get("ND", "")
                    if nd:
                        all_notices[nd] = n
                total = data.get("total", 0)
                fetched = page * 100
                print(f"    Page {page}: {len(notices)} results (total: {total})")
                if fetched >= total or len(notices) < 100:
                    break
                page += 1
        except Exception as e:
            print(f"  Warning: CPV {cpv} failed — {e}")
    return list(all_notices.values())


# ─────────────────────────────────────────────
# DASHBOARD OUTPUT
# ─────────────────────────────────────────────

COUNTRY_NAMES = {
    "GBR": "United Kingdom",
    "IRL": "Ireland",
    "PRT": "Portugal",
    "GRC": "Greece",
    "POL": "Poland",
}

DISTRIBUTOR_MAP = {
    "PRT": "I Motors (Filipe)",
    "GRC": "TBD",
    "POL": "TBD",
    "GBR": "TBD",
    "IRL": "TBD",
}

def format_dashboard(scored: list[dict]) -> str:
    """Format results as a plain-text dashboard for email/reporting."""
    lines = []
    lines.append("=" * 60)
    lines.append("ISZE TENDER MONITOR — DASHBOARD")
    lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Period: last {LOOKBACK_DAYS} days | Markets: {', '.join(TARGET_COUNTRIES)}")
    lines.append("=" * 60)

    # Summary by country
    by_country = {}
    for item in scored:
        cty = item["notice"].get("CY", "??")
        by_country.setdefault(cty, []).append(item)

    lines.append("\n📊 SUMMARY BY MARKET")
    lines.append("-" * 40)
    for cty, items in sorted(by_country.items()):
        high = sum(1 for i in items if i["score"] >= 60)
        med = sum(1 for i in items if 30 <= i["score"] < 60)
        dist = DISTRIBUTOR_MAP.get(cty, "TBD")
        lines.append(f"  {COUNTRY_NAMES.get(cty, cty)} ({cty}) — {dist}")
        lines.append(f"    High relevance: {high} | Medium: {med} | Total shown: {len(items)}")

    # High-signal results (score >= 60)
    high_signal = [i for i in scored if i["score"] >= 60]
    lines.append(f"\n🔴 HIGH RELEVANCE ({len(high_signal)} tenders — score ≥ 60)")
    lines.append("-" * 40)
    for item in high_signal:
        n = item["notice"]
        lines.append(f"\n  [{item['score']}/100] {n.get('TI', 'No title')}")
        lines.append(f"  Country: {COUNTRY_NAMES.get(n.get('CY',''), n.get('CY',''))} | "
                     f"Published: {n.get('PD', '?')} | Deadline: {n.get('DD', '?')}")
        lines.append(f"  Authority: {n.get('AU', '?')}")
        cpv_raw = n.get("PC", "")
        cpvs = cpv_raw if isinstance(cpv_raw, list) else [cpv_raw]
        lines.append(f"  CPV: {', '.join(str(c) for c in cpvs[:3])}")
        if n.get("VA"):
            lines.append(f"  Est. value: €{float(n.get('VA', 0)):,.0f}")
        lines.append(f"  Reasons: {'; '.join(item['reasons'][:3])}")
        nd = n.get("ND", "")
        if nd:
            lines.append(f"  TED link: https://ted.europa.eu/udl?uri=TED:NOTICE:{nd}:TEXT:EN:HTML")
        distributor = DISTRIBUTOR_MAP.get(n.get("CY", ""), "TBD")
        lines.append(f"  → Distributor: {distributor}")

    # Medium-signal results (score 30-59)
    medium_signal = [i for i in scored if 30 <= i["score"] < 60]
    lines.append(f"\n🟡 MEDIUM RELEVANCE ({len(medium_signal)} tenders — score 30–59)")
    lines.append("-" * 40)
    for item in medium_signal[:20]:  # cap at 20 for readability
        n = item["notice"]
        lines.append(f"  [{item['score']}/100] {n.get('TI', 'No title')} "
                     f"({n.get('CY', '?')}, {n.get('PD', '?')})")

    lines.append("\n" + "=" * 60)
    lines.append("Supply chain note: High-relevance tenders >6 months out")
    lines.append("should be flagged to Japan forecasting for modification parts.")
    lines.append("=" * 60)
    return "\n".join(lines)


def save_json(scored: list[dict], filepath: str):
    """Save full scored results as JSON for Power BI / further processing."""
    export = []
    for item in scored:
        n = item["notice"]
        export.append({
            "score": item["score"],
            "reasons": item["reasons"],
            "notice_id": n.get("ND"),
            "title": n.get("TI"),
            "country": n.get("CY"),
            "country_name": COUNTRY_NAMES.get(n.get("CY", ""), n.get("CY", "")),
            "distributor": DISTRIBUTOR_MAP.get(n.get("CY", ""), "TBD"),
            "published": n.get("PD"),
            "deadline": n.get("DD"),
            "authority": n.get("AU"),
            "cpv_codes": n.get("PC"),
            "estimated_value_eur": n.get("VA"),
            "ted_url": f"https://ted.europa.eu/udl?uri=TED:NOTICE:{n.get('ND')}:TEXT:EN:HTML" if n.get("ND") else None,
        })
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    print(f"  Saved JSON: {filepath}")


# ─────────────────────────────────────────────
# EMAIL ALERT (optional)
# ─────────────────────────────────────────────

def send_email_alert(dashboard_text: str, high_count: int,
                     smtp_host: str, smtp_port: int,
                     sender: str, password: str, recipient: str):
    """Send dashboard as email. Configure SMTP settings below."""
    subject = f"ISZE Tender Monitor — {high_count} high-relevance tenders"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(dashboard_text, "plain"))
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print(f"  Email sent to {recipient}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    since_date = (datetime.date.today() - datetime.timedelta(days=LOOKBACK_DAYS)).strftime("%Y%m%d")
    print(f"\nISSZE Tender Scraper v2")
    print(f"Fetching from {since_date} | Countries: {TARGET_COUNTRIES}")
    print(f"CPV codes: {len(CPV_CODES)}\n")

    # Fetch — use primary vehicle CPVs only (most specific signal)
    primary_cpvs = [
        "34130000", "34140000", "34144000", "34144700",
        "34300000", "50114000", "50111000",
    ]

    raw_notices = fetch_all_notices(primary_cpvs, TARGET_COUNTRIES, since_date)
    print(f"\nFetched {len(raw_notices)} unique notices before scoring\n")

    # Score and filter
    scored = []
    for notice in raw_notices:
        score, reasons = score_notice(notice)
        if score >= 30:  # minimum threshold
            scored.append({"score": score, "reasons": reasons, "notice": notice})

    # Sort by score desc
    scored.sort(key=lambda x: x["score"], reverse=True)

    print(f"After scoring: {len(scored)} relevant notices "
          f"({sum(1 for s in scored if s['score']>=60)} high, "
          f"{sum(1 for s in scored if 30<=s['score']<60)} medium)\n")

    # Dashboard output
    dashboard = format_dashboard(scored)
    print(dashboard)

    # Save outputs
    output_dir = "."
    dashboard_path = f"{output_dir}/tender_dashboard_{datetime.date.today().strftime('%Y%m%d')}.txt"
    json_path = f"{output_dir}/tender_results_{datetime.date.today().strftime('%Y%m%d')}.json"

    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(dashboard)
    print(f"\nDashboard saved: {dashboard_path}")

    save_json(scored, json_path)

    # ── Email alert (uncomment and configure to enable) ──
    # high_count = sum(1 for s in scored if s["score"] >= 60)
    # if high_count > 0:
    #     send_email_alert(
    #         dashboard_text=dashboard,
    #         high_count=high_count,
    #         smtp_host="smtp.gmail.com",
    #         smtp_port=465,
    #         sender="your@email.com",
    #         password="your_app_password",
    #         recipient="jerome@isze.com",
    #     )

    return scored


if __name__ == "__main__":
    main()
