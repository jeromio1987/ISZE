#!/usr/bin/env python3
"""
Contract 16 — ITUK PMS part-number audit (PN × category × year).

Output: Data/derived/ituk_pms_pn_audit.csv
Run after build_bvp_p0_p1.py (needs sales_fact + dimension).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, SALES_FACT_PARQUET, resolve_mapping_path  # noqa: E402
from modules.bvp_analytics import ensure_part_number  # noqa: E402
from modules.bvp_dimension import build_dimension_from_catalog  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.pms_engine import filter_pms_by_scope, pms_scope_for_distributor  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402
from scripts.build_bvp_p0_p1 import (  # noqa: E402
    _resolve_catalog,
    enrich_pms_from_dimension,
)

OUT = DERIVED_DIR / "ituk_pms_pn_audit.csv"
DIST = "ITUK"


def build_ituk_pms_pn_audit() -> pd.DataFrame:
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df_sales, _ = load_prism_sales(df_map)
    df_dim = build_dimension_from_catalog(_resolve_catalog())

    df = ensure_part_number(df_sales)
    df = enrich_pms_from_dimension(df, df_dim)
    df = df[(df["distributor_code"] == DIST) & df["is_pms"]].copy()
    scope = pms_scope_for_distributor(DIST)
    df = filter_pms_by_scope(df, scope)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "year",
                "distributor_code",
                "pms_category",
                "category_label",
                "part_number",
                "pms_type",
                "pms_model",
                "actual_qty",
                "actual_rev_eur",
                "share_of_category_qty",
                "scope",
            ]
        )

    g = (
        df.groupby(
            ["year", "pms_category", "part_number", "pms_type", "pms_model"],
            dropna=False,
        )
        .agg(actual_qty=("billed_qty", "sum"), actual_rev_eur=("net_sales_value", "sum"))
        .reset_index()
    )
    g["distributor_code"] = DIST
    g["scope"] = scope

    cat_totals = g.groupby(["year", "pms_category"])["actual_qty"].transform("sum")
    g["share_of_category_qty"] = (g["actual_qty"] / cat_totals.replace(0, float("nan"))).round(4)

    labels = {
        "oil_filter": "Oil Filter",
        "fuel_filter": "Fuel Filter",
        "air_filter": "Air Filter",
        "brake_pad": "Brake Pad",
        "brake_shoe": "Brake Shoe",
        "clutch_disc": "Clutch Disc",
        "clutch_pressure_plate": "Clutch Pressure Plate",
    }
    g["category_label"] = g["pms_category"].map(labels).fillna(g["pms_category"])

    cols = [
        "year",
        "distributor_code",
        "pms_category",
        "category_label",
        "part_number",
        "pms_type",
        "pms_model",
        "actual_qty",
        "actual_rev_eur",
        "share_of_category_qty",
        "scope",
    ]
    return g[cols].sort_values(["year", "pms_category", "actual_qty"], ascending=[True, True, False])


def main() -> int:
    if not SALES_FACT_PARQUET.exists():
        print("sales_fact.parquet missing — run build_sales_fact_from_cy.py first", flush=True)
        return 1

    df = build_ituk_pms_pn_audit()
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"  -> {len(df):,} rows -> {OUT}")
    if not df.empty:
        oil = df[df["pms_category"] == "oil_filter"]
        if not oil.empty:
            print("\nITUK oil_filter PN audit (top qty by year):")
            for year in sorted(oil["year"].unique()):
                sub = oil[oil["year"] == year].head(5)
                print(f"  CY{int(year)}: {sub[['part_number','pms_type','actual_qty','share_of_category_qty']].to_dict('records')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
