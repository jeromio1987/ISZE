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

dim = pd.read_csv(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\distributor_dimension.csv', dtype=str)
dim['_s'] = dim['sold_to_sap'].str.strip().str.split('.').str[0].str.zfill(10)
dmap = dict(zip(dim['_s'], dim['distributor_code']))
dscope = dict(zip(dim['distributor_code'], dim['scope']))
dregion = dict(zip(dim['distributor_code'], dim['region']))

sf = pd.read_csv(r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\Data\00_derived\sales_fact.csv', dtype=str)
sf['pn'] = sf['part_number'].map(norm)
sf['s'] = sf['sold_to_sap'].map(norm)
sf['_dg'] = sf['pn'].isin(dg_union)
dg_rows = sf[sf['_dg']].copy()
dg_rows['db'] = dg_rows['s'].map(dmap).fillna(dg_rows['s'])
dg_rows['scope'] = dg_rows['db'].map(dscope)
dg_rows['region'] = dg_rows['db'].map(dregion)
dg_rows['qty'] = dg_rows['billed_qty'].astype(float)
dg_rows['val'] = dg_rows['net_sales_value'].astype(float)

# Armenia single part
arm = dg_rows[dg_rows['db']=='ARMENIA']
print("ARMENIA DG parts:")
print(arm.groupby(['pn']).agg(qty=('qty','sum'), val=('val','sum'), desc=('description','first')).to_string())
print()

# top DG parts by value overall
print("===== TOP 15 DG parts by value (all DBs) =====")
tp = dg_rows.groupby('pn').agg(qty=('qty','sum'), val=('val','sum'), desc=('description','first'), dbs=('db','nunique')).sort_values('val', ascending=False).round(0)
print(tp.head(15).to_string())
print()

# scope check for top DBs
print("scope for key DBs:", {d: dscope.get(d) for d in ['IUK','ITUK','UMI','UTI','GERMANY','NORWAY','BELGIUM','PORTUGAL','SWEDEN','HUNGARY','IRELAND','GREECE','MALTA','CYPRUS','ROMANIA','DENMARK','FINLAND','ICELAND','ARMENIA','UKRAINE']})
print("region for ARMENIA/UKRAINE:", dregion.get('ARMENIA'), dregion.get('UKRAINE'))
