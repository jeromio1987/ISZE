"""
PRISM path configuration — reads ISZE/paths.yaml with legacy fallbacks.

Layout (numbered, preferred):
  ISZE_ROOT     = …/ISZE
  DATA_ROOT     = …/ISZE/01_data
  DERIVED_DIR   = …/ISZE/01_data/derived
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

_ROOT = Path(__file__).parent.resolve()


def _find_isze_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "FACTS.md").is_file() and (candidate / "paths.yaml").is_file():
            return candidate
    raise FileNotFoundError(
        "ISZE root not found (expected FACTS.md + paths.yaml in an ancestor of prism/)"
    )


ISZE_ROOT = _find_isze_root(_ROOT)


@lru_cache(maxsize=1)
def _paths_doc() -> dict:
    path = ISZE_ROOT / "paths.yaml"
    if yaml is None or not path.is_file():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _resolve_folder(key: str, legacy: str) -> Path:
    mapped = (_paths_doc().get("folders") or {}).get(key, legacy)
    preferred = ISZE_ROOT / mapped
    legacy_path = ISZE_ROOT / legacy
    if preferred.exists():
        return preferred
    if legacy_path.exists():
        return legacy_path
    return preferred


def _resolve_path(*parts: str, legacy: Optional[str] = None) -> Path:
    preferred = ISZE_ROOT.joinpath(*parts)
    if preferred.exists():
        return preferred
    if legacy:
        legacy_path = ISZE_ROOT / legacy
        if legacy_path.exists():
            return legacy_path
    return preferred


DATA_ROOT = _resolve_folder("data", "Data")


def _resolve_data_subfolder(key: str) -> Path:
    """Numbered 01_data subfolder (paths.yaml data_subfolders) with legacy/junction fallback."""
    entry = (_paths_doc().get("data_subfolders") or {}).get(key) or {}
    numbered = entry.get("numbered")
    legacy = entry.get("legacy")
    if numbered:
        path = DATA_ROOT / numbered
        if path.exists():
            return path
    if legacy:
        path = DATA_ROOT / legacy
        if path.exists():
            return path
    if numbered:
        return DATA_ROOT / numbered
    if legacy:
        return DATA_ROOT / legacy
    return DATA_ROOT / key


DERIVED_DIR = _resolve_data_subfolder("derived")
_raw_root = _resolve_data_subfolder("raw")
RAW_SALES_DIR = _raw_root / "sales"
RAW_REFERENCE_DIR = _raw_root / "reference"
MODELS_DIR = _resolve_data_subfolder("models")
PLANNING_DIR = _resolve_data_subfolder("planning")
DASHBOARDS_JSON_DIR = _resolve_data_subfolder("dashboards")
GPT_SAFE_DIR = _resolve_data_subfolder("gpt_safe")
INBOX_DIR = _resolve_data_subfolder("inbox")

# Folder roots (numbered preferred, legacy fallback via _resolve_folder)
DASHBOARDS_DIR = _resolve_folder("dashboards", "Dashboards")
TOOLS_DIR = _resolve_folder("tools", "Tools")
MEMORY_DIR = _resolve_folder("memory", "memory")

# Common subpaths
DATA_BUILD_DIR = _resolve_data_subfolder("build")
EXPORTS_DIR = _resolve_data_subfolder("exports")
RAW_DEALER_SALES_DIR = _raw_root / "dealer_sales"
BRIEFS_DIR = MEMORY_DIR / "briefs"

# Tool entrypoints
TENDER_MONITOR_DIR = TOOLS_DIR / "ISZE_Tender_Monitor_Install"
AUTODOC_SCRAPER_DIR = TOOLS_DIR / "autodoc_scraper"

PRISM_DATA_DIR = _ROOT / "data"
LEGACY_ISUZU_DATA = _ROOT.parent / "data"

# Canonical derived sales (build via scripts/build_sales_fact_from_cy.py or Phase 1 export)
SALES_FACT_PARQUET = DERIVED_DIR / "sales_fact.parquet"
SALES_FACT_CSV = DERIVED_DIR / "sales_fact.csv"
SALES_FACT_MONTHLY_CSV = DERIVED_DIR / "sales_fact_monthly.csv"

BVP_PN_DIMENSION_CSV = DERIVED_DIR / "bvp_pn_dimension.csv"
BVP_PN_DIMENSION_PARQUET = DERIVED_DIR / "bvp_pn_dimension.parquet"
GENUINE_BVP_CROSSREF_CSV = DERIVED_DIR / "genuine_bvp_crossref.csv"
GENUINE_BVP_CROSSREF_PARQUET = DERIVED_DIR / "genuine_bvp_crossref.parquet"
BVP_ADDRESSABLE_BASKET_CSV = DERIVED_DIR / "bvp_addressable_basket.csv"
SALES_WITH_CROSSREF_PARQUET = DERIVED_DIR / "sales_with_crossref.parquet"
SUBSTITUTION_BY_PAIR_YEAR_CSV = DERIVED_DIR / "substitution_by_pair_year.csv"
SUBSTITUTION_BY_DB_YEAR_CSV = DERIVED_DIR / "substitution_by_db_year.csv"
PMS_CAPTURE_BY_DB_CSV = DERIVED_DIR / "pms_capture_by_db_year.csv"
PMS_CAPTURE_BY_DB_PARQUET = DERIVED_DIR / "pms_capture_by_db_year.parquet"
PMS_SUMMARY_BY_DB_CSV = DERIVED_DIR / "pms_summary_by_db.csv"
BVP_CATALOG_XLSX = RAW_REFERENCE_DIR / "BVP PARTS CATALOG.xlsx"
MIX_BY_FAMILY_CSV = DERIVED_DIR / "mix_genuine_bvp_by_family.csv"
MIX_BY_SUBGROUP_CSV = DERIVED_DIR / "mix_genuine_bvp_by_subgroup.csv"
MIX_BY_GROUP_CSV = DERIVED_DIR / "mix_genuine_bvp_by_group.csv"
MIX_PMS_CSV = DERIVED_DIR / "mix_genuine_bvp_pms.csv"
DB_BENCHMARK_MIX_CSV = DERIVED_DIR / "db_benchmark_mix.csv"
DB_BENCHMARK_SUBGROUP_CSV = DERIVED_DIR / "db_benchmark_mix_subgroup.csv"
DB_BENCHMARK_GROUP_CSV = DERIVED_DIR / "db_benchmark_mix_group.csv"
GPS_SPU_BY_DB_CSV = DERIVED_DIR / "gps_spu_by_distributor.csv"
GPS_SPU_BY_FAMILY_CSV = DERIVED_DIR / "gps_spu_by_family.csv"
GPS_SPU_PMS_CSV = DERIVED_DIR / "gps_spu_pms.csv"
GPS_MODEL_TARGETS_CSV = PRISM_DATA_DIR / "gps_model_targets.csv"
PARTS_CATALOG_DIMENSION_CSV = DERIVED_DIR / "parts_catalog_dimension.csv"
PARTS_CATALOG_DIMENSION_PARQUET = DERIVED_DIR / "parts_catalog_dimension.parquet"
PR00_CLASSIFICATION_CSV = DERIVED_DIR / "pr00_classification.csv"
FIG_KEY_TAXONOMY_YAML = PRISM_DATA_DIR / "fig_key_taxonomy.yaml"
FIG_KEY_PN_OVERRIDES_CSV = PRISM_DATA_DIR / "fig_key_pn_overrides.csv"
AIM_FAMILY_RISK_CSV = DERIVED_DIR / "aim_bvp_family_risk.csv"
AIM_EXPOSURE_BY_DB_CSV = DERIVED_DIR / "aim_exposure_by_db_year.csv"
AIM_GPS_MATRIX_CSV = DERIVED_DIR / "aim_gps_matrix.csv"
AIM_PN_CLASSIFICATION_CSV = DERIVED_DIR / "aim_pn_classification.csv"
COMPETITIVENESS_AUTODOC_RISK_CSV = DERIVED_DIR / "competitiveness_autodoc_risk.csv"
MISLABELLED_SKU_AUDIT_CSV = DERIVED_DIR / "mislabelled_sku_audit.csv"
PMS_OPPORTUNITY_MATRIX_CSV = DERIVED_DIR / "pms_opportunity_matrix.csv"
NETWORK_PERCENTILE_CSV = DERIVED_DIR / "network_percentile.csv"
VOR_AIRFREIGHT_RISK_CSV = DERIVED_DIR / "vor_airfreight_risk.csv"
VOR_SEASONALITY_CSV = DERIVED_DIR / "vor_seasonality.csv"
VOR_PROFILE_CSV = DERIVED_DIR / "vor_profile.csv"
CAPTURE_TRAJECTORY_CSV = DERIVED_DIR / "capture_trajectory.csv"
PART_LIFECYCLE_CSV = DERIVED_DIR / "part_lifecycle.csv"
REVENUE_CONCENTRATION_CSV = DERIVED_DIR / "revenue_concentration.csv"
REVENUE_WATERFALL_CSV = DERIVED_DIR / "revenue_waterfall.csv"
PRICE_PREMIUM_CSV = DERIVED_DIR / "price_premium.csv"
BASKET_CORRELATION_CSV = DERIVED_DIR / "basket_correlation.csv"
SUBSTITUTION_TIMELINE_CSV = DERIVED_DIR / "substitution_timeline.csv"
CAPTURE_RECOVERY_CSV = DERIVED_DIR / "capture_recovery_model.csv"
DISTRIBUTOR_GEO_CSV = PRISM_DATA_DIR / "distributor_geo.csv"

_deploy = (_paths_doc().get("deploy") or {})
_master = Path(_deploy.get("master_dashboard", "Master Dashboard"))
AIM_WORKBOOK_CANDIDATES = [
    ISZE_ROOT / _master / "AIM_CY2025_Analysis.xlsx",
    ISZE_ROOT / "Master Dashboard" / "AIM_CY2025_Analysis.xlsx",
    _resolve_folder("legacy", "91_legacy") / "Isuzu" / "AIM_CY2025_Analysis.xlsx",
    ISZE_ROOT / "Isuzu" / "AIM_CY2025_Analysis.xlsx",
]

BETA_MODE = os.getenv("PRISM_BETA", "false").lower() == "true"

# Internal-only content gate (docs/DASHBOARD_IA.md §6). Default OFF — the app
# is MD-safe unless launched with PRISM_INTERNAL=true (dealer leakage, attach
# lift, elasticity, demand-flow Sankey, aftermarket scrape).
INTERNAL_MODE = os.getenv("PRISM_INTERNAL", "false").lower() == "true"

# Canonical UIO filenames — no version suffix (version tracked on Changelog sheet inside the file)
UIO_FILE_PROD = str(_ROOT / "data" / "UIO.xlsx")
UIO_FILE_BETA = str(_ROOT / "data" / "UIO_beta.xlsx")
UIO_FILE = UIO_FILE_BETA if BETA_MODE else UIO_FILE_PROD

_uio_root = _resolve_folder("uio", "UIO")
UIO_CANDIDATES = [
    _uio_root / "_CURRENT" / "ISUZU_UIO_Overview_2026.xlsx",   # canonical
    PRISM_DATA_DIR / "UIO.xlsx",                                         # local PRISM copy
    Path(UIO_FILE),
    Path(UIO_FILE_BETA),
    # Versioned fallbacks (canonical _CURRENT above is v19; these are used only if it is missing)
    _uio_root / "_CURRENT" / "ISUZU_UIO_Overview_2026_v19.xlsx",
    DATA_ROOT / "ISUZU_UIO_Overview_2026_v19.xlsx",
    PRISM_DATA_DIR / "UIO_v19.xlsx",
]

DISTRIBUTOR_MAPPING_CANDIDATES = [
    PRISM_DATA_DIR / "distributor_master_mapping.csv",
    LEGACY_ISUZU_DATA / "distributor_master_mapping.csv",
]

LEGACY_SALES_CANDIDATES = [
    SALES_FACT_PARQUET,
    SALES_FACT_CSV,
    DERIVED_DIR / "sales_detailed_for_claude_full_fixed.tsv",
    PRISM_DATA_DIR / "sales_detailed_for_claude_full_fixed.tsv",
    PRISM_DATA_DIR / "sales_detailed_for_claude_full_fixed(1).csv",
    PRISM_DATA_DIR / "sales_detailed_for_claude_full_fixed.csv",
    LEGACY_ISUZU_DATA / "sales_detailed_for_claude_full_fixed.tsv",
    LEGACY_ISUZU_DATA / "sales_detailed_for_claude_full_fixed(1).csv",
    LEGACY_ISUZU_DATA / "sales_detailed_for_claude_full_fixed.csv",
]


def resolve_first_existing(candidates: list[Path]) -> Optional[Path]:
    for path in candidates:
        if path.exists():
            return path.resolve()
    return None


def resolve_uio_path() -> Path:
    found = resolve_first_existing(UIO_CANDIDATES)
    if found:
        return found
    raise FileNotFoundError(
        "UIO workbook not found. Expected one of:\n"
        + "\n".join(f"  - {p}" for p in UIO_CANDIDATES)
    )


def resolve_mapping_path() -> Path:
    found = resolve_first_existing(DISTRIBUTOR_MAPPING_CANDIDATES)
    if found:
        return found
    raise FileNotFoundError(
        "distributor_master_mapping.csv not found. Expected one of:\n"
        + "\n".join(f"  - {p}" for p in DISTRIBUTOR_MAPPING_CANDIDATES)
    )


def data_status() -> dict[str, bool]:
    """Quick checks for Streamlit UI."""
    return {
        "mapping": resolve_first_existing(DISTRIBUTOR_MAPPING_CANDIDATES) is not None,
        "uio": resolve_first_existing(UIO_CANDIDATES) is not None,
        "sales_parquet": SALES_FACT_PARQUET.exists(),
        "sales_csv_derived": SALES_FACT_CSV.exists(),
        "sales_legacy": resolve_first_existing(LEGACY_SALES_CANDIDATES[2:]) is not None,
        "raw_cy2025": (RAW_SALES_DIR / "CY2025.XLSX").exists(),
        "raw_cy2023_24": (RAW_SALES_DIR / "CY2023-2024.XLSX").exists(),
        "bvp_dimension": BVP_PN_DIMENSION_CSV.exists(),
        "bvp_pms_capture": PMS_CAPTURE_BY_DB_CSV.exists(),
        "bvp_mix_family": MIX_BY_FAMILY_CSV.exists(),
        "bvp_mix_subgroup": MIX_BY_SUBGROUP_CSV.exists(),
        "bvp_mix_group": MIX_BY_GROUP_CSV.exists(),
        "bvp_mix_pms": MIX_PMS_CSV.exists(),
        "bvp_benchmark": DB_BENCHMARK_MIX_CSV.exists(),
        "bvp_benchmark_subgroup": DB_BENCHMARK_SUBGROUP_CSV.exists(),
        "bvp_gps_db": GPS_SPU_BY_DB_CSV.exists(),
        "bvp_aim_exposure": AIM_EXPOSURE_BY_DB_CSV.exists(),
    }
