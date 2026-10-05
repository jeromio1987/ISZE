"""Was the percentile change driven by the dropped row, or by the 21-Sep sales rebuild?

Reconstruct the published percentile from each vintage of gps_spu_by_distributor.csv
using the builder's own formula, and compare.
"""
from __future__ import annotations

import io
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")


def pct(values: pd.Series) -> pd.Series:
    n = values.notna().sum()
    if n <= 1:
        return pd.Series(50.0 if n == 1 else np.nan, index=values.index)
    ranked = values.rank(method="min", ascending=True)
    return (ranked - 1) / (n - 1) * 100.0


def rebuild_from(csv_text: str) -> pd.DataFrame:
    gps = pd.read_csv(io.StringIO(csv_text), dtype={"year": str})
    base = gps[["year", "distributor_code", "spend_per_unit_eur"]].rename(
        columns={"spend_per_unit_eur": "raw_value"}
    )
    out = []
    for year, grp in base.groupby("year", sort=True):
        g = grp.copy()
        g["network_median"] = g["raw_value"].median()
        g["n_distributors"] = g["raw_value"].notna().sum()
        g["percentile_rank"] = pct(g["raw_value"])
        out.append(g)
    return pd.concat(out, ignore_index=True)


committed_gps = subprocess.run(
    ["git", "show", "HEAD:01_data/00_derived/gps_spu_by_distributor.csv"],
    cwd=ROOT, capture_output=True, check=True,
).stdout.decode("utf-8-sig")
current_gps = (ROOT / "01_data/00_derived/gps_spu_by_distributor.csv").read_text(
    encoding="utf-8-sig"
)
committed_np = pd.read_csv(
    io.StringIO(
        subprocess.run(
            ["git", "show", "HEAD:01_data/00_derived/network_percentile.csv"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout.decode("utf-8-sig")
    ),
    dtype={"year": str},
)
current_np = pd.read_csv(ROOT / "01_data/00_derived/network_percentile.csv", dtype={"year": str})

for year in ("2025", "2026"):
    print("=" * 88)
    print(f"gps_spu {year}")
    for code in ("IUK", "HUNGARY", "GREECE", "ROMANIA", "UNMAPPED"):
        row = {}
        for lbl, df in (("committed_np", committed_np), ("current_np", current_np)):
            s = df[(df.metric == "gps_spu") & (df.year == year) & (df.distributor_code == code)]
            row[lbl] = (None if s.empty else s.iloc[0]["percentile_rank"])
        print(f"  {code:9} published_HEAD={row['committed_np']!s:22} published_NOW={row['current_np']!s:22}")

print("=" * 88)
print("Rebuild percentile from each GPS vintage, to attribute the change:")
for lbl, txt in (("HEAD gps file", committed_gps), ("current gps file", current_gps)):
    r = rebuild_from(txt)
    s = r[(r.year == "2026")]
    print(f"  {lbl}: rows={len(s)} n_distributors={s.n_distributors.iloc[0]} median={s.network_median.iloc[0]}")
    for code in ("IUK", "HUNGARY", "GREECE", "ROMANIA", "UNMAPPED"):
        v = s[s.distributor_code == code]
        if v.empty:
            print(f"     {code:9} absent")
        else:
            print(f"     {code:9} raw={v.raw_value.iloc[0]!r:22} pct={v.percentile_rank.iloc[0]!r}")
