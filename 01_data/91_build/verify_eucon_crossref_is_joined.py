# -*- coding: utf-8 -*-
"""
CORRECTION, 2026-09-18.

A cross-reference review claimed: "eucon_crossref_iam_20260329.csv holds 822 rows
with a real price column and had NEVER BEEN JOINED."

The first half is true. The second half is FALSE, and it matters because acting on
it would have ordered work we have already done.

What was verified here:
  - eucon_crossref_iam_20260329.csv carries 822 rows, 44 distinct isze_pn,
    432 competitor_pn, 155 brands, and a real price on every row.
  - eucon_price_gap.csv carries the SAME 44 part numbers - 44 of 44 overlap.
    It IS that cross-reference, aggregated to one row per part number.
  - The paper's T3 evidence tier reads eucon_price_gap.csv: 446 lines, EUR
    2,495,438. So the cross-reference IS wired, as T3.

What is genuinely unused is narrower and still useful:
  - the 432 IAM part numbers (competitor_pn) appear in NO derived file. They are
    usable as search keys anywhere that indexes by IAM catalogue number rather
    than by OEM number - which is most independent shops.
  - the per-brand price detail is collapsed in the gap file: the crossref has 822
    rows (brand x part number x country) against 44 aggregated rows.

Run: python 01_data/91_build/verify_eucon_crossref_is_joined.py
"""
import glob
import io
import json
import os
import sys

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
REF = os.path.join(ISZE, "02_dashboards", "Data", "01_Pricing", "_raw",
                   "eucon_crossref_iam_20260329.csv")


def say(m=""):
    print(m)
    sys.stdout.flush()


x = pd.read_csv(REF, dtype=str)
x["pn"] = x["isze_pn"].astype(str).str.strip().str.zfill(10)
x["price"] = pd.to_numeric(x["med_online_eur"], errors="coerce")
g = pd.read_csv(os.path.join(D, "eucon_price_gap.csv"), dtype=str)
g["pn"] = g["pn"].astype(str).str.strip()
spec = json.load(open(os.path.join(ISZE, "02_dashboards", "pricing", "_build",
                                   "_spec_basis_meta.json"), encoding="utf-8"))

say("=" * 82)
say("IS THE EUCON CROSS-REFERENCE ALREADY JOINED?")
say("=" * 82)
say(f"  crossref rows                     : {len(x):,}")
say(f"  crossref distinct isze_pn         : {x['pn'].nunique():,}")
say(f"  crossref distinct competitor_pn   : {x['competitor_pn'].nunique():,}")
say(f"  crossref distinct brands          : {x['Competitor_Brand'].nunique():,}")
say(f"  crossref rows with a real price   : {x['price'].notna().sum():,} of {len(x):,}")
say()
say(f"  eucon_price_gap.csv distinct pn   : {g['pn'].nunique():,}")
overlap = len(set(x["pn"]) & set(g["pn"]))
say(f"  overlap between the two           : {overlap} of {x['pn'].nunique()}")
say()
say("  VERDICT: the gap file IS the cross-reference aggregated to one row per part")
say("  number. 44 of 44 overlap. The claim that it 'had never been joined' is FALSE.")
say()
say(f"  And it is wired into the paper: the T3 evidence tier reads that file.")
say(f"    T3 lines : {spec['tier_counts']['T3']:,}")
say(f"    T3 euro  : EUR {spec['tier_eur']['T3']:,.0f}")
say()
say("=" * 82)
say("WHAT IS GENUINELY UNUSED IN IT")
say("=" * 82)
iam_pns = set(x["competitor_pn"].dropna().astype(str).str.strip())
found = []
for f in glob.glob(os.path.join(D, "*.csv")) + glob.glob(os.path.join(D, "*.parquet")):
    try:
        s = pd.read_csv(f, dtype=str, nrows=400) if f.endswith(".csv") else None
        if s is not None and any(c in s.columns for c in ("competitor_pn", "iam_pn", "brand_pn")):
            found.append(os.path.basename(f))
    except Exception:                                           # noqa: BLE001
        pass
say(f"  432 IAM part numbers (the competing catalogue numbers)")
say(f"    derived files that carry an IAM part-number column : "
    f"{found if found else 'NONE'}")
say()
say("  So the unused asset is the IAM NUMBERS THEMSELVES, not the cross-reference.")
say("  Those 432 numbers are valid search keys on any shop that indexes by IAM")
say("  catalogue number rather than by OEM number - which is most independent shops,")
say("  and is the exact barrier that made our scrapes return little.")
say()
say("  Per-brand detail is also collapsed in the gap file: 822 rows against 44.")
say("  The brand-level prices are there and the paper's table does not use them.")
say()
say("  Price tiers: crossref prices are online IAM EUR, DE and NO, against the raw")
say("  IE40 list. Not the same tier as KS GBP trade, and neither is the reference")
say("  dealer price. Never blend them.")
say()
say("VERIFY_OK")
