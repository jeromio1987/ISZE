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

for label, mask in [("ALL BillT", dj['_dg']),
                    ("F2 only (genuine shipped)", dj['_dg'] & (dj['BillT']=='F2'))]:
    d = dj[mask]
    print(f"\n===== {label}: DG lines={len(d)}, docs={d['Bill.Doc.'].nunique()} =====")
    print("docs by MoT:", d.groupby('MoT')['Bill.Doc.'].nunique().to_dict())
    print("lines by MoT:", d.groupby('MoT').size().to_dict())
    print("lines by Entity x MoT:", d.groupby(['Entity','MoT']).size().to_dict())
    print("EUR total:", round(d['EUR Amount'].sum(),2), "kg total:", round(d['Gross weight (kg)'].sum(),2))

# gear oil outlier
d = dj[dj['_dg']]
print("\n===== top DG materials by weight (F2) =====")
f2 = d[d['BillT']=='F2']
g = f2.groupby('Material').agg(lines=('Material','size'), eur=('EUR Amount','sum'), kg=('Gross weight (kg)','sum'), desc=('Description','first')).sort_values('kg', ascending=False)
print(g.head(8).to_string())
print("\nTotal DG weight (F2):", round(f2['Gross weight (kg)'].sum(),2), "kg; without gear oil:", round(f2[f2['Material']!='1884057860']['Gross weight (kg)'].sum(),2))

# 42 parts list with family
def fam(desc):
    d = str(desc).upper()
    if 'AIR BAG' in d or 'AIRBAG' in d: return 'Airbag'
    if 'BELT' in d: return 'Seatbelt pretensioner'
    if 'CONTROL UNIT' in d or 'SRS' in d: return 'SRS control unit'
    if 'OIL' in d or 'LUB' in d or 'FLUID' in d or 'CLEAN' in d or 'ATF' in d or 'GREASE' in d or 'DEF' in d or 'ADBLUE' in d: return 'Bulk lubricant'
    return 'Other'
f2 = f2.copy()
f2['fam'] = f2['desc'].map(fam)
print("\n===== 42 shipped DG parts: family distribution =====")
parts = f2.groupby('Material').agg(desc=('desc','first'), lines=('Material','size'), eur=('EUR Amount','sum'), kg=('Gross weight (kg)','sum')).reset_index()
parts['fam'] = parts['desc'].map(fam)
print("n parts:", len(parts))
print(parts.groupby('fam').agg(n=('Material','size'), eur=('eur','sum'), kg=('kg','sum'), lines=('lines','sum')).round(1).to_string())
print("\nNon-Other parts (fam != Other):")
print(parts[parts['fam']!='Other'][['Material','desc','fam','lines','eur','kg']].sort_values('fam').to_string(index=False))
print("\n'Other' shipped parts:")
print(parts[parts['fam']=='Other'][['Material','desc','fam','lines','eur','kg']].to_string(index=False))
