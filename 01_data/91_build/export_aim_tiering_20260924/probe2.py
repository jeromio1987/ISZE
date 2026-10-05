import pandas as pd, numpy as np
pd.set_option('display.width', 300); pd.set_option('display.max_rows', 100)
ROOT = r'C:\Users\jerom\Desktop\claude\ISZE'
OUT = ROOT + r'\01_data\91_build\export_aim_tiering_20260924'

q = pd.read_csv(OUT + r'\queue_final_tiered.csv', dtype=str, encoding='utf-8-sig')
for c in ('pr00', 'list'):
    q[c] = pd.to_numeric(q[c], errors='coerce')

print("=== what is the 'Value' column? list price / Value ratio ===")
r = q['list'] / q['pr00']
print(r.describe().to_string())
print("rows where Value < list price:", int((r > 1).sum()), " Value > list price:", int((r < 1).sum()))
print("ratio == 1 exactly:", int((r == 1).sum()))
print("sample of the largest Value rows:")
print(q.nlargest(6, 'pr00')[['pn', 'desc_norm', 'list', 'pr00']].to_string(index=False))
print()
print("=== does the commodity code add anything on the queue? ===")
# would the modal family per HS code match what the description route says?
t = pd.read_csv(OUT + r'\hs_to_l1_purity.csv', dtype=str)
hs_l1 = dict(zip(t['hs'], t['top_l1']))
q['hs_l1'] = q['hs'].map(hs_l1)
both = q[q['d_l1'].notna() & q['hs_l1'].notna()]
print("rows where both routes give something:", len(both))
print("HS modal family == description family:", int((both['hs_l1'] == both['d_l1']).sum()))
print("HS modal family != description family:", int((both['hs_l1'] != both['d_l1']).sum()))
print()
print("=== how often does ONE HS code carry several families on the queue itself? ===")
print("distinct HS codes on the queue:", q['hs'].replace('', np.nan).nunique())
print()
print("=== tier counts, unique part numbers ===")
q['tierA'] = q['tierA'] == 'True'
print("queue rows:", len(q), "unique PN:", q['pn'].nunique())
print("rows with blank commodity code:", int((q['hs'] == '').sum()))
print("Tier A rows:", int(q['tierA'].sum()))
