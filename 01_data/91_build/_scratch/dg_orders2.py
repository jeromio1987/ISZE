import sys, io
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'

o = pd.read_excel(P, sheet_name='Orders', header=3)
o.columns = [str(c).strip() for c in o.columns]
print("Orders cols:", list(o.columns))
print("rows:", len(o))
print("MoT values:", o['MoT'].value_counts(dropna=False).to_dict())
print("Has DG values:", o['Has DG'].value_counts(dropna=False).to_dict())

def hasdg(v):
    if v is None: return False
    if isinstance(v, bool): return v
    return str(v).strip().lower() in ('true','1','yes','y','x')
o['_dg'] = o['Has DG'].map(hasdg)
dg = o[o['_dg']]
print("\nDG bookings total:", len(dg))
print("DG bookings by MoT:", dg['MoT'].value_counts(dropna=False).to_dict())
print("DG bookings by Entity x MoT:", dg.groupby(['Entity','MoT']).size().to_dict())
print("\nDG booking total value:", round(dg['Total value (EUR)'].sum(),2))
print("DG booking total weight:", round(dg['DG weight (kg)'].sum(),2))
print("DG lines total:", dg['DG lines'].sum())
# single-line air DG bookings
air = dg[dg['MoT']=='Air']
print("\nAir DG bookings:", len(air), "single-line:", (air['Lines']==1).sum())
