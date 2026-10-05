import json, re, sys, io
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json'
d = json.load(open(P, encoding='utf-8'))
opps = d['opportunities']; nots = d['notices']

# --- text coverage on notices
def txt(n):
    return ' | '.join(str(n.get(k) or '') for k in ('Title','Title Compact','Description','CPV Desc','Buyer','Notice Type','Procedure Type'))

has_desc = sum(1 for n in nots if (n.get('Description') or '').strip())
print('notices:', len(nots), 'with non-empty Description:', has_desc, f'{100*has_desc/len(nots):.1f}%')
print('avg desc len:', round(sum(len((n.get('Description') or '')) for n in nots)/len(nots),1))
print('max desc len:', max(len((n.get('Description') or '')) for n in nots))
print()

# --- warranty vocabulary sweep
PAT = re.compile(r'(warrant|garant|guarantee|gewa(?:hr|er)leistung|garanzia|gwarancj|gwaranc|takuu|garant[ií]a|zamka|j[aá]m[yý]|ábyrg|garanti)', re.I)
YEAR = re.compile(r'(\d{1,2})\s*(?:ans?|anos?|jaar|jahre?|jahren|jahren|jaar|anni|lat|lata|ár|ara|years?|yrs?|años?|ani|år|vuotta|vuosi|metus?|metai|years|years\b|годин|года|лет|год)', re.I)
MONTH = re.compile(r'(\d{1,3})\s*(?:m[eê]s(?:es)?|maanden?|monat(?:e|en)?|mesi|miesi[eę]cy|m[aá]n[uú]?[dt]|månader|kuukautta|months?|mnd)', re.I)

hits = [n for n in nots if PAT.search(txt(n))]
print('notices mentioning warranty/garant*:', len(hits))
c = Counter(n['Country'] for n in hits)
for k,v in c.most_common(): print(f'  {v:4d}  {k}')
print()
print('--- sample warranty sentences ---')
shown=0
for n in hits:
    blob = txt(n)
    for m in PAT.finditer(blob):
        s=max(0,m.start()-120); e=min(len(blob),m.end()+160)
        seg=blob[s:e].replace('\n',' ')
        print(f"[{n['Country']}] {seg}")
        shown+=1
        break
    if shown>=40: break
