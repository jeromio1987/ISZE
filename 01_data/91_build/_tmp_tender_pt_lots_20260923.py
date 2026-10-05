import json, re, sys, io, os
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = r'C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install'

j = json.load(open(os.path.join(ROOT, '_pt_anuncios_tight.json'), encoding='utf-8'))
print('=== PORTUGAL BASE raw anunios fetched (pre-gate):', len(j), '===')
def lots(r):
    return ' || '.join(str(x) for x in (r.get('Lotes') or []))
def blob(r):
    return ' | '.join([str(r.get('descricaoAnuncio') or ''), lots(r),
                       ' '.join(r.get('CPVs') or []), str(r.get('designacaoEntidade') or ''),
                       ' '.join(r.get('tiposContrato') or [])])

V = re.compile(r'pick|pickup|pick-up|cabine|cabine\b|chassi|moto?r|máquina|maquina|cami[aã]o|pesado|mercadorias|caixa aberta|basculante|grua|cisterna|todo-?terreno|4x4|tra[cç][cç][aã]o|reboque|autocar|furg', re.I)
print()
print('--- lots / descriptions mentioning a commercial-vehicle shape ---')
n = 0
for r in j:
    b = blob(r)
    if V.search(b):
        n += 1
        print(f"  {r.get('dataPublicacao')}  {r.get('designacaoEntidade')[:52]:52s}  base {r.get('PrecoBase')}")
        print(f"      {str(r.get('descricaoAnuncio'))[:150]}")
        if r.get('Lotes'):
            for l in r['Lotes']:
                print(f"        LOT: {str(l)[:150]}")
        print(f"      CPV: {', '.join(r.get('CPVs') or [])[:120]}")
print('total CV-shaped:', n, 'of', len(j))

print()
print('=== warranty words in Portugal raw ===')
W = re.compile(r'warrant|garant|gwaranc|garanz|garantia|garant[ií]a', re.I)
h = [r for r in j if W.search(blob(r))]
print('hits:', len(h))
for r in h:
    print('  ', r.get('descricaoAnuncio'))
    for l in (r.get('Lotes') or []):
        if W.search(str(l)): print('      LOT:', l)

print()
print('=== Portugal CPV spread (raw pre-gate) ===')
c = Counter()
for r in j:
    for cp in (r.get('CPVs') or []):
        c[str(cp)[:8]] += 1
for k, v in c.most_common(25):
    print(f'  {v:4d}  {k}')
