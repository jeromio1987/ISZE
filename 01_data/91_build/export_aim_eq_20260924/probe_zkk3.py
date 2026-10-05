import pandas as pd

DER = '01_data/00_derived/'
EQ = '01_data/91_build/export_aim_eq_20260924/'
UNK = ['', 'unknown', 'unknown review', 'nan']


def n(v):
    return str(v).strip().upper().lstrip('0')


m = pd.read_csv(DER + 'aim_master_v2.csv', dtype=str, low_memory=False)
m['k'] = m['part_number'].map(n)
m['fam'] = m['aim_l1'].fillna('').str.strip()
m['leaf'] = m['aim_l1'].fillna('') + ' > ' + m['aim_l2'].fillna('') + ' > ' + m['aim_l3'].fillna('')
known = m[~m['fam'].str.lower().isin(UNK)].copy()

q = pd.read_csv(EQ + 'open_now_79.csv', dtype=str, low_memory=False)
q['k'] = q['part_number'].map(n)
mi = m.drop_duplicates('k').set_index('k')

CODES = ['jp_zkk', 'jp_zuk', 'jp_hkk', 'jp_eple', 'jp_fig_key']


def purity(code, level):
    z = known[known[code].fillna('').astype(str).str.strip() != ''].copy()
    if z.empty:
        return None
    g = z.groupby(code)[level].agg(n='nunique', sz='size')
    one = g[g['n'] == 1]
    return {
        'code': code,
        'level': level,
        'codes': len(g),
        'single': len(one),
        'single_rows': int(one['sz'].sum()),
        'total_rows': int(g['sz'].sum()),
    }


print('=== how far down the JP code ladder can you get? ===')
print()
for level in ['fam', 'leaf']:
    label = 'FAMILY' if level == 'fam' else 'EXACT LEAF (family > group > part type)'
    print('  ->', label)
    for c in CODES:
        r = purity(c, level)
        if not r:
            continue
        pct = 100.0 * r['single_rows'] / r['total_rows'] if r['total_rows'] else 0
        print('     %-14s %4d codes   %4d name it cleanly   %6s of %6s rows  (%4.1f%%)' % (
            c, r['codes'], r['single'],
            format(int(r['single_rows']), ','), format(r['total_rows'], ','), pct))
    print()

print()
print('=== can the 62 open parts with JP codes be placed at LEAF level? ===')
sub = mi.reindex(q['k'])
for c in CODES:
    z = known[known[c].fillna('').astype(str).str.strip() != '']
    g = z.groupby(c)['leaf'].agg(n='nunique', sz='size')
    good = g[(g['n'] == 1) & (g['sz'] >= 3)]
    hits = 0
    for k in q['k']:
        if k not in mi.index:
            continue
        code = str(mi.loc[k, c]).strip() if c in mi.columns else ''
        if code and code != 'nan' and code in good.index:
            hits += 1
    print('  %-14s places %2d of the 79 open parts  (%d clean codes with 3+ rows behind them)' % (c, hits, len(good)))

print()
print('=== and at FAMILY level (the looser test)? ===')
for c in CODES:
    z = known[known[c].fillna('').astype(str).str.strip() != '']
    g = z.groupby(c)['fam'].agg(n='nunique', sz='size')
    good = g[(g['n'] == 1) & (g['sz'] >= 3)]
    hits = 0
    for k in q['k']:
        if k not in mi.index:
            continue
        code = str(mi.loc[k, c]).strip() if c in mi.columns else ''
        if code and code != 'nan' and code in good.index:
            hits += 1
    print('  %-14s places %2d of the 79 open parts  (%d clean codes with 3+ rows behind them)' % (c, hits, len(good)))
