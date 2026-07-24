"""Dealer sell-out analytics — UTI/ITUK demand signal (PN-level, catalog taxonomy)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from modules.bvp_analytics import normalize_pn_value
from modules.dealer_sales_loader import normalize_pn
from modules.fig_key_catalog import (
    fig_meta,
    load_catalog_index,
    load_taxonomy,
    pms_category_from_pr00,
)
from modules.aim_pn_classifier import (
    filter_report_subgroup,
    infer_filter_part_role,
    load_aim_pn_classification,
)
from modules.bvp_product_nav import catalog_subcategories, group_for_subgroup

from config import DERIVED_DIR, SALES_FACT_PARQUET  # noqa: E402

SALES_PARQUET = SALES_FACT_PARQUET
BVP_PREFIXES = ("1876", "5876")


def load_dimension_and_xref() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dim = pd.read_csv(DERIVED_DIR / "bvp_pn_dimension.csv", dtype=str)
    dim["part_number"] = dim["part_number"].str.strip()
    xref = pd.read_csv(DERIVED_DIR / "genuine_bvp_crossref.csv", dtype=str)
    xref["genuine_pn"] = xref["genuine_pn"].str.strip()
    xref["bvp_pn"] = xref["bvp_pn"].str.strip()

    desc = pd.DataFrame(columns=["part_number", "description"])
    if SALES_PARQUET.exists():
        sf = pd.read_parquet(SALES_PARQUET, columns=["part_number", "description"])
        sf["part_number"] = sf["part_number"].map(normalize_pn)
        desc = (
            sf.dropna(subset=["part_number"])
            .groupby("part_number", as_index=False)["description"]
            .agg(lambda s: s.dropna().iloc[0] if len(s.dropna()) else "")
        )
    return dim, xref, desc


def expected_line_type(part_number: str) -> str | None:
    pn = str(part_number)
    if pn.startswith(BVP_PREFIXES):
        return "bvp"
    if len(pn) == 10 and pn[0] in "89":
        return "genuine"
    return None


def verify_bvp_genuine_integrity(dim: pd.DataFrame, xref: pd.DataFrame) -> dict[str, Any]:
    """Check dimension line_type vs crossref roles (canonical PRISM rules)."""
    gen_in_x = xref.merge(
        dim[["part_number", "line_type"]].rename(columns={"part_number": "genuine_pn", "line_type": "dim_lt"}),
        on="genuine_pn",
        how="left",
    )
    bvp_in_x = xref.merge(
        dim[["part_number", "line_type"]].rename(columns={"part_number": "bvp_pn", "line_type": "dim_lt"}),
        on="bvp_pn",
        how="left",
    )
    bad_gen = gen_in_x[gen_in_x["dim_lt"] != "genuine"]
    bad_bvp = bvp_in_x[bvp_in_x["dim_lt"] != "bvp"]

    dim = dim.copy()
    dim["expected_lt"] = dim["part_number"].map(expected_line_type)
    prefix_miss = dim[
        dim["expected_lt"].notna()
        & dim["line_type"].notna()
        & (dim["expected_lt"] != dim["line_type"])
    ]

    return {
        "xref_genuine_not_dimension_genuine": int(len(bad_gen)),
        "xref_bvp_not_dimension_bvp": int(len(bad_bvp)),
        "dimension_prefix_line_type_mismatch": int(len(prefix_miss)),
        "status": "ok"
        if len(bad_gen) == 0 and len(bad_bvp) == 0
        else "fail",
    }


def _pn_norm(part_number: object) -> str:
    n = normalize_pn_value(part_number) or ""
    return n.lstrip("0") or n


def _has_slug(val: object) -> bool:
    return pd.notna(val) and str(val).strip() not in ("", "nan", "(unclassified)")


def _keyword_product_subgroup(description: object) -> str | None:
    if description is None or (isinstance(description, float) and pd.isna(description)):
        return None
    desc_u = str(description).upper()
    is_brake = "BRAKE" in desc_u or "BRK" in desc_u
    if "OIL" in desc_u and "FILTER" in desc_u:
        return "oil_filter"
    if "FUEL" in desc_u and "FILTER" in desc_u:
        return "fuel_filter"
    if "AIR" in desc_u and "FILTER" in desc_u:
        return "air_filter"
    if "ADBLUE" in desc_u or "AD BLUE" in desc_u or "UREA" in desc_u:
        return "urea_filter"
    if "PAD" in desc_u and is_brake:
        return "brake_pad"
    if ("DISC" in desc_u or "ROTOR" in desc_u) and is_brake:
        return "brake_rotor"
    if "SHOE" in desc_u and is_brake:
        return "brake_shoe"
    if "CLUTCH" in desc_u:
        if "KIT" in desc_u:
            return "clutch_kit"
        if "DISC" in desc_u:
            return "clutch_disc"
        if "COVER" in desc_u or "PLATE" in desc_u:
            return "clutch_pressure_plate"
        return "clutch_disc"
    if "WIPER" in desc_u or "BLADE" in desc_u:
        return "wiper_blade"
    if "BELT" in desc_u and "FAN" in desc_u:
        return "fan_belt"
    if "SHOCK" in desc_u:
        return "shock_absorber"
    return None


def _subgroup_from_fig_key(taxonomy: dict, fig_key: object) -> str | None:
    if not _has_slug(fig_key):
        return None
    fk = str(fig_key).strip()
    meta = fig_meta(taxonomy, fk) or {}
    return meta.get("bvp_subgroup") or meta.get("pms_category")


def _pr00_coarse_slug(pr00_group: object) -> str | None:
    if not _has_slug(pr00_group):
        return None
    g = str(pr00_group).strip()
    return "pr00_" + g.lower().replace(" / ", "_").replace("/", "_").replace(" ", "_")


def enrich_unified_taxonomy(df: pd.DataFrame) -> pd.DataFrame:
    """Resolve product_subgroup / pms_category from BVP catalog, PR00 catalog, fig key, description."""
    if df.empty:
        return df
    tax = load_taxonomy()
    cat = load_catalog_index()
    pms_slugs = set(catalog_subcategories())
    out = df.copy()

    cat_cols = [
        "fig_key",
        "fig_key_label",
        "catalog_pms_category",
        "pr00_group",
        "pr00_level3_type",
        "pr00_family",
        "classification_source",
    ]
    for c in cat_cols:
        if c not in out.columns:
            out[c] = None
    aim_idx = load_aim_pn_classification()
    aim_cols = [
        "aim_l1",
        "aim_l2",
        "aim_l3",
        "catalog_l1",
        "catalog_l2",
        "catalog_l3",
        "filter_part_role",
        "aim_source",
    ]
    for c in aim_cols + ["product_group", "report_subgroup", "taxonomy_level", "taxonomy_source"]:
        if c not in out.columns:
            out[c] = None

    for i, row in out.iterrows():
        pn_n = _pn_norm(row.get("part_number"))
        cat_row = cat.loc[pn_n] if not cat.empty and pn_n in cat.index else None

        if cat_row is not None:
            for src, dst in (
                ("fig_key", "fig_key"),
                ("fig_key_label", "fig_key_label"),
                ("pms_category", "catalog_pms_category"),
                ("pr00_group", "pr00_group"),
                ("pr00_level3_type", "pr00_level3_type"),
                ("pr00_family", "pr00_family"),
                ("classification_source", "classification_source"),
            ):
                v = cat_row.get(src)
                if pd.notna(v) and str(v).strip():
                    out.at[i, dst] = v

        bvp_sub = row.get("product_subgroup")
        bvp_pms = row.get("pms_category")
        resolved_sub = bvp_sub if _has_slug(bvp_sub) else None
        resolved_pms = bvp_pms if _has_slug(bvp_pms) else None
        source = "bvp_dimension" if resolved_sub else None

        if not resolved_sub:
            csub = out.at[i, "catalog_pms_category"]
            if _has_slug(csub) and str(csub) in pms_slugs:
                resolved_sub = str(csub)
                source = source or "parts_catalog"

        if not resolved_sub:
            fk_sub = _subgroup_from_fig_key(tax, out.at[i, "fig_key"])
            if fk_sub:
                resolved_sub = fk_sub
                source = source or "fig_key"

        if not resolved_sub:
            inferred = pms_category_from_pr00(
                tax,
                pr00_group=out.at[i, "pr00_group"],
                level3_type=out.at[i, "pr00_level3_type"],
                fig_key=out.at[i, "fig_key"],
            )
            if inferred and inferred in pms_slugs:
                resolved_sub = inferred
                source = source or "pr00"

        if not resolved_sub:
            kw = _keyword_product_subgroup(row.get("description"))
            if kw:
                resolved_sub = kw
                source = source or "description"

        if not resolved_pms and resolved_sub:
            resolved_pms = resolved_sub

        if not resolved_pms:
            cp = out.at[i, "catalog_pms_category"]
            if _has_slug(cp):
                resolved_pms = cp

        out.at[i, "product_subgroup"] = resolved_sub
        out.at[i, "pms_category"] = resolved_pms
        out.at[i, "taxonomy_source"] = source

        if not aim_idx.empty and pn_n in aim_idx.index:
            ar = aim_idx.loc[pn_n]
            for c in aim_cols:
                v = ar.get(c)
                if pd.notna(v) and str(v).strip():
                    out.at[i, c] = v

        role = out.at[i, "filter_part_role"]
        if not _has_slug(role):
            role = infer_filter_part_role(
                description=row.get("description"),
                level3_type=out.at[i, "pr00_level3_type"],
                fig_key=out.at[i, "fig_key"],
                product_subgroup=resolved_sub,
            )
            out.at[i, "filter_part_role"] = role

        coarse = _pr00_coarse_slug(out.at[i, "pr00_group"])
        if resolved_sub:
            out.at[i, "product_group"] = group_for_subgroup(str(resolved_sub))
            out.at[i, "report_subgroup"] = (
                filter_report_subgroup(str(resolved_sub), role if _has_slug(role) else None)
                or str(resolved_sub)
            )
            out.at[i, "taxonomy_level"] = "pms_subgroup"
        elif coarse:
            out.at[i, "product_group"] = None
            out.at[i, "report_subgroup"] = coarse
            out.at[i, "taxonomy_level"] = "pr00_group"
        else:
            out.at[i, "product_group"] = None
            out.at[i, "report_subgroup"] = None
            out.at[i, "taxonomy_level"] = None

    missing = ~out["report_subgroup"].map(_has_slug)
    out.loc[missing, "report_subgroup"] = "(unclassified)"
    out.loc[missing & ~out["pms_category"].map(_has_slug), "taxonomy_level"] = "unclassified"
    return out


def catalog_pairs_table(xref: pd.DataFrame) -> pd.DataFrame:
    cat = xref[xref["pair_source"].astype(str).str.startswith("catalog")].copy()
    cat = cat.sort_values(["genuine_pn", "catalog_line_no"], na_position="last")
    primary = cat.drop_duplicates(subset=["genuine_pn"], keep="first")
    rev = cat.drop_duplicates(subset=["bvp_pn"], keep="first")
    return primary, rev


def attach_pn_master(
    df: pd.DataFrame,
    dim: pd.DataFrame,
    desc: pd.DataFrame,
    xref: pd.DataFrame,
) -> pd.DataFrame:
    out = df.merge(
        dim[
            [
                "part_number",
                "line_type",
                "pms_category",
                "category_label",
                "product_subgroup",
                "in_bvp_catalog",
            ]
        ],
        on="part_number",
        how="left",
    )
    if "description" in out.columns:
        out = out.drop(columns=["description"])
    out = out.merge(desc, on="part_number", how="left")

    out["expected_line_type"] = out["part_number"].map(expected_line_type)
    out["line_type_ok"] = out.apply(
        lambda r: True
        if pd.isna(r.get("line_type")) or pd.isna(r.get("expected_line_type"))
        else r["line_type"] == r["expected_line_type"],
        axis=1,
    )

    gen_primary, bvp_primary = catalog_pairs_table(xref)
    gen_map = gen_primary.set_index("genuine_pn")[["bvp_pn", "pair_source", "crossref_group"]].to_dict("index")
    bvp_map = bvp_primary.set_index("bvp_pn")[["genuine_pn", "pair_source", "crossref_group"]].to_dict("index")

    def cat_bvp(pn: str) -> str:
        row = gen_map.get(pn)
        return row["bvp_pn"] if row else ""

    def cat_gen(pn: str) -> str:
        row = bvp_map.get(pn)
        return row["genuine_pn"] if row else ""

    def cat_ps(pn: str) -> str:
        row = gen_map.get(pn) or bvp_map.get(pn)
        return str(row.get("pair_source", "")) if row else ""

    out["catalog_paired_bvp"] = out["part_number"].map(cat_bvp)
    out["catalog_paired_genuine"] = out["part_number"].map(cat_gen)
    out["catalog_pair_source"] = out["part_number"].map(cat_ps)
    return enrich_unified_taxonomy(out)


def dealer_qty_on_pn(qty_by_pn: dict[str, float], pn: str) -> float:
    if not pn or (isinstance(pn, float) and pd.isna(pn)):
        return 0.0
    return float(qty_by_pn.get(str(pn).strip(), 0))


def add_sellthrough_columns(
    audit: pd.DataFrame,
    uti_qty_by_pn: dict[str, float],
) -> pd.DataFrame:
    out = audit.copy()
    out["catalog_paired_dealer_ytd"] = out["catalog_paired_bvp"].map(
        lambda p: dealer_qty_on_pn(uti_qty_by_pn, p)
    )
    out["sellthrough_same_pn"] = out.apply(
        lambda r: (r["uti_dealer_ytd"] / r["uti_billing_qty"]) if r["uti_billing_qty"] else None,
        axis=1,
    )
    out["sellthrough_catalog_pair"] = out.apply(
        lambda r: (r["catalog_paired_dealer_ytd"] / r["uti_billing_qty"])
        if r["uti_billing_qty"]
        and r["line_type"] == "genuine"
        and r["catalog_paired_bvp"]
        else None,
        axis=1,
    )
    out["gap_flag"] = out.apply(
        lambda r: "billing_no_dealer"
        if r["uti_billing_qty"] >= 50 and r["uti_dealer_ytd"] == 0
        else ("dealer_no_billing" if r["uti_dealer_ytd"] >= 50 and r["uti_billing_qty"] == 0 else ""),
        axis=1,
    )

    def note(row: pd.Series) -> str:
        if row["line_type"] == "bvp":
            if row["uti_billing_qty"] >= 50 and row["uti_dealer_ytd"] < row["uti_billing_qty"] * 0.5:
                return "bvp_low_sellthrough_same_pn"
            return ""
        if row["line_type"] == "genuine" and row["catalog_paired_bvp"]:
            if row["uti_dealer_ytd"] == 0 and row["catalog_paired_dealer_ytd"] > 0:
                return f"dealer_qty_on_catalog_bvp_{row['catalog_paired_bvp']}"
        if row["line_type_ok"] is False:
            return "line_type_prefix_mismatch"
        return ""

    out["pair_note"] = out.apply(note, axis=1)
    return out
