"""Does the canonical map reproduce the family builder's own code->family dictionary?

If yes, the family builder can read the canonical map and its output cannot move. If no, the
differences are listed so they can be judged rather than silently absorbed.
"""
import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"

spec = importlib.util.spec_from_file_location(
    "bvfb", PRISM / "scripts" / "build_vehicle_family_bands.py")
m = importlib.util.module_from_spec(spec)
sys.modules["bvfb"] = m
spec.loader.exec_module(m)

with open(PRISM / "data" / "series_to_band.csv", encoding="utf-8-sig", newline="") as fh:
    can = {r["code"]: r["vehicle_group"] for r in csv.DictReader(fh)}

print(f"family CONCRETE codes : {len(m.CONCRETE)}")
print(f"canonical map codes   : {len(can)}")
print()
missing = sorted(set(m.CONCRETE) - set(can))
print(f"in the family dict but NOT in the canonical map ({len(missing)}): {missing}")
print()
mismatch = {c: (m.CONCRETE[c], can[c]) for c in sorted(set(m.CONCRETE) & set(can))
            if m.CONCRETE[c] != can[c]}
print(f"same code, different family ({len(mismatch)}):")
for c, (a, b) in mismatch.items():
    print(f"  {c:8s} family-dict={a:16s} canonical={b}")
print()
n_series_only = sorted(c for c, g in can.items() if g == "n_series_truck")
print(f"canonical n_series_truck codes ({len(n_series_only)}): {n_series_only}")
fam_ns = sorted(c for c, g in m.CONCRETE.items() if g == m.N_SERIES)
print(f"family-dict n_series_truck codes ({len(fam_ns)}): {fam_ns}")
print()
print(f"n_series sets equal: {set(n_series_only) == set(fam_ns)}")
print(f"  only canonical: {sorted(set(n_series_only) - set(fam_ns))}")
print(f"  only family   : {sorted(set(fam_ns) - set(n_series_only))}")
