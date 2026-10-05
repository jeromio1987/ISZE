"""Did the family builder's output move when it moved onto the canonical map?"""
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"


def n(s):
    return str(s).strip().lstrip("0") or "0"


a = pd.read_csv(DER / "vehicle_family_bands.csv.bak_before_canon_map_20260923",
                dtype=str, low_memory=False).fillna("")
b = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str, low_memory=False).fillna("")
print(f"rows: before {len(a)}  after {len(b)}")
print(f"columns only before: {sorted(set(a.columns) - set(b.columns))}")
print(f"columns only after : {sorted(set(b.columns) - set(a.columns))}")

a["_k"] = a.pn.map(n)
b["_k"] = b.pn.map(n)
a = a.set_index("_k").sort_index()
b = b.set_index("_k").sort_index()
print(f"same part numbers: {list(a.index) == list(b.index)}")
print()
for c in [c for c in a.columns if c in b.columns and c != "_k"]:
    same = bool(a[c].equals(b[c]))
    if not same:
        neq = int((a[c] != b[c]).sum())
        print(f"  {c:24s} DIFFERS on {neq} rows")
        for pn in a.index[a[c] != b[c]][:5]:
            print(f"      {pn}: before={a.loc[pn, c]!r}  after={b.loc[pn, c]!r}")
    else:
        print(f"  {c:24s} identical")
