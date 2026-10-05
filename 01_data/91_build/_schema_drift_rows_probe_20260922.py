"""Read-only probe 2: which ROWS (keys) vanished between HEAD and disk, for the shrinkers."""
from __future__ import annotations

import io
import subprocess
from pathlib import Path

import pandas as pd

REPO = Path(r"C:\Users\jerom\Desktop\claude\ISZE")


def head_df(rel: str) -> pd.DataFrame:
    raw = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=REPO,
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    return pd.read_csv(io.StringIO(raw), dtype=str, low_memory=False)


def disk_df(rel: str) -> pd.DataFrame:
    return pd.read_csv(REPO / rel, dtype=str, low_memory=False)


CASES = [
    ("01_data/00_derived/gps_spu_by_distributor.csv", ["year", "distributor_code"]),
    ("01_data/00_derived/lost_sales_model.csv", ["year", "distributor_code", "pms_category", "gap_type"]),
    ("01_data/00_derived/network_percentile.csv", ["year", "distributor_code", "metric"]),
    ("01_data/00_derived/aim_gps_matrix.csv", None),
    ("01_data/00_derived/capture_trajectory.csv", None),
]

for rel, keys in CASES:
    name = Path(rel).name
    h, d = head_df(rel), disk_df(rel)
    print(f"\n=== {name}  HEAD {len(h)} -> disk {len(d)} ===")
    if keys and all(k in h.columns for k in keys):
        hk = h[keys].astype(str).agg("|".join, axis=1)
        dk = d[keys].astype(str).agg("|".join, axis=1)
        gone = sorted(set(hk) - set(dk))
        new = sorted(set(dk) - set(hk))
        print(f"  key = {keys}")
        print(f"  keys gone ({len(gone)}): {gone[:25]}")
        print(f"  keys new  ({len(new)}): {new[:25]}")
        # duplicate keys?
        print(f"  dup keys HEAD {hk.duplicated().sum()}  disk {dk.duplicated().sum()}")
    else:
        print("  no stable key; column diff only")
    lost = [c for c in h.columns if c not in d.columns]
    print(f"  columns lost: {lost}")
