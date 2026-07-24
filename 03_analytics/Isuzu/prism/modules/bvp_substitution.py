"""
Build crossref-tagged sales and substitution rollups (genuine vs BVP per mapped pair).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from modules.bvp_analytics import ensure_part_number
from modules.bvp_crossref import tag_sales_with_crossref
from modules.bvp_product_nav import catalog_subcategories

SALES_KEEP_COLS = [
    "billing_date",
    "year",
    "month",
    "distributor_code",
    "part_number",
    "billed_qty",
    "net_sales_value",
    "sold_to",
    "material",
    "is_credit_note",
]


def build_sales_with_crossref(
    df_sales: pd.DataFrame, df_crossref: pd.DataFrame
) -> pd.DataFrame:
    """Line-level sales that match a genuine↔BVP crossref pair."""
    if df_crossref.empty:
        return pd.DataFrame()

    tagged = tag_sales_with_crossref(df_sales, df_crossref)
    if tagged.empty:
        return tagged

    tagged = tagged.rename(
        columns={"genuine_pn": "xref_genuine_pn", "bvp_pn": "xref_bvp_pn"}
    )
    tagged["pms_in_scope"] = tagged["product_subgroup"].astype(str).isin(catalog_subcategories())

    keep = [c for c in SALES_KEEP_COLS if c in tagged.columns]
    meta = [
        "crossref_id",
        "xref_genuine_pn",
        "xref_bvp_pn",
        "counterpart_pn",
        "crossref_role",
        "product_subgroup",
        "product_family",
        "pair_source",
        "vehicle_model",
        "engine_type",
        "pms_in_scope",
    ]
    cols = keep + [c for c in meta if c in tagged.columns]
    return tagged[cols].sort_values(
        ["year", "distributor_code", "crossref_id", "crossref_role", "billing_date"]
    ).reset_index(drop=True)


def build_substitution_by_pair_year(tagged: pd.DataFrame) -> pd.DataFrame:
    """
    One row per distributor × year × crossref pair with genuine/BVP qty split.
    """
    if tagged.empty:
        return pd.DataFrame()

    keys = [
        "distributor_code",
        "year",
        "crossref_id",
        "xref_genuine_pn",
        "xref_bvp_pn",
        "product_subgroup",
        "pair_source",
    ]
    keys = [k for k in keys if k in tagged.columns]

    qty = (
        tagged.groupby(keys + ["crossref_role"], dropna=False)["billed_qty"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={"genuine": "genuine_qty", "bvp": "bvp_qty"})
    )
    eur = (
        tagged.groupby(keys + ["crossref_role"], dropna=False)["net_sales_value"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={"genuine": "genuine_eur", "bvp": "bvp_eur"})
    )

    out = qty.join(eur, how="outer").reset_index()
    for c in ("genuine_qty", "bvp_qty", "genuine_eur", "bvp_eur"):
        if c not in out.columns:
            out[c] = 0.0
        out[c] = out[c].fillna(0.0)

    out["total_qty"] = out["genuine_qty"] + out["bvp_qty"]
    out["total_eur"] = out["genuine_eur"] + out["bvp_eur"]

    both = (out["genuine_qty"] > 0) & (out["bvp_qty"] > 0)
    gen_only = (out["genuine_qty"] > 0) & (out["bvp_qty"] <= 0)
    bvp_only = (out["bvp_qty"] > 0) & (out["genuine_qty"] <= 0)
    out["substitution_pattern"] = np.select(
        [both, gen_only, bvp_only],
        ["both", "genuine_only", "bvp_only"],
        default="none",
    )
    out["bvp_share_units"] = np.where(
        out["total_qty"] > 0, out["bvp_qty"] / out["total_qty"], np.nan
    )

    if "vehicle_model" in tagged.columns:
        veh = (
            tagged.groupby(keys, dropna=False)["vehicle_model"]
            .agg(lambda s: next((x for x in s if str(x).strip()), ""))
            .reset_index()
        )
        out = out.merge(veh, on=keys, how="left")

    return out.sort_values(keys).reset_index(drop=True)


def build_substitution_by_db_year(pair_df: pd.DataFrame) -> pd.DataFrame:
    """Roll up pair-level substitution to distributor × year (optional subgroup)."""
    if pair_df.empty:
        return pd.DataFrame()

    gcols = ["distributor_code", "year"]
    if "product_subgroup" in pair_df.columns:
        gcols.append("product_subgroup")

    rows: list[dict] = []
    for keys, g in pair_df.groupby(gcols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        rec = dict(zip(gcols, keys))
        rec["pairs_with_sales"] = len(g)
        rec["pairs_both"] = int((g["substitution_pattern"] == "both").sum())
        rec["pairs_genuine_only"] = int((g["substitution_pattern"] == "genuine_only").sum())
        rec["pairs_bvp_only"] = int((g["substitution_pattern"] == "bvp_only").sum())
        rec["genuine_qty"] = float(g["genuine_qty"].sum())
        rec["bvp_qty"] = float(g["bvp_qty"].sum())
        rec["total_qty"] = float(g["total_qty"].sum())
        rec["genuine_eur"] = float(g["genuine_eur"].sum())
        rec["bvp_eur"] = float(g["bvp_eur"].sum())
        n = rec["pairs_with_sales"]
        rec["pct_pairs_both"] = rec["pairs_both"] / n if n else np.nan
        rec["pct_pairs_bvp_only"] = rec["pairs_bvp_only"] / n if n else np.nan
        rec["bvp_share_units"] = (
            rec["bvp_qty"] / rec["total_qty"] if rec["total_qty"] > 0 else np.nan
        )
        rows.append(rec)

    return pd.DataFrame(rows).sort_values(gcols).reset_index(drop=True)
