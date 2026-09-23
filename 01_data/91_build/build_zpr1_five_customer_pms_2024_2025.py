"""Five-customer ZPR1 vs PR00 (PMS) + KPI MOS — 2024 vs 2025.

Scope (Jerome 2026-09-22): CBC, Grand Avto (GA), UTI, UMI, KIMA only.
Skip all other ZPR1 codes (Russia stubs, IUK/ITUK noise rows, etc.).

MOS = Days of Parts in Stock from KPI Master File (Parts Handling).
CBC / GA have no KPI MOS rows — left blank honestly.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DATA = ROOT / "01_data"
DER = DATA / "00_derived"
INBOX = DATA / "90_INBOX"

KEEP = {
    1797: ("UMI", "UNIVERSAL MOTORS ISRAEL LTD"),
    1799: ("UTI", "UNIVERSAL TRUCKS ISRAEL LTD"),
    2372: ("KIMA", "KIMA LATEJARET AL MARKABAT CO"),
    2733: ("GA", "Grand Avto LLC"),
    2734: ("CBC", "CBC-Trans LLP"),
}

# KPI Parts Handling distributor label for MOS / fill / sales-to-dealer
KPI_NAME = {
    1797: "UMI",
    1799: "UTI",
    2372: "KIMA",
    # CBC / GA: not in KPI master
}

ZPR1_FILES = {
    2024: DATA / "2024_ZPR1.XLSX",
    2025: DATA / "2025_ZPR1.XLSX",
}
KPI_FILE = DATA / "KPI Master File.xlsx"
PR00 = {
    2024: DER / "pricing_pr00_ie40_2024.parquet",
    2025: DER / "pricing_pr00_ie40_2025.parquet",
}

OUT_CUST = DER / "zpr1_five_customer_vs_pr00_pms_2024_2025.csv"
OUT_FAM = DER / "zpr1_five_customer_vs_pr00_pms_by_family_2024_2025.csv"
OUT_MOS = DER / "zpr1_five_customer_kpi_mos_2024_2025.csv"
OUT_PARQUET = {
    2024: DER / "pricing_zpr1_five_2024.parquet",
    2025: DER / "pricing_zpr1_five_2025.parquet",
}
OUT_MD = INBOX / "ZPR1_FIVE_CUSTOMER_PMS_MOS_2024_2025.md"


def norm_pn(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip().str.upper()
    return s.str.replace(r"\.0$", "", regex=True).str.lstrip("0").replace("", "0")


def parse_price(v) -> float:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return float("nan")
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def code_int(v) -> int | None:
    if v is None:
        return None
    s = str(v).strip().lstrip("0")
    if not s:
        return 0
    try:
        return int(float(s))
    except ValueError:
        return None


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


def extract_zpr1(year: int, path: Path) -> pd.DataFrame:
    """Stream ZPR1 xlsx; keep only five customer codes; one row per customer×pn."""
    keep_set = set(KEEP)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    hdr = [str(x).strip() if x is not None else "" for x in next(ws.iter_rows(max_row=1, values_only=True))]
    idx = {h: i for i, h in enumerate(hdr)}

    def col(*names, default=None):
        for n in names:
            if n in idx:
                return idx[n]
        return default

    i_cust = col("Customer Code")
    i_pn = col("Newest P/N", "P/N")
    i_pn_alt = col("P/N")
    i_price = col("Price")
    i_curr = col("Currency")
    i_start = col("Valid Start")
    i_end = col("Valid End")
    i_type = col("Price Condition Type")
    if i_cust is None or i_price is None:
        wb.close()
        raise SystemExit(f"Bad header in {path}: {hdr[:20]}")

    out: list[dict] = []
    n_in = n_keep = 0
    for r in ws.iter_rows(min_row=2, values_only=True):
        n_in += 1
        cust = code_int(r[i_cust])
        if cust not in keep_set:
            continue
        n_keep += 1
        pn = r[i_pn] if i_pn is not None else None
        if pn is None and i_pn_alt is not None:
            pn = r[i_pn_alt]
        price = parse_price(r[i_price])
        if not np.isfinite(price) or price <= 0:
            continue
        out.append(
            {
                "list_year": year,
                "customer": cust,
                "customer_label": KEEP[cust][0],
                "customer_name": KEEP[cust][1],
                "Material": str(pn).strip() if pn is not None else "",
                "Price": price,
                "Currency": r[i_curr] if i_curr is not None else "EUR",
                "Valid_From": r[i_start] if i_start is not None else None,
                "Valid_To": r[i_end] if i_end is not None else None,
                "condition_type": r[i_type] if i_type is not None else "ZPR1",
            }
        )
    wb.close()
    df = pd.DataFrame(out)
    if df.empty:
        raise SystemExit(f"No keep-customer rows in {path}")
    df["pn"] = norm_pn(df["Material"])
    df["Valid_From"] = pd.to_datetime(df["Valid_From"], errors="coerce")
    df = df.sort_values(["customer", "pn", "Valid_From"], na_position="first")
    df = df.drop_duplicates(subset=["customer", "pn"], keep="last")
    print(f"{year}: read {n_in:,} rows, kept {n_keep:,} raw, {len(df):,} unique customer×pn")
    return df


def load_pms() -> pd.DataFrame:
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
    return cat.drop_duplicates("pn")[["pn", "pms_category", "pms_family"]]


def load_sales_weights() -> pd.DataFrame:
    sf = pd.read_parquet(
        DER / "sales_fact.parquet",
        columns=["sold_to_sap", "part_number", "year", "net_sales_value"],
    )
    sf = sf[sf["year"].isin([2024, 2025])].copy()
    sf["customer"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce").astype("Int64")
    sf = sf[sf["customer"].isin(list(KEEP))].copy()
    sf["pn"] = norm_pn(sf["part_number"])
    sf["billed_eur"] = pd.to_numeric(sf["net_sales_value"], errors="coerce").fillna(0.0)
    return sf.groupby(["year", "customer", "pn"], as_index=False)["billed_eur"].sum()


def wmean(vals, weights) -> float:
    vals = np.asarray(vals, dtype=float)
    weights = np.asarray(weights, dtype=float)
    m = np.isfinite(vals) & np.isfinite(weights) & (weights > 0)
    if not m.any():
        return float("nan")
    return float(np.average(vals[m], weights=weights[m]))


def parse_kpi_parts_handling() -> pd.DataFrame:
    """Return long frame: distributor, metric, month, value for MOS/fill/sales-to-dealer."""
    raw = pd.read_excel(KPI_FILE, sheet_name="Parts Handling", header=None)
    metrics_wanted = {
        "Days of Parts in Stock": "mos_days",
        "First Fill Rate": "fill_rate",
        "Parts Sales DB to DLR in €": "sales_to_dealer_eur",
        "Parts Sales DB to DLR in �": "sales_to_dealer_eur",  # encoding variant
    }
    # Also match fuzzy
    blocks = []
    i = 0
    n = len(raw)
    while i < n:
        title = raw.iloc[i, 0]
        title_s = str(title).strip() if pd.notna(title) else ""
        metric_key = None
        for k, v in metrics_wanted.items():
            if title_s.startswith(k[:20]) or k in title_s:
                metric_key = v
                break
        if "Parts Sales DB to DLR" in title_s:
            metric_key = "sales_to_dealer_eur"
        if metric_key is None:
            i += 1
            continue
        # find Distributor header row
        j = i + 1
        while j < min(i + 5, n) and str(raw.iloc[j, 0]).strip() != "Distributor":
            j += 1
        if j >= n or str(raw.iloc[j, 0]).strip() != "Distributor":
            i += 1
            continue
        months = []
        for c in range(1, raw.shape[1]):
            h = raw.iloc[j, c]
            if pd.isna(h):
                months.append(None)
            else:
                months.append(str(h).strip())
        r = j + 1
        while r < n:
            name = raw.iloc[r, 0]
            if pd.isna(name) or str(name).strip() == "":
                # blank may end block
                if r + 1 < n and pd.isna(raw.iloc[r + 1, 0]):
                    break
                r += 1
                continue
            name_s = str(name).strip()
            if name_s == "Distributor" or name_s in metrics_wanted or name_s.startswith("Days of") or name_s.startswith("First Fill") or name_s.startswith("Parts Sales"):
                break
            for c, mon in enumerate(months, start=1):
                if not mon:
                    continue
                val = raw.iloc[r, c]
                blocks.append(
                    {
                        "distributor": name_s,
                        "metric": metric_key,
                        "month": mon,
                        "value": val,
                    }
                )
            r += 1
        i = r
    return pd.DataFrame(blocks)


def month_to_year(mon: str) -> int | None:
    # e.g. Apr 24, Jan 25, Dez 24
    parts = str(mon).strip().split()
    if len(parts) != 2:
        return None
    try:
        yy = int(parts[1])
    except ValueError:
        return None
    return 2000 + yy if yy < 100 else yy


def kpi_year_summary(kpi_long: pd.DataFrame) -> pd.DataFrame:
    """CY average MOS / fill / sales-to-dealer for UMI UTI KIMA, 2024 and 2025."""
    df = kpi_long.copy()
    df["year"] = df["month"].map(month_to_year)
    df = df[df["distributor"].isin(["UMI", "UTI", "KIMA"])].copy()
    df = df[df["year"].isin([2024, 2025])]

    def to_num(x):
        if pd.isna(x):
            return np.nan
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip().replace("%", "").replace(",", ".")
        if s.upper() in {"N/A", "N/D", "NA", "-", ""}:
            return np.nan
        try:
            return float(s)
        except ValueError:
            return np.nan

    df["value_num"] = df["value"].map(to_num)
    rows = []
    for (dist, year), g in df.groupby(["distributor", "year"]):
        rec = {"distributor": dist, "year": int(year)}
        for metric, col in [
            ("mos_days", "mos_days_avg"),
            ("fill_rate", "fill_rate_avg"),
            ("sales_to_dealer_eur", "sales_to_dealer_eur_sum"),
        ]:
            sub = g[g["metric"] == metric]["value_num"].dropna()
            if metric == "sales_to_dealer_eur":
                rec[col] = float(sub.sum()) if len(sub) else np.nan
                rec[f"{metric}_n_months"] = int(len(sub))
            else:
                rec[col] = float(sub.mean()) if len(sub) else np.nan
                rec[f"{metric}_n_months"] = int(len(sub))
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    pms = load_pms()
    sales_w = load_sales_weights()

    frames = {}
    for year, path in ZPR1_FILES.items():
        if not path.exists():
            raise SystemExit(f"Missing {path}")
        df = extract_zpr1(year, path)
        df.to_parquet(OUT_PARQUET[year], index=False)
        frames[year] = df

    # joins vs PR00 + PMS + sales
    cust_rows = []
    fam_rows = []
    for year, z in frames.items():
        pr00 = pd.read_parquet(PR00[year]).copy()
        pr00["pn"] = norm_pn(pr00["Material"])
        pr00["pr00"] = pd.to_numeric(pr00["Price_EUR"], errors="coerce")
        pr00 = pr00[["pn", "pr00"]].drop_duplicates("pn")

        m = z.merge(pr00, on="pn", how="inner")
        m = m.merge(pms, on="pn", how="inner")
        m["pct_vs_list"] = m["Price"] / m["pr00"] - 1.0
        sw = sales_w[sales_w["year"] == year][["customer", "pn", "billed_eur"]]
        m = m.merge(sw, on=["customer", "pn"], how="left")
        m["billed_eur"] = m["billed_eur"].fillna(0.0)

        for cust, g in m.groupby("customer"):
            label, name = KEEP[int(cust)]
            med = float(g["pct_vs_list"].median())
            wm = wmean(g["pct_vs_list"], g["billed_eur"])
            cust_rows.append(
                {
                    "customer": int(cust),
                    "customer_label": label,
                    "customer_name": name,
                    "year": year,
                    "n_pms_pns": int(len(g)),
                    "billed_eur_pms_matched": float(g["billed_eur"].sum()),
                    "median_zpr1_vs_pr00_pct": round(med * 100, 2),
                    "wmean_zpr1_vs_pr00_pct": round(wm * 100, 2) if np.isfinite(wm) else np.nan,
                    "pct_pns_above_list": round(100 * (g["pct_vs_list"] > 0).mean(), 2),
                    "pct_pns_le_minus20": round(100 * (g["pct_vs_list"] <= -0.20).mean(), 2),
                    "note": "UTI!=UMI; CBC!=GA; five-customer scope only",
                }
            )
            for fam, gf in g.groupby("pms_family"):
                medf = float(gf["pct_vs_list"].median())
                wmf = wmean(gf["pct_vs_list"], gf["billed_eur"])
                fam_rows.append(
                    {
                        "customer": int(cust),
                        "customer_label": label,
                        "year": year,
                        "pms_family": fam,
                        "n_pns": int(len(gf)),
                        "billed_eur": float(gf["billed_eur"].sum()),
                        "median_zpr1_vs_pr00_pct": round(medf * 100, 2),
                        "wmean_zpr1_vs_pr00_pct": round(wmf * 100, 2) if np.isfinite(wmf) else np.nan,
                    }
                )

    cust_df = pd.DataFrame(cust_rows).sort_values(["customer_label", "year"])
    fam_df = pd.DataFrame(fam_rows).sort_values(["customer_label", "pms_family", "year"])

    # YoY columns wide
    wide = cust_df.pivot(index=["customer", "customer_label", "customer_name"], columns="year")
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    wide = wide.reset_index()
    if "median_zpr1_vs_pr00_pct_2024" in wide.columns and "median_zpr1_vs_pr00_pct_2025" in wide.columns:
        wide["median_pct_pts_yoy"] = (
            wide["median_zpr1_vs_pr00_pct_2025"] - wide["median_zpr1_vs_pr00_pct_2024"]
        )

    # KPI MOS
    kpi_long = parse_kpi_parts_handling()
    kpi_sum = kpi_year_summary(kpi_long)
    # map customer codes
    inv = {v: k for k, v in KPI_NAME.items()}
    kpi_sum["customer"] = kpi_sum["distributor"].map(inv)
    kpi_sum["customer_label"] = kpi_sum["distributor"]
    # add blank rows for CBC / GA
    extra = []
    for code, (lab, _) in KEEP.items():
        if lab in {"CBC", "GA"}:
            for y in (2024, 2025):
                extra.append(
                    {
                        "distributor": lab,
                        "year": y,
                        "mos_days_avg": np.nan,
                        "fill_rate_avg": np.nan,
                        "sales_to_dealer_eur_sum": np.nan,
                        "mos_days_n_months": 0,
                        "fill_rate_n_months": 0,
                        "sales_to_dealer_eur_n_months": 0,
                        "customer": code,
                        "customer_label": lab,
                        "kpi_note": "not in KPI Master Parts Handling",
                    }
                )
    if "kpi_note" not in kpi_sum.columns:
        kpi_sum["kpi_note"] = "from KPI Master File Parts Handling"
    kpi_out = pd.concat([kpi_sum, pd.DataFrame(extra)], ignore_index=True)

    cust_df.to_csv(OUT_CUST, index=False)
    fam_df.to_csv(OUT_FAM, index=False)
    kpi_out.to_csv(OUT_MOS, index=False)

    # Markdown for Jerome
    lines = []
    lines.append("# Five-customer condition prices vs list + MOS — 2024 / 2025")
    lines.append("")
    lines.append("**Scope:** CBC, Grand Avto (GA), UTI, UMI, KIMA only. All other ZPR1 codes skipped.")
    lines.append("**Sources:** `2024_ZPR1.XLSX`, `2025_ZPR1.XLSX`, PR00 parquet, `KPI Master File.xlsx` (Days of Parts in Stock = MOS).")
    lines.append("")
    lines.append("## Condition price vs list (PMS parts)")
    lines.append("")
    lines.append("| Customer | 2024 median vs list | 2025 median vs list | Δ pp | 2025 PMS billed match |")
    lines.append("|---|---:|---:|---:|---:|")
    for _, r in wide.sort_values("customer_label").iterrows():
        m24 = r.get("median_zpr1_vs_pr00_pct_2024", np.nan)
        m25 = r.get("median_zpr1_vs_pr00_pct_2025", np.nan)
        dy = r.get("median_pct_pts_yoy", np.nan)
        bill = r.get("billed_eur_pms_matched_2025", np.nan)
        lines.append(
            f"| {r['customer_label']} ({int(r['customer'])}) | "
            f"{m24:.1f}% | {m25:.1f}% | {dy:+.1f} | EUR {bill:,.0f} |"
        )
    lines.append("")
    lines.append("UTI and UMI stay separate. CBC and GA above list = revision risk if list rises and their condition stays.")
    lines.append("")
    lines.append("## MOS (days of parts in stock) — KPI")
    lines.append("")
    lines.append("Only UTI, UMI and KIMA report in the KPI master. CBC and GA are blank.")
    lines.append("")
    lines.append("| Customer | 2024 MOS avg (months) | 2025 MOS avg | 2024 fill % | 2025 fill % |")
    lines.append("|---|---:|---:|---:|---:|")
    kwide = kpi_out.pivot(index="customer_label", columns="year")
    for lab in ["UTI", "UMI", "KIMA", "CBC", "GA"]:
        try:
            m24 = kwide[("mos_days_avg", 2024)].get(lab, np.nan)
            m25 = kwide[("mos_days_avg", 2025)].get(lab, np.nan)
            f24 = kwide[("fill_rate_avg", 2024)].get(lab, np.nan)
            f25 = kwide[("fill_rate_avg", 2025)].get(lab, np.nan)
        except KeyError:
            m24 = m25 = f24 = f25 = np.nan
        def fmt(x):
            return "n/a" if pd.isna(x) else f"{x:.1f}"
        lines.append(f"| {lab} | {fmt(m24)} | {fmt(m25)} | {fmt(f24)} | {fmt(f25)} |")
    lines.append("")
    lines.append(
        "How to read with the price story: high MOS + volume soft with flat list points to "
        "stocking / warehouse, not end-customer price refusal. Low MOS + volume soft points more at demand or capture."
    )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append(f"- `{OUT_CUST}`")
    lines.append(f"- `{OUT_FAM}`")
    lines.append(f"- `{OUT_MOS}`")
    lines.append(f"- `{OUT_PARQUET[2024]}` / `{OUT_PARQUET[2025]}`")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", OUT_CUST)
    print("Wrote", OUT_FAM)
    print("Wrote", OUT_MOS)
    print("Wrote", OUT_MD)
    print(wide.to_string())
    print(kpi_out.to_string())


if __name__ == "__main__":
    main()
