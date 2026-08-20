#!/usr/bin/env python3
"""One-off: dump ITUK Parts Sales Target Study structure."""
from pathlib import Path
import pandas as pd

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\08_Distributor\ITUK Parts Sales Target Study.xlsx")
out = Path(__file__).resolve().parent.parent / "data" / "_ituk_study_dump.txt"
lines = [f"exists={p.exists()}", f"path={p}"]
if p.exists():
    xl = pd.ExcelFile(p, engine="openpyxl")
    lines.append(f"sheets={xl.sheet_names}")
    for sn in xl.sheet_names:
        df = pd.read_excel(p, sheet_name=sn, header=None, engine="openpyxl")
        lines.append(f"\n=== {sn} ({df.shape[0]}x{df.shape[1]}) ===")
        for i in range(max(0, 33), min(len(df), 45)):
            row = [str(x) if pd.notna(x) else "" for x in df.iloc[i].tolist()]
            lines.append(f"row{i+1}: " + " | ".join(row[:20]))
out.write_text("\n".join(lines), encoding="utf-8")
print("wrote", out)
