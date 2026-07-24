#!/usr/bin/env python3
"""
DB Parts Classification — honest total-revenue genuine/BVP mix per distributor.

Every parts line is tagged into one of three buckets from real catalogue joins:
  - bvp             : part number is a Best Value Parts SKU
  - genuine_contested : genuine PN that HAS a BVP equivalent in the catalogue
  - genuine_only    : Isuzu genuine with no BVP alternative

Shares are over TOTAL parts revenue (line_kind == 'part'), not the restricted
paired basket — so they are comparable across distributors. The contested-basket
BVP capture (bvp / (bvp + genuine_contested)) shows how much of the conquerable
demand the value line has already taken per DB.

NOTE: this does NOT measure non-Isuzu competitor wallet share — that never
touches our invoice. See DATA_INTEGRITY_FLAGS: leakage is an inference, not this.

Output: Data/derived/db_parts_mix_classification.csv (+ .parquet)
Single source of truth for the Excel/PDF/Streamlit/Evidence/Dash views.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    DISTRIBUTOR_MAPPING_CANDIDATES,
    GENUINE_BVP_CROSSREF_CSV,
)
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales, resolve_first_existing  # noqa: E402

OUTPUT_CSV = DERIVED_DIR / "db_parts_mix_classification.csv"
OUTPUT_PARQUET = DERIVED_DIR / "db_parts_mix_classification.parquet"


def _classify(sales: pd.DataFrame, genuine_pns: set[str], bvp_pns: set[str]) -> pd.DataFrame:
    pn = sales["part_number"].astype(str).str.strip()
    bucket = pd.Series("genuine_only", index=sales.index)
    bucket.loc[pn.isin(genuine_pns)] = "genuine_contested"
    bucket.loc[pn.isin(bvp_pns)] = "bvp"
    sales = sales.copy()
    sales["bucket"] = bucket
    return sales


def build() -> pd.DataFrame:
    mapping_path = resolve_first_existing(DISTRIBUTOR_MAPPING_CANDIDATES)
    df_mapping = load_distributor_mapping(mapping_path)
    sales, _ = load_prism_sales(df_mapping)

    if "line_kind" in sales.columns:
        sales = sales[sales["line_kind"] == "part"]

    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype=str)
    genuine_pns = set(xref["genuine_pn"].dropna().str.strip())
    bvp_pns = set(xref["bvp_pn"].dropna().str.strip())

    sales = _classify(sales, genuine_pns, bvp_pns)

    grp = (
        sales.groupby(["distributor_code", "year", "bucket"])["net_sales_value"]
        .sum()
        .unstack("bucket", fill_value=0.0)
        .reset_index()
    )
    for col in ("bvp", "genuine_contested", "genuine_only"):
        if col not in grp.columns:
            grp[col] = 0.0

    grp["total_eur"] = grp[["bvp", "genuine_contested", "genuine_only"]].sum(axis=1)
    grp = grp[grp["total_eur"] > 0].copy()

    grp["bvp_pct"] = grp["bvp"] / grp["total_eur"]
    grp["genuine_contested_pct"] = grp["genuine_contested"] / grp["total_eur"]
    grp["genuine_only_pct"] = grp["genuine_only"] / grp["total_eur"]

    contested = grp["bvp"] + grp["genuine_contested"]
    grp["contested_eur"] = contested
    grp["contested_bvp_capture"] = grp["bvp"] / contested.where(contested > 0)

    grp = grp.rename(columns={
        "bvp": "bvp_eur",
        "genuine_contested": "genuine_contested_eur",
        "genuine_only": "genuine_only_eur",
    })

    ordered = [
        "distributor_code", "year", "total_eur",
        "bvp_eur", "genuine_contested_eur", "genuine_only_eur",
        "bvp_pct", "genuine_contested_pct", "genuine_only_pct",
        "contested_eur", "contested_bvp_capture",
    ]
    return grp[ordered].sort_values(["year", "total_eur"], ascending=[True, False])


def main() -> None:
    df = build()
    df.to_csv(OUTPUT_CSV, index=False)
    df.to_parquet(OUTPUT_PARQUET, index=False)
    latest = df["year"].max()
    net = df[df["year"] == latest]["total_eur"].sum()
    bvp = df[df["year"] == latest]["bvp_eur"].sum()
    print(f"ok: {len(df)} rows -> {OUTPUT_CSV}")
    print(f"   CY{latest}: network parts rev EUR {net:,.0f}  |  BVP share {bvp / net:.1%}")


if __name__ == "__main__":
    main()
