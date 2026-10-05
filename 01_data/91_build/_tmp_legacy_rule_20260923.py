"""How far does the family-evolution page move under each possible legacy-file rule?

The page reads `tonnage_capable_part_numbers.csv` for: how many bands a part number fits,
which part numbers fit exactly one band, and per PMS category whether any part number fits one
band only. Any of those moving changes what the page tells a reader, so the legacy file's rule
has to be chosen with the size of that move known.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260923_canon_map"


def n(s):
    return str(s).strip().lstrip("0") or "0"


def view(cap: pd.DataFrame) -> dict:
    cap = cap.copy()
    cap["pnk"] = cap.pn.map(n)
    cap = cap.drop_duplicates("pnk")
    cap["nb"] = cap.n_bands.astype(int)
    single = set(cap.pnk[cap.nb == 1])
    degree = {}
    for cat, g in cap.groupby("category"):
        if not str(cat).strip():
            continue
        degree[cat] = {"pns": int(len(g)), "single": int((g.nb == 1).sum()),
                       "placeable": bool((g.nb == 1).any())}
    return {"rows": len(cap), "single": single, "degree": degree,
            "nbands": dict(zip(cap.pnk, cap.nb))}


old = pd.read_csv(BAK / "tonnage_capable_part_numbers.csv", dtype=str).fillna("")
ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str).fillna("")

# ── candidate rule: legacy = part numbers that fit at least one N-series rung
cand = ap[ap.n_series_bands != ""].copy()
cand["n_bands"] = cand.n_series_bands.str.count(r"\|") + 1
cand["category"] = cand.pms_category

o, c = view(old), view(cand)
print("=" * 96)
print("LEGACY RULE: part numbers fitting at least one N-series rung")
print("=" * 96)
print(f"  rows                    : {o['rows']:,}  ->  {c['rows']:,}")
print(f"  SINGLE_BAND             : {len(o['single']):,}  ->  {len(c['single']):,}")
moved = [p for p in set(o["nbands"]) & set(c["nbands"]) if o["nbands"][p] != c["nbands"][p]]
print(f"  shared part numbers whose band count moved: {len(moved):,}")
print(f"  part numbers only in the new file          : {len(set(c['nbands']) - set(o['nbands'])):,}")
print(f"  part numbers only in the old file          : {len(set(o['nbands']) - set(c['nbands'])):,}")
flip = [(k, o["degree"].get(k, {}).get("placeable"), c["degree"].get(k, {}).get("placeable"))
        for k in sorted(set(o["degree"]) | set(c["degree"]))
        if o["degree"].get(k, {}).get("placeable") != c["degree"].get(k, {}).get("placeable")]
print(f"  categories whose 'placeable' flips         : {len(flip)}")
for k, a, b in flip:
    print(f"      {k:24s} {a} -> {b}")
