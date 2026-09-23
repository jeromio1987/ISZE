"""Check the applicability table against the brief item by item.

1. the six NMR-dependent shared brake rotors are quarantined (no band written)
2. the three evidenced LCV brake rotors land on LCV / D-Max, not on a truck rung
3. the F-series clutch booster / pilot bearing rows land on the heavy group
4. wildcards never produce a band
5. no part number appears twice (so nothing can be double-counted by joining on pn)
"""
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"


def n(s):
    return str(s).strip().lstrip("0") or "0"


ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
ap["_k"] = ap.pn.map(n)

print("=" * 96)
print("1. THE SIX NMR-DEPENDENT SHARED BRAKE ROTORS")
print("=" * 96)
nmr_six = ["8982488951", "8983034670", "8982488930", "8983034680", "8982488970", "8981710330"]
for p in nmr_six:
    r = ap[ap._k == n(p)]
    if r.empty:
        print(f"  {p}  ABSENT from the applicability table")
        continue
    r = r.iloc[0]
    print(f"  {p}  bands={r.vehicle_bands or '(none)':22s} status={r.band_status:16s} "
          f"parked={r.parked_codes or '-':8s} EUR {float(r.eur):>12,.0f}")

print()
print("=" * 96)
print("2. THE THREE EVIDENCED LCV BRAKE ROTORS")
print("=" * 96)
lcv = ["8983767550", "8979488071", "8983767530"]
for p in lcv:
    r = ap[ap._k == n(p)]
    if r.empty:
        print(f"  {p}  ABSENT")
        continue
    r = r.iloc[0]
    print(f"  {p}  groups={r.vehicle_groups:14s} bands={r.vehicle_bands:12s} "
          f"n_series_bands={r.n_series_bands or '(none)':10s} EUR {float(r.eur):>12,.0f}")

print()
print("=" * 96)
print("3. THE EVIDENCED F-SERIES CLUTCH / PILOT ROWS")
print("=" * 96)
fs = ["1876101590", "1876100890", "1318005162", "1318005113", "1318005124", "1318005252",
      "1098002571", "1876101581"]
for p in fs:
    r = ap[ap._k == n(p)]
    if r.empty:
        print(f"  {p}  ABSENT")
        continue
    r = r.iloc[0]
    print(f"  {p}  groups={r.vehicle_groups:14s} bands={r.vehicle_bands:18s} "
          f"n_series={r.n_series_bands or '(none)':10s} EUR {float(r.eur):>10,.0f}")

print()
print("=" * 96)
print("4. WILDCARDS NEVER PRODUCE A BAND")
print("=" * 96)
w = ap[(ap.wildcards_named != "")]
print(f"  part numbers with a wildcard named          : {len(w):,}")
print(f"  of those, band read from a wildcard alone   : "
      f"{int(((w.band_count == '0') & (w.codes_named != '')).sum()):,} "
      f"(must be 0 with no real code)")
print(f"  any band on a wildcard-only row             : "
      f"{int(((w.codes_named == '') & (w.band_count != '0')).sum())}  (must be 0)")

print()
print("=" * 96)
print("5. NO DUPLICATE PART NUMBERS, NO 5.5 t BAND IN CIRCULATION")
print("=" * 96)
print(f"  rows                        : {len(ap):,}")
print(f"  distinct part numbers       : {ap._k.nunique():,}")
print(f"  duplicates                  : {len(ap) - ap._k.nunique()}")
print(f"  rows carrying a 5.5 t band  : {int(ap.vehicle_bands.str.contains('5.5t').sum())} (must be 0 while NMR is parked)")
print(f"  rows with a parked code     : {int((ap.parked_codes != '').sum())}")
