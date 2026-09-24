# -*- coding: utf-8 -*-
r"""Read-only probe 5: the ITUK total capture row, and the network billing bases for the money chapter."""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ISZE = os.path.dirname(ROOT)
D = os.path.join(ISZE, "01_data", "00_derived")


def load(p):
    with open(p, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def f(x):
    return float(str(x).replace(",", "")) if str(x).strip() else 0.0


print("== ITUK 2025 capture, all line types")
rows = load(os.path.join(D, "pms_capture_by_db_year.csv"))
for r in rows:
    if r["distributor_code"] == "ITUK" and r["year"] == "2025" and r["line_type"] == "total":
        print("  %-22s capture %.4f  billed %12.2f gap %12.2f uio %s scope %s" % (
            r["category_label"], f(r["capture_rate"]), f(r["actual_rev_eur"]),
            f(r["revenue_gap_eur"]), r["uio_units"], r["scope"]))
tot = [r for r in rows if r["distributor_code"] == "ITUK" and r["year"] == "2025"
       and r["line_type"] == "total" and r["category_label"].lower().startswith("total")]
print("  rows whose label starts with 'total':", len(tot))
labels = sorted({r["category_label"] for r in rows if r["line_type"] == "total"})
print("  distinct total-line labels:", labels[:12], "... n=%d" % len(labels))

print()
print("== network billing bases, derived billing file")
import pandas as pd
df = pd.read_parquet(os.path.join(D, "sales_fact.parquet"))
dim = pd.read_csv(os.path.join(D, "distributor_dimension.csv"), encoding="utf-8-sig")
net = set(dim.loc[dim["network_role"].astype(str).eq("network_db"), "sold_to_sap"])
print("  network_db entities: %d" % len(net))
sub = df[df["sold_to_sap"].isin(net)]
ch = sub[sub["billing_date"] <= "2025-12-31"]
print("  calendar 2025, network entities only: %.2f across %d entities" % (
    ch["net_sales_value"].sum(), ch["sold_to_sap"].nunique()))
fy = sub[(sub["billing_date"] >= "2025-04-01") & (sub["billing_date"] <= "2026-03-31")]
print("  FY2026 (Apr 2025-Mar 2026), network entities only: %.2f across %d entities" % (
    fy["net_sales_value"].sum(), fy["sold_to_sap"].nunique()))
print("  whole horizon, network entities only: %.2f across %d entities" % (
    sub["net_sales_value"].sum(), sub["sold_to_sap"].nunique()))
print("  whole horizon, all entities: %.2f across %d entities" % (
    df["net_sales_value"].sum(), df["sold_to_sap"].nunique()))
print("  570000 as share of calendar-2025 network billed: %.4f%%" % (
    100 * 570000 / ch["net_sales_value"].sum()))
print("  570000 as share of FY2026 network billed: %.4f%%" % (
    100 * 570000 / fy["net_sales_value"].sum()))
print("  90000 as share of FY2026 network billed: %.4f%%" % (
    100 * 90000 / fy["net_sales_value"].sum()))
