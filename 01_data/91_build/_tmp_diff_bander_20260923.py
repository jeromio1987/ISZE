"""Diff the re-run bander outputs against the pre-change snapshot.

The whole point of the map refactor is that NOTHING moves in the N-series numbers. This proves it
row by row rather than by eyeballing the printed totals.
"""
import json
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260923_canon_map"

FILES = ["series_to_tonnage.csv", "epc_decode_nseries_banded.csv",
         "nseries_tonnage_evolution.csv", "nseries_tonnage_evolution.meta.json"]

print("=" * 92)
print("PRE-CHANGE SNAPSHOT vs NOW")
print("=" * 92)
for f in FILES:
    a = (BAK / f).read_bytes()
    b = (DER / f).read_bytes()
    same = a == b
    print(f"  {f:42s} {'IDENTICAL' if same else 'DIFFERS'}   ({len(a):,} -> {len(b):,} bytes)")

print()
old = json.loads((BAK / "nseries_tonnage_evolution.meta.json").read_text(encoding="utf-8"))
new = json.loads((DER / "nseries_tonnage_evolution.meta.json").read_text(encoding="utf-8"))

print("N-series headline:")
print(f"  total EUR all years     {old['n_series_total_eur_all_years']:>16,.2f}  ->  "
      f"{new['n_series_total_eur_all_years']:>16,.2f}")
print(f"  shared across bands     {old['shared_across_bands_eur']:>16,.2f}  ->  "
      f"{new['shared_across_bands_eur']:>16,.2f}")
print(f"  unresolved              {old['series_unresolved_eur']:>16,.2f}  ->  "
      f"{new['series_unresolved_eur']:>16,.2f}")
print(f"  tie-out delta           {old['tie_out']['delta_eur']:>16,.2f}  ->  "
      f"{new['tie_out']['delta_eur']:>16,.2f}")
print()
print("per-band, exclusive versus shared:")
for b in ("3.5t_N35", "5.5t_N50_N55", "7.5t_N50_N62_N75"):
    o, n = old["band_split_single_versus_shared"][b], new["band_split_single_versus_shared"][b]
    flag = "" if (o["single_band_eur"] == n["single_band_eur"]
                  and o["single_band_pns"] == n["single_band_pns"]) else "   <-- MOVED"
    print(f"  {b:20s} single {o['single_band_pns']:3d} PNs EUR {o['single_band_eur']:>12,.2f}"
          f"  ->  {n['single_band_pns']:3d} PNs EUR {n['single_band_eur']:>12,.2f}{flag}")
print()
print("by_status:")
for k in old["by_status"]:
    o, n = old["by_status"][k], new["by_status"][k]
    flag = "" if o == n else "   <-- MOVED"
    print(f"  {k:22s} {o['part_numbers']:3d} PNs EUR {o['eur_all_years']:>12,.2f}"
          f"  ->  {n['part_numbers']:3d} PNs EUR {n['eur_all_years']:>12,.2f}{flag}")

print()
unchanged = (old["n_series_total_eur_all_years"] == new["n_series_total_eur_all_years"]
             and old["band_split_single_versus_shared"] == new["band_split_single_versus_shared"]
             and old["by_status"] == new["by_status"])
print(f"VERDICT: N-series figures {'UNCHANGED' if unchanged else 'CHANGED'}")
