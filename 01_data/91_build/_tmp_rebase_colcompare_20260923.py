"""Compare the frozen legacy file's non-band columns with the corrected table, on the overlap.

The re-base rewrites the legacy file's three-rung columns from the corrected mapping. Every other
column has to keep the value the page already had, so this lists every row where `category` or
`eur` would differ - a category change would move the page's per-family grouping, so it must be
known before the write, not after.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BASE = ROOT / "01_data" / "91_build" / "_legacy_baseline_tonnage_capable.csv"
n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731


def main() -> int:
    base = pd.read_csv(BASE, dtype=str, low_memory=False).fillna("")
    live = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    for d in (base, live, ap):
        d["k"] = d.pn.map(n)

    j = base.merge(ap, on="k", suffixes=("_base", "_ap"), how="left")
    print(f"baseline rows {len(base):,}   live rows {len(live):,}   corrected rows {len(ap):,}")
    print(f"baseline part numbers absent from the corrected table: "
          f"{int(j.pms_category.isna().sum())}")
    print()

    catdiff = j[(j.category != j.pms_category)]
    print(f"rows where baseline `category` differs from corrected `pms_category`: {len(catdiff):,}")
    for r in catdiff.head(40).itertuples():
        print(f"   {r.pn:>12s}  baseline {r.category!r:24s} corrected {r.pms_category!r}")
    print()

    ed = j[(pd.to_numeric(j.eur_base, errors="coerce").fillna(0).round(2)
            - pd.to_numeric(j.eur_ap, errors="coerce").fillna(0).round(2)).abs() > 0.005]
    print(f"rows where baseline `eur` differs from corrected `eur`: {len(ed):,}")
    for r in ed.head(20).itertuples():
        print(f"   {r.pn:>12s}  baseline {r.eur_base:>14s}  corrected {r.eur_ap:>14s}")
    print()

    lj = live.merge(ap, on="k", suffixes=("_live", "_ap"), how="left")
    lc = lj[lj.category != lj.pms_category]
    print(f"rows where the LIVE legacy `category` differs from corrected: {len(lc):,}")
    for r in lc.head(40).itertuples():
        print(f"   {r.pn:>12s}  live {r.category!r:24s} corrected {r.pms_category!r}")

    catcols = ["clutch_kit", "oil_filter", "fuel_filter", "brake_shoe", "brake_rotor", "air_filter",
               "clutch_disc", "brake_pad", "release_bearing", "clutch_pressure_plate"]
    print()
    print("baseline rows with an empty category:", int((base.category == "").sum()))
    print("of those, how many the corrected table names:",
          int((j[j.category == ""].pms_category != "").sum()))
    print("baseline rows in the page's ten named families:",
          int(base.category.isin(catcols).sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
