#!/usr/bin/env python3
"""Audit: do all PMS parts have a fig key in parts_catalog_dimension?"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR  # noqa: E402
from modules.bvp_analytics import normalize_pn_value  # noqa: E402
from modules.fig_key_catalog import fig_key_for_category, load_taxonomy  # noqa: E402
from modules.pms_engine import PMS_PN_REGISTRY, PHASE1_CATEGORIES  # noqa: E402

DER = DERIVED_DIR


def _pn_norm(s) -> str:
    n = normalize_pn_value(s) or ""
    return n.lstrip("0") or n


def main() -> int:
    tax = load_taxonomy()
    pms_fig_keys = set((tax.get("pms_fig_keys") or {}).keys())

    cat = pd.read_csv(DER / "parts_catalog_dimension.csv", dtype=str)
    cat["_pn"] = cat["part_number"].map(_pn_norm)
    cat_idx = cat.drop_duplicates("_pn").set_index("_pn")

    dim = pd.read_csv(DER / "bvp_pn_dimension.csv", dtype=str)
    xref = pd.read_csv(DER / "genuine_bvp_crossref.csv", dtype=str)

    def catalog_fig(pn: str) -> str | None:
        n = _pn_norm(pn)
        if n not in cat_idx.index:
            return None
        fk = cat_idx.loc[n, "fig_key"]
        if pd.isna(fk) or not str(fk).strip():
            return None
        return str(fk).strip()

    print("=" * 60)
    print("PMS FIG KEYS (EPC taxonomy — filter PMS only)")
    print("=" * 60)
    for fk, meta in (tax.get("pms_fig_keys") or {}).items():
        print(f"  {fk}: {meta.get('label')} -> {meta.get('pms_category')}")

  # ── 55-PN registry ─────────────────────────────────────────────
    reg_rows = []
    for pn, meta in PMS_PN_REGISTRY.items():
        pn_n = str(pn).zfill(10)
        exp_fk = fig_key_for_category(tax, meta["category"])
        got_fk = catalog_fig(pn)
        reg_rows.append(
            {
                "part_number": pn_n,
                "category": meta["category"],
                "type": meta["type"],
                "model": meta["model"],
                "expected_fig_key": exp_fk,
                "catalog_fig_key": got_fk,
            }
        )
    reg = pd.DataFrame(reg_rows)

    has_default = reg["expected_fig_key"].notna()
    matched = has_default & (reg["catalog_fig_key"] == reg["expected_fig_key"])
    missing_fk = has_default & reg["catalog_fig_key"].isna()
    wrong_fk = has_default & reg["catalog_fig_key"].notna() & (
        reg["catalog_fig_key"] != reg["expected_fig_key"]
    )
    no_epc_fig = ~has_default

    print("\n" + "=" * 60)
    print("PMS_PN_REGISTRY (ITUK pilot + LCV extensions)")
    print("=" * 60)
    print(f"Total PNs: {len(reg)}")
    print(f"  Filter categories with EPC fig key: {has_default.sum()}")
    print(f"  Fig key present and correct: {matched.sum()}")
    print(f"  Missing fig key (should have one): {missing_fk.sum()}")
    print(f"  Wrong fig key: {wrong_fk.sum()}")
    print(f"  Wear/clutch - no EPC fig in taxonomy yet: {no_epc_fig.sum()}")
    if missing_fk.any():
        print("\nMISSING fig_key:")
        print(reg[missing_fk].to_string(index=False))
    if wrong_fk.any():
        print("\nWRONG fig_key:")
        print(reg[wrong_fk].to_string(index=False))
    if no_epc_fig.any():
        print("\nNo default EPC fig key (by category):")
        print(reg[no_epc_fig].groupby("category").size().to_string())

    # ── BVP catalog PMS-flagged ────────────────────────────────────
    pms_dim = dim[dim["pms_flag"].astype(str).str.lower().isin(["true", "1"])]
    pms_dim = pms_dim.copy()
    pms_dim["_fk"] = pms_dim["part_number"].map(lambda p: catalog_fig(p) is not None)

    print("\n" + "=" * 60)
    print("BVP CATALOG - pms_flag=true")
    print("=" * 60)
    print(f"Total PMS-flagged PNs: {len(pms_dim)}")
    print(f"  With fig_key: {pms_dim['_fk'].sum()}")
    print(f"  Without fig_key: {(~pms_dim['_fk']).sum()}")
    by_sub = (
        pms_dim.groupby("product_subgroup", dropna=False)
        .agg(total=("part_number", "count"), with_fig=("_fk", "sum"))
        .reset_index()
    )
    by_sub["without_fig"] = by_sub["total"] - by_sub["with_fig"]
    print("\nBy subgroup (no fig_key count):")
    print(by_sub.sort_values("without_fig", ascending=False).to_string(index=False))

    # ── Crossref PMS pairs ─────────────────────────────────────────
    pms_xref = xref[xref["pms_flag"].astype(str).str.lower().isin(["true", "1"])]
    print("\n" + "=" * 60)
    print("GENUINE-BVP CROSSREF - pms_flag=true pairs")
    print("=" * 60)
    print(f"Pairs: {len(pms_xref)}")
    for label, col in [("genuine_pn", "genuine_pn"), ("bvp_pn", "bvp_pn")]:
        pns = pms_xref[col].dropna().unique()
        ok = sum(catalog_fig(p) is not None for p in pns)
        print(f"  {label}: {len(pns)} unique, with fig_key: {ok}, missing: {len(pns) - ok}")

    # ── CY2025 sales lens ────────────────────────────────────────────
    sf = pd.read_parquet(DER / "sales_fact.parquet")
    if "line_kind" in sf.columns:
        sf = sf[sf["line_kind"] == "part"]
    sf = sf[sf["year"] == 2025].copy()
    sf["_pn"] = sf["part_number"].map(_pn_norm)

    reg_pns = {_pn_norm(p) for p in reg["part_number"]}
    sf_reg = sf[sf["_pn"].isin(reg_pns)]
    print("\n" + "=" * 60)
    print("CY2025 BILLING — registry PNs only")
    print("=" * 60)
    print(f"Lines: {len(sf_reg):,}  EUR: {sf_reg['net_sales_value'].sum():,.0f}")

    cat_merge = cat[["_pn", "fig_key", "pms_category"]].drop_duplicates("_pn")
    m = sf.merge(cat_merge, on="_pn", how="left")
    m["fig_key"] = m["fig_key"].fillna("unmapped")

    pms_cats = set(PHASE1_CATEGORIES) | {
        "urea_filter",
        "brake_shoe",
        "clutch_disc",
        "clutch_pressure_plate",
    }
    on_fk = m[m["fig_key"].isin(pms_fig_keys)]
    on_cat = m[m["pms_category"].isin(pms_cats)]
    on_reg = m[m["_pn"].isin(reg_pns)]

    print("\n" + "=" * 60)
    print("CY2025 BILLING — fig-key coverage (network)")
    print("=" * 60)
    print(f"Lines on 4 PMS fig keys: {len(on_fk):,}  EUR {on_fk['net_sales_value'].sum():,.0f}")
    print(f"Lines with pms_category in catalog: {len(on_cat):,}  EUR {on_cat['net_sales_value'].sum():,.0f}")
    print(f"Lines on registry PNs: {len(on_reg):,}  EUR {on_reg['net_sales_value'].sum():,.0f}")
    reg_no_fk = on_reg[on_reg["fig_key"] == "unmapped"]
    print(f"Registry PN lines WITHOUT fig_key: {len(reg_no_fk):,}  EUR {reg_no_fk['net_sales_value'].sum():,.0f}")

    # BVP PMS-flagged high revenue without fig key
    no_fk_pns = pms_dim.loc[~pms_dim["_fk"], "part_number"].tolist()
    sf_nf = sf[sf["_pn"].isin([_pn_norm(p) for p in no_fk_pns])]
    if not sf_nf.empty:
        top = sf_nf.groupby("_pn")["net_sales_value"].sum().sort_values(ascending=False).head(15)
        print("\nTop CY2025 EUR — BVP PMS-flagged but NO fig_key:")
        for pn, eur in top.items():
            row = pms_dim[pms_dim["part_number"].map(_pn_norm) == pn].iloc[0]
            print(f"  {pn:>12}  EUR {eur:>12,.0f}  {row['product_subgroup']}")

    # Summary verdict
    print("\n" + "=" * 60)
    print("VERDICT")
    print("=" * 60)
    filter_complete = missing_fk.sum() == 0 and wrong_fk.sum() == 0
    print(
        "Filter PMS (oil/fuel/air/urea) in 55-PN registry: "
        + ("COMPLETE fig-key mapping" if filter_complete else "GAPS — see above")
    )
    print(
        f"Wear/clutch registry PNs ({no_epc_fig.sum()}): "
        "no EPC fig keys in taxonomy yet — use pms_category / registry, not fig key"
    )
    print(
        f"BVP catalog PMS universe ({len(pms_dim)} PNs): "
        f"only {pms_dim['_fk'].sum()} have fig_key — expand taxonomy + overrides for full BVP PMS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
