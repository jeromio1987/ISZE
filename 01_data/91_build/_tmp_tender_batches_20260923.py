import json, glob, sys, io, os
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = r'C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install'

print('=== BATCH / MERGE STATS FILES (the waves) ===')
for f in sorted(glob.glob(os.path.join(ROOT, '_phase1_*stats*.json'))):
    j = json.load(open(f, encoding='utf-8'))
    print(f'--- {os.path.basename(f)} ---')
    print(json.dumps(j, indent=1, ensure_ascii=False)[:1500])
    print()

print('=== _phase1_pt_merge_stats.json (Portugal) direct ===')
p = os.path.join(ROOT, '_phase1_pt_merge_stats.json')
print(open(p, encoding='utf-8').read())

print()
print('=== longest descriptions in feed ===')
d = json.load(open(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json', encoding='utf-8'))
ns = sorted(d['notices'], key=lambda n: -len(n.get('Description') or ''))
for n in ns[:6]:
    print(f"[{n['Country']}] {n['Source']} len={len(n.get('Description') or '')}")
    print('  TITLE:', (n.get('Title') or '')[:200])
    print('  DESC :', (n.get('Description') or '')[:600])
    print()
