import openpyxl, sys
sys.stdout.reconfigure(encoding='utf-8')

v4 = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UMIUTI_Logistics_Study_v4_enhanced.xlsx"
wb = openpyxl.load_workbook(v4, read_only=True, data_only=True)
ws = wb['Stocking Candidates']
print("dims", ws.max_row, ws.max_column)
rows = list(ws.iter_rows(values_only=True))
# header
for i, r in enumerate(rows[:8]):
    print(i, r)
print("...")
# print all PMS rows + full list of materials for boundary check
pms_rows = []
for i, r in enumerate(rows):
    if r and any(isinstance(c,str) and 'PMS' in c for c in r):
        pms_rows.append((i, r))
print("\nPMS rows:")
for i, r in pms_rows:
    print(i, r)
