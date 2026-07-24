#!/usr/bin/env python3
"""
Dealer leakage — ITUK dealers under-indexing on specific service categories.

Logic: a dealer's expected category mix = the network-median share of that
category across all qualifying ITUK dealers (relative benchmark — no invented
demand). A dealer whose actual share of a category is far below the median
while buying normally elsewhere is leaking that category to the aftermarket.

    expected_units(category) = dealer_total_units x median_share(category)
    gap_units = expected - actual (where positive)
    gap_eur   = gap_units x network avg selling price for the category
                (observed avg EUR/unit from ITUK billing, sales_fact CY2025)

Output: Data/derived/dealer_leakage_ituk.csv — the call list.
Run from prism/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, GENUINE_BVP_CROSSREF_CSV, resolve_mapping_path  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.dealer_sales_loader import load_ituk_dealer_sales  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

OUT_CSV = DERIVED_DIR / "dealer_leakage_ituk.csv"
ASSUMPTIONS = PRISM_ROOT / "data" / "decision_model_assumptions.yaml"


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lstrip("0")


def main() -> int:
    cfg = yaml.safe_load(ASSUMPTIONS.read_text(encoding="utf-8"))["dealer_leakage"]
    min_units = int(cfg["min_dealer_total_units"])

    df = load_ituk_dealer_sales(2025)
    if df.empty:
        print("ERROR: ITUK dealer sell-out file not found")
        return 1
    df = df[df["qty_year"] > 0].copy()
    df["_pn"] = _norm(df["part_number"])

    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype={"genuine_pn": str, "bvp_pn": str})
    cat_map: dict[str, str] = {}
    for col in ("genuine_pn", "bvp_pn"):
        sub = xref.dropna(subset=[col, "pms_category"])
        cat_map.update(dict(zip(_norm(sub[col]), sub["pms_category"])))
    df["category"] = df["_pn"].map(cat_map)

    # avg selling price per category from ITUK billing CY2025 (observed)
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    bill, _ = load_prism_sales(df_map)
    bill = bill[(bill["distributor_code"] == "ITUK") & (bill["year"] == 2025)].copy()
    if "line_kind" in bill.columns:
        bill = bill[bill["line_kind"] == "part"]
    bill["category"] = _norm(bill["part_number"]).map(cat_map)
    asp = (
        bill.dropna(subset=["category"])
        .groupby("category")
        .apply(
            lambda g: g["net_sales_value"].sum() / g["billed_qty"].sum()
            if g["billed_qty"].sum() > 0
            else float("nan"),
            include_groups=False,
        )
        .to_dict()
    )

    dealer_total = df.groupby("dealer_name")["qty_year"].sum()
    qualified = dealer_total[dealer_total >= min_units].index
    tagged = df[df["category"].notna() & df["dealer_name"].isin(qualified)]

    cat_units = (
        tagged.groupby(["dealer_name", "category"])["qty_year"].sum().reset_index()
    )
    cat_units["dealer_total_units"] = cat_units["dealer_name"].map(dealer_total)
    cat_units["share"] = cat_units["qty_year"] / cat_units["dealer_total_units"]

    # complete the grid so zero-purchase categories count as share 0
    grid = (
        pd.MultiIndex.from_product(
            [qualified, sorted(tagged["category"].unique())],
            names=["dealer_name", "category"],
        )
        .to_frame(index=False)
        .merge(cat_units, on=["dealer_name", "category"], how="left")
    )
    grid["qty_year"] = grid["qty_year"].fillna(0.0)
    grid["dealer_total_units"] = grid["dealer_name"].map(dealer_total)
    grid["share"] = grid["qty_year"] / grid["dealer_total_units"]

    med_share = grid.groupby("category")["share"].median().to_dict()
    grid["median_share"] = grid["category"].map(med_share)
    grid["expected_units"] = grid["dealer_total_units"] * grid["median_share"]
    grid["gap_units"] = (grid["expected_units"] - grid["qty_year"]).clip(lower=0).round(1)
    grid["avg_sp_eur"] = grid["category"].map(asp)
    grid["gap_eur"] = (grid["gap_units"] * grid["avg_sp_eur"]).round(2)

    # Soft join: most sell-out PNs are not in genuine_bvp_crossref PMS tags.
    # Dealers with zero mapped units have no observable category mix — their
    # "gaps" are grid artifacts, not call-list evidence.
    mapped_units = tagged.groupby("dealer_name")["qty_year"].sum()
    grid["mapped_units"] = grid["dealer_name"].map(mapped_units).fillna(0.0)
    grid["pct_mapped"] = (
        grid["mapped_units"] / grid["dealer_total_units"]
    ).round(3)

    out = grid[(grid["gap_units"] > 0) & (grid["mapped_units"] > 0)].copy()
    out["benchmark_note"] = (
        "expected = dealer total units x network-MEDIAN category share "
        "(relative benchmark, NOT IML absolute demand); EUR at observed ITUK "
        "billing avg price CY2025; PMS-tag soft join — pct_mapped is low; "
        "dealers with zero mapped units excluded"
    )
    out = out.sort_values("gap_eur", ascending=False)
    out.to_csv(OUT_CSV, index=False)

    top = out.groupby("dealer_name")["gap_eur"].sum().sort_values(ascending=False)
    print(
        f"leakage: {len(out)} dealer x category gaps -> {OUT_CSV.name} | "
        f"{len(qualified)} qualifying dealers | total benchmark gap "
        f"EUR{out['gap_eur'].sum():,.0f}"
    )
    print("  top dealers by gap:", "; ".join(f"{d} EUR{v:,.0f}" for d, v in top.head(3).items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
