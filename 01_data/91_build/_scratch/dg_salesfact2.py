import sys, io
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'

dg = pd.read_excel(P, sheet_name='DG list (deduped)', header=3)
dg.columns = [str(c).strip() for c in dg.columns]
def norm(x):
    if x is None: return None
    return str(x).strip().split('.')[0].zfill(10)
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

dim = pd.read_csv(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\distributor_dimension.csv', dtype=str)
dim['_s'] = dim['sold_to_sap'].str.strip().str.split('.').str[0].str.zfill(10)
dmap = dict(zip(dim['_s'], dim['distributor_code']))
dname = dict(zip(dim['_s'], dim['customer_name']))
dscope = dict(zip(dim['_s'], dim['scope']))
dlabel = dict(zip(dim['_s'], dim['gps_db_label']))

sf = pd.read_csv(r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\Data\00_derived\sales_fact.csv', dtype=str)
sf['pn'] = sf['part_number'].map(norm)
sf['s'] = sf['sold_to_sap'].map(norm)
sf['_dg'] = sf['pn'].isin(dg_union)
dg_rows = sf[sf['_dg']].copy()
dg_rows['db'] = dg_rows['s'].map(dmap).fillna(dg_rows['s'])
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
print("DB | scope | #DG P/N | DG qty | DG value | years")
print(g.to_string())

print("\nTotal DG value:", round(dg_rows['val'].sum(),2), "  DG qty:", round(dg_rows['qty'].sum(),1), "  distinct DG P/Ns:", dg_rows['pn'].nunique())
print("Total distinct distributors with DG demand:", dg_rows['db'].nunique())

# family split per top DB (value)
print("\n===== DG family VALUE per top-12 DB =====")
for db in g.head(12).index:
    sub = dg_rows[dg_rows['db']==db]
    fc = sub.groupby('fam')['val'].sum().round(0).sort_values(ascending=False).to_dict()
    fq = sub.groupby('fam')['qty'].sum().round(0).sort_values(ascending=False).to_dict()
    print(f"{db:12s} value={fc}")
    print(f"{'':12s} qty  ={fq}")
