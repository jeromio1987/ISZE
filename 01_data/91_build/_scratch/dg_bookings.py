# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import io, warnings
warnings.filterwarnings('ignore')

OUT = io.open(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\dg_bookings.txt', 'w', encoding='utf-8')
def p(*a):
    print(*a, file=OUT)

XLSX = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'
BASE = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived'

def s(x):
    if pd.isna(x): return ''
    if isinstance(x, float) and x.is_integer(): return str(int(x))
    return str(x).strip()

data = pd.read_excel(XLSX, sheet_name='Data (joined)', header=3)
dglist = pd.read_excel(XLSX, sheet_name='DG list (deduped)', header=3)
for c in ['Material','Bill.Doc.','Sales Doc.']:
    data[c] = data[c].map(s)
data['BillT'] = data['BillT'].astype(str).str.strip()
data['Entity'] = data['Entity'].astype(str).str.strip()
data['MoT'] = data['MoT'].astype(str).str.strip()

dglist['Material'] = dglist['Material'].map(s)
dglist['Newest material no.'] = dglist['Newest material no.'].map(s)
dg_mat = set(dglist['Material']) | set(dglist['Newest material no.'])
dg_mat.discard('')
data['IsDG'] = data['Material'].map(lambda m: m in dg_mat)

gen = data[(data['BillT']=='F2') & (data['Material']!='REBATE')].copy()

# ---- booking rollup (replicate Orders logic) ----
grp = gen.groupby('Bill.Doc.').agg(
    entity=('Entity','first'),
    billt=('BillT','first'),
    year=('Year','first'),
    date=('Billing Date','first'),
    lines=('Qty','size'),
    air=('MoT', lambda x: int((x=='Air').sum())),
    sea=('MoT', lambda x: int((x=='Sea').sum())),
    truck=('MoT', lambda x: int((x=='Truck').sum())),
    dglines=('IsDG','sum'),
    tot_w=('Gross weight (kg)','sum'),
    dg_w=('Gross weight (kg)', lambda x: x[gen.loc[x.index,'IsDG']==True].sum() if hasattr(x,'index') else 0),
    tot_v=('EUR Amount','sum'),
).reset_index()

# dg_w computed incorrectly above; recompute properly
dg_w_map = gen[gen['IsDG']].groupby('Bill.Doc.')['Gross weight (kg)'].sum()
grp['dg_w'] = grp['Bill.Doc.'].map(dg_w_map).fillna(0)
grp['has_dg'] = grp['dglines'] > 0

def mot(r):
    a,s,t = r['air'], r['sea'], r['truck']
    if a>0 and s==0 and t==0: return 'Air'
    if s>0 and a==0 and t==0: return 'Sea'
    if t>0 and a==0 and s==0: return 'Truck'
    if a+s+t==0: return '(none)'
    return 'Mixed'
grp['MoT'] = grp.apply(mot, axis=1)

p('=== bookings total (F2) ===', len(grp))
p('=== bookings by MoT ===')
p(grp['MoT'].value_counts().to_dict())

# DG bookings
dg_bk = grp[grp['has_dg']].copy()
p()
p('=== DG-containing bookings total ===', len(dg_bk))
p('=== DG bookings by MoT ===')
p(dg_bk['MoT'].value_counts().to_dict())

# pure-air DG bookings
pure_air_dg = dg_bk[dg_bk['MoT']=='Air']
p()
p('=== DG bookings that are PURE AIR ===', len(pure_air_dg))
p('=== DG bookings with ANY air line (Air + Mixed-with-air) ===', int((dg_bk['air']>0).sum()))
p('=== DG bookings pure air, single-line (lines==1) ===', int((pure_air_dg['lines']==1).sum()))
p('=== DG bookings pure air, multi-line ===', int((pure_air_dg['lines']>1).sum()))
p('=== DG pure-air median lines ===', pure_air_dg['lines'].median())
p('=== DG pure-air median weight (kg) ===', pure_air_dg['dg_w'].median())
p('=== DG pure-air median total weight (kg) ===', pure_air_dg['tot_w'].median())
p('=== DG pure-air median value (EUR) ===', pure_air_dg['tot_v'].median())
p('=== DG pure-air total weight ===', pure_air_dg['dg_w'].sum())
p('=== DG pure-air total value ===', pure_air_dg['tot_v'].sum())
p('=== DG pure-air mean kg ===', pure_air_dg['dg_w'].mean())
p()
p('=== DG pure-air bookings detail (sorted by date) ===')
cols=['Bill.Doc.','entity','year','date','lines','air','sea','truck','dglines','dg_w','tot_w','tot_v']
p(pure_air_dg.sort_values('date')[cols].to_string(index=False))

# DG sea bookings
pure_sea_dg = dg_bk[dg_bk['MoT']=='Sea']
p()
p('=== DG bookings PURE SEA ===', len(pure_sea_dg))
p('=== DG pure-sea median kg ===', pure_sea_dg['dg_w'].median())
p('=== DG pure-sea mean kg ===', pure_sea_dg['dg_w'].mean())
p('=== DG pure-sea total weight ===', pure_sea_dg['dg_w'].sum())
p('=== DG pure-sea total value ===', pure_sea_dg['tot_v'].sum())
p()
p('=== DG sea booking detail ===')
p(pure_sea_dg.sort_values('dg_w', ascending=False)[cols].head(30).to_string(index=False))

OUT.close()
print('done_bookings')
