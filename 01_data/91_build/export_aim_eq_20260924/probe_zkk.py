import pandas as pd

DER = '01_data/00_derived/'
EQ = '01_data/91_build/export_aim_eq_20260924/'
m = pd.read_csv(DER + 'aim_master_v2.csv', dtype=str, low_memory=False)

print('=== JP code columns present ===')
jp = [c for c in m.columns if c.startswith('jp_')]
print(jp)
print()

for c in jp:
    v = m[c].fillna('').astype(str).str.strip()
    filled = (v != '').sum()
    print('%-16s filled %7s  distinct %6s' % (c, format(filled, ','), format(v[v != ''].nunique(), ',')))

print()
print('=== ZKK values, top 40 ===')
zkk = m['jp_zkk'].fillna('').astype(str).str.strip()
print(zkk[zkk != ''].value_counts().head(40).to_string())

print()
print('=== any leaf anywhere with CAB in it ===')
for col in ['aim_l2', 'aim_l3']:
    v = m[col].fillna('').astype(str).str.strip()
    hits = v[v.str.upper().str.contains('CAB', na=False)]
    print(col, '->', hits.value_counts().head(15).to_dict())

print()
print('=== leaves under Accident & Body, top 25 ===')
ab = m[m['aim_l1'].fillna('').str.strip() == 'Accident & Body']
print(ab['aim_l2'].fillna('').value_counts().head(25).to_string())

print()
print('=== full paths containing CAB ===')
p = (m['aim_l1'].fillna('') + ' > ' + m['aim_l2'].fillna('') + ' > ' + m['aim_l3'].fillna(''))
hp = p[p.str.upper().str.contains('CAB', na=False)]
print(hp.value_counts().head(20).to_string())

print()
print('=== the open parts, with any JP code evidence ===')
q = pd.read_csv(EQ + 'open_now_79.csv', dtype=str, low_memory=False)
q['k'] = q['part_number'].astype(str).str.strip().str.upper().str.lstrip('0')
m['k'] = m['part_number'].astype(str).str.strip().str.upper().str.lstrip('0')
mi = m.drop_duplicates('k').set_index('k')
cols = ['jp_zkk', 'jp_zuk', 'jp_hkk', 'jp_eple', 'jp_fig_key', 'jp_class_new', 'jp_class_current', 'jp_code_source', 'fig_key']
sub = mi.reindex(q['k'])
q = q.assign(**{c: sub[c].values for c in cols if c in sub.columns})
print(q[['part_number', 'what', 'eur', 'why', 'jp_zkk', 'jp_zuk', 'jp_class_current', 'fig_key']].head(30).to_string(index=False))
q.to_csv(EQ + 'open_79_with_jp_codes.csv', index=False, encoding='utf-8-sig')
print()
print('written', EQ + 'open_79_with_jp_codes.csv')
