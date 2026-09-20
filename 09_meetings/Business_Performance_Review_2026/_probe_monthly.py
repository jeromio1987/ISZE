from pathlib import Path
import pandas as pd

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ISZE_MONTHLY_SALES_REPORT_09.2026.xlsx")
print("exists", p.exists(), p.stat().st_size if p.exists() else "")
xl = pd.ExcelFile(p)
print("sheets", xl.sheet_names)
for sh in xl.sheet_names[:4]:
    df = pd.read_excel(p, sheet_name=sh, header=None, nrows=14)
    print("=== sheet", sh, df.shape)
    print(df.head(12).to_string(max_colwidth=28))
