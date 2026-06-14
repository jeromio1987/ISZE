#!/usr/bin/env python3
"""Compute verified UTI meeting facts after dimension fix."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[3] / "Projects" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))
ROOT = Path(__file__).resolve().parents[3]

from config import BVP_PN_DIMENSION_CSV, resolve_mapping_path  # noqa: E402
from modules.bvp_analytics import tag_sales_with_dimension  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

DERIVED = ROOT / "Data" / "derived"


def main() -> None:
    dim = pd.read_csv(BVP_PN_DIMENSION_CSV, dtype=str)
    mix_sg = pd.read_csv(DERIVED / "mix_genuine_bvp_by_subgroup.csv")
    gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")
    dt = pd.read_csv(DERIVED / "bvp_downtrade_gp.csv")
    npct = pd.read_csv(DERIVED / "network_percentile.csv")

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sales, _ = load_prism_sales(df_map)
    tagged = tag_sales_with_dimension(sales, dim)
    y25 = tagged[tagged["year"] == 2025]

    print("=" * 70)
    print("POST-FIX DATA CHECK (registry line_type bug corrected)")
    print("=" * 70)

    for dist in ("UTI", "ITUK"):
        d = y25[y25["distributor_code"] == dist]
        tot = d["net_sales_value"].sum()
        ic = d[d["line_type"].isin(["genuine", "bvp"])]
        ge = ic.loc[ic["line_type"] == "genuine", "net_sales_value"].sum()
        be = ic.loc[ic["line_type"] == "bvp", "net_sales_value"].sum()
        print(f"\n{dist} CY2025 parts EUR {tot:,.0f}")
        print(f"  Overall: genuine {100*ge/tot:.1f}% | BVP {100*be/tot:.1f}% | non-catalog {100*(tot-ge-be)/tot:.1f}%")

    uti = mix_sg[(mix_sg["distributor_code"] == "UTI") & (mix_sg["year"] == 2025)]
    gq, bq = uti["genuine_qty"].sum(), uti["bvp_qty"].sum()
    print(f"\nUTI wear-basket (contestable catalog lines only, NOT overall mix):")
    print(f"  Substitution rate: BVP {100*bq/(gq+bq):.1f}% units")
    for _, r in uti.sort_values("product_subgroup").iterrows():
        t = r["genuine_qty"] + r["bvp_qty"]
        if t < 5:
            continue
        print(f"  {r['product_subgroup']:22s}  BVP {r['bvp_share_units']*100:5.1f}%  (g={r['genuine_qty']:.0f} b={r['bvp_qty']:.0f})")

    # UTI downtrade opportunity: apply network gap/u to UTI BVP qty in air+fuel
    uti25 = y25[y25["distributor_code"] == "UTI"]
    uti25 = uti25[uti25["line_type"].isin(["genuine", "bvp"])]
    for cat in ("air_filter", "fuel_filter", "oil_filter", "brake_pad"):
        g = uti25[uti25["pms_category"] == cat]
        if g.empty:
            continue
        tq = g["billed_qty"].sum()
        bq_c = g.loc[g["line_type"] == "bvp", "billed_qty"].sum()
        row = dt[dt["pms_category"] == cat]
        gap_u = float(row["genuine_gp_per_unit"].iloc[0] - row["bvp_gp_per_unit"].iloc[0]) if len(row) else 0
        opp = bq_c * gap_u
        print(f"\n  UTI {cat}: {100*bq_c/tq:.1f}% BVP units | uptick GP if all BVP->genuine @ network rates: EUR {opp:,.0f}")

    g_ut = gps[(gps["distributor_code"] == "UTI")].sort_values("year")
    print("\nUTI GPS spend per unit:")
    print(g_ut[["year", "gps_spu_eur", "uio_units"]].to_string(index=False))

    # Network GPS genuine share by value if available
    if "genuine_share_eur" in gps.columns:
        g25 = gps[gps["year"] == 2025].sort_values("genuine_share_eur", ascending=False)
        print("\nNetwork genuine share by value CY2025 (GPS):")
        for _, r in g25.head(12).iterrows():
            print(f"  {r['distributor_code']:8s}  {r['genuine_share_eur']*100:5.1f}%  spu EUR {r.get('gps_spu_eur', float('nan')):,.0f}")

    print("\nNetwork downtrade GP gap (annual, network volumes):")
    for _, r in dt.sort_values("downtrade_gp_gap_eur", ascending=False).iterrows():
        print(f"  {r['pms_category']:22s}  EUR {r['downtrade_gp_gap_eur']:>8,.0f}")


if __name__ == "__main__":
    main()
