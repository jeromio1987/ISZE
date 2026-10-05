import json, re, sys, io, os
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = r'C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install'

j = json.load(open(os.path.join(ROOT, 'isze_dashboard_v2_data.json'), encoding='utf-8'))
print('type', type(j), list(j.keys())[:10] if isinstance(j, dict) else len(j))

def walk(o, path=''):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + '/' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, path + '[]')
    else:
        yield path, o

hits = [(p, v) for p, v in walk(j) if isinstance(v, str) and re.search(r'warrant|garant|гаранц', v, re.I)]
print('string fields containing a warranty word:', len(hits))
c = Counter(p for p, v in hits)
for k, v in c.most_common(20):
    print(f'  {v:5d}  {k}')
print()
for p, v in hits[:15]:
    print(f'  {p}: {v[:200]}')
