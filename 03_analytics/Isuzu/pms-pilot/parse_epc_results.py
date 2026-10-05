"""
Parse EPC scrape results into enriched FIG-KEY workbook columns.

Input: epc_results.json — list of per-PN scrape dicts from window.__allResults
Output: enrichment dict keyed by PN with derived columns.

The series -> weight answer is NOT held in this file. It comes from the one authored map,
`03_analytics/Isuzu/prism/data/series_to_band.csv`, read through
`03_analytics/Isuzu/prism/modules/vehicle_bands.py`.

Until 2026-09-24 this file carried its own `SERIES_TO_GVW` dictionary, typed by hand with no
source. It disagreed with the map, and those answers are now gone:

  * `NKR` was read as 5.5 t. Every sourced table says 3.5 t (the N35 Grafter rung).
  * `NHR`, `NN` and `NP` were given a weight. The sources do not settle any of them, so the
    map marks them unresolved and this file now records no weight for them.
  * `NNR` was read as 5.5 t. The map puts it on the 7.5 t band, its own nominal GVW being 6.5 t.
  * the heavy and bus codes were given an invented class (`HCV 26t+`, `Bus`, `SUV`) instead of
    the map's own answer: outside the four bands ISZE ships.

A series the map leaves unresolved stays without a weight. Nothing here falls back to a default,
because a default is exactly what made the old table wrong.
"""
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load_vehicle_bands():
    """The one reader of the authored map, loaded by file path.

    Loaded by path, and registered in `sys.modules` before the spec is executed, so the module
    resolves however this script is invoked - imported, run from another folder, or run by a
    launcher. Same pattern as `01_data/07_UIO/vin/build_vin_register.py`.
    """
    prism = _HERE.parents[2] / "03_analytics" / "Isuzu" / "prism"
    spec = importlib.util.spec_from_file_location(
        "vehicle_bands", prism / "modules" / "vehicle_bands.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vehicle_bands"] = mod
    spec.loader.exec_module(mod)
    return mod


vehicle_bands = _load_vehicle_bands()


def _series_vocabulary() -> frozenset:
    """Every code the map names as a vehicle: the series an EPC row may legitimately carry.

    The codes the map files under the `unresolved` *group* are the wildcard and stray tokens it
    recorded so they could not be mistaken for a model code (`CV`, `TF`, `X2`, `R` ...). Those
    are not a series vocabulary and are left out. A code whose *band* is unresolved (`NHR`,
    `NN`, `NP`) is a real series and stays in: it is listed on the row and carries no weight.
    """
    return frozenset(
        code for code, row in vehicle_bands.load_map().items()
        if (row.get("vehicle_group") or "").strip() != vehicle_bands.GROUP_UNRESOLVED
    )


def _series_to_gvw() -> dict:
    """{code: weight class label} for every code the map puts on a band.

    A code the map leaves unresolved - or does not carry at all - is absent on purpose. The
    caller records no weight for it rather than falling back to a default.
    """
    out = {}
    rows = vehicle_bands.load_map()
    for code in sorted(_series_vocabulary()):
        band = vehicle_bands.band_for(code)
        if band in vehicle_bands.BAND_LABEL:
            out[code] = vehicle_bands.BAND_LABEL[band]
        elif band == vehicle_bands.NOT_IN_SCOPE:
            label = (rows[code].get("weight_label") or "").strip()
            if label:
                out[code] = label
    return out


# Derived from `series_to_band.csv`, not typed here. Edit the CSV to change a mapping.
SERIES_VOCABULARY = _series_vocabulary()
SERIES_TO_GVW = _series_to_gvw()


def resolved_series_table() -> dict:
    """The series -> weight answer this module exposes. Read-only, for verification."""
    return dict(SERIES_TO_GVW)

# Market keywords -> normalized market label
MARKET_KEYWORDS = [
    ('EUROPE', 'Europe'), ('RHD', 'RHD'), ('LHD', 'LHD'),
    ('AUST/NZ', 'AUS/NZ'), ('AUSTRALIA', 'AUS'), ('NEW ZEALAND', 'NZ'),
    ('TURKEY', 'Turkey'), ('MIDDLE EAST', 'Middle East'),
    ('INDONESIA', 'Indonesia'), ('MALAYSIA', 'Malaysia'),
    ('HONG KONG', 'Hong Kong'), ('CANADA', 'Canada'),
    ('BANGLADESH', 'Bangladesh'), ('AIMI', 'AIMI'),
    ('AIOS', 'AIOS'), ('TAIWAN', 'Taiwan'), ('THAI', 'Thailand'),
    ('CNG', 'CNG'), ('EXP', 'Export'), ('DOM', 'Domestic'),
]

EMISSION_RE = re.compile(r'\b(EURO\s*\d|EU\s*\d[A-Z\+,]*|EXC\.\s*EURO\s*\d|NON[\s-]*EURO)\b', re.I)
YEAR_RE = re.compile(r'\b(\d{2,4}\.\d)\b|\b(19|20)?(\d{2})\s*-\s*(19|20)?(\d{2})\b')

# Family classification (from EPC headers) -> bucket
FAMILY_TO_BUCKET = {
    'TRUCKS N': 'LCV',
    'TRUCKS F&G': 'MCV/HCV',
    'TRUCKS 810': 'HCV',
    'TRUCKS C&E': 'HCV',
    'BUSES LT, LV': 'Bus',
    'BUSES LR': 'Bus',
    'PASSENGER VEHICLE PICK UP': 'Pickup',
    'PASSENGER VEHICLE SUV': 'SUV',
    'INDUSTRIAL ENGINE 4-CYLINDER': 'Industrial',
    'INDUSTRIAL ENGINE 6-CYLINDER': 'Industrial',
    'MARINE ENGINE 4-CYLINDER': 'Marine',
    'MARINE ENGINE 6-CYLINDER': 'Marine',
    'COMPONENT COMPONENT': 'Component',
}


def parse_series(text: str) -> set:
    """Extract model series codes from a row text."""
    found = set()
    # Tokenize on common separators
    tokens = re.split(r'[\s\(\)/,]+', text.upper())
    for t in tokens:
        if t in SERIES_VOCABULARY:
            found.add(t)
        # Also match prefixes like 'CYH(LHD)' -> 'CYH'
        m = re.match(r'^([A-Z]{2,4})', t)
        if m and m.group(1) in SERIES_VOCABULARY:
            found.add(m.group(1))
    return found


def parse_markets(text: str) -> set:
    """Extract markets from a row text."""
    upper = text.upper()
    out = set()
    for kw, label in MARKET_KEYWORDS:
        if kw in upper:
            out.add(label)
    return out


def parse_emissions(text: str) -> set:
    """Extract emission level tokens."""
    return {m.group(1).upper().replace(' ', '') for m in EMISSION_RE.finditer(text)}


def parse_year_span(text: str):
    """Return (min_year, max_year) parsed from text, or (None, None)."""
    years = []
    # Pattern: "92.0 - 96.0" -> 1992, 1996
    for m in re.finditer(r'\b(\d{2})\.(\d)\b', text):
        y = int(m.group(1))
        full = 2000 + y if y < 30 else 1900 + y
        years.append(full)
    # Pattern: "2016", "1992-2002"
    for m in re.finditer(r'\b(19|20)(\d{2})\b', text):
        years.append(int(m.group(1) + m.group(2)))
    if not years:
        return (None, None)
    return (min(years), max(years))


def enrich(scrape_result: dict) -> dict:
    """Take one PN scrape result and return enriched dict."""
    pn = scrape_result.get('pn')
    found = scrape_result.get('found', False)
    total = scrape_result.get('total')
    editions = scrape_result.get('editions', 0)
    avg_positions = scrape_result.get('avgPositions')
    families = scrape_result.get('families', [])
    by_family = scrape_result.get('byFamily', {}) or {}

    series = set()
    markets = set()
    emissions = set()
    years = []

    for fam, rows in by_family.items():
        for row in rows:
            txt = row.get('text', '')
            series.update(parse_series(txt))
            markets.update(parse_markets(txt))
            emissions.update(parse_emissions(txt))
            y_lo, y_hi = parse_year_span(txt)
            if y_lo: years.append(y_lo)
            if y_hi: years.append(y_hi)

    # GVW class from series
    gvw_classes = sorted({SERIES_TO_GVW[s] for s in series if s in SERIES_TO_GVW})

    # Buckets from families (high-level)
    buckets = sorted({FAMILY_TO_BUCKET.get(f, f) for f in families})

    return {
        'pn': pn,
        'epc_found': 'Y' if found else 'N',
        'epc_total_results': total,
        'epc_editions': editions,
        'epc_avg_positions': avg_positions,
        'epc_multi_position_flag': 'Y' if avg_positions and avg_positions >= 1.5 else '',
        'epc_vehicle_families': '; '.join(sorted(families)),
        'epc_buckets': '; '.join(buckets),
        'epc_model_series': ', '.join(sorted(series)),
        'epc_gvw_classes': ' / '.join(gvw_classes),
        'epc_markets': '; '.join(sorted(markets)),
        'epc_emissions': '; '.join(sorted(emissions)),
        'epc_year_min': min(years) if years else None,
        'epc_year_max': max(years) if years else None,
        'epc_year_span': f"{min(years)}-{max(years)}" if years else '',
        'epc_partial': scrape_result.get('partial') or ('truncated' if scrape_result.get('truncated') else ''),
        'epc_error': scrape_result.get('error', ''),
    }


def main():
    if len(sys.argv) < 2:
        print('usage: parse_epc_results.py <epc_results.json> [out.json]')
        sys.exit(1)
    with open(sys.argv[1], encoding='utf-8') as f:
        results = json.load(f)
    # Dedupe: keep first non-error per PN
    seen = {}
    for r in results:
        pn = r.get('pn')
        if not pn: continue
        if pn not in seen or (seen[pn].get('error') and not r.get('error')):
            seen[pn] = r
    enriched = [enrich(r) for r in seen.values()]
    out_path = sys.argv[2] if len(sys.argv) > 2 else 'epc_enriched.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, ensure_ascii=False, indent=1)
    print(f'Parsed {len(enriched)} unique PNs -> {out_path}')
    # Summary stats
    found = sum(1 for e in enriched if e['epc_found'] == 'Y')
    multi = sum(1 for e in enriched if e['epc_multi_position_flag'])
    print(f'  EPC_Found Y: {found}/{len(enriched)}')
    print(f'  Multi-position (avgPos >= 1.5): {multi}')
    bucket_counts = defaultdict(int)
    for e in enriched:
        for b in e['epc_buckets'].split('; '):
            if b: bucket_counts[b] += 1
    print('  Distribution by bucket:')
    for b, c in sorted(bucket_counts.items(), key=lambda x: -x[1]):
        print(f'    {b}: {c}')


if __name__ == '__main__':
    main()
