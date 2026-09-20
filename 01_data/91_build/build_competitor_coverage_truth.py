# -*- coding: utf-8 -*-
"""
Consolidated competitor evidence inventory, with the true coverage of each source.

Motivation (2026-09-18): a review found that eucon_crossref_iam_20260329.csv holds
822 rows of isze_pn -> competitor_brand -> competitor_pn with a REAL price column,
on our own disk and never joined. That is a richer competitor base than the
same-shop listings panel the pricing paper was built on. This file measures both
and states which is which, so the paper cannot understate what we hold.

Run: python 01_data/91_build/build_competitor_coverage_truth.py
Writes: 01_data/00_derived/competitor_coverage_truth.csv
        01_data/00_derived/competitor_coverage_truth_meta.json
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"

LEGACY = os.path.join(ISZE, "02_dashboards", "Data", "01_Pricing", "_raw")


def say(m=""):
    print(m)
    sys.stdout.flush()


# ---- the book, to convert coverage into euro
book = pd.read_parquet(os.path.join(D, "pricing_aim_source_lines.parquet"))
book["pn"] = book["part_number"].astype(str).str.strip()
pr = book[book["priced_both"] == True].copy()                      # noqa: E712
BOOK_EUR = pr["billed_eur"].sum()
BOOK_PNS = pr["pn"].nunique()
say("=" * 86)
say("THE PRICED BOOK WE ARE TRYING TO PRICE")
say("=" * 86)
say(f"  billed euro   : EUR {BOOK_EUR:,.0f}")
say(f"  part numbers  : {BOOK_PNS:,}")
say()

rows = []


def coverage(label, pns, note, price_kind):
    s = set(pns)
    m = pr[pr["pn"].isin(s)]
    rows.append({
        "source": label,
        "part_numbers": len(s & set(pr["pn"])),
        "billed_eur": float(m["billed_eur"].sum()),
        "pct_of_book_eur": 100 * m["billed_eur"].sum() / BOOK_EUR,
        "price_kind": price_kind,
        "note": note,
    })
    return m["billed_eur"].sum()


# ---------------------------------------------------------------- 1. KS panel
ks = pd.read_csv(os.path.join(D, "iam_ks_price_gap.csv"), dtype={"pn": str})
ks["pn"] = ks["pn"].str.strip()
cov_ks = coverage("Same-shop listings (KS), the panel in the paper",
                  ks["pn"].unique(),
                  "ONE UK source, fanned across 18 market rows. GBP ex-VAT at 1.17",
                  "same-shop trade, GBP")
say(f"  KS panel                    : {ks['pn'].nunique():>5} PNs  "
    f"EUR {cov_ks:>12,.0f}  {100*cov_ks/BOOK_EUR:.1f}% of book")

# ---------------------------------------------------------------- 2. Eucon crossref
xp = os.path.join(LEGACY, "eucon_crossref_iam_20260329.csv")
x = pd.read_csv(xp, dtype=str) if os.path.exists(xp) else pd.DataFrame()
if len(x):
    x["pn"] = x["isze_pn"].astype(str).str.strip().str.zfill(10)
    x["price"] = pd.to_numeric(x["med_online_eur"], errors="coerce")
    cov_x = coverage("Eucon IAM cross-reference (822 rows, never joined)",
                     x["pn"].unique(),
                     f"{x['competitor_pn'].nunique()} IAM part numbers, "
                     f"{x['Competitor_Brand'].nunique()} brands, "
                     f"countries {sorted(x['Country'].dropna().unique())}",
                     "online IAM, EUR, DE/NO")
    say(f"  Eucon crossref              : {x['pn'].nunique():>5} PNs  "
        f"EUR {cov_x:>12,.0f}  {100*cov_x/BOOK_EUR:.1f}% of book")
    say(f"     IAM part numbers         : {x['competitor_pn'].nunique():,}")
    say(f"     competitor brands        : {x['Competitor_Brand'].nunique():,}")
    say(f"     rows with a real price   : {x['price'].notna().sum():,} of {len(x):,}")

# ---------------------------------------------------------------- 3. Eucon gap
g = pd.read_csv(os.path.join(D, "eucon_price_gap.csv"), dtype=str)
g["pn"] = g["pn"].astype(str).str.strip()
cov_g = coverage("Eucon/PartsPool gap file (the 44 we quote)",
                 g["pn"].unique(),
                 "min/avg/max competitor EUR and a brand list per part number",
                 "online IAM, EUR, DE/NO")
cnt = pd.to_numeric(g["Competitor_Count"], errors="coerce")
say(f"  Eucon gap file              : {g['pn'].nunique():>5} PNs  "
    f"EUR {cov_g:>12,.0f}  {100*cov_g/BOOK_EUR:.1f}% of book")
say(f"     competitor offers per PN : median {cnt.median():.0f}, max {cnt.max():.0f}")
say(f"     brands named in file     : "
    f"{len({b.strip() for s in g['Brands_Found'].dropna() for b in str(s).split(',')})}")

# ---------------------------------------------------------------- 4. the rest
au = pd.read_csv(os.path.join(D, "competitiveness_autodoc_risk.csv"), dtype=str)
au["pn"] = au["part_number"].astype(str).str.strip()
cov_a = coverage("Autodoc extract (brand names only, prices corrupt)",
                 au["pn"].unique(), "277 of 298 rows carry the identical value 2.34",
                 "none usable")
say(f"  Autodoc extract             : {au['pn'].nunique():>5} PNs  "
    f"EUR {cov_a:>12,.0f}  {100*cov_a/BOOK_EUR:.1f}% of book")

wl = pd.read_csv(os.path.join(D, "price_collection_worklist.csv"), dtype={"pn": str})
wl["pn"] = wl["pn"].str.strip()
cov_w = coverage("The worklist (rival named, price not held)",
                 wl["pn"].unique(), "the 139 to go and price", "none yet")
say(f"  Worklist                    : {wl['pn'].nunique():>5} PNs  "
    f"EUR {cov_w:>12,.0f}  {100*cov_w/BOOK_EUR:.1f}% of book")

# ---------------------------------------------------------------- union
union_all = set(ks["pn"]) | set(g["pn"]) | set(au["pn"])
if len(x):
    union_all |= set(x["pn"])
cov_ua = coverage("UNION of every competitor source on disk", union_all,
                  "includes sources whose price is unusable", "mixed tiers, never blended")

# the union that actually carries a PRICE - the number that matters
priced_union = set(ks["pn"]) | set(g["pn"])
if len(x):
    priced_union |= set(x["pn"])
cov_up = coverage("UNION of sources that carry a USABLE price", priced_union,
                  "KS trade GBP + Eucon/PartsPool online IAM EUR", "two real tiers")

say()
say("=" * 86)
say("THE HONEST TOTAL")
say("=" * 86)
say(f"  part numbers with ANY competitor record on disk  : "
    f"{len(union_all & set(pr['pn'])):,}   EUR {cov_ua:,.0f}   "
    f"{100*cov_ua/BOOK_EUR:.1f}% of book")
say(f"  part numbers with a USABLE COMPETITOR PRICE      : "
    f"{len(priced_union & set(pr['pn'])):,}   EUR {cov_up:,.0f}   "
    f"{100*cov_up/BOOK_EUR:.1f}% of book")
say()
say("  Read the second line, not the first. The Autodoc extract covers 298 part")
say("  numbers and 57.0% of the book by value but its PRICE COLUMN IS UNUSABLE")
say("  (277 of 298 rows carry the identical 2.34). Counting it in a coverage")
say("  figure would overstate what we can price by a factor of about four.")
say()

# ---------------------------------------------------------------- overlap
say("=" * 86)
say("HOW THE SOURCES OVERLAP")
say("=" * 86)
sets = {"KS panel": set(ks["pn"]), "Eucon crossref": set(x["pn"]) if len(x) else set(),
        "Eucon gap": set(g["pn"]), "Autodoc": set(au["pn"])}
names = list(sets)
say(f"  {'':<18}" + "".join(f"{n:>16}" for n in names))
for a in names:
    line = f"  {a:<18}"
    for b in names:
        line += f"{len(sets[a] & sets[b]):>16}"
    say(line)
say()
say(f"  in the Eucon crossref but NOT in the KS panel  : {len(sets['Eucon crossref'] - sets['KS panel'])}")
say(f"  in the KS panel but NOT in the Eucon crossref  : {len(sets['KS panel'] - sets['Eucon crossref'])}")

out = pd.DataFrame(rows)
out.to_csv(os.path.join(D, "competitor_coverage_truth.csv"), index=False)
meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "book": {"billed_eur": float(BOOK_EUR), "part_numbers": int(BOOK_PNS)},
    "union_with_any_record": {
        "part_numbers": int(len(union_all & set(pr["pn"]))),
        "billed_eur": float(cov_ua),
        "pct_of_book_eur": float(100 * cov_ua / BOOK_EUR),
    },
    "union_with_usable_price": {
        "part_numbers": int(len(priced_union & set(pr["pn"]))),
        "billed_eur": float(cov_up),
        "pct_of_book_eur": float(100 * cov_up / BOOK_EUR),
    },
    "sources": rows,
    "correction": [
        "The pricing paper described the competitor panel as 43 part numbers from one "
        "source, 16.5% of the book. That is the KS panel alone.",
        "eucon_crossref_iam_20260329.csv holds a part-number-level cross-reference to "
        "432 IAM part numbers and 155 brands with a real price on all 822 rows, and had "
        "never been joined. It is a richer base than the panel the paper was built on.",
        "The union with a USABLE PRICE is the number that matters. The larger union that "
        "includes the Autodoc extract must not be quoted as coverage, because that "
        "source has no usable price.",
    ],
    "caveats": [
        "Price tiers differ and must never be blended: KS is GBP trade ex-VAT; "
        "Eucon/PartsPool is online IAM EUR in DE/NO. Both differ from the reference "
        "dealer price we compare against.",
        "The Eucon crossref covers DE and NO only.",
        "TecAlliance sells both the cross-reference (OE Parts Data) and the prices "
        "(OE Prices / IAM Prices) as licensed products. Whether the price module returns "
        "a competing retail price directly is unverified and needs a vendor demo.",
    ],
}
with open(os.path.join(D, "competitor_coverage_truth_meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say()
say("BUILD_OK")
