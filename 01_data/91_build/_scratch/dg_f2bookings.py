import sys, io
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'
o = pd.read_excel(P, sheet_name='Orders', header=3)
o.columns = [str(c).strip() for c in o.columns]
def hasdg(v):
    if v is None: return False
    if isinstance(v, bool): return v
    return str(v).strip().lower() in ('true','1','yes','y','x')
o['_dg'] = o['Has DG'].map(hasdg)
for label, m in [("ALL BillT", o['_dg']), ("F2 only", o['_dg'] & (o['BillT']=='F2'))]:
    d = o[m]
    print(f"{label}: DG bookings={len(d)}  by MoT={d['MoT'].value_counts(dropna=False).to_dict()}")
    print("   by Entity x MoT:", d.groupby(['Entity','MoT']).size().to_dict())
