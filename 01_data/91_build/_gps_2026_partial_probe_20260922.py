"""Read-only probe: how far do the 2026 rows of gps_spu_by_distributor.csv sit from sales_fact?

Part 2 evidence for the schema-guard task, 2026-09-22. Writes nothing but its own stdout.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
sys.path.insert(0, str(PRISM))
sys.path.insert(0, str(PRISM / "scripts"))

from config import resolve_mapping_path  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

sales, _ = load_prism_sales(load_distributor_mapping(str(resolve_mapping_path())))
if "line_kind" in sales.columns:
    sales = sales[sales["line_kind"] == "part"]
sales = sales[~sales["is_credit_note"]].copy()
sales["billing_date"] = pd.to_datetime(sales["billing_date"], errors="coerce")
sales["ym"] = sales["billing_date"].dt.to_period("M")

print("billing horizon on sales_fact:", sales["billing_date"].min().date(), "->", sales["billing_date"].max().date())

gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")

# ---- 1. calendar-2026 total on sales_fact vs the 2026 rows -------------------
tot26 = (sales[sales["billing_date"].dt.year == 2026]
         .groupby("distributor_code")["net_sales_value"].sum())
rows26 = gps[gps.year == 2026].set_index("distributor_code")
cmp = pd.DataFrame({"file_total_2026": rows26["total_sales_eur"], "sales_fact_2026": tot26})
cmp["delta_eur"] = cmp["file_total_2026"] - cmp["sales_fact_2026"]
cmp["file_over_fact_pct"] = 100 * cmp["delta_eur"] / cmp["sales_fact_2026"]
cmp = cmp.sort_values("delta_eur", ascending=False)
print("\n=== 2026: file total_sales_eur vs sales_fact calendar-2026 ===")
print(cmp.to_string(float_format=lambda v: f"{v:,.2f}"))
print(f"\nsum file 2026 {cmp['file_total_2026'].sum():,.2f}   sum sales_fact 2026 {cmp['sales_fact_2026'].sum():,.2f}")
print(f"file total across 22 rows / fact total = {cmp['file_total_2026'].sum()/cmp['sales_fact_2026'].sum():.4f}")

# ---- 2. months actually present in 2026 ------------------------------------
print("\n=== sales_fact 2026 euro by month ===")
m26 = sales[sales["billing_date"].dt.year == 2026].groupby("ym")["net_sales_value"].sum()
print(m26.to_string(float_format=lambda v: f"{v:,.2f}"))
print("\n2025 by month (for H1 compare):")
m25 = sales[sales["billing_date"].dt.year == 2025].groupby("ym")["net_sales_value"].sum()
print(m25.to_string(float_format=lambda v: f"{v:,.2f}"))

for label, months in (("H1 (Jan-Jun)", range(1, 7)), ("Jan-Aug", range(1, 9))):
    a = sales[(sales["billing_date"].dt.year == 2026) & (sales["billing_date"].dt.month.isin(months))]["net_sales_value"].sum()
    b = sales[(sales["billing_date"].dt.year == 2025) & (sales["billing_date"].dt.month.isin(months))]["net_sales_value"].sum()
    print(f"\n{label}: 2026 {a:,.2f}  vs 2025 {b:,.2f}  -> {100*(a-b)/b:+.1f}%")

# ---- 3. the false collapse in spend per unit -------------------------------
spu = gps.pivot_table(index="distributor_code", columns="year", values="spend_per_unit_eur")
cols = [c for c in (2023, 2024, 2025, 2026) if c in spu.columns]
spu = spu[cols]
spu["26_vs_25_pct"] = 100 * (spu[2026] - spu[2025]) / spu[2025]
print("\n=== spend_per_unit_eur: the apparent collapse ===")
print(spu.to_string(float_format=lambda v: f"{v:,.2f}"))
print(f"network 2025 total {spu[2025].sum():,.2f} -> 2026 {spu[2026].sum():,.2f}  ({spu['26_vs_25_pct'].mean():+.1f}% mean)")

# ---- 4. what the capture would read if it used the same months -------------
# For the 18 rows that carry max_spend and a capture, show the file capture and what a
# same-months (Jan-Aug both years) capture would be if 2026 = 8/12 of a year.
r26 = gps[(gps.year == 2026) & gps["gps_capture_vs_max"].notna()].copy()
r26["file_capture"] = r26["gps_capture_vs_max"]
r26["fact_2026"] = r26["distributor_code"].map(tot26)
r26["months_factor"] = 8 / 12
r26["annualised_capture"] = r26["file_capture"] / r26["months_factor"]
print("\n=== 2026 rows carrying a capture: file reading vs annualised ===")
print(r26[["distributor_code", "total_sales_eur", "max_spend_eur", "file_capture",
           "annualised_capture", "traffic_light_v9"]]
      .to_string(index=False, float_format=lambda v: f"{v:,.4f}"))
