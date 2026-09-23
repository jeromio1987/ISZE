"""Does the re-base move an NMR-bearing part number's band?

NMR is quarantined pending a ruling. The corrected table parks it (`parked_codes`), which keeps
NMR's interim 5.5 t out of the band list. That is not the same as reclassifying NMR, but it can
make a part number look single-band that the frozen file called shared. This counts that, so the
size of the effect is known rather than assumed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import (  # noqa: E402
    N_SERIES_BANDS, NOT_IN_SCOPE, UNRESOLVED, band_for, is_pending_ruling,
)

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
SHORT = {"3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t", "7.5t_N50_N62_N75": "7.5t"}


def main() -> int:
    ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    old = pd.read_csv(ROOT / "01_data" / "91_build" / "_legacy_baseline_tonnage_capable.csv",
                      dtype=str, low_memory=False).fillna("")
    leg = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    for d in (ap, old, leg):
        d["k"] = d.pn.map(n)

    scope = ap[ap.n_series_bands != ""].copy()
    scope["nb"] = scope.n_series_bands.str.count(r"\|") + 1
    print("=" * 96)
    print("A. THE RE-BASED SCOPE: part numbers fitting at least one N-series rung")
    print("=" * 96)
    print(f"  rows {len(scope):,}   single-band {int((scope.nb == 1).sum()):,}   "
          f"multi-band {int((scope.nb > 1).sum()):,}")

    parked = scope[scope.parked_codes != ""]
    print()
    print(f"  rows carrying a parked (NMR / NMR85) code: {len(parked):,}")
    print(f"      of those single-band: {int((parked.nb == 1).sum()):,}")
    print(f"      of those multi-band : {int((parked.nb > 1).sum()):,}")

    # what the band count would be if the parked code's interim band were counted as well
    def with_interim(row) -> int:
        bands = {b for b in str(row.n_series_bands).split("|") if b}
        for c in str(row.parked_codes).split(";"):
            c = c.strip()
            if not c:
                continue
            b = band_for(c)
            if b not in (UNRESOLVED, NOT_IN_SCOPE) and b in N_SERIES_BANDS:
                bands.add(b)
        return len(bands)

    parked = parked.copy()
    parked["nb_with_interim"] = parked.apply(with_interim, axis=1)
    flips = parked[(parked.nb == 1) & (parked.nb_with_interim > 1)]
    print()
    print("  part numbers that are single-band ONLY because the parked code was kept out:")
    print(f"      {len(flips):,}")
    for r in flips.head(25).itertuples():
        print(f"      {r.pn:>12s}  cat {str(r.pms_category):22s} kept {r.n_series_bands:26s}"
              f" parked {r.parked_codes:16s} would be {r.nb_with_interim}")
    if len(flips) > 25:
        print(f"      ... {len(flips) - 25:,} more")

    print()
    print("  do these flip a service family to placeable that would otherwise not be?")
    cats_scope = {c for c in scope[scope.nb == 1].pms_category if str(c).strip()}
    without = scope[~scope.k.isin(set(flips.k))]
    cats_without = {c for c in without[without.nb == 1].pms_category if str(c).strip()}
    gained = sorted(cats_scope - cats_without)
    print(f"      families placeable thanks only to the parked rows: {gained or 'none'}")

    print()
    print("=" * 96)
    print("B. THE 8 PART NUMBERS THE FROZEN FILE CARRIED THAT THE CORRECTED MAP GIVES NO TRUCK RUNG")
    print("=" * 96)
    dropped = old[~old.k.isin(set(scope.k))]
    for r in dropped.itertuples():
        row = ap[ap.k == r.k]
        groups = row.vehicle_groups.iloc[0] if len(row) else "(absent from the corrected table)"
        bands = row.vehicle_bands.iloc[0] if len(row) else "-"
        print(f"  {r.pn:>12s}  frozen n_bands {r.n_bands:>2s} bands {r.bands:12s}"
              f" | corrected groups {groups:24s} bands {bands}")

    print()
    print("=" * 96)
    print("C. NMR ITSELF - nothing in the mapping was touched")
    print("=" * 96)
    for code in ("NMR", "NMR85"):
        print(f"  {code:6s} band_for {band_for(code):20s} pending_ruling {is_pending_ruling(code)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
