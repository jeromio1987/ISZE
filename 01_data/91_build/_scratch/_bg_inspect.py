import openpyxl, sys

def sheets(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    return wb.sheetnames

for p in [r"c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx",
          r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UMIUTI_Logistics_Study_v4_enhanced.xlsx",
          r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UMIUTI_Logistics_Study_v3.xlsx"]:
    try:
        print("="*80)
        print(p)
        for s in sheets(p):
            print("   ", s)
    except Exception as e:
        print("ERR", p, e)
