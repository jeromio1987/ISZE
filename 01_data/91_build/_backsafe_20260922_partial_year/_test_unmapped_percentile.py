"""Decisive test: do the four percentile ranks move when the UNMAPPED row is present?

Holds the current raw values constant and only toggles the UNMAPPED row, so the
difference is attributable to the row alone (not to the 21-Sep sales rebuild).
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
GPS = ROOT / "01_data/00_derived/gps_spu_by_distributor.csv"
NP = ROOT / "01_data/00_derived/network_percentile.csv"


def percentile_rank(values: pd.Series, invert: bool = False) -> pd.Series:
    n = values.notna().sum()
    if n <= 1:
        return pd.Series(50.0 if n == 1 else np.nan, index=values.index)
    ranked = values.rank(method="min", ascending=not invert)
    return (ranked - 1) / (n - 1) * 100.0


gps = pd.read_csv(GPS, dtype={"year": str})
base = gps[["year", "distributor_code", "spend_per_unit_eur"]].rename(
    columns={"spend_per_unit_eur": "raw_value"}
)

# The row as it stood in git HEAD, same shape.
unmapped = pd.DataFrame(
    [{"year": "2026", "distributor_code": "UNMAPPED", "raw_value": np.nan}]
)

# The row's real 2026 billed euro, for the record.
with GPS.open(encoding="utf-8-sig", newline="") as fh:
    cur_rows = list(csv.DictReader(fh))

results = {}
for label, frame in (
    ("WITHOUT row (current file)", base),
    ("WITH row (as HEAD)", pd.concat([base, unmapped], ignore_index=True)),
):
    for year, grp in frame.groupby("year", sort=True):
        g = grp.copy()
        g["network_median"] = g["raw_value"].median()
        g["n_distributors"] = g["raw_value"].notna().sum()
        g["percentile_rank"] = percentile_rank(g["raw_value"])
        if year == "2026":
            if label not in results:
                results[label] = {}
            for _, r in g.iterrows():
                results[label][r["distributor_code"]] = (
                    r["percentile_rank"], r["network_median"], r["n_distributors"]
                )

print("gps_spu / 2026 percentile rank, same raw values, UNMAPPED toggled:")
w = results["WITHOUT row (current file)"]
wo = results["WITH row (as HEAD)"]
codes = sorted(set(w) | set(wo))
moved = 0
for c in codes:
    a = wo.get(c, (None, None, None))[0]
    b = w.get(c, (None, None, None))[0]
    flag = ""
    if a is not None and b is not None and abs(float(a) - float(b)) > 1e-9:
        flag = "   <-- MOVES"
        moved += 1
    if a is None:
        a = "n/a (row absent)"
    print(f"  {c:12} with={a!s:22} without={b!s:22}{flag}")
print(f"\n  markets whose 2026 gps_spu percentile moves when the row is toggled: {moved}")
for label in results:
    med = results[label]["IUK"][1]
    n = results[label]["IUK"][2]
    print(f"  {label:30} median={med!r} n_distributors={n}")

# What the published file actually carries now.
np_df = pd.read_csv(NP, dtype={"year": str})
s26 = np_df[(np_df.metric == "gps_spu") & (np_df.year == "2026")]
print(f"\npublished network_percentile.csv gps_spu 2026: n={len(s26)} "
      f"median={s26.network_median.iloc[0]!r} n_distributors={s26.n_distributors.iloc[0]}")
for m in ("IUK", "HUNGARY", "GREECE", "ROMANIA"):
    print(f"  {m:8} published percentile={s26[s26.distributor_code == m].percentile_rank.iloc[0]!r}")
print(f"\nEUR on the dropped row: {sum(float(r['total_sales_eur'] or 0) for r in cur_rows if r['distributor_code']=='UNMAPPED')}")
