#!/usr/bin/env python3
"""
P4: GPS / spend-per-unit by distributor and by BVP family (+ PMS slice).
P5: AIM pricing-risk × BVP family × distributor (description join to AIM Parts Master).

Run after build_bvp_p0_p1.py and build_bvp_p2_mix.py.

  python scripts/build_bvp_p4_p5.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    AIM_WORKBOOK_CANDIDATES,
    BVP_PN_DIMENSION_CSV,
    DERIVED_DIR,
    SALES_FACT_PARQUET,
    resolve_mapping_path,
    resolve_uio_path,
)
from modules.bvp_analytics import (  # noqa: E402
    ensure_part_number,
    resolve_uio_for_distributor,
    tag_sales_with_dimension,
)
from modules.data_prep import (  # noqa: E402
    EXCLUDED_CODES,
    build_uio_lookup,
    get_distributor_metadata,
    load_distributor_mapping,
    load_uio_from_excel,
)
from modules.gps_engine import calculate_spend_per_unit  # noqa: E402
from modules.gps_warranty import apply_warranty_to_spu_frame  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

GPS_SPU_DB_CSV = DERIVED_DIR / "gps_spu_by_distributor.csv"
GPS_SPU_FAMILY_CSV = DERIVED_DIR / "gps_spu_by_family.csv"
GPS_SPU_PMS_CSV = DERIVED_DIR / "gps_spu_pms.csv"
AIM_FAMILY_RISK_CSV = DERIVED_DIR / "aim_bvp_family_risk.csv"
AIM_DB_YEAR_CSV = DERIVED_DIR / "aim_exposure_by_db_year.csv"

# BVP catalog families → AIM Category L1 (for family-level risk weighting)
FAMILY_TO_AIM_L1: dict[str, list[str]] = {
    "PMS_Filters": ["Filters", "Engine", "Fuel System"],
    "Brakes": ["Brakes"],
    "Clutch_Driveline": ["Clutch", "Transmission", "Driveline"],
    "Suspension_Chassis": ["Suspension", "Chassis", "Axle"],
    "Electrical": ["Electrical"],
    "Belts_Cooling": ["Engine", "Cooling"],
    "Cab_Misc": ["Cab", "Body"],
    "Other": [],
}

RISK_FLAGS = {
    "must review",
    "commercial review",
    "class distortion",
    "competitive overpricing",
    "margin leakage",
}


def _resolve_aim() -> Path:
    for p in AIM_WORKBOOK_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(
        "AIM_CY2025_Analysis.xlsx not found. Expected one of:\n"
        + "\n".join(f"  - {p}" for p in AIM_WORKBOOK_CANDIDATES)
    )


def _norm_desc(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.upper()


def _traffic_light(spu: float) -> str:
    if pd.isna(spu):
        return "unknown"
    if spu > 150:
        return "green"
    if spu >= 50:
        return "amber"
    return "red"


def load_aim_parts_master(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Parts Master", header=1)
    df.columns = [str(c).strip() for c in df.columns]
    desc_col = next(c for c in df.columns if c.lower().startswith("description"))
    rev_col = next(c for c in df.columns if "revenue" in c.lower())
    gp_col = next(c for c in df.columns if c == "GP%" or c.startswith("GP%"))
    out = pd.DataFrame(
        {
            "description_norm": _norm_desc(df[desc_col]),
            "aim_category_l1": df.get("Category L1", df.get("Category_L1")),
            "aim_demand_type": df.get("Demand Type", df.get("Demand_Type")),
            "aim_bucket": df.get("Bucket"),
            "aim_pricing_risk": df.get("Pricing Risk", df.get("Pricing_Risk")),
            "aim_strategic_score": pd.to_numeric(
                df.get("Strategic Score", df.get("Strategic_Score")), errors="coerce"
            ),
            "aim_revenue_network": pd.to_numeric(df[rev_col], errors="coerce").fillna(0),
            "aim_gp_pct": pd.to_numeric(df[gp_col], errors="coerce"),
        }
    )
    out = out[out["description_norm"] != ""].drop_duplicates("description_norm")
    pr = out["aim_pricing_risk"].fillna("").astype(str).str.strip().str.lower()
    out["aim_high_risk"] = pr.isin(RISK_FLAGS) | pr.str.contains("review", na=False)
    out["aim_strategic"] = out["aim_bucket"].fillna("").astype(str).str.contains(
        "Strategic", case=False, na=False
    )
    return out


def build_p4(
    df_sales: pd.DataFrame,
    df_dim: pd.DataFrame,
    df_uio: pd.DataFrame,
    df_meta: pd.DataFrame,
) -> None:
    uio_lookup, uio_proxy = build_uio_lookup(df_uio)
    years = sorted(int(y) for y in df_sales["year"].dropna().unique() if 2020 <= int(y) <= 2030)

    # Overall SPU (reuse gps_engine)
    spu_frames = []
    for year in years:
        spu = calculate_spend_per_unit(
            df_sales,
            df_uio,
            df_meta,
            year=year,
            year_type="calendar",
            include_credit_notes=True,
            exclude_warranty=False,
        )
        if spu.empty:
            continue
        spu["year"] = year
        spu_frames.append(spu)

    if spu_frames:
        spu_all = pd.concat(spu_frames, ignore_index=True)
        spu_all["traffic_light"] = spu_all["spend_per_unit_eur"].map(_traffic_light)
        # ITUK UIO source flag
        spu_all["uio_source"] = spu_all.apply(
            lambda r: resolve_uio_for_distributor(
                r["distributor_code"], int(r["year"]), uio_lookup, uio_proxy
            )[2],
            axis=1,
        )
        spu_all = apply_warranty_to_spu_frame(spu_all)
        cols = [
            "year",
            "distributor_code",
            "country",
            "region",
            "total_sales_eur",
            "warranty_parts_eur",
            "sales_ex_warranty_eur",
            "uio_units",
            "spend_per_unit_eur",
            "spend_per_unit_ex_warranty_eur",
            "uio_proxy",
            "uio_source",
            "traffic_light",
            "warranty_data_gap",
        ]
        spu_all[cols].to_csv(GPS_SPU_DB_CSV, index=False)
        print(f"P4: {len(spu_all)} rows -> {GPS_SPU_DB_CSV}")

    tagged = tag_sales_with_dimension(df_sales, df_dim)
    tagged = tagged[~tagged["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]

    fam_rows: list[dict] = []
    pms_rows: list[dict] = []

    for year in years:
        df_y = tagged[tagged["year"] == year]
        for dist in df_y["distributor_code"].dropna().unique():
            df_d = df_y[df_y["distributor_code"] == dist]
            uio_units, uio_is_proxy, uio_src = resolve_uio_for_distributor(
                dist, year, uio_lookup, uio_proxy
            )
            if not uio_units:
                continue

            for family in df_d["product_family"].dropna().unique():
                df_f = df_d[df_d["product_family"] == family]
                for line_type in ("genuine", "bvp", "all"):
                    sub = df_f if line_type == "all" else df_f[df_f["line_type"] == line_type]
                    rev = float(sub["net_sales_value"].sum())
                    fam_rows.append(
                        {
                            "year": year,
                            "distributor_code": dist,
                            "product_family": family,
                            "line_type": line_type,
                            "net_sales_eur": round(rev, 2),
                            "uio_units": uio_units,
                            "uio_proxy_used": uio_is_proxy,
                            "uio_source": uio_src,
                            "spu_eur": round(rev / uio_units, 2) if uio_units else np.nan,
                        }
                    )

            pms_mask = df_d["pms_flag"]
            if pms_mask.dtype == object:
                pms_mask = pms_mask.astype(str).str.lower().isin(("true", "1", "yes"))
            pms = df_d[pms_mask]
            for cat in pms["pms_category"].dropna().unique():
                df_c = pms[pms["pms_category"] == cat]
                for line_type in ("genuine", "bvp", "all"):
                    sub = df_c if line_type == "all" else df_c[df_c["line_type"] == line_type]
                    rev = float(sub["net_sales_value"].sum())
                    pms_rows.append(
                        {
                            "year": year,
                            "distributor_code": dist,
                            "pms_category": cat,
                            "line_type": line_type,
                            "net_sales_eur": round(rev, 2),
                            "uio_units": uio_units,
                            "uio_proxy_used": uio_is_proxy,
                            "uio_source": uio_src,
                            "spu_eur": round(rev / uio_units, 2) if uio_units else np.nan,
                        }
                    )

    pd.DataFrame(fam_rows).to_csv(GPS_SPU_FAMILY_CSV, index=False)
    pd.DataFrame(pms_rows).to_csv(GPS_SPU_PMS_CSV, index=False)
    print(f"P4: {len(fam_rows)} rows -> {GPS_SPU_FAMILY_CSV}")
    print(f"P4: {len(pms_rows)} rows -> {GPS_SPU_PMS_CSV}")


def build_p5(
    df_sales: pd.DataFrame,
    df_dim: pd.DataFrame,
    df_aim: pd.DataFrame,
) -> None:
    df = ensure_part_number(df_sales.copy())
    if "description" not in df.columns:
        df["description_norm"] = ""
    else:
        df["description_norm"] = _norm_desc(df["description"])

    df = df[~df["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]
    df = df.merge(df_aim, on="description_norm", how="left")
    df["aim_matched"] = df["aim_category_l1"].notna()

    # Tag BVP dimension on all sales lines (left join — not only catalog)
    dim = df_dim.drop_duplicates("part_number")
    dim["_pn"] = dim["part_number"].astype(str).str.strip().str.lstrip("0")
    df["_pn"] = df["part_number"].astype(str).str.strip().str.lstrip("0")
    df = df.merge(
        dim[["_pn", "product_family", "line_type", "pms_flag", "pms_category"]],
        on="_pn",
        how="left",
    )

    # P5a: distributor × year AIM exposure (catalog-agnostic)
    db_rows: list[dict] = []
    for (year, dist), g in df.groupby(["year", "distributor_code"]):
        rev = g["net_sales_value"].sum()
        matched = g[g["aim_matched"]]
        rev_m = matched["net_sales_value"].sum()
        db_rows.append(
            {
                "year": int(year),
                "distributor_code": dist,
                "net_sales_eur": round(rev, 2),
                "aim_matched_rev_eur": round(rev_m, 2),
                "aim_match_rate_rev": round(rev_m / rev, 4) if rev else np.nan,
                "high_risk_rev_eur": round(
                    matched.loc[
                        matched["aim_high_risk"].fillna(False), "net_sales_value"
                    ].sum(),
                    2,
                ),
                "high_risk_rev_pct": round(
                    matched.loc[
                        matched["aim_high_risk"].fillna(False), "net_sales_value"
                    ].sum()
                    / rev_m,
                    4,
                )
                if rev_m
                else np.nan,
                "strategic_rev_eur": round(
                    matched.loc[
                        matched["aim_strategic"].fillna(False), "net_sales_value"
                    ].sum(),
                    2,
                ),
            }
        )
    pd.DataFrame(db_rows).to_csv(AIM_DB_YEAR_CSV, index=False)
    print(f"P5: {len(db_rows)} rows -> {AIM_DB_YEAR_CSV}")

    # P5b: BVP catalog families × AIM risk (genuine|bvp in catalog only)
    cat = df[df["product_family"].notna() & df["line_type"].isin(["genuine", "bvp"])].copy()
    fam_rows: list[dict] = []
    for (year, dist, family), g in cat.groupby(
        ["year", "distributor_code", "product_family"]
    ):
        rev = g["net_sales_value"].sum()
        gen = g[g["line_type"] == "genuine"]["net_sales_value"].sum()
        bvp = g[g["line_type"] == "bvp"]["net_sales_value"].sum()
        scoped = gen + bvp
        risk_rev = g.loc[g["aim_high_risk"].fillna(False), "net_sales_value"].sum()
        fam_rows.append(
            {
                "year": int(year),
                "distributor_code": dist,
                "product_family": family,
                "aim_l1_hints": "|".join(FAMILY_TO_AIM_L1.get(family, [])),
                "genuine_eur": round(gen, 2),
                "bvp_eur": round(bvp, 2),
                "bvp_share_eur": round(bvp / scoped, 4) if scoped else np.nan,
                "catalog_sales_eur": round(scoped, 2),
                "aim_high_risk_rev_eur": round(risk_rev, 2),
                "aim_high_risk_rev_pct": round(risk_rev / scoped, 4) if scoped else np.nan,
                "lines": len(g),
            }
        )

    fam_df = pd.DataFrame(fam_rows)
    if not fam_df.empty:
        med = fam_df.groupby(["year", "product_family"])["aim_high_risk_rev_pct"].median()
        fam_df = fam_df.merge(
            med.reset_index().rename(
                columns={"aim_high_risk_rev_pct": "network_median_risk_pct"}
            ),
            on=["year", "product_family"],
            how="left",
        )
        fam_df["vs_network_risk_pp"] = (
            fam_df["aim_high_risk_rev_pct"] - fam_df["network_median_risk_pct"]
        ) * 100

    fam_df.to_csv(AIM_FAMILY_RISK_CSV, index=False)
    print(f"P5: {len(fam_df)} rows -> {AIM_FAMILY_RISK_CSV}")


def main() -> int:
    if not SALES_FACT_PARQUET.exists() or not BVP_PN_DIMENSION_CSV.exists():
        print("Run build_sales_fact_from_cy.py and build_bvp_p0_p1.py first")
        return 1

    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df_meta = get_distributor_metadata(df_map)
    df_sales, src = load_prism_sales(df_map)
    df_dim = pd.read_csv(BVP_PN_DIMENSION_CSV, dtype=str)
    df_uio = load_uio_from_excel(str(resolve_uio_path()))
    print(f"P4/P5: sales {len(df_sales):,} from {src}")

    build_p4(df_sales, df_dim, df_uio, df_meta)

    aim_path = _resolve_aim()
    print(f"P5: AIM from {aim_path.name}")
    df_aim = load_aim_parts_master(aim_path)
    build_p5(df_sales, df_dim, df_aim)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
