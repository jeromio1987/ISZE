# -*- coding: utf-8 -*-
"""Read-only probes for the white-paper figure plan: what the source CSVs actually hold."""
import csv
import sys

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
sys.stdout.reconfigure(encoding="utf-8")


def rows(name):
    with open(ROOT + "\\" + name, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


print("=== ITUK brake subgroups in pms_genuine_bvp_vs_price_2024_2025.csv ===")
gb = rows("pms_genuine_bvp_vs_price_2024_2025.csv")
ituk = [r for r in gb if r["distributor_code"] == "ITUK"]
for r in ituk:
    print("  %-22s %-26s 2024=%-14s 2025=%-14s qty %s->%s"
          % (r["product_group_label"][:22], r["product_subgroup"], r["total_eur_2024"],
             r["total_eur_2025"], r["total_qty_2024"], r["total_qty_2025"]))
print("  ITUK subgroups:", sorted({r["product_subgroup"] for r in ituk}))

print()
print("=== PORTUGAL rows ===")
pt = [r for r in gb if r["distributor_code"] == "PORTUGAL"]
print("  subgroups:", sorted({r["product_subgroup"] for r in pt}))

print()
print("=== pms_capture_by_db_year.csv columns ===")
cap = rows("pms_capture_by_db_year.csv")
print("  cols:", list(cap[0].keys()))
it = [r for r in cap if r.get("distributor_code") == "ITUK" and r.get("year") == "2025"]
for r in it[:8]:
    print("   ", {k: r[k] for k in list(r)[:26]})

print()
print("=== tender outcomes / decisions ===")
import json
t = json.load(open(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json",
                   encoding="utf-8"))
print("  meta.generated_at:", t["meta"]["generated_at"])
print("  stats:", t["meta"]["stats"])
print("  decisions:", t["meta"]["decision_counts"])
print("  outcomes:", t["meta"]["outcomes_summary"])
