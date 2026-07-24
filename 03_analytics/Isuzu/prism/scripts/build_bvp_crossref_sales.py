#!/usr/bin/env python3
"""
Tag sales_fact lines with genuine<->BVP crossref and build substitution rollups.

Outputs:
  derived/sales_with_crossref.parquet
  derived/substitution_by_pair_year.csv
  derived/substitution_by_db_year.csv

Run after build_bvp_p0_p1.py (needs genuine_bvp_crossref.csv + sales_fact.parquet).
"""

from __future__ import annotations

import sys
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    SALES_FACT_PARQUET,
    SALES_WITH_CROSSREF_PARQUET,
    SUBSTITUTION_BY_DB_YEAR_CSV,
    SUBSTITUTION_BY_PAIR_YEAR_CSV,
    resolve_mapping_path,
)
from modules.bvp_crossref import load_crossref  # noqa: E402
from modules.bvp_product_nav import catalog_subcategories  # noqa: E402
from modules.bvp_substitution import (  # noqa: E402
    build_sales_with_crossref,
    build_substitution_by_db_year,
    build_substitution_by_pair_year,
)
from modules.data_prep import EXCLUDED_CODES, load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402


def main() -> int:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    if not GENUINE_BVP_CROSSREF_CSV.exists():
        print("Run build_bvp_p0_p1.py first (missing genuine_bvp_crossref.csv)")
        return 1
    if not SALES_FACT_PARQUET.exists():
        print("Run build_sales_fact_from_cy.py first")
        return 1

    xref = load_crossref(GENUINE_BVP_CROSSREF_CSV)
    print(f"Crossref: {len(xref):,} pairs", flush=True)

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df_sales, src = load_prism_sales(df_map)
    df_sales = df_sales[~df_sales["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]
    print(f"Sales: {len(df_sales):,} rows from {src}", flush=True)

    tagged = build_sales_with_crossref(df_sales, xref)
    tagged.to_parquet(SALES_WITH_CROSSREF_PARQUET, index=False)
    print(f"  -> {len(tagged):,} tagged lines -> {SALES_WITH_CROSSREF_PARQUET.name}")

    scoped = tagged[tagged["pms_in_scope"]].copy() if "pms_in_scope" in tagged.columns else tagged
    print(f"     PMS in-scope tagged lines: {len(scoped):,}")

    pair_all = build_substitution_by_pair_year(tagged)
    pair_all.to_csv(SUBSTITUTION_BY_PAIR_YEAR_CSV, index=False)
    print(f"  -> {len(pair_all):,} pair x DB x year rows -> {SUBSTITUTION_BY_PAIR_YEAR_CSV.name}")

    pair_scope = build_substitution_by_pair_year(scoped)
    db_year = build_substitution_by_db_year(pair_scope)
    db_year.to_csv(SUBSTITUTION_BY_DB_YEAR_CSV, index=False)
    print(f"  -> {len(db_year):,} DB x year rows (PMS scope) -> {SUBSTITUTION_BY_DB_YEAR_CSV.name}")

    if not pair_scope.empty:
        pat = pair_scope["substitution_pattern"].value_counts()
        print("\nSubstitution patterns (PMS in-scope pairs with sales):")
        for k, v in pat.items():
            print(f"  {k}: {v:,}")

    ituk = db_year[
        (db_year["distributor_code"] == "ITUK")
        & db_year["product_subgroup"].isin(catalog_subcategories())
    ]
    if not ituk.empty:
        latest = int(ituk["year"].max())
        row = ituk[ituk["year"] == latest].groupby("product_subgroup").head(1)
        print(f"\nITUK {latest} sample (subgroups):")
        cols = ["product_subgroup", "pairs_with_sales", "pairs_both", "pct_pairs_both", "bvp_share_units"]
        print(row[cols].to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
