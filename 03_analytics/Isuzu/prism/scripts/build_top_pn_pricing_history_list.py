#!/usr/bin/env python3
"""
Top-N part numbers by net revenue, as a template for Jerome to backfill
historical list-price points against.

Feeds ISZE_Pricing_Spec_v1.md sec12 ask #3 (dated PR00 snapshots) at a
manageable PN count instead of the full ~15,000-line list. Output is a CSV
with blank price_point_* columns to fill in by hand.

  python scripts/build_top_pn_pricing_history_list.py
  python scripts/build_top_pn_pricing_history_list.py --top 500 --year 2025
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from config import DERIVED_DIR, resolve_mapping_path  # noqa: E402
from modules.bvp_analytics import normalize_pn_value  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=500)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, src = load_prism_sales(df_map)
    print(f"Loaded sales from {src}")

    parts = sales[(sales["line_kind"] == "part") & (~sales["is_credit_note"])].copy()
    parts = parts[parts["year"] == args.year]
    parts["_pn"] = parts["part_number"].map(lambda x: normalize_pn_value(x) or "")
    parts = parts[parts["_pn"] != ""]

    agg = (
        parts.groupby("_pn")
        .agg(
            revenue_eur=("net_sales_value", "sum"),
            qty=("billed_qty", "sum"),
            description=("description", "first"),
            n_distributors=("distributor_code", "nunique"),
        )
        .reset_index()
        .rename(columns={"_pn": "part_number"})
    )

    agg = agg.sort_values("revenue_eur", ascending=False).head(args.top).reset_index(drop=True)
    agg.insert(0, "rank", range(1, len(agg) + 1))

    # Blank columns for Jerome to fill in dated historical list-price points.
    for col in (
        "price_point_1_date", "price_point_1_eur",
        "price_point_2_date", "price_point_2_eur",
        "price_point_3_date", "price_point_3_eur",
    ):
        agg[col] = ""

    out = (
        Path(args.out)
        if args.out
        else DERIVED_DIR / f"top{args.top}_pn_by_revenue_cy{args.year}_price_history_template.csv"
    )
    agg.to_csv(out, index=False)
    print(f"Wrote {len(agg)} PNs, EUR {agg['revenue_eur'].sum():,.0f} total revenue, to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
