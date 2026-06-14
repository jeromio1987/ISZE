"""
Parse EPC scrape results into enriched FIG-KEY workbook columns.

Input: epc_results.json — list of per-PN scrape dicts from window.__allResults
Output: enrichment dict keyed by PN with derived columns.
"""
import json, re, sys
from collections import defaultdict

# Isuzu model series -> GVW class
# Source: official Isuzu nomenclature, public spec sheets
SERIES_TO_GVW = {
    # N-series LCV (3.5-7.5t)
    'NHR': 'LCV 3.5t', 'NLR': 'LCV 3.5t', 'NMR': 'LCV 5.5t',
    'NKR': 'LCV 5.5t', 'NPR': 'LCV 7.5t', 'NQR': 'LCV 7.5t',
    'NNR': 'LCV 5.5t', 'NRR': 'LCV 7.5t', 'NN': 'LCV', 'NP': 'LCV',
    # F-series medium (10-26t)
    'FRR': 'MCV 10-12t', 'FSR': 'MCV 12-14t', 'FSS': 'MCV 12-14t',
    'FTR': 'MCV 12-18t', 'FTS': 'MCV 12-18t', 'FVR': 'HCV 18-26t',
    'FVZ': 'HCV 24-26t', 'FVM': 'HCV 24t+', 'FVL': 'HCV',
    # G-series (rare)
    'GVR': 'HCV', 'GVZ': 'HCV', 'GVM': 'HCV',
    # 810 / C&E heavy 26t+
    'CVR': 'HCV 26t+', 'CXH': 'HCV 26t+', 'CYH': 'HCV 26t+',
    'CXJ': 'HCV 26t+', 'CXY': 'HCV 26t+', 'CXZ': 'HCV 26t+',
    'CYZ': 'HCV 26t+', 'CVS': 'HCV 26t+', 'CXW': 'HCV 26t+',
    'CYW': 'HCV 26t+',
    # Passenger pickup (D-Max predecessor)
    'TFR': 'Pickup 2-2.5t', 'TFS': 'Pickup 2-2.5t',
    # Passenger SUV
    'UBS': 'SUV', 'UBR': 'SUV', 'UPS': 'SUV', 'UES': 'SUV',
    'UER': 'SUV', 'UCS': 'SUV', 'UCR': 'SUV',
    # Buses
    'LT': 'Bus', 'LV': 'Bus', 'LR': 'Bus',
}

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
        if t in SERIES_TO_GVW:
            found.add(t)
        # Also match prefixes like 'CYH(LHD)' -> 'CYH'
        m = re.match(r'^([A-Z]{2,4})', t)
        if m and m.group(1) in SERIES_TO_GVW:
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
