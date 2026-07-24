#!/usr/bin/env python3
"""
P0: bvp_pn_dimension.csv (+ .parquet)
P0b: genuine_bvp_crossref.csv — OE ↔ BVP PN pairs from catalog + registry
P1: pms_capture_by_db_year.csv — genuine | bvp | total by category × distributor × year

Run from prism/:
  python scripts/build_sales_fact_from_cy.py   # if parquet missing
  python scripts/build_bvp_p0_p1.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    GENUINE_BVP_CROSSREF_CSV,
    GENUINE_BVP_CROSSREF_PARQUET,
    RAW_REFERENCE_DIR,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
    resolve_uio_path,
)
from modules.bvp_analytics import (  # noqa: E402
    ensure_part_number,
    resolve_uio_for_distributor,
)
from modules.bvp_crossref import build_genuine_bvp_crossref  # noqa: E402
from modules.bvp_dimension import build_dimension_from_catalog  # noqa: E402
from modules.data_prep import (  # noqa: E402
    EXCLUDED_CODES,
    build_uio_lookup,
    load_distributor_mapping,
    load_uio_from_excel,
)
from modules.pms_capture_config import (  # noqa: E402
    CONSUMABLE_CATS,
    CONSUMABLE_FACTOR,
    P1_CATEGORIES,
    UIO_BY_BUCKET,
    WEAR_FACTOR,
)
from modules.pms_engine import (  # noqa: E402
    CATEGORY_LABELS,
    DEFAULT_PARC_CONFIG,
    expected_addressable_services,
    expected_by_category_bucketed,
    filter_pms_by_scope,
    parc_config_for_distributor,
    pms_scope_for_distributor,
)
from modules.pms_tagging import tag_pms_sales  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

BVP_CATALOG_CANDIDATES = [
    RAW_REFERENCE_DIR / "BVP PARTS CATALOG.xlsx",
    PRISM_ROOT.parent.parent.parent / "new files" / "BVP PARTS CATALOG.xlsx",
]

DIM_CSV = DERIVED_DIR / "bvp_pn_dimension.csv"
DIM_PARQUET = DERIVED_DIR / "bvp_pn_dimension.parquet"
P1_CSV = DERIVED_DIR / "pms_capture_by_db_year.csv"
P1_PARQUET = DERIVED_DIR / "pms_capture_by_db_year.parquet"

# Category factors: modules/pms_capture_config.py (air 0.5 provisional since 2026-07-02 — flag C mitigated, IML ratio pending).


def _resolve_catalog() -> Path:
    for p in BVP_CATALOG_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("BVP PARTS CATALOG.xlsx not found under Data/raw/reference/")


def _expected_qty_for_db(
    uio_units: float,
    category: str,
    parc_cfg: dict,
    scope: str,
) -> float:
    if uio_units <= 0:
        return 0.0
    base = expected_addressable_services(uio_units, scope, parc_cfg)
    fo = (parc_cfg or {}).get("factor_overrides") or {}
    if category in fo:
        return base * float(fo[category])
    if category in CONSUMABLE_CATS:
        return base * CONSUMABLE_FACTOR.get(category, 1.0)
    return base * WEAR_FACTOR.get(category, 0.0)


# Capture actuals: ITUK pilot registry + every BVP-catalog PMS PN (filters, wear, urea).
CAPTURE_FILL_CATALOG_PMS = True


def enrich_pms_from_dimension(
    df: pd.DataFrame, df_dim: pd.DataFrame, *, fill_catalog_pms: bool = CAPTURE_FILL_CATALOG_PMS
) -> pd.DataFrame:
    """Tag PMS sales for capture build.

    fill_catalog_pms=True (default): registry + BVP catalog PMS-flagged PNs with pms_category.
    fill_catalog_pms=False: 55-PN registry only (legacy pilot lens).
    """
    return tag_pms_sales(df, df_dim, fill_catalog_pms=fill_catalog_pms)


def build_p1_capture(
    df_sales: pd.DataFrame, df_uio_agg: pd.DataFrame, df_dim: pd.DataFrame
) -> pd.DataFrame:
    """PMS capture + EUR gap by year × distributor × category × line_type."""
    parc_cfg = dict(DEFAULT_PARC_CONFIG)
    uio_lookup, uio_proxy = build_uio_lookup(df_uio_agg)

    df = ensure_part_number(df_sales)
    df = enrich_pms_from_dimension(df, df_dim)
    n_pms = int(df["is_pms"].sum())
    print(f"  PMS-tagged billing lines: {n_pms:,}", flush=True)
    df = df[df["is_pms"]].copy()
    if "is_credit_note" in df.columns:
        # Flag H (2026-07-03): a credited/returned filter or brake pad should not
        # count as an actual sale in the capture numerator.
        n_credit = int(df["is_credit_note"].sum())
        if n_credit:
            print(f"  Excluded from capture (credit note / return, SaTy CR/RE): {n_credit:,} lines", flush=True)
        df = df[~df["is_credit_note"]].copy()
    if "pms_capture_eligible" in df.columns:
        n_excl = int((~df["pms_capture_eligible"]).sum())
        if n_excl:
            print(
                f"  Excluded from capture (filter asm/kit/unknown): {n_excl:,} lines",
                flush=True,
            )
        df = df[df["pms_capture_eligible"]].copy()
    print(f"  PMS capture lines (elements + wear): {len(df):,}", flush=True)

    years = sorted(int(y) for y in df["year"].dropna().unique() if int(y) >= 2020)
    distributors = sorted(df["distributor_code"].dropna().unique())

    rows: list[dict] = []
    for year in years:
        df_y = df[df["year"] == year]
        for dist in distributors:
            if dist in EXCLUDED_CODES or dist == "UNMAPPED":
                continue
            df_d = df_y[df_y["distributor_code"] == dist]
            if df_d.empty:
                continue

            scope = pms_scope_for_distributor(dist)
            dist_parc = parc_config_for_distributor(dist, parc_cfg)

            # 2026-07-15 fix: use the real per-model-type-bucket UIO split when
            # this distributor has one (data/uio_by_model_bucket.csv), instead
            # of forcing every distributor into a single N75/LCV scope — see
            # modules/pms_engine.expected_by_category_bucketed(). Falls back to
            # the legacy single-scope calc for distributors with no bucket
            # entry, mirroring modules/pms_engine.calculate_pms_capture().
            # ITUK = 23,068 (cv_std+f_series). Flat DVLA 22,389 stays in IML §1 only.
            bucketed = (
                expected_by_category_bucketed(dist, dist_parc)
                if dist_parc.get("uio_units") is None
                else None
            )

            if bucketed is not None:
                # Real UIO split already covers every vehicle class this
                # distributor actually sells — don't drop cross-model sales
                # from the numerator by filtering to a single scope's models.
                df_d_scope = df_d
            else:
                df_d_scope = filter_pms_by_scope(df_d, scope)

            uio, uio_used_proxy, uio_source = resolve_uio_for_distributor(
                dist, year, uio_lookup, uio_proxy
            )
            if bucketed is not None:
                bucket = UIO_BY_BUCKET.get(dist, {})
                uio_report = int(round(sum(bucket.values())))
                uio_proxy_report = False
                uio_source_report = "model_bucket_split"
            else:
                uio_report = int(uio or 0)
                uio_proxy_report = uio_used_proxy
                uio_source_report = uio_source

            for cat in P1_CATEGORIES:
                if bucketed is not None and cat in bucketed:
                    exp_qty = float(bucketed[cat]["qty"])
                else:
                    exp_qty = _expected_qty_for_db(
                        float(uio or 0), cat, dist_parc, scope
                    )
                if exp_qty <= 0:
                    continue

                df_cat = df_d_scope[df_d_scope["pms_category"] == cat]
                for line_type in ("genuine", "bvp", "total"):
                    if line_type == "total":
                        sub = df_cat
                    else:
                        sub = df_cat[df_cat["pms_type"] == line_type]

                    act_qty = float(sub["billed_qty"].sum())
                    act_rev = float(sub["net_sales_value"].sum())
                    # QUOTABLE-KPI FIREWALL (2026-07-21): avg_sp=0.0 when act_qty==0
                    # makes revenue_gap_eur below read EUR0 for a distributor with ZERO
                    # actual sales in this category — the worst real outcome scoring as
                    # the best (smallest) gap. See modules/pms_engine.py's matching
                    # firewall comment and DECISIONS.md 2026-07-17. Flagged via
                    # revenue_gap_quotable below rather than silently ranked — do not
                    # sort/league-table on revenue_gap_eur without excluding
                    # revenue_gap_quotable==False rows.
                    avg_sp = (act_rev / act_qty) if act_qty > 0 else 0.0

                    # Capture is computed identically for all line_types so the
                    # parts hold together: genuine + bvp units = total units, hence
                    # genuine_rate <= total_rate always. (Previously only `total` was
                    # capped at 1.0 while genuine/bvp were not — that asymmetry made
                    # genuine capture exceed total and produced negative BVP gaps.)
                    # A rate > 1.0 is left intact and means actual sales exceed the
                    # UIO-proxy demand estimate (data-integrity flag, see header note);
                    # it is NOT clamped, since clamping would fabricate a ceiling and
                    # break the genuine/bvp/total relationship.
                    cap = act_qty / exp_qty if exp_qty > 0 else 0.0
                    gap_qty = max(exp_qty - act_qty, 0.0)

                    rows.append(
                        {
                            "year": year,
                            "distributor_code": dist,
                            "pms_category": cat,
                            "category_label": CATEGORY_LABELS.get(cat, cat),
                            "line_type": line_type,
                            "uio_units": uio_report,
                            "uio_proxy_used": uio_proxy_report,
                            "uio_source": uio_source_report,
                            "expected_qty": round(exp_qty, 1),
                            "actual_qty": round(act_qty, 1),
                            "actual_rev_eur": round(act_rev, 2),
                            "capture_rate": round(cap, 4),
                            "avg_sp_eur": round(avg_sp, 2),
                            "revenue_gap_eur": round(gap_qty * avg_sp, 2),
                            "revenue_gap_quotable": act_qty > 0,
                            "scope": "model_bucket" if bucketed is not None else scope,
                        }
                    )

    return pd.DataFrame(rows)


def main() -> int:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    catalog = _resolve_catalog()
    print(f"P0: parsing {catalog.name} …", flush=True)
    df_dim = build_dimension_from_catalog(catalog)
    from modules.aim_pn_classifier import enrich_dimension_filter_roles  # noqa: E402

    df_dim = enrich_dimension_filter_roles(df_dim)
    df_dim.to_csv(DIM_CSV, index=False)
    df_dim.to_parquet(DIM_PARQUET, index=False)
    print(f"  -> {len(df_dim):,} PNs -> {DIM_CSV}")

    pms_n = df_dim["pms_flag"].sum()
    bvp_n = (df_dim["line_type"] == "bvp").sum()
    gen_n = (df_dim["line_type"] == "genuine").sum()
    print(f"     PMS-flagged: {pms_n:,} | BVP: {bvp_n:,} | Genuine: {gen_n:,}")

    print("P0b: genuine <-> BVP cross-reference ...", flush=True)
    df_xref = build_genuine_bvp_crossref(catalog)
    df_xref.to_csv(GENUINE_BVP_CROSSREF_CSV, index=False)
    df_xref.to_parquet(GENUINE_BVP_CROSSREF_PARQUET, index=False)
    n_cat = (df_xref["pair_source"].str.startswith("catalog")).sum() if not df_xref.empty else 0
    n_reg = (df_xref["pair_source"] == "registry_model_category").sum() if not df_xref.empty else 0
    print(f"  -> {len(df_xref):,} pairs -> {GENUINE_BVP_CROSSREF_CSV.name}")
    print(f"     catalog: {n_cat:,} | registry supplement: {n_reg:,}")

    print("P1: loading sales …", flush=True)
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    if SALES_FACT_PARQUET.exists():
        df_sales, src = load_prism_sales(df_map)
    else:
        print("  sales_fact.parquet missing — run build_sales_fact_from_cy.py first", flush=True)
        return 1
    print(f"  -> {len(df_sales):,} rows from {src}")

    uio_path = resolve_uio_path()
    df_uio = load_uio_from_excel(str(uio_path))
    print(f"P1: UIO from {uio_path.name}", flush=True)

    # PMS capture supplement: genuine OE PMS PNs absent from the BVP catalog (catalog pms_category,
    # sold but uncounted) + brake_rotor. Injected into the capture dimension ONLY — the written
    # dimension above (mix/BVP/GPS) is untouched. Provenance: _OKF_assessment/_build/make_pms_supplement.py
    supp_path = Path(__file__).resolve().parents[1] / "data" / "pms_capture_supplement.csv"
    if supp_path.exists():
        df_supp = pd.read_csv(supp_path, dtype={"part_number": str})
        before_n = len(df_dim)
        df_dim = pd.concat([df_dim, df_supp], ignore_index=True)
        print(f"P1: +{len(df_supp):,} supplement PNs into capture dimension "
              f"({before_n:,} -> {len(df_dim):,}) [{supp_path.name}]", flush=True)
    else:
        print(f"P1: no capture supplement found at {supp_path}", flush=True)

    df_p1 = build_p1_capture(df_sales, df_uio, df_dim)
    df_p1.to_csv(P1_CSV, index=False)
    df_p1.to_parquet(P1_PARQUET, index=False)
    print(f"  -> {len(df_p1):,} rows -> {P1_CSV}")

    if df_p1.empty:
        print("  WARNING: P1 produced 0 rows — check PMS PN match on material numbers", flush=True)
        return 0

    ituk = df_p1[(df_p1["distributor_code"] == "ITUK") & (df_p1["line_type"] == "total")]
    if not ituk.empty:
        print("\nITUK total capture sample (oil filter):")
        oil = ituk[ituk["pms_category"] == "oil_filter"].sort_values("year")
        if not oil.empty:
            print(oil[["year", "actual_qty", "expected_qty", "capture_rate", "revenue_gap_eur"]].to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
