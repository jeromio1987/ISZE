"""Load derived BVP analytics CSVs for Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import (
    AIM_EXPOSURE_BY_DB_CSV,
    AIM_FAMILY_RISK_CSV,
    BASKET_CORRELATION_CSV,
    CAPTURE_RECOVERY_CSV,
    CAPTURE_TRAJECTORY_CSV,
    DISTRIBUTOR_GEO_CSV,
    NETWORK_PERCENTILE_CSV,
    PART_LIFECYCLE_CSV,
    PMS_OPPORTUNITY_MATRIX_CSV,
    PRICE_PREMIUM_CSV,
    REVENUE_CONCENTRATION_CSV,
    REVENUE_WATERFALL_CSV,
    SUBSTITUTION_TIMELINE_CSV,
    VOR_AIRFREIGHT_RISK_CSV,
    VOR_PROFILE_CSV,
    VOR_SEASONALITY_CSV,
    BVP_PN_DIMENSION_CSV,
    GENUINE_BVP_CROSSREF_CSV,
    SUBSTITUTION_BY_DB_YEAR_CSV,
    SUBSTITUTION_BY_PAIR_YEAR_CSV,
    DB_BENCHMARK_GROUP_CSV,
    DB_BENCHMARK_MIX_CSV,
    DB_BENCHMARK_SUBGROUP_CSV,
    DERIVED_DIR,
    GPS_SPU_BY_DB_CSV,
    GPS_SPU_BY_FAMILY_CSV,
    GPS_SPU_PMS_CSV,
    MIX_BY_FAMILY_CSV,
    MIX_BY_GROUP_CSV,
    MIX_BY_SUBGROUP_CSV,
    MIX_PMS_CSV,
    PMS_CAPTURE_BY_DB_CSV,
)
from modules.bvp_product_nav import (
    PMS_STRICT_SUBCATEGORIES,
    PRODUCT_GROUPS,
    attach_navigation_columns,
    filter_in_scope,
    group_for_subgroup,
    group_label,
    subgroup_label,
)

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"
ISZE_LIGHT = "#D6E4F0"
COLOR_GENUINE = "#1B3A6B"
COLOR_BVP = "#E87722"
COLOR_TOTAL = "#2C5AA0"

PILOT_DIST = "ITUK"


def derived_status() -> dict[str, bool]:
    files = {
        "bvp_pn_dimension": BVP_PN_DIMENSION_CSV,
        "genuine_bvp_crossref": GENUINE_BVP_CROSSREF_CSV,
        "substitution_db": SUBSTITUTION_BY_DB_YEAR_CSV,
        "substitution_pair": SUBSTITUTION_BY_PAIR_YEAR_CSV,
        "pms_capture": PMS_CAPTURE_BY_DB_CSV,
        "mix_subgroup": MIX_BY_SUBGROUP_CSV,
        "mix_group": MIX_BY_GROUP_CSV,
        "mix_family": MIX_BY_FAMILY_CSV,
        "mix_pms": MIX_PMS_CSV,
        "benchmark_subgroup": DB_BENCHMARK_SUBGROUP_CSV,
        "benchmark_group": DB_BENCHMARK_GROUP_CSV,
        "gps_db": GPS_SPU_BY_DB_CSV,
        "gps_pms": GPS_SPU_PMS_CSV,
        "aim_db": AIM_EXPOSURE_BY_DB_CSV,
        "aim_family": AIM_FAMILY_RISK_CSV,
        "pms_opportunity": PMS_OPPORTUNITY_MATRIX_CSV,
        "network_percentile": NETWORK_PERCENTILE_CSV,
        "vor_airfreight": VOR_AIRFREIGHT_RISK_CSV,
        "vor_seasonality": VOR_SEASONALITY_CSV,
        "vor_profile": VOR_PROFILE_CSV,
        "capture_trajectory": CAPTURE_TRAJECTORY_CSV,
        "part_lifecycle": PART_LIFECYCLE_CSV,
        "revenue_concentration": REVENUE_CONCENTRATION_CSV,
        "revenue_waterfall": REVENUE_WATERFALL_CSV,
        "price_premium": PRICE_PREMIUM_CSV,
        "basket_correlation": BASKET_CORRELATION_CSV,
        "substitution_timeline": SUBSTITUTION_TIMELINE_CSV,
        "capture_recovery": CAPTURE_RECOVERY_CSV,
        "distributor_geo": DISTRIBUTOR_GEO_CSV,
    }
    return {k: p.exists() for k, p in files.items()}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _enrich_pms_capture(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "pms_category" not in df.columns:
        return df
    out = df.copy()
    out["product_group"] = out["pms_category"].map(
        lambda c: group_for_subgroup(c) if pd.notna(c) else None
    )
    out["product_group_label"] = out["product_group"].map(group_label)
    out["subgroup_label"] = out["pms_category"].map(subgroup_label)
    return out[out["pms_category"].isin(PMS_STRICT_SUBCATEGORIES)]


def _fallback_mix_subgroup(mix_pms: pd.DataFrame) -> pd.DataFrame:
    """Build subgroup mix from legacy mix_pms when new CSV not built yet."""
    if mix_pms.empty:
        return pd.DataFrame()
    if mix_pms.empty:
        return pd.DataFrame()
    out = mix_pms.copy()
    out["product_group"] = out["product_subgroup"].map(group_for_subgroup)
    out["product_group_label"] = out["product_group"].map(group_label)
    out["subgroup_label"] = out["product_subgroup"].map(subgroup_label)
    return out


def load_bvp_bundle() -> dict[str, pd.DataFrame]:
    dimension = _read_csv(BVP_PN_DIMENSION_CSV)
    if not dimension.empty and "product_group" not in dimension.columns:
        dimension = attach_navigation_columns(dimension)
    if not dimension.empty:
        dimension = attach_navigation_columns(dimension) if "dashboard_scope" not in dimension.columns else dimension
        dimension = dimension[dimension["dashboard_scope"]].copy() if "dashboard_scope" in dimension.columns else dimension

    mix_subgroup = _read_csv(MIX_BY_SUBGROUP_CSV)
    mix_pms = _read_csv(MIX_PMS_CSV)
    if mix_subgroup.empty and not mix_pms.empty:
        mix_subgroup = _fallback_mix_subgroup(mix_pms)

    mix_group = _read_csv(MIX_BY_GROUP_CSV)
    bench_subgroup = _read_csv(DB_BENCHMARK_SUBGROUP_CSV)
    bench_group = _read_csv(DB_BENCHMARK_GROUP_CSV)

    return {
        "dimension": dimension,
        "pms_capture": _enrich_pms_capture(_read_csv(PMS_CAPTURE_BY_DB_CSV)),
        "mix_subgroup": mix_subgroup,
        "mix_group": mix_group,
        "mix_family": _read_csv(MIX_BY_FAMILY_CSV),
        "mix_pms": mix_pms,
        "benchmark_subgroup": bench_subgroup,
        "benchmark_group": bench_group,
        "benchmark": _read_csv(DB_BENCHMARK_MIX_CSV),
        "gps_db": _read_csv(GPS_SPU_BY_DB_CSV),
        "gps_family": _read_csv(GPS_SPU_BY_FAMILY_CSV),
        "gps_pms": _read_csv(GPS_SPU_PMS_CSV),
        "aim_db": _read_csv(AIM_EXPOSURE_BY_DB_CSV),
        "aim_family": _read_csv(AIM_FAMILY_RISK_CSV),
        "crossref": _read_csv(GENUINE_BVP_CROSSREF_CSV),
        "substitution_db": _read_csv(SUBSTITUTION_BY_DB_YEAR_CSV),
        "substitution_pair": _read_csv(SUBSTITUTION_BY_PAIR_YEAR_CSV),
        "pms_opportunity": _read_csv(PMS_OPPORTUNITY_MATRIX_CSV),
        "network_percentile": _read_csv(NETWORK_PERCENTILE_CSV),
        "vor_airfreight": _read_csv(VOR_AIRFREIGHT_RISK_CSV),
        "vor_seasonality": _read_csv(VOR_SEASONALITY_CSV),
        "vor_profile": _read_csv(VOR_PROFILE_CSV),
        "capture_trajectory": _read_csv(CAPTURE_TRAJECTORY_CSV),
        "part_lifecycle": _read_csv(PART_LIFECYCLE_CSV),
        "revenue_concentration": _read_csv(REVENUE_CONCENTRATION_CSV),
        "revenue_waterfall": _read_csv(REVENUE_WATERFALL_CSV),
        "price_premium": _read_csv(PRICE_PREMIUM_CSV),
        "basket_correlation": _read_csv(BASKET_CORRELATION_CSV),
        "substitution_timeline": _read_csv(SUBSTITUTION_TIMELINE_CSV),
        "capture_recovery": _read_csv(CAPTURE_RECOVERY_CSV),
        "distributor_geo": _read_csv(DISTRIBUTOR_GEO_CSV),
    }


def is_ready(bundle: dict[str, pd.DataFrame]) -> bool:
    if bundle.get("pms_capture") is not None and not bundle["pms_capture"].empty:
        if not bundle.get("mix_subgroup", pd.DataFrame()).empty:
            return True
        if not bundle.get("mix_pms", pd.DataFrame()).empty:
            return True
    return False


def fmt_pct(v, d=1):
    if pd.isna(v):
        return "—"
    return f"{v * 100:.{d}f}%"


def fmt_eur(v, d=0):
    if pd.isna(v):
        return "—"
    return f"€{v:,.{d}f}"


def default_group() -> str:
    return "filters"


def default_subgroup(group_id: str) -> str:
    return PRODUCT_GROUPS.get(group_id, {}).get("default_subgroup", "")
