import sys, io
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'

dj = pd.read_excel(P, sheet_name='Data (joined)', header=3)
dj.columns = [str(c).strip() for c in dj.columns]
def isdg(v):
    if v is None: return False
    if isinstance(v, bool): return v
    return str(v).strip().lower() in ('true','1','yes','y','x','dg')
dj['_dg'] = dj['Is DG'].map(isdg)
d = dj[dj['_dg']]
f2 = d[d['BillT']=='F2'].copy()

def fam(desc):
    x = str(desc).upper()
    if 'AIR BAG' in x or 'AIRBAG' in x: return 'Airbag'
    if 'BELT' in x: return 'Seatbelt pretensioner'
    if 'CONTROL UNIT' in x or 'SRS' in x: return 'SRS control unit'
    if any(k in x for k in ['OIL','LUB','FLUID','CLEAN','ATF','GREASE','DEF','ADBLUE']): return 'Bulk lubricant'
    return 'Other'
f2['fam'] = f2['Description'].map(fam)

parts = f2.groupby('Material').agg(desc=('Description','first'), lines=('Material','size'), eur=('EUR Amount','sum'), kg=('Gross weight (kg)','sum')).reset_index()
parts['fam'] = parts['desc'].map(fam)
print("n distinct shipped DG parts (F2):", len(parts))
print("\nFamily summary:")
print(parts.groupby('fam').agg(n=('Material','size'), lines=('lines','sum'), eur=('eur','sum'), kg=('kg','sum')).round(1).to_string())
print("\n42 parts (F2) sorted by family then EUR:")
print(parts.sort_values(['fam','eur'], ascending=[True,False])[['Material','desc','fam','lines','eur','kg']].to_string(index=False))
