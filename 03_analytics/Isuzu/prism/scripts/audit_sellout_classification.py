#!/usr/bin/env python3
"""Audit sell-out PN classification coverage (BVP dim vs parts_catalog)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRISM))

from modules.dealer_sales_loader import (  # noqa: E402
    UTI_DIR,
    aggregate_pn,
    load_ituk_dealer_sales,
    load_uti_part_sales,
)
from modules.dealer_sellout_analytics import attach_pn_master, load_dimension_and_xref  # noqa: E402
from modules.fig_key_catalog import category_hint_for_pn, load_catalog_index  # noqa: E402


def _ascii(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")


def load_sellout(dist: str) -> pd.DataFrame:
    if dist == "ITUK":
        raw = load_ituk_dealer_sales(2025)
        return raw.groupby("part_number", as_index=False)["qty_year"].sum()
    path = UTI_DIR / "UTIPartSales_2025-12_YTD.xlsx"
    df, _ = load_uti_part_sales(path if path.exists() else None)
    return aggregate_pn(df, "qty_ytd").rename(columns={"qty": "qty_year"})


def main() -> int:
    dim, xref, desc = load_dimension_and_xref()
    cat = load_catalog_index()

    for dist in ("ITUK", "UTI"):
        sell = load_sellout(dist)
        sell = attach_pn_master(sell, dim, desc, xref)
        total_qty = float(sell["qty_year"].sum())

        pms_sub = sell["product_subgroup"].notna() & (sell["product_subgroup"].astype(str).str.strip() != "")
        pms_cat = sell["pms_category"].notna() & (sell["pms_category"].astype(str).str.strip() != "")
        report = sell["report_subgroup"].astype(str) != "(unclassified)"
        pr00_only = sell["taxonomy_level"].astype(str) == "pr00_group"

        cat_pms = []
        cat_fk = []
        hints = []
        for _, r in sell.iterrows():
            pn = str(r["part_number"]).strip().lstrip("0")
            row = cat.loc[pn] if not cat.empty and pn in cat.index else None
            cat_pms.append(
                row is not None
                and pd.notna(row.get("pms_category"))
                and str(row.get("pms_category")).strip()
            )
            cat_fk.append(
                row is not None
                and pd.notna(row.get("fig_key"))
                and str(row.get("fig_key")).strip()
                and str(row.get("fig_key")) != "unmapped"
            )
            hints.append(category_hint_for_pn(pn, row, r.get("description")))

        sell["_cat_pms"] = pd.Series(cat_pms, index=sell.index, dtype=bool)
        sell["_cat_fk"] = pd.Series(cat_fk, index=sell.index, dtype=bool)
        sell["_hint"] = hints

        def qty_share(mask):
            return float(sell.loc[mask, "qty_year"].sum()) / total_qty if total_qty else 0

        print("=" * 70)
        print(f"{dist} sell-out CY2025 — {len(sell):,} unique PNs, qty {total_qty:,.0f}")
        print("=" * 70)
        print(f"  Resolved PMS subgroup:     {qty_share(pms_sub)*100:5.1f}% qty  ({pms_sub.sum():,} PNs)")
        print(f"  Resolved pms_category:     {qty_share(pms_cat)*100:5.1f}% qty")
        print(f"  Report bucket (not uncl.): {qty_share(report)*100:5.1f}% qty")
        print(f"  PR00 coarse only:          {qty_share(pr00_only)*100:5.1f}% qty")
        if "taxonomy_source" in sell.columns:
            print("  Sources:", sell.loc[pms_sub, "taxonomy_source"].value_counts().to_dict())
        print(f"  Catalog pms_category:      {qty_share(sell['_cat_pms'])*100:5.1f}% qty")
        print(f"  Catalog fig_key:           {qty_share(sell['_cat_fk'])*100:5.1f}% qty")
        un_hint = sell["_hint"].str.contains("Unclassified", na=False)
        print(f"  Keyword hint unclassified: {qty_share(un_hint)*100:5.1f}% qty")

        # Top unclassified by qty (BVP dim)
        un = sell[~report].sort_values("qty_year", ascending=False).head(10)
        print("\n  Top 10 still (unclassified) by qty:")
        for _, r in un.iterrows():
            pn = r["part_number"]
            pn_n = str(pn).strip().lstrip("0")
            row = cat.loc[pn_n] if not cat.empty and pn_n in cat.index else None
            fk = row.get("fig_key") if row is not None else "—"
            pc = row.get("pms_category") if row is not None else "—"
            pr00 = row.get("pr00_level3_type") if row is not None else "—"
            print(
                f"    {pn}  qty {r['qty_year']:>8,.0f}  "
                f"fig={fk}  cat_pms={pc}  pr00_l3={pr00}  "
                f"hint={_ascii(str(r['_hint'])[:50])}"
            )

        # fuel filter vs filter asm price check
        filt = sell[sell["description"].astype(str).str.contains("FILTER", case=False, na=False)]
        filt = filt.copy()
        filt["desc_u"] = filt["description"].astype(str).upper()
        fuel = filt[filt["desc_u"].str.contains("FUEL")]
        asm = filt[filt["desc_u"].str.contains("ASSY|ASSEMBLY|ASM")]
        print(f"\n  FILTER lines: fuel {fuel['qty_year'].sum():,.0f} qty, assembly {asm['qty_year'].sum():,.0f} qty")
        print(f"    fuel w/ BVP subgroup: {(fuel['product_subgroup']=='fuel_filter').sum()} PNs labeled fuel_filter")
        print(f"    asm w/ BVP subgroup:  {(asm['product_subgroup'].notna() & (asm['product_subgroup']!='')).sum()} PNs any subgroup")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
