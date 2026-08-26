# -*- coding: utf-8 -*-
import openpyxl, io
OUT = io.open(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\dg_tabs.txt', 'w', encoding='utf-8')
def p(*a): print(*a, file=OUT)
wb = openpyxl.load_workbook(r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx', read_only=True)
for name in ['Executive Summary','Strange Behaviours','Stocking Candidates','Data Audit']:
    ws = wb[name]
    p('=====', name, '=====')
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        # skip fully empty rows
        if all(v is None for v in row): 
            continue
        p(i+1, row)
    p()
OUT.close()
print('done_tabs')
