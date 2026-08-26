import sys, io, openpyxl
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
dgd = dj[dj['_dg']].copy()

print("BillT values (DG):", dgd['BillT'].value_counts(dropna=False).to_dict())
print("Year values (DG):", dgd['Year'].value_counts(dropna=False).to_dict())
print("Entity x MoT doc counts:")
print(dgd.groupby(['Entity','MoT'])['Bill.Doc.'].nunique())
print("\nDG docs by Entity (any MoT):", dgd.groupby('Entity')['Bill.Doc.'].nunique())
print("DG docs total:", dgd['Bill.Doc.'].nunique())
print("\nDocs with BOTH air and sea DG lines?")
tbl = dgd.groupby('Bill.Doc.')['MoT'].nunique()
print("docs spanning >1 MoT:", (tbl>1).sum())
print("\nMoT NaN DG lines:")
print(dgd[dgd['MoT'].isna()][['Bill.Doc.','Material','Description','Entity','MoT','EUR Amount']].to_string())
print("\nTruck DG lines:", dgd[dgd['MoT']=='Truck'].shape[0])

# Check the 'Orders' sheet and 'Data Audit' for the "genuine shipped lines" filter
print("\n\n===== Data Audit sheet =====")
da = pd.read_excel(P, sheet_name='Data Audit', header=None)
for i,row in da.iterrows():
    print(i, [str(c)[:40] if c is not None else '' for c in row])
