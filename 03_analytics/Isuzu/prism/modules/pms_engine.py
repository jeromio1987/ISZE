"""
PRISM Data Hierarchy — Layer 2B: PMS (Preventive Maintenance Service coverage)
===============================================================================
PMS answers: "For specific service items, are we getting the jobs?"

Formula:   Actual PNs sold / Expected demand = Capture Rate %
Depends on: UIO (Layer 1) — surviving parc is the denominator for expected demand
Granularity: Distributor x model x PN category (micro view, specific PNs)

Expected demand:
  Addressable parc (S2+S3) x Service frequency x Parts per service
  Service frequency = 40,000 km interval / ~20,000 km avg annual mileage = 0.5/yr
  IMPORTANT: 1.5/yr (previous assumption) was WRONG. Use 0.5/yr.

Phase 1 scope: N75 only — NPR75 (4HK1) + NPR88 (4JZ1)
Phase 2:       N35 — NLR87 (RZ4E) + NLR88 (4JZ1) — follows N75 pilot

PN authority: ITUK pilot registry (Apr 2026) plus BVP PARTS CATALOG PMS sheets
              (filters, brake/clutch wear, urea). Registry wins on overlap; catalog
              widens capture actuals to ~all catalogue PMS part numbers.

Source: ISZE sales data tagged against PN registry in this module
Refinements (May 2026): BVP/genuine split, age cohort interface, seasonal annualisation, dealer drill-down
"""

# Module: PMS Coverage Engine
# ISZE GPS Dashboard — PMS Classification & Capture Rate Analysis
#
# Phase 1 scope: N75 / 7.5t fleet (NPR75/4HK1 and NPR88/4JZ1).
# N35 (NLR87/NLR88) included in registry but shown as reference only.
#
# Source: ITUK guidance Apr 2026

import pandas as pd
import numpy as np
import yaml
from datetime import datetime
from pathlib import Path

# ─── PMS PN Registry ──────────────────────────────────────────────────────────
# Maps each part number → {model, category, type}
# Some PNs appear in multiple model/category combos — each mapping is explicit.
# "genuine" = OE Isuzu; "bvp" = Best Value Parts (branded alternative)

PMS_PN_REGISTRY: dict = {
    # ── NPR75 / N75 / 4HK1 ──────────────────────────────────────────────────
    # Oil Filter
    "8983282071": {"model": "N75_4HK1", "category": "oil_filter",          "type": "genuine"},
    "8983282070": {"model": "N75_4HK1", "category": "oil_filter",          "type": "genuine"},
    "1876102890": {"model": "N75_4HK1", "category": "oil_filter",          "type": "bvp"},
    "5876101170": {"model": "N75_4HK1", "category": "oil_filter",          "type": "bvp"},
    "5876100310": {"model": "N75_4HK1", "category": "oil_filter",          "type": "bvp"},
    # Fuel Filter
    "8975425050": {"model": "N75_4HK1", "category": "fuel_filter",         "type": "genuine"},
    "8975425400": {"model": "N75_4HK1", "category": "fuel_filter",         "type": "genuine"},
    "1876102860": {"model": "N75_4HK1", "category": "fuel_filter",         "type": "bvp"},
    # Air Filter
    "8981772710": {"model": "N75_4HK1", "category": "air_filter",          "type": "genuine"},
    "8981235322": {"model": "N75_4HK1", "category": "air_filter",          "type": "genuine"},
    "8982157230": {"model": "N75_4HK1", "category": "air_filter",          "type": "genuine"},
    "5876102500": {"model": "N75_4HK1", "category": "air_filter",          "type": "bvp"},
    # Brake Pad
    "8982447940": {"model": "N75_4HK1", "category": "brake_pad",           "type": "genuine"},
    # Clutch Disc
    "8981649171": {"model": "N75_4HK1", "category": "clutch_disc",         "type": "genuine"},
    "5876100920": {"model": "N75_4HK1", "category": "clutch_disc",         "type": "bvp"},
    # Clutch Pressure Plate
    "8970388314": {"model": "N75_4HK1", "category": "clutch_pressure_plate", "type": "genuine"},
    "5876101040": {"model": "N75_4HK1", "category": "clutch_pressure_plate", "type": "bvp"},

    # ── NPR88 / N75 / 4JZ1 ──────────────────────────────────────────────────
    # Oil Filter
    "8975439050": {"model": "N75_4JZ1", "category": "oil_filter",          "type": "genuine"},
    # Fuel Filter
    "8983104491": {"model": "N75_4JZ1", "category": "fuel_filter",         "type": "genuine"},
    "8983104490": {"model": "N75_4JZ1", "category": "fuel_filter",         "type": "genuine"},
    "8983572930": {"model": "N75_4JZ1", "category": "fuel_filter",         "type": "genuine"},
    "8983752250": {"model": "N75_4JZ1", "category": "fuel_filter",         "type": "genuine"},
    "8980374810": {"model": "N75_4JZ1", "category": "fuel_filter",         "type": "genuine"},
    "5876101570": {"model": "N75_4JZ1", "category": "fuel_filter",         "type": "bvp"},
    "8980318470": {"model": "N75_4JZ1", "category": "fuel_filter",         "type": "genuine"},
    "8980179710": {"model": "N75_4JZ1", "category": "fuel_filter",         "type": "genuine"},
    # Air Filter
    "8976659910": {"model": "N75_4JZ1", "category": "air_filter",          "type": "genuine"},
    "8976739570": {"model": "N75_4JZ1", "category": "air_filter",          "type": "genuine"},
    # Brake Pad
    "8982169220": {"model": "N75_4JZ1", "category": "brake_pad",           "type": "genuine"},
    "5876102380": {"model": "N75_4JZ1", "category": "brake_pad",           "type": "bvp"},
    "5876170050": {"model": "N75_4JZ1", "category": "brake_pad",           "type": "bvp"},
    # Clutch Disc
    "8978283700": {"model": "N75_4JZ1", "category": "clutch_disc",         "type": "genuine"},
    "8982551391": {"model": "N75_4JZ1", "category": "clutch_disc",         "type": "genuine"},
    "5876100771": {"model": "N75_4JZ1", "category": "clutch_disc",         "type": "bvp"},
    # Clutch Pressure Plate
    "8980400932": {"model": "N75_4JZ1", "category": "clutch_pressure_plate", "type": "genuine"},
    "5876100910": {"model": "N75_4JZ1", "category": "clutch_pressure_plate", "type": "bvp"},

    # ── NLR87 / N35.125 / RZ4E ───────────────────────────────────────────────
    # Oil Filter
    "8982705240": {"model": "N35_RZ4E", "category": "oil_filter",          "type": "genuine"},
    "5876150530": {"model": "N35_RZ4E", "category": "oil_filter",          "type": "bvp"},
    # Fuel Filter
    "8975080920": {"model": "N35_RZ4E", "category": "fuel_filter",         "type": "genuine"},
    "8975080932": {"model": "N35_RZ4E", "category": "fuel_filter",         "type": "genuine"},
    "8981596930": {"model": "N35_RZ4E", "category": "fuel_filter",         "type": "genuine"},
    "8981941190": {"model": "N35_RZ4E", "category": "fuel_filter",         "type": "genuine"},
    "5876150170": {"model": "N35_RZ4E", "category": "fuel_filter",         "type": "bvp"},
    "5876150240": {"model": "N35_RZ4E", "category": "fuel_filter",         "type": "bvp"},
    # Air Filter
    "8983214130": {"model": "N35_RZ4E", "category": "air_filter",          "type": "genuine"},
    "8975095290": {"model": "N35_RZ4E", "category": "air_filter",          "type": "genuine"},
    "5876102900": {"model": "N35_RZ4E", "category": "air_filter",          "type": "bvp"},
    # Brake Pad (front)
    "8982169210": {"model": "N35_RZ4E", "category": "brake_pad",           "type": "genuine"},
    # Brake Shoe (rear)
    "8973319320": {"model": "N35_RZ4E", "category": "brake_shoe",          "type": "genuine"},
    "5878320440": {"model": "N35_RZ4E", "category": "brake_shoe",          "type": "genuine"},
    # Clutch Disc
    "8983753331": {"model": "N35_RZ4E", "category": "clutch_disc",         "type": "genuine"},
    # Clutch Pressure Plate
    "8982831940": {"model": "N35_RZ4E", "category": "clutch_pressure_plate", "type": "genuine"},
    # Urea (AdBlue) filter — BVP UREA FILTER sheet
    "1876102341": {"model": "N75_4HK1", "category": "urea_filter",          "type": "bvp"},
    "8983507161": {"model": "N75_4HK1", "category": "urea_filter",          "type": "genuine"},

    # ── NLR88 / N35.150 / 4JZ1 ──────────────────────────────────────────────
    # Oil Filter — shares 8975439050 with N75_4JZ1; N35 entry separate key with suffix
    # (handled via multi-model logic below — see _MULTI_MODEL_REGISTRY)
    # Fuel Filter
    "8977903031": {"model": "N35_4JZ1", "category": "fuel_filter",         "type": "genuine"},
    "8978293170": {"model": "N35_4JZ1", "category": "clutch_disc",         "type": "genuine"},
    # Clutch Pressure Plate — shares 8980400932 with N75_4JZ1
    # Air Filter — shares 8976739570 with N75_4JZ1
    # Brake Pad (front) — shares 8982169220 with N75_4JZ1
    # Brake Pad (rear) — shares 8982169210 with N35_RZ4E
}

# PNs that appear in multiple models — list all applicable mappings
# Registry above stores the FIRST model encountered; this dict handles multi-model PNs.
_MULTI_MODEL = {
    # PN: list of {model, category, type}
    "8975439050": [
        {"model": "N75_4JZ1", "category": "oil_filter", "type": "genuine"},
        {"model": "N35_4JZ1", "category": "oil_filter", "type": "genuine"},
    ],
    "8983104491": [
        {"model": "N75_4JZ1", "category": "fuel_filter", "type": "genuine"},
        {"model": "N35_4JZ1", "category": "fuel_filter", "type": "genuine"},
    ],
    "8983752250": [
        {"model": "N75_4JZ1", "category": "fuel_filter", "type": "genuine"},
        {"model": "N35_4JZ1", "category": "fuel_filter", "type": "genuine"},
    ],
    "8981941190": [
        {"model": "N35_RZ4E", "category": "fuel_filter", "type": "genuine"},
        {"model": "N35_4JZ1", "category": "fuel_filter", "type": "genuine"},
    ],
    "5876150240": [
        {"model": "N35_RZ4E", "category": "fuel_filter", "type": "bvp"},
        {"model": "N35_4JZ1", "category": "fuel_filter", "type": "bvp"},
    ],
    "8976739570": [
        {"model": "N75_4JZ1", "category": "air_filter",  "type": "genuine"},
        {"model": "N35_4JZ1", "category": "air_filter",  "type": "genuine"},
    ],
    "8982447940": [
        {"model": "N75_4HK1", "category": "brake_pad",   "type": "genuine"},
        {"model": "N75_4JZ1", "category": "brake_pad",   "type": "genuine"},
    ],
    "8982169220": [
        {"model": "N75_4JZ1", "category": "brake_pad",   "type": "genuine"},
        {"model": "N35_RZ4E", "category": "brake_pad",   "type": "genuine"},
        {"model": "N35_4JZ1", "category": "brake_pad",   "type": "genuine"},
    ],
    "8982169210": [
        {"model": "N35_RZ4E", "category": "brake_pad",   "type": "genuine"},
        {"model": "N35_4JZ1", "category": "brake_pad",   "type": "genuine"},
    ],
    "5876102380": [
        {"model": "N75_4JZ1", "category": "brake_pad",   "type": "bvp"},
        {"model": "N35_RZ4E", "category": "brake_pad",   "type": "bvp"},
        {"model": "N35_4JZ1", "category": "brake_pad",   "type": "bvp"},
    ],
    "8980400932": [
        {"model": "N75_4JZ1", "category": "clutch_pressure_plate", "type": "genuine"},
        {"model": "N35_4JZ1", "category": "clutch_pressure_plate", "type": "genuine"},
    ],
    "5876100910": [
        {"model": "N75_4JZ1", "category": "clutch_pressure_plate", "type": "bvp"},
        {"model": "N35_4JZ1", "category": "clutch_pressure_plate", "type": "bvp"},
    ],
    "8976643531": [
        {"model": "N35_4JZ1", "category": "air_filter",  "type": "genuine"},
    ],
}

# Add remaining N35_4JZ1 PNs not yet in main registry
_N35_4JZ1_EXTRA = {
    "8976643531": {"model": "N35_4JZ1", "category": "air_filter",            "type": "genuine"},
}
PMS_PN_REGISTRY.update(_N35_4JZ1_EXTRA)

# Human-readable category labels
CATEGORY_LABELS = {
    "oil_filter":            "Oil Filter",
    "fuel_filter":           "Fuel Filter",
    "air_filter":            "Air Filter",
    "urea_filter":           "Urea (AdBlue) Filter",
    "blower_filter":         "Blower Unit Filter",
    "brake_pad":             "Brake Pad",
    "brake_shoe":            "Brake Shoe",
    "clutch_disc":           "Clutch Disc",
    "clutch_pressure_plate": "Clutch Pressure Plate",
    "clutch_kit":            "Clutch Kit",
    "release_bearing":       "Release Bearing",
    "pilot_bearing":         "Pilot Bearing",
    "clutch_booster":        "Clutch Booster",
    "brake_rotor":           "Brake Rotor",
}

# Phase 1 categories (N75 focus for capture rate KPIs)
PHASE1_CATEGORIES = ["oil_filter", "fuel_filter", "air_filter", "brake_pad"]

# Model groups for parc-based calculations
N75_MODELS = {"N75_4HK1", "N75_4JZ1"}
N35_MODELS = {"N35_RZ4E", "N35_4JZ1"}
LCV_MODELS = {"LCV_DMax"}

# Distributors that sell LCV (D-Max) only — must use LCV/N35 PMS scope, not N75 trucks
LCV_DISTRIBUTORS = frozenset({"IUK", "UMI"})
CV_TRUCK_DISTRIBUTORS = frozenset({"ITUK", "UTI"})


def _load_lcv_pms_genuine() -> tuple[dict, dict]:
    """Merge data/lcv_pms_genuine.yaml into registry + multi-model map."""
    path = Path(__file__).resolve().parents[1] / "data" / "lcv_pms_genuine.yaml"
    if not path.is_file():
        return {}, {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    model = raw.get("model", "LCV_DMax")
    extra_registry: dict = {}
    extra_multi: dict = {}
    for item in raw.get("parts") or []:
        pn = str(item.get("part_number", "")).strip().lstrip("0")
        if not pn:
            continue
        cat = item.get("category")
        typ = item.get("type", "genuine")
        entry = {"model": model, "category": cat, "type": typ}
        if pn in PMS_PN_REGISTRY or pn in _MULTI_MODEL:
            extra_multi.setdefault(pn, []).append(entry)
        else:
            extra_registry[pn] = entry
    return extra_registry, extra_multi


# ─── Default parc config ──────────────────────────────────────────────────────
DEFAULT_PARC_CONFIG = {
    "N75_surviving_parc":    8515,   # 10-year surviving UK parc
    "N35_surviving_parc":    9818,   # 10-year surviving UK parc
    "N75_services_per_year": 0.5,    # 40,000km interval / ~20,000km avg annual
    "N35_services_per_year": 0.75,   # N35.125 at 20,000km; blended
    "LCV_services_per_year": 1.0,    # D-Max ~10k km service interval
    "addressable_pct":       1.00,   # full parc addressable (Jerome 2026-07-03)
    "scope":                 "N75_only",  # N75_only | LCV_only | all
}


def pms_scope_for_distributor(distributor_code: str | None) -> str:
    """Pilot KPI lens for PMS capture — not a filter on what the distributor may sell.

    ITUK's DVLA car park includes N35, N75, F-series, etc., and distributors also sell
    PMS lines to other OEM fleets (e.g. DAF). Billing actuals stay complete; this scope
    only chooses which registry rows roll into the capture numerator vs which UIO-based
    expected demand applies (N75 truck parc for ITUK/UTI, LCV for IUK/UMI).
    """
    if distributor_code in LCV_DISTRIBUTORS:
        return "LCV_only"
    if distributor_code in CV_TRUCK_DISTRIBUTORS:
        return "N75_only"
    return DEFAULT_PARC_CONFIG.get("scope", "N75_only")


def pms_models_for_scope(scope: str) -> set[str]:
    if scope == "LCV_only":
        return N35_MODELS | LCV_MODELS | {"multi"}
    if scope == "all":
        return N75_MODELS | N35_MODELS | LCV_MODELS | {"multi"}
    return N75_MODELS | {"multi"}


def filter_pms_by_scope(df_pms: pd.DataFrame, scope: str) -> pd.DataFrame:
    if df_pms.empty:
        return df_pms
    allowed = pms_models_for_scope(scope)
    return df_pms[df_pms["pms_model"].isin(allowed)].copy()


def parc_config_for_distributor(
    distributor_code: str | None,
    base: dict | None = None,
) -> dict:
    cfg = {**DEFAULT_PARC_CONFIG, **(base or {})}
    scope = pms_scope_for_distributor(distributor_code)
    cfg["scope"] = scope
    from modules.pms_capture_config import n75_addressable_pct
    cfg["addressable_pct"] = n75_addressable_pct()
    # Per-country / per-distributor interval overrides (docs/pms_service_intervals.md §5).
    from modules.pms_capture_config import COUNTRY_OVERRIDES
    ov = COUNTRY_OVERRIDES.get(distributor_code) or {}
    if ov.get("services_per_year") is not None:
        cfg["services_per_year_override"] = float(ov["services_per_year"])
    if ov.get("factors"):
        cfg["factor_overrides"] = dict(ov["factors"])
    return cfg


def _services_per_year_for_scope(scope: str, cfg: dict) -> float:
    override = cfg.get("services_per_year_override")
    if override is not None:
        return float(override)
    if scope == "LCV_only":
        return float(cfg.get("LCV_services_per_year", 1.0))
    if scope == "all":
        return float(cfg.get("N35_services_per_year", 0.75))
    return float(cfg.get("N75_services_per_year", 0.5))


def expected_addressable_services(uio_units: float, scope: str, cfg: dict) -> float:
    if uio_units <= 0:
        return 0.0
    svc = _services_per_year_for_scope(scope, cfg)
    return uio_units * svc * float(cfg.get("addressable_pct", 1.00))


def expected_by_category_bucketed(distributor_code: str, cfg: dict) -> dict | None:
    """Real per-model-type-bucket expected demand (2026-07-15 fix).

    Replaces the single-scope (N75_only/LCV_only) expected-demand calc with a
    weighted sum across each distributor's real CV-standard/F-Series/LCV UIO
    split, instead of forcing every distributor into one vehicle-class bucket.
    See modules/pms_capture_config.py and scripts/build_uio_by_model_bucket.py.

    Returns None if this distributor has no real UIO-bucket entry — callers
    must fall back to the legacy single-scope calculation in that case (this
    keeps existing behaviour unchanged for synthetic/test distributor codes
    and any market not yet covered by uio_by_model_bucket.csv).
    """
    from modules.pms_capture_config import (
        CONSUMABLE_FACTOR,
        WEAR_FACTOR,
        BUCKET_SERVICES_PER_YEAR,
        BUCKET_SERVICES_PER_YEAR_OVERRIDES,
        LCV_BUCKET_FACTOR_OVERRIDES,
        UIO_BY_BUCKET,
    )

    bucket = UIO_BY_BUCKET.get(distributor_code)
    if not bucket:
        return None

    addr = float(cfg.get("addressable_pct", 1.00))
    svc = {**BUCKET_SERVICES_PER_YEAR, **BUCKET_SERVICES_PER_YEAR_OVERRIDES.get(distributor_code, {})}
    base_cv = bucket["cv_std"] * svc["cv_std"] * addr
    base_f = bucket["f_series"] * svc["f_series"] * addr
    base_l = bucket["lcv"] * svc["lcv"] * addr

    # 2026-07-21 fix: cfg["factor_overrides"] (from pms_capture_assumptions.yaml
    # country_overrides.factors, e.g. ITUK brake_pad/brake_shoe 0.4) was silently
    # dropped on this bucketed path — only the legacy _expected_qty_for_db() path
    # in scripts/build_bvp_p0_p1.py applied it. Same fix, same precedence: a
    # distributor-specific override replaces the global factor for that category
    # outright (not a multiplier) before the LCV bucket-component override is
    # considered. See ISZE_ROADMAP.md "country_overrides.factors is dead config"
    # (fixed) and DECISIONS.md 2026-07-21.
    factor_overrides = cfg.get("factor_overrides") or {}
    all_factors = {**CONSUMABLE_FACTOR, **WEAR_FACTOR}
    expected: dict = {}
    for cat, fac in all_factors.items():
        fac = factor_overrides.get(cat, fac)
        fac_lcv = LCV_BUCKET_FACTOR_OVERRIDES.get(cat, fac)
        expected[cat] = {"qty": base_cv * fac + base_f * fac + base_l * fac_lcv}
    return expected


_LCV_REG, _LCV_MULTI = _load_lcv_pms_genuine()
PMS_PN_REGISTRY.update(_LCV_REG)
for _pn, _maps in _LCV_MULTI.items():
    if _pn in _MULTI_MODEL:
        existing = {(m["model"], m["category"], m["type"]) for m in _MULTI_MODEL[_pn]}
        for m in _maps:
            key = (m["model"], m["category"], m["type"])
            if key not in existing:
                _MULTI_MODEL[_pn].append(m)
    else:
        _MULTI_MODEL[_pn] = _maps


# ─── classify_pms_sales ───────────────────────────────────────────────────────

def classify_pms_sales(df_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Add PMS classification columns to a sales DataFrame.

    New columns added:
        is_pms        bool    — True if PN is in PMS registry
        pms_category  str     — e.g. "oil_filter" (NaN if not PMS)
        pms_model     str     — e.g. "N75_4HK1" or "multi" (NaN if not PMS)
        pms_type      str     — "genuine" | "bvp" (NaN if not PMS)

    For PNs mapped to multiple models, pms_model is set to "multi" and
    pms_category reflects the shared category (which is consistent across all
    mappings for multi-model PNs).

    Strips leading zeros and whitespace from part_number before matching.
    Does not modify the original DataFrame.
    """
    df = df_sales.copy()

    # Normalise part_number: strip whitespace, remove leading zeros
    df['_pn_norm'] = (
        df['part_number']
        .astype(str)
        .str.strip()
        .str.lstrip('0')
    )

    def _lookup(pn_norm):
        # Multi-model check first
        if pn_norm in _MULTI_MODEL:
            mappings = _MULTI_MODEL[pn_norm]
            # Category is consistent for multi-model PNs; take first
            return True, mappings[0]['category'], "multi", mappings[0]['type']
        if pn_norm in PMS_PN_REGISTRY:
            m = PMS_PN_REGISTRY[pn_norm]
            return True, m['category'], m['model'], m['type']
        return False, np.nan, np.nan, np.nan

    results = df['_pn_norm'].apply(_lookup)
    df['is_pms']       = results.apply(lambda r: r[0])
    df['pms_category'] = results.apply(lambda r: r[1])
    df['pms_model']    = results.apply(lambda r: r[2])
    df['pms_type']     = results.apply(lambda r: r[3])

    df.drop(columns=['_pn_norm'], inplace=True)
    return df


# ─── _filter_by_year ─────────────────────────────────────────────────────────

def _filter_by_year(
    df: pd.DataFrame,
    year: int,
    year_type: str = "calendar",
    distributor_code: str = None,
) -> pd.DataFrame:
    col = 'fiscal_year' if year_type == "fiscal" else 'year'
    df = df[df[col] == year]
    if distributor_code:
        df = df[df['distributor_code'] == distributor_code]
    return df


# ─── calculate_pms_capture ────────────────────────────────────────────────────

def calculate_pms_capture(
    df_sales: pd.DataFrame,
    year: int,
    year_type: str = "calendar",
    distributor_code: str = None,
    parc_config: dict = None,
    df_dim: pd.DataFrame | None = None,
    fill_catalog_pms: bool = True,
) -> dict:
    """
    Calculate PMS capture rates and revenue opportunity.

    parc_config keys (all optional — defaults in DEFAULT_PARC_CONFIG):
        N75_surviving_parc    int
        N35_surviving_parc    int
        N75_services_per_year float
        N35_services_per_year float
        addressable_pct       float  (0–1)
        scope                 str    "N75_only" | "all"

    Returns dict:
        actual_by_category      {category: {qty, revenue_eur}}
        expected_by_category    {category: {qty}}
        capture_rate_by_category {category: float}  actual/expected
        revenue_opportunity     {category: float}   (expected-actual) * avg_sp
        total_actual_eur        float
        total_opportunity_eur   float
        summary_df              pd.DataFrame
    """
    cfg = parc_config_for_distributor(distributor_code, parc_config)

    from modules.pms_capture_config import CONSUMABLE_CATS, CONSUMABLE_FACTOR, WEAR_FACTOR
    from modules.pms_tagging import tag_pms_sales

    # ── Classify and filter ────────────────────────────────────────────────
    df_classified = tag_pms_sales(
        df_sales, df_dim, fill_catalog_pms=fill_catalog_pms
    )
    df_period = _filter_by_year(df_classified, year, year_type, distributor_code)

    # Guard: if year column didn't exist, df_period may be an empty copy with or
    # without is_pms; ensure is_pms column exists before boolean indexing.
    if 'is_pms' not in df_period.columns or df_period.empty:
        df_pms = pd.DataFrame(columns=list(df_period.columns) + [
            'is_pms', 'pms_category', 'pms_model', 'pms_type'
        ])
    else:
        df_pms = df_period[df_period['is_pms']].copy()
    if "pms_capture_eligible" in df_pms.columns:
        df_pms = df_pms[df_pms["pms_capture_eligible"]].copy()

    # ── Determine scope (IUK/UMI = LCV D-Max + N35; ITUK/UTI = N75 trucks) ─
    scope = cfg.get("scope", "N75_only")

    # 2026-07-15 fix: prefer the real per-model-type-bucket calculation when
    # this distributor has one (data/uio_by_model_bucket.csv) and no explicit
    # uio_units override was supplied. Explicit overrides (e.g. live-resolved
    # UIO passed in by callers) and distributors without bucket data fall
    # through to the original single-scope logic below, unchanged — this
    # keeps every existing caller and test working exactly as before.
    bucketed_expected = None
    if cfg.get("uio_units") is None and distributor_code:
        bucketed_expected = expected_by_category_bucketed(distributor_code, cfg)

    if bucketed_expected is not None:
        # Real UIO split already covers every vehicle class this distributor
        # actually sells — don't drop cross-model sales from the numerator
        # by filtering to a single scope's model list.
        df_pms_scope = df_pms
    else:
        df_pms_scope = filter_pms_by_scope(df_pms, scope)

    # ── Actual quantities / revenue by category ────────────────────────────
    actual_by_category: dict = {}
    if not df_pms_scope.empty:
        grp = (
            df_pms_scope.groupby('pms_category')
            .agg(qty=('billed_qty', 'sum'), revenue_eur=('net_sales_value', 'sum'))
            .reset_index()
        )
        for _, row in grp.iterrows():
            actual_by_category[row['pms_category']] = {
                'qty':         float(row['qty']),
                'revenue_eur': float(row['revenue_eur']),
            }

    if bucketed_expected is not None:
        expected_by_category = bucketed_expected
    else:
        # ── Expected quantities (parc × services/year × addressable_pct) ──
        uio_units = float(
            cfg.get("uio_units")
            or (cfg["N35_surviving_parc"] if scope == "LCV_only" else cfg["N75_surviving_parc"])
        )
        addressable = expected_addressable_services(uio_units, scope, cfg)

        n75_addressable = (
            cfg['N75_surviving_parc'] * cfg['N75_services_per_year'] * cfg['addressable_pct']
        ) if scope == "N75_only" else 0.0
        n35_addressable = addressable if scope in ("LCV_only", "all") else 0.0
        if scope == "LCV_only":
            n75_addressable = 0.0
        elif scope == "N75_only":
            n35_addressable = 0.0
            addressable = n75_addressable
        elif scope == "all":
            n75_addressable = (
                cfg['N75_surviving_parc'] * cfg['N75_services_per_year'] * cfg['addressable_pct']
            )
            n35_addressable = (
                cfg['N35_surviving_parc'] * cfg['N35_services_per_year'] * cfg['addressable_pct']
            )

        base_n75 = addressable if scope == "LCV_only" else n75_addressable
        base_n35 = n35_addressable if scope in ("LCV_only", "all") else 0.0
        if scope == "N75_only":
            base_n35 = 0.0
            addressable = n75_addressable
        elif scope == "LCV_only":
            base_n75 = addressable

        # 2026-07-21 fix: this legacy single-scope path previously never read
        # cfg["factor_overrides"] either (only scripts/build_bvp_p0_p1.py's
        # _expected_qty_for_db() applied it) — same distributor-specific
        # override-replaces-default pattern applied here for consistency with
        # expected_by_category_bucketed() above.
        factor_overrides = cfg.get("factor_overrides") or {}
        expected_by_category: dict = {}
        for cat in CONSUMABLE_CATS:
            fac = factor_overrides.get(cat, CONSUMABLE_FACTOR.get(cat, 1.0))
            expected_by_category[cat] = {"qty": base_n75 * fac}
        for cat, wf in WEAR_FACTOR.items():
            wf = factor_overrides.get(cat, wf)
            expected_by_category[cat] = {"qty": base_n75 * wf}

        if cfg["scope"] == "all":
            for cat in CONSUMABLE_CATS:
                fac = factor_overrides.get(cat, CONSUMABLE_FACTOR.get(cat, 1.0))
                existing = expected_by_category.get(cat, {}).get("qty", 0)
                expected_by_category[cat] = {"qty": existing + base_n35 * fac}
            for cat, wf in WEAR_FACTOR.items():
                wf = factor_overrides.get(cat, wf)
                existing = expected_by_category.get(cat, {}).get("qty", 0)
                expected_by_category[cat] = {"qty": existing + base_n35 * wf}

    # ── Capture rates ──────────────────────────────────────────────────────
    capture_rate_by_category: dict = {}
    for cat, exp in expected_by_category.items():
        exp_qty = exp['qty']
        act_qty = actual_by_category.get(cat, {}).get('qty', 0.0)
        if exp_qty > 0:
            capture_rate_by_category[cat] = act_qty / exp_qty
        else:
            capture_rate_by_category[cat] = 0.0

    # ── Revenue opportunity ────────────────────────────────────────────────
    # QUOTABLE-KPI FIREWALL (2026-07-21): avg_sp falls back to 0.0 whenever
    # act_qty == 0 (no actual sales to derive a real unit price from), which
    # makes gap_qty * 0.0 = EUR0 for that category — i.e. a distributor with
    # ZERO capture in a category scores the BEST possible (smallest) revenue
    # gap. This silently rewards non-selling as if the opportunity were fully
    # captured and is UNSAFE to use for € league-table ranking (see
    # DECISIONS.md 2026-07-17 "Not done — revenue_gap_eur is still unsafe").
    # A network-median unit price fallback would fix this properly, but this
    # single-distributor function has no visibility into other distributors'
    # prices to build that median from (calculate_pms_capture is called once
    # per distributor) — doing it here would require a wider signature change
    # across every caller, so instead: flag every act_qty==0 category as
    # `revenue_gap_quotable: False` in the summary_df (see below) rather than
    # silently shipping an unsafe EUR0. Callers must exclude
    # revenue_gap_quotable==False rows from any € ranking / league table.
    revenue_opportunity: dict = {}
    revenue_gap_quotable: dict = {}
    for cat, exp in expected_by_category.items():
        exp_qty = exp['qty']
        act_data = actual_by_category.get(cat, {})
        act_qty = act_data.get('qty', 0.0)
        act_rev = act_data.get('revenue_eur', 0.0)
        avg_sp = (act_rev / act_qty) if act_qty > 0 else 0.0
        gap_qty = max(exp_qty - act_qty, 0.0)
        revenue_opportunity[cat] = gap_qty * avg_sp
        revenue_gap_quotable[cat] = act_qty > 0

    # ── Summary DataFrame ──────────────────────────────────────────────────
    rows = []
    all_cats = sorted(set(list(expected_by_category.keys()) + list(actual_by_category.keys())))
    for cat in all_cats:
        act_data  = actual_by_category.get(cat, {'qty': 0.0, 'revenue_eur': 0.0})
        exp_data  = expected_by_category.get(cat, {'qty': 0.0})
        act_qty   = act_data['qty']
        act_rev   = act_data['revenue_eur']
        exp_qty   = exp_data['qty']
        cap_rate  = capture_rate_by_category.get(cat, 0.0)
        avg_sp    = (act_rev / act_qty) if act_qty > 0 else 0.0
        rev_gap   = revenue_opportunity.get(cat, 0.0)
        # False whenever act_qty==0 for this category — avg_sp/rev_gap is a
        # EUR0 artefact, not a real "fully captured" gap. See the firewall
        # comment above `revenue_opportunity`. Exclude False rows from any
        # € ranking/league table.
        gap_quotable = revenue_gap_quotable.get(cat, act_qty > 0)
        rows.append({
            'category':       cat,
            'category_label': CATEGORY_LABELS.get(cat, cat),
            'actual_qty':     act_qty,
            'expected_qty':   exp_qty,
            'capture_rate':   cap_rate,
            'avg_sp_eur':     avg_sp,
            'revenue_gap_eur': rev_gap,
            'revenue_gap_quotable': gap_quotable,
            'actual_rev_eur': act_rev,
        })

    summary_df = pd.DataFrame(rows).sort_values('revenue_gap_eur', ascending=False).reset_index(drop=True)

    total_actual_eur     = sum(v['revenue_eur'] for v in actual_by_category.values())
    total_opportunity_eur = sum(revenue_opportunity.values())
    # Sum restricted to categories with a real avg_sp (act_qty>0) — the safe
    # € figure to quote in a league table. total_opportunity_eur above still
    # includes the unsafe EUR0-priced categories (kept for backwards compat).
    total_opportunity_eur_quotable = sum(
        v for cat, v in revenue_opportunity.items() if revenue_gap_quotable.get(cat)
    )

    return {
        'actual_by_category':        actual_by_category,
        'expected_by_category':      expected_by_category,
        'capture_rate_by_category':  capture_rate_by_category,
        'revenue_opportunity':        revenue_opportunity,
        'revenue_gap_quotable':      revenue_gap_quotable,
        'total_actual_eur':          total_actual_eur,
        'total_opportunity_eur':     total_opportunity_eur,
        'total_opportunity_eur_quotable': total_opportunity_eur_quotable,
        'summary_df':                summary_df,
    }


# ─── calculate_ituk_incentive ─────────────────────────────────────────────────

def calculate_ituk_incentive(
    df_sales: pd.DataFrame,
    year: int,
    year_type: str = "calendar",
    baseline_months: int = 6,
) -> pd.DataFrame:
    """
    Calculate dealer incremental performance vs baseline for ITUK incentive structure.

    Baseline = average monthly PMS sales over previous N months x campaign months.
    Incremental = actual campaign period sales - baseline.

    Bonus tiers (% above baseline):
        >= 150% of baseline (50% above) → "150pct" → £750 dealer credit
        >= 125% of baseline (25% above) → "125pct" → £500 dealer credit
        >= 100% of baseline (any uplift) → "100pct" → £250 dealer credit
        < 100% of baseline              → None

    Note: The spec uses "above baseline" language — 100% of target means
    achieving baseline (0% incremental), 125% = 25% above, 150% = 50% above.

    Returns DataFrame: category | baseline_qty | actual_qty | incremental_qty |
                       pct_of_target | bonus_tier | bonus_amount_gbp
    """
    df_classified = classify_pms_sales(df_sales)
    year_col = 'fiscal_year' if year_type == "fiscal" else 'year'

    # Campaign period = selected year
    df_campaign = df_classified[
        (df_classified[year_col] == year) &
        df_classified['is_pms']
    ]

    # Baseline period = previous year (same year_type)
    df_baseline = df_classified[
        (df_classified[year_col] == year - 1) &
        df_classified['is_pms']
    ]

    # Restrict to ITUK distributor if present
    if 'ITUK' in df_classified['distributor_code'].unique():
        df_campaign = df_campaign[df_campaign['distributor_code'] == 'ITUK']
        df_baseline = df_baseline[df_baseline['distributor_code'] == 'ITUK']

    def _agg_by_cat(df_in):
        if df_in.empty:
            return {}
        grp = df_in.groupby('pms_category').agg(qty=('billed_qty', 'sum')).reset_index()
        return dict(zip(grp['pms_category'], grp['qty']))

    campaign_qty = _agg_by_cat(df_campaign)
    baseline_qty_full = _agg_by_cat(df_baseline)

    # Scale baseline to number of campaign months
    # Baseline full year → monthly avg → × baseline_months (campaign window)
    all_cats = sorted(set(list(campaign_qty.keys()) + list(baseline_qty_full.keys())))
    rows = []
    for cat in all_cats:
        bl_full  = baseline_qty_full.get(cat, 0.0)
        bl_monthly = bl_full / 12.0
        bl_period  = bl_monthly * baseline_months
        act_qty   = float(campaign_qty.get(cat, 0.0))
        incr_qty  = act_qty - bl_period
        pct_target = (act_qty / bl_period) if bl_period > 0 else 0.0

        if pct_target >= 1.50:
            bonus_tier = "150pct"
            bonus_gbp  = 750
        elif pct_target >= 1.25:
            bonus_tier = "125pct"
            bonus_gbp  = 500
        elif pct_target >= 1.00:
            bonus_tier = "100pct"
            bonus_gbp  = 250
        else:
            bonus_tier = None
            bonus_gbp  = 0

        rows.append({
            'category':          cat,
            'category_label':    CATEGORY_LABELS.get(cat, cat),
            'baseline_qty':      round(bl_period, 1),
            'actual_qty':        round(act_qty, 1),
            'incremental_qty':   round(incr_qty, 1),
            'pct_of_target':     pct_target,
            'bonus_tier':        bonus_tier,
            'bonus_amount_gbp':  bonus_gbp,
        })

    return pd.DataFrame(rows)


# ─── get_pms_summary_by_distributor ──────────────────────────────────────────

def get_pms_summary_by_distributor(
    df_sales: pd.DataFrame,
    year: int,
    year_type: str = "calendar",
) -> pd.DataFrame:
    """
    Aggregate PMS sales by distributor and category.

    Returns DataFrame:
        distributor_code | category | category_label | model | qty | revenue_eur | avg_sp_eur
    """
    df_classified = classify_pms_sales(df_sales)
    df_period = _filter_by_year(df_classified, year, year_type, distributor_code=None)
    df_pms = df_period[df_period['is_pms']].copy()

    if df_pms.empty:
        return pd.DataFrame(columns=[
            'distributor_code', 'category', 'category_label',
            'model', 'qty', 'revenue_eur', 'avg_sp_eur'
        ])

    grp = (
        df_pms.groupby(['distributor_code', 'pms_category', 'pms_model'])
        .agg(
            qty=('billed_qty',      'sum'),
            revenue_eur=('net_sales_value', 'sum'),
        )
        .reset_index()
        .rename(columns={'pms_category': 'category', 'pms_model': 'model'})
    )
    grp['category_label'] = grp['category'].map(CATEGORY_LABELS).fillna(grp['category'])
    grp['avg_sp_eur'] = np.where(grp['qty'] != 0, grp['revenue_eur'] / grp['qty'], 0.0)
    grp = grp.sort_values(['distributor_code', 'revenue_eur'], ascending=[True, False])
    return grp.reset_index(drop=True)


# ─── split_genuine_vs_bvp ─────────────────────────────────────────────────────

def split_genuine_vs_bvp(df_sales: pd.DataFrame) -> dict:
    """
    Split PMS sales into genuine OE vs BVP (Best Value Parts) streams.

    Calls classify_pms_sales internally. Only rows where is_pms=True are
    included in the output DataFrames.

    Returns:
        {
            'genuine':  DataFrame of PMS rows where pms_type == 'genuine',
            'bvp':      DataFrame of PMS rows where pms_type == 'bvp',
            'all_pms':  DataFrame of all PMS rows (genuine + bvp),
        }

    Useful for the PMS page to show "genuine PN capture rate" vs
    "BVP acceptance rate" as separate KPIs.
    """
    df_classified = classify_pms_sales(df_sales)
    df_all_pms = df_classified[df_classified['is_pms']].copy()

    df_genuine = df_all_pms[df_all_pms['pms_type'] == 'genuine'].copy().reset_index(drop=True)
    df_bvp     = df_all_pms[df_all_pms['pms_type'] == 'bvp'].copy().reset_index(drop=True)
    df_all_pms = df_all_pms.reset_index(drop=True)

    return {
        'genuine': df_genuine,
        'bvp':     df_bvp,
        'all_pms': df_all_pms,
    }


# ─── calculate_pms_capture (vehicle age cohort extension) ─────────────────────
# NOTE: registration_year_range is injected into calculate_pms_capture via a
# thin wrapper below rather than modifying the existing signature, so the
# original function remains untouched. The wrapper is the public entry point
# when age cohort filtering is needed.

def calculate_pms_capture_with_cohort(
    df_sales: pd.DataFrame,
    year: int,
    year_type: str = "calendar",
    distributor_code: str = None,
    parc_config: dict = None,
    registration_year_range: tuple = None,
) -> dict:
    """
    Thin wrapper around calculate_pms_capture that adds an age cohort interface.

    registration_year_range: tuple of (start_year, end_year) inclusive, e.g. (2018, 2022).
        Represents the vehicle registration window used to define the target cohort.
        Actual VIN-level filtering is NOT performed because VIN data is not currently
        available in the sales feed. The parameter is accepted to establish the interface
        for future implementation. A warning is injected into the returned dict.

    All other parameters are forwarded unchanged to calculate_pms_capture.

    Returns:
        The full dict from calculate_pms_capture, plus:
            age_cohort_available  bool   — always False until VIN data is integrated
            age_cohort_note       str    — human-readable cohort description (if provided)
            age_cohort_warning    str    — explains why filtering was not applied
    """
    result = calculate_pms_capture(
        df_sales=df_sales,
        year=year,
        year_type=year_type,
        distributor_code=distributor_code,
        parc_config=parc_config,
    )

    result['age_cohort_available'] = False

    if registration_year_range is not None:
        start_yr, end_yr = registration_year_range
        age_min = year - end_yr
        age_max = year - start_yr
        result['age_cohort_note'] = (
            f"N75 registrations {start_yr}–{end_yr} "
            f"({age_min}–{age_max} years old in {year})"
        )
        result['age_cohort_warning'] = (
            "VIN-level registration data is not currently available in the sales feed. "
            "Age cohort filter was NOT applied — results reflect the full parc. "
            "This parameter establishes the interface for future VIN data integration."
        )
    else:
        result['age_cohort_note'] = None
        result['age_cohort_warning'] = None

    return result


# ─── Seasonal adjustment utilities ───────────────────────────────────────────

# Seasonal demand multipliers for PMS parts based on commercial vehicle
# service patterns and ITUK campaign calendar.
_SEASONAL_WEIGHTS: dict = {
    1:  0.85,   # January  — post-holiday slowdown
    2:  0.90,   # February
    3:  1.05,   # March    — pre-spring campaign
    4:  1.15,   # April    — Spring into Service campaign
    5:  1.15,   # May
    6:  1.10,   # June
    7:  0.90,   # July     — holiday season
    8:  0.85,   # August
    9:  1.10,   # September — Brakes & Safety campaign
    10: 1.10,   # October
    11: 1.00,   # November
    12: 0.85,   # December — year-end slowdown
}


def get_seasonal_weights(month: int) -> float:
    """
    Return the seasonal demand multiplier for PMS parts for the given month.

    Multipliers are based on commercial vehicle service patterns and the
    ITUK campaign calendar (Spring into Service, Brakes & Safety).

    Args:
        month: Calendar month as integer (1 = January … 12 = December).

    Returns:
        float multiplier, e.g. 1.15 for April.

    Raises:
        ValueError: if month is not in range 1–12.
    """
    if month not in _SEASONAL_WEIGHTS:
        raise ValueError(f"month must be 1–12, got {month!r}")
    return _SEASONAL_WEIGHTS[month]


def calculate_annualised_capture(
    df_sales: pd.DataFrame,
    year: int,
    year_type: str = "calendar",
    current_month: int = None,
) -> dict:
    """
    Return YTD PMS quantities and, optionally, a seasonally-weighted full-year
    projection.

    When current_month is provided (e.g. 5 for May), the function:
      1. Sums actual PMS billed_qty for the year up to and including current_month.
      2. Divides by the sum of seasonal weights for those months to derive a
         normalised monthly rate.
      3. Multiplies by the sum of all 12 seasonal weights to project the full year.

    When current_month is None the function returns the full-year actuals with no
    projection applied.

    Args:
        df_sales:      Sales DataFrame (requires 'year'/'fiscal_year', 'month',
                       'billed_qty', 'part_number' columns).
        year:          Calendar or fiscal year to analyse.
        year_type:     "calendar" (default) or "fiscal".
        current_month: Latest complete month of data (1–12), or None for full year.

    Returns dict:
        ytd_actual_qty      float  — actual billed qty for the YTD / full-year period
        projected_annual_qty float  — seasonally-projected full-year qty
                                      (equals ytd_actual_qty when current_month is None)
        projection_note     str    — human-readable description of the calculation
    """
    year_col = 'fiscal_year' if year_type == "fiscal" else 'year'

    df_classified = classify_pms_sales(df_sales)
    df_period = df_classified[
        (df_classified[year_col] == year) &
        df_classified['is_pms']
    ].copy()

    if current_month is not None:
        if current_month not in range(1, 13):
            raise ValueError(f"current_month must be 1–12, got {current_month!r}")

        df_ytd = df_period[df_period['month'] <= current_month]
        ytd_qty = float(df_ytd['billed_qty'].sum()) if not df_ytd.empty else 0.0

        # Weight of covered months vs full year
        ytd_weight  = sum(_SEASONAL_WEIGHTS[m] for m in range(1, current_month + 1))
        full_weight = sum(_SEASONAL_WEIGHTS.values())

        projected = (ytd_qty / ytd_weight * full_weight) if ytd_weight > 0 else 0.0

        month_names = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
        }
        note = (
            f"YTD Jan–{month_names[current_month]} projected to full year "
            f"using seasonal weights"
        )
    else:
        ytd_qty   = float(df_period['billed_qty'].sum()) if not df_period.empty else 0.0
        projected = ytd_qty
        note      = f"Full-year {year_type} {year} actuals — no projection applied"

    return {
        'ytd_actual_qty':      ytd_qty,
        'projected_annual_qty': projected,
        'projection_note':      note,
    }


# ─── get_dealer_capture_detail ────────────────────────────────────────────────

def get_dealer_capture_detail(
    df_sales: pd.DataFrame,
    distributor_code: str,
    year: int,
    year_type: str = "calendar",
) -> pd.DataFrame:
    """
    Return a PN-level breakdown of PMS sales for a single distributor.

    Classifies sales, filters to the given distributor and year, then
    aggregates to part_number level with descriptive metadata columns.

    Useful for the "what exactly is this distributor buying?" drill-down on
    the PMS page — shows the mix of genuine vs BVP, which categories dominate,
    and average selling prices.

    Args:
        df_sales:          Full sales DataFrame.
        distributor_code:  Distributor to filter to (exact match on distributor_code).
        year:              Calendar or fiscal year.
        year_type:         "calendar" (default) or "fiscal".

    Returns DataFrame with columns:
        part_number, description, pms_category, pms_model, pms_type,
        total_qty, total_revenue_eur, avg_sp_eur

    Sorted by pms_category (ascending), then total_revenue_eur (descending).
    Returns an empty DataFrame with the correct columns if no PMS sales found.
    """
    _OUTPUT_COLS = [
        'part_number', 'description', 'pms_category', 'pms_model',
        'pms_type', 'total_qty', 'total_revenue_eur', 'avg_sp_eur',
    ]

    df_classified = classify_pms_sales(df_sales)
    df_period = _filter_by_year(df_classified, year, year_type, distributor_code=distributor_code)

    if 'is_pms' not in df_period.columns or df_period.empty:
        return pd.DataFrame(columns=_OUTPUT_COLS)

    df_pms = df_period[df_period['is_pms']].copy()

    if df_pms.empty:
        return pd.DataFrame(columns=_OUTPUT_COLS)

    # description column is optional — fill with empty string if absent
    if 'description' not in df_pms.columns:
        df_pms['description'] = ''

    grp = (
        df_pms.groupby(
            ['part_number', 'description', 'pms_category', 'pms_model', 'pms_type'],
            dropna=False,
        )
        .agg(
            total_qty=('billed_qty',       'sum'),
            total_revenue_eur=('net_sales_value', 'sum'),
        )
        .reset_index()
    )

    grp['avg_sp_eur'] = np.where(
        grp['total_qty'] != 0,
        grp['total_revenue_eur'] / grp['total_qty'],
        0.0,
    )

    grp = grp.sort_values(
        ['pms_category', 'total_revenue_eur'],
        ascending=[True, False],
    ).reset_index(drop=True)

    return grp[_OUTPUT_COLS]
