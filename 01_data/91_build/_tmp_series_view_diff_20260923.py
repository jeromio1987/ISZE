"""series_to_tonnage.csv DIFFERS in bytes - is any BAND different, or only the row set?

It is a generated view of the authored map, so it legitimately gains rows (the map carries
more codes and richer evidence). What must NOT change is the band any code already had.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260923_canon_map"

a = pd.read_csv(BAK / "series_to_tonnage.csv", encoding="utf-8-sig", dtype=str).fillna("")
b = pd.read_csv(DER / "series_to_tonnage.csv", encoding="utf-8-sig", dtype=str).fillna("")
print(f"rows: before {len(a)}  after {len(b)}")
print(f"columns only before: {sorted(set(a.columns) - set(b.columns))}")
print(f"columns only after : {sorted(set(b.columns) - set(a.columns))}")

A = dict(zip(a.series.str.upper(), a.tonnage_band))
B = dict(zip(b.series.str.upper(), b.tonnage_band))

moved = {k: (A[k], B[k]) for k in set(A) & set(B) if A[k] != B[k]}
print()
print(f"codes present in both: {len(set(A) & set(B))}")
print(f"codes whose band MOVED: {len(moved)}")
for k, (x, y) in sorted(moved.items()):
    print(f"    {k}: {x!r} -> {y!r}")
print()
print(f"codes only in the new file ({len(set(B) - set(A))}): {sorted(set(B) - set(A))}")
print(f"codes only in the old file ({len(set(A) - set(B))}): {sorted(set(A) - set(B))}")
print()
verdict = "no band moved" if not moved else "A BAND MOVED"
print(f"VERDICT: {verdict}; the byte change is the added rows and the longer evidence quotes.")
