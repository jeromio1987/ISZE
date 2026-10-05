# -*- coding: utf-8 -*-
"""Temp: derive the chart figures from disk and reconcile against the briefed numbers."""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"


def rd(p):
    with open(os.path.join(D, p), encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fn(v, d=0.0):
    try:
        s = str(v).strip()
        return float(s) if s else d
    except Exception:
        return d


# ---- 1. billed book, 18 markets
g = rd("gps_spu_by_distributor.csv")
g25 = [r for r in g if r["year"] == "2025"]
ws = [r for r in g25 if r["spend_per_unit_eur"].strip()]
sales_net = sum(fn(r["total_sales_eur"]) for r in ws)
uio_net = sum(fn(r["uio_units"]) for r in ws)
print("18-market billed  %.2f   (%s)" % (sales_net, len(ws)))
print("18-market UIO     %d" % uio_net)
print("network SPU       %.2f" % (sales_net / uio_net))

# ---- 2. the two directions
mix = rd("sellout_aim_network_mix_2025.csv")
bill = {r["distributor_code"]: fn(r["total_eur"]) for r in mix if r["layer"] == "billing_isze_db"}
sel = {r["distributor_code"]: fn(r["total_eur"]) for r in mix if r["layer"] == "sellout_db_dlr"}
six = sorted(set(bill) & set(sel))
print("\ntwo directions, six markets:")
for k in six:
    print("   %-9s billing %13.2f  sellout %13.2f  ratio %6.1f%%" % (k, bill[k], sel[k], 100 * sel[k] / bill[k]))
bt = sum(bill[k] for k in six)
st = sum(sel[k] for k in six)
print("   TOTAL     billing %13.2f  sellout %13.2f  ratio %6.1f%%" % (bt, st, 100 * st / bt))
print("   billing/sales_net  = %.2f%%   <-- share of billed euro in those six" % (100 * bt / sales_net))
print("   sellout/sales_net  = %.2f%%" % (100 * st / sales_net))

# ---- 2b. dealer_sellout_gps_2025.csv, same six, aggregates only
ds = rd("dealer_sellout_gps_2025.csv")
agg = {r["distributor_code"]: fn(r["total_eur"]) for r in ds if r["distributor_code"] in six}
print("\n   dealer_sellout_gps_2025 aggregates:")
for k in six:
    print("     %-9s %13.2f" % (k, agg.get(k, 0)))
print("     sum of aggregates %.2f  (brief says 16.38M)" % sum(agg.values()))

# ---- 3. three-way service-part split, CY2025
pms = rd("pms_capture_by_db_year.csv")
print("\npms_capture columns:", list(pms[0].keys()))
print("line_type values:", sorted(set(r["line_type"] for r in pms)))
y25 = [r for r in pms if r["year"] == "2025"]
for lt in sorted(set(r["line_type"] for r in pms)):
    s = sum(fn(r["actual_qty"]) for r in y25 if r["line_type"] == lt)
    se = sum(fn(r["expected_qty"]) for r in y25 if r["line_type"] == lt)
    print("  2025 %-22s actual_qty %12.0f  expected_qty %12.0f" % (lt, s, se))

# ---- 4. weight class km/yr
km = rd("warranty_cv_km_age_by_market.csv")
print("\nkm/yr aggregates (n-weighted by vins_cv_claims):")
for col in ["km_yr_N35", "km_yr_N75", "km_yr_F"]:
    num = den = 0.0
    for r in km:
        v = fn(r[col])
        n = fn(r["vins_cv_claims"])
        if v > 0:
            num += v * n
            den += n
    print("   %-12s weighted %9.0f   simple mean %9.0f" % (col, num / den if den else 0,
          sum(fn(r[col]) for r in km if fn(r[col]) > 0) / max(1, len([r for r in km if fn(r[col]) > 0]))))
il = next(r for r in km if r["market"] == "ISRAEL")
print("   ISRAEL      km_yr_all %s  N75 %s  F %s" % (il["km_yr_all_median"], il["km_yr_N75"], il["km_yr_F"]))

# ---- 5. open gaps
md = open(os.path.join(D, "_data_integrity_open_issues.md"), encoding="utf-8").read()
open_ids = [l.split("|")[1].strip().strip("*") for l in md.splitlines()
            if l.startswith("| **") and "|" in l]
print("\nopen-issue ids found:", open_ids)
