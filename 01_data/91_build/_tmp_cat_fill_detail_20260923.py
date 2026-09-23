"""Which rows gained a category tag, and what that does to the page's per-category verdict."""
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260923_canon_map"


def n(s):
    return str(s).strip().lstrip("0") or "0"


old = pd.read_csv(BAK / "tonnage_capable_part_numbers.csv", dtype=str).fillna("")
new = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str).fillna("")
for df in (old, new):
    df["_k"] = df.pn.map(n)
o = old.set_index("_k").sort_index()
w = new.set_index("_k").sort_index()

print("rows that gained a category:")
gained = w.index[(o.category.astype(str).str.strip() == "")
                 & (w.category.astype(str).str.strip() != "")]
print(f"  count: {len(gained)}")
for pn in gained:
    print(f"  {pn}  category={w.loc[pn, 'category']:16s} n_bands={w.loc[pn, 'n_bands']:>2s} "
          f"band_list={w.loc[pn, 'band_list']}")

print()
print("per-category single-band counts (the page's 'placeable' input):")
for cat in sorted({c for c in list(o.category) + list(w.category) if str(c).strip()}):
    a = o[o.category == cat]
    b = w[w.category == cat]
    a1 = int((a.n_bands.astype(int) == 1).sum()) if len(a) else 0
    b1 = int((b.n_bands.astype(int) == 1).sum()) if len(b) else 0
    flag = "   <-- FLIPS" if (a1 == 0) != (b1 == 0) else ""
    print(f"  {cat:24s} PNs {len(a):3d}->{len(b):3d}   single-band {a1:3d}->{b1:3d}{flag}")
