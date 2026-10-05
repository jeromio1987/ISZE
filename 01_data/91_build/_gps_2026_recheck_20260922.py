"""Re-verify the Part 2 findings against the CURRENT file (it was rewritten at 18:55 today)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")
print("rows", len(gps), "cols", len(gps.columns))
print("has period_basis:", "period_basis" in gps.columns,
      "| has coverage_note:", "coverage_note" in gps.columns)
d = gps[gps.year == 2026]
print()
print("2026 rows:", len(d))
print("capture non-null:", int(d["gps_capture_vs_max"].notna().sum()))
print("capture range:", (round(d["gps_capture_vs_max"].min(), 4), round(d["gps_capture_vs_max"].max(), 4)))
print("capture mean:", round(d["gps_capture_vs_max"].mean(), 4))
print("red:", int((d["traffic_light_v9"] == "red").sum()),
      "amber:", int((d["traffic_light_v9"] == "amber").sum()),
      "unknown:", int((d["traffic_light_v9"] == "unknown").sum()))
print("period_basis:", d["period_basis"].value_counts().to_dict() if "period_basis" in d.columns else "MISSING")
print("ex-warranty capture non-null:", int(d["gps_capture_ex_warranty_vs_max"].notna().sum()))
print()
print("UNMAPPED present in 2026:", "UNMAPPED" in set(d["distributor_code"]))
print()
print(d[["distributor_code", "total_sales_eur", "max_spend_eur", "gps_capture_vs_max",
         "traffic_light_v9", "period_basis"]].to_string(index=False))
cap = d[d["max_spend_eur"].notna()]
print()
print(f"sum max_spend {cap['max_spend_eur'].sum():,.2f}")
print(f"gap as file reads  { (cap['max_spend_eur']-cap['total_sales_eur']).sum():,.2f}")
print(f"gap annualised     { (cap['max_spend_eur']-cap['total_sales_eur']*12/8).sum():,.2f}")
print(f"overstated         { (cap['max_spend_eur']-cap['total_sales_eur']).sum() - (cap['max_spend_eur']-cap['total_sales_eur']*12/8).sum():,.2f}")
