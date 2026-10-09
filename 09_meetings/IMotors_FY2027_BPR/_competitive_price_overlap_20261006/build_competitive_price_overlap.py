# -*- coding: utf-8 -*-
"""I-Motors Portugal: competitive / contested StD vs aftermarket brand prices.

Primary lens: OTHER AFTERMARKET BRANDS (Eucon / KS AM / online IAM), not OEM grey.
OEM peer (genuine_grey / Amayama) kept as secondary only.

Outputs under this folder. Read-only on source data.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

AIM = DER / "_releases" / "aim_pn_classification_release_2026-10-04.csv"
REF_DB = 1.40
REF_DLR = 1.275
REF_FACTOR = REF_DB * REF_DLR  # 1.785 — reference dealer price from list

# Aftermarket brand price types (primary)
AM_PRICE_TYPES = {
    "aftermarket_retail",
    "aftermarket_rrp",
    "aftermarket_trade",
    "online_median",
    "marketplace",
    "survey_workshop",
    "survey_list",
}
# Secondary OEM-peer / grey
OEM_PEER_TYPES = {"genuine_grey", "dealer"}

# Contested wear AIM L1 families (secondary basket beside catalogue Competitive parts)
CONTESTED_AIM_L1 = {
    "Brakes",
    "Clutch",
    "Suspension",
    "Maintenance Service",
    "Accident & Body",
}


def norm(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.lstrip("0")
        .replace("", "0")
        .replace("nan", "")
        .replace("None", "")
    )


def load_aim() -> pd.DataFrame:
    a = pd.read_csv(
        AIM,
        dtype=str,
        usecols=[
            "part_number",
            "catalog_l1",
            "catalog_l2",
            "catalog_l3",
            "aim_l1_fixed",
            "aim_l2_fixed",
            "aim_l3_fixed",
        ],
    )
    a["pn"] = norm(a.part_number)
    a["catalog_l1"] = a["catalog_l1"].fillna("(unclassified)")
    a["catalog_l2"] = a["catalog_l2"].fillna("(unclassified)")
    a["aim_l1"] = a["aim_l1_fixed"].fillna("(unclassified)")
    a["aim_l2"] = a["aim_l2_fixed"].fillna("(unclassified)")
    a["aim_l3"] = a["aim_l3_fixed"].fillna(a.get("catalog_l3", pd.Series(dtype=str))).fillna("(unclassified)")
    return a.drop_duplicates("pn")[
        ["pn", "catalog_l1", "catalog_l2", "aim_l1", "aim_l2", "aim_l3"]
    ]


def load_list() -> pd.Series:
    p = pd.read_parquet(DER / "pricing_pr00_ie40.parquet", columns=["part_number", "newest_pn", "sp_eur"])
    p["pn"] = norm(p.part_number)
    p["new"] = norm(p.newest_pn)
    p = p[p.sp_eur > 0]
    own = p.drop_duplicates("pn").set_index("pn").sp_eur
    newest = p.set_index("pn").sp_eur.reindex(p.new.values)
    newest.index = p.pn.values
    newest = newest[~newest.index.duplicated()].dropna()
    return own.combine_first(newest)


def load_desc() -> pd.Series:
    p = pd.read_parquet(DER / "pricing_pr00_ie40.parquet", columns=["part_number", "description"])
    p["pn"] = norm(p.part_number)
    return p.drop_duplicates("pn").set_index("pn")["description"]


def load_sellout() -> pd.DataFrame:
    so = pd.concat(
        [
            pd.read_csv(
                DER / f"dealer_sellout_long_PORTUGAL_{p}.csv",
                dtype={"part_number": str, "period": str},
            )
            for p in ("CY2025", "CY2026YTD")
        ]
    )
    so = so[so.period_grain == "month"].copy()
    so["ym"] = so.period
    so["pn"] = norm(so.part_number)
    so["qty"] = pd.to_numeric(so.qty, errors="coerce").fillna(0.0)
    return so[["ym", "pn", "qty"]]


def load_am_prices() -> pd.DataFrame:
    obs = pd.read_parquet(DER / "price_observations.parquet")
    obs["pn"] = norm(obs.part_no)
    obs["price_eur"] = pd.to_numeric(obs.price_eur, errors="coerce")
    obs = obs[obs.price_eur.notna() & (obs.price_eur > 0)].copy()

    am = obs[obs.price_type.isin(AM_PRICE_TYPES)].copy()
    am["lens"] = "aftermarket_brand"
    oem = obs[obs.price_type.isin(OEM_PEER_TYPES)].copy()
    oem["lens"] = "oem_peer_secondary"

    # Prefer median per PN within aftermarket; keep min for overprice flag
    def agg_lens(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(
                columns=[
                    "pn",
                    "lens",
                    "am_price_min_eur",
                    "am_price_median_eur",
                    "am_price_max_eur",
                    "am_n_obs",
                    "am_brands",
                    "am_sources",
                    "am_countries",
                    "am_price_types",
                ]
            )
        g = (
            df.groupby("pn")
            .agg(
                am_price_min_eur=("price_eur", "min"),
                am_price_median_eur=("price_eur", "median"),
                am_price_max_eur=("price_eur", "max"),
                am_n_obs=("price_eur", "size"),
                am_brands=("competitor_brand", lambda s: ", ".join(sorted({str(x) for x in s.dropna()}))[:300]),
                am_sources=("loader", lambda s: ", ".join(sorted({str(x) for x in s.dropna()}))[:200]),
                am_countries=("country", lambda s: ", ".join(sorted({str(x) for x in s.dropna()}))[:80]),
                am_price_types=("price_type", lambda s: ", ".join(sorted({str(x) for x in s.dropna()}))[:120]),
            )
            .reset_index()
        )
        g["lens"] = df["lens"].iloc[0]
        return g

    am_agg = agg_lens(am)
    oem_agg = agg_lens(oem)
    return am_agg, oem_agg, am, oem


def load_bvp_crossref() -> pd.DataFrame:
    p = DER / "genuine_bvp_crossref.csv"
    if not p.exists():
        return pd.DataFrame(columns=["genuine_pn", "bvp_pn"])
    g = pd.read_csv(p, dtype=str, usecols=["genuine_pn", "bvp_pn"])
    g["genuine_pn"] = norm(g.genuine_pn)
    g["bvp_pn"] = norm(g.bvp_pn)
    return g.dropna().drop_duplicates()


def period_blocks(ym: str) -> dict[str, bool]:
    y, m = int(ym[:4]), int(ym[5:7])
    return {
        "CY2025": y == 2025,
        "CY2026_JanAug": y == 2026 and m <= 8,
        "FY26_AprAug": (y == 2025 and m >= 4 and m <= 8),
        "FY27_AprAug": (y == 2026 and m >= 4 and m <= 8),
        "clean_Oct25_Aug26": (y == 2025 and m >= 10) or (y == 2026 and m <= 8),
    }


def main() -> None:
    aim = load_aim()
    plist = load_list()
    desc = load_desc()
    so = load_sellout()
    am_agg, oem_agg, am_raw, oem_raw = load_am_prices()
    xref = load_bvp_crossref()

    so = so.merge(aim, on="pn", how="left")
    so["catalog_l1"] = so["catalog_l1"].fillna("(unclassified)")
    so["aim_l1"] = so["aim_l1"].fillna("(unclassified)")
    so["aim_l2"] = so["aim_l2"].fillna("(unclassified)")
    so["list_eur_unit"] = so["pn"].map(plist)
    so["list_eur"] = so["qty"] * so["list_eur_unit"].fillna(0.0)
    so["is_competitive_catalog"] = so["catalog_l1"] == "Competitive parts"
    so["is_contested_aim"] = so["aim_l1"].isin(CONTESTED_AIM_L1)
    so["in_scope"] = so["is_competitive_catalog"] | so["is_contested_aim"]

    scope = so[so["in_scope"]].copy()
    for name, flag in [
        ("CY2025", lambda ym: period_blocks(ym)["CY2025"]),
        ("CY2026_JanAug", lambda ym: period_blocks(ym)["CY2026_JanAug"]),
        ("FY26_AprAug", lambda ym: period_blocks(ym)["FY26_AprAug"]),
        ("FY27_AprAug", lambda ym: period_blocks(ym)["FY27_AprAug"]),
        ("clean_Oct25_Aug26", lambda ym: period_blocks(ym)["clean_Oct25_Aug26"]),
    ]:
        scope[f"qty_{name}"] = np.where(scope["ym"].map(flag), scope["qty"], 0.0)
        scope[f"list_{name}"] = np.where(scope["ym"].map(flag), scope["list_eur"], 0.0)

    # Monthly family totals — competitive catalog + contested AIM
    monthly = (
        scope.groupby(["ym", "is_competitive_catalog", "aim_l1"], as_index=False)
        .agg(std_qty=("qty", "sum"), std_list_eur=("list_eur", "sum"), n_pn=("pn", "nunique"))
        .sort_values(["ym", "std_list_eur"], ascending=[True, False])
    )
    monthly.to_csv(OUT / "monthly_std_competitive_contested.csv", index=False)

    # Family block summary
    fam_rows = []
    for label, mask in [
        ("Competitive parts (catalogue L1)", scope["is_competitive_catalog"]),
        ("Contested AIM L1 basket", scope["is_contested_aim"]),
        ("Union (competitive OR contested)", scope["in_scope"]),
    ]:
        sub = scope[mask]
        row = {"basket": label, "n_pn": sub["pn"].nunique()}
        for blk in ["CY2025", "CY2026_JanAug", "FY26_AprAug", "FY27_AprAug", "clean_Oct25_Aug26"]:
            row[f"std_qty_{blk}"] = float(sub[f"qty_{blk}"].sum())
            row[f"std_list_eur_{blk}"] = float(sub[f"list_{blk}"].sum())
        # annualise 2026 Jan-Aug to 12m for direction compare
        q25 = row["std_qty_CY2025"]
        q26 = row["std_qty_CY2026_JanAug"]
        e25 = row["std_list_eur_CY2025"]
        e26 = row["std_list_eur_CY2026_JanAug"]
        row["qty_runrate_2026_vs_CY2025_pct"] = (
            ((q26 / 8 * 12) / q25 - 1) * 100 if q25 > 0 else None
        )
        row["list_runrate_2026_vs_CY2025_pct"] = (
            ((e26 / 8 * 12) / e25 - 1) * 100 if e25 > 0 else None
        )
        q_fy26 = row["std_qty_FY26_AprAug"]
        q_fy27 = row["std_qty_FY27_AprAug"]
        e_fy26 = row["std_list_eur_FY26_AprAug"]
        e_fy27 = row["std_list_eur_FY27_AprAug"]
        row["qty_FY27_vs_FY26_AprAug_pct"] = (
            (q_fy27 / q_fy26 - 1) * 100 if q_fy26 > 0 else None
        )
        row["list_FY27_vs_FY26_AprAug_pct"] = (
            (e_fy27 / e_fy26 - 1) * 100 if e_fy26 > 0 else None
        )
        fam_rows.append(row)
    fam_df = pd.DataFrame(fam_rows)
    fam_df.to_csv(OUT / "basket_std_period_compare.csv", index=False)

    # AIM L1 inside competitive catalog
    comp = scope[scope["is_competitive_catalog"]]
    aim_l1_blocks = []
    for l1, g in comp.groupby("aim_l1"):
        r = {"aim_l1": l1, "n_pn": g["pn"].nunique()}
        for blk in ["CY2025", "CY2026_JanAug", "FY26_AprAug", "FY27_AprAug"]:
            r[f"std_list_eur_{blk}"] = float(g[f"list_{blk}"].sum())
            r[f"std_qty_{blk}"] = float(g[f"qty_{blk}"].sum())
        e26a = r["std_list_eur_FY26_AprAug"]
        e27a = r["std_list_eur_FY27_AprAug"]
        r["list_FY27_vs_FY26_AprAug_pct"] = (e27a / e26a - 1) * 100 if e26a > 0 else None
        aim_l1_blocks.append(r)
    aim_l1_df = pd.DataFrame(aim_l1_blocks).sort_values("std_list_eur_CY2025", ascending=False)
    aim_l1_df.to_csv(OUT / "competitive_catalog_by_aim_l1_periods.csv", index=False)

    # PN grain for competitive catalog (primary) + contested with AM price
    pn = (
        scope.groupby(
            ["pn", "catalog_l1", "catalog_l2", "aim_l1", "aim_l2", "is_competitive_catalog", "is_contested_aim"],
            as_index=False,
        )
        .agg(
            std_qty_CY2025=("qty_CY2025", "sum"),
            std_list_CY2025=("list_CY2025", "sum"),
            std_qty_CY2026_JanAug=("qty_CY2026_JanAug", "sum"),
            std_list_CY2026_JanAug=("list_CY2026_JanAug", "sum"),
            std_qty_FY26_AprAug=("qty_FY26_AprAug", "sum"),
            std_list_FY26_AprAug=("list_FY26_AprAug", "sum"),
            std_qty_FY27_AprAug=("qty_FY27_AprAug", "sum"),
            std_list_FY27_AprAug=("list_FY27_AprAug", "sum"),
            std_qty_clean=("qty_clean_Oct25_Aug26", "sum"),
            std_list_clean=("list_clean_Oct25_Aug26", "sum"),
        )
    )
    pn["description"] = pn["pn"].map(desc)
    pn["list_eur_unit"] = pn["pn"].map(plist)
    pn["ref_dealer_eur"] = pn["list_eur_unit"] * REF_FACTOR

    # Direction: prefer FY Apr-Aug (same 5 months); fallback CY run-rate on list €
    pn["list_delta_fy_apr_aug"] = pn["std_list_FY27_AprAug"] - pn["std_list_FY26_AprAug"]
    pn["qty_delta_fy_apr_aug"] = pn["std_qty_FY27_AprAug"] - pn["std_qty_FY26_AprAug"]
    pn["list_chg_fy_pct"] = np.where(
        pn["std_list_FY26_AprAug"] > 0,
        pn["list_delta_fy_apr_aug"] / pn["std_list_FY26_AprAug"] * 100,
        np.nan,
    )
    # CY: compare 2026 Jan-Aug annualised to CY2025
    pn["list_2026_runrate"] = pn["std_list_CY2026_JanAug"] / 8 * 12
    pn["list_chg_cy_runrate_pct"] = np.where(
        pn["std_list_CY2025"] > 0,
        (pn["list_2026_runrate"] / pn["std_list_CY2025"] - 1) * 100,
        np.nan,
    )
    # Dropping = FY Apr-Aug list € down ≥15% AND FY26 base ≥ €200, OR CY run-rate down ≥20% with CY2025 ≥ €400
    pn["dropping"] = (
        ((pn["std_list_FY26_AprAug"] >= 200) & (pn["list_chg_fy_pct"] <= -15))
        | ((pn["std_list_CY2025"] >= 400) & (pn["list_chg_cy_runrate_pct"] <= -20))
    )
    pn["growing"] = (
        ((pn["std_list_FY26_AprAug"] >= 200) & (pn["list_chg_fy_pct"] >= 15))
        | ((pn["std_list_CY2025"] >= 400) & (pn["list_chg_cy_runrate_pct"] >= 20))
    )

    # Join aftermarket brand prices (primary)
    pn = pn.merge(am_agg, on="pn", how="left", suffixes=("", "_am"))
    # Expand via genuine↔BVP crossref: if PN has no AM price, try counterpart
    am_by_pn = am_agg.set_index("pn")
    def price_via_xref(row):
        if pd.notna(row.get("am_price_median_eur")):
            return pd.Series(
                {
                    "am_price_via": "direct",
                    "am_xref_pn": row["pn"],
                }
            )
        # try as genuine → bvp, or bvp → genuine
        bvp = xref.loc[xref["genuine_pn"] == row["pn"], "bvp_pn"]
        gen = xref.loc[xref["bvp_pn"] == row["pn"], "genuine_pn"]
        for counterpart, via in [
            (bvp, "via_bvp_pair"),
            (gen, "via_genuine_pair"),
        ]:
            for cpn in counterpart.unique():
                if cpn in am_by_pn.index:
                    return pd.Series({"am_price_via": via, "am_xref_pn": cpn})
        return pd.Series({"am_price_via": None, "am_xref_pn": None})

    via = pn.apply(price_via_xref, axis=1)
    pn = pd.concat([pn, via], axis=1)
    need_fill = pn["am_price_median_eur"].isna() & pn["am_xref_pn"].notna()
    for col in [
        "am_price_min_eur",
        "am_price_median_eur",
        "am_price_max_eur",
        "am_n_obs",
        "am_brands",
        "am_sources",
        "am_countries",
        "am_price_types",
    ]:
        pn.loc[need_fill, col] = pn.loc[need_fill, "am_xref_pn"].map(am_by_pn[col])

    # Secondary OEM peer
    oem_cols = {
        "am_price_min_eur": "oem_peer_min_eur",
        "am_price_median_eur": "oem_peer_median_eur",
        "am_n_obs": "oem_peer_n_obs",
        "am_brands": "oem_peer_brands",
        "am_sources": "oem_peer_sources",
    }
    oem_ren = oem_agg.rename(columns=oem_cols)[["pn"] + list(oem_cols.values())]
    pn = pn.merge(oem_ren, on="pn", how="left")

    # Price indices — reference dealer price vs aftermarket brand median
    pn["has_am_price"] = pn["am_price_median_eur"].notna()
    pn["index_ref_vs_am_median"] = pn["ref_dealer_eur"] / pn["am_price_median_eur"]
    pn["index_list_vs_am_median"] = pn["list_eur_unit"] / pn["am_price_median_eur"]
    pn["index_ref_vs_am_min"] = pn["ref_dealer_eur"] / pn["am_price_min_eur"]
    # Overpriced vs AM: reference dealer price above AM median (index > 1.10 = ≥10% above)
    pn["overpriced_vs_am"] = pn["has_am_price"] & (pn["index_ref_vs_am_median"] > 1.10)
    # Gap € per piece at dealer working price
    pn["overprice_gap_eur_per_pc"] = np.where(
        pn["overpriced_vs_am"],
        pn["ref_dealer_eur"] - pn["am_price_median_eur"],
        0.0,
    )
    # Lost StD list €: use the same window that triggered "dropping"
    pn["std_list_lost_fy"] = np.maximum(-pn["list_delta_fy_apr_aug"], 0.0)
    pn["std_list_lost_cy_runrate"] = np.maximum(pn["std_list_CY2025"] - pn["list_2026_runrate"], 0.0)
    fy_drop = (pn["std_list_FY26_AprAug"] >= 200) & (pn["list_chg_fy_pct"] <= -15)
    pn["std_list_lost"] = np.where(fy_drop, pn["std_list_lost_fy"], pn["std_list_lost_cy_runrate"])
    # Impact score: lost StD list € × relative overprice gap (ref/AM - 1)
    pn["overprice_ratio_gap"] = np.maximum(pn["index_ref_vs_am_median"] - 1.0, 0.0)
    pn["impact_score"] = pn["std_list_lost"] * pn["overprice_ratio_gap"]

    # Scope tags for shortlist
    pn["scope_tag"] = np.where(
        pn["is_competitive_catalog"] & pn["is_contested_aim"],
        "competitive_catalog+contested_aim",
        np.where(pn["is_competitive_catalog"], "competitive_catalog", "contested_aim_only"),
    )

    # End-goal intersection (need real lost €, not a zero-score CY-only quirk)
    hit = pn[pn["dropping"] & pn["overpriced_vs_am"] & (pn["std_list_lost"] > 50)].sort_values(
        "impact_score", ascending=False
    )
    near_drop_no_price = pn[pn["dropping"] & ~pn["has_am_price"]].sort_values("std_list_lost", ascending=False)
    near_exp_growing = pn[pn["overpriced_vs_am"] & pn["growing"]].sort_values(
        "index_ref_vs_am_median", ascending=False
    )

    out_cols = [
        "pn",
        "description",
        "scope_tag",
        "catalog_l1",
        "catalog_l2",
        "aim_l1",
        "aim_l2",
        "list_eur_unit",
        "ref_dealer_eur",
        "am_price_min_eur",
        "am_price_median_eur",
        "am_price_max_eur",
        "am_n_obs",
        "am_brands",
        "am_sources",
        "am_countries",
        "am_price_types",
        "am_price_via",
        "am_xref_pn",
        "index_ref_vs_am_median",
        "index_list_vs_am_median",
        "index_ref_vs_am_min",
        "overprice_gap_eur_per_pc",
        "overprice_ratio_gap",
        "std_list_CY2025",
        "std_list_CY2026_JanAug",
        "std_list_FY26_AprAug",
        "std_list_FY27_AprAug",
        "std_qty_FY26_AprAug",
        "std_qty_FY27_AprAug",
        "list_chg_fy_pct",
        "list_chg_cy_runrate_pct",
        "std_list_lost",
        "impact_score",
        "oem_peer_median_eur",
        "oem_peer_n_obs",
        "oem_peer_sources",
    ]
    hit[out_cols].to_csv(OUT / "shortlist_dropping_and_overpriced_vs_am.csv", index=False)
    near_drop_no_price[out_cols].head(80).to_csv(OUT / "near_miss_dropping_no_am_price.csv", index=False)
    near_exp_growing[out_cols].head(80).to_csv(OUT / "near_miss_overpriced_but_std_growing.csv", index=False)
    pn[out_cols + ["dropping", "growing", "overpriced_vs_am", "has_am_price"]].to_csv(
        OUT / "pn_competitive_contested_full.csv", index=False
    )

    # Coverage / sufficiency
    comp_pn = pn[pn["is_competitive_catalog"]]
    cov = {
        "sold_to": 519,
        "distributor": "I-Motors Portugal",
        "primary_lens": "aftermarket brand prices (not OEM peer)",
        "secondary_lens": "OEM peer / grey import (Amayama genuine_grey) — not used for shortlist gate",
        "std_source": "dealer_sellout_long_PORTUGAL_CY2025 + CY2026YTD MONTH rows through 2026-08",
        "aim_release": AIM.name,
        "competitive_definition": "catalog_l1 == Competitive parts (AIM L1 remaps these into Brakes/Suspension/…)",
        "contested_aim_l1": sorted(CONTESTED_AIM_L1),
        "list_basis": "PR00 IE40 list (pricing_pr00_ie40)",
        "reference_dealer_price": f"list × {REF_DB} × {REF_DLR} = ×{REF_FACTOR:.3f} (spoken as reference dealer price / %GM channel, not factors in findings)",
        "overpriced_rule": "reference dealer price > aftermarket brand median × 1.10",
        "dropping_rule": "FY26→FY27 Apr–Aug list€ ≤ −15% with FY26 base ≥ €200, OR CY2025→2026 run-rate ≤ −20% with CY2025 ≥ €400",
        "am_price_types": sorted(AM_PRICE_TYPES),
        "coverage": {
            "competitive_catalog_std_pns": int(comp_pn["pn"].nunique()),
            "competitive_catalog_std_list_eur_all_months": float(comp_pn["std_list_CY2025"].sum() + comp_pn["std_list_CY2026_JanAug"].sum()),
            "competitive_with_am_price_pns": int(comp_pn["has_am_price"].sum()),
            "competitive_with_am_price_list_eur_cy2025": float(comp_pn.loc[comp_pn["has_am_price"], "std_list_CY2025"].sum()),
            "competitive_cy2025_list_eur": float(comp_pn["std_list_CY2025"].sum()),
            "competitive_am_coverage_share_cy2025_list": float(
                comp_pn.loc[comp_pn["has_am_price"], "std_list_CY2025"].sum() / comp_pn["std_list_CY2025"].sum()
                if comp_pn["std_list_CY2025"].sum() > 0
                else 0
            ),
            "shortlist_hit_pns": int(len(hit)),
            "shortlist_impact_score_sum": float(hit["impact_score"].sum()),
            "shortlist_std_list_lost_sum": float(hit["std_list_lost"].sum()),
            "near_miss_dropping_no_am_pns": int(len(near_drop_no_price)),
            "near_miss_overpriced_growing_pns": int(len(near_exp_growing)),
            "am_obs_rows": int(len(am_raw)),
            "am_obs_pns_global": int(am_raw["pn"].nunique()),
            "oem_peer_obs_pns_global": int(oem_raw["pn"].nunique()),
            "am_countries_note": "Eucon/KS aftermarket prices are mostly DE/NO/UK — not Portugal shop prices",
        },
        "basket_direction": fam_df.to_dict(orient="records"),
        "top_shortlist": hit[out_cols].head(25).to_dict(orient="records"),
        "gaps": [
            "Aftermarket brand prices cover only a minority of Portugal competitive StD PNs (see coverage share).",
            "Observed prices are DE/NO/UK IAM listings, not Portuguese dealer purchase prices.",
            "Price tiers mixed (retail / RRP / trade / online median) — never average across types into one 'true' price; we use median of available AM obs per PN as a working signal.",
            "Reference dealer price uses the standard channel dials (×1.40 × 1.275); I-Motors actual %GM may differ.",
            "genuine_bvp_crossref expands a few PNs but most competitive StD still has no AM observation.",
            "Sep 2026 StD KPI euros have no PN grain — out of this cut.",
            "List € is ISZE list × qty, not I-Motors net to dealer.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(cov, indent=2, default=str), encoding="utf-8")

    # FINDINGS.md — plain English for Jerome
    write_findings(cov, fam_df, aim_l1_df, hit, near_drop_no_price, near_exp_growing, comp_pn)
    print("OK", OUT)
    print("shortlist", len(hit), "impact", round(float(hit["impact_score"].sum()), 1))


def write_findings(cov, fam_df, aim_l1_df, hit, near_drop, near_grow, comp_pn) -> None:
    c = cov["coverage"]
    # basket lines
    def basket_line(name: str) -> str:
        r = fam_df[fam_df["basket"] == name].iloc[0]
        fy = r["list_FY27_vs_FY26_AprAug_pct"]
        cy = r["list_runrate_2026_vs_CY2025_pct"]
        return (
            f"- **{name}:** CY2025 sales to dealer list €{r['std_list_eur_CY2025']:,.0f} "
            f"→ 2026 Jan–Aug €{r['std_list_eur_CY2026_JanAug']:,.0f} "
            f"(annualised vs CY2025: {cy:+.1f}% on list €). "
            f"FY Apr–Aug: €{r['std_list_eur_FY26_AprAug']:,.0f} → €{r['std_list_eur_FY27_AprAug']:,.0f} "
            f"({fy:+.1f}%)."
        )

    top_lines = []
    for i, r in enumerate(hit.head(15).itertuples(index=False), 1):
        d = r.description if isinstance(r.description, str) and r.description != "nan" else "(no description)"
        fam = f"{r.aim_l1} / {r.aim_l2}"
        top_lines.append(
            f"{i}. **{d}** (`{r.pn}`) — {fam}. "
            f"Sales to dealer list € lost (working cut): €{r.std_list_lost:,.0f}. "
            f"Our reference dealer price €{r.ref_dealer_eur:,.2f} vs aftermarket brand median €{r.am_price_median_eur:,.2f} "
            f"(index {r.index_ref_vs_am_median:.2f}, brands: {str(r.am_brands)[:80]}). "
            f"FY Apr–Aug list €: €{r.std_list_FY26_AprAug:,.0f} → €{r.std_list_FY27_AprAug:,.0f}."
        )

    # sufficiency verdict
    share = c["competitive_am_coverage_share_cy2025_list"] * 100
    if share >= 40 and c["shortlist_hit_pns"] >= 5:
        sufficiency = (
            f"**Partially sufficient for a priced shortlist.** About {share:.0f}% of Portugal "
            f"Competitive-parts sales-to-dealer list € in CY2025 has an aftermarket brand price on file "
            f"({c['competitive_with_am_price_pns']} of {c['competitive_catalog_std_pns']} part numbers). "
            f"That is enough to rank candidates, not enough to close the whole competitive book."
        )
    elif share >= 15:
        sufficiency = (
            f"**Thin but usable for a first shortlist.** Aftermarket brand prices cover only "
            f"{share:.0f}% of Competitive-parts sales-to-dealer list € in CY2025 "
            f"({c['competitive_with_am_price_pns']} part numbers). Treat hits as evidence where the join exists; "
            f"do not generalise to every competitive part."
        )
    else:
        sufficiency = (
            f"**Insufficient to conclude on the full competitive book.** Aftermarket brand coverage is only "
            f"{share:.0f}% of Competitive-parts sales-to-dealer list €. Report what the join shows; stop short of a market-wide claim."
        )

    # top dropping AIM L1 inside competitive
    drop_fams = aim_l1_df[aim_l1_df["list_FY27_vs_FY26_AprAug_pct"].notna()].copy()
    drop_fams = drop_fams.sort_values("list_FY27_vs_FY26_AprAug_pct").head(8)
    fam_txt = []
    for r in drop_fams.itertuples(index=False):
        fam_txt.append(
            f"- {r.aim_l1}: FY Apr–Aug list €{r.std_list_eur_FY26_AprAug:,.0f} → €{r.std_list_eur_FY27_AprAug:,.0f} "
            f"({r.list_FY27_vs_FY26_AprAug_pct:+.1f}%)"
        )

    near_d = near_drop.head(10)
    near_g = near_grow.head(8)
    near_d_txt = []
    for r in near_d.itertuples(index=False):
        d = r.description if isinstance(r.description, str) else ""
        near_d_txt.append(
            f"- {d} (`{r.pn}`), {r.aim_l1}: list € lost ~€{r.std_list_lost:,.0f} — **no aftermarket brand price on file**"
        )
    near_g_txt = []
    for r in near_g.itertuples(index=False):
        d = r.description if isinstance(r.description, str) else ""
        near_g_txt.append(
            f"- {d} (`{r.pn}`): reference dealer €{r.ref_dealer_eur:,.2f} vs AM median €{r.am_price_median_eur:,.2f} "
            f"(index {r.index_ref_vs_am_median:.2f}) but sales to dealer list € is **rising**"
        )

    md = f"""# I-Motors Portugal — competitive parts vs aftermarket brand prices

Computed 2026-10-06. Primary lens: **other aftermarket brands** (Blue Print, Bosch, Delphi, Febi, Herth+Buss, etc. in the price ledger). OEM peer / grey import is secondary only and does **not** gate the shortlist.

## Data sufficiency

{sufficiency}

| Source | What it gives | Limit |
|---|---|---|
| Portugal sales to dealer MONTH files | PN × month qty through **2026-08** | No Sep PN; network total, not by dealer |
| AIM release 2026-10-04 | Catalogue **Competitive parts** + AIM family | Competitive is catalogue L1; AIM remaps into Brakes / Suspension / … |
| `price_observations` aftermarket types | Brand prices + cross-ref IAM (Eucon, KS AM, …) | Mostly **DE / NO / UK**, not Portugal shops |
| PR00 IE40 list | Our list €; reference dealer price = list × 1.40 × 1.275 | Not I-Motors net; actual Portugal %GM may differ |
| Genuine↔BVP cross-ref | Fills a few missing AM prices via the paired number | Small lift only |

**Coverage (Competitive catalogue L1, Portugal sales to dealer):**  
{c['competitive_with_am_price_pns']} part numbers with an aftermarket brand price = **{share:.1f}%** of CY2025 competitive sales-to-dealer list € (€{c['competitive_with_am_price_list_eur_cy2025']:,.0f} of €{c['competitive_cy2025_list_eur']:,.0f}).

## Direction — is competitive sales to dealer dropping?

List € = qty × ISZE list (same basis as the AIM evolution pack).

{basket_line("Competitive parts (catalogue L1)")}
{basket_line("Contested AIM L1 basket")}
{basket_line("Union (competitive OR contested)")}

Inside Competitive catalogue, AIM families with the softest FY Apr–Aug (FY2026 → FY2027) list €:

{chr(10).join(fam_txt) if fam_txt else "(no family rows)"}

## End-goal shortlist — dropping **and** expensive vs aftermarket brands

Rule: sales to dealer list € dropping (FY Apr–Aug −15%+ or CY run-rate −20%+) **and** our **reference dealer price** more than 10% above the aftermarket brand **median** on that part (or its genuine/BVP pair).

Ranked by impact = list € lost × overprice gap ratio.

**Hits: {c['shortlist_hit_pns']} part numbers.** Combined working list € lost on those hits: €{c['shortlist_std_list_lost_sum']:,.0f}.

{chr(10).join(top_lines) if top_lines else "_No PN cleared both filters under the current thresholds._"}

## Near-misses

**Dropping, but no aftermarket brand price** (priority to get a brand quote):

{chr(10).join(near_d_txt) if near_d_txt else "(none)"}

**Looks expensive vs aftermarket brands, but sales to dealer is growing** (price pressure, not volume loss yet):

{chr(10).join(near_g_txt) if near_g_txt else "(none)"}

## What this does **not** prove

- That Portuguese workshops pay the Eucon/KS listing — those are foreign aftermarket observations.
- That list € lost is all lost to aftermarket brands (stock, campaigns, and mix also move the line).
- That every Competitive part is overpriced — most have **no** brand price on file.
- OEM peer / Amayama grey as a substitute for aftermarket brand competition (kept in the full table as a secondary column only).

## Output files

| File | Content |
|---|---|
| `shortlist_dropping_and_overpriced_vs_am.csv` | End-goal hits |
| `near_miss_dropping_no_am_price.csv` | Dropping, no brand price |
| `near_miss_overpriced_but_std_growing.csv` | Expensive, StD rising |
| `basket_std_period_compare.csv` | Basket CY / FY direction |
| `competitive_catalog_by_aim_l1_periods.csv` | Competitive remapped to AIM L1 |
| `monthly_std_competitive_contested.csv` | Monthly series |
| `pn_competitive_contested_full.csv` | Full PN table |
| `summary.json` | Machine summary + coverage |

Builder: `build_competitive_price_overlap.py`
"""
    (OUT / "FINDINGS.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
