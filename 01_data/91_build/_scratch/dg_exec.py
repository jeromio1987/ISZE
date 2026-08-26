import sys, io, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'
wb = openpyxl.load_workbook(P, read_only=True, data_only=True)

for s in ['Executive Summary','DG x MoT Summary']:
    ws = wb[s]
    print(f"\n===== {s} =====")
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        vals = [str(c) if c is not None else '' for c in r]
        if any(vals):
            print(i, " | ".join(v.strip()[:70] for v in vals if v.strip()))
