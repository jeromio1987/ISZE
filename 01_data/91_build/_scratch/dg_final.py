# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import io, warnings
warnings.filterwarnings('ignore')

OUT = io.open(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\dg_final.txt', 'w', encoding='utf-8')
def p(*a): print(*a, file=OUT)

XLSX = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'
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
data['Description'] = data['Description'].astype(str).str.strip()

dglist['Material'] = dglist['Material'].map(s)
dglist['Newest material no.'] = dglist['Newest material no.'].map(s)
dg_mat = set(dglist['Material']) | set(dglist['Newest material no.'])
dg_mat.discard('')
data['IsDG'] = data['Material'].map(lambda m: m in dg_mat)

gen = data[(data['BillT']=='F2') & (data['Material']!='REBATE')].copy()
dg = gen[gen['IsDG']].copy()

# booking rollup
dg_w_map = gen[gen['IsDG']].groupby('Bill.Doc.')['Gross weight (kg)'].sum()
grp = gen.groupby('Bill.Doc.').agg(
    entity=('Entity','first'), year=('Year','first'), date=('Billing Date','first'),
    lines=('Qty','size'),
    air=('MoT', lambda x:int((x=='Air').sum())),
    sea=('MoT', lambda x:int((x=='Sea').sum())),
    truck=('MoT', lambda x:int((x=='Truck').sum())),
    dglines=('IsDG','sum'),
    tot_w=('Gross weight (kg)','sum'),
    tot_v=('EUR Amount','sum'),
).reset_index()
grp['dg_w'] = grp['Bill.Doc.'].map(dg_w_map).fillna(0)
grp['has_dg'] = grp['dglines']>0
def mot(r):
    a,s,t = r['air'],r['sea'],r['truck']
    if a>0 and s==0 and t==0: return 'Air'
    if s>0 and a==0 and t==0: return 'Sea'
    if t>0 and a==0 and s==0: return 'Truck'
    if a+s+t==0: return '(none)'
    return 'Mixed'
grp['MoT'] = grp.apply(mot, axis=1)
grp['ym'] = grp['date'].dt.to_period('M').astype(str)

pure_air = grp[(grp['MoT']=='Air') & grp['has_dg']]
pure_sea = grp[(grp['MoT']=='Sea') & grp['has_dg']]
mixed_dg = grp[(grp['MoT']=='Mixed') & grp['has_dg']]

p('=== 4. AIR vs SEA DG booking size ===')
p('DG PURE-AIR bookings:', len(pure_air), ' mean dg_w=', round(pure_air['dg_w'].mean(),2), ' median dg_w=', round(pure_air['dg_w'].median(),3), ' mean tot_w=', round(pure_air['tot_w'].mean(),2), ' median tot_w=', round(pure_air['tot_w'].median(),3))
p('DG PURE-SEA bookings:', len(pure_sea), ' mean dg_w=', round(pure_sea['dg_w'].mean(),2), ' median dg_w=', round(pure_sea['dg_w'].median(),3), ' mean tot_w=', round(pure_sea['tot_w'].mean(),2), ' median tot_w=', round(pure_sea['tot_w'].median(),3))
p()
p('=== mixed DG bookings detail (reconcile 28/30/35 and 79/85) ===')
p(mixed_dg[['Bill.Doc.','entity','year','date','lines','air','sea','truck','dglines','dg_w','tot_w','tot_v']].to_string(index=False))
p('mixed DG bookings with sea lines:', int((mixed_dg['sea']>0).sum()))
p('mixed DG bookings with air lines:', int((mixed_dg['air']>0).sum()))
p('=> bookings with ANY sea line = 79 pure + mixed-with-sea =', 79 + int((mixed_dg['sea']>0).sum()))
p('=> bookings with ANY air line = 28 pure + mixed-with-air =', 28 + int((mixed_dg['air']>0).sum()))
p()
# median excluding the 2 gear-oil air outliers
go_air = [147.6, 147.6]
ex = pure_air['dg_w'][~pure_air['dg_w'].isin([147.6])]
p('median dg_w excluding the 2x147.6kg gear-oil air bookings:', round(ex.median(),3))

p()
p('=== 4b. DG value & weight by ENTITY x MoT (genuine, all years) ===')
t = dg.groupby(['Entity','MoT']).agg(lines=('Qty','size'), value=('EUR Amount','sum'), weight=('Gross weight (kg)','sum')).reset_index()
p(t.to_string(index=False))
p()
p('=== DG by YEAR x MoT (both entities) ===')
t2 = dg.groupby(['Year','MoT']).agg(lines=('Qty','size'), value=('EUR Amount','sum'), weight=('Gross weight (kg)','sum')).reset_index()
p(t2.to_string(index=False))
p()
p('=== DG by ENTITY x YEAR (all modes) ===')
t3 = dg.groupby(['Entity','Year']).agg(lines=('Qty','size'), value=('EUR Amount','sum'), weight=('Gross weight (kg)','sum')).reset_index()
p(t3.to_string(index=False))

p()
p('=== 5. SEASONALITY: DG pure-air bookings per month ===')
mcount = pure_air.groupby('ym').agg(n=('Bill.Doc.','nunique'), kg=('dg_w','sum')).reset_index()
p(mcount.to_string(index=False))
p('distinct months with >=1 DG air booking:', mcount['n'].count())
p('total DG air bookings:', int(mcount['n'].sum()))
p('=> monthly consolidation: 28 bookings ->', mcount['n'].count(), 'monthly =', int(mcount['n'].sum()) - mcount['n'].count(), 'fees saved')
p()
p('=== weekday distribution of DG air bookings ===')
pure_air['wd'] = pure_air['date'].dt.day_name()
p(pure_air['wd'].value_counts().to_dict())
p('=== day-of-month of DG air bookings ===')
pure_air['dom'] = pure_air['date'].dt.day
p('day-of-month sorted:', sorted(pure_air['dom'].tolist()))
p('month-end (day>=25):', int((pure_air['dom']>=25).sum()), 'of', len(pure_air))
p('first-half (day<=15):', int((pure_air['dom']<=15).sum()), 'of', len(pure_air))

p()
p('=== 3. FEE WASTE (DG fee €100/booking, air fixed €300/booking) ===')
n = len(pure_air)
single = int((pure_air['lines']==1).sum())
multi = n - single
months = mcount['n'].count()
p('DG air bookings:', n, '| single-line:', single, '| multi-line:', multi)
p('DG fee today: ', n, 'x 100 =', n*100)
p('DG fee if monthly: ', months, 'x 100 =', months*100, ' => DG-fee saving =', (n-months)*100)
p('Full fixed+DG (only the', single, 'single-line bookings carry a full AWB of their own):')
p('   single-line fixed+DG today:', single, 'x 400 =', single*400)
p('   multi-line: DG fee only (booking rides with non-DG):', multi, 'x 100 =', multi*100)

p()
p('=== SRS CONTROL UNIT air bookings (study challenge #2) ===')
cu = dg[dg['Description'].str.upper().str.contains('CONTROL UNIT')]
cu_air = cu[cu['MoT']=='Air']
p('control-unit DG lines:', len(cu), ' air lines:', len(cu_air))
p('control-unit air bookings (Bill.Doc):', sorted(cu_air['Bill.Doc.'].unique().tolist()))
p('control-unit air kg:', round(cu_air['Gross weight (kg)'].sum(),2), ' value:', round(cu_air['EUR Amount'].sum(),2))

p()
p('=== GEAR OIL LSD: entity split ===')
go = dg[dg['Material']=='1884057860']
p(go.groupby('Entity').agg(lines=('Qty','size'), air=('MoT', lambda x:int((x=='Air').sum())), sea=('MoT', lambda x:int((x=='Sea').sum())), value=('EUR Amount','sum'), weight=('Gross weight (kg)','sum')).to_string())
p()
p('=== restraint (seatbelt+airbag+control unit) entity split ===')
rest = dg[dg['Description'].str.upper().str.contains('BELT|AIR BAG|AIRBAG|CONTROL UNIT')]
p(rest.groupby('Entity').agg(lines=('Qty','size'), value=('EUR Amount','sum'), weight=('Gross weight (kg)','sum')).to_string())

OUT.close()
print('done_final')
