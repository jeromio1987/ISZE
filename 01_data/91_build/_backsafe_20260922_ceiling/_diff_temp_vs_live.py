"""Compare the temp rebuild against the live file, cell by cell, and say what moved.

Read-only. Prints:
  - row/column identity
  - which cells differ, grouped by column, with a count per column
  - whether any change is outside the six markets the split correction reaches
  - whether the captured columns moved anywhere
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OLD = ROOT / "01_data/00_derived/wallet_waterfall.csv"
NEW = ROOT / "01_data/00_derived/wallet_waterfall.csv.tmp_ceiling_20260922"

SIX = {"PORTUGAL", "IRELAND", "GERMANY", "BELGIUM", "MALTA", "CYPRUS"}
CAPTURED = {
    "captured_genuine_eur", "captured_bvp_eur", "captured_total_eur",
    "over_target_eur", "uncaptured_eur", "addressable_uncaptured_eur",
    "structural_nonaddressable_eur", "gps_pct", "bvp_share_of_captured_pct",
    "theoretical_wallet_eur",
}


def main() -> int:
    old = pd.read_csv(OLD)
    new = pd.read_csv(NEW)
    cols = list(old.columns)
    print("columns identical:", cols == list(new.columns), f"({len(cols)})")

    ko = set(zip(old.year, old.distributor_code))
    kn = set(zip(new.year, new.distributor_code))
    print("row keys identical:", ko == kn)
    if ko != kn:
        print("  only old:", sorted(ko - kn))
        print("  only new:", sorted(kn - ko))

    o = old.set_index(["year", "distributor_code"]).sort_index()
    n = new.set_index(["year", "distributor_code"]).sort_index()

    print("\nrow ORDER differs:", not old.equals(new) and list(map(tuple, old[["year", "distributor_code"]].values)) !=
          list(map(tuple, new[["year", "distributor_code"]].values)))
    print("  (the builder sorts by year, then ceiling DESC, so order follows the values)")

    per_col: dict[str, int] = {}
    outside = []
    in_captured = []
    examples = {}
    for c in cols:
        if c in ("year", "distributor_code"):
            continue
        for key in o.index:
            a, b = o.at[key, c], n.at[key, c]
            same = (abs(float(a) - float(b)) <= 5e-7) if isinstance(a, float) and isinstance(b, float) \
                else (str(a) == str(b))
            if same:
                continue
            per_col[c] = per_col.get(c, 0) + 1
            tag = f"{key[0]} {key[1]}"
            examples.setdefault(c, []).append(f"{tag}: {a!r} -> {b!r}")
            if key[1] not in SIX:
                outside.append((c, tag, a, b))
            if c in CAPTURED - {"theoretical_wallet_eur"}:
                in_captured.append((c, tag, a, b))

    print("\ncells that moved, by column:")
    for c, cnt in sorted(per_col.items(), key=lambda kv: -kv[1]):
        print(f"  {c:32s} {cnt:>3} cells")
        for e in examples[c][:8]:
            print(f"        {e}")
        if len(examples[c]) > 8:
            print(f"        ... and {len(examples[c]) - 8} more")

    print(f"\nchanges OUTSIDE the six corrected markets: {len(outside)}")
    for x in outside[:20]:
        print("   ", x)
    print(f"changes in a captured/uncaptured column (billed book must not move): {len(in_captured)}")
    for x in in_captured[:20]:
        print("   ", x)

    print("\nper-year ceilings:")
    for y in sorted(old.year.unique()):
        a = old[old.year == y].theoretical_wallet_eur.sum()
        b = new[new.year == y].theoretical_wallet_eur.sum()
        ca = old[old.year == y].captured_total_eur.sum()
        cb = new[new.year == y].captured_total_eur.sum()
        print(f"  CY{y}  ceiling {a:>14,.2f} -> {b:>14,.2f} ({b-a:>+13,.2f})   "
              f"billed {ca:>14,.2f} -> {cb:>14,.2f} ({cb-ca:>+.2f})")

    print("\nsix-market ceilings, all years:")
    for y in sorted(old.year.unique()):
        for code in sorted(SIX):
            a = float(old[(old.year == y) & (old.distributor_code == code)].theoretical_wallet_eur.iloc[0])
            b = float(new[(new.year == y) & (new.distributor_code == code)].theoretical_wallet_eur.iloc[0])
            print(f"  CY{y} {code:9s} {a:>14,.2f} -> {b:>14,.2f}  {b-a:>+12,.2f}")

    print("\nUTI rows (must be identical):")
    for y in sorted(old.year.unique()):
        a = old[(old.year == y) & (old.distributor_code == "UTI")]
        b = new[(new.year == y) & (new.distributor_code == "UTI")]
        print(f"  CY{y} uio {int(a.uio_units.iloc[0])} -> {int(b.uio_units.iloc[0])}   "
              f"ceiling {float(a.theoretical_wallet_eur.iloc[0]):,.2f} -> {float(b.theoretical_wallet_eur.iloc[0]):,.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
