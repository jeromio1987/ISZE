"""Does the family-evolution page's own read of the legacy candidate table still behave?

The page (`02_dashboards/sales/_build/build_family_evolution_v2.py`) reads
`tonnage_capable_part_numbers.csv` for three things:
  PN_NBANDS  - how many bands a part number fits
  SINGLE_BAND - the set with exactly one band ("fits one band only")
  degree[cat] - per PMS category: how many part numbers, how many single-band, placeable?

This re-runs that logic on the pre-change file and the new one and compares the outcomes, so a
silent change to what the page concludes cannot hide behind a schema description.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260923_canon_map"


def n(s):
    return str(s).strip().lstrip("0") or "0"


def page_view(path: Path) -> dict:
    cap = pd.read_csv(path, dtype=str).fillna("")
    cap["pnk"] = cap.pn.map(n)
    cap = cap.drop_duplicates("pnk")
    pn_nbands = dict(zip(cap.pnk, cap.n_bands.astype(int)))
    single = {p for p, k in pn_nbands.items() if k == 1}
    degree = {}
    for cat, g in cap.groupby("category"):
        degree[cat] = {"pns": int(len(g)),
                       "singleBand": int((g.n_bands.astype(int) == 1).sum()),
                       "multiBand": int((g.n_bands.astype(int) > 1).sum()),
                       "placeable": bool((g.n_bands.astype(int) == 1).any())}
    return {"pn_nbands": pn_nbands, "single": single, "degree": degree}


old = page_view(BAK / "tonnage_capable_part_numbers.csv")
new = page_view(DER / "tonnage_capable_part_numbers.csv")

print("=" * 96)
print("THE PAGE'S OWN READ, BEFORE vs AFTER")
print("=" * 96)
print(f"  rows the page sees      : {len(old['pn_nbands']):,}  ->  {len(new['pn_nbands']):,}")
print(f"  SINGLE_BAND (fits one)  : {len(old['single']):,}  ->  {len(new['single']):,}")

# does any part number change how many bands it fits?
moved = {p: (old["pn_nbands"].get(p), new["pn_nbands"].get(p))
         for p in set(old["pn_nbands"]) | set(new["pn_nbands"])
         if old["pn_nbands"].get(p) != new["pn_nbands"].get(p)}
print(f"  part numbers whose band count moved: {len(moved):,}")
for p, (a, b) in list(moved.items())[:12]:
    print(f"      {p}: {a} -> {b}")

print()
print("  per-category verdict inputs (a category can only change if placeable flips):")
flips = []
for cat in sorted(set(old["degree"]) | set(new["degree"])):
    a = old["degree"].get(cat, {})
    b = new["degree"].get(cat, {})
    if a.get("placeable") != b.get("placeable"):
        flips.append((cat, a, b))
if flips:
    for cat, a, b in flips:
        print(f"      {cat:24s} placeable {a.get('placeable')} -> {b.get('placeable')}")
else:
    print("      no category flips placeable")
print()
print(f"  VERDICT: page inputs {'UNCHANGED' if not moved and not flips else 'CHANGED'}")
