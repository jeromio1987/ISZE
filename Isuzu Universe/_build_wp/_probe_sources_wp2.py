# -*- coding: utf-8 -*-
r"""Read-only probe 2: the two contradictions, plus the horizon figure and the ITUK fleet base."""
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


print("== raw ids_dealer_network.csv  score column, by network")
rows = load(os.path.join(D, "ids_dealer_network.csv"))
print("  columns:", list(rows[0].keys()))
sc = [f(r["points_pct"]) for r in rows if str(r.get("points_pct", "")).strip()]
print("  scored %d of %d, min %s max %s" % (len(sc), len(rows), min(sc), max(sc)))
big = [r for r in rows if str(r.get("points_pct", "")).strip() and f(r["points_pct"]) > 100]
print("  above 100: %d" % len(big))
tabs = {}
for r in big:
    tabs[r["ids_tab"]] = tabs.get(r["ids_tab"], 0) + 1
print("  by tab:", tabs)
ok = [f(r["points_pct"]) for r in rows
      if str(r.get("points_pct", "")).strip() and f(r["points_pct"]) <= 100]
print("  the <=100 subset: %d rows, avg %.4f" % (len(ok), sum(ok) / len(ok)))

print()
print("== cleaned file: any date / address?")
rows = load(os.path.join(D, "ids_dealer_network_cleaned_2026-09-20.csv"))
print("  address non-empty: %d of %d" % (sum(1 for r in rows if r["address"].strip()), len(rows)))
names = [r["dealer_name"].strip().lower() for r in rows]
print("  distinct names: %d" % len(set(names)))

print()
print("== billing horizon: can I reproduce a network total?")
for fn in ("cy2023_2024.csv", "cy2025_raw.csv", "cy2026_q1.csv"):
    p = os.path.join(D, fn)
    if not os.path.exists(p):
        print("  %s  MISSING" % fn)
        continue
    import csv as _c
    with open(p, encoding="utf-8-sig", newline="") as fh:
        rd = _c.reader(fh)
        hdr = next(rd)
        n = 0
        for _ in rd:
            n += 1
    print("  %s  %d data rows" % (fn, n))
    print("      columns:", hdr)

print()
print("== order_headers_from_Order_Detail.csv")
p = os.path.join(D, "order_headers_from_Order_Detail.csv")
with open(p, encoding="utf-8-sig", newline="") as fh:
    rd = csv.reader(fh)
    hdr = next(rd)
    n = sum(1 for _ in rd)
print("  %d rows" % n)
print("  columns:", hdr)

print()
print("== distributor_dimension.csv")
rows = load(os.path.join(D, "distributor_dimension.csv"))
print("  %d rows, columns %s" % (len(rows), list(rows[0].keys())))

print()
print("== ITUK fleet base 22,389 - where does it live?")
p = os.path.join(ISZE, "01_data", "00_derived", "gps_spu_by_distributor.csv")
for r in load(p):
    if r["distributor_code"] == "ITUK":
        print("  %s ituk: uio=%s max_spend=%s billed=%s period=%s" % (
            r["year"], r["uio_units"], r["max_spend_eur"], r["total_sales_eur"],
            r["period_basis"]))
