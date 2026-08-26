import sys, io
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'

dg = pd.read_excel(P, sheet_name='DG list (deduped)', header=3)
dg.columns = [str(c).strip() for c in dg.columns]
def norm(x):
    if x is None: return None
    s = str(x).strip()
    return s.zfill(10)
dg['_mat'] = dg['Material'].map(norm)
dg['_new'] = dg['Newest material no.'].map(norm)
dg_union = set(dg['_mat']) | set(dg['_new'])
desc = dict(zip(dg['_mat'], dg['Description'])) | dict(zip(dg['_new'], dg['Description']))
def fam(d):
    x = str(d).upper()
    if 'AIR BAG' in x or 'AIRBAG' in x: return 'Airbag'
    if 'BELT' in x: return 'Seatbelt pretensioner'
    if 'CONTROL UNIT' in x or 'SRS' in x: return 'SRS control unit'
    if any(k in x for k in ['OIL','LUB','FLUID','CLEAN','ATF','GREASE','DEF','ADBLUE','BATTERY']): return 'Bulk lubricant'
    return 'Other'

sf = pd.read_csv(r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\Data\00_derived\sales_fact.csv', dtype=str)
print("sales_fact shape:", sf.shape)
print("years:", sf['year'].value_counts().to_dict())
print("sold_to_sap count:", sf['sold_to_sap'].nunique())
sf['pn'] = sf['part_number'].map(norm)
sf['_dg'] = sf['pn'].isin(dg_union)
dg_rows = sf[sf['_dg']]
print("DG rows in sales_fact:", len(dg_rows))
print("DG distinct part numbers:", dg_rows['pn'].nunique())
print("DG qty:", dg_rows['billed_qty'].astype(float).sum())
print("DG net_sales_value:", dg_rows['net_sales_value'].astype(float).sum())

# map sold_to_sap -> distributor code
dim = pd.read_csv(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\distributor_dimension.csv', dtype=str)
dim['sold_to_sap'] = dim['sold_to_sap'].str.strip()
dmap = dict(zip(dim['sold_to_sap'], dim['distributor_code']))
dscope = dict(zip(dim['distributor_code'], dim['scope']))

dg_rows = dg_rows.copy()
dg_rows['db'] = dg_rows['sold_to_sap'].map(dmap).fillna(dg_rows['sold_to_sap'])
dg_rows['scope'] = dg_rows['db'].map(dscope)
dg_rows['qty'] = dg_rows['billed_qty'].astype(float)
dg_rows['val'] = dg_rows['net_sales_value'].astype(float)
dg_rows['fam'] = dg_rows['pn'].map(lambda p: fam(desc.get(p,'')))

g = dg_rows.groupby('db').agg(
    dg_pn=('pn','nunique'),
    dg_qty=('qty','sum'),
    dg_val=('val','sum'),
    years=('year', lambda s: ','.join(sorted(set(s)))),
    scope=('scope','first'),
).sort_values('dg_val', ascending=False).round(1)
print("\n===== DG demand per distributor (ISZE->DB billing, sales_fact) =====")
print(g.to_string())

print("\n===== DG family (qty) per top DB =====")
for db in g.head(8).index:
    sub = dg_rows[dg_rows['db']==db]
    fc = sub.groupby('fam')['qty'].sum().round(0).sort_values(ascending=False).to_dict()
    print(f"{db:14s} {fc}")
