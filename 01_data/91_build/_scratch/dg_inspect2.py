import sys, io, csv, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def head_csv(p, n=3):
    print(f"\n===== CSV {p} =====")
    with open(p, newline='', encoding='utf-8-sig') as f:
        r = csv.reader(f)
        for i, row in enumerate(r):
            print(i, row)
            if i >= n: break

base = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived'
head_csv(base + r'\dealer_sellout_long_IUK_CY2025.csv')
head_csv(base + r'\dealer_sellout_long_IRELAND_CY2025.csv')
head_csv(r'C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\Data\00_derived\dealer_sellout_long_GREECE_CY2025.csv')

def head_xlsx(p, sheet=None, n=4, hdr=0):
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    print(f"\n===== XLSX {p} =====")
    print("SHEETS:", wb.sheetnames)
    for s in (wb.sheetnames if sheet is None else [sheet]):
        ws = wb[s]
        print(f"--- sheet {s!r} dims {ws.max_row}x{ws.max_column} ---")
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            print("  ", [str(c)[:20] if c is not None else '' for c in r])
            if i >= hdr + n: break

head_xlsx(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\ITUK\Sales to Dealers_ITUK_CY2025.xlsx')
head_xlsx(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\UTI\UTIPartSales_2025-12_YTD.xlsx')
head_xlsx(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\GREECE\Petros_Parts_Sold_Qties_2025.xlsx')
head_xlsx(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\IRELAND\IRELAND_Sales_to_Dealer_2025_2026YTD_Jul.xlsx')
head_xlsx(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\dealer_sales\IUK\IUK_Monthly_Demand_2025_2026YTD_July.xlsx')
