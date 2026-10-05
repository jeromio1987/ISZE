import pandas as pd
pd.set_option('display.width', 300); pd.set_option('display.max_rows', 500)
qt = pd.read_csv(r'01_data\91_build\export_aim_tiering_20260924\queue_tiered.csv', dtype=str, encoding='utf-8-sig')
qt['pr00_eur'] = pd.to_numeric(qt['pr00_eur'], errors='coerce')
qt['list_eur'] = pd.to_numeric(qt['list_eur'], errors='coerce')
ta = qt[qt['tierA'] == 'True']
d = ta.groupby(['desc_norm', 'd_l1', 'fk']).agg(rows=('pn', 'size'), eur=('pr00_eur', 'sum'), d_n=('d_n', 'max')).reset_index()
d = d.sort_values('eur', ascending=False)
print('Tier A (description, family, fig_key) triples:', len(d))
for _, r in d.iterrows():
    print("%-46s | %-24s | %-9s | %3d | %11.2f | %d" % (
        str(r['desc_norm'])[:46], str(r['d_l1'])[:24], str(r['fk']), int(r['rows']), float(r['eur']), int(r['d_n'])))
