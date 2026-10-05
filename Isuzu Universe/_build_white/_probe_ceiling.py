# -*- coding: utf-8 -*-
"""Read-only probe: which 2025 markets sit on a flat per-truck ceiling, and what they hold."""
import csv
import sys

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
sys.stdout.reconfigure(encoding="utf-8")

rows = [r for r in csv.DictReader(
    open(ROOT + r"\01_data\00_derived\gps_spu_by_distributor.csv", encoding="utf-8-sig"))
    if r["year"] == "2025"]

print("code          uio        ceiling           ceil/uio   spend/truck  source")
for r in rows:
    u = float(r["uio_units"])
    m = float(r["max_spend_eur"])
    print("%-12s %9.0f %15.2f %10.4f %10.2f  %s"
          % (r["distributor_code"], u, m, m / u, float(r["spend_per_unit_eur"]), r["uio_source"]))

flat = [r for r in rows if abs(float(r["max_spend_eur"]) / float(r["uio_units"]) - 250.0) < 0.01]
print()
print("markets on a flat 250 per truck:", len(flat), [r["distributor_code"] for r in flat])
print("their ceiling sum:", round(sum(float(r["max_spend_eur"]) for r in flat), 2))
total = sum(float(r["max_spend_eur"]) for r in rows)
print("all 2025 ceiling:", round(total, 2),
      "flat share:", round(100 * sum(float(r["max_spend_eur"]) for r in flat) / total, 2), "%")
