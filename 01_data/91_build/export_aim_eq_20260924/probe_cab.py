import pandas as pd

DER = '01_data/00_derived/'
m = pd.read_csv(DER + 'aim_master_v2.csv', dtype=str, low_memory=False)
cl = pd.read_csv(DER + 'aim_pn_classification_20260920.csv', dtype=str, low_memory=False)

print('=== every taxonomy column that exists, and its distinct values ===')
for df, name, cols in [
    (m, 'aim_master_v2', ['aim_l1', 'aim_l2', 'aim_l3', 'cat_l1', 'cat_l2', 'cat_l3', 'jp_class_current']),
    (cl, 'classification_20260920', ['catalog_l1', 'catalog_l2', 'catalog_l3', 'workbook_l1', 'workbook_l2', 'workbook_l3']),
]:
    for c in cols:
        if c not in df.columns:
            continue
        v = df[c].fillna('').astype(str).str.strip()
        vals = sorted(set(v[v != '']))
        hit = [x for x in vals if 'CAB' in x.upper()]
        print('%-26s %-18s %3d values   cab-ish: %s' % (name, c, len(vals), hit if hit else '-'))

print()
print('=== what does the whole master call a cab part? (top leaf paths) ===')
m['path'] = m['aim_l1'].fillna('') + ' > ' + m['aim_l2'].fillna('') + ' > ' + m['aim_l3'].fillna('')
cab = m[m['description'].fillna('').str.upper().str.contains(r'\bCAB\b', na=False, regex=True)]
print('parts with the standalone word CAB:', len(cab))
print(cab['path'].value_counts().head(20).to_string())

print()
print('=== and the CAB ASM family of parts specifically ===')
for pat in ['CAB ASM', 'CAB;', '; CAB', 'CAB MTG', 'CAB MOUNT']:
    s = m[m['description'].fillna('').str.upper().str.contains(pat, na=False, regex=True)]
    print('%-10s %4d parts   top path: %s' % (pat, len(s), s['path'].value_counts().head(1).to_dict()))

print()
print('=== how big is the Accident & Body / body-structure area? ===')
ab = m[m['cat_l1'].fillna('').str.strip() == 'Accident']
print('cat_l1 = Accident:', len(ab))
print(ab['path'].value_counts().head(15).to_string())
