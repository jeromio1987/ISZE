import re, sys, pathlib

p = pathlib.Path(r'C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\Universe_Yellow_Paper_COMPLETE_DRAFT_2026-09-21.md')
t = p.read_text(encoding='utf-8')
low = t.lower()

print('WORDS:', len(t.split()), 'CHARS:', len(t), 'LINES:', t.count('\n')+1)

banned = ['mode a','mode b','sell-out','sellout','sell out','street fill','street index',' wallet','wallet ','book b',
          'class_factor','loss function','ship-gate','spar','harness','payload','artefact','artifact','rollup',
          'granularity','instantiate',' upsteam','upstream','downstream','residual','spine','baseline',
          'the gate','gate report','drift','catalogue','taxonomy','fully verified','2,526','2526','337,181',
          '54.4','32.4','61,791','37,019','248.54 per dealer','846 bought','no local copy was available was']
print('\n--- banned words / phrases')
for b in banned:
    n = low.count(b)
    if n:
        print(f'  HIT {b!r}: {n}')

print('\n--- required do-not-publish figure scan (digits)')
for pat in [r'\b2,526\b', r'\b337,181\b', r'\b54\.4\b', r'\b32\.4\b', r'\b61,791\b', r'\b37,019\b',
            r'\b124,952\b', r'\b1,090\b', r'\b137,700\b', r'\b226,626\b', r'\b628,185\b', r'\b1\.22%\b',
            r'\b864\b', r'\b365,093\b', r'\b223,897\b', r'\b3,467\b', r'\b2,402\b', r'\b47,923\b',
            r'\b249\b', r'\b425\b', r'\b1,930\b', r'\b27,543\.79\b', r'\b719\b', r'\b836\b', r'\b852\b',
            r'\b147\b', r'\b148\b', r'\b519\b', r'\b514\b', r'\b40\.3\b', r'\b117\.6\b', r'\b55\.3\b',
            r'\b11,835,911\b', r'\b2\.11\b', r'\b50\.85\b', r'\b22,389\b', r'\b66,018\b', r'\b538,346\b']:
    m = re.findall(pat, t)
    if m: print(f'  {pat}: {len(m)}')

print('\n--- acronym first-use check')
for a in ['AIM','IDS','PRISM','BVP','SPA','GP','GM','CY','FY','UIO','GPS','PMS','VIN','SaTy','DLOD','DB','IUK','UMI','UTI','ITUK','ISZE','IML','KPI']:
    i = t.find(a)
    print(f'  {a}: first at char {i}')
