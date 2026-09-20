# -*- coding: utf-8 -*-
"""Temp: reconcile the briefed 54.4% visibility and the weight-class km/yr figures."""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"


def rd(p):
    with open(os.path.join(D, p), encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fn(v, d=0.0):
    try:
        s = str(v).strip()
        return float(s) if s else d
    except Exception:
        return d


g = rd("gps_spu_by_distributor.csv")
g25 = [r for r in g if r["year"] == "2025"]
ws = [r for r in g25 if r["spend_per_unit_eur"].strip()]
sales_net = sum(fn(r["total_sales_eur"]) for r in ws)
no_spu = [r for r in g25 if not r["spend_per_unit_eur"].strip()]
print("with-SPU rows %d  billed %.2f" % (len(ws), sales_net))
print("no-SPU rows %d  billed %.2f -> %s" % (
    len(no_spu), sum(fn(r["total_sales_eur"]) for r in no_spu),
    [r["distributor_code"] for r in no_spu]))

# true sum of every entity row in dealer_sellout_gps_2025.csv
ds = rd("dealer_sellout_gps_2025.csv")
six = ["ITUK", "UTI", "IRELAND", "IUK", "GREECE", "PORTUGAL"]
per = {}
for k in six:
    rows = [r for r in ds if r["distributor_code"] == k]
    per[k] = (len(rows), sum(fn(r["total_eur"]) for r in rows))
print("\ndealer_sellout_gps_2025.csv, all entity rows per market:")
tot = 0.0
n = 0
for k in six:
    print("   %-9s entities %3d  total %13.2f" % (k, per[k][0], per[k][1]))
    tot += per[k][1]
    n += per[k][0]
print("   TOTAL     entities %3d  total %13.2f" % (n, tot))
print("   sellout / 18-market billed book = %.2f%%" % (100 * tot / sales_net))

mix = rd("sellout_aim_network_mix_2025.csv")
sel = sum(fn(r["total_eur"]) for r in mix if r["layer"] == "sellout_db_dlr")
bil = sum(fn(r["total_eur"]) for r in mix if r["layer"] == "billing_isze_db")
print("\nmix file: sellout %.2f  billing %.2f" % (sel, bil))
print("   sellout/billed      = %.2f%%" % (100 * sel / sales_net))
print("   billing/billed      = %.2f%%" % (100 * bil / sales_net))
print("   (briefed visibility = 54.4%%)")

# what numerator gives 54.4%?
print("   numerator needed for 54.4%% = %.0f" % (0.544 * sales_net))

# ---- weight class km
km = rd("warranty_cv_km_age_by_market.csv")
print("\nkm/yr per weight class, all rows:")
for col in ["km_yr_N35", "km_yr_N75", "km_yr_F"]:
    vals = [(r["market"], fn(r[col]), fn(r["vins_cv_claims"])) for r in km if fn(r[col]) > 0]
    print("  %s  n=%d" % (col, len(vals)))
    for m, v, c in vals:
        print("      %-22s %9.0f   vins %6.0f" % (m, v, c))
    print("      simple mean %.0f | n-weighted %.0f | total-vins weighted %.0f"
          % (sum(v for _, v, _ in vals) / len(vals),
             sum(v * c for _, v, c in vals) / sum(c for _, _, c in vals),
             sum(v for _, v, _ in vals) / len(vals)))
    # excluding the tiny sample markets (the file's own 'thin' markets)
    big = [(m, v, c) for m, v, c in vals if c >= 200]
    if big:
        print("      markets with >=200 VINs only (n=%d): simple mean %.0f | weighted %.0f"
              % (len(big), sum(v for _, v, _ in big) / len(big),
                 sum(v * c for _, v, c in big) / sum(c for _, _, c in big)))
