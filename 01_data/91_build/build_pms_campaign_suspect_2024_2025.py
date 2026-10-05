"""Tag PMS billing lines as campaign-suspect when ASP << reference price.

Reference price:
  - ZPR1 customer condition for CBC / GA / UTI / UMI / KIMA when present
  - else PR00 list for that calendar year

PRD is supporting evidence only (also used for replenishment).

Outputs under 01_data/00_derived/ + short inbox note.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
INBOX = ROOT / "01_data" / "90_INBOX"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))

from config import resolve_mapping_path  # noqa: E402
from modules.data_prep import apply_distributor_codes, load_distributor_mapping  # noqa: E402

FIVE = {1797, 1799, 2372, 2733, 2734}
YEARS = (2024, 2025)
THRESHOLDS = (0.20, 0.30)  # 20% / 30% under reference

OUT_LINE = DER / "pms_campaign_suspect_lines_2024_2025.csv"
OUT_DB = DER / "pms_campaign_suspect_by_db_2024_2025.csv"
OUT_FAM = DER / "pms_campaign_suspect_by_family_2024_2025.csv"
OUT_MD = INBOX / "PMS_CAMPAIGN_SUSPECT_PRICE_VS_LIST_2024_2025.md"


def norm_pn(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip().str.upper()
    return s.str.replace(r"\.0$", "", regex=True).str.lstrip("0").replace("", "0")


def load_sales() -> pd.DataFrame:
    sf = pd.read_parquet(
        DER / "sales_fact.parquet",
        columns=[
            "billing_date",
            "year",
            "sold_to_sap",
            "part_number",
            "description",
            "billed_qty",
            "net_sales_value",
            "saty",
        ],
    )
    sf = sf[sf["year"].isin(YEARS)].copy()
    mapping = load_distributor_mapping(str(resolve_mapping_path()))
    sf = apply_distributor_codes(sf, mapping)
    # hard UTI/UMI by sold-to (never blend)
    sap = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    sf.loc[sap == 1799, "distributor_code"] = "UTI"
    sf.loc[sap == 1797, "distributor_code"] = "UMI"
    sf["customer"] = sap.astype("Int64")
    sf["pn"] = norm_pn(sf["part_number"])
    sf["asp"] = sf["net_sales_value"] / sf["billed_qty"].replace(0, np.nan)
    sf["saty"] = sf["saty"].fillna("blank").astype(str).str.strip().str.upper()
    return sf


def load_pms() -> pd.DataFrame:
    cat = pd.read_csv(
        DER / "parts_catalog_dimension.csv",
        dtype=str,
        usecols=["part_number", "pms_category"],
    )
    cat["pn"] = norm_pn(cat["part_number"])
    cat = cat[
        cat["pms_category"].notna()
        & (cat["pms_category"].str.strip() != "")
        & (cat["pms_category"] != "not_a_service_family")
    ].drop_duplicates("pn")
    return cat[["pn", "pms_category"]]


def load_pr00(year: int) -> pd.DataFrame:
    pr = pd.read_parquet(DER / f"pricing_pr00_ie40_{year}.parquet")
    pr["pn"] = norm_pn(pr["Material"])
    pr["pr00"] = pd.to_numeric(pr["Price_EUR"], errors="coerce")
    return pr[["pn", "pr00"]].dropna().query("pr00 > 0").drop_duplicates("pn")


def load_zpr1(year: int) -> pd.DataFrame:
    path = DER / f"pricing_zpr1_five_{year}.parquet"
    if not path.exists():
        path = DER / f"pricing_zpr1_{year}.parquet"
    z = pd.read_parquet(path)
    # five parquet schema vs old
    if "Customer" in z.columns:
        z["customer"] = pd.to_numeric(z["Customer"], errors="coerce").astype("Int64")
        z["pn"] = norm_pn(z["Material"])
        z["zpr1"] = pd.to_numeric(z["Price"], errors="coerce")
    else:
        z["customer"] = pd.to_numeric(z["customer"], errors="coerce").astype("Int64")
        z["pn"] = norm_pn(z["pn"] if "pn" in z.columns else z["Material"])
        z["zpr1"] = pd.to_numeric(z["Price"], errors="coerce")
    z = z[z["customer"].isin(FIVE)]
    z = z.dropna(subset=["zpr1"]).query("zpr1 > 0")
    z = z.sort_values(["customer", "pn"]).drop_duplicates(["customer", "pn"], keep="last")
    return z[["customer", "pn", "zpr1"]]


def main() -> None:
    print("Loading sales…")
    sf = load_sales()
    pms = load_pms()
    sf = sf.merge(pms, on="pn", how="inner")
    print(f"PMS lines 2024-25: {len(sf):,}")

    frames = []
    for year in YEARS:
        print(f"Join prices {year}…")
        sub = sf[sf["year"] == year].copy()
        pr = load_pr00(year)
        z = load_zpr1(year)
        sub = sub.merge(pr, on="pn", how="left")
        sub = sub.merge(z, on=["customer", "pn"], how="left")
        sub["ref_price"] = np.where(sub["zpr1"].notna() & (sub["zpr1"] > 0), sub["zpr1"], sub["pr00"])
        sub["ref_source"] = np.where(sub["zpr1"].notna() & (sub["zpr1"] > 0), "ZPR1", "PR00")
        sub.loc[sub["ref_price"].isna() | (sub["ref_price"] <= 0), "ref_source"] = "NONE"
        sub["vs_ref_pct"] = sub["asp"] / sub["ref_price"] - 1.0
        sub["campaign_ge20"] = sub["vs_ref_pct"] <= -0.20
        sub["campaign_ge30"] = sub["vs_ref_pct"] <= -0.30
        sub["is_prd"] = sub["saty"] == "PRD"
        frames.append(sub)

    lines = pd.concat(frames, ignore_index=True)
    # keep only rows with a usable reference + positive asp
    usable = lines[lines["ref_source"] != "NONE"].dropna(subset=["asp", "vs_ref_pct"]).copy()
    print(f"Usable vs reference: {len(usable):,} / {len(lines):,}")

    # Line extract: suspects only (20%+) to keep file size sane, plus a thin sample of normals? suspects only.
    suspects = usable[usable["campaign_ge20"]].copy()
    out_cols = [
        "year",
        "billing_date",
        "distributor_code",
        "customer",
        "part_number",
        "pn",
        "description",
        "pms_category",
        "saty",
        "is_prd",
        "billed_qty",
        "net_sales_value",
        "asp",
        "ref_price",
        "ref_source",
        "vs_ref_pct",
        "campaign_ge20",
        "campaign_ge30",
    ]
    suspects[out_cols].to_csv(OUT_LINE, index=False)

    def rollup(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
        rows = []
        for key, g in df.groupby(keys, dropna=False):
            if not isinstance(key, tuple):
                key = (key,)
            e = float(g["net_sales_value"].sum())
            if e <= 0:
                continue
            rec = dict(zip(keys, key))
            rec.update(
                {
                    "n_lines": int(len(g)),
                    "billed_eur": e,
                    "pct_eur_ge20_under_ref": 100
                    * float(g.loc[g["campaign_ge20"], "net_sales_value"].sum())
                    / e,
                    "pct_eur_ge30_under_ref": 100
                    * float(g.loc[g["campaign_ge30"], "net_sales_value"].sum())
                    / e,
                    "pct_eur_prd": 100 * float(g.loc[g["is_prd"], "net_sales_value"].sum()) / e,
                    "pct_eur_ge20_and_prd": 100
                    * float(g.loc[g["campaign_ge20"] & g["is_prd"], "net_sales_value"].sum())
                    / e,
                    "among_ge20_pct_that_are_prd": (
                        100
                        * float(g.loc[g["campaign_ge20"] & g["is_prd"], "net_sales_value"].sum())
                        / float(g.loc[g["campaign_ge20"], "net_sales_value"].sum())
                        if g.loc[g["campaign_ge20"], "net_sales_value"].sum() > 0
                        else np.nan
                    ),
                    "pct_eur_ref_zpr1": 100
                    * float(g.loc[g["ref_source"] == "ZPR1", "net_sales_value"].sum())
                    / e,
                }
            )
            rows.append(rec)
        return pd.DataFrame(rows)

    by_db = rollup(usable, ["year", "distributor_code"]).sort_values(
        ["year", "pct_eur_ge20_under_ref"], ascending=[True, False]
    )
    by_fam = rollup(usable, ["year", "pms_category"]).sort_values(
        ["year", "pct_eur_ge20_under_ref"], ascending=[True, False]
    )
    by_db_fam = rollup(usable, ["year", "distributor_code", "pms_category"]).sort_values(
        ["year", "distributor_code", "pct_eur_ge20_under_ref"], ascending=[True, True, False]
    )

    by_db.to_csv(OUT_DB, index=False)
    by_fam.to_csv(OUT_FAM, index=False)
    by_db_fam.to_csv(DER / "pms_campaign_suspect_by_db_family_2024_2025.csv", index=False)

    # Network totals
    def net_row(year: int) -> dict:
        g = usable[usable["year"] == year]
        e = float(g["net_sales_value"].sum())
        return {
            "year": year,
            "billed_eur": e,
            "pct_ge20": 100 * float(g.loc[g["campaign_ge20"], "net_sales_value"].sum()) / e,
            "pct_ge30": 100 * float(g.loc[g["campaign_ge30"], "net_sales_value"].sum()) / e,
            "pct_prd": 100 * float(g.loc[g["is_prd"], "net_sales_value"].sum()) / e,
            "among_ge20_prd": 100
            * float(g.loc[g["campaign_ge20"] & g["is_prd"], "net_sales_value"].sum())
            / max(float(g.loc[g["campaign_ge20"], "net_sales_value"].sum()), 1),
        }

    n24, n25 = net_row(2024), net_row(2025)

    # Top DBs / families for narrative
    top_db_25 = by_db[by_db["year"] == 2025].head(8)
    top_fam_25 = by_fam[by_fam["year"] == 2025].head(10)
    iuk = by_db[(by_db["distributor_code"] == "IUK") & (by_db["year"].isin([2024, 2025]))]
    iuk_air = by_db_fam[
        (by_db_fam["distributor_code"] == "IUK")
        & (by_db_fam["pms_category"] == "air_filter")
        & (by_db_fam["year"].isin([2024, 2025]))
    ]

    lines_md = []
    lines_md.append("# PMS campaign-suspect — price vs your list / condition")
    lines_md.append("")
    lines_md.append(
        "**Rule:** billed ASP ≥20% (or ≥30%) under reference. "
        "Reference = ZPR1 for CBC/GA/UTI/UMI/KIMA when present, else PR00. "
        "PRD is support only — not the definition."
    )
    lines_md.append("")
    lines_md.append("## Network (all PMS parts with a reference price)")
    lines_md.append("")
    lines_md.append("| Year | PMS billed | ≥20% under ref | ≥30% under ref | PRD share | Of the ≥20% under, how much is PRD |")
    lines_md.append("|---|---:|---:|---:|---:|---:|")
    for n in (n24, n25):
        lines_md.append(
            f"| {n['year']} | EUR {n['billed_eur']/1e6:.2f}M | {n['pct_ge20']:.1f}% | {n['pct_ge30']:.1f}% | {n['pct_prd']:.1f}% | {n['among_ge20_prd']:.1f}% |"
        )
    lines_md.append("")
    lines_md.append(
        "Reading: deep under-reference euro is the campaign-shaped slice. "
        "High PRD with low under-reference share means PRD is mostly replenishment."
    )
    lines_md.append("")
    lines_md.append("## Top distributors 2025 by % euro ≥20% under reference")
    lines_md.append("")
    lines_md.append("| DB | Billed | ≥20% under | ≥30% under | PRD | ≥20% that is PRD |")
    lines_md.append("|---|---:|---:|---:|---:|---:|")
    for _, r in top_db_25.iterrows():
        lines_md.append(
            f"| {r['distributor_code']} | EUR {r['billed_eur']/1e3:.0f}k | {r['pct_eur_ge20_under_ref']:.1f}% | "
            f"{r['pct_eur_ge30_under_ref']:.1f}% | {r['pct_eur_prd']:.1f}% | {r['among_ge20_pct_that_are_prd']:.0f}% |"
        )
    lines_md.append("")
    lines_md.append("## Top PMS families 2025 by % euro ≥20% under reference")
    lines_md.append("")
    lines_md.append("| Family | Billed | ≥20% under | ≥30% under | PRD |")
    lines_md.append("|---|---:|---:|---:|---:|")
    for _, r in top_fam_25.iterrows():
        lines_md.append(
            f"| {r['pms_category']} | EUR {r['billed_eur']/1e3:.0f}k | {r['pct_eur_ge20_under_ref']:.1f}% | "
            f"{r['pct_eur_ge30_under_ref']:.1f}% | {r['pct_eur_prd']:.1f}% |"
        )
    lines_md.append("")
    lines_md.append("## IUK check (air filters + all PMS)")
    lines_md.append("")
    if len(iuk):
        lines_md.append(iuk[["year", "billed_eur", "pct_eur_ge20_under_ref", "pct_eur_ge30_under_ref", "pct_eur_prd", "among_ge20_pct_that_are_prd"]].to_string(index=False))
        lines_md.append("")
    if len(iuk_air):
        lines_md.append("IUK air_filter:")
        lines_md.append(iuk_air[["year", "billed_eur", "pct_eur_ge20_under_ref", "pct_eur_ge30_under_ref", "pct_eur_prd", "among_ge20_pct_that_are_prd"]].to_string(index=False))
        lines_md.append("")
    lines_md.append("## Files")
    lines_md.append("")
    lines_md.append(f"- `{OUT_LINE}` — line-level suspects (≥20% under)")
    lines_md.append(f"- `{OUT_DB}`")
    lines_md.append(f"- `{OUT_FAM}`")
    lines_md.append(f"- `{DER / 'pms_campaign_suspect_by_db_family_2024_2025.csv'}`")
    OUT_MD.write_text("\n".join(lines_md), encoding="utf-8")

    print("Network 2024", n24)
    print("Network 2025", n25)
    print("Wrote", OUT_LINE, "suspects", len(suspects))
    print("Wrote", OUT_DB)
    print("Wrote", OUT_FAM)
    print("Wrote", OUT_MD)


if __name__ == "__main__":
    main()
