"""Reproducible evidence for the re-base: the single-band count before and after.

Kept as the one standing measurement script for the 2026-09-23 re-base. It answers, from the files
on disk, the question the ruling settled:

    how many part numbers fit exactly one truck tonnage rung, and did that change?

and reports the same figure on the four-group basis beside it, so the narrower question the page
uses and the neutral table's wider one cannot be confused for each other.

The rule it applies is the ruled one: a quarantined code contributes its interim band. It also
prints what the count would be under the rejected rule (`parked OUT`) so the 180 and the wrong 230
are both visible in one run and neither can be quoted without the other.

Run:
    python 01_data/91_build/measure_legacy_rebase_20260923.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
BAK = ROOT / "02_dashboards" / "sales" / "_backsafe_rebase_20260923"
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import (  # noqa: E402
    N_SERIES_BANDS, NOT_IN_SCOPE, UNRESOLVED, band_for,
)

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
SHORT = {"3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t", "7.5t_N50_N62_N75": "7.5t"}


def rungs(row, parked_counts: bool) -> list[str]:
    out = {b for b in str(row.n_series_bands).split("|") if b}
    if parked_counts:
        for c in str(row.parked_codes).split(";"):
            c = c.strip()
            if not c:
                continue
            b = band_for(c)
            if b not in (UNRESOLVED, NOT_IN_SCOPE) and b in N_SERIES_BANDS:
                out.add(b)
    return sorted(out)


def main() -> int:
    app = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    now = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    bak = pd.read_csv(BAK / "tonnage_capable_part_numbers.csv.bak_pre_rebase",
                      dtype=str, low_memory=False).fillna("")

    print("=" * 100)
    print("FAMILY-EVOLUTION RE-BASE, 2026-09-23 - single-band part numbers")
    print("=" * 100)
    print(f"  the file the page reads : 01_data/00_derived/tonnage_capable_part_numbers.csv")
    print(f"  before (frozen backup)  : {len(bak):,} rows, "
          f"{int((bak.n_bands.astype(int) == 1).sum())} fit exactly one rung")
    print(f"  after  (on disk now)    : {len(now):,} rows, "
          f"{int((now.n_bands.astype(int) == 1).sum())} fit exactly one rung")
    print()
    print("  columns unchanged: "
          f"{list(bak.columns) == list(now.columns)}  ({len(now.columns)} columns, same order)")
    print()
    print("  the same question recomputed from the corrected mapping, so the count is not taken "
          "on trust:")
    for tag, parked in (("a quarantined code contributes its interim band  <-- RULED", True),
                        ("a quarantined code contributes nothing              (REJECTED)", False)):
        sel = app[(app.n_series_bands != "") | (app.parked_codes != "")].copy()
        sel["nb"] = [len(rungs(r, parked)) for r in sel.itertuples()]
        print(f"      {tag:62s} {int((sel.nb == 1).sum()):4d}")
    four = app[(app.n_series_bands != "") | (app.parked_codes != "")]
    print(f"      four-group basis (band_count == 1) on the same rows"
          f"                     {int((four.band_count.astype(int) == 1).sum()):4d}")
    print()
    print("  by service family, on the ruled rule, three-rung basis:")
    sel = app[(app.n_series_bands != "") | (app.parked_codes != "")].copy()
    sel["nb"] = [len(rungs(r, True)) for r in sel.itertuples()]
    sel["cat"] = sel.pms_category.replace("", "(untagged)")
    for cat, g in sorted(sel.groupby("cat"), key=lambda kv: -int((kv[1].nb == 1).sum())):
        print(f"      {cat:24s} rows {len(g):4d}  single {int((g.nb == 1).sum()):4d}"
              f"  multi {int((g.nb > 1).sum()):4d}  placeable {bool((g.nb == 1).any())}")
    print()
    print("  the three families the ruling named:")
    for cat in ("air_filter", "brake_rotor", "brake_shoe"):
        a = bak[bak.category == cat]
        b = now[now.category == cat]
        print(f"      {cat:14s} before single {int((a.n_bands.astype(int) == 1).sum()):3d} of "
              f"{len(a):3d}  ->  after single {int((b.n_bands.astype(int) == 1).sum()):3d} of "
              f"{len(b):3d}  placeable {bool((b.n_bands.astype(int) == 1).any())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
