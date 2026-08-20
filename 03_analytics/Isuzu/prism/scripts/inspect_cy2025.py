import pandas as pd
from pathlib import Path
p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\sales\CY2025.XLSX")
xl = pd.ExcelFile(p)
print("SHEETS", xl.sheet_names)
for name in xl.sheet_names:
    df = pd.read_excel(p, sheet_name=name, nrows=2)
    full = pd.read_excel(p, sheet_name=name)
    print(name, "cols=", list(df.columns)[:8], "rows=", len(full))
