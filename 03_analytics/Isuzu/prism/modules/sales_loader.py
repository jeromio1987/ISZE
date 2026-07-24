"""
Load sales for PRISM (GPS / PMS).

Priority:
  1. ISZE/Data/derived/sales_fact.parquet  (canonical — fast)
  2. ISZE/Data/derived/sales_fact.csv
  3. Legacy TSV/CSV under prism/data or Projects/Isuzu/data
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

from config import LEGACY_SALES_CANDIDATES, SALES_FACT_PARQUET, SALES_FACT_CSV, resolve_first_existing
from modules.data_prep import apply_distributor_codes, ensure_sales_part_columns, load_sales_data

# Non-part lines that sit inside the sales extract as placeholder part numbers.
# These are freight / financial / adjustment lines, NOT genuine parts, and must be
# excluded from parts-revenue rankings and spend-per-unit (data-integrity flag A).
NON_PART_LINE_KIND = {
    "TRANSPORT": "freight",
    "REBATE": "rebate",
    "LATE PAYMENT INTEREST": "finance",
    "DISRACK01": "adjustment",
    # INTERFACE MX2-T is diagnostic hardware, not a spare part — keep it out of
    # parts revenue / genuine-vs-BVP mix (€279K across these three SKUs).
    "5874123810": "tool",
    "5874123811": "tool",
    "5874123812": "tool",
}

# Known master-data description corrections (data-integrity flag B). Keyed by the
# raw part_number; value replaces the mislabelled description. 550047337 is described
# as "Rim ..." but the spec (15W40 CK4, 3×5L) is engine oil, not a rim.
DESCRIPTION_OVERRIDES = {
    "550047337": "Engine Oil 15W40 CK4 (3x5L) [corrected: master described as Rim]",
    "550047252": "Engine Oil 15W40 CJ4 (209L) [corrected: master described as Rim]",
}


def _normalize_sales_fact_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Align Phase 1 / CY export column names to PRISM expectations."""
    rename = {
        "Billing Date": "billing_date",
        "Sold-to pt": "sold_to",
        "Sold-to party": "sold_to",
        "Billed Quantity": "billed_qty",
        "Net value": "net_sales_value",
        "Net Value": "net_sales_value",
        "Net price": "net_sales_value",
        "SaTy": "saty",
    }
    if "part_number" not in df.columns:
        rename["Material"] = "part_number"
    if "material" not in df.columns and "Material" in df.columns:
        rename.setdefault("Material", "material")
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "sold_to" not in df.columns and "Payer" in df.columns:
        df["sold_to"] = df["Payer"]
    if "part_number" not in df.columns and "material" in df.columns:
        df["part_number"] = df["material"]
    return df


def _finish_sales_frame(df: pd.DataFrame, df_mapping: pd.DataFrame) -> pd.DataFrame:
    """Apply distributor mapping + dtypes when loading from parquet (skip load_sales_data file IO)."""
    from modules.data_prep import EXCLUDED_CODES, _get_fiscal_year

    df = _normalize_sales_fact_columns(df)
    if "distributor_code" not in df.columns or df["distributor_code"].isna().all():
        df = apply_distributor_codes(df, df_mapping)
    df = df[~df["distributor_code"].isin(EXCLUDED_CODES)].copy()

    df["billing_date"] = pd.to_datetime(df["billing_date"], dayfirst=True, errors="coerce")
    if "year" not in df.columns or df["year"].isna().all():
        df["year"] = df["billing_date"].dt.year
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
    df["month"] = df["billing_date"].dt.month
    df["quarter"] = df["billing_date"].dt.quarter
    df["fiscal_year"] = df.apply(_get_fiscal_year, axis=1)
    df["net_sales_value"] = pd.to_numeric(
        df.get("net_sales_value", 0), errors="coerce"
    ).fillna(0)
    df["billed_qty"] = pd.to_numeric(df.get("billed_qty", 0), errors="coerce").fillna(0)
    # Flag H: SAP extract has zero negative-value rows, but SaTy carries explicit
    # CR (credit) / RE (return) codes on positive-value lines (verified 2026-07-03:
    # 350 rows, EUR2.17M, 0 qty-negative across 2023-2026 — Jerome flagged these may
    # not be pre-netted). Until ERP confirms netting, treat CR/RE as credit notes.
    saty_col = df["saty"] if "saty" in df.columns else pd.Series("", index=df.index)
    is_return_saty = saty_col.astype(str).str.strip().str.upper().isin(["CR", "RE"])
    df["is_credit_note"] = (df["net_sales_value"] < 0) | is_return_saty

    # Flag A: tag non-part lines so parts-revenue views can exclude them.
    pn_key = df["part_number"].astype(str).str.strip()
    df["line_kind"] = pn_key.map(NON_PART_LINE_KIND).fillna("part")

    # Flag B: correct known mislabelled descriptions.
    if "description" in df.columns:
        override = pn_key.map(DESCRIPTION_OVERRIDES)
        df["description"] = override.where(override.notna(), df["description"])

    return ensure_sales_part_columns(df)


def load_prism_sales(df_mapping: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """
    Load sales for GPS/PMS. Returns (dataframe, human-readable source path).
    """
    if SALES_FACT_PARQUET.exists():
        df = pd.read_parquet(SALES_FACT_PARQUET)
        df = _finish_sales_frame(df, df_mapping)
        unmapped_share = (df["distributor_code"] == "UNMAPPED").mean()
        if unmapped_share > 0.15:
            legacy = resolve_first_existing(LEGACY_SALES_CANDIDATES[2:])
            if legacy:
                print(
                    f"[sales_loader] Parquet has {unmapped_share:.0%} UNMAPPED — "
                    f"using legacy file: {legacy}"
                )
                return load_sales_data(str(legacy), df_mapping), str(legacy)
        return df, str(SALES_FACT_PARQUET)

    if SALES_FACT_CSV.exists():
        df = pd.read_csv(SALES_FACT_CSV, low_memory=False)
        return _finish_sales_frame(df, df_mapping), str(SALES_FACT_CSV)

    legacy = resolve_first_existing(LEGACY_SALES_CANDIDATES[2:])
    if legacy:
        return load_sales_data(str(legacy), df_mapping), str(legacy)

    raise FileNotFoundError(
        "No sales data found. Build canonical file first:\n"
        f"  python scripts/build_sales_fact_from_cy.py\n"
        f"Target: {SALES_FACT_PARQUET}\n"
        "Or place legacy TSV in prism/data/."
    )
