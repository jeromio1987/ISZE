from __future__ import annotations

import ast
import hashlib
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Domain dictionaries
# ---------------------------------------------------------------------------

COUNTRY_NAME_MAP = {
    "AUT": "Austria",
    "BEL": "Belgium",
    "BGR": "Bulgaria",
    "CYP": "Cyprus",
    "CZE": "Czechia",
    "DEU": "Germany",
    "DNK": "Denmark",
    "ESP": "Spain",
    "EST": "Estonia",
    "FIN": "Finland",
    "FRA": "France",
    "GB": "United Kingdom",
    "GBR": "United Kingdom",
    "GRC": "Greece",
    "HRV": "Croatia",
    "HUN": "Hungary",
    "IRL": "Ireland",
    "ISR": "Israel",
    "ITA": "Italy",
    "LTU": "Lithuania",
    "LUX": "Luxembourg",
    "LVA": "Latvia",
    "MLT": "Malta",
    "NLD": "Netherlands",
    "NOR": "Norway",
    "POL": "Poland",
    "PRT": "Portugal",
    "ROU": "Romania",
    "SVK": "Slovakia",
    "SVN": "Slovenia",
    "SWE": "Sweden",
    "UK": "United Kingdom",
}

COUNTRY_CLUSTER_MAP = {
    "United Kingdom": "UK/IE Lead",
    "Ireland": "UK/IE Lead",
    "Germany": "DACH Lead",
    "Austria": "DACH Lead",
    "Switzerland": "DACH Lead",
    "Netherlands": "Benelux Lead",
    "Belgium": "Benelux Lead",
    "Luxembourg": "Benelux Lead",
    "Norway": "Nordics Lead",
    "Finland": "Nordics Lead",
    "Sweden": "Nordics Lead",
    "Denmark": "Nordics Lead",
    "Spain": "Iberia Lead",
    "Portugal": "Iberia Lead",
    "France": "France Lead",
    "Italy": "Italy Lead",
    "Israel": "Israel Lead",
    "Bulgaria": "CEE Lead",
    "Croatia": "CEE Lead",
    "Czechia": "CEE Lead",
    "Estonia": "CEE Lead",
    "Greece": "CEE Lead",
    "Hungary": "CEE Lead",
    "Latvia": "CEE Lead",
    "Lithuania": "CEE Lead",
    "Poland": "CEE Lead",
    "Romania": "CEE Lead",
    "Slovakia": "CEE Lead",
    "Slovenia": "CEE Lead",
    "Cyprus": "South EU Lead",
    "Malta": "South EU Lead",
}

# v3: ISZE's active markets — used for country filtering at scrape time
ISZE_TARGET_MARKETS = {
    "GBR", "IRL", "POL", "PRT", "GRC", "ISR",
    "DEU", "FRA", "ESP", "ITA", "NLD", "BEL",
    "DNK", "SWE", "NOR", "FIN", "ROU", "HUN",
    "CZE", "SVK", "BGR", "HRV", "AUT", "LVA",
    "LTU", "EST", "SVN",
    "CYP", "MLT",
}

OWNER_OPTIONS = [
    "Unassigned",
    "UK/IE Lead",
    "DACH Lead",
    "Benelux Lead",
    "Nordics Lead",
    "Iberia Lead",
    "France Lead",
    "Italy Lead",
    "CEE Lead",
    "South EU Lead",
    "Israel Lead",
    "Strategic Accounts",
    "Bid Desk",
]

STATUS_OPTIONS = [
    "Needs owner",
    "Bid / No-Bid",
    "Enrich",
    "Review",
    "Watch",
    "Partnering",
    "Bid in progress",
    "Submitted",
    "Won",
    "Lost",
    "Contract live",
]

SOURCE_SHEET_MAP = {
    "UK Tenders": "🇬🇧 UK",
    "UK Contracts Finder": "🇬🇧 UK-CF",
    "Germany National": "🇩🇪 DE",
    "EU TED Tenders": "🇪🇺 EU",
    "Norway Doffin": "🇳🇴 Norway",
    "Finland HILMA": "🇫🇮 Finland",
    "Israel Tenders": "🇮🇱 Israel",
    "Belgium": "🇧🇪 BE",
    "Netherlands": "🇳🇱 NL",
    "France BOAMP": "🇫🇷 FR-BOAMP",
    "Poland BZP": "🇵🇱 PL-BZP",
    "Ireland eTenders": "🇮🇪 IE-eTenders",
}

SOURCE_COUNTRY_FALLBACK = {
    "🇬🇧 UK": "United Kingdom",
    "🇬🇧 UK-CF": "United Kingdom",
    "🇩🇪 DE": "Germany",
    "🇪🇺 EU": "European Union",
    "🇳🇴 Norway": "Norway",
    "🇫🇮 Finland": "Finland",
    "🇮🇱 Israel": "Israel",
    "🇧🇪 BE": "Belgium",
    "🇳🇱 NL": "Netherlands",
    "🇫🇷 FR-BOAMP": "France",
    "🇵🇱 PL-BZP": "Poland",
    "🇮🇪 IE-eTenders": "Ireland",
}

BRAND_TERMS = [
    "isuzu", "d-max", "d max", "dmax", "n-series", "n series", "f-series", "f series",
]

SERVICE_TERMS = [
    "maintenance", "service contract", "repair and maintenance", "servicing", "after-sales",
    "aftersales", "spare parts", "parts supply", "parts and labour", "fleet management",
    "preventive maintenance", "corrective maintenance", "full maintenance", "scheduled maintenance",
    "vehicle maintenance", "repair", "overhaul", "upkeep", "workshop", "support services",
    "wartung", "instandhaltung", "reparatur", "fahrzeugwartung", "werkstatt", "ersatzteile",
    "entretien", "réparation", "reparation", "révision", "atelier", "gestion de flotte",
    "mantenimiento", "reparación", "reparacion", "taller", "mantenimiento de vehículos",
    "manutenzione", "riparazione", "officina", "ricambi", "assistenza", "gestione flotta",
    "konserwacja", "naprawa", "serwis", "utrzymanie", "warsztat",
    "onderhoud", "reparatie", "werkplaats", "onderdelen", "voertuigonderhoud",
    "manutenção", "manutencao", "reparação", "reparacao",
    "mentenanță", "mentenanta", "reparații", "reparatii", "întreținere", "intretinere",
    "karbantartás", "karbantartas", "javítás", "javitas", "szerviz",
    "údržba", "udrzba", "oprava", "underhåll", "underhall", "reservdelar",
    "vedligeholdelse", "reservedele", "værksted", "vaerksted",
    "תחזוקה", "תיקון", "חלקי חילוף", "ניהול צי",
]

# R&M contract terms — stricter than SERVICE_TERMS.
# These indicate a fleet operator is outsourcing repair AND maintenance of their
# vehicles to a third-party contractor who will need a guaranteed supply of genuine
# Isuzu parts. Highest-value lead type for ISZE distributor development.
# CPV 501xx range (fleet management / repair services) is the clearest API signal.
RM_CONTRACT_TERMS = [
    # English — core phrases
    "repair and maintenance", "maintenance and repair", "repair, maintenance",
    "full maintenance", "full service maintenance", "fleet maintenance",
    "vehicle maintenance service", "maintenance contract", "service and maintenance",
    "r&m", "r & m",
    "preventive maintenance", "corrective maintenance",
    "fleet management", "fleet management service", "fleet management and repair",
    "repair and maintenance services", "maintenance and repair services",
    "scheduled maintenance", "unscheduled maintenance",
    "breakdown and maintenance", "maintenance, repair",
    # German
    "wartung und reparatur", "reparatur und wartung", "fahrzeugwartung",
    "vollwartung", "flottenmanagement", "instandhaltung und reparatur",
    "wartungsvertrag", "wartungs- und reparaturvertrag",
    # French
    "réparation et entretien", "entretien et réparation", "reparation et entretien",
    "maintenance et réparation", "contrat de maintenance", "gestion de flotte",
    "entretien préventif", "entretien correctif",
    # Spanish
    "reparación y mantenimiento", "mantenimiento y reparación", "mantenimiento correctivo",
    "mantenimiento preventivo", "gestión de flota", "contrato de mantenimiento",
    # Italian
    "riparazione e manutenzione", "manutenzione e riparazione",
    "manutenzione correttiva", "manutenzione preventiva",
    "gestione della flotta", "contratto di manutenzione",
    # Polish
    "naprawa i konserwacja", "konserwacja i naprawa", "zarządzanie flotą",
    "serwis i naprawa", "utrzymanie i naprawa",
    # Dutch
    "reparatie en onderhoud", "onderhoud en reparatie", "wagenparkbeheer",
    "preventief onderhoud", "correctief onderhoud",
    # Portuguese
    "reparação e manutenção", "manutenção e reparação", "gestão de frota",
    "manutenção preventiva", "manutenção corretiva",
    "manutenção de viaturas", "manutenção de veículos",
    "reparação de viaturas", "assistência de viaturas",
    # Romanian
    "reparatii si intretinere", "mentenanta si reparatii",
    "întreținere flotă", "intretinere flota", "mentenanță flotă",
    # Hungarian / Czech
    "jármű karbantartás", "jarmu karbantartas", "flotta karbantartás",
    "údržba vozidel", "udrzba vozidel", "oprava vozidel",
    # Swedish / Danish / Norwegian
    "reparation och underhåll", "underhåll och reparation",
    "reparation og vedligeholdelse", "vedligeholdelse og reparation",
    "vedligeholdelse af køretøjer", "køretøjsvedligeholdelse",
    "reparasjon og vedlikehold", "vedlikehold og reparasjon",
    # Hebrew
    "תיקון ותחזוקה", "תחזוקה ותיקון", "ניהול צי רכבים",
    # Extra Phase-2 service terminology (also used as R&M signal when paired)
    "manutenzione", "entretien", "wartung", "onderhoud", "mantenimiento",
    "manutenção", "manutencao", "konserwacja", "údržba", "udrzba",
    "mentenanță", "mentenanta", "karbantartás", "karbantartas",
    "vedlikehold", "underhåll", "underhall",
]


# ---------------------------------------------------------------------------
# Aftersales hook tags (commercial clarity for ISZE parts / service)
# Only set from notice text or CPV evidence — never invent a contract.
# Stable tag ids → chips on v4. See _AFTERSALES_TAGS.md.
# ---------------------------------------------------------------------------
AFTERSALES_TAG_ORDER = [
    "service_contract",
    "repair_maintenance",
    "parts",
    "extended_warranty",
    "full_service_lease",
]

AFTERSALES_TAG_LABELS = {
    "service_contract": "Service contract",
    "repair_maintenance": "R&M",
    "parts": "Parts",
    "extended_warranty": "Ext. warranty",
    "full_service_lease": "Full-service lease",
}

# Service / maintenance *contract* language (not bare "repair")
AFTERSALES_SERVICE_CONTRACT_TERMS = [
    "service contract", "maintenance contract", "service agreement",
    "maintenance agreement", "servicing contract", "aftersales contract",
    "after-sales contract", "support contract", "fleet service contract",
    "contrat de service", "contrat d'entretien", "contrat de maintenance",
    "contrat entretien", "marché d'entretien", "marche d'entretien",
    "wartungsvertrag", "servicevertrag", "instandhaltungsvertrag",
    "wartungs- und reparaturvertrag", "full-service-vertrag",
    "serviceavtal", "underhållsavtal", "underhallsavtal", "serviceaftale",
    "vedligeholdelsesaftale", "serviceavtale", "vedlikeholdsavtale",
    "huoltosopimus", "ylläpitosopimus", "yllapitosopimus",
    "contratto di manutenzione", "contratto di servizio",
    "contrato de mantenimiento", "contrato de serviço", "contrato de servico",
    "contrato de manutenção", "contrato de manutencao",
    "manutenção de viaturas", "manutencao de viaturas",
    "manutenção de veículos", "manutencao de veiculos",
    "assistência técnica de viaturas", "assistencia tecnica de viaturas",
    "umowa serwisowa", "umowa serwis", "umowa na serwis",
    "onderhoudscontract", "servicecontract",
    "contract de mentenanță", "contract de mentenanta",
    "contract de întreținere", "contract de intretinere",
    "karbantartási szerződés", "karbantartasi szerzodes",
    "smlouva o údržbě", "smlouva o udrzbe",
    "vedligeholdelse af køretøjer", "vedligeholdelse af koretojer",
    "חוזה שירות", "חוזה תחזוקה", "הסכם שירות", "הסכם תחזוקה",
]

AFTERSALES_PARTS_TERMS = [
    "spare parts", "parts supply", "parts and labour", "parts and labor",
    "replacement parts", "genuine parts", "oem parts", "parts package",
    "supply of parts", "parts provisioning", "consumables and parts",
    "pièces détachées", "pieces detachees", "pièces de rechange",
    "pieces de rechange", "fourniture de pièces", "fourniture de pieces",
    "ersatzteile", "ersatzteilversorgung", "ersatzteil",
    "ricambi", "parti di ricambio", "fornitura ricambi",
    "repuestos", "piezas de recambio", "suministro de piezas",
    "onderdelen", "reservdelar", "reservedele", "varaosat",
    "części zamienne", "czesci zamienne",
    "peças", "pecas", "peças para viaturas", "pecas para viaturas",
    "peças de reposição", "pecas de reposicao",
    "piese de schimb", "piese schimb",
    "alkatrész", "alkatresz", "náhradní díly", "nahradni dily",
    "חלקי חילוף", "חלפים", "אספקת חלקים",
]

AFTERSALES_EXTENDED_WARRANTY_TERMS = [
    "extended warranty", "warranty extension", "extended guarantee",
    "prolonged warranty", "extra warranty", "warranty package",
    "garantie étendue", "garantie etendue", "garantie prolongée",
    "garantie prolongee", "extension de garantie",
    "erweiterte garantie", "anschlussgarantie", "garantieerweiterung",
    "verlängerte gewährleistung", "verlangerte gewahrleistung",
    "garanzia estesa", "estensione di garanzia",
    "garantía extendida", "garantia extendida", "ampliación de garantía",
    "förlängd garanti", "forlangd garanti", "udvidet garanti",
    "verlengde garantie", "przedłużona gwarancja", "przedluzona gwarancja",
    "אחריות מורחבת", "הארכת אחריות",
]

AFTERSALES_FULL_SERVICE_LEASE_TERMS = [
    "full-service lease", "full service lease", "fullservice lease",
    "full service leasing", "full-service leasing", "wet lease",
    "operational lease with maintenance", "lease including maintenance",
    "lease with maintenance", "leasing with maintenance",
    "leasing avec entretien", "location avec entretien",
    "vollservice-leasing", "vollserviceleasing", "fullserviceleasing",
    "fullservice-leasing", "wetlease",
    "leasing con manutenzione", "leasing con mantenimiento",
    "operational leasing met onderhoud",
]

AFTERSALES_KEYWORD_SETS = {
    "service_contract": AFTERSALES_SERVICE_CONTRACT_TERMS,
    "parts": AFTERSALES_PARTS_TERMS,
    "extended_warranty": AFTERSALES_EXTENDED_WARRANTY_TERMS,
    "full_service_lease": AFTERSALES_FULL_SERVICE_LEASE_TERMS,
}

FRAMEWORK_TERMS = [
    "framework agreement", "framework contract", "dynamic purchasing", "dps", "multi-year",
    "annual contract", "call-off", "call off", "blanket order", "framework", "lot ", "lots ",
    "rahmenvertrag", "rahmenvereinbarung", "accord-cadre", "accord cadre", "acuerdo marco",
    "accordo quadro", "umowa ramowa", "raamovereenkomst", "acordo quadro", "acordo-quadro",
    "acord-cadru", "acord cadru", "keretmegállapodás", "keretmegallapodas",
    "rámcová smlouva", "ramcova smlouva", "ramavtal", "rammeaftale",
]

VEHICLE_TERMS = [
    "vehicle", "vehicles", "truck", "trucks", "van", "vans", "pickup", "pick-up",
    "pick up", "4x4", "chassis cab", "tipper", "dropside", "crew cab", "double cab",
    "flatbed", "box van", "fleet", "commercial vehicle", "light truck", "medium truck",
    "rigid truck", "refuse vehicle", "municipal vehicle", "utility vehicle", "light utility",
    "motor vehicle", "goods vehicle", "public works vehicle", "road maintenance",
    "טנדר", "משאית", "רכב מסחרי", "צי רכבים",
]

PICKUP_TRUCK_TERMS = [
    "pickup", "pick-up", "pick up", "4x4", "utility vehicle", "chassis cab", "crew cab",
    "double cab", "single cab", "extra cab", "d-max", "d max", "dmax",
]

LIFECYCLE_TERMS = {
    "planning": [
        "prior information", "pipeline", "planning notice", "information notice",
        "preliminary market engagement", "market consultation",
    ],
    "result": [
        "award notice", "contract award", "contract details", "direct award", "winner",
        "award", "jälki-ilmoitus", "result notice", "award decision",
    ],
    "completion": [
        "performance notice", "completion notice", "termination", "contract performance",
    ],
    "change": [
        "corrigendum", "change notice", "modification notice", "amendment", "corrigendum",
    ],
}

# v3/v4: CPV codes that are in-scope for "vehicles" but completely out-of-scope for ISZE.
# Any notice whose CPV starts with one of these prefixes is discarded before scoring.
EXCLUDED_CPV_PREFIXES: Tuple[str, ...] = (
    "34120",   # Buses and coaches
    "34121",   # Coaches and buses (subgroup)
    "34144210", "34144211", "34144212",  # Firefighting vehicles
    "34144510", "34144511", "34144512",  # Refuse-collection / compaction vehicles
    "34144700",  # Ambulances
    "34144720",  # Stretcher vehicles
    "34144400",  # Military / armoured vehicles
    "34142",   # Tractor units and special trailers (heavy haulage)
    "34143",   # Winter-maintenance vehicles
    "600",     # Transport services (passenger/route) — wrong family for Isuzu LCV/parts
    "60170",   # Hire of passenger transport vehicles with driver
    "60112",   # Public road transport services
    "42414",   # Cranes and lifting equipment
    "34223",   # Trailers (non-vehicle)
    "35110",   # Firefighting / rescue equipment
    "501181",  # Tyre repair / remould / supply services
)

# CPV prefixes that are Isuzu-core without needing extra title tokens
# (pickups, 4WD, goods vehicles, truck R&M). Panel-van CPV 34136 alone is NOT
# core — postal/courier panel vans are hard-dropped (see passes_not_for_us_gate).
ISUZU_CORE_CPV_PREFIXES: Tuple[str, ...] = (
    "34131",   # Pickups — D-Max core
    "34113",   # 4WD vehicles
    "34130",   # Motor vehicles for goods transport
    "50114",   # Repair and maintenance of trucks
)

# Title/description noise — passenger routes, SEND, towing, cemetery kit, etc.
# Hebrew passenger/taxi/bus/tow/tyre/fire — pairs with Hebrew LCV keep-signals below.
ISUZU_NOISE_TITLE_RE = re.compile(
    r"(?i)("
    r"\bsend\b|special educational|client transport|"
    r"passenger transport|passenger vehicle|passenger car|"
    r"4[- ]?seat(?:ed)?|cemeter|"
    r"towing[- ]away|vehicle towing|tow[- ]away|"
    r"sweeping machine|car ?sharing|"
    r"tyre repair|tire repair|tyre supply|tire supply|"
    r"firefight|feuerwehr|ambulance|refuse[- ]collection|"
    # Hebrew noise (Latin EU patterns unchanged)
    r"רכב\s*פרטי|מונית|מוניות|אוטובוס|אוטובוסים|"
    r"הסעת\s*נוסעים|הסעות|"
    r"כיבוי|כבאות|אמבולנס|גרירה|"
    r"צמיג|צמיגים|אופנוע|אופנועים"
    r")"
)

# Positive LCV / Isuzu / goods-fleet signals (multilingual light set)
# NOTE: do NOT use bare \bvan\b — Dutch "van" (of/from) false-positives TenderNed titles.
# Hebrew keep-signals mirror Latin LCV/fleet/R&M; do NOT add bare תחזוקה (IT/facility noise).
ISUZU_LCV_SIGNAL_RE = re.compile(
    r"(?i)("
    r"isuzu|d[- ]?max|n[- ]?series|f[- ]?series|"
    r"pickup|pick[- ]?up|chassis(?:\s+cab)?|tipper|dropside|"
    r"crew cab|double cab|flatbed|box van|panel van|"
    r"4x4|\blcv\b|goods vehicle|commercial vehicle|light goods|"
    r"municipal vehicle|public works|rigid(?:\s+truck)?|"
    r"light truck|medium truck|utility vehicle|off[- ]road|all[- ]terrain|"
    r"\bvans\b|\btruck\b|\btrucks\b|"
    r"vehicle fleet|fleet of|parc (?:de |automobile)|flotte (?:de |v[eé]hicule)|"
    r"furgon|camionnette|bestelwagen|bestelauto|bedrijfswagen|benne|nacelle|"
    # DE/AT goods-truck (bund RSS often has title-only, no CPV) — not PKW/Transporter
    r"\blkw\b|\bnkw\b|nutzfahrzeuge?n?|pritsche|fahrgestell|kofferaufbau|"
    r"3[.,]5\s*t(?:onne)?|7[.,]5\s*t(?:onne)?|12\s*t(?:onne)?|"
    # Nordic commercial (DK/NO/SE) — lastbil not lastbilar?-only; skip bare bil/el-bil/køretøj
    r"\blastbil(?:ar|er)?\b|\blastebil(?:er)?\b|\bvarebil(?:er)?\b|"
    r"\btippelad\b|\bakslet\b|\blastvogn(?:e|en)?\b|"
    # Hebrew LCV / commercial / fleet (word-ish; avoid סטנדרטים false טנדר)
    r"משאי(?:ת|ות)|(?<![א-ת])טנדר(?:ים|ונים|ון)?(?![א-ת])|"
    r"רכב\s*מסחרי|רכבים?\s*מסחרי(?:ים|ות)?|מסחריים|"
    r"צי\s*רכבי?ם?|כלי\s*רכב|רכב\s*שטח|"
    r"תחזוק[הת]\s*(?:ל)?משאי|משאי(?:ת|ות).{0,12}תחזוק|"
    r"מכליות|מרכבים|"
    # Common Latin transliteration of Hebrew LCV terms (not bare English "tender")
    r"\bmasait\b|\bmasa['’]?it\b|\brechev\b|\brekhev\b|\bmischar(?:i)?\b"
    r")"
)

# v3: CPV codes that are the ISZE sweet spot — used to give a CPV bonus in scoring
ISZE_TARGET_CPV_PREFIXES: Tuple[str, ...] = (
    "34131",   # Pickups — D-Max core
    "34113",   # 4WD vehicles
    "34136",   # Vans
    "34130",   # Motor vehicles for goods transport
    "34114",   # Special-purpose vehicles (ambiguous — kept but lower weight)
    "50110",   # Repair and maintenance of motor vehicles
    "50112",   # Repair of cars
    "50116",   # Repair of specific vehicle parts
    "50111",   # Vehicle fleet management and repair services
)

CPV_SERVICE_PREFIXES = ("501",)
CPV_VEHICLE_PREFIXES = ("341",)

# Product-fit segments — operator-facing product reality (not score polish).
# GPS wallet in gps_spu_by_distributor.csv is one SPU per distributor (pickup/network
# UIO); there is no separate N-Series SPU — so pure van/LCV must not get GPS €.
PRODUCT_SEGMENTS = ("pickup", "lcv_van", "truck", "rm_only", "weak")
PRODUCT_SEGMENT_LABELS: Dict[str, str] = {
    "pickup": "Pickup / D-Max-shaped",
    "lcv_van": "Postal van / LCV",
    "truck": "Truck / chassis",
    "rm_only": "R&M only — no vehicle buy",
    "weak": "Generic vehicle — weak fit",
}
# Segments eligible for GPS € when fleet + distributor SPU exist.
GPS_ELIGIBLE_SEGMENTS = frozenset({"pickup", "truck"})

# Discriminating product-shape regexes (order applied in classify_product_segment).
_PICKUP_SHAPE_RE = re.compile(
    r"(?i)("
    r"\bpick[- ]?ups?\b|d[- ]?max|double cab|crew cab|single cab|extra cab|"
    r"chassis\s+cab\s+pickup|4x4\s+(?:pickup|utility|pick[- ]?up)|"
    r"טנדר"
    r")"
)
_TRUCK_SHAPE_RE = re.compile(
    r"(?i)("
    r"\btippers?\b|dropside|medium truck|rigid(?:\s+truck)?|heavy goods|\bhgv\b|"
    r"\btrucks?\b|chassis\s+cab(?!\s+pickup)|kipper|\bbenne\b|"
    r"six[- ]wheel|6[- ]wheel|dump truck|tipper truck|"
    r"n[- ]?series|f[- ]?series|"
    # DE/AT goods-truck stems (not PKW / Transporter panel van)
    r"\blkw\b|\bnkw\b|nutzfahrzeuge?n?|nutz kraftwagen|nutz kraftwagen|"
    r"pritsche|fahrgestell|kofferaufbau|einzelkabine|"
    r"ci[eę][zż]arow\w*|samochod(?:y|ów)?\s+ci[eę][zż]ar|"
    r"\bdmc\b|gvw|gvwr|"
    r"(?:do|tot|up to|max\.?)\s*\d+[.,]?\d*\s*t(?:onne|on)?\b|"
    r"\d+[.,]?\d*\s*t(?:onne|on)?(?:\s+(?:gvw|dmc|truck|lorry))|"
    r"lichte\s+vrachtwagens?|vrachtwagens?|"
    # Nordic goods-truck (DK lastbil / NO lastebil / SE lastbil) — not passenger el-bil
    r"\blastbil(?:ar|er)?\b|\blastebil(?:er)?\b|\blastvogn(?:e|en)?\b|"
    r"\btippelad\b|\bakslet\b|\b\d[- ]?akslet\b|"
    r"משאית|משאיות"
    r")"
)
_LCV_VAN_SHAPE_RE = re.compile(
    r"(?i)("
    r"\bvans\b|panel van|box van|postal|courier|"
    r"autovehicul(?:e)?\s+utilitar|utilitar(?:e|ă|a)?|"
    r"furgon|camionnette|bestelwagen|bestelauto|bedrijfswagen|"
    r"light commercial|\blcv\b|parcels?\s+van|delivery van|"
    r"–\s*vans?\s*–|—\s*vans?\s*—|"
    r"רכב\s*מסחרי|רכבים?\s*מסחרי"
    r")"
)
# Postal / courier buyers and panel-van purchase shapes — not an Isuzu D-Max desk play.
# Hard-drop from opportunities (not merely GPS-null). See _NOT_FOR_US_GATE.md.
POSTAL_COURIER_NOT_FOR_US_RE = re.compile(
    r"(?i)("
    r"\bposta\b|po[sșşš]ta|post\s*(?:office|europ)|"
    r"posta\s*romana|c\.?n\.?\s*posta|hrvatska\s*po[sš]ta|"
    r"la\s*poste|\bbpost\b|deutsche\s*post|royal\s*mail|"
    r"\bcourier\b|parcel\s*force|\bdpd\b|\bgls\b|"
    r"postal\s*(?:service|fleet|van|vehicle)|"
    r"parcels?\s+van|delivery\s+van"
    r")"
)
PANEL_VAN_PURCHASE_RE = re.compile(
    r"(?i)("
    r"panel\s*van|kastenwagen|\btransporter\b|"
    r"autovehicul(?:e)?\s+utilitar|utilitar(?:e|ă|a)?|"
    r"autoutilitar|"
    r"bestelwagen|bestelauto|electrische\s+bestelwagen|"
    r"camionnette|furgon|box\s*van|"
    r"e[- ]?utilities|aankopen\s+van\s+bestel|"
    r"leasing.{0,40}(?:van|utilitar|bestel|furgon|transporter)|"
    r"(?:van|utilitar|bestel|furgon|transporter).{0,40}leasing"
    r")"
)
_VEHICLE_BUY_RE = re.compile(
    r"(?i)("
    r"leasing|lease|purchase|procurement of|supply of|acquisition|"
    r"achizi[tț]|acquisto|lieferung|livraison|aanschaf|"
    r"\bnoi\b|\bnew\s+(?:van|vans|truck|trucks|vehicle|vehicles|pickup)|"
    r"autovehicule?\s+noi|vehicule?\s+noi"
    r")"
)

TIER_ORDER = {"large": 0, "medium": 1, "small": 2, "micro": 3, "unknown": 4}
DECISION_ORDER = {"Attack": 0, "Selective": 1, "Watch": 2, "Ignore": 3}
URGENCY_ORDER = {"critical": 0, "soon": 1, "ok": 2, "none": 3, "expired": 4}


# ---------------------------------------------------------------------------
# Basic text parsing helpers  (unchanged from v2)
# ---------------------------------------------------------------------------

def extract_text(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return ""
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                parsed = ast.literal_eval(s)
                return extract_text(parsed)
            except Exception:
                return s.strip("[]'\" ")
        return s.strip("[]'\" ")
    if isinstance(raw, dict):
        for key in ("eng", "EN", "ENG", "en", "description", "name", "title"):
            if key in raw and raw[key]:
                return extract_text(raw[key])
        for value in raw.values():
            txt = extract_text(value)
            if txt:
                return txt
        return ""
    if isinstance(raw, (list, tuple, set)):
        for item in raw:
            txt = extract_text(item)
            if txt:
                return txt
        return ""
    return str(raw).strip("[]'\" ")


def extract_list(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = ast.literal_eval(s)
                return [extract_text(x) for x in parsed if extract_text(x)]
            except Exception:
                return [s.strip("[]'\" ")]
        return [s.strip("[]'\" ")]
    if isinstance(raw, (list, tuple, set)):
        out = []
        for item in raw:
            txt = extract_text(item)
            if txt:
                out.append(txt)
        return out
    txt = extract_text(raw)
    return [txt] if txt else []


def ascii_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    return value


def normalize_text(value: str) -> str:
    value = ascii_text(value).lower()
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def compact_title(title: str) -> str:
    title = title or ""
    parts = [p.strip() for p in re.split(r"\s+[–—-]\s+", title) if p.strip()]
    if len(parts) >= 3 and normalize_country(parts[0]) != parts[0]:
        title = " - ".join(parts[2:])
    return title.strip()


def normalize_title_for_family(title: str) -> str:
    title = compact_title(title)
    title = normalize_text(title)
    title = re.sub(
        r"\b(corrigendum|correction|change notice|modification notice|amendment|award notice|contract award|jalki ilmoitus|results?|result notice)\b",
        " ",
        title,
    )
    title = re.sub(r"\b20\d{2}\b", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def parse_number(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, dict):
        for key in ("amount", "amountGross", "value", "estimatedValue"):
            if key in raw and raw[key] not in (None, ""):
                return parse_number(raw[key])
        return None
    if isinstance(raw, (list, tuple, set)):
        for item in raw:
            val = parse_number(item)
            if val is not None:
                return val
        return None
    s = extract_text(raw)
    if not s:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return float(s)
    s = s.replace(" ", "")
    s = s.replace(",", "") if s.count(",") > 1 else s
    s = re.sub(r"[^0-9.,-]", "", s)
    if not s:
        return None
    if s.count(",") == 1 and s.count(".") == 0:
        left, right = s.split(",")
        if len(right) <= 2:
            s = left + "." + right
        else:
            s = left + right
    elif s.count(".") > 1 and s.count(",") == 0:
        s = s.replace(".", "")
    try:
        return float(s)
    except Exception:
        return None


def parse_datetime_like(raw: Any) -> Optional[datetime]:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, (list, tuple, set)):
        for item in raw:
            dt = parse_datetime_like(item)
            if dt:
                return dt
        return None
    if isinstance(raw, dict):
        for key in ("date", "endDate", "publishedDate", "deadline"):
            if key in raw:
                dt = parse_datetime_like(raw[key])
                if dt:
                    return dt
        return None
    s = extract_text(raw)
    if not s or s in ("None", "nan"):
        return None
    if s.startswith("[") and s.endswith("]"):
        try:
            return parse_datetime_like(ast.literal_eval(s))
        except Exception:
            pass
    if re.fullmatch(r"\d{8}", s):
        try:
            return datetime.strptime(s, "%Y%m%d").replace(tzinfo=timezone.utc)
        except Exception:
            return None
    cleaned = s.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[+-]\d{2}:\d{2}", cleaned):
        cleaned = cleaned[:10]
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except Exception:
        pass
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
    ):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    try:
        dt = parsedate_to_datetime(cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def iso_date(raw: Any) -> str:
    dt = parse_datetime_like(raw)
    return dt.date().isoformat() if dt else ""


def iso_datetime(raw: Any) -> str:
    dt = parse_datetime_like(raw)
    if not dt:
        return ""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def days_until(deadline_raw: Any, now: Optional[datetime] = None) -> Optional[int]:
    dt = parse_datetime_like(deadline_raw)
    if not dt:
        return None
    now = now or datetime.now(timezone.utc)
    return (dt.date() - now.date()).days


def normalize_country(raw: Any) -> str:
    text = extract_text(raw)
    if not text:
        return ""
    up = text.upper()
    if up in COUNTRY_NAME_MAP:
        return COUNTRY_NAME_MAP[up]
    return text


def country_code(raw: Any) -> str:
    text = extract_text(raw).upper()
    if not text:
        return ""
    if len(text) in (2, 3):
        return text
    for code, name in COUNTRY_NAME_MAP.items():
        if name.lower() == text.lower() and len(code) == 3:
            return code
    return text[:3]


# Multilingual fleet-size extraction (Phase 2) — ported from _reference_fleet_extractor.py
_FLEET_NOUNS = (
    r"vehicles?|trucks?|vans?|lorr(?:y|ies)|buses?|coaches?|pick[\s-]?ups?|minibuses?"
    r"|v[ée]hicules?|camions?|camionnettes?|autobus"
    r"|fahrzeuge?n?|lkw|nkw|pkw|nutzfahrzeuge?n?|kraftfahrzeuge?n?|transporter"
    r"|veicoli?|autoveicoli?|autocarri?|automezzi?|furgoni?"
    r"|veh[íi]culos?|camiones?|furgonetas?|turismos?"
    r"|ve[íi]culos?|carrinhas?"
    r"|voertuigen?|bestelwagens?|vrachtwagens?"
    r"|pojazd[oóyw]*|samochod[oóyw]*|ci[eę][zż]ar[oó]w[a-z]*|ci[aą]gnik[oóyw]*"
    r"|vozidel|vozidla|vozidlo|automobil[uůy]?"
    r"|autovehicule?|autoutilitar[ae]?|automobile?"
    r"|g[ée]pj[aá]rm[uű][a-z]*"
    r"|fordon|lastbil(?:ar|er)?"
    r"|kj[oø]ret[oø]y|lastebil(?:er)?|varebil(?:er)?|k[øo]ret[øo]j(?:er)?"
    r"|ajoneuvo[a-z]*|kuorma-auto[a-z]*"
    r"|автомобил[а-я]*"
    r"|vozila?"
)
_FLEET_COUNTERS = r"st[uü]ck|szt|buc|db|ks|kpl|units?|stk|pcs"
_PAT_NUM_NOUN = re.compile(
    rf"(?<![\d/.,-])(\d{{1,4}})\s*(?:{_FLEET_COUNTERS})?\.?\s*(?:{_FLEET_NOUNS})\b", re.I
)
_PAT_NOUN_NUM = re.compile(
    rf"(?:{_FLEET_NOUNS})\W{{0,12}}?(?<![\d/.,-])(\d{{1,4}})\s*(?:{_FLEET_COUNTERS})\b", re.I
)
_PAT_FLEET_OF = re.compile(r"\bfleet\s+of\s+(\d{1,4})\b", re.I)
_FLEET_MAX = 3000


def extract_fleet_size(*fields: str) -> int:
    """Return maximum plausible fleet size from title/description fields, else 0.

    Guards: reject years 1900-2100, reject numbers abutting '/', cap at 3000,
    take the MAXIMUM plausible match (not the first). Accepts title and/or description.
    """
    text = " ".join(f for f in fields if f)
    if not text:
        return 0
    best = 0
    for pat in (_PAT_NUM_NOUN, _PAT_NOUN_NUM, _PAT_FLEET_OF):
        for match in pat.finditer(text):
            try:
                n = int(match.group(1))
            except Exception:
                continue
            if not (1 <= n <= _FLEET_MAX):
                continue
            if 1900 <= n <= 2100:
                continue
            s, e = match.span(1)
            before = text[max(0, s - 2):s]
            after = text[e:e + 2]
            if "/" in before or "/" in after:
                continue
            if n > best:
                best = n
    return best



def detect_aftersales(
    *,
    title: str = "",
    description: str = "",
    cpv_desc: str = "",
    cpv: str = "",
    rm_hits: Optional[List[str]] = None,
    rm_contract: bool = False,
) -> Dict[str, Any]:
    """Tag aftersales hooks from notice text / CPV only — never invent.

    Returns aftersales_tags (list), aftersales_summary (str|None),
    aftersales_evidence (tag -> matched snippets), aftersales_match_tip (str).
    Empty tags + null summary when nothing matched (vehicles-only).
    """
    blob = " ".join([title or "", cpv_desc or "", description or ""]).lower()
    cpv_s = str(cpv or "").strip()
    evidence: Dict[str, List[str]] = {}
    tags: List[str] = []

    for tag, terms in AFTERSALES_KEYWORD_SETS.items():
        hits = keyword_hits(blob, terms, limit=4)
        if hits:
            tags.append(tag)
            evidence[tag] = hits

    rm_matched = list(rm_hits or []) or keyword_hits(blob, RM_CONTRACT_TERMS, limit=4)
    cpv_service = cpv_s.startswith(CPV_SERVICE_PREFIXES)
    if rm_matched or cpv_service or rm_contract:
        if "repair_maintenance" not in tags:
            tags.append("repair_maintenance")
        bits = list(rm_matched[:3])
        if cpv_service:
            bits.append(f"CPV {cpv_s[:5] or '501'}xx")
        if not bits and rm_contract:
            bits.append("rm_contract")
        evidence["repair_maintenance"] = bits[:4]

    if cpv_s.startswith("50116") and "parts" not in tags:
        tags.append("parts")
        evidence["parts"] = [f"CPV {cpv_s[:8]}"]

    tags = [t for t in AFTERSALES_TAG_ORDER if t in tags]

    if not tags:
        return {
            "aftersales_tags": [],
            "aftersales_summary": None,
            "aftersales_evidence": {},
            "aftersales_match_tip": "No service/parts/warranty language found in notice",
        }

    labels = [AFTERSALES_TAG_LABELS.get(t, t) for t in tags]
    summary = " · ".join(labels)
    tip_bits = []
    for t in tags:
        matched = evidence.get(t) or []
        if matched:
            tip_bits.append(f"{AFTERSALES_TAG_LABELS.get(t, t)}: {', '.join(matched[:3])}")
        else:
            tip_bits.append(AFTERSALES_TAG_LABELS.get(t, t))
    tip = "Matched in notice — " + "; ".join(tip_bits)
    return {
        "aftersales_tags": tags,
        "aftersales_summary": summary,
        "aftersales_evidence": evidence,
        "aftersales_match_tip": tip,
    }


def attach_aftersales(row: Dict[str, Any]) -> Dict[str, Any]:
    """Add/refresh aftersales_* fields on a notice or opportunity row (idempotent)."""
    title = row.get("Title") or row.get("title") or row.get("title_raw") or ""
    description = row.get("Description") or row.get("description") or ""
    cpv_desc = row.get("CPV Desc") or row.get("cpv_desc") or ""
    cpv = row.get("CPV Code") or row.get("cpv_code") or ""
    # Opportunity families rarely carry full description — fall back to notice titles
    if not description and isinstance(row.get("notices"), list):
        description = " ".join(
            str(n.get("title") or "") for n in row["notices"] if isinstance(n, dict)
        )
    result = detect_aftersales(
        title=str(title),
        description=str(description),
        cpv_desc=str(cpv_desc),
        cpv=str(cpv),
        rm_hits=row.get("rm_hits") or [],
        rm_contract=bool(row.get("rm_contract")),
    )
    row.update(result)
    return row



def keyword_hits(text: str, candidates: Iterable[str], limit: int = 6) -> List[str]:
    haystack = (text or "").lower()
    hits: List[str] = []
    for term in candidates:
        if term.lower() in haystack and term not in hits:
            hits.append(term)
        if len(hits) >= limit:
            break
    return hits


def value_tier(value_amount: Optional[float]) -> str:
    if value_amount is None:
        return "unknown"
    if value_amount > 1_000_000:
        return "large"
    if value_amount >= 250_000:
        return "medium"
    if value_amount >= 50_000:
        return "small"
    if value_amount >= 0:
        return "micro"
    return "unknown"


def urgency_from_days(days: Optional[int]) -> str:
    if days is None:
        return "none"
    if days < 0:
        return "expired"
    if days <= 7:
        return "critical"
    if days <= 21:
        return "soon"
    return "ok"


def classify_lifecycle(text: str, notice_type: str = "") -> str:
    blob = f"{text or ''} {notice_type or ''}".lower()
    for stage in ("completion", "result", "change", "planning"):
        if any(term in blob for term in LIFECYCLE_TERMS[stage]):
            return stage
    return "competition"


def evidence_score(row: Dict[str, Any]) -> Tuple[int, str, List[str]]:
    score = 0
    gaps: List[str] = []
    checks = [
        ("Buyer", 12, "buyer"),
        ("CPV Code", 12, "cpv"),
        ("Country", 10, "country"),
        ("Published", 10, "published date"),
        ("Deadline", 14, "deadline"),
        ("Est. Value", 14, "value"),
        ("URL", 8, "url"),
        ("Source Notice ID", 10, "source notice id"),
        ("Notice Type", 5, "notice type"),
        ("Lifecycle", 5, "lifecycle"),
    ]
    for field, weight, label in checks:
        val = row.get(field)
        present = False
        if field == "Est. Value":
            present = row.get("value_amount") is not None
        elif field in ("Published", "Deadline"):
            present = bool(row.get(field) and iso_date(row.get(field)))
        else:
            present = bool(extract_text(val))
        if present:
            score += weight
        else:
            gaps.append(label)
    if score >= 75:
        return score, "High", gaps
    if score >= 50:
        return score, "Medium", gaps
    return score, "Low", gaps


def score_legacy(title: str, value_amount: Optional[float] = None) -> int:
    t = (title or "").lower()
    brand = any(k in t for k in BRAND_TERMS)
    service = any(k in t for k in SERVICE_TERMS)
    fw = any(k in t for k in FRAMEWORK_TERMS)
    high_value = bool(value_amount and value_amount > 500_000)
    if brand and service:
        return 5
    if service and fw:
        return 4
    if service:
        return 3
    if fw or high_value:
        return 2
    return 1


def relevance_score_1to5(
    title: str,
    country_code: Optional[str] = None,
    value_amount: Optional[float] = None,
) -> int:
    """Explicit 1–5 relevance: title (via score_legacy) + ISZE target market + value.

    Notices outside ISZE_TARGET_MARKETS are capped at 2 so relevance_pass (>=3)
    is false, but callers must still keep the row in the export.
    """
    base = score_legacy(title, value_amount)
    code = (country_code or "").strip().upper()
    if not code:
        return base
    if code in ISZE_TARGET_MARKETS:
        return base
    return min(base, 2)


def relevance_pass(score: int, threshold: int = 3) -> bool:
    return int(score) >= threshold


_XML_SAFE_ENTS = {"amp", "lt", "gt", "quot", "apos"}


def sanitize_xml_entities(text: str) -> str:
    """Replace HTML-only entities (&nbsp;, &laquo;, …) that break stdlib XML parse."""
    if not text:
        return text

    def _repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in _XML_SAFE_ENTS:
            return match.group(0)
        code = html.entities.name2codepoint.get(name)
        if code is not None:
            return chr(code)
        html5 = html.entities.html5.get(name + ";")
        return html5 if html5 else ""

    return re.sub(r"&([a-zA-Z][a-zA-Z0-9]+);", _repl, text)


def parse_xml_root(content: str):
    """Parse RSS/Atom XML after entity sanitize; recover parser on structural errors."""
    import xml.etree.ElementTree as ET

    if not content or not str(content).strip():
        raise ET.ParseError("empty document")
    sanitized = sanitize_xml_entities(content)
    try:
        return ET.fromstring(sanitized)
    except ET.ParseError as first:
        try:
            from lxml import etree

            parser = etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False)
            tree = etree.fromstring(sanitized.encode("utf-8", errors="replace"), parser=parser)
            return ET.fromstring(etree.tostring(tree))
        except Exception:
            raise first


def retry_after_seconds(
    header_value: Optional[str],
    attempt: int = 0,
    fallback_schedule: Optional[List[int]] = None,
) -> int:
    """Honor Retry-After (delta-seconds or HTTP-date); else scheduled backoff."""
    schedule = fallback_schedule or [30, 60, 90, 120, 180, 240]
    fallback = schedule[min(max(attempt, 0), len(schedule) - 1)]
    if header_value is None:
        return fallback
    raw = str(header_value).strip()
    if not raw:
        return fallback
    if raw.isdigit():
        return max(int(raw), 1)
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = (dt - datetime.now(timezone.utc)).total_seconds()
        return max(int(delta), 1) if delta > 0 else fallback
    except (TypeError, ValueError, OverflowError):
        return fallback


# ---------------------------------------------------------------------------
# v3: CPV exclusion gate
# ---------------------------------------------------------------------------

def cpv_is_excluded(cpv: str) -> bool:
    """Return True if this CPV code maps to a vehicle category ISZE does not compete in."""
    if not cpv:
        return False
    return cpv.startswith(EXCLUDED_CPV_PREFIXES)


def cpv_is_target(cpv: str) -> bool:
    """Return True if this CPV is in ISZE's sweet spot."""
    if not cpv:
        return False
    return cpv.startswith(ISZE_TARGET_CPV_PREFIXES)


def cpv_is_isuzu_core(cpv: str) -> bool:
    """Return True if CPV alone is enough for the Isuzu commercial net."""
    if not cpv:
        return False
    return cpv.startswith(ISUZU_CORE_CPV_PREFIXES)


def text_has_isuzu_noise(text: str) -> bool:
    return bool(text and ISUZU_NOISE_TITLE_RE.search(text))


def text_has_lcv_signal(text: str) -> bool:
    return bool(text and ISUZU_LCV_SIGNAL_RE.search(text))


def passes_isuzu_selection_gate(
    title: str = "",
    description: str = "",
    cpv: str = "",
    cpv_desc: str = "",
) -> bool:
    """Commercial shortlist gate for D-Max / N-Series / truck + real fleet R&M.

    Keeps notices with Isuzu-core CPV or an LCV/goods/fleet signal in the text.
    Drops transport-services CPV, passenger/SEND/towing noise, and generic
    passenger-car R&M with no LCV signal. Prefer this filter over score retune.

    Postal/courier panel-van buys are hard-dropped by passes_not_for_us_gate
    (called from row_passes_isuzu_selection_gate) — not merely GPS-null.
    """
    cpv_s = extract_text(cpv) if not isinstance(cpv, str) else (cpv or "").strip()
    if cpv_is_excluded(cpv_s):
        return False
    blob = " ".join([title or "", description or "", cpv_desc or ""])
    if text_has_isuzu_noise(blob):
        return False
    if cpv_is_isuzu_core(cpv_s):
        return True
    # Parent "motor vehicles" / car R&M: only with LCV signal
    if cpv_s.startswith("34100000") or cpv_s.startswith("50112"):
        return text_has_lcv_signal(blob)
    if text_has_lcv_signal(blob):
        return True
    return False


def is_postal_courier_not_for_us(title: str = "", description: str = "", buyer: str = "") -> bool:
    """True when buyer/title is postal/courier — near-zero exclusive D-Max play."""
    blob = " ".join([buyer or "", title or "", description or ""])
    return bool(blob and POSTAL_COURIER_NOT_FOR_US_RE.search(blob))


def is_panel_van_purchase_not_for_us(title: str = "", description: str = "") -> bool:
    """True when the notice is a panel-van / utilitar / transporter purchase."""
    blob = " ".join([title or "", description or ""])
    return bool(blob and PANEL_VAN_PURCHASE_RE.search(blob))


def passes_not_for_us_gate(
    title: str = "",
    description: str = "",
    cpv: str = "",
    cpv_desc: str = "",
    buyer: str = "",
    product_segment: str = "",
    aftersales_tags: Optional[List[str]] = None,
    rm_contract: bool = False,
) -> bool:
    """Hard commercial desk gate — drop what is not for Isuzu (not GPS-null only).

    DROP:
      - Postal / courier buyers and postal van fleets (Poșta, Hrvatska pošta, …)
      - Panel-van / utilitar / transporter / bestelwagen vehicle buys & leasing
      - product_segment == lcv_van vehicle buys (pure passenger/postal panel vans)

    KEEP:
      - pickup / truck (incl. chassis cab, tipper, N-Series-shaped)
      - rm_only and real fleet R&M / parts aftersales on commercial vehicles
        (when not a postal org and not a panel-van purchase)
      - weak (generic goods) — still in data; dashboard defaults to CV filter

    See _NOT_FOR_US_GATE.md.
    """
    blob = " ".join([title or "", description or "", cpv_desc or "", buyer or ""])
    if is_postal_courier_not_for_us(title, description, buyer):
        return False

    seg = (product_segment or "").strip()
    if not seg:
        code, _ = classify_product_segment(
            title, description, cpv, cpv_desc, rm_contract=rm_contract
        )
        seg = code

    if seg in ("pickup", "truck"):
        return True
    if seg == "rm_only":
        return True

    if seg == "lcv_van":
        # Panel-van / utilitar purchase or leasing → hard drop
        if is_panel_van_purchase_not_for_us(title, description):
            return False
        tags = list(aftersales_tags or [])
        has_as = bool(tags) or bool(rm_contract)
        # Real aftersales (parts / fleet R&M) without panel-van buy shape → keep
        if has_as and not _VEHICLE_BUY_RE.search(blob):
            return True
        # Remaining lcv_van (TED “Vans”, courier panel fleets, pure van buys) → drop
        return False

    # weak: leave to Isuzu selection + CV default filter on the desk
    return True


def row_passes_not_for_us_gate(row: Dict[str, Any]) -> bool:
    """Not-for-us gate on a notice/opportunity dict (ensures product_segment + aftersales)."""
    attach_product_segment(row)
    attach_aftersales(row)
    title = str(row.get("Title") or row.get("title") or row.get("title_raw") or "")
    desc = str(row.get("Description") or row.get("description") or "")
    cpv = str(row.get("CPV Code") or row.get("cpv") or row.get("cpv_code") or "")
    cpv_desc = str(row.get("CPV Desc") or row.get("cpv_desc") or "")
    buyer = str(row.get("Buyer") or row.get("buyer") or "")
    return passes_not_for_us_gate(
        title=title,
        description=desc,
        cpv=cpv,
        cpv_desc=cpv_desc,
        buyer=buyer,
        product_segment=str(row.get("product_segment") or ""),
        aftersales_tags=list(row.get("aftersales_tags") or []),
        rm_contract=bool(row.get("rm_contract")),
    )


def row_passes_isuzu_selection_gate(row: Dict[str, Any]) -> bool:
    """Gate a notice or opportunity dict (export or raw keys).

    Combines Isuzu selection (noise/CPV) with not-for-us hard drop
    (postal/courier panel vans). Order: classify segment → Isuzu → not-for-us.
    """
    attach_product_segment(row)
    title = str(row.get("Title") or row.get("title") or row.get("title_raw") or "")
    desc = str(row.get("Description") or row.get("description") or "")
    cpv = str(row.get("CPV Code") or row.get("cpv") or row.get("cpv_code") or "")
    cpv_desc = str(row.get("CPV Desc") or row.get("cpv_desc") or "")
    if not passes_isuzu_selection_gate(title, desc, cpv, cpv_desc):
        return False
    return row_passes_not_for_us_gate(row)


def classify_product_segment(
    title: str = "",
    description: str = "",
    cpv: str = "",
    cpv_desc: str = "",
    rm_contract: bool = False,
) -> Tuple[str, str]:
    """Return (segment_code, operator_label) from product reality — not fake precision.

    Priority: pickup > truck > lcv_van > rm_only > weak.
    Pickup beats van when both appear (mixed lot may include D-Max-shaped units).
    Pure postal/utilitar van → lcv_van. Desk then hard-drops those via
    passes_not_for_us_gate (GPS null alone is not enough).
    """
    cpv_s = extract_text(cpv) if not isinstance(cpv, str) else (cpv or "").strip()
    blob = " ".join([title or "", description or "", cpv_desc or ""])
    # CPV shortcuts (title can still upgrade pickup over van)
    cpv_pickup = cpv_s.startswith("34131") or cpv_s.startswith("34113")
    cpv_van = cpv_s.startswith("34136")
    cpv_goods = cpv_s.startswith("34130")
    cpv_truck_rm = cpv_s.startswith("50114")
    cpv_service = cpv_s.startswith(CPV_SERVICE_PREFIXES)

    has_pickup = bool(_PICKUP_SHAPE_RE.search(blob)) or cpv_pickup
    has_truck = bool(_TRUCK_SHAPE_RE.search(blob)) or cpv_truck_rm
    has_van = bool(_LCV_VAN_SHAPE_RE.search(blob)) or cpv_van
    has_buy = bool(_VEHICLE_BUY_RE.search(blob))

    if has_pickup:
        return "pickup", PRODUCT_SEGMENT_LABELS["pickup"]
    if has_truck and not has_van:
        return "truck", PRODUCT_SEGMENT_LABELS["truck"]
    if has_truck and has_van and not has_pickup:
        # "trucks and vans" / ciężarowe mislabeled TED Vans → truck-shaped
        return "truck", PRODUCT_SEGMENT_LABELS["truck"]
    if has_van:
        return "lcv_van", PRODUCT_SEGMENT_LABELS["lcv_van"]
    if cpv_goods and has_buy:
        # Generic goods vehicles with a buy signal — weak product shape
        return "weak", PRODUCT_SEGMENT_LABELS["weak"]
    if rm_contract or cpv_service:
        if not has_buy and not has_pickup and not has_truck and not has_van:
            return "rm_only", PRODUCT_SEGMENT_LABELS["rm_only"]
    return "weak", PRODUCT_SEGMENT_LABELS["weak"]


def attach_product_segment(row: Dict[str, Any]) -> Dict[str, Any]:
    """Set product_segment + product_segment_label on a notice/opportunity dict."""
    title = str(row.get("Title") or row.get("title") or row.get("title_raw") or "")
    desc = str(row.get("Description") or row.get("description") or "")
    cpv = str(row.get("CPV Code") or row.get("cpv") or row.get("cpv_code") or "")
    cpv_desc = str(row.get("CPV Desc") or row.get("cpv_desc") or "")
    rm = bool(row.get("rm_contract"))
    code, label = classify_product_segment(title, desc, cpv, cpv_desc, rm_contract=rm)
    row["product_segment"] = code
    row["product_segment_label"] = label
    return row


# ---------------------------------------------------------------------------
# v3: Revised scoring — lower base, requires dual signal, CPV-aware
# ---------------------------------------------------------------------------

def compute_scores(row: Dict[str, Any]) -> Tuple[int, int, int, List[str]]:
    text = " ".join(
        [
            row.get("Title", ""),
            row.get("CPV Desc", ""),
            row.get("Description", ""),
            row.get("Notice Type", ""),
        ]
    ).lower()
    cpv = extract_text(row.get("CPV Code"))

    brand_hits = keyword_hits(text, BRAND_TERMS)
    service_hits = keyword_hits(text, SERVICE_TERMS)
    framework_hits = keyword_hits(text, FRAMEWORK_TERMS)
    vehicle_hits = keyword_hits(text, VEHICLE_TERMS)
    pickup_hits = keyword_hits(text, PICKUP_TRUCK_TERMS)

    reasons: List[str] = []

    # --- Fit score ---
    # v3: Base is 0. Vehicle signal alone is NOT enough — requires at least one
    # secondary qualifier (service, brand, pickup-specific, or target CPV).
    fit = 0

    if brand_hits:
        fit += 40
        reasons.append("ISZE brand signal")

    if service_hits:
        fit += 25
        reasons.append("service / parts signal")

    if cpv_is_target(cpv):
        fit += 20
        reasons.append("target CPV match")
    elif vehicle_hits or cpv.startswith(CPV_VEHICLE_PREFIXES):
        # Vehicle signal but NOT a target CPV — only add points if there's
        # a second qualifying signal (service or brand already added above)
        if brand_hits or service_hits:
            fit += 15
            reasons.append("vehicle procurement")
        else:
            fit += 5  # not enough on its own to escape Ignore

    if pickup_hits:
        fit += 12
        reasons.append("pickup / light truck relevance")

    if framework_hits:
        fit += 8
        reasons.append("framework route")

    if cpv.startswith(CPV_SERVICE_PREFIXES):
        fit += 10

    fit = min(100, fit)

    # --- Win score ---
    win = 20
    days = row.get("days_to_deadline")
    if days is None:
        # No penalty for missing deadline — TED search results routinely omit it,
        # and penalising here systematically downgrades 90%+ of EU tenders.
        # Missing deadline is already captured in evidence_score and urgency=none.
        pass
    elif days < 0:
        win -= 30
        reasons.append("deadline passed")
    elif days <= 7:
        win += 5
        reasons.append("urgent decision needed")
    elif days <= 21:
        win += 15
        reasons.append("decision window open")
    else:
        win += 25
        reasons.append("good runway")

    if row.get("Buyer"):
        win += 10
    if row.get("Country"):
        win += 8
    if row.get("evidence_label") == "High":
        win += 20
    elif row.get("evidence_label") == "Medium":
        win += 10
    if framework_hits:
        win -= 3
    if row.get("Lifecycle") == "result":
        win -= 15
        reasons.append("award/result stage")
    if row.get("Lifecycle") == "planning":
        win += 10
        reasons.append("early-stage visibility")
    win = max(0, min(100, win))

    # --- Economic score ---
    econ = 10
    tier = row.get("tier")
    if tier == "large":
        econ += 40
        reasons.append("large value")
    elif tier == "medium":
        econ += 25
        reasons.append("medium value")
    elif tier == "small":
        econ += 12
    elif tier == "micro":
        econ += 6
    else:
        econ += 8

    if service_hits:
        econ += 24
    if framework_hits:
        econ += 20
        reasons.append("recurring framework potential")
    if cpv.startswith(CPV_SERVICE_PREFIXES):
        econ += 10

    fleet_size = int(row.get("fleet_size") or 0)
    if fleet_size >= 20:
        econ += 15
        reasons.append("material fleet size")
    elif fleet_size >= 5:
        econ += 10
    elif fleet_size >= 1:
        econ += 4

    if brand_hits:
        econ += 10

    econ = min(100, econ)

    return fit, win, econ, reasons[:6]


def derive_decision(fit: int, win: int, econ: int, lifecycle: str) -> str:
    if lifecycle == "result":
        if econ >= 50:
            return "Watch"
        return "Ignore"
    if fit >= 60 and win >= 55 and econ >= 45:
        return "Attack"
    if fit >= 52 and (win >= 45 or econ >= 50):
        return "Selective"
    if fit >= 38 or econ >= 32:
        return "Watch"
    return "Ignore"


def suggest_owner(country: str) -> str:
    return COUNTRY_CLUSTER_MAP.get(country, "Unassigned")


def suggest_status(decision: str, urgency: str, lifecycle: str, evidence_label: str) -> str:
    if lifecycle == "result":
        return "Review"
    if decision == "Attack" and urgency in ("critical", "soon"):
        return "Bid / No-Bid"
    if decision == "Attack":
        return "Needs owner"
    if decision == "Selective" and evidence_label == "Low":
        return "Enrich"
    if decision == "Selective":
        return "Review"
    return "Watch"


def suggest_next_action(row: Dict[str, Any]) -> str:
    decision = row.get("decision", "Watch")
    urgency = row.get("urgency", "none")
    lifecycle = row.get("Lifecycle", "competition")
    if lifecycle == "result":
        return "Mine award outcome and incumbent insight"
    if not row.get("Buyer"):
        return "Enrich buyer and route to owner"
    if not row.get("deadline_date"):
        return "Validate deadline and notice details"
    if decision == "Attack" and urgency == "critical":
        return "Open bid desk now and confirm go / no-go"
    if decision == "Attack" and row.get("value_amount") is None:
        return "Estimate value and lot scope before qualification"
    if decision == "Attack":
        return "Assign owner and run qualification call"
    if decision == "Selective" and row.get("evidence_label") == "Low":
        return "Enrich data before country review"
    if decision == "Selective":
        return "Review with regional lead"
    return "Monitor only"


def extract_notice_id(url: str) -> str:
    url = extract_text(url)
    if not url:
        return ""
    match = re.search(r"/Notice/([^/]+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/detail/([^/?#]+)", url)
    if match:
        return match.group(1)
    return url.rstrip("/").split("/")[-1]


def build_family_id(title: str, buyer: str, country: str) -> str:
    key = "|".join(
        [
            normalize_title_for_family(title),
            normalize_text(buyer),
            normalize_text(country),
        ]
    )
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def normalize_raw_row(raw: Dict[str, Any], source_hint: str = "") -> Dict[str, Any]:
    source = extract_text(raw.get("Source") or raw.get("_source") or source_hint)
    title = extract_text(raw.get("Title"))
    buyer = extract_text(raw.get("Buyer"))
    cpv = extract_text(raw.get("CPV Code"))
    cpv_desc = extract_text(raw.get("CPV Desc"))
    description = extract_text(raw.get("Description"))
    published = raw.get("Published", "")
    deadline = raw.get("Deadline", "")
    value_amount = parse_number(raw.get("Est. Value"))
    country = normalize_country(raw.get("Country") or SOURCE_COUNTRY_FALLBACK.get(source, ""))
    ccode = extract_text(raw.get("Country Code")) or country_code(country)
    notice_type = extract_text(raw.get("Notice Type"))
    lifecycle = extract_text(raw.get("Lifecycle")) or classify_lifecycle(
        " ".join([title, cpv_desc, description]),
        notice_type,
    )
    source_notice_id = extract_text(raw.get("Source Notice ID")) or extract_notice_id(raw.get("URL", ""))
    raw_fleet = parse_number(raw.get("FleetSize"))
    extracted_fleet = extract_fleet_size(title, description)
    fleet_size = int(raw_fleet or extracted_fleet or 0)
    # Confidence: "extracted" only when source or extractor provided a size — never guessed.
    fleet_size_confidence = "extracted" if fleet_size else None
    days = days_until(deadline)
    tier = value_tier(value_amount)
    urgency = urgency_from_days(days)

    row: Dict[str, Any] = {
        "Source": source,
        "Source Notice ID": source_notice_id,
        "Lifecycle": lifecycle,
        "Notice Type": notice_type,
        "Procedure Type": extract_text(raw.get("Procedure Type")),
        "Buyer Type": extract_text(raw.get("Buyer Type")),
        "Score": int(parse_number(raw.get("Score")) or score_legacy(title, value_amount)),
        "relevance_score_1to5": relevance_score_1to5(title, country_code=ccode, value_amount=value_amount),
        "FleetSize": fleet_size,
        "Title": title,
        "Title Compact": compact_title(title),
        "Buyer": buyer,
        "CPV Code": cpv,
        "CPV Desc": cpv_desc,
        "Description": description,
        "Est. Value": "" if value_amount is None else value_amount,
        "Currency": extract_text(raw.get("Currency")),
        "Published": iso_datetime(published) or extract_text(published),
        "Published Date": iso_date(published),
        "Deadline": iso_datetime(deadline) or extract_text(deadline),
        "Deadline Date": iso_date(deadline),
        "Country": country,
        "Country Code": ccode,
        "URL": extract_text(raw.get("URL")),
        "Source Raw": raw,
        "days_to_deadline": days,
        "urgency": urgency,
        "value_amount": value_amount,
        "tier": tier,
        "fleet_size": fleet_size,
        "fleet_size_confidence": fleet_size_confidence,
        "cpv_excluded": cpv_is_excluded(cpv),  # v3: flag for transparency
    }
    row["relevance_pass"] = relevance_pass(row["relevance_score_1to5"])
    row["opportunity_id"] = build_family_id(row["Title Compact"], buyer, country)
    _text_blob = " ".join([title, cpv_desc, description]).lower()
    row["brand_hits"] = keyword_hits(_text_blob, BRAND_TERMS)
    row["service_hits"] = keyword_hits(_text_blob, SERVICE_TERMS)
    row["framework_hits"] = keyword_hits(_text_blob, FRAMEWORK_TERMS)
    row["vehicle_hits"] = keyword_hits(_text_blob, VEHICLE_TERMS)
    row["rm_hits"] = keyword_hits(_text_blob, RM_CONTRACT_TERMS)
    # parts_signal: True when any maintenance/repair/spare-parts language is present,
    # or when the CPV is in the service (501xx) range.
    row["parts_signal"] = bool(
        row["service_hits"] or cpv.startswith(CPV_SERVICE_PREFIXES)
    )
    # rm_contract: Stricter flag — True only when a fleet operator is outsourcing
    # the repair AND maintenance of vehicles to a contractor.
    # These are ISZE's highest-priority leads: the winning contractor will need a
    # guaranteed parts supply from the distributor. CPV 501xx is the clearest signal.
    row["rm_contract"] = bool(
        row["rm_hits"] or cpv.startswith(CPV_SERVICE_PREFIXES)
    )
    attach_aftersales(row)
    attach_product_segment(row)
    ev_score, ev_label, gaps = evidence_score(row)
    row["evidence_score"] = ev_score
    row["evidence_label"] = ev_label
    row["data_gaps"] = gaps
    fit, win, econ, reasons = compute_scores(row)
    row["fit_score"] = fit
    row["win_score"] = win
    row["econ_score"] = econ
    row["score_drivers"] = reasons
    row["decision"] = derive_decision(fit, win, econ, lifecycle)
    row["owner_suggested"] = suggest_owner(country)
    row["status_suggested"] = suggest_status(row["decision"], urgency, lifecycle, ev_label)
    row["next_action_suggested"] = suggest_next_action(row)
    return row


def source_label_from_sheet(sheet_name: str) -> str:
    return SOURCE_SHEET_MAP.get(sheet_name, "")


def aggregate_opportunities(notices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in notices:
        groups[row["opportunity_id"]].append(row)

    opportunities: List[Dict[str, Any]] = []
    for opp_id, items in groups.items():
        items = sorted(
            items,
            key=lambda r: (
                DECISION_ORDER.get(r["decision"], 9),
                -int(r["fit_score"]),
                -int(r["win_score"]),
                -int(r["econ_score"]),
                -int(r.get("evidence_score", 0)),
                -int(r.get("days_to_deadline") or -9999),
            ),
        )
        rep = items[0]
        sources = sorted({r["Source"] for r in items if r["Source"]})
        countries = sorted({r["Country"] for r in items if r["Country"]})
        notice_ids = [r["Source Notice ID"] for r in items if r["Source Notice ID"]]
        all_drivers = []
        seen_driver = set()
        for r in items:
            for driver in r.get("score_drivers", []):
                if driver not in seen_driver:
                    all_drivers.append(driver)
                    seen_driver.add(driver)
        deadlines = [r["Deadline Date"] for r in items if r["Deadline Date"]]
        published = [r["Published Date"] for r in items if r["Published Date"]]
        value_amounts = [r["value_amount"] for r in items if r["value_amount"] is not None]
        evidence_scores = [r["evidence_score"] for r in items]
        service_hits = []
        framework_hits = []
        brand_hits = []
        rm_hits = []
        gaps = []
        for r in items:
            for term, bag in (
                (r.get("service_hits", []), service_hits),
                (r.get("framework_hits", []), framework_hits),
                (r.get("brand_hits", []), brand_hits),
                (r.get("rm_hits", []), rm_hits),
                (r.get("data_gaps", []), gaps),
            ):
                for x in term:
                    if x not in bag:
                        bag.append(x)

        value_amount = max(value_amounts) if value_amounts else None
        tier = value_tier(value_amount)
        fit = max(int(r["fit_score"]) for r in items)
        win = max(int(r["win_score"]) for r in items)
        econ = max(int(r["econ_score"]) for r in items)
        lifecycle_counter = Counter(r["Lifecycle"] for r in items)
        lifecycle = lifecycle_counter.most_common(1)[0][0]
        ev_score = int(round(sum(evidence_scores) / len(evidence_scores))) if evidence_scores else 0
        ev_label = "High" if ev_score >= 75 else "Medium" if ev_score >= 50 else "Low"
        decision = derive_decision(fit, win, econ, lifecycle)
        urgency_values = [r["urgency"] for r in items]
        urgency = min(urgency_values, key=lambda x: URGENCY_ORDER.get(x, 9)) if urgency_values else "none"
        fleet_size = max(int(r.get("fleet_size") or 0) for r in items)
        fleet_size_confidence = "extracted" if fleet_size else None
        buyer = rep.get("Buyer") or next((r.get("Buyer") for r in items if r.get("Buyer")), "")
        country = rep.get("Country") or (countries[0] if countries else "")
        owner = suggest_owner(country)

        opportunity = {
            "opportunity_id": opp_id,
            "title": rep["Title Compact"] or rep["Title"],
            "title_raw": rep["Title"],
            "buyer": buyer,
            "country": country,
            "country_code": rep.get("Country Code", ""),
            "countries": countries,
            "sources": sources,
            "source_notice_ids": notice_ids,
            "source_count": len(sources),
            "notice_count": len(items),
            "duplicate_count": max(0, len(items) - 1),
            "published_first": min(published) if published else "",
            "published_latest": max(published) if published else "",
            "deadline_date": min(deadlines) if deadlines else "",
            "days_to_deadline": min((r["days_to_deadline"] for r in items if r["days_to_deadline"] is not None), default=None),
            "urgency": urgency,
            "value_amount": value_amount,
            "currency": rep.get("Currency", "") or next((r.get("Currency") for r in items if r.get("Currency")), ""),
            "tier": tier,
            "fleet_size": fleet_size,
            "fleet_size_confidence": fleet_size_confidence,
            "lifecycle": lifecycle,
            "notice_type": rep.get("Notice Type", ""),
            "buyer_type": rep.get("Buyer Type", ""),
            "procedure_type": rep.get("Procedure Type", ""),
            "fit_score": fit,
            "win_score": win,
            "econ_score": econ,
            "opportunity_score": int(round((fit * 0.4) + (win * 0.3) + (econ * 0.3))),
            "decision": decision,
            "evidence_score": ev_score,
            "evidence_label": ev_label,
            "score_drivers": all_drivers[:6],
            "service_hits": service_hits[:6],
            "framework_hits": framework_hits[:6],
            "brand_hits": brand_hits[:6],
            "rm_hits": rm_hits[:6],
            "data_gaps": gaps[:8],
            # parts_signal: True if ANY notice in the family has a service/parts signal.
            "parts_signal": any(r.get("parts_signal") for r in items),
            # rm_contract: True if ANY notice is specifically an R&M outsourcing contract
            # (fleet operator handing repair+maintenance to a third party).
            # Highest-value lead type — winning contractor needs guaranteed parts supply.
            "rm_contract": any(r.get("rm_contract") for r in items),
            "owner_suggested": owner,
            "status_suggested": suggest_status(decision, urgency, lifecycle, ev_label),
            "next_action_suggested": suggest_next_action(
                {
                    "decision": decision,
                    "urgency": urgency,
                    "Lifecycle": lifecycle,
                    "Buyer": buyer,
                    "deadline_date": min(deadlines) if deadlines else "",
                    "value_amount": value_amount,
                    "evidence_label": ev_label,
                }
            ),
            "url": rep.get("URL", ""),
            "cpv_code": rep.get("CPV Code", ""),
            "cpv_desc": rep.get("CPV Desc", ""),
            "notices": [
                {
                    "source": r.get("Source", ""),
                    "source_notice_id": r.get("Source Notice ID", ""),
                    "title": r.get("Title", ""),
                    "buyer": r.get("Buyer", ""),
                    "published_date": r.get("Published Date", ""),
                    "deadline_date": r.get("Deadline Date", ""),
                    "urgency": r.get("urgency", "none"),
                    "value_amount": r.get("value_amount"),
                    "currency": r.get("Currency", ""),
                    "lifecycle": r.get("Lifecycle", "competition"),
                    "notice_type": r.get("Notice Type", ""),
                    "url": r.get("URL", ""),
                }
                for r in sorted(items, key=lambda x: (x.get("Published Date", ""), x.get("Source Notice ID", "")), reverse=True)
            ],
        }
        attach_product_segment(opportunity)
        # Merge aftersales tags across family notices (any-match union)
        fam_tags: List[str] = []
        fam_evidence: Dict[str, List[str]] = {}
        for r in items:
            attach_aftersales(r)
            for t in r.get("aftersales_tags") or []:
                if t not in fam_tags:
                    fam_tags.append(t)
            for t, hits in (r.get("aftersales_evidence") or {}).items():
                bag = fam_evidence.setdefault(t, [])
                for h in hits or []:
                    if h not in bag:
                        bag.append(h)
        # Prefer family-level detect on combined text, then union with notice tags
        attach_aftersales(opportunity)
        for t in fam_tags:
            if t not in (opportunity.get("aftersales_tags") or []):
                opportunity.setdefault("aftersales_tags", []).append(t)
        opportunity["aftersales_tags"] = [
            t for t in AFTERSALES_TAG_ORDER if t in (opportunity.get("aftersales_tags") or [])
        ]
        if opportunity.get("aftersales_tags"):
            for t, hits in fam_evidence.items():
                bag = opportunity.setdefault("aftersales_evidence", {}).setdefault(t, [])
                for h in hits:
                    if h not in bag:
                        bag.append(h)
            labels = [AFTERSALES_TAG_LABELS.get(t, t) for t in opportunity["aftersales_tags"]]
            opportunity["aftersales_summary"] = " · ".join(labels)
            tip_bits = []
            for t in opportunity["aftersales_tags"]:
                matched = (opportunity.get("aftersales_evidence") or {}).get(t) or []
                if matched:
                    tip_bits.append(f"{AFTERSALES_TAG_LABELS.get(t, t)}: {', '.join(matched[:3])}")
                else:
                    tip_bits.append(AFTERSALES_TAG_LABELS.get(t, t))
            opportunity["aftersales_match_tip"] = "Matched in notice — " + "; ".join(tip_bits)
        else:
            opportunity["aftersales_summary"] = None
            opportunity["aftersales_evidence"] = {}
            opportunity["aftersales_match_tip"] = (
                "No service/parts/warranty language found in notice"
            )
        opportunities.append(opportunity)

    opportunities.sort(
        key=lambda o: (
            DECISION_ORDER.get(o["decision"], 9),
            URGENCY_ORDER.get(o["urgency"], 9),
            -int(o["opportunity_score"]),
            -int(o.get("evidence_score", 0)),
            o["title"].lower(),
        )
    )
    return opportunities


def meta_summary(notices: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
    action_queue = [
        o for o in opportunities
        if o["decision"] in ("Attack", "Selective") and (
            o["urgency"] in ("critical", "soon") or
            o["evidence_label"] == "Low" or
            o["status_suggested"] in ("Needs owner", "Bid / No-Bid", "Enrich")
        )
    ]
    stats = {
        "raw_notices": len(notices),
        "opportunities": len(opportunities),
        "attack": sum(1 for o in opportunities if o["decision"] == "Attack"),
        "selective": sum(1 for o in opportunities if o["decision"] == "Selective"),
        "action_queue": len(action_queue),
        "due_14d": sum(1 for o in opportunities if o["days_to_deadline"] is not None and o["days_to_deadline"] <= 14 and o["days_to_deadline"] >= 0),
        "missing_deadline": sum(1 for n in notices if not n.get("Deadline Date")),
        "missing_value": sum(1 for n in notices if n.get("value_amount") is None),
        "duplicate_families": sum(1 for o in opportunities if o["duplicate_count"] > 0),
        "low_evidence": sum(1 for o in opportunities if o["evidence_label"] == "Low"),
        "aftersales_tagged": sum(1 for o in opportunities if o.get("aftersales_tags")),
    }
    source_counts = Counter(n.get("Source", "Unknown") for n in notices)
    country_counts = Counter(o.get("country", "Unknown") for o in opportunities if o.get("country"))
    lifecycle_counts = Counter(o.get("lifecycle", "competition") for o in opportunities)
    decision_counts = Counter(o.get("decision", "Watch") for o in opportunities)
    owner_counts = Counter(o.get("owner_suggested", "Unassigned") for o in opportunities)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stats": stats,
        "source_counts": dict(source_counts),
        "country_counts": dict(country_counts),
        "lifecycle_counts": dict(lifecycle_counts),
        "decision_counts": dict(decision_counts),
        "owner_counts": dict(owner_counts),
        "owner_options": OWNER_OPTIONS,
        "status_options": STATUS_OPTIONS,
    }


def row_to_export(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    out.pop("Source Raw", None)
    return out
