import sys, io, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'
wb = openpyxl.load_workbook(P, read_only=True, data_only=True)
ws = wb['Orders']
print("Orders dims:", ws.max_row, ws.max_column)
for i, r in enumerate(ws.iter_rows(values_only=True)):
    vals = [str(c) if c is not None else '' for c in r]
    print(i, " | ".join(v.strip()[:24] for v in vals))
    if i >= 12: break

# also compute total distinct Bill.Doc among F2 lines from Data joined via pandas
import pandas as pd
dj = pd.read_excel(P, sheet_name='Data (joined)', header=3)
dj.columns = [str(c).strip() for c in dj.columns]
f2 = dj[dj['BillT']=='F2']
print("\nF2 lines:", len(f2), "distinct Bill.Doc (shipments):", f2['Bill.Doc.'].nunique())
print("F2 MoT doc counts:", f2.groupby('MoT')['Bill.Doc.'].nunique().to_dict())
print("F2 total docs by MoT sum:", sum(f2.groupby('MoT')['Bill.Doc.'].nunique().values))
