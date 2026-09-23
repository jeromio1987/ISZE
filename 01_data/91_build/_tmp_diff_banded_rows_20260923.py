"""Row-level check that the bander's per-part-number bands did not move.

The aggregates are identical; this proves the underlying rows are too, so the small byte-size
change in the banded file is not a silent reclassification.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260923_canon_map"


def n(s):
    return str(s).strip().lstrip("0") or "0"


a = pd.read_csv(BAK / "epc_decode_nseries_banded.csv", dtype=str, low_memory=False).fillna("")
b = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str, low_memory=False).fillna("")
print(f"rows: old {len(a)}  new {len(b)}")
print(f"columns only in old: {sorted(set(a.columns) - set(b.columns))}")
print(f"columns only in new: {sorted(set(b.columns) - set(a.columns))}")

a["_k"] = a.pn.map(n)
b["_k"] = b.pn.map(n)
common = [c for c in a.columns if c in b.columns and c != "pn"]
a = a.set_index("_k").sort_index()
b = b.set_index("_k").sort_index()

print(f"same part numbers: {list(a.index) == list(b.index)}")
diffs = []
for c in [c for c in common if c != "_k"]:
    if not a[c].equals(b[c]):
        neq = (a[c] != b[c]).sum()
        diffs.append((c, int(neq)))

if diffs:
    print("\ncolumns that differ row by row:")
    for c, k in diffs:
        print(f"  {c:24s} {k} rows")
        sel = a.index[a[c] != b[c]][:4]
        for pn in sel:
            print(f"      pn {pn}: old={a.loc[pn, c]!r}  new={b.loc[pn, c]!r}")
else:
    print("\nEVERY shared column identical row by row.")

# the three band columns specifically
for c in ("tonnage_band", "band_status", "band_list"):
    if c in a.columns and c in b.columns:
        print(f"  {c:16s} identical: {bool(a[c].equals(b[c]))}")
