import pandas as pd, numpy as np
pd.set_option('display.width', 300); pd.set_option('display.max_rows', 100)
ROOT = r'C:\Users\jerom\Desktop\claude\ISZE'
OUT = ROOT + r'\01_data\91_build\export_aim_tiering_20260924'

q = pd.read_csv(OUT + r'\queue_final_tiered.csv', dtype=str, encoding='utf-8-sig')
q['hs'] = (q['Commodity Code'].fillna('').astype(str).str.strip()
           .str.replace(r'\.0$', '', regex=True).str.replace(' ', '', regex=False))
for c in ('pr00', 'list', 'd_n', 'f_n'):
    q[c] = pd.to_numeric(q[c], errors='coerce')
q['tierA'] = q['tierA'] == 'True'

t = pd.read_csv(OUT + r'\hs_to_l1_purity.csv', dtype=str)
hs_l1 = dict(zip(t['hs'], t['top_l1']))
q['hs_l1'] = q['hs'].map(hs_l1)
both = q[q['d_l1'].notna() & q['hs_l1'].notna()]
print("queue rows with both a description route and an HS route:", len(both))
print("  HS modal family == description family:", int((both['hs_l1'] == both['d_l1']).sum()))
print("  HS modal family != description family:", int((both['hs_l1'] != both['d_l1']).sum()))
print("  HS modal family would be right only if you never look at the part text")

print()
print("=== the queue's own HS spread ===")
hq = q[q['hs'] != '']
print("distinct HS codes:", hq['hs'].nunique(), " rows:", len(hq))
g = hq.groupby('hs').agg(rows=('pn', 'size'), nfam=('d_l1', 'nunique'))
print("HS codes that carry more than one family ON THE QUEUE:", int((g['nfam'] > 1).sum()), "of", len(g))
print("largest codes and how many families they hold:")
for k, r in g.sort_values('rows', ascending=False).head(10).iterrows():
    print("  %s  rows=%3d  families=%d" % (k, int(r['rows']), int(r['nfam'])))
print()
print("=== Tier A euro by the metric that matters ===")
A = q[q['tierA']]
print("Tier A rows=%d PN=%d" % (len(A), A['pn'].nunique()))
print("  list-price EUR sum (what the customer pays for one): %.2f" % A['list'].sum())
print("  the extract's Value column sum (not comparable across goods): %.2f" % A['pr00'].sum())
print("Tier B rows=%d PN=%d" % (len(q) - len(A), q[~q['tierA']]['pn'].nunique()))
print("  list-price EUR sum: %.2f" % q[~q['tierA']]['list'].sum())
