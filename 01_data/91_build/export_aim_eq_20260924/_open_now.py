import pandas as pd

DER = '01_data/00_derived/'
EQ = '01_data/91_build/export_aim_eq_20260924/'
UNK = ['', 'unknown', 'unknown review', 'nan']


def n(v):
    return str(v).strip().upper().lstrip('0')


q = pd.read_csv(EQ + 'queue.csv', dtype=str, low_memory=False)
q['k'] = q['pn'].map(n)
q = q.drop_duplicates('k')

m = pd.read_csv(DER + 'aim_master_v2.csv', dtype=str, low_memory=False)
m['k'] = m['part_number'].map(n)
mi = m.drop_duplicates('k').set_index('k')

sub = mi.reindex(q['k'])
fam = sub['aim_l1'].fillna('').str.strip().str.lower()
has_row = sub['part_number'].notna()

open_mask = fam.isin(UNK)
print('price-list parts                :', len(q))
print('with a real family              :', int((~open_mask).sum()))
print('still open                      :', int(open_mask.sum()))
print()
o = pd.DataFrame({'k': q['k'].values, 'fam': fam.values, 'has_row': has_row.values})[open_mask.values]
print('  of the open:')
print('    still carrying the marker   :', int(o['fam'].isin(['unknown', 'unknown review']).sum()))
print('    no row on the master at all :', int((~o['has_row']).sum()))
print('    row present, family blank   :', int((o['has_row'] & (o['fam'] == '')).sum()))
print('    total                       :', len(o))
