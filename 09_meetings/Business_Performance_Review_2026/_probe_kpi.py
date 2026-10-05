from pathlib import Path
import pandas as pd

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\planning\KPI Master File august 2026.xlsx")
ph = pd.read_excel(p, sheet_name="Parts Handling", header=None)
print("shape", ph.shape)
for i in range(0, 60):
    row = ph.iloc[i].tolist()
    txt = " | ".join("" if pd.isna(v) else str(v)[:14] for v in row[:8])
    if txt.strip(" |"):
        print(i, "::", txt)
