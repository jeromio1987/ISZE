import json, sys, io
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd

FEED = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json'
d = json.load(open(FEED, encoding='utf-8'))
opps = d['opportunities']

def val(o):
    v = o.get('value_amount')
    return v if isinstance(v, (int, float)) else None

print('=== PER-SOURCE QUALITY (latest feed, opportunity level) ===')
rows = []
for src in sorted({s for o in opps for s in (o.get('sources') or [])}):
    sub = [o for o in opps if src in (o.get('sources') or [])]
    cv = [o for o in sub if o.get('product_segment') in ('pickup', 'truck')]
    sel = [o for o in sub if o.get('decision') in ('Attack', 'Selective')]
    withv = [o for o in sub if val(o) is not None]
    withf = [o for o in sub if o.get('fleet_size')]
    gps = [o for o in sub if o.get('gps_addressable_per_year_eur')]
    vs = [val(o) for o in withv]
    rows.append(dict(source=src, opps=len(sub), cv=len(cv), selective=len(sel),
                     with_value=len(withv), pct_value=round(100*len(withv)/len(sub)),
                     with_fleet=len(withf), with_gps=len(gps),
                     eur_value=round(sum(vs)) if vs else 0,
                     median_eur=round(pd.Series(vs).median()) if vs else 0))
t = pd.DataFrame(rows).sort_values('opps', ascending=False)
pd.set_option('display.width', 200)
print(t.to_string(index=False))

print()
print('=== same, PORTUGAL only, row by row ===')
po = [o for o in opps if o.get('country') == 'Portugal']
for o in sorted(po, key=lambda x: x.get('published_first') or ''):
    v = val(o)
    print(f"  {o.get('published_first')}  {o.get('decision'):9s} {o.get('product_segment'):8s} "
          f"{(f'{v:,.0f}' if v else '-'):>11s} {o.get('currency') or '':3s} "
          f"fleet={o.get('fleet_size')}  {(o.get('title') or '')[:80]}")

print()
print('=== feed-level summary ===')
print('opportunities:', len(opps))
print('with a value:', sum(1 for o in opps if val(o) is not None))
print('with a fleet count:', sum(1 for o in opps if o.get('fleet_size')))
print('with GPS euros:', sum(1 for o in opps if o.get('gps_addressable_per_year_eur')))
print('with a deadline:', sum(1 for o in opps if o.get('deadline_date')))
print('CV (pickup+truck):', sum(1 for o in opps if o.get('product_segment') in ('pickup','truck')))
print('decision Attack:', sum(1 for o in opps if o.get('decision') == 'Attack'))
print('decision Selective:', sum(1 for o in opps if o.get('decision') == 'Selective'))
print('brand hits:', sum(1 for o in opps if o.get('brand_hits')))
print('aftersales tagged:', sum(1 for o in opps if o.get('aftersales_tags')))
print('outcomes recorded:', sum(1 for o in opps if o.get('outcome')))
