# -*- coding: utf-8 -*-
r"""Read-only probe 3: the billing horizon total, the rebate lines, and the DLOD label search."""
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


# ---- net value across the three raw slices, as a cross-check on the horizon total
grand = 0.0
ents = set()
for fn, keys in (("cy2023_2024.csv", ("Sold-to pt", "Payer")),
                 ("cy2025_raw.csv", ("Sold-to pt", "DB")),
                 ("cy2026_q1.csv", ("Sold-to pt", "Payer"))):
    p = os.path.join(D, fn)
    with open(p, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames
        tot = 0.0
        n = 0
        for r in rd:
            n += 1
            tot += f(r.get("Net value"))
            for k in keys:
                if r.get(k, "").strip():
                    ents.add(r[k].strip())
        grand += tot
        print("%-18s %7d rows  Net value %18.2f   keys %s" % (fn, n, tot, keys))
print("three slices together: %.2f   distinct entity keys seen: %d" % (grand, len(ents)))

# ---- sales_fact.parquet
try:
    import pandas as pd
    p = os.path.join(D, "sales_fact.parquet")
    df = pd.read_parquet(p)
    print()
    print("sales_fact.parquet: %d rows, %d columns" % (len(df), len(df.columns)))
    print("  columns:", list(df.columns))
    txt = df.astype(str)
    for needle in ("DLOD", "dlod", "DLAD", "DLAD Q1 2023"):
        hits = txt.apply(lambda c: c.str.contains(needle, case=False, regex=False, na=False))
        print("  case-insensitive %-14s total hits: %d" % (needle, int(hits.sum().sum())))
    # rebate lines
    mcol = [c for c in df.columns if "material" in c.lower() or c.lower() == "material"]
    print("  candidate material columns:", mcol)
    col = None
    for c in txt.columns:
        if txt[c].str.fullmatch("REBATE", case=False, na=False).any():
            col = c
            break
    print("  REBATE rows found in column:", col)
    if col:
        sub = df[txt[col].str.fullmatch("REBATE", case=False, na=False)]
        print("  REBATE rows: %d" % len(sub))
        vcol = [c for c in df.columns if c.lower() in ("net_value", "net value", "netvalue")]
        print("  value columns:", vcol)
        if vcol:
            print("  REBATE value total: %.2f" % sub[vcol[0]].astype(float).sum())
except Exception as exc:
    print("parquet step failed:", exc)
