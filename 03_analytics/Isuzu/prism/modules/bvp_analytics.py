"""
Shared BVP / PMS sales analytics helpers (P0–P2).
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from modules.pms_engine import classify_pms_sales

# ITUK pilot: DVLA-confirmed car park (Mar 2026) — use as capture denominator
UIO_OVERRIDES: dict[str, dict] = {
    "ITUK": {
        "uio_units": 22_389,
        "uio_source": "ituk_dvla_2026",
        "note": "DVLA registration car park; replaces V13 CV UIO for expected-demand sizing",
    },
}

PN_RE = re.compile(r"^0*(\d{10})$")


def normalize_pn_value(val) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    if isinstance(val, (int, np.integer)):
        return str(int(val))
    if isinstance(val, float):
        try:
            return str(int(round(val)))
        except (ValueError, OverflowError):
            pass
    s = str(val).strip()
    if s.lower() in ("nan", "none", "<na>", ""):
        return ""
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    s = s.replace(" ", "")
    if s.isdigit() and len(s) <= 10:
        return s.zfill(10) if len(s) < 10 else s[:10]
    m = PN_RE.match(s)
    return m.group(1) if m else s


def ensure_part_number(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "part_number" not in df.columns:
        if "material" in df.columns:
            df["part_number"] = df["material"]
        else:
            raise ValueError("Sales data needs part_number or material column")
    df["part_number"] = df["part_number"].map(normalize_pn_value)
    return df


def resolve_uio_for_distributor(
    distributor_code: str,
    year: int,
    uio_lookup: dict,
    uio_proxy: dict,
) -> tuple[int, bool, str]:
    """Return (uio_units, proxy_used, uio_source)."""
    if distributor_code in UIO_OVERRIDES:
        o = UIO_OVERRIDES[distributor_code]
        return int(o["uio_units"]), False, o["uio_source"]

    uio = uio_lookup.get((distributor_code, year))
    if uio is not None:
        return int(uio), False, "v18_actual"
    proxy = uio_proxy.get(distributor_code, 0)
    return int(proxy or 0), True, "v18_proxy_2025"


def tag_sales_with_dimension(df_sales: pd.DataFrame, df_dim: pd.DataFrame) -> pd.DataFrame:
    """Attach catalog family + line_type; extend PMS tags from dimension."""
    df = ensure_part_number(df_sales)
    dim = df_dim.drop_duplicates("part_number").copy()
    if df_dim["pms_flag"].dtype == object:
        dim["pms_flag"] = dim["pms_flag"].astype(str).str.lower().isin(
            ("true", "1", "yes")
        )
    dim["_pn"] = dim["part_number"].astype(str).str.strip().str.lstrip("0")
    df["_pn"] = df["part_number"].astype(str).str.strip().str.lstrip("0")

    cat_cols = [
        "product_family",
        "product_subgroup",
        "mix_subgroup",
        "line_type",
        "in_bvp_catalog",
        "pms_flag",
        "pms_category",
        "filter_part_role",
        "pms_capture_eligible",
    ]
    df = df.merge(dim[["_pn"] + cat_cols], on="_pn", how="inner")
    df = classify_pms_sales(df)
    df = enrich_pms_from_dimension_cols(df, dim)  # catalog PMS flags for mix / BVP views
    return df.drop(columns=["_pn"], errors="ignore")


def enrich_pms_from_dimension_cols(df: pd.DataFrame, df_dim: pd.DataFrame) -> pd.DataFrame:
    flagged = df_dim["pms_flag"]
    if flagged.dtype == object:
        flagged = flagged.astype(str).str.lower().isin(("true", "1", "yes"))
    dim = (
        df_dim.loc[flagged & df_dim["pms_category"].notna(),]
        .drop_duplicates("part_number")
        .assign(
            _pn=lambda d: d["part_number"].astype(str).str.strip().str.lstrip("0"),
            dim_line_type=lambda d: d["line_type"],
            dim_pms_category=lambda d: d["pms_category"],
        )[["_pn", "dim_line_type", "dim_pms_category"]]
    )
    if "_pn" not in df.columns:
        df["_pn"] = df["part_number"].astype(str).str.strip().str.lstrip("0")
    df = df.merge(dim, on="_pn", how="left")
    fill = df["dim_pms_category"].notna() & ~df["is_pms"]
    if fill.any():
        df["pms_category"] = df["pms_category"].astype(object)
        df["pms_type"] = df["pms_type"].astype(object)
        df["pms_model"] = df["pms_model"].astype(object)
        df.loc[fill, "is_pms"] = True
        df.loc[fill, "pms_category"] = df.loc[fill, "dim_pms_category"].values
        lt = df.loc[fill, "dim_line_type"]
        df.loc[fill, "pms_type"] = np.where(lt.isin(["genuine", "bvp"]), lt, "bvp")
        df.loc[fill, "pms_model"] = "multi"
    return df.drop(columns=["dim_line_type", "dim_pms_category"], errors="ignore")
