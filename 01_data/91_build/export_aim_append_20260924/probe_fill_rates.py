# -*- coding: utf-8 -*-
"""Read-only: fill rates and conventions on the master, to mirror them in the append."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"

rows = []
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    hdr = list(csv.reader([fh.readline()]))[0]
    for r in csv.DictReader(fh, fieldnames=hdr):
        rows.append(r)
print("rows", len(rows))

print("\n--- fill rate per column (non-empty) ---")
for c in hdr:
    ne = sum(1 for r in rows if (r.get(c) or "").strip() != "")
    print(f"{c:<24} {ne:>7}  {100*ne/len(rows):5.1f}%")

print("\n--- ENGINE ASM rows: fig_key / fig_no / key_no / cat_* ---")
eng = [r for r in rows if (r.get("description") or "") == "ENGINE ASM"]
print("count", len(eng))
print("fig_key:", Counter((r.get("fig_key") or "") for r in eng).most_common(5))
print("fig_no :", Counter((r.get("fig_no") or "") for r in eng).most_common(5))
print("key_no :", Counter((r.get("key_no") or "") for r in eng).most_common(5))
print("cat_l1 :", Counter((r.get("cat_l1") or "") for r in eng).most_common(5))
print("cat_l2 :", Counter((r.get("cat_l2") or "") for r in eng).most_common(5))
print("cat_l3 :", Counter((r.get("cat_l3") or "") for r in eng).most_common(5))
print("cat_pms_flag:", Counter((r.get("cat_pms_flag") or "") for r in eng).most_common(5))
print("price_class_iml:", Counter((r.get("price_class_iml") or "") for r in eng).most_common(5))
print("aim_demand_type:", Counter((r.get("aim_demand_type") or "") for r in eng).most_common(5))
print("aim_core_noncore:", Counter((r.get("aim_core_noncore") or "") for r in eng).most_common(5))
print("has_catalogue_node:", Counter((r.get("has_catalogue_node") or "") for r in eng).most_common(5))

print("\n--- l12m_billed_eur and eur: empty vs zero vs value ---")
for c in ("l12m_billed_eur", "eur"):
    vals = [(r.get(c) or "").strip() for r in rows]
    print(f"{c}: empty={sum(1 for v in vals if v=='')} zero={sum(1 for v in vals if v in ('0','0.0','0.00'))}")
    print("   sample non-numeric:", [v for v in vals if v and not v.replace('.', '').replace('-', '').isdigit()][:8])

print("\n--- comparison of master cat_l1 vs classification catalog_l1 (sample 3000) ---")
cls = {}
with (D / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        cls[r["part_number"]] = r
agree = dis = miss = 0
for r in rows[:40000]:
    c = cls.get(r["part_number"])
    if not c:
        miss += 1
        continue
    a = (r.get("cat_l1") or "").strip()
    b = (c.get("catalog_l1") or "").strip()
    if a == b:
        agree += 1
    else:
        dis += 1
print(f"agree={agree} disagree={dis} not_in_classification={miss}")

print("\n--- price_class_iml on the master overall ---")
print(Counter((r.get("price_class_iml") or "") for r in rows).most_common(15))

print("\n--- aim_demand_type overall ---")
print(Counter((r.get("aim_demand_type") or "") for r in rows).most_common(12))

print("\n--- cat_pms_flag overall ---")
print(Counter((r.get("cat_pms_flag") or "") for r in rows).most_common(6))

print("\n--- rows whose fig_no == '001' ---")
print("count", sum(1 for r in rows if (r.get("fig_no") or "").strip() == "001"))
print("fig_key values:", Counter((r.get("fig_key") or "") for r in rows if (r.get("fig_no") or "").strip() == "001").most_common(8))
