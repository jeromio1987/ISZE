"""Tag sales rows as PMS (registry + optional BVP catalog)."""

from __future__ import annotations

import pandas as pd

from modules.aim_pn_classifier import attach_pms_filter_roles
from modules.bvp_analytics import enrich_pms_from_dimension_cols
from modules.pms_engine import classify_pms_sales


def tag_pms_sales(
    df_sales: pd.DataFrame,
    df_dim: pd.DataFrame | None = None,
    *,
    fill_catalog_pms: bool = True,
) -> pd.DataFrame:
    """Registry first, then BVP-catalog PMS rows with pms_category when fill_catalog_pms."""
    df = classify_pms_sales(df_sales)
    if fill_catalog_pms and df_dim is not None and not df_dim.empty:
        if "_pn" not in df.columns:
            df["_pn"] = df["part_number"].astype(str).str.strip().str.lstrip("0")
        df = enrich_pms_from_dimension_cols(df, df_dim)
        df = df.drop(columns=["_pn"], errors="ignore")
    return attach_pms_filter_roles(df)
