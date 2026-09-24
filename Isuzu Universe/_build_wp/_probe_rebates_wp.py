# -*- coding: utf-8 -*-
r"""Read-only probe 10: the rebate lines, the duplicate pair, and the Cordwallis case numbers."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ISZE = os.path.dirname(ROOT)
D = os.path.join(ISZE, "01_data", "00_derived")

df = pd.read_parquet(os.path.join(D, "sales_fact.parquet"))
reb = df[df["part_number"].astype(str).str.fullmatch("REBATE", case=False, na=False)].copy()
print("REBATE lines: %d  total %.2f" % (len(reb), reb["net_sales_value"].sum()))
print("distinct sold_to_sap: %d -> %s" % (reb["sold_to_sap"].nunique(),
                                          sorted(reb["sold_to_sap"].unique())))
print("distinct sold_to names: %d" % reb["sold_to"].nunique())
print("distinct description: %s" % reb["description"].unique())
print("\nITUK only (2575 + 2194):")
it = reb[reb["sold_to_sap"].isin([2575.0, 2194.0])]
print("  %d lines, %.2f" % (len(it), it["net_sales_value"].sum()))
print("\nall rebate lines:")
print(reb[["billing_date", "sold_to_sap", "sold_to", "description", "net_sales_value", "saty"]]
      .sort_values("billing_date").to_string())

print("\n== the repeated value, whatever it is")
for v, g in reb.groupby("net_sales_value"):
    if len(g) > 1:
        print("  value %.2f appears %d times:" % (v, len(g)))
        print("   ", g[["billing_date", "sold_to_sap", "sold_to"]].to_dict("records"))

print("\n== Cordwallis case verification file")
p = os.path.join(ROOT, "_STRATEGY", "_ORCHESTRATION", "ITUK_CASE_2026-09-21_01",
                 "evidence", "C04_verify_return.json")
d = json.load(open(p, encoding="utf-8"))
print("  keys:", list(d.keys()))
print("  checks_run %s  failures %s" % (d.get("checks_run"), d.get("checks_failed")))
for c in d["checks"]:
    txt = json.dumps(c, ensure_ascii=False)
    if any(k in txt for k in ("1,627", "1627", "72", "269", "147", "148", "719", "836", "852",
                              "629", "fitted", "bought", "trucks")):
        print("   -", c.get("check"), "|", c.get("return_says_or_source_says"),
              "|", str(c.get("verdict", ""))[:40])
