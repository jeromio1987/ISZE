import pandas as pd
from pathlib import Path

for name in ["CY2023-2024.XLSX", "CY2025.XLSX"]:
    p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\12_raw\sales") / name
    xl = pd.ExcelFile(p)
    for sheet in xl.sheet_names:
        df = pd.read_excel(p, sheet_name=sheet, nrows=3)
        if "Billing Date" in df.columns:
            print("===", name, sheet, "===")
            print(list(df.columns))
            df5 = pd.read_excel(p, sheet_name=sheet, nrows=5)
            for col in ["Sold-to pt", "Payer", "DB", "Sold-to party"]:
                if col in df5.columns:
                    print(col, "->", df5[col].tolist())
            break
