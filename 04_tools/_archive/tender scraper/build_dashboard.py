"""
ISZE Tender Dashboard Builder
Reads isuzu_tenders.xlsx and generates a visual HTML dashboard.
Run this after tender_scraper.py.
"""

import os, json, openpyxl
from datetime import datetime, date

XLSX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "isuzu_tenders.xlsx")
HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "isze_dashboard.html")

SHEET_SOURCE_MAP = {
    "UK Tenders":      "🇬🇧 UK",
    "EU TED Tenders":  "🇪🇺 EU",
    "Norway Doffin":   "🇳🇴 Norway",
    "Finland HILMA":   "🇫🇮 Finland",
    "Israel Tenders":  "🇮🇱 Israel",
}

# ── Scoring keywords (mirrored from tender_scraper.py) ──────────────────────
SCORE_BRAND = [
    "isuzu", "d-max", "d max", "dmax", "n-series", "n series", "f-series", "f series",
]
SCORE_SERVICE = [
    "maintenance", "service contract", "repair and maintenance", "servicing",
    "after-sales", "aftersales", "spare parts", "parts supply", "parts and labour",
    "fleet management", "preventive maintenance", "corrective maintenance",
    "full maintenance", "scheduled maintenance", "vehicle maintenance",
    "repair", "overhaul", "upkeep", "workshop",
    "wartung", "instandhaltung", "reparatur", "fahrzeugwartung", "kfz-wartung",
    "inspektion", "werkstatt", "ersatzteile", "fahrzeugpflege", "kfz-reparatur",
    "entretien", "réparation", "reparation", "révision", "revision",
    "pièces détachées", "pieces detachees", "pièces de rechange", "atelier",
    "gestion de flotte",
    "mantenimiento", "reparación", "reparacion", "taller",
    "piezas de repuesto", "revisión", "mantenimiento de vehículos",
    "manutenzione", "riparazione", "officina", "ricambi", "assistenza",
    "gestione flotta",
    "konserwacja", "naprawa", "serwis", "części zamienne", "czesci zamienne",
    "utrzymanie", "warsztat",
    "onderhoud", "reparatie", "werkplaats", "onderdelen", "voertuigonderhoud",
    "vlootbeheer",
    "manutenção", "manutencao", "reparação", "reparacao", "oficina",
    "peças sobressalentes", "pecas sobressalentes",
    "mentenanță", "mentenanta", "reparații", "reparatii", "întreținere",
    "intretinere", "piese de schimb",
    "karbantartás", "karbantartas", "javítás", "javitas", "alkatrészek",
    "alkatreszek", "szerviz",
    "údržba", "udrzba", "oprava", "náhradní díly", "nahradni dily",
    "underhåll", "underhall", "reparation", "reservdelar", "fordonsunderhåll",
    "vedligeholdelse", "reservedele", "værksted", "vaerksted",
    "συντήρηση", "επισκευή", "ανταλλακτικά",
    "תחזוקה", "תיקון", "חלקי חילוף", "ניהול צי",
]
SCORE_FRAMEWORK = [
    "framework agreement", "framework contract", "dynamic purchasing",
    "dps", "multi-year", "annual contract", "lot ", "lots ",
    "call-off", "call off", "blanket order",
    "rahmenvertrag", "rahmenvereinbarung", "dynamisches beschaffungssystem",
    "accord-cadre", "accord cadre", "système d'acquisition dynamique",
    "systeme d'acquisition dynamique",
    "acuerdo marco", "sistema dinámico de adquisición",
    "sistema dinamico de adquisicion",
    "accordo quadro", "sistema dinamico di acquisizione",
    "umowa ramowa", "dynamiczny system zakupów", "dynamiczny system zakupow",
    "raamovereenkomst", "dynamisch aankoopsysteem",
    "acordo quadro", "acordo-quadro",
    "acord-cadru", "acord cadru",
    "keretmegállapodás", "keretmegallapodas",
    "rámcová smlouva", "ramcova smlouva",
    "ramavtal",
    "rammeaftale",
]

def detect_keywords(title):
    """Return lists of matched keywords per category for tooltip display."""
    t = title.lower()
    matched_brand   = [k for k in SCORE_BRAND    if k in t]
    matched_service = [k for k in SCORE_SERVICE  if k in t]
    matched_fw      = [k for k in SCORE_FRAMEWORK if k in t]
    return matched_brand, matched_service, matched_fw

def extract_fleet_size(title):
    """Try to extract a fleet quantity from the tender title. Returns int or 0."""
    import re
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

# ── Date / urgency helpers ───────────────────────────────────────────────────
def parse_date(val):
    if not val or val in ("", "None"):
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y%m%d",
                "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except Exception:
            pass
    return None

def days_until(d):
    if d is None:
        return None
    return (d - date.today()).days

def urgency(days):
    if days is None:
        return "none"
    if days < 0:
        return "expired"
    if days <= 7:
        return "critical"
    if days <= 21:
        return "soon"
    return "ok"

def value_tier(val_str):
    """Bucket contract value: micro / small / medium / large / unknown."""
    if not val_str or val_str in ("", "None"):
        return "unknown"
    try:
        v = float(str(val_str).replace(",", "").strip())
        if v < 50_000:    return "micro"
        if v < 250_000:   return "small"
        if v < 1_000_000: return "medium"
        return "large"
    except Exception:
        return "unknown"

# ── Data loader ──────────────────────────────────────────────────────────────
def load_tenders():
    wb = openpyxl.load_workbook(XLSX)
    all_rows = []
    for sheet_name, source_label in SHEET_SOURCE_MAP.items():
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            continue
        headers = [str(h).strip() if h else "" for h in rows[0]]
        for row in rows[1:]:
            if not any(row):
                continue
            d = {headers[i]: (str(row[i]) if row[i] is not None else "") for i in range(len(headers))}
            if d.get("Title", "").startswith("No ") and "results" in d.get("Title", ""):
                continue
            d["_source"] = source_label
            deadline = parse_date(d.get("Deadline", ""))
            d["_deadline_date"] = deadline.isoformat() if deadline else ""
            d["_days"] = days_until(deadline)
            d["_urgency"] = urgency(d["_days"])
            # Value tier
            d["_tier"] = value_tier(d.get("Est. Value", ""))
            # Keyword breakdown + fleet size for tooltip (computed at build time)
            title = d.get("Title", "")
            mb, ms, mf = detect_keywords(title)
            d["_kw_brand"]   = mb[:3]
            d["_kw_service"] = ms[:4]
            d["_kw_fw"]      = mf[:3]
            # FleetSize: use stored value if available, otherwise detect from title
            raw_fs = d.get("FleetSize", "")
            try:
                d["_fleet"] = int(raw_fs) if str(raw_fs).isdigit() else extract_fleet_size(title)
            except Exception:
                d["_fleet"] = extract_fleet_size(title)
            all_rows.append(d)
    return all_rows

# ── HTML builder ─────────────────────────────────────────────────────────────
def build_html(rows):
    today = date.today().strftime("%d %b %Y")
    total = len(rows)
    by_source = {}
    by_country = {}
    for r in rows:
        s = r["_source"]
        by_source[s] = by_source.get(s, 0) + 1
        c = r.get("Country", "Unknown") or "Unknown"
        c = c.strip("[]'\" ") or "Unknown"
        by_country[c] = by_country.get(c, 0) + 1

    top_countries = sorted(by_country.items(), key=lambda x: -x[1])[:10]
    rows_json = json.dumps(rows, ensure_ascii=False)

    source_cards = ""
    icons = {"🇬🇧 UK": "#1a73e8", "🇪🇺 EU": "#003399", "🇳🇴 Norway": "#ef2b2d",
             "🇫🇮 Finland": "#003580", "🇮🇱 Israel": "#0038b8"}
    for src, count in sorted(by_source.items(), key=lambda x: -x[1]):
        color = icons.get(src, "#555")
        source_cards += f"""
        <div class="stat-card" style="border-top:4px solid {color}">
            <div class="stat-num">{count}</div>
            <div class="stat-label">{src}</div>
        </div>"""

    country_bars = ""
    max_count = top_countries[0][1] if top_countries else 1
    for country, count in top_countries:
        pct = int(count / max_count * 100)
        country_bars += f"""
        <div class="bar-row">
            <span class="bar-label">{country}</span>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
            <span class="bar-count">{count}</span>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ISZE Tender Monitor</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f0f2f5; color: #1a1a2e; }}
  header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
            color: white; padding: 28px 36px; display:flex; align-items:center; gap:24px; }}
  header h1 {{ font-size: 1.6rem; font-weight: 700; letter-spacing: 0.5px; flex:1; }}
  header p {{ opacity: 0.65; font-size: 0.85rem; margin-top: 4px; }}
  .export-btn {{ background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.3);
                color: white; padding: 9px 18px; border-radius: 8px; cursor: pointer;
                font-size: 0.82rem; font-weight: 600; white-space: nowrap;
                transition: background 0.2s; }}
  .export-btn:hover {{ background: rgba(255,255,255,0.22); }}
  .main {{ padding: 28px 36px; max-width: 1600px; margin: 0 auto; }}

  /* Stat cards */
  .stats-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
  .stat-card {{ background: white; border-radius: 12px; padding: 20px 24px;
               flex: 1; min-width: 140px; box-shadow: 0 2px 8px rgba(0,0,0,.07); }}
  .stat-card.total {{ border-top: 4px solid #0f3460; }}
  .stat-num {{ font-size: 2rem; font-weight: 700; color: #1a1a2e; }}
  .stat-label {{ font-size: 0.78rem; color: #888; margin-top: 4px; text-transform: uppercase;
                letter-spacing: 0.5px; }}

  /* Two-col layout */
  .layout {{ display: grid; grid-template-columns: 260px 1fr; gap: 20px; align-items: start; }}
  .sidebar {{ display:flex; flex-direction:column; gap:16px; }}
  .sidebar-card {{ background: white; border-radius: 12px; padding: 20px;
                  box-shadow: 0 2px 8px rgba(0,0,0,.07); }}
  .sidebar-card h3 {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;
                     color: #888; margin-bottom: 14px; }}
  .bar-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
  .bar-label {{ font-size: 0.78rem; width: 80px; white-space: nowrap; overflow: hidden;
               text-overflow: ellipsis; color: #333; }}
  .bar-track {{ flex: 1; background: #f0f2f5; border-radius: 4px; height: 8px; }}
  .bar-fill {{ background: linear-gradient(90deg, #0f3460, #1a73e8); border-radius: 4px; height: 8px; }}
  .bar-count {{ font-size: 0.75rem; color: #888; width: 28px; text-align: right; }}

  /* Tier legend */
  .tier-row {{ display:flex; align-items:center; gap:8px; margin-bottom:8px; font-size:0.8rem; }}
  .tier-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}

  /* Table panel */
  .table-panel {{ background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.07);
                  overflow: hidden; }}
  .table-controls {{ display: flex; gap: 12px; padding: 16px 20px; border-bottom: 1px solid #f0f2f5;
                     flex-wrap: wrap; align-items: center; }}
  .search-box {{ flex: 1; min-width: 200px; padding: 8px 14px; border: 1px solid #e0e0e0;
                border-radius: 8px; font-size: 0.85rem; outline: none; }}
  .search-box:focus {{ border-color: #1a73e8; }}
  select.filter {{ padding: 8px 12px; border: 1px solid #e0e0e0; border-radius: 8px;
                  font-size: 0.85rem; background: white; outline: none; cursor: pointer; }}
  .result-count {{ margin-left: auto; font-size: 0.8rem; color: #888; }}

  /* Table */
  .table-wrap {{ overflow-x: auto; max-height: 620px; overflow-y: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  th {{ background: #f8f9fa; padding: 11px 14px; text-align: left; font-size: 0.73rem;
       text-transform: uppercase; letter-spacing: 0.4px; color: #666; border-bottom: 2px solid #eee;
       position: sticky; top: 0; z-index: 1; white-space: nowrap; cursor: pointer; user-select: none; }}
  th:hover {{ background: #edf2fb; }}
  td {{ padding: 10px 14px; border-bottom: 1px solid #f4f4f4; vertical-align: top; }}
  tr:hover td {{ background: #fafbff; }}
  .title-cell {{ max-width: 320px; line-height: 1.4; }}
  .title-link {{ color: #1a73e8; text-decoration: none; font-weight: 500; }}
  .title-link:hover {{ text-decoration: underline; }}
  .buyer-cell {{ max-width: 160px; color: #555; font-size: 0.78rem; }}
  .cpv-badge {{ display: inline-block; background: #edf2fb; color: #1a73e8; border-radius: 4px;
               padding: 2px 7px; font-size: 0.72rem; font-weight: 600; }}
  .country-text {{ font-size: 0.78rem; color: #555; }}
  .value-text {{ font-size: 0.78rem; color: #333; white-space: nowrap; }}

  /* Value tier badges */
  .tier-badge {{ display:inline-block; padding:2px 7px; border-radius:4px; font-size:0.7rem;
                font-weight:600; white-space:nowrap; }}
  .tier-large  {{ background:#e8f5e9; color:#2e7d32; }}
  .tier-medium {{ background:#fff8e1; color:#f57f17; }}
  .tier-small  {{ background:#e3f2fd; color:#1565c0; }}
  .tier-micro  {{ background:#fce4ec; color:#c62828; }}
  .tier-unknown{{ background:#f5f5f5; color:#9e9e9e; }}

  /* Urgency badges */
  .badge {{ display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 0.72rem;
            font-weight: 600; white-space: nowrap; }}
  .badge-critical {{ background: #fde8e8; color: #c0392b; }}
  .badge-soon {{ background: #fef9e7; color: #d35400; }}
  .badge-ok {{ background: #e8f8f0; color: #27ae60; }}
  .badge-expired {{ background: #f0f0f0; color: #999; }}
  .badge-none {{ background: #f5f5f5; color: #aaa; }}
  .source-pill {{ display: inline-block; padding: 2px 8px; border-radius: 10px;
                 font-size: 0.7rem; background: #f0f2f5; color: #555; }}
  .no-results {{ text-align: center; padding: 48px; color: #aaa; font-size: 0.9rem; }}

  /* Score stars */
  .score-5 {{ color: #e67e22; }}
  .score-4 {{ color: #f39c12; }}
  .score-3 {{ color: #27ae60; }}
  .score-2 {{ color: #2980b9; }}
  .score-1 {{ color: #bdc3c7; }}
  .score-cell {{ text-align: center; white-space: nowrap; position:relative; cursor:help; }}
  .score-label {{ display: block; font-size: 0.62rem; color: #aaa; }}
  .fleet-badge {{ display:inline-block; background:#fff3e0; color:#e65100; border-radius:4px;
                 padding:1px 6px; font-size:0.68rem; font-weight:700; margin-left:5px;
                 vertical-align:middle; }}

  /* Tooltip */
  .tooltip {{ display:none; position:absolute; left:50%; transform:translateX(-50%);
              bottom:calc(100% + 6px); background:#1a1a2e; color:white; border-radius:8px;
              padding:10px 13px; font-size:0.75rem; white-space:nowrap; z-index:100;
              box-shadow:0 4px 16px rgba(0,0,0,.25); min-width:180px; text-align:left; }}
  .tooltip::after {{ content:''; position:absolute; top:100%; left:50%; transform:translateX(-50%);
                    border:5px solid transparent; border-top-color:#1a1a2e; }}
  .score-cell:hover .tooltip {{ display:block; }}
  .tt-row {{ margin-bottom:4px; }}
  .tt-cat {{ opacity:0.6; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.4px; }}
  .tt-kw  {{ font-weight:600; color:#7ec8f4; }}
</style>
</head>
<body>

<header>
  <div>
    <h1>🚛 ISZE Tender Monitor</h1>
    <p>Last run: {today} &nbsp;·&nbsp; {total} tenders matched across all markets</p>
  </div>
  <button class="export-btn" onclick="exportCSV()">⬇ Export filtered CSV</button>
</header>

<div class="main">
  <div class="stats-row">
    <div class="stat-card total">
      <div class="stat-num">{total}</div>
      <div class="stat-label">Total Tenders</div>
    </div>
    {source_cards}
  </div>

  <div class="layout">
    <div class="sidebar">
      <div class="sidebar-card">
        <h3>Top Countries</h3>
        {country_bars}
      </div>
      <div class="sidebar-card">
        <h3>Contract Size</h3>
        <div class="tier-row"><span class="tier-dot" style="background:#2e7d32"></span><span>Large &gt; €1M</span></div>
        <div class="tier-row"><span class="tier-dot" style="background:#f57f17"></span><span>Medium €250k–1M</span></div>
        <div class="tier-row"><span class="tier-dot" style="background:#1565c0"></span><span>Small €50k–250k</span></div>
        <div class="tier-row"><span class="tier-dot" style="background:#c62828"></span><span>Micro &lt; €50k</span></div>
        <div class="tier-row"><span class="tier-dot" style="background:#9e9e9e"></span><span>Unknown</span></div>
        <p style="font-size:0.72rem;color:#aaa;margin-top:10px">Based on Est. Value field</p>
      </div>
    </div>

    <div class="table-panel">
      <div class="table-controls">
        <input class="search-box" type="text" id="searchBox" placeholder="🔍  Search title, buyer, country..." oninput="applyFilters()">
        <select class="filter" id="sourceFilter" onchange="applyFilters()">
          <option value="">All sources</option>
          <option>🇬🇧 UK</option>
          <option>🇪🇺 EU</option>
          <option>🇳🇴 Norway</option>
          <option>🇫🇮 Finland</option>
          <option>🇮🇱 Israel</option>
        </select>
        <select class="filter" id="scoreFilter" onchange="applyFilters()">
          <option value="">All scores</option>
          <option value="5">★★★★★ Brand+Service</option>
          <option value="4">★★★★☆ Service+Framework</option>
          <option value="3">★★★☆☆ Service</option>
          <option value="2">★★☆☆☆ Fleet/Framework</option>
          <option value="1">★☆☆☆☆ Purchase only</option>
        </select>
        <select class="filter" id="urgencyFilter" onchange="applyFilters()">
          <option value="">All deadlines</option>
          <option value="critical">🔴 Due ≤7 days</option>
          <option value="soon">🟡 Due ≤21 days</option>
          <option value="ok">🟢 Due later</option>
          <option value="expired">⚫ Expired</option>
          <option value="none">No deadline</option>
        </select>
        <select class="filter" id="tierFilter" onchange="applyFilters()">
          <option value="">All sizes</option>
          <option value="large">Large &gt;€1M</option>
          <option value="medium">Medium €250k–1M</option>
          <option value="small">Small €50k–250k</option>
          <option value="micro">Micro &lt;€50k</option>
          <option value="unknown">Size unknown</option>
        </select>
        <span class="result-count" id="resultCount"></span>
      </div>
      <div class="table-wrap">
        <table id="tenderTable">
          <thead>
            <tr>
              <th onclick="sortTable(0)">Score ↕</th>
              <th onclick="sortTable(1)">Title ↕</th>
              <th onclick="sortTable(2)">Buyer ↕</th>
              <th onclick="sortTable(3)">CPV ↕</th>
              <th onclick="sortTable(4)">Country ↕</th>
              <th onclick="sortTable(5)">Size ↕</th>
              <th onclick="sortTable(6)">Value ↕</th>
              <th onclick="sortTable(7)">Deadline ↕</th>
              <th onclick="sortTable(8)">Source ↕</th>
            </tr>
          </thead>
          <tbody id="tableBody"></tbody>
        </table>
        <div class="no-results" id="noResults" style="display:none">No tenders match your filters.</div>
      </div>
    </div>
  </div>
</div>

<script>
const ALL_ROWS = {rows_json};

const SCORE_STARS = {{ 5:"★★★★★", 4:"★★★★☆", 3:"★★★☆☆", 2:"★★☆☆☆", 1:"★☆☆☆☆" }};
const SCORE_LABEL = {{ 5:"Brand+Service", 4:"Service+Framework", 3:"Service", 2:"Fleet/Framework", 1:"Purchase only" }};
const TIER_ORDER  = {{large:0, medium:1, small:2, micro:3, unknown:4}};

function buildTooltip(r) {{
  const sc = parseInt(r.Score) || 1;
  let parts = [`<div class="tt-cat">Score ${{sc}}: ${{SCORE_LABEL[sc]}}</div>`];
  if (r._kw_brand && r._kw_brand.length)     parts.push(`<div class="tt-row"><span class="tt-cat">Brand · </span><span class="tt-kw">${{r._kw_brand.join(', ')}}</span></div>`);
  if (r._kw_service && r._kw_service.length) parts.push(`<div class="tt-row"><span class="tt-cat">Service · </span><span class="tt-kw">${{r._kw_service.join(', ')}}</span></div>`);
  if (r._kw_fw && r._kw_fw.length)           parts.push(`<div class="tt-row"><span class="tt-cat">Framework · </span><span class="tt-kw">${{r._kw_fw.join(', ')}}</span></div>`);
  if (r._fleet && r._fleet > 0)              parts.push(`<div class="tt-row"><span class="tt-cat">Fleet · </span><span class="tt-kw">~${{r._fleet}} vehicles detected</span></div>`);
  if (parts.length === 1) parts.push('<div style="opacity:0.6;font-size:0.72rem">No specific keywords matched</div>');
  return `<div class="tooltip">${{parts.join('')}}</div>`;
}}

function formatDeadline(row) {{
  const u = row._urgency;
  const d = row._days;
  const dateStr = row._deadline_date || row.Deadline || "";
  if (!dateStr || dateStr === "None" || dateStr === "") return '<span class="badge badge-none">—</span>';
  let label = dateStr.substring(0, 10);
  if (d !== null && d !== undefined) {{
    if (d < 0) label += " (expired)";
    else if (d === 0) label += " (today)";
    else label += ` (${{d}}d)`;
  }}
  return `<span class="badge badge-${{u}}">${{label}}</span>`;
}}

function formatValue(row) {{
  const v = row["Est. Value"];
  const c = row["Currency"];
  if (!v || v === "None" || v === "") return '<span style="color:#ccc">—</span>';
  const num = parseFloat(v);
  if (isNaN(num)) return v;
  return `<span class="value-text">${{c}} ${{num.toLocaleString()}}</span>`;
}}

function formatTier(tier) {{
  const labels = {{large:"Large", medium:"Medium", small:"Small", micro:"Micro", unknown:"—"}};
  const cls = `tier-badge tier-${{tier}}`;
  return `<span class="${{cls}}">${{labels[tier] || "—"}}</span>`;
}}

function renderTable(rows) {{
  const tbody = document.getElementById("tableBody");
  document.getElementById("resultCount").textContent = rows.length + " results";
  if (rows.length === 0) {{
    tbody.innerHTML = "";
    document.getElementById("noResults").style.display = "block";
    return;
  }}
  document.getElementById("noResults").style.display = "none";
  tbody.innerHTML = rows.map(r => {{
    const url = r.URL && r.URL !== "None" ? r.URL : "";
    const titleText = r.Title || "—";
    const fleetBadge = (r._fleet && r._fleet >= 5)
      ? ` <span class="fleet-badge">🚛 ${{r._fleet}}</span>` : "";
    const title = (url
      ? `<a class="title-link" href="${{url}}" target="_blank">${{titleText}}</a>`
      : titleText) + fleetBadge;
    const cpv = r["CPV Code"] && r["CPV Code"] !== "None"
      ? `<span class="cpv-badge">${{r["CPV Code"]}}</span>`
      : '<span style="color:#ccc">—</span>';
    const country = r.Country && r.Country !== "None" ? r.Country : "—";
    const buyer = r.Buyer && r.Buyer !== "None" ? r.Buyer : "—";
    const sc = parseInt(r.Score) || 1;
    const scoreHtml = `<div class="score-cell"><span class="score-${{sc}}">${{SCORE_STARS[sc]}}</span><span class="score-label">${{SCORE_LABEL[sc]}}</span>${{buildTooltip(r)}}</div>`;
    return `<tr data-source="${{r._source}}" data-urgency="${{r._urgency}}" data-tier="${{r._tier || 'unknown'}}">
      <td>${{scoreHtml}}</td>
      <td class="title-cell">${{title}}</td>
      <td class="buyer-cell">${{buyer}}</td>
      <td>${{cpv}}</td>
      <td class="country-text">${{country}}</td>
      <td>${{formatTier(r._tier || 'unknown')}}</td>
      <td>${{formatValue(r)}}</td>
      <td>${{formatDeadline(r)}}</td>
      <td><span class="source-pill">${{r._source}}</span></td>
    </tr>`;
  }}).join("");
}}

let sortCol = -1, sortAsc = true;
function sortTable(col) {{
  if (sortCol === col) sortAsc = !sortAsc;
  else {{ sortCol = col; sortAsc = true; }}
  applyFilters();
}}

let currentFiltered = [];

function applyFilters() {{
  const q   = document.getElementById("searchBox").value.toLowerCase();
  const src = document.getElementById("sourceFilter").value;
  const urg = document.getElementById("urgencyFilter").value;
  const sc  = document.getElementById("scoreFilter").value;
  const tier= document.getElementById("tierFilter").value;
  let rows = ALL_ROWS.filter(r => {{
    const text = (r.Title + " " + r.Buyer + " " + r.Country).toLowerCase();
    if (q   && !text.includes(q))       return false;
    if (src && r._source !== src)        return false;
    if (urg && r._urgency !== urg)       return false;
    if (sc  && String(r.Score) !== sc)   return false;
    if (tier&& (r._tier || "unknown") !== tier) return false;
    return true;
  }});
  if (sortCol >= 0) {{
    const keys = ["Score", "Title", "Buyer", "CPV Code", "Country", "_tier", "Est. Value", "_deadline_date", "_source"];
    const key = keys[sortCol];
    rows.sort((a, b) => {{
      let av = (a[key] || "").toString();
      let bv = (b[key] || "").toString();
      // Numeric sort for Score and Value
      if (key === "Score" || key === "Est. Value") {{
        const na = parseFloat(av) || 0, nb = parseFloat(bv) || 0;
        return sortAsc ? na - nb : nb - na;
      }}
      // Tier sort by order
      if (key === "_tier") {{
        const ta = TIER_ORDER[av] ?? 4, tb = TIER_ORDER[bv] ?? 4;
        return sortAsc ? ta - tb : tb - ta;
      }}
      return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    }});
  }}
  currentFiltered = rows;
  renderTable(rows);
}}

// CSV export of current filtered view
function exportCSV() {{
  if (!currentFiltered.length) {{ alert("No rows to export."); return; }}
  const cols = ["Score", "Title", "Buyer", "CPV Code", "Country", "Est. Value", "Currency", "Deadline", "_source", "URL"];
  const headers = ["Score","Title","Buyer","CPV Code","Country","Est. Value","Currency","Deadline","Source","URL"];
  const esc = v => '"' + String(v || "").replace(/"/g, '""') + '"';
  const lines = [headers.map(esc).join(",")];
  currentFiltered.forEach(r => lines.push(cols.map(c => esc(r[c] || "")).join(",")));
  const blob = new Blob([lines.join("\\n")], {{type:"text/csv;charset=utf-8;"}});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "isze_tenders_" + new Date().toISOString().slice(0,10) + ".csv";
  a.click();
}}

// Initial render — sort by Score desc, then fleet size desc, then deadline urgency
ALL_ROWS.sort((a, b) => {{
  const sd = (parseInt(b.Score) || 1) - (parseInt(a.Score) || 1);
  if (sd !== 0) return sd;
  const fd = (parseInt(b._fleet) || 0) - (parseInt(a._fleet) || 0);
  if (fd !== 0) return fd;
  const order = {{critical:0, soon:1, ok:2, none:3, expired:4}};
  return (order[a._urgency] ?? 5) - (order[b._urgency] ?? 5);
}});
applyFilters();
</script>
</body>
</html>"""
    return html

def main():
    print("Reading", XLSX)
    rows = load_tenders()
    print(f"Loaded {len(rows)} tenders")
    html = build_html(rows)
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ Dashboard saved: {HTML}")

if __name__ == "__main__":
    main()
