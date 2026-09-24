import json, glob, os, sys, io, re
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd

ROOT = r'C:\Users\jerom\Desktop\claude\ISZE'
FEED = os.path.join(ROOT, '01_data', '14_dashboards', 'tender_data.json')

d = json.load(open(FEED, encoding='utf-8'))
opps = d['opportunities']; nots = d['notices']

print('#' * 70)
print('# 1. FEED HISTORY — every saved run (the batches over time)')
print('#' * 70)
files = sorted(glob.glob(os.path.join(ROOT, '01_data', '14_dashboards', 'tender_data*.json')))
rows = []
for f in files:
    try:
        j = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        rows.append((os.path.basename(f), 'ERR', 0, 0, '', '')); continue
    o = j.get('opportunities') or []
    n = j.get('notices') or []
    meta = j.get('meta') or {}
    sc = meta.get('source_counts') or {}
    rows.append((os.path.basename(f), len(n), len(o), len(sc),
                 meta.get('generated_at', '')[:16],
                 ' '.join(sorted(k.split()[-1] for k in sc))))
print(f"{'file':50s} {'notices':>8s} {'opps':>6s} {'srcs':>5s}  generated")
for r in rows:
    print(f"{r[0]:50s} {r[1]:>8} {r[2]:>6} {r[3]:>5}  {r[4]}")
print()
print('sources in latest feed:')
for k, v in sorted((d['meta']['source_counts']).items(), key=lambda x: -x[1]):
    print(f'  {v:5d}  {k}')

print()
print('#' * 70)
print('# 2. PER-BATCH YIELD (merge stat files: raw -> gated -> merged)')
print('#' * 70)
for f in sorted(glob.glob(os.path.join(ROOT, '04_tools', 'ISZE_Tender_Monitor_Install', '_phase1_*merge_stats.json'))):
    j = json.load(open(f, encoding='utf-8'))
    tag = os.path.basename(f).replace('_phase1_', '').replace('_merge_stats.json', '')
    for sheet, s in (j.get('sheets') or {}).items():
        if 'side_raw' in s:
            raw = s['side_raw']; gk = s['gated_kept']; mg = s['merged_into_main']
            print(f"  {tag:12s} {sheet:22s} raw {raw:4d} -> gated {gk:4d} -> merged {mg:4d}"
                  f"  (dropped {raw-gk}, xdup {s.get('skipped_cross_sheet_dup',0)}, idup {s.get('skipped_internal_dup',0)})")
        else:
            print(f"  {tag:12s} {sheet:22s} {s}")

print()
print('#' * 70)
print('# 3. PORTUGAL — everything we hold')
print('#' * 70)
po = [o for o in opps if o.get('country') == 'Portugal']
pn = [n for n in nots if n.get('Country') == 'Portugal']
print(f'opportunities: {len(po)}   notices: {len(pn)}')
print()
print(f"{'published':11s} {'deadline':11s} {'decision':10s} {'seg':16s} {'value':>11s} {'cur':4s} {'brand':6s}  title")
for o in sorted(po, key=lambda x: x.get('published_first') or ''):
    v = o.get('value_amount')
    vs = f"{v:,.0f}" if isinstance(v, (int, float)) else '-'
    print(f"{(o.get('published_first') or '-'):11s} {(o.get('deadline_date') or '-'):11s} "
          f"{(o.get('decision') or '-'):10s} {(o.get('product_segment') or '-'):16s} {vs:>11s} "
          f"{(o.get('currency') or '-'):4s} {','.join(o.get('brand_hits') or []) or '-':6s}  "
          f"{(o.get('title') or '')[:95]}")
print()
print('Portugal by source:', dict(Counter(s for o in po for s in (o.get('sources') or []))))
print('Portugal decisions:', dict(Counter(o.get('decision') for o in po)))
print('Portugal segments:', dict(Counter(o.get('product_segment') for o in po)))
print('Portugal aftersales:', dict(Counter(o.get('aftersales_summary') for o in po)))
vals = [o['value_amount'] for o in po if isinstance(o.get('value_amount'), (int, float))]
print(f'Portugal with a value: {len(vals)}/{len(po)}  sum EUR {sum(vals):,.0f}  median {pd.Series(vals).median():,.0f}' if vals else 'no values')

print()
print('#' * 70)
print('# 4. WHAT WAS ASKED — CPV mix across the whole feed')
print('#' * 70)
def cpv2(o):
    c = str(o.get('cpv_code') or '')
    return c[:5] if len(c) >= 5 else '?'
c = Counter(cpv2(o) for o in opps)
for k, v in c.most_common(20):
    sample = next((o.get('cpv_desc') or '' for o in opps if cpv2(o) == k and o.get('cpv_desc')), '')
    print(f'  {v:4d}  CPV {k}  {sample[:90]}')

print()
print('#' * 70)
print('# 5. WHAT WAS IN FOR ISUZU — brand hits and vehicle-tender shape')
print('#' * 70)
bh = [o for o in opps if o.get('brand_hits')]
print(f'opportunities with a brand hit: {len(bh)} of {len(opps)}')
print('brands named:', dict(Counter(b for o in bh for b in o['brand_hits'])))
print()
print('--- the ones that name Isuzu ---')
for o in bh:
    if 'isuzu' in [b.lower() for b in o['brand_hits']]:
        print(f"  [{o['country']}] {(o.get('published_first') or '-')} {o.get('decision')} "
              f"{(o.get('value_amount') or 0):,.0f} {o.get('currency')}")
        print(f"    {o['title'][:180]}")
        print(f"    {o.get('buyer')}  |  {o.get('url')}")
print()
print('--- product_segment mix (whole feed) ---')
print(dict(Counter(o.get('product_segment') for o in opps)))
print('--- decision mix (whole feed) ---')
print(dict(Counter(o.get('decision') for o in opps)))
print('--- aftersales summary mix ---')
print(dict(Counter(o.get('aftersales_summary') for o in opps)))

print()
print('#' * 70)
print('# 6. WARRANTY / GUARANTEE SWEEP — every language pattern')
print('#' * 70)
PATTERNS = {
    'warrant(y|ies)': r'warrant(?:y|ies)',
    'garantie/garantia/garanzia/gwarancja': r'garant|gwaranc|garanz|ábyrg',
    'Gewährleistung/Garantie': r'gew[äa]hrleistung|garantie',
    'takuu (fi)': r'takuu',
    'jámy (cz) / záruka': r'z[áa]ruka|j[áa]m',
    'garanti (dk/no/sv)': r'garanti',
    'garantía (es) / garantia (pt)': r'garant[ií]a',
    'eγγύηση (gr)': r'εγγ[ύυ]ηση',
    'гаранц (bg)': r'гаранц',
}
def blob(n):
    return ' | '.join(str(n.get(k) or '') for k in ('Title','Title Compact','Description','CPV Desc','Buyer','Notice Type','Procedure Type'))
for name, pat in PATTERNS.items():
    rx = re.compile(pat, re.I)
    hits = [n for n in nots if rx.search(blob(n))]
    print(f'  {name:42s} {len(hits):4d} notices  {dict(Counter(n["Country"] for n in hits))}')

print()
print('--- duration-in-years pattern next to a warranty-ish word (any language) ---')
YW = re.compile(r'(\d{1,2})\s*(?:ans?|anos?|jaar|jahre?|anni|lat|lata|ár|аños?|years?|år|vuotta|metus?|годин|года|лет)\b', re.I)
ANYW = re.compile(r'warrant|garant|gwaranc|garanz|gew[äa]hrleistung|takuu|z[áa]ruka|ábyrg|εγγ[ύυ]ηση|гаранц', re.I)
for n in nots:
    b = blob(n)
    if ANYW.search(b) or YW.search(b):
        m = YW.search(b); w = ANYW.search(b)
        if w:
            print(f"  [{n['Country']}] {(n.get('Title') or '')[:110]}")
            print(f"      ctx: {b[max(0,w.start()-110):w.end()+130]}")

print()
print('#' * 70)
print('# 7. TEXT DEPTH — what the engine can actually read')
print('#' * 70)
descs = [(n.get('Description') or '') for n in nots]
print(f'notices {len(nots)}; non-empty description {sum(1 for x in descs if x.strip())} '
      f'({100*sum(1 for x in descs if x.strip())/len(nots):.1f}%)')
print(f'median desc length {pd.Series([len(x) for x in descs]).median():.0f} chars; '
      f'p90 {pd.Series([len(x) for x in descs]).quantile(.9):.0f}; max {max(len(x) for x in descs)}')
print(f'descriptions at the 2000-char cap: {sum(1 for x in descs if len(x)==2000)}')
