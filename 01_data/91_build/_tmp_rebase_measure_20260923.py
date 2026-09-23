"""Measure the single-band claim before and after the re-base, from the page's own read.

Prints, for every file the page's tonnage logic touches:
  * how many part numbers the page sees
  * how many of those fit exactly one band (the page's SINGLE_BAND set)
  * the same figure broken out by service family, with the placeable verdict
plus a direct comparison of the frozen legacy columns against the corrected mapping.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260923_canon_map"
BASE = ROOT / "01_data" / "91_build" / "_legacy_baseline_tonnage_capable.csv"


def n(s) -> str:
    return str(s).strip().lstrip("0") or "0"


def page_view(path: Path, catcol: str = "category") -> dict:
    cap = pd.read_csv(path, dtype=str, low_memory=False).fillna("")
    cap["pnk"] = cap.pn.map(n)
    cap = cap.drop_duplicates("pnk")
    nbands = dict(zip(cap.pnk, cap.n_bands.astype(int)))
    single = {p for p, k in nbands.items() if k == 1}
    degree = {}
    for cat, g in cap.groupby(catcol):
        degree[cat] = {"pns": int(len(g)),
                       "single": int((g.n_bands.astype(int) == 1).sum()),
                       "multi": int((g.n_bands.astype(int) > 1).sum()),
                       "placeable": bool((g.n_bands.astype(int) == 1).any())}
    return {"path": path, "rows": len(cap), "nbands": nbands,
            "single": single, "degree": degree, "frame": cap}


def report(tag: str, v: dict) -> None:
    print("=" * 96)
    print(f"{tag}  ({v['path']})")
    print("=" * 96)
    print(f"  part numbers the page sees      : {v['rows']:,}")
    print(f"  SINGLE_BAND (fits exactly one)  : {len(v['single']):,}")
    placeable = sorted(c for c, d in v["degree"].items() if d["placeable"])
    print(f"  placeable service families      : {len(placeable)} of {len(v['degree'])}")
    for c in sorted(v["degree"], key=lambda x: (not v["degree"][x]["placeable"], x)):
        d = v["degree"][c]
        print(f"      {c:24s} pns {d['pns']:3d}  single {d['single']:3d}  multi {d['multi']:3d}"
              f"   placeable {d['placeable']}")
    print()


def main() -> int:
    frozen_bak = page_view(BAK / "tonnage_capable_part_numbers.csv")
    frozen_live = page_view(DER / "tonnage_capable_part_numbers.csv")
    frozen_base = page_view(BASE)
    corrected = page_view(DER / "vehicle_band_applicability.csv", catcol="pms_category")

    report("A. LEGACY FILE AS SHIPPED, BEFORE THE RE-BASE (live on disk)", frozen_live)
    report("B. LEGACY FILE'S PRECHANGE COPY (the backup of the same frozen values)", frozen_bak)
    report("C. THE FROZEN BASELINE THE BUILDER READS TO FREEZE FROM", frozen_base)
    report("D. THE CORRECTED MAPPING (vehicle_band_applicability.csv)", corrected)

    base_k = set(frozen_base["nbands"])
    app = corrected["frame"]
    app_in_base = app[app.pnk.isin(base_k)]
    print("=" * 96)
    print("THE QUESTION THE PAGE ASKS, ON THE CORRECTED MAPPING, RESTRICTED TO THE LEGACY ROWS")
    print("=" * 96)
    print(f"  baseline part numbers                                : {len(base_k):,}")
    print(f"  of those, present in the corrected table             : {len(app_in_base):,}")
    print(f"  fits exactly one band, corrected three-rung (n_bands): "
          f"{(app_in_base.n_bands.astype(int) == 1).sum():,}")
    print(f"  fits exactly one band, corrected ALL FOUR groups     : "
          f"{(app_in_base.band_count.astype(int) == 1).sum():,}")
    print(f"  exclusive_band stated, ALL FOUR groups               : "
          f"{(app_in_base.exclusive_band.fillna('') != '').sum():,}")
    print(f"  n_series_bands stated (a truck rung)                 : "
          f"{(app_in_base.n_series_bands.fillna('') != '').sum():,}")
    print()
    print("  first 20 part numbers that flip to single-band under the corrected map:")
    flips = app_in_base[app_in_base.n_bands.astype(int) == 1]
    for r in flips.head(20).itertuples():
        print(f"      {r.pn:>12s}  cat {str(r.pms_category):22s} bands {r.band_list:8s}"
              f"  groups {r.vehicle_groups}")
    print(f"  ... {max(0, len(flips) - 20):,} more")

    moved = {p: (frozen_base["nbands"].get(p), corrected["nbands"].get(p))
             for p in set(frozen_base["nbands"]) | set(corrected["nbands"])
             if frozen_base["nbands"].get(p) != corrected["nbands"].get(p)
             and p in base_k}
    print()
    print(f"  baseline part numbers whose three-rung band count changes: {len(moved):,}")
    up = sum(1 for a, b in moved.values() if (b or 0) > (a or 0))
    down = sum(1 for a, b in moved.values() if (b or 0) < (a or 0))
    print(f"      becomes single-band: {up:,}   becomes multi-band: {down:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
