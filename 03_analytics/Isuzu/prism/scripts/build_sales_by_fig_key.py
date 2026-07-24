#!/usr/bin/env python3
"""
Roll up parts sales by distributor × year × EPC fig key (GPS V2).

Requires: sales_fact.parquet + parts_catalog_dimension.csv
Output:   Data/derived/sales_by_db_fig_key_year.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    PARTS_CATALOG_DIMENSION_CSV,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)
from modules.bvp_analytics import normalize_pn_value  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

OUT = DERIVED_DIR / "sales_by_db_fig_key_year.csv"


def main() -> int:
    if not SALES_FACT_PARQUET.exists():
        print("sales_fact.parquet missing")
        return 1
    if not PARTS_CATALOG_DIMENSION_CSV.exists():
        print("parts_catalog_dimension.csv missing — run build_fig_key_dimension.py")
        return 1

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, _ = load_prism_sales(df_map)
    if "line_kind" in sales.columns:
        sales = sales[sales["line_kind"] == "part"]

    cat = pd.read_csv(PARTS_CATALOG_DIMENSION_CSV, dtype=str)
    cat["_pn"] = cat["part_number"].map(lambda x: normalize_pn_value(x) or "")
    cat = cat.drop_duplicates("_pn", keep="first")[["_pn", "fig_key", "fig_key_label", "pms_category"]]

    sales["_pn"] = sales["part_number"].map(lambda x: normalize_pn_value(x) or "")
    # sales_fact carries fig_key since 2026-07-02; the rollup re-derives it from
    # the catalog just rebuilt upstream, so drop the incoming column pre-merge.
    sales = sales.drop(columns=[c for c in ("fig_key", "fig_key_source") if c in sales.columns])
    m = sales.merge(cat, on="_pn", how="left")
    m["fig_key"] = m["fig_key"].fillna("unmapped")
    m["fig_key_label"] = m["fig_key_label"].fillna("Unmapped")

    g = (
        m.groupby(
            ["year", "distributor_code", "fig_key", "fig_key_label"],
            dropna=False,
        )
        .agg(
            billed_qty=("billed_qty", "sum"),
            net_sales_eur=("net_sales_value", "sum"),
            distinct_pns=("part_number", "nunique"),
        )
        .reset_index()
    )
    g["billed_qty"] = g["billed_qty"].round(1)
    g["net_sales_eur"] = g["net_sales_eur"].round(2)

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    g.to_csv(OUT, index=False)
    mapped = m["fig_key"].ne("unmapped").mean()
    print(f"  -> {len(g):,} rows -> {OUT}")
    print(f"     line-level fig_key match: {mapped:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
