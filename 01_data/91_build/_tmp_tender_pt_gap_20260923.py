import json, re, sys, io, os
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = r'C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install'
FEED = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json'

pt = json.load(open(os.path.join(ROOT, '_pt_anuncios_tight.json'), encoding='utf-8'))
print('Portugal raw anunios fetched by the fetcher:', len(pt))

W = re.compile(r'warrant|garant|gwaranc|garanz|garantia|garant[ií]a', re.I)
def lots(r): return ' || '.join(str(x) for x in (r.get('Lotes') or []))
def blob(r):
    return ' | '.join([str(r.get('descricaoAnuncio') or ''), lots(r),
                       ' '.join(r.get('CPVs') or []), str(r.get('designacaoEntidade') or '')])
h = [r for r in pt if W.search(blob(r))]
print('Portugal raw ads containing a warranty/garantia word:', len(h))
for r in h:
    print('   -', str(r.get('descricaoAnuncio'))[:140])

print()
print('--- Portugal CPV spread (raw, pre-gate) ---')
c = Counter()
for r in pt:
    for cp in (r.get('CPVs') or []):
        c[str(cp)[:8]] += 1
for k, v in c.most_common(20):
    print(f'   {v:4d}  {k}')

# what reached the feed
d = json.load(open(FEED, encoding='utf-8'))
feed_ids = set()
for n in d['notices']:
    if n.get('Country') == 'Portugal':
        feed_ids.add(str(n.get('Source Notice ID')))
print()
print('Portugal notices in feed:', len(feed_ids))
missing = [r for r in pt if str(r.get('IdIncm')) not in feed_ids]
print('Portugal raw ads NOT in feed:', len(missing), 'of', len(pt))
print()
print('--- the 20 biggest raw Portugal ads by base price: in feed or not ---')
def base(r):
    try: return float(r.get('PrecoBase') or 0)
    except: return 0.0
for r in sorted(pt, key=lambda x: -base(x))[:22]:
    inb = 'IN  ' if str(r.get('IdIncm')) in feed_ids else 'out '
    lotsn = len(r.get('Lotes') or [])
    print(f"  {inb} EUR {base(r):>14,.0f}  {lotsn:2d} lots  {str(r.get('descricaoAnuncio'))[:105]}")
