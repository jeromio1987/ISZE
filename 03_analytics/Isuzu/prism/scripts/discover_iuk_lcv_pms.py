#!/usr/bin/env python3
"""Discover LCV / IUK PMS part numbers from sales + BVP dimension."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import DERIVED_DIR, resolve_mapping_path  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.pms_engine import classify_pms_sales, PMS_PN_REGISTRY  # noqa: E402

OUT = PRISM / "data" / "iuk_lcv_pms_discovery.csv"


def main() -> int:
    dim = pd.read_csv(DERIVED_DIR / "bvp_pn_dimension.csv", dtype=str)
    dim_pms = dim[dim["pms_flag"].astype(str).str.lower().isin(("true", "1", "yes"))].copy()
    dim_pms["_pn"] = dim_pms["part_number"].str.lstrip("0")

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, _ = load_prism_sales(df_map)
    iuk = sales[(sales["distributor_code"] == "IUK") & (sales["year"].isin([2024, 2025]))].copy()
    iuk["_pn"] = iuk["part_number"].astype(str).str.strip().str.lstrip("0")

    merged = iuk.merge(
        dim_pms[["_pn", "pms_category", "line_type", "product_subgroup"]],
        on="_pn",
        how="inner",
    )
    top = (
        merged.groupby(["_pn", "pms_category", "line_type", "part_description"], dropna=False)
        .agg(qty=("billed_qty", "sum"), rev=("net_sales_value", "sum"))
        .reset_index()
        .sort_values(["pms_category", "qty"], ascending=[True, False])
    )
    top.to_csv(OUT, index=False)

    classified = classify_pms_sales(iuk)
    in_reg = classified[classified["is_pms"]]
    not_reg = classified[~classified["is_pms"]]
    kw = not_reg[
        not_reg["part_description"].str.contains(
            r"FILTER|BRAKE|CLUTCH|OIL|ELEMENT",
            case=False,
            na=False,
        )
    ]
    kw_top = (
        kw.groupby(["_pn", "part_description"])
        .agg(qty=("billed_qty", "sum"), rev=("net_sales_value", "sum"))
        .reset_index()
        .sort_values("qty", ascending=False)
        .head(80)
    )
    kw_out = PRISM / "data" / "iuk_lcv_untagged_filters.csv"
    kw_top.to_csv(kw_out, index=False)

    print(f"Wrote {OUT} ({len(top)} rows)")
    print(f"Wrote {kw_out} ({len(kw_top)} rows)")
    print(f"IUK billing lines 2024-25: {len(iuk):,}")
    print(f"Already in PMS_PN_REGISTRY: {in_reg['is_pms'].sum():,} lines")
    print(f"Registry size: {len(PMS_PN_REGISTRY)} PNs")
    for cat in ["oil_filter", "fuel_filter", "air_filter", "brake_pad", "brake_shoe"]:
        sub = top[top["pms_category"] == cat].head(8)
        if sub.empty:
            continue
        print(f"\n=== {cat} (BVP dim tagged) ===")
        for _, r in sub.iterrows():
            print(f"  {r['_pn']:>10}  qty={int(r['qty']):>6}  {r['line_type']}  {str(r['part_description'])[:50]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
