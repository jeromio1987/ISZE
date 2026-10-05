"""ZPR1 customer condition price vs PR00 list — PMS parts, 2024 vs 2025.

Outputs:
  zpr1_vs_pr00_pms_by_customer_2024_2025.csv
  zpr1_vs_pr00_pms_by_customer_family_2024_2025.csv
  90_INBOX/CUSTOMER_CONDITION_PRICE_VS_LIST_PMS_2024_2025.md
  refresh zpr1_vs_pr00_by_payer_year.csv (2024/2025 rows for customers present)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
INBOX = ROOT / "01_data" / "90_INBOX"

HARD_PAYER = {
    1797: "UMI",
    1799: "UTI",
    2372: "ZPR1_2372",
    2733: "CBC_2733",
    2734: "CBC_2734",
}


def norm_pn(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip().str.upper()
    return s.str.replace(r"\.0$", "", regex=True)


def wmean(vals, weights) -> float:
    vals = np.asarray(vals, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.isfinite(vals) & np.isfinite(weights) & (weights > 0)
    if not mask.any():
        return float("nan")
    return float(np.average(vals[mask], weights=weights[mask]))


def family_bucket(c: str) -> str:
    c = str(c).lower()
    if "filter" in c:
        return "filters"
    if "brake" in c or "lining" in c:
        return "brakes"
    if "clutch" in c or "release_bearing" in c or "pilot_bearing" in c:
        return "clutch"
    if c in {"fan_belt", "water_pump", "shock_absorber", "leaf_spring", "bushing"}:
        return "maintenance_wear"
    return "other_pms"


def load_pms_map() -> pd.DataFrame:
    cat = pd.read_csv(
        DER / "parts_catalog_dimension.csv",
        dtype=str,
        usecols=["part_number", "pms_category"],
        low_memory=False,
    )
    cat["pn"] = norm_pn(cat["part_number"])
    cat = cat[
        cat["pms_category"].notna()
        & (cat["pms_category"].str.strip() != "")
        & (cat["pms_category"] != "not_a_service_family")
    ].copy()
    cat["pms_family"] = cat["pms_category"].map(family_bucket)
    return cat.drop_duplicates(subset=["pn"], keep="first")[
        ["pn", "pms_category", "pms_family"]
    ]


def load_customers() -> pd.DataFrame:
    cust = pd.read_parquet(DER / "pricing_zpr1_customers.parquet")
    cust["customer_code_int"] = pd.to_numeric(
        cust["customer_code"], errors="coerce"
    ).astype("Int64")
    cust["payer"] = cust["customer_alias"].fillna("").replace("", pd.NA)
    cust["payer"] = cust["payer"].fillna(cust["customer_name"])
    cust["payer"] = cust["customer_code_int"].map(HARD_PAYER).fillna(cust["payer"])
    return cust


def load_sales_weights(years=(2024, 2025)) -> pd.DataFrame:
    sf = pd.read_parquet(
        DER / "sales_fact.parquet",
        columns=["sold_to_sap", "part_number", "year", "net_sales_value"],
    )
    sf = sf[sf["year"].isin(years)].copy()
    sf["customer"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce").astype("Int64")
    sf["pn"] = norm_pn(sf["part_number"])
    sf["billed_eur"] = pd.to_numeric(sf["net_sales_value"], errors="coerce").fillna(0.0)
    return (
        sf.groupby(["year", "customer", "pn"], as_index=False)["billed_eur"].sum()
    )


def year_join(list_year: int, pms: pd.DataFrame, sales_w: pd.DataFrame) -> pd.DataFrame:
    z = pd.read_parquet(DER / f"pricing_zpr1_{list_year}.parquet").copy()
    pr = pd.read_parquet(DER / f"pricing_pr00_ie40_{list_year}.parquet").copy()

    z["pn"] = norm_pn(z["Material"])
    z["customer"] = pd.to_numeric(z["Customer"], errors="coerce").astype("Int64")
    z["zpr1"] = pd.to_numeric(z["Price"], errors="coerce")
    z = z.sort_values(["customer", "pn", "Valid_From"]).drop_duplicates(
        subset=["customer", "pn"], keep="last"
    )

    pr["pn"] = norm_pn(pr["Material"])
    pr["pr00"] = pd.to_numeric(pr["Price_EUR"], errors="coerce")
    pr = pr.drop_duplicates(subset=["pn"], keep="last")

    m = z.merge(pr[["pn", "pr00"]], on="pn", how="inner")
    m = m.merge(pms, on="pn", how="inner")
    m = m[(m["zpr1"] > 0) & (m["pr00"] > 0)].copy()
    m["zpr1_vs_pr00_pct"] = (m["zpr1"] / m["pr00"] - 1.0) * 100.0
    m["list_year"] = list_year

    w = sales_w[sales_w["year"] == list_year][["customer", "pn", "billed_eur"]]
    m = m.merge(w, on=["customer", "pn"], how="left")
    m["billed_eur"] = m["billed_eur"].fillna(0.0)
    return m


def risk_flag(med25: float) -> str:
    if pd.isna(med25):
        return "no_2025"
    if med25 >= 0:
        return "above_list"
    if med25 >= -8:
        return "tight_vs_list"
    if med25 <= -25:
        return "deep_discount"
    return "mid_discount"


def fmt_pct(x) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{x:+.1f}%"


def fmt_eur(x) -> str:
    if pd.isna(x) or x == 0:
        return "EUR 0 / no billed match"
    return f"EUR {x:,.0f}"


def main() -> None:
    pms = load_pms_map()
    cust = load_customers()
    sales_w = load_sales_weights()
    cmap = cust.set_index("customer_code_int")[["payer", "customer_name"]].to_dict(
        "index"
    )

    print("PMS PNs:", len(pms), pms["pms_family"].value_counts().to_dict())

    all_lines = pd.concat(
        [year_join(y, pms, sales_w) for y in (2024, 2025)], ignore_index=True
    )
    print(
        "joined PMS lines:",
        len(all_lines),
        "customers:",
        sorted(all_lines["customer"].dropna().unique().tolist()),
    )
    print(all_lines.groupby(["list_year", "customer"]).size().to_dict())

    # customer × year
    rows = []
    for (yr, cust_code), g in all_lines.groupby(["list_year", "customer"]):
        billed = float(g["billed_eur"].sum())
        med = float(g["zpr1_vs_pr00_pct"].median())
        rows.append(
            {
                "list_year": int(yr),
                "customer": int(cust_code),
                "n_pms_pns": int(g["pn"].nunique()),
                "billed_eur_pms": round(billed, 2),
                "median_zpr1_vs_pr00_pct": round(med, 2),
                "p25_zpr1_vs_pr00_pct": round(
                    float(g["zpr1_vs_pr00_pct"].quantile(0.25)), 2
                ),
                "p75_zpr1_vs_pr00_pct": round(
                    float(g["zpr1_vs_pr00_pct"].quantile(0.75)), 2
                ),
                "wmean_zpr1_vs_pr00_pct": round(
                    wmean(g["zpr1_vs_pr00_pct"], g["billed_eur"]), 2
                ),
                "pct_pns_above_list": round(
                    float((g["zpr1_vs_pr00_pct"] > 0).mean() * 100), 2
                ),
                "pct_pns_deep_discount_le_m20": round(
                    float((g["zpr1_vs_pr00_pct"] <= -20).mean() * 100), 2
                ),
            }
        )
    cust_sum = pd.DataFrame(rows)
    cust_sum["payer"] = cust_sum["customer"].map(
        lambda c: cmap.get(c, {}).get("payer", str(c))
    )
    cust_sum["customer_name"] = cust_sum["customer"].map(
        lambda c: cmap.get(c, {}).get("customer_name", "")
    )

    yoy_rows = []
    for c in sorted(cust_sum["customer"].unique()):
        sub = cust_sum[cust_sum["customer"] == c].set_index("list_year")
        r = {
            "customer": int(c),
            "payer": sub.iloc[0]["payer"],
            "customer_name": sub.iloc[0]["customer_name"],
        }
        for y in (2024, 2025):
            if y in sub.index:
                r[f"n_pms_pns_{y}"] = int(sub.loc[y, "n_pms_pns"])
                r[f"billed_eur_pms_{y}"] = float(sub.loc[y, "billed_eur_pms"])
                r[f"median_zpr1_vs_pr00_pct_{y}"] = float(
                    sub.loc[y, "median_zpr1_vs_pr00_pct"]
                )
                r[f"wmean_zpr1_vs_pr00_pct_{y}"] = float(
                    sub.loc[y, "wmean_zpr1_vs_pr00_pct"]
                )
                r[f"pct_pns_above_list_{y}"] = float(sub.loc[y, "pct_pns_above_list"])
                r[f"pct_pns_deep_discount_le_m20_{y}"] = float(
                    sub.loc[y, "pct_pns_deep_discount_le_m20"]
                )
            else:
                for k in (
                    "n_pms_pns",
                    "billed_eur_pms",
                    "median_zpr1_vs_pr00_pct",
                    "wmean_zpr1_vs_pr00_pct",
                    "pct_pns_above_list",
                    "pct_pns_deep_discount_le_m20",
                ):
                    r[f"{k}_{y}"] = np.nan

        if pd.notna(r.get("median_zpr1_vs_pr00_pct_2024")) and pd.notna(
            r.get("median_zpr1_vs_pr00_pct_2025")
        ):
            r["median_pct_pts_yoy"] = round(
                r["median_zpr1_vs_pr00_pct_2025"] - r["median_zpr1_vs_pr00_pct_2024"],
                2,
            )
            r["wmean_pct_pts_yoy"] = round(
                r["wmean_zpr1_vs_pr00_pct_2025"] - r["wmean_zpr1_vs_pr00_pct_2024"],
                2,
            )
        else:
            r["median_pct_pts_yoy"] = np.nan
            r["wmean_pct_pts_yoy"] = np.nan

        r["revision_risk_flag"] = risk_flag(r.get("median_zpr1_vs_pr00_pct_2025"))
        r["note"] = "UTI!=UMI; never blend; IUK!=ITUK; PMS pms_category only"
        yoy_rows.append(r)

    by_cust = pd.DataFrame(yoy_rows)
    by_cust["billed_eur_sort"] = by_cust[
        ["billed_eur_pms_2024", "billed_eur_pms_2025"]
    ].max(axis=1)
    by_cust = by_cust.sort_values("billed_eur_sort", ascending=False).drop(
        columns=["billed_eur_sort"]
    )

    out_cust = DER / "zpr1_vs_pr00_pms_by_customer_2024_2025.csv"
    by_cust.to_csv(out_cust, index=False)
    print("wrote", out_cust, "rows", len(by_cust))
    print(by_cust.to_string())

    # family × customer × year
    fam_rows = []
    for (yr, cust_code, fam), g in all_lines.groupby(
        ["list_year", "customer", "pms_family"]
    ):
        fam_rows.append(
            {
                "list_year": int(yr),
                "customer": int(cust_code),
                "payer": cmap.get(int(cust_code), {}).get("payer", str(cust_code)),
                "pms_family": fam,
                "n_pms_pns": int(g["pn"].nunique()),
                "billed_eur_pms": round(float(g["billed_eur"].sum()), 2),
                "median_zpr1_vs_pr00_pct": round(
                    float(g["zpr1_vs_pr00_pct"].median()), 2
                ),
                "wmean_zpr1_vs_pr00_pct": round(
                    wmean(g["zpr1_vs_pr00_pct"], g["billed_eur"]), 2
                ),
                "pct_pns_above_list": round(
                    float((g["zpr1_vs_pr00_pct"] > 0).mean() * 100), 2
                ),
            }
        )
    by_fam = pd.DataFrame(fam_rows).sort_values(
        ["list_year", "customer", "billed_eur_pms"], ascending=[True, True, False]
    )
    out_fam = DER / "zpr1_vs_pr00_pms_by_customer_family_2024_2025.csv"
    by_fam.to_csv(out_fam, index=False)
    print("wrote", out_fam, "rows", len(by_fam))

    # refresh all-PN reference for customers present in 2024/2025 extracts
    ref_rows = []
    for yr in (2024, 2025):
        z = pd.read_parquet(DER / f"pricing_zpr1_{yr}.parquet").copy()
        pr = pd.read_parquet(DER / f"pricing_pr00_ie40_{yr}.parquet").copy()
        z["pn"] = norm_pn(z["Material"])
        z["customer"] = pd.to_numeric(z["Customer"], errors="coerce").astype("Int64")
        z["zpr1"] = pd.to_numeric(z["Price"], errors="coerce")
        z = z.sort_values(["customer", "pn", "Valid_From"]).drop_duplicates(
            ["customer", "pn"], keep="last"
        )
        pr["pn"] = norm_pn(pr["Material"])
        pr["pr00"] = pd.to_numeric(pr["Price_EUR"], errors="coerce")
        pr = pr.drop_duplicates("pn", keep="last")
        m = z.merge(pr[["pn", "pr00"]], on="pn", how="left")
        for cust_code, g0 in m.groupby("customer"):
            g = g0[(g0["zpr1"] > 0) & (g0["pr00"] > 0)].copy()
            if g.empty:
                continue
            g["pct"] = (g["zpr1"] / g["pr00"] - 1.0) * 100.0
            payer = cmap.get(int(cust_code), {}).get("payer", str(int(cust_code)))
            ref_rows.append(
                {
                    "year": yr,
                    "customer": int(cust_code),
                    "payer": payer if payer not in (None, "") else str(int(cust_code)),
                    "n_zpr1_pns": int(g0["pn"].nunique()),
                    "n_vs_pr00": int(g["pn"].nunique()),
                    "median_zpr1_vs_pr00_pct": round(float(g["pct"].median()), 2),
                    "p25_zpr1_vs_pr00_pct": round(float(g["pct"].quantile(0.25)), 2),
                    "p75_zpr1_vs_pr00_pct": round(float(g["pct"].quantile(0.75)), 2),
                    "note": "UTI!=UMI; never blend; all ZPR1 PNs (not PMS-only)",
                }
            )

    old = pd.read_csv(DER / "zpr1_vs_pr00_by_payer_year.csv")
    keep = old[~old["year"].isin([2024, 2025])].copy()
    new_ref = pd.concat([keep, pd.DataFrame(ref_rows)], ignore_index=True)
    new_ref = new_ref.sort_values(["year", "customer"]).reset_index(drop=True)
    new_ref.to_csv(DER / "zpr1_vs_pr00_by_payer_year.csv", index=False)
    print("refreshed zpr1_vs_pr00_by_payer_year.csv")
    print(new_ref[new_ref["year"].isin([2024, 2025])].to_string())

    # blend guard
    if {1797, 1799}.issubset(set(by_cust["customer"])):
        u = by_cust.set_index("customer")
        same_med = (
            u.loc[1797, "median_zpr1_vs_pr00_pct_2025"]
            == u.loc[1799, "median_zpr1_vs_pr00_pct_2025"]
        )
        same_n = u.loc[1797, "n_pms_pns_2025"] == u.loc[1799, "n_pms_pns_2025"]
        if same_med and same_n:
            raise SystemExit("FAIL: UMI and UTI look identical — possible blend")

    # markdown
    md_path = INBOX / "CUSTOMER_CONDITION_PRICE_VS_LIST_PMS_2024_2025.md"
    lines: list[str] = []
    lines.append("# Customer condition price vs list — PMS parts 2024–2025")
    lines.append("")
    lines.append(
        "On scheduled-service parts (PMS: filters, brakes, clutch, maintenance wear), "
        "how far does each customer's **condition price** (ZPR1) sit vs the **list price** "
        "(PR00 IE40), and how did that move from list-year 2024 to 2025?"
    )
    lines.append("")
    lines.append(
        "Join ZPR1 to PR00 on material for 2024 and 2025. Keep only part numbers with a "
        "`pms_category` in `parts_catalog_dimension.csv`. Per customer: median and "
        "billed-euro-weighted mean of (condition ÷ list − 1). Billed euro from "
        "`sales_fact.parquet` for the same calendar year on sold-to × part number. "
        "UTI (1799) and UMI (1797) are never blended. IUK and ITUK have no ZPR1 rows in "
        "these year extracts — they are not invented."
    )
    lines.append("")
    lines.append(
        "Note: `01_data/2025_PR00.XLSX` in the data root is mislabelled (July–Sep 2026 "
        "billing, not a list). This study uses `pricing_pr00_ie40_2024/2025.parquet` only."
    )
    lines.append("")
    lines.append("## Customers in the ZPR1 year extracts")
    lines.append("")
    lines.append(
        "| Customer | Payer | 2024 median vs list | 2025 median vs list | "
        "YoY (pp) | 2025 billed PMS EUR | Risk flag |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---|")
    for _, r in by_cust.iterrows():
        yoy = (
            "n/a"
            if pd.isna(r["median_pct_pts_yoy"])
            else f"{r['median_pct_pts_yoy']:+.1f}"
        )
        lines.append(
            f"| {int(r['customer'])} | {r['payer']} | "
            f"{fmt_pct(r['median_zpr1_vs_pr00_pct_2024'])} | "
            f"{fmt_pct(r['median_zpr1_vs_pr00_pct_2025'])} | {yoy} | "
            f"{fmt_eur(r['billed_eur_pms_2025'])} | {r['revision_risk_flag']} |"
        )
    lines.append("")
    lines.append(
        "Risk flag: `above_list` = condition ≥ list (raising list hurts immediately). "
        "`tight_vs_list` = within about 8% below list. `deep_discount` = median at least "
        "25% below list (more room before the customer sits on list). `mid_discount` = "
        "in between."
    )
    lines.append("")
    lines.append("## UTI vs UMI (keep separate)")
    lines.append("")
    for code, label in ((1799, "UTI"), (1797, "UMI")):
        r = by_cust[by_cust["customer"] == code]
        if r.empty:
            lines.append(f"- **{label} ({code}):** not in these ZPR1 extracts.")
            continue
        r = r.iloc[0]
        yoy = (
            "n/a"
            if pd.isna(r["median_pct_pts_yoy"])
            else f"{r['median_pct_pts_yoy']:+.1f} pp"
        )
        lines.append(
            f"- **{label} ({code}):** median condition vs list "
            f"{fmt_pct(r['median_zpr1_vs_pr00_pct_2024'])} (2024) → "
            f"{fmt_pct(r['median_zpr1_vs_pr00_pct_2025'])} (2025), YoY {yoy}. "
            f"Billed PMS match {fmt_eur(r['billed_eur_pms_2024'])} / "
            f"{fmt_eur(r['billed_eur_pms_2025'])}. Flag: {r['revision_risk_flag']}."
        )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append(f"- `{out_cust}`")
    lines.append(f"- `{out_fam}`")
    lines.append(
        f"- refreshed `{DER / 'zpr1_vs_pr00_by_payer_year.csv'}` "
        "(all ZPR1 PNs, not PMS-only; 2024/2025 refreshed for customers in the extracts)"
    )
    lines.append("")
    lines.append("Built 2026-09-22.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", md_path)

    # top by billed for chat handoff
    print("\n=== TOP BY BILLED (max of 2024/2025 PMS match) ===")
    for i, (_, r) in enumerate(by_cust.iterrows(), 1):
        print(
            f"{i}. {r['payer']} ({int(r['customer'])}): "
            f"median 2024 {fmt_pct(r['median_zpr1_vs_pr00_pct_2024'])} / "
            f"2025 {fmt_pct(r['median_zpr1_vs_pr00_pct_2025'])}; "
            f"billed 2025 {fmt_eur(r['billed_eur_pms_2025'])}; "
            f"flag {r['revision_risk_flag']}"
        )


if __name__ == "__main__":
    main()
