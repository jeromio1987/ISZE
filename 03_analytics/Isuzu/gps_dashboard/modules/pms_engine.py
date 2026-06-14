"""
Module: PMS Coverage Engine
ISZE GPS Dashboard — PMS Classification & Capture Rate Analysis

Phase 1 scope: N75 / 7.5t fleet (NPR75/4HK1 and NPR88/4JZ1).
N35 (NLR87/NLR88) included in registry but shown as reference only.

Source: ITUK guidance Apr 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime

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
    "brake_pad":             "Brake Pad",
    "brake_shoe":            "Brake Shoe",
    "clutch_disc":           "Clutch Disc",
    "clutch_pressure_plate": "Clutch Pressure Plate",
}

# Phase 1 categories (N75 focus for capture rate KPIs)
PHASE1_CATEGORIES = ["oil_filter", "fuel_filter", "air_filter", "brake_pad"]

# Model groups for parc-based calculations
N75_MODELS = {"N75_4HK1", "N75_4JZ1"}
N35_MODELS = {"N35_RZ4E", "N35_4JZ1"}


# ─── Default parc config ──────────────────────────────────────────────────────
DEFAULT_PARC_CONFIG = {
    "N75_surviving_parc":    8515,   # 10-year surviving UK parc
    "N35_surviving_parc":    9818,   # 10-year surviving UK parc
    "N75_services_per_year": 0.5,    # 40,000km interval / ~20,000km avg annual
    "N35_services_per_year": 0.75,   # N35.125 at 20,000km; blended
    "addressable_pct":       0.70,   # S2+S3 proportion (est. 70% of parc)
    "scope":                 "N75_only",  # "N75_only" | "all"
}


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
    cfg = {**DEFAULT_PARC_CONFIG, **(parc_config or {})}

    # ── Classify and filter ────────────────────────────────────────────────
    df_classified = classify_pms_sales(df_sales)
    df_period = _filter_by_year(df_classified, year, year_type, distributor_code)

    # Guard: if year column didn't exist, df_period may be an empty copy with or
    # without is_pms; ensure is_pms column exists before boolean indexing.
    if 'is_pms' not in df_period.columns or df_period.empty:
        df_pms = pd.DataFrame(columns=list(df_period.columns) + [
            'is_pms', 'pms_category', 'pms_model', 'pms_type'
        ])
    else:
        df_pms = df_period[df_period['is_pms']].copy()

    # ── Determine scope ────────────────────────────────────────────────────
    if df_pms.empty:
        df_pms_scope = df_pms
    elif cfg['scope'] == "N75_only":
        scope_models = N75_MODELS | {"multi"}  # include multi-model PNs (shared across N75 variants)
        df_pms_scope = df_pms[
            (df_pms['pms_model'].isin(scope_models)) |
            (df_pms['pms_model'] == "multi")
        ]
    else:
        df_pms_scope = df_pms

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

    # ── Expected quantities (parc × services/year × addressable_pct) ──────
    n75_addressable = (
        cfg['N75_surviving_parc']
        * cfg['N75_services_per_year']
        * cfg['addressable_pct']
    )
    n35_addressable = (
        cfg['N35_surviving_parc']
        * cfg['N35_services_per_year']
        * cfg['addressable_pct']
    ) if cfg['scope'] == "all" else 0.0

    # Each service requires 1 of each consumable category
    expected_by_category: dict = {}
    consumables_n75 = ["oil_filter", "fuel_filter", "air_filter"]
    wear_n75 = {
        "brake_pad":             n75_addressable * 0.5,   # replaced every ~2 services
        "clutch_disc":           n75_addressable * 0.2,
        "clutch_pressure_plate": n75_addressable * 0.2,
    }
    for cat in consumables_n75:
        expected_by_category[cat] = {'qty': n75_addressable}
    for cat, qty in wear_n75.items():
        expected_by_category[cat] = {'qty': qty}

    if cfg['scope'] == "all":
        consumables_n35 = ["oil_filter", "fuel_filter", "air_filter"]
        wear_n35 = {
            "brake_pad":             n35_addressable * 0.5,
            "brake_shoe":            n35_addressable * 0.5,
            "clutch_disc":           n35_addressable * 0.2,
            "clutch_pressure_plate": n35_addressable * 0.2,
        }
        for cat in consumables_n35:
            existing = expected_by_category.get(cat, {}).get('qty', 0)
            expected_by_category[cat] = {'qty': existing + n35_addressable}
        for cat, qty in wear_n35.items():
            existing = expected_by_category.get(cat, {}).get('qty', 0)
            expected_by_category[cat] = {'qty': existing + qty}

    # ── Capture rates ──────────────────────────────────────────────────────
    capture_rate_by_category: dict = {}
    for cat, exp in expected_by_category.items():
        exp_qty = exp['qty']
        act_qty = actual_by_category.get(cat, {}).get('qty', 0.0)
        if exp_qty > 0:
            capture_rate_by_category[cat] = min(act_qty / exp_qty, 1.0)  # cap at 100%
        else:
            capture_rate_by_category[cat] = 0.0

    # ── Revenue opportunity ────────────────────────────────────────────────
    revenue_opportunity: dict = {}
    for cat, exp in expected_by_category.items():
        exp_qty = exp['qty']
        act_data = actual_by_category.get(cat, {})
        act_qty = act_data.get('qty', 0.0)
        act_rev = act_data.get('revenue_eur', 0.0)
        avg_sp = (act_rev / act_qty) if act_qty > 0 else 0.0
        gap_qty = max(exp_qty - act_qty, 0.0)
        revenue_opportunity[cat] = gap_qty * avg_sp

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
        rows.append({
            'category':       cat,
            'category_label': CATEGORY_LABELS.get(cat, cat),
            'actual_qty':     act_qty,
            'expected_qty':   exp_qty,
            'capture_rate':   cap_rate,
            'avg_sp_eur':     avg_sp,
            'revenue_gap_eur': rev_gap,
            'actual_rev_eur': act_rev,
        })

    summary_df = pd.DataFrame(rows).sort_values('revenue_gap_eur', ascending=False).reset_index(drop=True)

    total_actual_eur     = sum(v['revenue_eur'] for v in actual_by_category.values())
    total_opportunity_eur = sum(revenue_opportunity.values())

    return {
        'actual_by_category':        actual_by_category,
        'expected_by_category':      expected_by_category,
        'capture_rate_by_category':  capture_rate_by_category,
        'revenue_opportunity':        revenue_opportunity,
        'total_actual_eur':          total_actual_eur,
        'total_opportunity_eur':     total_opportunity_eur,
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
