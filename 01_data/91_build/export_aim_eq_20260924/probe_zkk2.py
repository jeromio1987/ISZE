import pandas as pd

DER = '01_data/00_derived/'
EQ = '01_data/91_build/export_aim_eq_20260924/'
UNK = ['', 'unknown', 'unknown review', 'nan']


def n(v):
    return str(v).strip().upper().lstrip('0')


m = pd.read_csv(DER + 'aim_master_v2.csv', dtype=str, low_memory=False)
m['k'] = m['part_number'].map(n)
m['fam'] = m['aim_l1'].fillna('').str.strip()
m['path'] = m['aim_l1'].fillna('') + ' > ' + m['aim_l2'].fillna('') + ' > ' + m['aim_l3'].fillna('')
known = m[~m['fam'].str.lower().isin(UNK)].copy()

q = pd.read_csv(EQ + 'open_now_79.csv', dtype=str, low_memory=False)
q['k'] = q['part_number'].map(n)
mi = m.drop_duplicates('k').set_index('k')
sub = mi.reindex(q['k'])

print('=== do the 79 open parts carry JP codes? ===')
for c in ['jp_zkk', 'jp_zuk', 'jp_hkk', 'jp_eple', 'jp_class_current', 'jp_class_new', 'fig_key']:
    v = sub[c] if c in sub.columns else pd.Series([None] * len(q))
    fill = v.notna() & (v.fillna('').astype(str).str.strip() != '')
    print('%-18s filled on %3d of %d open parts   (%d of the whole master)' % (c, int(fill.sum()), len(q), int((m[c].fillna('').astype(str).str.strip() != '').sum())))

print()
print('=== how pure is ZKK as a way to name a family? ===')
z = known[known['jp_zkk'].fillna('').astype(str).str.strip() != ''].copy()
g = z.groupby('jp_zkk')['fam'].agg(n='nunique', sz='size')
clean = g[g['n'] == 1]
print('ZKK codes on the master           :', len(g))
print('  map to exactly one family       :', len(clean), ' covering %s rows' % format(int(clean['sz'].sum()), ','))
print('  map to more than one family     :', len(g) - len(clean), ' covering %s rows' % format(int(g['sz'].sum() - clean['sz'].sum()), ','))
print()
print('the mixed ones that matter (top 10 by size):')
mx = g[g['n'] > 1].sort_values('sz', ascending=False).head(10)
for code, r in mx.iterrows():
    fams = z[z['jp_zkk'] == code]['fam'].value_counts().head(3).to_dict()
    print('  ZKK %-5s %6s rows -> %s' % (code, format(int(r['sz']), ','), fams))

print()
print('=== same test for the JP class column (26 values) ===')
for c in ['jp_class_current', 'jp_class_new']:
    zz = known[known[c].fillna('').astype(str).str.strip() != ''].copy()
    gg = zz.groupby(c)['fam'].agg(n='nunique', sz='size')
    cl = gg[gg['n'] == 1]
    print('%-18s: %s codes, %s single-family (%s rows), %s mixed (%s rows)' % (
        c, len(gg), len(cl), format(int(cl['sz'].sum()), ','), len(gg) - len(cl), format(int(gg['sz'].sum() - cl['sz'].sum()), ',')))

print()
print('=== what ZKK do cab-like parts carry? ===')
cab = m[m['description'].fillna('').str.upper().str.contains('CAB', na=False)]
print('parts with CAB in the text:', len(cab))
cv = cab[cab['jp_zkk'].fillna('').astype(str).str.strip() != '']
print(cv.groupby('jp_zkk')['fam'].agg(rows='size', families='nunique').sort_values('rows', ascending=False).head(10).to_string())
print()
print('sample cab parts and where they sit:')
print(cab[['part_number', 'description', 'jp_zkk', 'path']].head(12).to_string(index=False))
