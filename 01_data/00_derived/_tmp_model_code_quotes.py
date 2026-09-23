"""Ad-hoc: quote the four model-code statements with exact line numbers."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PY = ROOT / "03_analytics" / "Isuzu" / "prism" / "scripts" / "build_model_code_to_tonnage.py"
CSV = ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "model_code_to_tonnage.csv"

print("=== build_model_code_to_tonnage.py ===")
for i, line in enumerate(PY.read_text(encoding="utf-8").splitlines(), 1):
    if "provably wrong" in line or "NMR" in line:
        print(f"{i:4d}| {line}")

print()
print("=== model_code_to_tonnage.csv, NMR rows ===")
import csv as _csv
with open(CSV, encoding="utf-8", newline="") as fh:
    for i, row in enumerate(_csv.reader(fh), 1):
        if row and row[0] in ("model_code", "NMR", "NMR85"):
            print(f"{i:4d}| code={row[0]!r} band={row[1]!r} label={(row[2] if len(row)>2 else '')!r} "
                  f"conf={row[-1]!r}")
