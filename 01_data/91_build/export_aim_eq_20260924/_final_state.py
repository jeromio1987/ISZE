import pandas as pd

DER = '01_data/00_derived/'
EQ = '01_data/91_build/export_aim_eq_20260924/'
UNK = ['', 'unknown', 'unknown review', 'nan']


def n(v):
    return str(v).strip().upper().lstrip('0')


q = pd.read_csv(EQ + 'queue.csv', dtype=str, low_memory=False)
q['k'] = q['pn'].map(n)
q = q.drop_duplicates('k')

pub = pd.read_csv(DER + 'AIM_Master_PN_Categories_Figkey_20260924.csv', dtype=str, low_memory=False)
pub['k'] = pub['part_number'].map(n)
pi = pub.drop_duplicates('k').set_index('k')

v = pi.reindex(q['k'])['aim_level_1'].fillna('').astype(str).str.strip().str.lower()
real = ~v.isin(UNK)
print('WHAT THE PUBLISHED FILE SHOWS (aim_level_1 - the column a person filters on)')
print('  price-list parts      :', len(q))
print('  with a real family    :', int(real.sum()))
print('  open                  :', int((~real).sum()))
print('    carrying the marker :', int(v.isin(['unknown', 'unknown review']).sum()))
print('    row but blank       :', int((v == '').sum()))
print()
print('published file rows     :', len(pub))
print('published with a family :', int((~pub['aim_level_1'].fillna('').str.strip().str.lower().isin(UNK)).sum()))

m = pd.read_csv(DER + 'aim_master_v2.csv', dtype=str, low_memory=False)
print()
print('master rows             :', len(m))
mw = pd.read_csv(DER + 'aim_master_v2.csv.bak_pre_def_pump_leaf_20260924_182731', dtype=str, low_memory=False)
print('master rows in last backup:', len(mw))
d = pd.read_csv(DER + 'aim_master_v2.csv', dtype=str, low_memory=False)
t = d[d['part_number'].astype(str).str.strip() == '7552710010']
print()
print('DEF pump kit row now:')
print(t[['part_number', 'description', 'aim_l1', 'aim_l2', 'aim_l3', 'aim_source']].to_string(index=False))
