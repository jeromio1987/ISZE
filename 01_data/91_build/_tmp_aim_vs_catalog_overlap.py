import csv
import pandas as pd
from collections import defaultdict
from pathlib import Path

rows = list(csv.DictReader(Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_pn_classification_v2.csv").open(encoding="utf-8", newline="")))
sf = pd.read_parquet(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_fact.parquet", columns=["billing_date", "part_number", "net_sales_value"])
sf["d"] = pd.to_datetime(sf["billing_date"], errors="coerce")
w = sf[sf["d"] >= "2025-01-01"].copy()
w["pn"] = w["part_number"].astype(str)
eur = w.groupby("pn")["net_sales_value"].sum().to_dict()

both = [
    r for r in rows
    if r["workbook_l1"].strip() and r["workbook_l1"] not in ("Unknown", "Unknown Review")
    and r["catalog_l1"].strip() and r["catalog_l1"] != "Other / review"
]
print("rows where BOTH a real AIM category and a real catalogue node exist:", len(both))

d = defaultdict(set)
for r in both:
    d[r["workbook_l1"]].add(r["catalog_l1"])
multi = {k: v for k, v in d.items() if len(v) > 1}
print("AIM Level-1 values spanning >1 catalogue posture:", len(multi), "of", len(d))
print()

tot = 0.0
amb = 0.0
for k, v in sorted(d.items(), key=lambda x: -len(x[1]))[:12]:
    e = sum(eur.get(r["part_number"], 0) for r in both if r["workbook_l1"] == k)
    tot += e
    if len(v) > 1:
        amb += e
    joined = ", ".join(sorted(v))[:66]
    print("%-26s spans %d posture(s)  eur %10s  ->  %s" % (k, len(v), round(e), joined))
print()
print("euro on those top-12 AIM values:", round(tot))
print("of which spans >1 posture:", round(amb))
