#!/usr/bin/env python3
"""
Per-distributor addressable BVP basket from lifetime Genuine sales (sales-driven scope).

Output: Data/derived/bvp_addressable_basket.csv

Run after build_bvp_crossref_sales.py (needs sales_with_crossref.parquet).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    BVP_ADDRESSABLE_BASKET_CSV,
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    SALES_WITH_CROSSREF_PARQUET,
)


def main() -> int:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    if not SALES_WITH_CROSSREF_PARQUET.exists():
        print("Run build_bvp_crossref_sales.py first (missing sales_with_crossref.parquet)")
        return 1
    if not GENUINE_BVP_CROSSREF_CSV.exists():
        print("Run build_bvp_p0_p1.py first (missing genuine_bvp_crossref.csv)")
        return 1

    swx = pd.read_parquet(SALES_WITH_CROSSREF_PARQUET)
    xref = pd.read_csv(
        GENUINE_BVP_CROSSREF_CSV,
        dtype={"genuine_pn": str, "bvp_pn": str},
    )

    for col in ("crossref_role", "xref_genuine_pn", "xref_bvp_pn"):
        if col not in swx.columns:
            print(f"sales_with_crossref missing column: {col}")
            return 1

    gen_sold = (
        swx.loc[swx["crossref_role"] == "genuine"]
        .groupby("distributor_code")["xref_genuine_pn"]
        .apply(lambda s: set(s.dropna().astype(str)))
        .to_dict()
    )
    bvp_sold = (
        swx.loc[swx["crossref_role"] == "bvp"]
        .groupby("distributor_code")["xref_bvp_pn"]
        .apply(lambda s: set(s.dropna().astype(str)))
        .to_dict()
    )

    xref_cols = [
        "genuine_pn",
        "bvp_pn",
        "product_subgroup",
        "product_family",
        "vehicle_model",
        "engine_type",
        "origin",
        "pms_flag",
    ]
    xref_use = xref[[c for c in xref_cols if c in xref.columns]].copy()

    rows: list[dict] = []
    for dist, gen_set in gen_sold.items():
        if not gen_set:
            continue
        addressable = xref_use[xref_use["genuine_pn"].astype(str).isin(gen_set)]
        sold_bvp = bvp_sold.get(dist, set())
        for _, p in addressable.iterrows():
            bvp_pn = str(p["bvp_pn"])
            rows.append(
                {
                    "distributor_code": dist,
                    "genuine_pn": str(p["genuine_pn"]),
                    "bvp_pn": bvp_pn,
                    "product_subgroup": p.get("product_subgroup"),
                    "product_family": p.get("product_family"),
                    "vehicle_model": p.get("vehicle_model"),
                    "engine_type": p.get("engine_type"),
                    "origin": p.get("origin"),
                    "pms_flag": bool(p.get("pms_flag")) if pd.notna(p.get("pms_flag")) else False,
                    "currently_selling_bvp": bvp_pn in sold_bvp,
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(BVP_ADDRESSABLE_BASKET_CSV, index=False)
    print(f"Addressable basket: {len(out):,} rows -> {BVP_ADDRESSABLE_BASKET_CSV.name}")

    if not out.empty:
        n_dist = out["distributor_code"].nunique()
        n_sg = out["product_subgroup"].nunique()
        print(f"  Distributors: {n_dist} · Subgroups: {n_sg}")

        for dist in ("ITUK", "ICELAND", "PORTUGAL"):
            sub = out[out["distributor_code"] == dist]
            if sub.empty:
                print(f"  {dist}: (no rows)")
                continue
            n_addr = sub["bvp_pn"].nunique()
            n_selling = sub.loc[sub["currently_selling_bvp"], "bvp_pn"].nunique()
            pct = n_selling / n_addr * 100 if n_addr else 0
            print(f"  {dist}: {n_selling}/{n_addr} BVP PNs selling ({pct:.0f}% penetration)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
