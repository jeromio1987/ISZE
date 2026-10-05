# -*- coding: utf-8 -*-
r"""Read-only probe: reproduce every number the whitepaper will print, from its named source.

Run:  python _build_wp\_probe_sources_wp.py
"""
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = os.path.join(os.path.dirname(ROOT), "01_data", "00_derived")
TENDER = os.path.join(os.path.dirname(ROOT), "01_data", "14_dashboards", "tender_data.json")


def load(name):
    with open(os.path.join(D, name), encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def f(x):
    return float(x) if str(x).strip() else 0.0


print("== pms_genuine_bvp_vs_price_2024_2025.csv")
rows = load("pms_genuine_bvp_vs_price_2024_2025.csv")
for code, sub in (("ITUK", "brake_pad"), ("PORTUGAL", "clutch_kit")):
    r = [x for x in rows if x["distributor_code"] == code and x["product_subgroup"] == sub]
    for x in r:
        print("  %s/%s  eur %s -> %s   qty %s -> %s" % (
            code, sub, x["total_eur_2024"], x["total_eur_2025"],
            x["total_qty_2024"], x["total_qty_2025"]))
        print("        genuine %s -> %s   bvp %s -> %s" % (
            x["genuine_eur_2024"], x["genuine_eur_2025"],
            x["bvp_eur_2024"], x["bvp_eur_2025"]))
ituk_brakes = [x for x in rows if x["distributor_code"] == "ITUK"
               and x["product_group_label"] == "Brakes"]
print("  ITUK brakes subgroups:")
tot = 0.0
for x in sorted(ituk_brakes, key=lambda z: f(z["total_eur_2025"]) - f(z["total_eur_2024"])):
    d = f(x["total_eur_2024"]) - f(x["total_eur_2025"])
    tot += d
    print("    %-28s %14.2f -> %14.2f   reduction %12.2f" % (
        x["product_subgroup"], f(x["total_eur_2024"]), f(x["total_eur_2025"]), d))
print("    combined reduction %.2f" % tot)

print()
print("== pms_campaign_suspect_by_db_2024_2025.csv")
rows = load("pms_campaign_suspect_by_db_2024_2025.csv")
for yr in ("2024", "2025"):
    y = [r for r in rows if r["year"] == yr]
    tot = sum(f(r["billed_eur"]) for r in y)
    w20 = sum(f(r["billed_eur"]) * f(r["pct_eur_ge20_under_ref"]) / 100 for r in y)
    w30 = sum(f(r["billed_eur"]) * f(r["pct_eur_ge30_under_ref"]) / 100 for r in y)
    print("  %s: %d distributors, billed %.2f, ge20 %.2f (%.4f%%), ge30 %.2f (%.4f%%)" % (
        yr, len(y), tot, w20, 100 * w20 / tot, w30, 100 * w30 / tot))
    print("      ge30 share of total = %.4f%%" % (100 * w30 / tot))
y25 = sorted([r for r in rows if r["year"] == "2025"],
             key=lambda r: -f(r["pct_eur_ge20_under_ref"]))
for r in y25[:12]:
    print("      %-14s %6.2f%%  billed %14.2f" % (
        r["distributor_code"], f(r["pct_eur_ge20_under_ref"]), f(r["billed_eur"])))

print()
print("== pms_campaign_suspect_by_family_2024_2025.csv (2025)")
rows = [r for r in load("pms_campaign_suspect_by_family_2024_2025.csv") if r["year"] == "2025"]
rows.sort(key=lambda r: -f(r["billed_eur"]))
for r in rows[:10]:
    print("      %-22s %6.2f%%  billed %14.2f  n=%s" % (
        r["pms_category"], f(r["pct_eur_ge20_under_ref"]), f(r["billed_eur"]), r["n_lines"]))

print()
print("== gps_spu_by_distributor.csv")
rows = load("gps_spu_by_distributor.csv")
for yr in ("2025",):
    y = [r for r in rows if r["year"] == yr and r["total_sales_eur"].strip()]
    tot = sum(f(r["total_sales_eur"]) for r in y)
    print("  %s: %d rows with billed EUR, total %.2f" % (yr, len(y), tot))
    yf = [r for r in y if r["uio_units"].strip() and r["max_spend_eur"].strip()]
    print("       %d rows with a fleet figure and a ceiling, billed %.2f, ceiling %.2f" % (
        len(yf), sum(f(r["total_sales_eur"]) for r in yf),
        sum(f(r["max_spend_eur"]) for r in yf)))
    flat = [r for r in yf if abs(f(r["max_spend_eur"]) / f(r["uio_units"]) - 250.0) < 0.01]
    print("       flat 250/truck: %d markets, ceiling %.2f = %.4f%%" % (
        len(flat), sum(f(r["max_spend_eur"]) for r in flat),
        100 * sum(f(r["max_spend_eur"]) for r in flat)
        / sum(f(r["max_spend_eur"]) for r in yf)))
    print("       names:", ", ".join(sorted(r["distributor_code"] for r in flat)))
    print("       100k as share of billed: %.4f%%" % (100000 / tot * 100))
    print("       300k as share of billed: %.4f%%" % (300000 / tot * 100))
    print("       ituk billed: %s" % [r["total_sales_eur"] for r in y
                                      if r["distributor_code"] == "ITUK"])

print()
print("== ids_dealer_network_cleaned_2026-09-20.csv")
rows = load("ids_dealer_network_cleaned_2026-09-20.csv")
sc = [f(r["points_pct"]) for r in rows if r["points_pct"].strip()]
print("  rows %d, scored %d, avg %.4f, min %s max %s" % (
    len(rows), len(sc), sum(sc) / len(sc), min(sc), max(sc)))
ns = [r for r in rows if r["points_pct"].strip() and f(r["points_pct"]) > 100]
print("  rows above 100: %d, max %s" % (len(ns), max([f(r["points_pct"]) for r in ns] or [0])))
bysrc = {}
for r in rows:
    bysrc.setdefault(r["ids_tab"], 0)
    bysrc[r["ids_tab"]] += 1
print("  tabs %d" % len(bysrc))
print("  " + ", ".join("%s %d" % kv for kv in sorted(bysrc.items(), key=lambda z: -z[1])))

print()
print("== ids_dealer_network.csv (raw)")
rows = load("ids_dealer_network.csv")
print("  rows %d" % len(rows))
print("  cols:", list(rows[0].keys())[:20])

print()
print("== pms_capture_by_db_year.csv  ITUK 2025 total")
rows = load("pms_capture_by_db_year.csv")
r = [x for x in rows if x["distributor_code"] == "ITUK" and x["year"] == "2025"
     and x["line_type"] == "total"]
r.sort(key=lambda z: -f(z["actual_rev_eur"]))
for x in r[:12]:
    print("      %-22s capture %8.4f  rev %14.2f  gap %14.2f" % (
        x["category_label"], f(x["capture_rate"]), f(x["actual_rev_eur"]),
        f(x["revenue_gap_eur"])))
print("  denominators:", sorted({x["uio_units"] + "/" + x["scope"] for x in r}))

print()
print("== tender_data.json")
d = json.load(open(TENDER, encoding="utf-8"))
print("  stats:", json.dumps(d["meta"]["stats"], ensure_ascii=False))
print("  outcomes:", json.dumps(d["meta"]["outcomes_summary"], ensure_ascii=False))
print("  meta keys:", list(d["meta"].keys()))
