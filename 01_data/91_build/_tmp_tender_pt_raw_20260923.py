import json, re, sys, io, os
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = r'C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install'

# --- Portugal raw anúncios scrape (richer than the feed row?)
for name in ('_pt_anuncios_tight.json', '_pt_anuncios_hit_sample.json'):
    p = os.path.join(ROOT, name)
    if not os.path.exists(p): continue
    j = json.load(open(p, encoding='utf-8'))
    print('='*70); print(name, type(j), (len(j) if hasattr(j,'__len__') else ''))
    if isinstance(j, dict):
        for k, v in j.items():
            print('  key:', k, type(v), (len(v) if hasattr(v,'__len__') else v))
        # find the list
        for k, v in j.items():
            if isinstance(v, list) and v:
                print('  sample row keys:', list(v[0].keys()) if isinstance(v[0], dict) else type(v[0]))
                print('  sample:', json.dumps(v[0], ensure_ascii=False)[:1200])
                break
    elif isinstance(j, list) and j:
        print('  row keys:', list(j[0].keys()) if isinstance(j[0], dict) else type(j[0]))
        print('  sample:', json.dumps(j[0], ensure_ascii=False)[:1500])
    print()

# --- warranty vocabulary across ALL raw probe/batch JSON in the install folder
print('='*70)
print('WARRANTY-SPEC SWEEP across all raw batch/probe JSON in the install folder')
W = re.compile(r'warrant|garant|gwaranc|garanz|gew[äa]hrleistung|takuu|z[áa]ruka|ábyrg|garanti|εγγ[ύυ]ηση|гаранц|garantia|garant[ií]a', re.I)
YR = re.compile(r'(\d{1,2})\s*[-–]?\s*(?:ans?|anos?|jaar|jahre?|anni|lat|lata|años?|years?|år|vuotta|metus?|годин|года|лет)\b', re.I)
tot_hits = 0
for f in sorted(os.listdir(ROOT)):
    if not f.lower().endswith('.json'): continue
    p = os.path.join(ROOT, f)
    try:
        raw = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if not W.search(raw): continue
    hits = W.findall(raw)
    print(f'  {f:48s} warranty-word hits {len(hits):4d}  distinct {sorted(set(h.lower() for h in hits))[:8]}')
    tot_hits += 1
print('files containing warranty vocabulary:', tot_hits)
