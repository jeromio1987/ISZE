# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import io, warnings
warnings.filterwarnings('ignore')

OUT = io.open(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\dg_main.txt', 'w', encoding='utf-8')
def p(*a):
    print(*a, file=OUT)

XLSX = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'
BASE = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived'

def s(x):
    if pd.isna(x): return ''
    if isinstance(x, float) and x.is_integer(): return str(int(x))
    return str(x).strip()

# ---- load ----
data = pd.read_excel(XLSX, sheet_name='Data (joined)', header=3)
dglist = pd.read_excel(XLSX, sheet_name='DG list (deduped)', header=3)

for c in ['Material','Bill.Doc.','Sales Doc.']:
    data[c] = data[c].map(s)
data['BillT'] = data['BillT'].astype(str).str.strip()
data['Entity'] = data['Entity'].astype(str).str.strip()
data['MoT'] = data['MoT'].astype(str).str.strip()
data['Description'] = data['Description'].astype(str).str.strip()

# commodity code -> string
def cc(x):
    if pd.isna(x): return ''
    return str(int(x)).zfill(10)
data['HS'] = data['Commodity code'].map(cc)

# ---- recompute DG set from DG list ----
dglist['Material'] = dglist['Material'].map(s)
dglist['Newest material no.'] = dglist['Newest material no.'].map(s)
dg_mat = set(dglist['Material']) | set(dglist['Newest material no.'])
dg_mat.discard('')

# master mapping P/N -> newest P/N for extra safety
master = pd.read_excel(XLSX, sheet_name='Master data', header=0)
master['P/N'] = master['P/N'].map(s)
master['Newest P/N'] = master['Newest P/N'].map(s)
pn2newest = dict(zip(master['P/N'], master['Newest P/N']))

def is_dg(m):
    if m in dg_mat: return True
    nm = pn2newest.get(m, '')
    return nm in dg_mat

data['DG_recomputed'] = data['Material'].map(is_dg)

# cross-check with provided Is DG column
p('=== cross-check recomputed DG vs provided Is DG ===')
p('provided True count:', int(data['Is DG'].sum()))
p('recomputed True count:', int(data['DG_recomputed'].sum()))
p('mismatch count:', int((data['Is DG'] != data['DG_recomputed']).sum()))
# show a few mismatches
mism = data[data['Is DG'] != data['DG_recomputed']][['Material','Description','Is DG','DG_recomputed']]
p('mismatch sample (first 20):')
p(mism.head(20).to_string())

# Use recomputed as canonical DG flag
data['IsDG'] = data['DG_recomputed']

# ---- filter genuine shipped ----
gen = data[(data['BillT']=='F2') & (data['Material']!='REBATE')].copy()
p()
p('=== genuine shipped lines (F2, excl REBATE) ===', len(gen))
p('=== genuine DG lines ===', int(gen['IsDG'].sum()))

dg = gen[gen['IsDG']].copy()

# distinct materials shipped that are DG
p('=== distinct DG materials shipped (genuine) ===', dg['Material'].nunique())

# map material -> newest material no. (canonical) for description/family/UN
mat2newest = dict(zip(dglist['Material'], dglist['Newest material no.']))
mat2desc_list = dict(zip(dglist['Material'], dglist['Description']))
# also newest -> desc (rows where material==newest)
newest2desc = {}
for _, r in dglist.iterrows():
    newest2desc[r['Newest material no.']] = r['Description']
    mat2desc_list[r['Material']] = r['Description']

def canon(m):
    return mat2newest.get(m, m)

def fam(d):
    u = d.upper()
    if 'AIR BAG' in u or 'AIRBAG' in u:
        return 'Airbag module/inflator'
    if 'BELT' in u and ('SEAT' in u or 'TONGUE' in u or 'BUCKLE' in u or 'PASSENGER' in u or 'OUTER' in u):
        return 'Seatbelt pretensioner/webbing'
    if 'CONTROL UNIT' in u:
        return 'SRS control unit'
    if 'BATTERY' in u:
        return 'Battery (lithium)'
    if 'ENGINE' in u:
        return 'Engine assembly'
    if any(k in u for k in ['OIL','ATF','FLUID','CLEAN','GREASE','GASKET','SILICON']):
        return 'Bulk lubricant/chemical'
    return 'Other'

# UN / class domain map (DATA HAS NO UN NUMBERS — these are domain-knowledge assignments)
def un_class(fam, desc):
    u = desc.upper()
    if fam == 'Airbag module/inflator':
        return ('UN3353 (hist. UN3268 / UN0503 1.4S)', 'Class 9', 'Air bag inflators / modules', 'CAO (cargo-only)')
    if fam == 'Seatbelt pretensioner/webbing':
        return ('UN3353 (hist. UN3268 / UN0503 1.4S)', 'Class 9 (or 1.4S)', 'Seat-belt pretensioners / safety devices, pyrotechnic', 'CAO (cargo-only) typically')
    if fam == 'SRS control unit':
        return ('Not regulated (unless Li cell)', 'n/a', 'Electronic control unit', 'Passenger OK')
    if fam == 'Battery (lithium)':
        return ('UN3480/UN3481', 'Class 9', 'Lithium ion battery(ies)', 'Passenger restricted (Section II)')
    if fam == 'Engine assembly':
        return ('UN3166 (residual fuel)', 'Class 9', 'Engine, flammable liquid powered', 'CAO/PA restricted')
    if fam == 'Bulk lubricant/chemical':
        if 'CLEAN' in u or 'INJECTER' in u or 'INJECTOR' in u:
            return ('UN1950 (aerosol) / UN1993', 'Class 2.1 / 3', 'Aerosols / Flammable liquid', 'Varies (LQ may apply)')
        return ('Not IATA-regulated (flash pt >60C)', 'n/a', 'Lubricating oil (not DG for air)', 'Passenger OK')
    return ('unknown', 'unknown', '', 'unknown')

# ---- DG inventory per shipped material ----
g = dg.groupby('Material').agg(
    desc=('Description','first'),
    lines=('Qty','size'),
    qty=('Qty','sum'),
    value=('EUR Amount','sum'),
    weight=('Gross weight (kg)','sum'),
    air_lines=('MoT', lambda x: int((x=='Air').sum())),
    sea_lines=('MoT', lambda x: int((x=='Sea').sum())),
    truck_lines=('MoT', lambda x: int((x=='Truck').sum())),
    hs=('HS','first'),
).reset_index()
g['canon'] = g['Material'].map(canon)
g['family'] = g['desc'].map(fam)
g[['un','cls','psn','airrest']] = g.apply(lambda r: pd.Series(un_class(r['family'], r['desc'])), axis=1)
g = g.sort_values('value', ascending=False).reset_index(drop=True)
g['net_weight_unit'] = g['Material'].map(dict(zip(dglist['Material'], dglist['Net weight'])))

p()
p('========== DG PART INVENTORY (genuine shipped, sorted by value) ==========')
p('count of distinct shipped DG parts =', len(g))
cols = ['Material','canon','desc','family','un','cls','psn','airrest','hs','lines','air_lines','sea_lines','truck_lines','qty','weight','value','net_weight_unit']
p(g[cols].to_string(index=False))

p()
p('=== total DG value ===', round(g['value'].sum(),2))
p('=== total DG weight ===', round(g['weight'].sum(),2))
p('=== total DG lines ===', int(g['lines'].sum()))
p('=== DG parts by family (value) ===')
famsum = g.groupby('family').agg(n_parts=('Material','nunique'), lines=('lines','sum'), value=('value','sum'), weight=('weight','sum')).sort_values('value', ascending=False)
p(famsum.to_string())

# Gear oil LSD specific
go = g[g['desc'].str.upper().str.contains('GEAR OIL LSD')]
p()
p('=== GEAR OIL LSD outlier ===')
p(go[cols].to_string(index=False))
# find its air lines detail
go_lines = dg[dg['Material'].isin(go['Material'])]
p(go_lines[['Material','Bill.Doc.','MoT','Qty','Gross weight (kg)','EUR Amount','Billing Date']].to_string(index=False))

OUT.close()
print('done_main')
