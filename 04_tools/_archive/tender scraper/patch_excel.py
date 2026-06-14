"""
patch_excel.py — One-shot fix for isuzu_tenders.xlsx
- Extracts clean English titles from TED's multilingual dict strings
- Adds Score column based on title content
- Adds FleetSize column (vehicle quantity detected from title)
- Fixes Buyer, CPV, Country columns
Run once, then run build_dashboard.py
"""

import os, re, ast, openpyxl

XLSX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "isuzu_tenders.xlsx")

# ── SCORING ────────────────────────────────────────────────────────────────────

SCORE_BRAND = [
    "isuzu", "d-max", "d max", "dmax", "n-series", "n series", "f-series", "f series",
]
SCORE_SERVICE = [
    "maintenance", "service contract", "repair and maintenance", "servicing",
    "after-sales", "aftersales", "spare parts", "parts supply", "parts and labour",
    "fleet management", "preventive maintenance", "corrective maintenance",
    "full maintenance", "scheduled maintenance", "vehicle maintenance",
    "repair", "overhaul", "upkeep", "workshop",
    "wartung", "instandhaltung", "reparatur", "fahrzeugwartung", "werkstatt", "ersatzteile",
    "entretien", "réparation", "reparation", "révision", "atelier", "gestion de flotte",
    "mantenimiento", "reparación", "reparacion", "taller",
    "manutenzione", "riparazione", "officina", "ricambi", "assistenza",
    "konserwacja", "naprawa", "serwis", "utrzymanie", "warsztat",
    "onderhoud", "reparatie", "werkplaats", "onderdelen",
    "manutenção", "manutencao", "reparação", "reparacao",
    "mentenanță", "mentenanta", "reparații", "reparatii", "întreținere",
    "karbantartás", "karbantartas", "javítás", "javitas", "szerviz",
    "údržba", "udrzba", "oprava",
    "underhåll", "underhall", "reservdelar",
    "vedligeholdelse", "reservedele", "værksted",
    "תחזוקה", "תיקון", "חלקי חילוף",
]
SCORE_FRAMEWORK = [
    "framework agreement", "framework contract", "dynamic purchasing",
    "dps", "multi-year", "annual contract", "lot ", "lots ", "call-off", "blanket order",
    "rahmenvertrag", "rahmenvereinbarung",
    "accord-cadre", "accord cadre",
    "acuerdo marco",
    "accordo quadro",
    "umowa ramowa",
    "raamovereenkomst",
    "acordo quadro", "acordo-quadro",
    "acord-cadru", "acord cadru",
    "keretmegállapodás", "keretmegallapodas",
    "rámcová smlouva", "ramcova smlouva",
    "ramavtal", "rammeaftale",
]

def score_tender(title, value=None):
    t = (title or "").lower()
    brand   = any(k in t for k in SCORE_BRAND)
    service = any(k in t for k in SCORE_SERVICE)
    fw      = any(k in t for k in SCORE_FRAMEWORK)
    try:
        high_value = float(str(value).replace(",", "")) > 500_000 if value else False
    except Exception:
        high_value = False
    if brand and service: return 5
    if service and fw:    return 4
    if service:           return 3
    if fw or high_value:  return 2
    return 1

def extract_fleet_size(title):
    """
    Try to extract a fleet quantity from the tender title.
    Returns an integer if found, or 0 if not detectable.
    """
    t = (title or "").lower()
    patterns = [
        r'fleet\s+of\s+(\d+)',
        r'(\d+)\s+(?:vehicles?|trucks?|vans?|lorr(?:y|ies)|buses?|coaches?|pick[\s-]?ups?'
        r'|motor\s+vehicles?|commercial\s+vehicles?|light\s+commercial|minibuses?)',
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

def extract_text(raw):
    """Extract clean text from a value that might be a dict, list, or string-encoded dict."""
    if raw is None:
        return ""
    if isinstance(raw, str):
        raw = raw.strip()
        if raw.startswith("{") or raw.startswith("["):
            try:
                raw = ast.literal_eval(raw)
            except Exception:
                return raw
    if isinstance(raw, dict):
        val = (raw.get("eng") or raw.get("EN") or raw.get("ENG")
               or next(iter(raw.values()), ""))
        return extract_text(val)
    if isinstance(raw, list):
        return extract_text(raw[0]) if raw else ""
    return str(raw).strip("[]'\" ")

# ── MAIN ───────────────────────────────────────────────────────────────────────

wb = openpyxl.load_workbook(XLSX)
total_fixed = 0

for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        continue

    headers = list(rows[0])
    has_score     = "Score"     in headers
    has_fleetsize = "FleetSize" in headers

    # Build new headers: Score, FleetSize first, then the rest
    base = [h for h in headers if h not in ("Score", "FleetSize")]
    new_headers = ["Score", "FleetSize"] + base

    new_rows = [new_headers]
    fixed = 0

    for row in rows[1:]:
        if not any(row):
            continue

        d = {headers[i]: row[i] for i in range(len(headers))}

        # Extract clean title
        raw_title = d.get("Title", "")
        title = extract_text(raw_title)

        # Skip placeholder rows
        if title.startswith("No ") and "results" in title:
            new_rows.append([d.get(h, "") for h in new_headers])
            continue

        # Extract clean buyer
        buyer = extract_text(d.get("Buyer", ""))

        # Extract clean CPV
        cpv_raw = d.get("CPV Code", "")
        if isinstance(cpv_raw, str) and cpv_raw.startswith("["):
            try:
                cpv_list = ast.literal_eval(cpv_raw)
                cpv = str(cpv_list[0]).strip("'\" ") if cpv_list else ""
            except Exception:
                cpv = cpv_raw
        else:
            cpv = str(cpv_raw or "").strip("[]'\" ")

        # Extract clean country
        country_raw = d.get("Country", "")
        country = str(country_raw).strip("[]'\" ") if country_raw else ""

        # Score + FleetSize
        score     = score_tender(title, d.get("Est. Value"))
        fleetsize = extract_fleet_size(title)

        new_d = dict(d)
        new_d["Title"]     = title
        new_d["Buyer"]     = buyer
        new_d["CPV Code"]  = cpv
        new_d["Country"]   = country
        new_d["Score"]     = score
        new_d["FleetSize"] = fleetsize
        fixed += 1

        new_rows.append([new_d.get(h, "") for h in new_headers])

    # Rewrite sheet
    ws.delete_rows(1, ws.max_row)
    for r in new_rows:
        ws.append(r)

    print(f"  {sheet_name}: {fixed} rows patched")
    total_fixed += fixed

wb.save(XLSX)
print(f"\n✓ Saved {XLSX}")
print(f"  Total rows fixed: {total_fixed}")
print("\nNow run: python build_dashboard.py")
