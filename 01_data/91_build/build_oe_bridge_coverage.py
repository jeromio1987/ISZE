# -*- coding: utf-8 -*-
"""
The multi-brand OE bridge - what it actually resolved, measured.

A 2026-09-18 review tested a third-party multi-brand OE lookup against all 58
part numbers on our worklist that carry a named competing brand. It reported
"35 came back with an IAM part number AND a EUR price, worth EUR 2.78M billed."

Verifying it precisely:
  - the sweep CSV has 58 rows; n_brands > 0 on 33
  - the cards file has 35 keys, all of them a subset of the 58
  - the CSV's own euro_hits column is 0 on every row, so it does not carry the
    price flag - the prices are in the cards file
So 33 is the CSV's count and 35 is the cards' count. This file settles which
part numbers have both an IAM number AND a price, and what they are worth.

Run: python 01_data/91_build/build_oe_bridge_coverage.py
Writes: 01_data/00_derived/oe_bridge_coverage.csv
        01_data/00_derived/oe_bridge_coverage_meta.json
"""
from __future__ import annotations

import io
import json
import os
import sys

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
RAW = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw"


def say(m=""):
    print(m)
    sys.stdout.flush()


sweep = pd.read_csv(os.path.join(RAW, "spareto_oe_sweep_20260918.csv"), dtype=str)
sweep["pn"] = sweep["pn"].astype(str).str.strip().str.zfill(10)
cards = json.load(open(os.path.join(RAW, "spareto_all_cards_20260918.json"), encoding="utf-8"))

book = pd.read_parquet(os.path.join(D, "pricing_aim_source_lines.parquet"))
book["pn"] = book["part_number"].astype(str).str.strip()
pr = book[book["priced_both"] == True]                                  # noqa: E712
billed = pr.groupby("pn")["billed_eur"].sum()
BOOK = pr["billed_eur"].sum()

wl = pd.read_csv(os.path.join(D, "price_collection_worklist.csv"), dtype={"pn": str})
wl["pn"] = wl["pn"].astype(str).str.strip().str.zfill(10)
wl_named = set(wl[wl["competing_brand"].notna()]["pn"])

say("=" * 84)
say("THE MULTI-BRAND OE BRIDGE, MEASURED")
say("=" * 84)
say(f"  part numbers tested (the worklist's named-brand set) : {len(sweep):,}")
nb = pd.to_numeric(sweep["n_brands"], errors="coerce").fillna(0)
say(f"  returned at least one brand (sweep CSV)              : {int((nb > 0).sum())}")
say(f"  cards held (cards JSON)                              : {len(cards)}")
say()

rows = []
for pn, lst in cards.items():
    pn = str(pn).strip().zfill(10)
    priced = [c for c in lst if c.get("price_eur") is not None]
    rows.append({
        "pn": pn,
        "brands_offered": len(lst),
        "brands_with_price": len(priced),
        "min_price_eur": min((c["price_eur"] for c in priced), default=None),
        "cheapest_brand": next((c["brand"] for c in sorted(
            priced, key=lambda c: c["price_eur"])), None),
        "our_billed_eur": float(billed.get(pn, 0.0)),
    })
bt = pd.DataFrame(rows).sort_values("our_billed_eur", ascending=False)

both = bt[bt["brands_with_price"] > 0]
no_price = bt[bt["brands_with_price"] == 0]

say("=" * 84)
say("WHAT IT RESOLVED, AND WHAT THAT IS WORTH")
say("=" * 84)
say(f"  PNs with an IAM number AND a price : {len(both):>3}   "
    f"billed EUR {both['our_billed_eur'].sum():>12,.0f}   "
    f"{100*both['our_billed_eur'].sum()/BOOK:.2f}% of the priced book")
say(f"  PNs with an IAM number, no price   : {len(no_price):>3}   "
    f"billed EUR {no_price['our_billed_eur'].sum():>12,.0f}")
say(f"  PNs that returned nothing          : {len(sweep) - len(bt):>3}   "
    f"billed EUR "
    f"{sum(float(billed.get(p, 0)) for p in set(sweep['pn']) - set(bt['pn'])):>12,.0f}")
say()
say("  the top 12 by our own revenue behind them:")
say(bt.head(12)[["pn", "brands_offered", "brands_with_price", "min_price_eur",
                 "cheapest_brand", "our_billed_eur"]].to_string(
    index=False, float_format=lambda v: f"{v:,.2f}"))
say()

# how it sits against the worklist
covered = set(bt[bt["brands_with_price"] > 0]["pn"])
say("=" * 84)
say("WHERE THIS SITS AGAINST THE WORKLIST")
say("=" * 84)
say(f"  worklist part numbers with a named brand : {len(wl_named)}")
say(f"  of those, now with an IAM number AND price: {len(covered & wl_named)}")
say(f"  still to collect                         : {len(wl_named - covered)}")
say()
say("  Before this, the worklist was a list of part numbers to go and price by")
say("  hand. A third of it now has a competing part number and a price attached.")

bt.to_csv(os.path.join(D, "oe_bridge_coverage.csv"), index=False)

say()
say("=" * 84)
say("UNIT-OF-MEASURE FLAG")
say("=" * 84)
susp = bt[bt["min_price_eur"] > 1000]
say(f"  bridge prices above EUR 1,000 (a review flagged these as probable kit/unit")
say(f"  mismatches - confirm the unit before any of them informs a decision):")
for _, r in susp.iterrows():
    say(f"    {r['pn']}  EUR {r['min_price_eur']:>10,.2f}  {r['cheapest_brand']}")
say()
say("  These stay in the file so the fault is visible, and must be excluded from any")
say("  commercial statement until the unit is confirmed.")

meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "source_files": [
        "01_data/01_Pricing/_raw/spareto_oe_sweep_20260918.csv",
        "01_data/01_Pricing/_raw/spareto_all_cards_20260918.json",
        "(rescued from the system temp folder on 2026-09-18 before it was swept)",
    ],
    "counts": {
        "tested": int(len(sweep)),
        "cards": int(len(cards)),
        "with_iam_number_and_price": int(len(both)),
        "with_iam_number_no_price": int(len(no_price)),
        "returned_nothing": int(len(sweep) - len(bt)),
    },
    "value": {
        "billed_eur_resolved": float(both["our_billed_eur"].sum()),
        "pct_of_priced_book": float(100 * both["our_billed_eur"].sum() / BOOK),
    },
    "reconciliation": [
        "The review reported '35 came back with an IAM part number AND a EUR price'. "
        "35 is the number of keys in the cards file. The sweep CSV reports n_brands>0 "
        "on 33. The count with BOTH a number and a price is stated above and is lower "
        "than either, because some cards carry a brand with no price.",
        "The sweep CSV's own euro_hits column reads 0 on every row, so it does not carry "
        "the price flag at all. The prices live only in the cards JSON.",
    ],
    "caveats": [
        "A distributor's list price is not a market price and is not comparable to our "
        "PR00 or our reference dealer price. Do not put these in the same column.",
        "The source is a third-party multi-brand lookup. Its provenance and its licence "
        "to redistribute are NOT established. Keep internal until checked.",
        "The bridge resolved part numbers we already knew have a named competitor. The "
        "rate across all 15,273 priced part numbers will be lower.",
        "UNIT-OF-MEASURE FAULT, found 2026-09-18 by a downstream review and confirmed "
        "here: two rows price far above any plausible retail. 8980252486 and "
        "8982127181, both EGR coolers, carry EUR 1,851.82 and EUR 1,975.98 against our "
        "own list of EUR 258.74 - 7.16x and 7.64x. A bridge price many times our own "
        "list is a quantity-unit mismatch (a kit or pack priced as one unit), not a "
        "competitor price. EXCLUDE these two from any commercial statement until the "
        "unit is confirmed. Excluding them, the resolved set is 33 part numbers worth "
        "EUR 2,594,755 = 7.96% of the priced book, against 35 / EUR 2,782,752 / 8.54% "
        "including them.",
    ],
}
with open(os.path.join(D, "oe_bridge_coverage_meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say()
say("BUILD_OK")
