import sys, io, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def rows(p, sheet, start, n):
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb[sheet]
    print(f"\n===== {p} :: {sheet} rows {start}..{start+n} =====")
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i < start: continue
        print(i, [str(c)[:22] if c is not None else '' for c in r])
        if i >= start+n: break

rows(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\ITUK\Sales to Dealers_ITUK_CY2025.xlsx', 'Sheet1', 4, 8)
rows(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\UTI\UTIPartSales_2025-12_YTD.xlsx', 'UTIPartSales', 4, 8)
