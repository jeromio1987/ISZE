"""Read-only probe 3: like-for-like Jan-Aug 2026 vs 2025, per distributor, against the file."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PRISM = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism")
sys.path.insert(0, str(PRISM))
from config import resolve_mapping_path  # noqa: E402
from modules.data_prep import load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
sales, _ = load_prism_sales(load_distributor_mapping(str(resolve_mapping_path())))
if "line_kind" in sales.columns:
    sales = sales[sales["line_kind"] == "part"]
sales = sales[~sales["is_credit_note"]].copy()
sales["billing_date"] = pd.to_datetime(sales["billing_date"], errors="coerce")

JAN_AUG = range(1, 9)
jan_aug = sales[sales["billing_date"].dt.month.isin(JAN_AUG)]
a26 = jan_aug[jan_aug["billing_date"].dt.year == 2026].groupby("distributor_code")["net_sales_value"].sum()
a25 = jan_aug[jan_aug["billing_date"].dt.year == 2025].groupby("distributor_code")["net_sales_value"].sum()

gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")
r26 = gps[gps.year == 2026].set_index("distributor_code")
r25 = gps[gps.year == 2025].set_index("distributor_code")

out = pd.DataFrame({
    "file_2026_sales": r26["total_sales_eur"],
    "fact_jan_aug_2026": a26,
    "fact_jan_aug_2025": a25,
    "fact_yoy_pct": 100 * (a26 - a25) / a25,
    "file_spu_2026": r26["spend_per_unit_eur"],
    "file_spu_2025": r25["spend_per_unit_eur"],
})
out["file_spu_implied_pct"] = 100 * (out["file_spu_2026"] - out["file_spu_2025"]) / out["file_spu_2025"]
out["false_reading_pp"] = out["file_spu_implied_pct"] - out["fact_yoy_pct"]
out = out.sort_values("false_reading_pp")
print("=== spend per unit: what the file implies vs sales_fact like-for-like (Jan-Aug) ===")
print(out.to_string(float_format=lambda v: f"{v:,.2f}"))
print()
print(f"network: file implies {out['file_spu_implied_pct'].mean():+.1f}% mean move in spend/unit; "
      f"sales_fact like-for-like is {100*(a26.sum()-a25.sum())/a25.sum():+.1f}% "
      f"(EUR {a26.sum()-a25.sum():,.0f})")
print(f"mean false reading: {out['false_reading_pp'].mean():+.1f} pp")

# ---- capture: part-year numerator over full-year denominator ----------------
cap = gps[(gps.year == 2026) & gps["max_spend_eur"].notna()].copy()
cap["gap_file_eur"] = cap["max_spend_eur"] - cap["total_sales_eur"]
cap["annualised_sales"] = cap["total_sales_eur"] * 12 / 8
cap["gap_annualised_eur"] = cap["max_spend_eur"] - cap["annualised_sales"]
cap["gap_overstated_eur"] = cap["gap_file_eur"] - cap["gap_annualised_eur"]
print("\n=== the implied 'gap' in euro, part-year vs annualised ===")
print(cap[["distributor_code", "total_sales_eur", "max_spend_eur", "gps_capture_vs_max",
           "gap_file_eur", "gap_annualised_eur", "gap_overstated_eur"]]
      .to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
print()
print(f"sum max_spend (18 rows) {cap['max_spend_eur'].sum():,.2f}")
print(f"sum file capture reading: min {cap['gps_capture_vs_max'].min():.4f} "
      f"max {cap['gps_capture_vs_max'].max():.4f} mean {cap['gps_capture_vs_max'].mean():.4f}")
print(f"sum implied gap as the file reads it      EUR {cap['gap_file_eur'].sum():,.2f}")
print(f"sum implied gap on an annualised basis    EUR {cap['gap_annualised_eur'].sum():,.2f}")
print(f"gap OVERSTATED by the part-year basis     EUR {cap['gap_overstated_eur'].sum():,.2f}")

# ---- distinct values ---------------------------------------------------------
print("\n=== traffic_light_v9 distinct values, all years ===")
print(gps.groupby(["year", "traffic_light_v9"]).size().to_string())
print("\n=== traffic_light (legacy) distinct, all years ===")
print(gps.groupby(["year", "traffic_light"]).size().to_string())
print("\n=== gps_capture_ex_warranty_vs_max non-null by year ===")
print(gps.groupby("year")["gps_capture_ex_warranty_vs_max"].apply(lambda s: s.notna().sum()).to_string())
print("\n=== period_basis x year ===")
print(gps.groupby(["year", "period_basis"]).size().to_string())
