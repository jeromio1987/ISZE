"""
ISZE Tender Collector v5
Sources:
- UK:      Find a Tender (official OCDS API, paginated)
- EU:      TED Europa (all member states + Norway)
- Norway:  Doffin (below-threshold tenders) — requires free API key
- Finland: HILMA (below-threshold tenders) — requires free API key
- Israel:  Government RSS feed

Output: isuzu_tenders.xlsx (separate tab per source)

── HOW TO GET FREE API KEYS ──────────────────────────────────────────
Doffin (Norway):
  1. Go to https://dof-notices-prod-api.developer.azure-api.net/
  2. Sign up for a free account
  3. Subscribe to the "Public API" product
  4. Copy your subscription key into DOFFIN_API_KEY below

HILMA (Finland):
  1. Go to https://hns-hilma-prod-apim.developer.azure-api.net/
  2. Sign up for a free account
  3. Subscribe to the "AVP API" product
  4. Copy your subscription key into HILMA_API_KEY below
──────────────────────────────────────────────────────────────────────
"""

import os, re, time, requests, openpyxl, ast
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# ── CONFIG ─────────────────────────────────────────────────────────────────────

LOOKBACK_DAYS = 30
# Always save next to the script itself, regardless of where you run it from
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "isuzu_tenders.xlsx")

# ── API KEYS (free — see signup instructions at top of file) ───────────────────
# Leave as "" to skip that source gracefully
DOFFIN_API_KEY = ""   # Norway: https://dof-notices-prod-api.developer.azure-api.net/
HILMA_API_KEY  = ""   # Finland: https://hns-hilma-prod-apim.developer.azure-api.net/

KEYWORDS = [
    # ── General vehicle / fleet terms ──────────────────────────
    "vehicle", "van", "truck", "pickup", "pick-up", "4x4",
    "chassis cab", "tipper", "dropside", "crew cab", "double cab",
    "flatbed", "box van", "fleet", "lcv", "goods vehicle",
    "commercial vehicle", "motor vehicle", "light goods",
    "municipal vehicle", "service vehicle", "pool vehicle",
    "road maintenance", "public works vehicle",

    # ── Isuzu brand & model lines ───────────────────────────────
    "isuzu",                            # brand name in any context
    "d-max", "d max", "dmax",           # D-Max pickup range
    "n-series", "n series",             # N Series light/medium trucks
    "f-series", "f series",             # F Series medium/heavy trucks

    # ── Pickup / D-Max relevant ─────────────────────────────────
    "pickup truck", "pick up truck",
    "4x4 vehicle", "off-road vehicle", "all-terrain vehicle",
    "utility vehicle", "light utility",
    "single cab", "extra cab",

    # ── N Series relevant (3.5t – 7.5t light/medium trucks) ─────
    "light truck", "medium truck", "rigid truck",
    "3.5 tonne", "3.5t ", "5 tonne", "7.5 tonne", "7.5t ",
    "box truck", "curtainsider", "curtain sider", "luton",
    "refrigerated vehicle", "temperature controlled vehicle",
    "tail lift", "taillift", "liftgate",

    # ── F Series relevant (up to 12t — FRR/FSR European range) ──
    "12 tonne", "12t ",
    "skip lorry", "skip truck", "hook lift", "hooklift", "hook arm",
    "refuse vehicle", "refuse collection",
    "tipper truck", "tipping truck",
]

KEYWORDS_HE = [
    "רכב", "משאית", "טנדר", "כלי רכב", "רכב שטח", "רכב מסחרי", "צי רכבים",
]

# ── RELEVANCE SCORING ──────────────────────────────────────────────────────────
# Signals used to score each tender 1–5 for parts consumption potential

SCORE_BRAND = [
    "isuzu", "d-max", "d max", "dmax", "n-series", "n series", "f-series", "f series",
]
SCORE_SERVICE = [
    # ── English ──────────────────────────────────────────────────
    "maintenance", "service contract", "repair and maintenance", "servicing",
    "after-sales", "aftersales", "spare parts", "parts supply", "parts and labour",
    "fleet management", "preventive maintenance", "corrective maintenance",
    "full maintenance", "scheduled maintenance", "vehicle maintenance",
    "repair", "overhaul", "upkeep", "workshop",
    # ── German (DE) ──────────────────────────────────────────────
    "wartung", "instandhaltung", "reparatur", "fahrzeugwartung", "kfz-wartung",
    "inspektion", "werkstatt", "ersatzteile", "fahrzeugpflege", "kfz-reparatur",
    # ── French (FR) ──────────────────────────────────────────────
    "entretien", "maintenance", "réparation", "reparation", "révision", "revision",
    "pièces détachées", "pieces detachees", "pièces de rechange", "atelier",
    "gestion de flotte",
    # ── Spanish (ES) ─────────────────────────────────────────────
    "mantenimiento", "reparación", "reparacion", "taller",
    "piezas de repuesto", "revisión", "revision", "mantenimiento de vehículos",
    # ── Italian (IT) ─────────────────────────────────────────────
    "manutenzione", "riparazione", "officina", "ricambi", "assistenza",
    "gestione flotta",
    # ── Polish (PL) ──────────────────────────────────────────────
    "konserwacja", "naprawa", "serwis", "części zamienne", "czesci zamienne",
    "utrzymanie", "warsztat",
    # ── Dutch (NL) ───────────────────────────────────────────────
    "onderhoud", "reparatie", "werkplaats", "onderdelen", "voertuigonderhoud",
    "vlootbeheer",
    # ── Portuguese (PT) ──────────────────────────────────────────
    "manutenção", "manutencao", "reparação", "reparacao", "oficina",
    "peças sobressalentes", "pecas sobressalentes",
    # ── Romanian (RO) ────────────────────────────────────────────
    "mentenanță", "mentenanta", "reparații", "reparatii", "întreținere",
    "intretinere", "piese de schimb",
    # ── Hungarian (HU) ───────────────────────────────────────────
    "karbantartás", "karbantartas", "javítás", "javitas", "alkatrészek",
    "alkatreszek", "szerviz",
    # ── Czech (SK/CZ) ────────────────────────────────────────────
    "údržba", "udrzba", "oprava", "náhradní díly", "nahradni dily",
    # ── Swedish (SE) ─────────────────────────────────────────────
    "underhåll", "underhall", "reparation", "reservdelar", "fordonsunderhåll",
    # ── Danish (DK) ──────────────────────────────────────────────
    "vedligeholdelse", "reparation", "reservedele", "værksted", "vaerksted",
    # ── Greek (GR) ───────────────────────────────────────────────
    "συντήρηση", "επισκευή", "ανταλλακτικά",
    # ── Hebrew (IL) ──────────────────────────────────────────────
    "תחזוקה", "תיקון", "חלקי חילוף", "ניהול צי",
]
SCORE_FRAMEWORK = [
    # ── English ──────────────────────────────────────────────────
    "framework agreement", "framework contract", "dynamic purchasing",
    "dps", "multi-year", "annual contract", "lot ", "lots ",
    "call-off", "call off", "blanket order",
    # ── German (DE) ──────────────────────────────────────────────
    "rahmenvertrag", "rahmenvereinbarung", "dynamisches beschaffungssystem",
    # ── French (FR) ──────────────────────────────────────────────
    "accord-cadre", "accord cadre", "système d'acquisition dynamique",
    "systeme d'acquisition dynamique",
    # ── Spanish (ES) ─────────────────────────────────────────────
    "acuerdo marco", "sistema dinámico de adquisición",
    "sistema dinamico de adquisicion",
    # ── Italian (IT) ─────────────────────────────────────────────
    "accordo quadro", "sistema dinamico di acquisizione",
    # ── Polish (PL) ──────────────────────────────────────────────
    "umowa ramowa", "dynamiczny system zakupów", "dynamiczny system zakupow",
    # ── Dutch (NL) ───────────────────────────────────────────────
    "raamovereenkomst", "dynamisch aankoopsysteem",
    # ── Portuguese (PT) ──────────────────────────────────────────
    "acordo quadro", "acordo-quadro",
    # ── Romanian (RO) ────────────────────────────────────────────
    "acord-cadru", "acord cadru",
    # ── Hungarian (HU) ───────────────────────────────────────────
    "keretmegállapodás", "keretmegallapodas",
    # ── Czech (SK/CZ) ────────────────────────────────────────────
    "rámcová smlouva", "ramcova smlouva",
    # ── Swedish (SE) ─────────────────────────────────────────────
    "ramavtal",
    # ── Danish (DK) ──────────────────────────────────────────────
    "rammeaftale",
]

def extract_fleet_size(title):
    """
    Try to extract a fleet quantity from the tender title.
    Returns an integer if found, or 0 if not detectable.
    Examples matched:
      "Supply of 50 vehicles"  → 50
      "Fleet of 120 trucks"    → 120
      "100 commercial vehicles"→ 100
      "Lot: 30 vans"           → 30
    """
    t = title.lower()
    patterns = [
        # "fleet of N ..."
        r'fleet\s+of\s+(\d+)',
        # "N vehicles/trucks/vans/etc."
        r'(\d+)\s+(?:vehicles?|trucks?|vans?|lorr(?:y|ies)|buses?|coaches?|pick[\s-]?ups?'
        r'|motor\s+vehicles?|commercial\s+vehicles?|light\s+commercial|minibuses?)',
        # "provision/supply/acquisition of N ..."
        r'(?:supply|provision|acquisition|purchase|procurement)\s+of\s+(\d+)',
    ]
    for pat in patterns:
        m = re.search(pat, t)
        if m:
            try:
                return int(m.group(1))
            except (IndexError, ValueError):
                pass
    return 0


def score_tender(title, value=None):
    """
    Score 1–5 based on parts consumption potential:
    5 = Isuzu brand + service/maintenance  (direct parts demand, brand-specific)
    4 = Any vehicle + service + framework  (recurring, multi-supplier opportunity)
    3 = Any vehicle + service/maintenance  (ongoing parts demand)
    2 = Vehicle + framework OR high value  (fleet scale, potential service tail)
    1 = Generic vehicle purchase only      (one-time, low parts signal)
    """
    t = title.lower()
    brand   = any(k in t for k in SCORE_BRAND)
    service = any(k in t for k in SCORE_SERVICE)
    fw      = any(k in t for k in SCORE_FRAMEWORK)

    try:
        high_value = float(str(value).replace(",", "")) > 500_000 if value else False
    except Exception:
        high_value = False

    if brand and service:
        return 5
    if service and fw:
        return 4
    if service:
        return 3
    if fw or high_value:
        return 2
    return 1

# CPV codes — vehicles + maintenance/repair services
# Vehicle purchase: 341xxxxx
# Vehicle maintenance/repair services: 501xxxxx  ← NEW: catches service contracts
CPV_CODES = [
    # ── Vehicle purchase (fleet tenders) ──────────────────────────
    "34100000",  # Motor vehicles
    "34130000",  # Motor vehicles for transport of goods
    "34131000",  # Pick-up trucks
    "34113000",  # 4-wheel-drive vehicles
    "34136000",  # Vans
    "34114000",  # Special-purpose vehicles
    "34120000",  # Motor vehicles for transport of ≥8 persons
    # ── Maintenance & repair services (parts consumption) ─────────
    "50110000",  # Repair and maintenance of motor vehicles
    "50112000",  # Repair and maintenance of cars
    "50113000",  # Repair and maintenance of buses
    "50114000",  # Repair and maintenance of trucks
    "50116000",  # Repair/maintenance of vehicle electrical equipment
    "50190000",  # Miscellaneous repair/maintenance of vehicles
    "50100000",  # Repair/maintenance of vehicles and equipment
]

# TED v3 API requires 2-letter ISO codes for the CY= field
# (3-letter codes like GBR silently return 0 results)
TED_COUNTRY_MAP = {
    "GBR": "GB", "IRL": "IE", "PRT": "PT", "GRC": "GR", "POL": "PL",
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY",
    "CZE": "CZ", "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR",
    "DEU": "DE", "HUN": "HU", "ITA": "IT", "LVA": "LV", "LTU": "LT",
    "LUX": "LU", "MLT": "MT", "NLD": "NL", "ROU": "RO", "SVK": "SK",
    "SVN": "SI", "ESP": "ES", "SWE": "SE", "NOR": "NO",
}

# European markets (all EU member states + Norway/EEA)
# Note: GBR is also fetched separately via the UK Find a Tender API
COUNTRIES = [
    # Original markets
    "GBR",  # United Kingdom (also via dedicated UK fetcher)
    "IRL",  # Ireland
    "PRT",  # Portugal
    "GRC",  # Greece
    "POL",  # Poland
    # Remaining EU member states
    "AUT",  # Austria
    "BEL",  # Belgium
    "BGR",  # Bulgaria
    "HRV",  # Croatia
    "CYP",  # Cyprus
    "CZE",  # Czech Republic
    "DNK",  # Denmark
    "EST",  # Estonia
    "FIN",  # Finland
    "FRA",  # France
    "DEU",  # Germany
    "HUN",  # Hungary
    "ITA",  # Italy
    "LVA",  # Latvia
    "LTU",  # Lithuania
    "LUX",  # Luxembourg
    "MLT",  # Malta
    "NLD",  # Netherlands
    "ROU",  # Romania
    "SVK",  # Slovakia
    "SVN",  # Slovenia
    "ESP",  # Spain
    "SWE",  # Sweden
    # EEA (non-EU but uses TED)
    "NOR",  # Norway
]

# ── HELPERS ────────────────────────────────────────────────────────────────────

def match_keywords(text, keywords):
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)

def safe_get(d, path, default=""):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur or default

def get_with_retry(session, url, params=None, max_retries=4):
    for attempt in range(max_retries):
        try:
            r = session.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(5 + attempt * 3)
                continue
            r.raise_for_status()
            return r
        except Exception:
            time.sleep(2 + attempt * 2)
    return None

# ── UK FIND A TENDER ───────────────────────────────────────────────────────────

def fetch_uk(session, from_dt, to_dt):
    print("\n[UK] Fetching from Find a Tender...")
    base_url = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages"
    all_releases = []
    cursor = None
    page = 0

    while page < 50:
        params = {
            "updatedFrom": from_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "updatedTo":   to_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "stages": "tender",
            "limit": 100,
        }
        if cursor:
            params["cursor"] = cursor

        resp = get_with_retry(session, base_url, params=params)
        if not resp:
            print("[UK] Request failed.")
            break

        pkg = resp.json()
        releases = pkg.get("releases", []) or []
        all_releases.extend(releases)
        print(f"  Page {page+1}: {len(releases)} releases (total: {len(all_releases)})")

        next_url = safe_get(pkg, ["links", "next"], None)
        if next_url and "cursor=" in next_url:
            cursor = next_url.split("cursor=")[-1]
        else:
            break

        page += 1
        time.sleep(0.5)

    print(f"[UK] Total fetched: {len(all_releases)}")

    results = []
    for rel in all_releases:
        tender = rel.get("tender", {}) or {}
        title = str(tender.get("title") or "")

        if not match_keywords(title, KEYWORDS):
            continue

        val = safe_get(tender, ["value", "amount"])
        results.append({
            "Score":      score_tender(title, val),
            "FleetSize":  extract_fleet_size(title),
            "Title":      title,
            "Buyer":      safe_get(rel, ["buyer", "name"]),
            "CPV Code":   safe_get(tender, ["classification", "id"]),
            "CPV Desc":   safe_get(tender, ["classification", "description"]),
            "Est. Value": val,
            "Currency":   safe_get(tender, ["value", "currency"]),
            "Published":  str(rel.get("date") or ""),
            "Deadline":   safe_get(tender, ["tenderPeriod", "endDate"]),
            "Country":    "United Kingdom",
            "URL":        f"https://www.find-tender.service.gov.uk/Notice/{rel.get('id','')}"
        })

    print(f"[UK] Matches: {len(results)}")
    return results

# ── TED EU ─────────────────────────────────────────────────────────────────────

def fetch_ted(session, from_dt):
    print("\n[TED] Fetching from TED Europa...")
    url = "https://api.ted.europa.eu/v3/notices/search"

    date_from = from_dt.strftime("%Y%m%d")

    cpv_block = " OR ".join([f"PC={c}" for c in CPV_CODES])

    # Exclude GBR: UK post-Brexit tenders are not on TED (handled by UK fetcher).
    eu_countries = [c for c in COUNTRIES if c != "GBR"]

    # TED CY= field rejects both 2-letter and 3-letter ISO codes.
    # Drop country filter entirely — TED is EU-only by nature.
    # Keyword filter handles noise from non-target markets.
    query = f"({cpv_block}) AND PD>={date_from}"
    print(f"  Query: {query}")

    all_notices = []
    LIMIT = 100
    next_token = None

    # TED uses cursor/iteration pagination (iterationNextToken), not page numbers.
    # paginationMode PAGE_NUMBER was causing totalNoticeCount:None (query not processed).
    while True:
        payload = {
            "query":  query,
            "fields": ["ND", "TI", "PD", "DD", "CY", "PC", "AU"],
            "limit":  LIMIT,
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
            total = data.get("totalNoticeCount", "?")
            print(f"  TED totalNoticeCount: {total}")

            notices = data.get("notices", [])
            if not notices:
                if not all_notices:
                    print(f"  TED raw response: {str(data)[:500]}")
                break

            all_notices.extend(notices)
            print(f"  Fetched {len(notices)} (running total: {len(all_notices)})")

            next_token = data.get("iterationNextToken")
            if not next_token:
                break
            time.sleep(0.5)

        except Exception as e:
            print(f"  TED exception: {e}")
            break

    print(f"[TED] Total fetched from API: {len(all_notices)} — applying keyword filter...")

    results = []
    for n in all_notices:
        # TI comes back as a string-encoded dict e.g. "{'eng': 'Spain – ...', 'deu': '...'}"
        # OR as an actual dict depending on API version — handle both
        title_raw = n.get("TI", {})
        if isinstance(title_raw, str):
            try:
                title_raw = ast.literal_eval(title_raw)
            except Exception:
                pass  # leave as string if unparseable
        if isinstance(title_raw, dict):
            title = (title_raw.get("eng") or title_raw.get("EN") or title_raw.get("ENG")
                     or next(iter(title_raw.values()), ""))
            if isinstance(title, list):
                title = title[0] if title else ""
        else:
            title = str(title_raw)
        title = str(title)

        # Apply same keyword filter as UK — cuts 2000+ CPV matches to relevant ones
        if not match_keywords(title, KEYWORDS):
            continue

        # CY and PC can be lists — extract first value cleanly
        country_raw = n.get("CY", "")
        country = country_raw[0] if isinstance(country_raw, list) else str(country_raw)
        country = country.strip("[]'\" ")

        cpv_raw = n.get("PC", "")
        cpv = cpv_raw[0] if isinstance(cpv_raw, list) else str(cpv_raw)
        cpv = cpv.strip("[]'\" ")

        # AU (buyer) — same string-encoded dict issue as TI
        buyer_raw = n.get("AU", "")
        if isinstance(buyer_raw, str):
            try:
                buyer_raw = ast.literal_eval(buyer_raw)
            except Exception:
                pass
        if isinstance(buyer_raw, dict):
            buyer = (buyer_raw.get("eng") or buyer_raw.get("EN")
                     or next(iter(buyer_raw.values()), ""))
            if isinstance(buyer, list):
                buyer = buyer[0] if buyer else ""
        elif isinstance(buyer_raw, list):
            buyer = buyer_raw[0] if buyer_raw else ""
            if isinstance(buyer, dict):
                buyer = next(iter(buyer.values()), "")
        else:
            buyer = str(buyer_raw)
        buyer = str(buyer).strip("[]'\" ")

        results.append({
            "Score":      score_tender(title),
            "FleetSize":  extract_fleet_size(title),
            "Title":      title,
            "Buyer":      buyer,
            "CPV Code":   cpv,
            "CPV Desc":   "",
            "Est. Value": "",
            "Currency":   "",
            "Published":  str(n.get("PD", "")),
            "Deadline":   str(n.get("DD", "")),
            "Country":    country,
            "URL":        f"https://ted.europa.eu/en/notice/-/detail/{n.get('ND','')}"
        })
    print(f"[TED] Keyword matches: {len(results)} (from {len(all_notices)} total)")
    return results

# ── ISRAEL RSS ─────────────────────────────────────────────────────────────────

def fetch_israel(session):
    print("\n[IL] Fetching Israel government tenders RSS...")
    url = "https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml"

    try:
        resp = get_with_retry(session, url)
        if not resp:
            print("[IL] Failed to fetch RSS.")
            return []

        root = ET.fromstring(resp.content)
        results = []

        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el  = item.find("link")
            date_el  = item.find("pubDate")

            title = title_el.text if title_el is not None else ""
            link  = link_el.text  if link_el  is not None else ""
            date  = date_el.text  if date_el  is not None else ""

            if not match_keywords(title, KEYWORDS + KEYWORDS_HE):
                continue

            results.append({
                "Score":      score_tender(title),
                "FleetSize":  extract_fleet_size(title),
                "Title":      title,
                "Buyer":      "",
                "CPV Code":   "",
                "CPV Desc":   "",
                "Est. Value": "",
                "Currency":   "",
                "Published":  date,
                "Deadline":   "",
                "Country":    "Israel",
                "URL":        link
            })

        print(f"[IL] Matches: {len(results)}")
        return results

    except Exception as e:
        print(f"[IL] Error: {e}")
        return []

# ── DOFFIN (NORWAY) ────────────────────────────────────────────────────────────

def fetch_doffin(session, from_dt):
    if not DOFFIN_API_KEY:
        print("\n[Doffin] No API key set — skipping. See instructions at top of file.")
        return []

    print("\n[Doffin] Fetching from Doffin (Norway)...")
    base_url = "https://betaapi.doffin.no/public/v2/notices"
    headers  = {"Ocp-Apim-Subscription-Key": DOFFIN_API_KEY}

    date_from = from_dt.strftime("%Y-%m-%d")

    # Build keyword search string from vehicle terms
    search_terms = " OR ".join([
        "vehicle", "truck", "van", "fleet", "pickup",
        "chassis cab", "tipper", "commercial vehicle"
    ])

    all_results = []
    page = 1
    LIMIT = 100

    while True:
        params = {
            "searchString": search_terms,
            "publishedFrom": date_from,
            "limit": LIMIT,
            "offset": (page - 1) * LIMIT,
        }

        try:
            resp = session.get(base_url, headers=headers, params=params, timeout=30)
            print(f"  Page {page} – Status: {resp.status_code}")

            if resp.status_code == 401:
                print("  [Doffin] Invalid API key. Check DOFFIN_API_KEY.")
                break
            if resp.status_code != 200:
                print(f"  [Doffin] Error: {resp.text[:300]}")
                break

            data = resp.json()

            if page == 1:
                total = data.get("total", data.get("count", "unknown"))
                print(f"  Doffin reports {total} total matching notices")

            notices = data.get("notices", data.get("items", data if isinstance(data, list) else []))
            if not notices:
                break

            for n in notices:
                title = n.get("title", n.get("noticeTitle", ""))
                if not isinstance(title, str):
                    title = str(title)

                val = str(n.get("estimatedValue", n.get("value", "")))
                all_results.append({
                    "Score":      score_tender(title, val),
                    "FleetSize":  extract_fleet_size(title),
                    "Title":      title,
                    "Buyer":      str(n.get("contractingAuthority", n.get("buyer", ""))),
                    "CPV Code":   str(n.get("cpvCode", n.get("cpv", ""))),
                    "CPV Desc":   str(n.get("cpvDescription", "")),
                    "Est. Value": val,
                    "Currency":   "NOK",
                    "Published":  str(n.get("publishedDate", n.get("publicationDate", ""))),
                    "Deadline":   str(n.get("deadline", n.get("submissionDeadline", ""))),
                    "Country":    "Norway",
                    "URL":        str(n.get("url", n.get("noticeUrl",
                                  f"https://www.doffin.no/notices/{n.get('id', '')}")))
                })

            print(f"  Fetched {len(notices)} (running total: {len(all_results)})")

            if len(notices) < LIMIT:
                break
            page += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"  [Doffin] Exception on page {page}: {e}")
            break

    print(f"[Doffin] Total: {len(all_results)}")
    return all_results

# ── HILMA (FINLAND) ────────────────────────────────────────────────────────────

def fetch_hilma(session, from_dt):
    if not HILMA_API_KEY:
        print("\n[HILMA] No API key set — skipping. See instructions at top of file.")
        return []

    print("\n[HILMA] Fetching from HILMA (Finland)...")
    base_url = "https://hns-hilma-prod-apim.azure-api.net/avp/hilmatenders/"
    headers  = {"Ocp-Apim-Subscription-Key": HILMA_API_KEY}

    # HILMA accepts CPV codes semicolon-delimited
    cpv_string = ";".join(CPV_CODES)
    date_from  = from_dt.strftime("%Y-%m-%d")

    params = {
        "CPV":           cpv_string,
        "publishedFrom": date_from,
    }

    try:
        resp = session.get(base_url, headers=headers, params=params, timeout=30)
        print(f"  Status: {resp.status_code}")

        if resp.status_code == 401:
            print("  [HILMA] Invalid API key. Check HILMA_API_KEY.")
            return []
        if resp.status_code != 200:
            print(f"  [HILMA] Error: {resp.text[:300]}")
            return []

        data = resp.json()
        notices = data if isinstance(data, list) else data.get("tenders", data.get("notices", []))
        print(f"[HILMA] Got {len(notices)} notices")

        results = []
        for n in notices:
            title = n.get("name", n.get("title", ""))
            results.append({
                "Score":      score_tender(str(title)),
                "FleetSize":  extract_fleet_size(str(title)),
                "Title":      str(title),
                "Buyer":      str(n.get("organisation", n.get("organization", ""))),
                "CPV Code":   str(n.get("cpv", "")),
                "CPV Desc":   "",
                "Est. Value": "",
                "Currency":   "EUR",
                "Published":  str(n.get("entrydate", n.get("publishedDate", ""))),
                "Deadline":   str(n.get("tenderdate", n.get("deadline", ""))),
                "Country":    "Finland",
                "URL":        str(n.get("url", ""))
            })

        print(f"[HILMA] Matches: {len(results)}")
        return results

    except Exception as e:
        print(f"[HILMA] Error: {e}")
        return []

# ── SAVE TO EXCEL ──────────────────────────────────────────────────────────────

def save_to_excel(uk_rows, il_rows, ted_rows, doffin_rows, hilma_rows, filename):
    wb = openpyxl.Workbook()
    headers = ["Score", "FleetSize", "Title", "Buyer", "CPV Code", "CPV Desc",
               "Est. Value", "Currency", "Published", "Deadline", "Country", "URL"]

    def write_sheet(ws, rows, empty_msg):
        ws.append(headers)
        if rows:
            for row in rows:
                ws.append([row.get(h, "") for h in headers])
        else:
            ws.append([empty_msg])

    ws_uk = wb.active
    ws_uk.title = "UK Tenders"
    write_sheet(ws_uk, uk_rows, "No UK results found")

    ws_ted = wb.create_sheet("EU TED Tenders")
    write_sheet(ws_ted, ted_rows, "No TED results found")

    ws_doffin = wb.create_sheet("Norway Doffin")
    write_sheet(ws_doffin, doffin_rows,
                "No results — add DOFFIN_API_KEY (free) at top of script")

    ws_hilma = wb.create_sheet("Finland HILMA")
    write_sheet(ws_hilma, hilma_rows,
                "No results — add HILMA_API_KEY (free) at top of script")

    ws_il = wb.create_sheet("Israel Tenders")
    write_sheet(ws_il, il_rows, "No Israel results found")

    wb.save(filename)
    print(f"\n✓ Saved: {filename}")
    print(f"  UK:      {len(uk_rows)}")
    print(f"  TED EU:  {len(ted_rows)}")
    print(f"  Norway:  {len(doffin_rows)}")
    print(f"  Finland: {len(hilma_rows)}")
    print(f"  Israel:  {len(il_rows)}")

# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  ISZE TENDER MONITOR v5")
    print(f"  Last {LOOKBACK_DAYS} days | Markets: UK, EU, Norway, Finland, Israel")
    print("=" * 60)

    now     = datetime.now(timezone.utc)
    from_dt = now - timedelta(days=LOOKBACK_DAYS)

    with requests.Session() as s:
        uk_rows     = fetch_uk(s, from_dt, now)
        ted_rows    = fetch_ted(s, from_dt)
        doffin_rows = fetch_doffin(s, from_dt)
        hilma_rows  = fetch_hilma(s, from_dt)
        il_rows     = fetch_israel(s)

    save_to_excel(uk_rows, il_rows, ted_rows, doffin_rows, hilma_rows, OUTPUT_FILE)
    print("\nDone.")
    print("=" * 60)

if __name__ == "__main__":
    main()
