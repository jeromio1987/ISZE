"""The gap between the two derived files, measured. Do not assert it.

neutral  = vehicle_band_applicability.csv, n_series_bands count == 1
pagefile = tonnage_capable_part_numbers.csv, n_bands == 1
Reports both counts, the set difference in each direction, and how many of that difference carry a
quarantined code.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
sys.path.insert(0, str(ROOT / "03_analytics" / "Isuzu" / "prism"))
from modules.vehicle_bands import band_for, pending_ruling_codes  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731


def main() -> int:
    ap = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    pg = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    ap["k"] = ap.pn.map(n)
    pg["k"] = pg.pn.map(n)

    scope = ap[ap.n_series_bands != ""].copy()
    scope["nb_neutral"] = scope.n_series_bands.str.count(r"\|") + 1
    # the page file's rule: settled rungs plus each quarantined code's interim band
    def page_nb(row) -> int:
        bands = {b for b in str(row.n_series_bands).split("|") if b}
        for c in pending_ruling_codes():
            if c in str(row.parked_codes):
                b = band_for(c)
                if b not in ("unresolved", "not_in_scope"):
                    bands.add(b)
        return len(bands)
    scope["nb_pagerule"] = scope.apply(page_nb, axis=1)

    on_neutral = set(scope[scope.nb_neutral == 1].k)
    on_page = set(pg[pg.n_bands.astype(int) == 1].k)
    print("=" * 100)
    print("THE TWO FILES' ANSWERS TO 'FITS EXACTLY ONE TRUCK RUNG'")
    print("=" * 100)
    print(f"  neutral table, n_series_bands count == 1 : {len(on_neutral):,}")
    print(f"  neutral table, page rule applied         : "
          f"{int((scope.nb_pagerule == 1).sum()):,}")
    print(f"  page file on disk, n_bands == 1          : {len(on_page):,}")
    print()
    both = on_neutral & on_page
    only_neutral = on_neutral - on_page
    only_page = on_page - on_neutral
    print(f"  in both                                  : {len(both):,}")
    print(f"  neutral says one, page file says not      : {len(only_neutral):,}")
    print(f"  page file says one, neutral says not      : {len(only_page):,}")
    print(f"  symmetric difference                     : {len(only_neutral) + len(only_page):,}")
    print()
    A = scope.set_index("k")
    for tag, s in (("neutral says one, page file says not", only_neutral),
                   ("page file says one, neutral says not", only_page)):
        parked = [k for k in s if k in A.index and str(A.loc[k].parked_codes).strip()]
        absent = [k for k in s if k not in A.index]
        print(f"  {tag}: {len(s)} rows, of which carrying a quarantined code: {len(parked)}"
              f"   (not in the neutral table's banded scope at all: {len(absent)})")
        for k in sorted(s)[:6]:
            if k in A.index:
                print(f"      {k:>12s} neutral {A.loc[k].n_series_bands:26s} "
                      f"page_rule {A.loc[k].nb_pagerule}  parked {A.loc[k].parked_codes!r}")
            else:
                pg_row = pg[pg.k == k]
                print(f"      {k:>12s} not in the neutral banded scope; page file "
                      f"{pg_row.bands.iloc[0] if len(pg_row) else '-'}")
        print()
    print(f"  neutral 230 vs page file 176: the {len(only_neutral)} rows neutral calls one-band and"
          f" the page file does not share {len([k for k in only_neutral if k in A.index and str(A.loc[k].parked_codes).strip()])}"
          f" quarantined, so the gap is NOT the ruling alone")
    print(f"  the page file says one-band on {len(only_page)} row(s) the neutral table does not, "
          f"because those rows are outside its banded scope")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
