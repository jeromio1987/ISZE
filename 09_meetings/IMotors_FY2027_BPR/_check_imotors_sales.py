from pathlib import Path
import json, re

# Find likely monthly report / plan files mentioning IMOTORS with those magnitudes
root = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
candidates = []
for folder in [
    root/"01_data",
    root/"09_meetings/IMotors_FY2027_BPR",
]:
    if not folder.exists(): continue
    for p in folder.rglob("*"):
        if not p.is_file(): continue
        n = p.name.lower()
        if p.suffix.lower() not in {".xlsx",".xls",".csv",".json"}: continue
        if any(x in n for x in ["monthly", "kpi", "plan", "imotor", "vp", "forecast", "master"]):
            candidates.append(p)

print("CAND", len(candidates))
for p in sorted(candidates, key=lambda x: x.stat().st_mtime, reverse=True)[:40]:
    print(f"{p.stat().st_mtime:.0f}\t{p.stat().st_size}\t{p}")
