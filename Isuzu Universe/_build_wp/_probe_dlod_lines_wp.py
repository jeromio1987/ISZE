# -*- coding: utf-8 -*-
r"""Read-only probe 7: read the DLOD / DLAD lines out of the raw billing extracts, line by line."""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ISZE = os.path.dirname(ROOT)
D = os.path.join(ISZE, "01_data", "00_derived")


def f(x):
    return float(str(x).replace(",", "")) if str(x).strip() else 0.0


for fn in ("cy2023_2024.csv", "cy2025_raw.csv", "cy2026_q1.csv"):
    p = os.path.join(D, fn)
    print("==", fn)
    with open(p, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        refcol = None
        for cand in ("Purchase order no.", "Purchase Order Number"):
            if cand in (rd.fieldnames or []):
                refcol = cand
        tot = 0.0
        hits = 0
        for r in rd:
            ref = (r.get(refcol) or "").strip()
            up = ref.upper()
            if "DLOD" in up or "DLAD" in up:
                hits += 1
                val = f(r.get("Net value"))
                tot += val
                print("   ref=%-22r date=%-22s payer=%-28s soldto=%-8s net=%14.2f curr=%s doc=%s" % (
                    ref, r.get("Billing Date"), r.get("Payer") or r.get("DB"),
                    r.get("Sold-to pt"), val, r.get("Curr."), r.get("Sales Doc.")))
        print("   labelled lines: %d   total %.2f   (reference column: %s)" % (hits, tot, refcol))

print()
print("== order_headers_from_Order_Detail.csv")
p = os.path.join(D, "order_headers_from_Order_Detail.csv")
with open(p, encoding="utf-8-sig", newline="") as fh:
    rd = csv.DictReader(fh)
    for r in rd:
        ref = (r.get("Purchase Order Number") or "").strip().upper()
        if "DLOD" in ref or "DLAD" in ref:
            print("   ref=%-22r created=%-12s soldto=%-8s party=%-30s eur=%14.2f qty=%s" % (
                r.get("Purchase Order Number"), r.get("created"), r.get("Sold-to pt"),
                r.get("Sold-to party"), f(r.get("eur")), r.get("qty")))
