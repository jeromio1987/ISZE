#!/usr/bin/env python3
"""
P2: Genuine vs BVP mix + YoY by family, product group, and PMS subcategory.

Outputs:
  derived/mix_genuine_bvp_by_family.csv
  derived/mix_genuine_bvp_by_subgroup.csv   (PMS in-scope only)
  derived/mix_genuine_bvp_by_group.csv
  derived/mix_genuine_bvp_pms.csv           (legacy flat PMS slice)
  derived/db_benchmark_mix.csv
  derived/db_benchmark_mix_subgroup.csv
  derived/db_benchmark_mix_group.csv

Run after build_bvp_p0_p1.py (needs sales_fact + bvp_pn_dimension).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    BVP_PN_DIMENSION_CSV,
    DB_BENCHMARK_GROUP_CSV,
    DB_BENCHMARK_MIX_CSV,
    DB_BENCHMARK_SUBGROUP_CSV,
    DERIVED_DIR,
    MIX_BY_FAMILY_CSV,
    MIX_BY_GROUP_CSV,
    MIX_BY_SUBGROUP_CSV,
    MIX_PMS_CSV,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
)
from modules.bvp_analytics import tag_sales_with_dimension  # noqa: E402
from modules.bvp_product_nav import (  # noqa: E402
    attach_navigation_columns,
    catalog_subcategories,
    group_label,
    subgroup_label,
)
from modules.data_prep import EXCLUDED_CODES  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402


def _aggregate_mix(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    scoped = df[df["line_type"].isin(["genuine", "bvp"])].copy()
    if scoped.empty:
        return pd.DataFrame()

    qty = (
        scoped.groupby(group_cols + ["line_type"], dropna=False)["billed_qty"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={"genuine": "genuine_qty", "bvp": "bvp_qty"})
    )
    rev = (
        scoped.groupby(group_cols + ["line_type"], dropna=False)["net_sales_value"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={"genuine": "genuine_eur", "bvp": "bvp_eur"})
    )

    out = qty.join(rev, how="outer").reset_index()
    for c in ("genuine_qty", "bvp_qty", "genuine_eur", "bvp_eur"):
        if c not in out.columns:
            out[c] = 0.0
        out[c] = out[c].fillna(0.0)

    denom_qty = out["genuine_qty"] + out["bvp_qty"]
    denom_eur = out["genuine_eur"] + out["bvp_eur"]
    out["bvp_share_units"] = np.where(denom_qty > 0, out["bvp_qty"] / denom_qty, np.nan)
    out["bvp_share_eur"] = np.where(denom_eur > 0, out["bvp_eur"] / denom_eur, np.nan)
    out["total_qty"] = denom_qty
    out["total_eur"] = denom_eur
    return out


def _add_yoy_trends(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if df.empty or "year" not in df.columns:
        return df

    sort_cols = group_cols + ["year"]
    df = df.sort_values(sort_cols).copy()
    gcols = [c for c in group_cols if c != "year"]

    df["prior_year"] = df.groupby(gcols)["year"].shift(1)
    df["bvp_share_units_prior"] = df.groupby(gcols)["bvp_share_units"].shift(1)
    df["bvp_share_eur_prior"] = df.groupby(gcols)["bvp_share_eur"].shift(1)
    df["total_qty_prior"] = df.groupby(gcols)["total_qty"].shift(1)
    df["genuine_qty_prior"] = df.groupby(gcols)["genuine_qty"].shift(1)

    df["bvp_share_units_yoy_pp"] = (df["bvp_share_units"] - df["bvp_share_units_prior"]) * 100
    df["bvp_share_eur_yoy_pp"] = (df["bvp_share_eur"] - df["bvp_share_eur_prior"]) * 100
    # Flag G: a prior-year base of a handful of units turns 1→many into thousands of %
    # and makes YoY charts unreadable. Suppress YoY% to NaN when the prior base is below
    # this threshold — the percentage is meaningless there, not informative.
    YOY_MIN_BASE = 10
    df["total_qty_yoy_pct"] = np.where(
        df["total_qty_prior"] >= YOY_MIN_BASE,
        (df["total_qty"] - df["total_qty_prior"]) / df["total_qty_prior"] * 100,
        np.nan,
    )
    df["genuine_qty_yoy_pct"] = np.where(
        df["genuine_qty_prior"] >= YOY_MIN_BASE,
        (df["genuine_qty"] - df["genuine_qty_prior"]) / df["genuine_qty_prior"] * 100,
        np.nan,
    )
    df["substitution_flag"] = (
        (df["bvp_share_units_yoy_pp"] > 2)
        & (df["genuine_qty_yoy_pct"] < -5)
        & (df["total_qty_yoy_pct"].between(-5, 10, inclusive="both"))
    )
    return df


def _build_benchmarks(df: pd.DataFrame, level_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    med = (
        df.groupby(["year"] + level_cols, dropna=False)["bvp_share_units"]
        .median()
        .reset_index()
        .rename(columns={"bvp_share_units": "network_median_bvp_share_units"})
    )
    bench = df.merge(med, on=["year"] + level_cols, how="left")
    bench["vs_network_median_pp"] = (
        bench["bvp_share_units"] - bench["network_median_bvp_share_units"]
    ) * 100
    bench["quartile_rank"] = bench.groupby(["year"] + level_cols)["bvp_share_units"].rank(
        pct=True
    )
    sort_cols = ["year"] + level_cols + ["distributor_code"]
    return bench.sort_values(sort_cols)


def main() -> int:
    if not BVP_PN_DIMENSION_CSV.exists():
        print("Run build_bvp_p0_p1.py first (missing bvp_pn_dimension.csv)")
        return 1
    if not SALES_FACT_PARQUET.exists():
        print("Run build_sales_fact_from_cy.py first")
        return 1

    df_dim = pd.read_csv(BVP_PN_DIMENSION_CSV, dtype=str)
    if "product_group" not in df_dim.columns:
        df_dim = attach_navigation_columns(df_dim)

    df_map = __import__(
        "modules.data_prep", fromlist=["load_distributor_mapping"]
    ).load_distributor_mapping(str(resolve_mapping_path()))
    df_sales, src = load_prism_sales(df_map)
    print(f"P2: {len(df_sales):,} sales rows from {src}")

    tagged = tag_sales_with_dimension(df_sales, df_dim)
    tagged = tagged[~tagged["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]
    tagged = tagged[tagged["line_type"].isin(["genuine", "bvp"])]

    print(f"  Catalog-matched genuine|bvp lines: {len(tagged):,}")

    # All catalog families (reference)
    fam = _aggregate_mix(tagged, ["year", "distributor_code", "product_family"])
    fam = _add_yoy_trends(fam, ["distributor_code", "product_family"])
    fam.to_csv(MIX_BY_FAMILY_CSV, index=False)
    print(f"  -> {len(fam):,} rows -> {MIX_BY_FAMILY_CSV}")

    # Full BVP catalog subgroups (27) — per-distributor scope via addressable basket in UI
    catalog_sg = set(catalog_subcategories())
    asm_sg = {f"{s}_asm" for s in catalog_sg} | {f"{s}_kit" for s in catalog_sg}
    catalog_sg_all = catalog_sg | asm_sg
    if "mix_subgroup" not in tagged.columns:
        tagged["mix_subgroup"] = tagged.get("product_subgroup", tagged.get("pms_category"))
    if "product_subgroup" not in tagged.columns:
        tagged["product_subgroup"] = tagged.get("pms_category")
    scoped = tagged[tagged["mix_subgroup"].astype(str).isin(catalog_sg_all)].copy()
    scoped["product_subgroup"] = scoped["mix_subgroup"]
    if "product_group" not in scoped.columns:
        scoped = scoped.merge(
            df_dim[["part_number", "product_group"]].drop_duplicates("part_number"),
            on="part_number",
            how="left",
        )

    sub = _aggregate_mix(
        scoped,
        ["year", "distributor_code", "product_group", "product_subgroup"],
    )
    sub["product_group_label"] = sub["product_group"].map(group_label)
    sub["subgroup_label"] = sub["product_subgroup"].map(subgroup_label)
    sub = _add_yoy_trends(sub, ["distributor_code", "product_group", "product_subgroup"])
    sub.to_csv(MIX_BY_SUBGROUP_CSV, index=False)
    print(f"  -> {len(sub):,} rows -> {MIX_BY_SUBGROUP_CSV}")

    grp = _aggregate_mix(scoped, ["year", "distributor_code", "product_group"])
    grp["product_group_label"] = grp["product_group"].map(group_label)
    grp = _add_yoy_trends(grp, ["distributor_code", "product_group"])
    grp.to_csv(MIX_BY_GROUP_CSV, index=False)
    print(f"  -> {len(grp):,} rows -> {MIX_BY_GROUP_CSV}")

    # Legacy flat PMS file (subgroup = pms_category, with product_group)
    pms_agg = sub.drop(columns=["subgroup_label"], errors="ignore").copy()
    pms_agg["product_family"] = pms_agg["product_group"]
    pms_agg.to_csv(MIX_PMS_CSV, index=False)
    print(f"  -> {len(pms_agg):,} rows -> {MIX_PMS_CSV}")

    bench_fam = _build_benchmarks(fam, ["product_family"])
    bench_fam.to_csv(DB_BENCHMARK_MIX_CSV, index=False)
    print(f"  -> {len(bench_fam):,} rows -> {DB_BENCHMARK_MIX_CSV}")

    bench_sub = _build_benchmarks(sub, ["product_group", "product_subgroup"])
    bench_sub.to_csv(DB_BENCHMARK_SUBGROUP_CSV, index=False)
    print(f"  -> {len(bench_sub):,} rows -> {DB_BENCHMARK_SUBGROUP_CSV}")

    bench_grp = _build_benchmarks(grp, ["product_group"])
    bench_grp.to_csv(DB_BENCHMARK_GROUP_CSV, index=False)
    print(f"  -> {len(bench_grp):,} rows -> {DB_BENCHMARK_GROUP_CSV}")

    ituk = sub[
        (sub["distributor_code"] == "ITUK") & (sub["product_subgroup"] == "oil_filter")
    ].sort_values("year")
    if not ituk.empty:
        print("\nITUK oil_filter mix:")
        print(
            ituk[
                [
                    "year",
                    "bvp_share_units",
                    "bvp_share_units_yoy_pp",
                    "total_qty_yoy_pct",
                    "substitution_flag",
                ]
            ].to_string(index=False)
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
