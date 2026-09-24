import pandas as pd

DER = '01_data/00_derived/'
EQ = '01_data/91_build/export_aim_eq_20260924/'
UNK = ['', 'unknown', 'unknown review', 'nan']


def n(v):
    return str(v).strip().upper().lstrip('0')


def price(s):
    t = (s.fillna('').astype(str).str.replace('\u00a0', '', regex=False)
         .str.replace(' ', '', regex=False))

    # The Price column mixes Dutch and US punctuation: 1 300 rows read 177,06
    # and 18 read 8 693.31. If there is a comma, comma is the decimal point and
    # any dot is a thousands separator. If there is no comma, a lone dot is the
    # decimal point. Assuming one convention turns 1 177,96 into 117796.
    def one(x):
        x = x.strip()
        if ',' in x:
            return x.replace('.', '').replace(',', '.')
        return x

    return pd.to_numeric(t.map(one), errors='coerce')


q = pd.read_csv(EQ + 'queue.csv', dtype=str, low_memory=False)
q['k'] = q['pn'].map(n)
q = q.drop_duplicates('k')

pub = pd.read_csv(DER + 'AIM_Master_PN_Categories_Figkey_20260924.csv', dtype=str, low_memory=False)
pub['k'] = pub['part_number'].map(n)
pi = pub.drop_duplicates('k').set_index('k')

m = pd.read_csv(DER + 'aim_master_v2.csv', dtype=str, low_memory=False)
m['k'] = m['part_number'].map(n)
mi = m.drop_duplicates('k').set_index('k')

fam = pi.reindex(q['k'])['aim_level_1'].fillna('').astype(str).str.strip()
fam_l = fam.str.lower()
open_mask = fam_l.isin(UNK)

sub = mi.reindex(q['k'])
has_row = sub['part_number'].notna()
marker = fam_l.isin(['unknown', 'unknown review'])

o = pd.DataFrame({
    'part_number': q['k'].values,
    'what': q['Description'].values,
    'eur': price(q['list_eur']).values,
    'marker': marker.values,
    'has_row': has_row.values,
})[open_mask.values].copy()


def reason(r):
    if not r['has_row']:
        return 'no row on the master to write to'
    if r['marker']:
        return 'still shows the Unknown marker'
    return 'row is blank, nothing in the wording to reason from'


o['why'] = o.apply(reason, axis=1)
o = o.sort_values('eur', ascending=False)

print('OPEN PARTS: %d   list value EUR %s' % (len(o), format(round(o['eur'].sum(), 2), ',')))
print()
print('by reason:')
g = o.groupby('why').agg(parts=('part_number', 'size'), eur=('eur', 'sum')).sort_values('eur', ascending=False)
for w, r in g.iterrows():
    print('  %-46s %3d parts   EUR %s' % (w, r['parts'], format(round(r['eur'], 2), ',')))
print()
print('the 25 biggest:')
print('%-12s %-38s %10s  %s' % ('part', 'what it is', 'EUR', 'why open'))
for r in o.head(25).itertuples(index=False):
    print('%-12s %-38s %10s  %s' % (r.part_number[:12], str(r.what)[:38], format(round(r.eur, 2), ','), r.why))

o.to_csv(EQ + 'open_now_79.csv', index=False, encoding='utf-8-sig')
print()
print('written:', EQ + 'open_now_79.csv')
