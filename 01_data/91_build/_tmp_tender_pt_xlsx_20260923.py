import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd

P = r'C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isuzu_tenders_v3_pt.xlsx'
xl = pd.ExcelFile(P)
print('sheets:', xl.sheet_names)
for s in xl.sheet_names:
    df = xl.parse(s)
    print('---', s, df.shape)
    print('cols:', list(df.columns))
    print(df.head(20).to_string()[:6000])
    print()
