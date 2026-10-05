import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

p = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json'
d = json.load(open(p, encoding='utf-8'))

print('META:')
print(json.dumps(d['meta'], indent=1, ensure_ascii=False))
print()
print('--- OPPORTUNITY SAMPLE ---')
print(json.dumps(d['opportunities'][0], indent=1, ensure_ascii=False))
print()
print('--- NOTICE SAMPLE ---')
print(json.dumps(d['notices'][0], indent=1, ensure_ascii=False))
print()
print('--- OPP KEYS UNION ---')
ks = {}
for o in d['opportunities']:
    for k in o:
        ks[k] = ks.get(k, 0) + 1
for k, v in sorted(ks.items(), key=lambda x: -x[1]):
    print(f'{v:5d}  {k}')
print()
print('--- NOTICE KEYS UNION ---')
ks = {}
for o in d['notices']:
    for k in o:
        ks[k] = ks.get(k, 0) + 1
for k, v in sorted(ks.items(), key=lambda x: -x[1]):
    print(f'{v:5d}  {k}')
