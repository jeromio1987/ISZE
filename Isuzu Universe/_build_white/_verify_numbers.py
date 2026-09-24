# -*- coding: utf-8 -*-
"""Read-only verification of every number the white paper will print, straight from source."""
import csv
import json
import sys

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
sys.stdout.reconfigure(encoding="utf-8")


def rows(name):
    with open(ROOT + "\\" + name, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


print("=== 1. ITUK brake pads and the three brake categories ===")
gb = rows("pms_genuine_bvp_vs_price_2024_2025.csv")
it = [r for r in gb if r["distributor_code"] == "ITUK"]
brakes = [r for r in it if r["product_group_label"] == "Brakes"]
tot24 = tot25 = 0.0
for r in brakes:
    a, b = float(r["total_eur_2024"]), float(r["total_eur_2025"])
    tot24 += a
    tot25 += b
    print("  %-16s 2024 %12.2f  2025 %12.2f  delta %11.2f  qty %s->%s"
          % (r["product_subgroup"], a, b, b - a, r["total_qty_2024"], r["total_qty_2025"]))
print("  COMBINED brakes delta: %.2f" % (tot25 - tot24))
pads = [r for r in brakes if r["product_subgroup"] == "brake_pad"][0]
print("  pads share of the combined reduction: %.1f%%"
      % (100 * (float(pads["total_eur_2025"]) - float(pads["total_eur_2024"])) / (tot25 - tot24)))

print()
print("=== 2. Portugal clutch kit ===")
pt = [r for r in gb if r["distributor_code"] == "PORTUGAL" and r["product_subgroup"] == "clutch_kit"][0]
for f in ("total_eur_2024", "total_eur_2025", "total_qty_2024", "total_qty_2025",
          "genuine_eur_2024", "genuine_eur_2025", "bvp_eur_2024", "bvp_eur_2025"):
    print("  %-18s %s" % (f, pt[f]))
c24 = float(pt["total_eur_2024"])
c25 = float(pt["total_eur_2025"])
print("  combined change %.2f = %.2f%%" % (c25 - c24, 100 * (c25 - c24) / c24))

print()
print("=== 3. Deep concession, 2025 ===")
dbs = [r for r in rows("pms_campaign_suspect_by_db_2024_2025.csv") if r["year"] == "2025"]
billed = sum(float(r["billed_eur"]) for r in dbs)
print("  distributors: %d   billed 2025: %.2f" % (len(dbs), billed))
ge20 = sum(float(r["billed_eur"]) * float(r["pct_eur_ge20_under_ref"]) / 100 for r in dbs)
ge30 = sum(float(r["billed_eur"]) * float(r["pct_eur_ge30_under_ref"]) / 100 for r in dbs)
print("  EUR at least 20%% under reference: %.0f = %.1f%%" % (ge20, 100 * ge20 / billed))
print("  EUR at least 30%% under reference: %.0f = %.1f%%" % (ge30, 100 * ge30 / billed))
for r in sorted(dbs, key=lambda x: -float(x["pct_eur_ge20_under_ref"]))[:6]:
    print("    %-12s %5.1f%%  of EUR %10.0f" % (r["distributor_code"],
                                                 float(r["pct_eur_ge20_under_ref"]),
                                                 float(r["billed_eur"])))
d24 = [r for r in rows("pms_campaign_suspect_by_db_2024_2025.csv") if r["year"] == "2024"]
b24 = sum(float(r["billed_eur"]) for r in d24)
g24 = sum(float(r["billed_eur"]) * float(r["pct_eur_ge20_under_ref"]) / 100 for r in d24)
g34 = sum(float(r["billed_eur"]) * float(r["pct_eur_ge30_under_ref"]) / 100 for r in d24)
print("  2024 base %.2f  ge20 %.1f%%  ge30 %.1f%%" % (b24, 100 * g24 / b24, 100 * g34 / b24))

print()
print("=== 4. Deep concession by family, 2025 ===")
fam = [r for r in rows("pms_campaign_suspect_by_family_2024_2025.csv") if r["year"] == "2025"]
fam.sort(key=lambda r: -float(r["billed_eur"]))
for r in fam[:8]:
    print("    %-18s %5.1f%%  of EUR %10.0f" % (r["pms_category"],
                                                 float(r["pct_eur_ge20_under_ref"]),
                                                 float(r["billed_eur"])))
