"""Reconciliation after the scoped apply - corrected partition.

Part A: the N-series band file, using ITS OWN tie-out fields rather than a recomputation.
Part B: the applicability table, partitioned so the three buckets cover every row exactly once.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260923_canon_map"


def n(s):
    return str(s).strip().lstrip("0") or "0"


print("=" * 98)
print("PART A - N-SERIES BAND FILE   (18 book markets, billing 2023-01 to 2026-08)")
print("=" * 98)
print("  basis: the file's own scope rule - only rows flagged in_n_series_family = 'yes'")
print("         enter the three bands; the shared pool and the unresolved group sit beside them.")
print()
old = json.loads((BAK / "nseries_tonnage_evolution.meta.json").read_text(encoding="utf-8"))
new = json.loads((DER / "nseries_tonnage_evolution.meta.json").read_text(encoding="utf-8"))
ob, nb = old["band_split_single_versus_shared"], new["band_split_single_versus_shared"]

print(f"  {'line':36s} {'before':>16s} {'after':>16s}  moved")
lines = [
    ("N-series billed EUR total", old["n_series_total_eur_all_years"],
     new["n_series_total_eur_all_years"]),
    ("exclusive 3.5 t", ob["3.5t_N35"]["single_band_eur"], nb["3.5t_N35"]["single_band_eur"]),
    ("exclusive 5.5 t", ob["5.5t_N50_N55"]["single_band_eur"], nb["5.5t_N50_N55"]["single_band_eur"]),
    ("exclusive 7.5 t", ob["7.5t_N50_N62_N75"]["single_band_eur"],
     nb["7.5t_N50_N62_N75"]["single_band_eur"]),
    ("shared across N-series bands", old["shared_across_bands_eur"], new["shared_across_bands_eur"]),
    ("unresolved (series not stated)", old["series_unresolved_eur"], new["series_unresolved_eur"]),
    ("no series found", old["by_status"]["no_series_found"]["eur_all_years"],
     new["by_status"]["no_series_found"]["eur_all_years"]),
]
for label, a, b in lines:
    print(f"  {label:36s} {a:16,.2f} {b:16,.2f}  {'no' if a == b else 'YES'}")

eo = sum(ob[k]["single_band_eur"] for k in ("3.5t_N35", "5.5t_N50_N55", "7.5t_N50_N62_N75"))
en = sum(nb[k]["single_band_eur"] for k in ("3.5t_N35", "5.5t_N50_N55", "7.5t_N50_N62_N75"))
to, tn = old["n_series_total_eur_all_years"], new["n_series_total_eur_all_years"]
print()
print(f"  exclusive-attribution share          {eo / to * 100:15.4f}% {en / tn * 100:15.4f}%  "
      f"{'no' if abs(eo / to - en / tn) < 1e-12 else 'YES'}")
print(f"    = exclusive EUR {en:,.2f} of N-series EUR {tn:,.2f}")

print()
print("  the file's OWN tie-out fields (read, not recomputed):")
print(f"    bands_plus_shared_plus_unresolved_eur  "
      f"before {old['tie_out']['bands_plus_shared_plus_unresolved_eur']:,.2f}   "
      f"after {new['tie_out']['bands_plus_shared_plus_unresolved_eur']:,.2f}")
print(f"    tagged_n_series_billing_eur            "
      f"before {old['tie_out']['tagged_n_series_billing_eur']:,.2f}   "
      f"after {new['tie_out']['tagged_n_series_billing_eur']:,.2f}")
print(f"    delta_eur                              "
      f"before {old['tie_out']['delta_eur']:,.2f}   after {new['tie_out']['delta_eur']:,.2f}")

banded = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str, low_memory=False).fillna("")
banded["_k"] = banded.pn.map(n)
print()
print(f"  banded file: {len(banded):,} rows / {banded._k.nunique():,} distinct part numbers "
      f"(duplicates {len(banded) - banded._k.nunique()}); "
      f"{int((banded.in_n_series_family == 'yes').sum())} in band scope")

print()
print("=" * 98)
print("PART B - VEHICLE-BAND APPLICABILITY   (all markets, all years, from sales_fact)")
print("=" * 98)
ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
ap["_k"] = ap.pn.map(n)
ap["bc"] = ap.band_count.astype(int)
ap["eur_f"] = pd.to_numeric(ap.eur, errors="coerce").fillna(0.0)
print(f"  rows {len(ap):,}   distinct part numbers {ap._k.nunique():,}   "
      f"duplicates {len(ap) - ap._k.nunique()}")
print()

print("  exclusive to exactly one vehicle band:")
for band, label in [("LCV_D-Max", "LCV / D-Max (D-Max pickup and SUV)"),
                    ("3.5t_N35", "3.5 t (N35 Grafter)"),
                    ("5.5t_N50_N55", "5.5 t (N50 / N55)"),
                    ("7.5t_N50_N62_N75", "7.5 t (N75 / N50 / N62)"),
                    ("F_series_MD_heavy", "F-series / MD (heavy)")]:
    sel = ap[ap.exclusive_band == band]
    print(f"    {label:40s} {len(sel):5,d} PNs   EUR {sel.eur_f.sum():>16,.2f}")
excl = ap[ap.exclusive_band != ""]
print(f"    {'EXCLUSIVE TOTAL':40s} {len(excl):5,d} PNs   EUR {excl.eur_f.sum():>16,.2f}")

print()
pooled = ap[(ap.bc >= 1) & (ap.exclusive_band == "")]
print(f"  fits more than one band, plus the parked rows (pooled, never apportioned):")
print(f"    {len(pooled):5,d} PNs   EUR {pooled.eur_f.sum():>16,.2f}")
parked = pooled[pooled.parked_codes != ""]
print(f"      of which held pending the NMR ruling: {len(parked)} PNs   "
      f"EUR {parked.eur_f.sum():,.2f}")

none = ap[ap.bc == 0]
print()
print(f"  no band from any source:")
print(f"    {len(none):5,d} PNs   EUR {none.eur_f.sum():>16,.2f}")
wonly = none[none.wildcards_named != ""]
print(f"      wildcard-only evidence: {len(wonly)} PNs   EUR {wonly.eur_f.sum():,.2f} "
      f"(recorded, never converted into a band)")
noev = none[none.wildcards_named == ""]
print(f"      no vehicle named at all: {len(noev)} PNs   EUR {noev.eur_f.sum():,.2f}")

print()
print("  DOUBLE-COUNT PROOF (part B) - the three buckets must cover every row exactly once:")
total = ap.eur_f.sum()
print(f"    exclusive          {excl.eur_f.sum():>16,.2f}  ({len(excl):,} rows)")
print(f"    pooled / parked    {pooled.eur_f.sum():>16,.2f}  ({len(pooled):,} rows)")
print(f"    no band            {none.eur_f.sum():>16,.2f}  ({len(none):,} rows)")
print(f"    ----------------------------------------------------")
print(f"    sum                {excl.eur_f.sum() + pooled.eur_f.sum() + none.eur_f.sum():>16,.2f}  "
      f"({len(excl) + len(pooled) + len(none):,} rows)")
print(f"    table total        {total:>16,.2f}  ({len(ap):,} rows)")
diff = abs((excl.eur_f.sum() + pooled.eur_f.sum() + none.eur_f.sum()) - total)
rows_covered = len(excl) + len(pooled) + len(none)
print(f"    difference         {diff:>16,.2f}   rows covered {rows_covered:,} of {len(ap):,}")
print(f"    -> {'every euro and every row counted exactly once' if diff < 0.01 and rows_covered == len(ap) else 'MISMATCH'}")

print()
print("  a part number appears once, so joining on it cannot double-count:")
print(f"    distinct part numbers {ap._k.nunique():,} = rows {len(ap):,}: "
      f"{ap._k.nunique() == len(ap)}")
