#!/usr/bin/env python3
"""One-off UTI data audit — dimension vs crossref vs sales vs mix file."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]  # ISZE/
PRISM = ROOT / "Projects" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))
os.chdir(PRISM)

from config import BVP_PN_DIMENSION_CSV, SALES_FACT_PARQUET  # noqa: E402
from modules.bvp_analytics import tag_sales_with_dimension  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402


def norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.upper()


def main() -> int:
    dim = pd.read_csv(BVP_PN_DIMENSION_CSV, dtype=str)
    xref = pd.read_csv(ROOT / "Data/derived/genuine_bvp_crossref.csv", dtype=str)
    mix = pd.read_csv(ROOT / "Data/derived/mix_genuine_bvp_pms.csv")
    mix_sg = pd.read_csv(ROOT / "Data/derived/mix_genuine_bvp_by_subgroup.csv")

    dim["pn"] = norm(dim["part_number"])
    xref["g_pn"] = norm(xref["genuine_pn"])
    xref["b_pn"] = norm(xref["bvp_pn"])

    xref_bvp = set(xref["b_pn"].dropna())
    xref_gen = set(xref["g_pn"].dropna())
    dim_idx = dim.set_index("pn")

    bvp_tagged_genuine = dim[(dim["pn"].isin(xref_bvp)) & (dim["line_type"] == "genuine")]
    gen_tagged_bvp = dim[(dim["pn"].isin(xref_gen)) & (dim["line_type"] == "bvp")]

    def bvp_prefix(pn: str) -> bool:
        return str(pn).startswith(("1876", "5876"))

    prefix_genuine = dim[(dim["line_type"] == "genuine") & dim["pn"].map(bvp_prefix)]

    print("=" * 60)
    print("DIMENSION vs CROSSREF")
    print("=" * 60)
    print(f"Dimension: {len(dim)} PNs (bvp={(dim['line_type']=='bvp').sum()}, genuine={(dim['line_type']=='genuine').sum()})")
    print(f"Crossref pairs: {len(xref)}")
    print(f"BVP role in crossref but line_type=genuine in dim: {len(bvp_tagged_genuine)}")
    if len(bvp_tagged_genuine):
        print(bvp_tagged_genuine[["part_number", "product_subgroup", "sheet_source"]].to_string(index=False))
    print(f"Genuine role in crossref but line_type=bvp in dim: {len(gen_tagged_bvp)}")
    if len(gen_tagged_bvp):
        print(gen_tagged_bvp[["part_number", "product_subgroup", "sheet_source"]].head(15).to_string(index=False))
    print(f"BVP-prefix (1876/5876) tagged genuine: {len(prefix_genuine)}")
    if len(prefix_genuine):
        print(prefix_genuine[["part_number", "product_subgroup", "sheet_source"]].to_string(index=False))

    # Sales
    df_map = load_distributor_mapping(str(PRISM / "data" / "distributor_mapping.csv"))
    sales, src = load_prism_sales(df_map)
    print(f"\nSales loaded: {len(sales):,} from {src}")

    tagged = tag_sales_with_dimension(sales, dim)
    y2025 = tagged[tagged["year"] == 2025].copy()

    for dist in ("UTI", "ITUK"):
        d = y2025[y2025["distributor_code"] == dist]
        total = d["net_sales_value"].sum()
        in_cat = d[d["line_type"].isin(["genuine", "bvp"])]
        gen_e = in_cat.loc[in_cat["line_type"] == "genuine", "net_sales_value"].sum()
        bvp_e = in_cat.loc[in_cat["line_type"] == "bvp", "net_sales_value"].sum()
        other_e = total - gen_e - bvp_e
        print(f"\n--- {dist} CY2025 (dimension line_type) ---")
        print(f"  Total parts sales EUR: {total:,.0f}")
        print(f"  Catalog-tagged genuine EUR: {gen_e:,.0f} ({100*gen_e/total:.1f}%)")
        print(f"  Catalog-tagged BVP EUR: {bvp_e:,.0f} ({100*bvp_e/total:.1f}%)")
        print(f"  Untagged / other EUR: {other_e:,.0f} ({100*other_e/total:.1f}%)")

        # Re-tag BVP PNs using crossref bvp set only
        d2 = d.copy()
        d2["lt_xref"] = np.where(d2["part_number"].isin(xref_bvp), "bvp", np.where(d2["part_number"].isin(xref_gen), "genuine", "other"))
        xb = d2[d2["lt_xref"] == "bvp"]["net_sales_value"].sum()
        xg = d2[d2["lt_xref"] == "genuine"]["net_sales_value"].sum()
        contest = xb + xg
        if contest:
            print(f"  Crossref-only contestable: BVP {100*xb/contest:.1f}% EUR | Genuine {100*xg/contest:.1f}%")

    # Mix file interpretation for UTI 2025
    uti_mix = mix[(mix["distributor_code"] == "UTI") & (mix["year"] == 2025)]
    if not uti_mix.empty:
        gq = uti_mix["genuine_qty"].sum()
        bq = uti_mix["bvp_qty"].sum()
        print(f"\n--- mix_genuine_bvp_pms.csv UTI 2025 (flat PMS) ---")
        print(f"  Substitution basket only: BVP {100*bq/(gq+bq):.1f}% units | Genuine {100*gq/(gq+bq):.1f}%")

    uti_sg = mix_sg[(mix_sg["distributor_code"] == "UTI") & (mix_sg["year"] == 2025)]
    print(f"\n--- Per-subgroup UTI 2025 (mix file = contestable lines only) ---")
    for _, r in uti_sg.sort_values("product_subgroup").iterrows():
        tq = r["genuine_qty"] + r["bvp_qty"]
        if tq < 1:
            continue
        print(f"  {r['product_subgroup']:25s}  BVP {r['bvp_share_units']*100:5.1f}% units  (g={r['genuine_qty']:.0f} b={r['bvp_qty']:.0f})")

    # Per-subgroup from ALL sales (dimension tag)
    print(f"\n--- Per-subgroup UTI 2025 (ALL sales lines with pms_category) ---")
    uti25 = y2025[y2025["distributor_code"] == "UTI"]
    uti25 = uti25[uti25["line_type"].isin(["genuine", "bvp"])]
    if "pms_category" in uti25.columns:
        for cat, g in uti25.groupby("pms_category"):
            tq = g["billed_qty"].sum()
            bq = g.loc[g["line_type"] == "bvp", "billed_qty"].sum()
            if tq < 1:
                continue
            print(f"  {str(cat):25s}  BVP {100*bq/tq:5.1f}% units")

    # Oil filter PN drill-down
    oil = uti25[uti25["pms_category"] == "oil_filter"] if "pms_category" in uti25.columns else pd.DataFrame()
    if not oil.empty:
        top = (
            oil.groupby(["part_number", "line_type"])["billed_qty"]
            .sum()
            .reset_index()
            .sort_values("billed_qty", ascending=False)
            .head(8)
        )
        print("\n--- UTI oil filter top PNs (dimension line_type) ---")
        print(top.to_string(index=False))

    # Impact of fixing mistags on mix
    if len(bvp_tagged_genuine):
        bad_pns = set(bvp_tagged_genuine["pn"])
        uti_lines = y2025[(y2025["distributor_code"] == "UTI") & (y2025["part_number"].isin(bad_pns))]
        print(f"\n--- Sales on mis-tagged BVP-as-genuine PNs (UTI 2025) ---")
        print(f"  Lines: {len(uti_lines):,}  EUR: {uti_lines['net_sales_value'].sum():,.0f}  Qty: {uti_lines['billed_qty'].sum():,.0f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
