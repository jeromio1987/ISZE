from pathlib import Path
import pandas as pd

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ISZE_MONTHLY_SALES_REPORT_09.2026.xlsx")
df = pd.read_excel(p, sheet_name="14.09.26", header=None)
print("latest shape", df.shape)
print(df.to_string(max_colwidth=26))
print()
bp = pd.read_excel(p, sheet_name="BP", header=None, nrows=16)
print("BP shape", bp.shape)
print(bp.to_string(max_colwidth=24))
