#!/usr/bin/env python3
"""READ-ONLY evidence for the sibling-file decision. Writes nothing.

Answers, per file, whether the 2026 figure is:
  (a) wrong as a rate            -> blank it
  (b) correct for a part year    -> disclose it
  (c) a ranking artefact         -> correct the label
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
pd.set_option("display.width", 220)


def line(t: str) -> None:
    print("\n" + "=" * 100)
    print(t)
    print("=" * 100)


line("A. gps_spu_by_family.csv — is the 2026 spu_eur a rate for its period, or a false rate?")
fam = pd.read_csv(DER / "gps_spu_by_family.csv")
print("columns:", list(fam.columns))
print("years:", sorted(fam["year"].unique()))
a = fam[fam["line_type"] == "all"]
tot = a.groupby("year").agg(net_sales_eur=("net_sales_eur", "sum"))
print("\nnetwork net_sales_eur by year (line_type=all):")
print(tot)
print("\n2026 as a share of 2025:",
      round(float(tot.loc[2026, 'net_sales_eur'] / tot.loc[2025, 'net_sales_eur']), 4))
print("if the 2026 numerator were a full 12 months it would be that share x 12/8 =",
      round(float(tot.loc[2026, 'net_sales_eur'] / tot.loc[2025, 'net_sales_eur']) * 12 / 8, 4))
print("\nuio_units per year for one market (IUK) — is the denominator a full-year fleet?")
print(a[a["distributor_code"] == "IUK"][["year", "product_family", "line_type",
                                         "net_sales_eur", "uio_units", "spu_eur"]].to_string(index=False))

line("B. gps_spu_pms.csv — same question")
pms = pd.read_csv(DER / "gps_spu_pms.csv")
print("columns:", list(pms.columns))
ap = pms[pms["line_type"] == "all"]
totp = ap.groupby("year").agg(net_sales_eur=("net_sales_eur", "sum"))
print("\nnetwork net_sales_eur by year (line_type=all):")
print(totp)

line("C. aim_gps_matrix.csv — are the six 2026 'priority target' labels created by the part year?")
m = pd.read_csv(DER / "aim_gps_matrix.csv")
cols = ["year", "distributor_code", "gps_spu_eur", "gps_median_benchmark_eur", "gps_high",
        "pms_capture_all", "capture_median_benchmark", "capture_high", "quadrant",
        "year_coverage_pct", "is_partial_year"]
print(m[cols].to_string(index=False))

print("\n--- priority_target markets by year:")
for yr in sorted(m["year"].unique()):
    sub = m[(m["year"] == yr) & (m["quadrant"] == "priority_target")]
    print(f"  {yr}: {sorted(sub['distributor_code'].tolist())}")

six = ["GREECE", "HUNGARY", "IUK", "NORWAY", "SWEDEN", "UMI"]
print("\n--- the six 2026 priority_target markets, their quadrant history:")
for db in six:
    h = m[m["distributor_code"] == db].sort_values("year")
    print(f"  {db:10s} " + "  ".join(f"{int(r.year)}={r.quadrant}" for r in h.itertuples()))

print("\n--- sanity: does a common scale factor move the 2026 quadrant?")
y26 = m[m["year"] == 2026].copy()
for f, lbl in ((1.0, "as-is"), (12 / 8, "gps axis annualised x12/8"),
               (8 / 12, "gps axis scaled x8/12")):
    g = y26["gps_spu_eur"] * f
    med = g.median()
    high = (g >= med) & g.notna()
    ch = (y26["pms_capture_all"] >= y26["capture_median_benchmark"]) & y26["pms_capture_all"].notna()
    q = []
    for gh, c in zip(high, ch):
        if pd.isna(gh) or pd.isna(c):
            q.append("insufficient_data")
        elif gh and c:
            q.append("defend")
        elif gh and not c:
            q.append("attach_gap")
        elif c:
            q.append("wallet_gap")
        else:
            q.append("priority_target")
    same = sorted(y26.loc[[x == "priority_target" for x in q], "distributor_code"])
    print(f"  {lbl:28s} median {med:8.3f} -> priority_target {same}")

print("\n--- what the capture axis denominator is, by year (is it full-year?)")
cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
c = cap[cap["line_type"] == "total"]
print(c.groupby("year").agg(expected_qty=("expected_qty", "sum"),
                            actual_qty=("actual_qty", "sum")).to_string())
print("IUK expected_qty per year:")
print(c[c["distributor_code"] == "IUK"].groupby("year")["expected_qty"].sum().to_string())

line("D. net_sales vs prior year on the same eight months, for the six markets")
sf = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
s = pd.read_parquet(sf, columns=["billing_date", "net_sales_value", "distributor_code"])
s["billing_date"] = pd.to_datetime(s["billing_date"])
s["y"] = s["billing_date"].dt.year
s["m"] = s["billing_date"].dt.month
jan8 = s[s["m"] <= 8]
piv = jan8.pivot_table(index="distributor_code", columns="y",
                       values="net_sales_value", aggfunc="sum")
piv["chg_pct"] = (piv[2026] / piv[2025] - 1) * 100
print(piv.loc[[d for d in six if d in piv.index]].round(1).to_string())
print("\nmax billing_date in sales_fact:", s["billing_date"].max())
