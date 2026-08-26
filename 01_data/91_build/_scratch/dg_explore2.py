import openpyxl
import io

OUT = io.open(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\dg_explore2.txt', 'w', encoding='utf-8')
def p(*a):
    print(*a, file=OUT)

wb = openpyxl.load_workbook(r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx', read_only=True)

# Master data
ws = wb['Master data']
p('===== Master data =====')
for i, row in enumerate(ws.iter_rows(min_row=1, max_row=8, values_only=True)):
    p(i+1, row)

# Raw data
ws = wb['Raw data']
p()
p('===== Raw data =====')
for i, row in enumerate(ws.iter_rows(min_row=1, max_row=8, values_only=True)):
    p(i+1, row)

# DG x MoT Summary full (values)
ws = wb['DG x MoT Summary']
p()
p('===== DG x MoT Summary (full, formulas) =====')
for i, row in enumerate(ws.iter_rows(min_row=1, max_row=20, values_only=True)):
    p(i+1, row)

# Savings Scenarios full
ws = wb['Savings Scenarios']
p()
p('===== Savings Scenarios (full) =====')
for i, row in enumerate(ws.iter_rows(min_row=1, max_row=38, values_only=True)):
    p(i+1, row)

# Air Booking Economics full
ws = wb['Air Booking Economics']
p()
p('===== Air Booking Economics (full) =====')
for i, row in enumerate(ws.iter_rows(min_row=1, max_row=29, values_only=True)):
    p(i+1, row)

OUT.close()
print('done2')
