"""Read-only diff: what moved in the derived files after the PRISM rebuilds."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
B = ROOT / "02_dashboards/_build/_aim_refresh2/before_derived"
D = ROOT / "01_data/00_derived"

FILES = [
    "gps_spu_by_distributor.csv",
    "gps_spu_by_family.csv",
    "gps_spu_pms.csv",
    "aim_exposure_by_db_year.csv",
    "aim_bvp_family_risk.csv",
]


def load(p: Path) -> pd.DataFrame:
    if p.suffix == ".parquet":
        return pd.read_parquet(p)
    return pd.read_csv(p, low_memory=False)


for name in FILES:
    b, a = load(B / name), load(D / name)
    print("==", name, "rows", len(b), "->", len(a))
    if list(b.columns) != list(a.columns):
        print("   COLUMNS DIFFER:", set(a.columns) ^ set(b.columns))
    common = [c for c in b.columns if c in a.columns]
    if len(b) == len(a) and len(common) == len(b.columns):
        moved = {}
        for c in common:
            if a[c].dtype.kind in "fi" and b[c].dtype.kind in "fi":
                n = int((a[c].fillna(0) - b[c].fillna(0)).abs().gt(1e-9).sum())
            else:
                n = int((a[c].astype(str) != b[c].astype(str)).sum())
            if n:
                moved[c] = n
        print("   cells/rows moved per column:", moved or "identical")
    else:
        print("   shape changed - comparing on best-effort")
