#!/usr/bin/env python3
"""
GPS V2 — build parts_catalog_dimension.csv (PN → fig key + PR00 + PMS tags).

Run after pr00_classification.csv and bvp_pn_dimension.csv exist:
  python scripts/build_pr00_classification.py   # if PR00 xlsx available
  python scripts/build_bvp_p0_p1.py
  python scripts/build_fig_key_dimension.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    BVP_PN_DIMENSION_CSV,
    DERIVED_DIR,
)
from modules.fig_key_catalog import build_parts_catalog_dimension  # noqa: E402

OUT_CSV = DERIVED_DIR / "parts_catalog_dimension.csv"
OUT_PARQUET = DERIVED_DIR / "parts_catalog_dimension.parquet"
PR00_CSV = DERIVED_DIR / "pr00_classification.csv"


def main() -> int:
    if not PR00_CSV.exists():
        print(f"WARN: {PR00_CSV.name} missing — run build_pr00_classification.py first")
    if not BVP_PN_DIMENSION_CSV.exists():
        print(f"ERROR: {BVP_PN_DIMENSION_CSV.name} missing — run build_bvp_p0_p1.py first")
        return 1

    df = build_parts_catalog_dimension(
        pr00_csv=PR00_CSV,
        bvp_dimension_csv=BVP_PN_DIMENSION_CSV,
    )
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    df.to_parquet(OUT_PARQUET, index=False)

    with_fk = df["fig_key"].notna().sum()
    reg = df["pms_registry"].astype(str).str.lower().isin(("true", "1"))
    pms_fk = int((reg & df["fig_key"].notna()).sum())
    reg_n = int(reg.sum())
    print(f"  -> {len(df):,} PNs -> {OUT_CSV}")
    print(f"     fig_key assigned: {with_fk:,} | PMS registry with fig_key: {pms_fk}/{reg_n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
