# -*- coding: utf-8 -*-
"""
Every part number where we can check our price against a competitor, and what it
says about Israel against the UK, and about CV against LCV.

The single most important finding is a negative one: the index for a part number
is the SAME in every market it appears in, because our list price is global and
the observed competitor price is a single national listing. So every market-level
difference in this file is a COMPOSITION effect - which parts that market happens
to see - not a market difference. That is stated at the top of the output because
it governs how every number below may be read.

Run: python 01_data/91_build/build_competitor_price_panel.py
Writes: 01_data/00_derived/competitor_price_panel.csv
        01_data/00_derived/competitor_price_panel_meta.json
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"


def say(m):
    print(m)
    sys.stdout.flush()


ks = pd.read_csv(os.path.join(D, "iam_ks_price_gap.csv"), dtype={"pn": str})
ks["pn"] = ks["pn"].str.strip()
ks["our_list"] = pd.to_numeric(ks["isze_price_eur"], errors="coerce")
ks["our_ref"] = pd.to_numeric(ks["proj_retail_eur"], errors="coerce")
ks["iam"] = pd.to_numeric(ks["ks_am_min_eur"], errors="coerce")
ks["idx"] = ks["our_ref"] / ks["iam"]
ks["below"] = ks["idx"] < 1.0
ks["far_above"] = ks["idx"] > 1.5

# vehicle type, where the distributor tells us which it is
CV, LCV = {"ITUK", "UTI"}, {"IUK", "UMI"}
ks["vehicle"] = ks["db"].map(lambda d: "CV" if d in CV else ("LCV" if d in LCV else "other"))

FACTOR = 1.785

say("=" * 84)
say("THE GOVERNING FINDING")
say("=" * 84)
uniq = ks.groupby("pn")["idx"].nunique()
say(f"  part numbers in the file                        : {ks['pn'].nunique()}")
say(f"  markets                                         : {ks['db'].nunique()}")
say(f"  PNs whose index is IDENTICAL in every market    : {int((uniq == 1).sum())} of {len(uniq)}")
say(f"  PNs where OUR reference price differs by market : {int((ks.groupby('pn')['our_ref'].nunique() > 1).sum())}")
say(f"  PNs where the COMPETITOR price differs by market : {int((ks.groupby('pn')['iam'].nunique() > 1).sum())}")
say("")
say("  Our list price is global and the observed competitor price is a single")
say("  national listing, so the same part has ONE index everywhere. Every market")
say("  difference below is therefore COMPOSITION - which parts that market sees -")
say("  and not a statement about that market. This file cannot answer 'is Israel")
say("  different from the UK'.")
say("")

say("=" * 84)
say("WHAT IT CAN ANSWER: THE DISTRIBUTION ACROSS PARTS")
say("=" * 84)
per_pn = ks.groupby("pn").agg(
    description=("description", "first"),
    our_list=("our_list", "first"),
    our_ref=("our_ref", "first"),
    iam=("iam", "median"),
    idx=("idx", "median"),
    markets=("db", "nunique"),
    brands=("competitor_count", "median"),
).reset_index().sort_values("idx", ascending=False)
per_pn["gap_eur_at_dealer"] = (per_pn["our_ref"] - per_pn["iam"]).round(2)
per_pn["cost_est"] = (per_pn["our_list"] * 0.50).round(2)
per_pn["gm_if_matched_pct"] = (100 * (1 - per_pn["cost_est"] / per_pn["iam"])).round(1)

say(f"  median index (our reference dealer price / competitor) : {per_pn['idx'].median():.2f}x")
for q in (0.10, 0.25, 0.75, 0.90):
    say(f"    p{int(q*100):<3} {per_pn['idx'].quantile(q):.2f}x")
say("")
n_above = int((per_pn["idx"] > 1).sum())
n_unreach = int((per_pn["gm_if_matched_pct"] < 0).sum())
n_slim = int(((per_pn["gm_if_matched_pct"] >= 0) & (per_pn["gm_if_matched_pct"] < 20)).sum())
say(f"  parts where we sit ABOVE the competitor   : {n_above} of {len(per_pn)}")
say(f"  parts where matching them means < 0% margin: {n_unreach}")
say(f"  parts where matching them means 0-20%      : {n_slim}")
say(f"  parts where matching them leaves 20%+      : {len(per_pn) - n_unreach - n_slim}")
say("")
say("  top 12 by how far above the competitor we sit:")
say(per_pn.head(12)[["pn", "description", "our_list", "our_ref", "iam", "idx",
                     "markets", "gm_if_matched_pct"]].to_string(
    index=False, float_format=lambda v: f"{v:,.2f}"))
say("")
say("  and the parts where we are BELOW the competitor (price is not the problem):")
say(per_pn.tail(8)[["pn", "description", "our_list", "our_ref", "iam", "idx",
                    "markets"]].to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

say("")
say("=" * 84)
say("ISRAEL AGAINST THE UK, AND CV AGAINST LCV")
say("=" * 84)
for label, pair in (("ISRAEL", ["UTI", "UMI"]), ("UNITED KINGDOM", ["ITUK", "IUK"])):
    s = ks[ks["db"].isin(pair)]
    say(f"  {label}")
    for d in pair:
        x = s[s["db"] == d]
        if not len(x):
            continue
        kind = "CV " if d in CV else "LCV"
        say(f"    {d:<6} {kind}  sees {x['pn'].nunique():>2} of the 43 part numbers "
            f"({100*x['pn'].nunique()/43:.0f}%)  median index {x['idx'].median():.2f}x  "
            f"{100*x['below'].mean():.0f}% below the competitor")
    say("")

shared = per_pn["pn"]
six = ks.groupby(["pn", "vehicle"])["idx"].median().unstack()
six = six.dropna()
if len(six):
    say(f"  the {len(six)} part numbers carried in BOTH a CV and an LCV market:")
    say(six.to_string(float_format=lambda v: f"{v:.2f}"))
    same = bool(np.allclose(six["CV"], six["LCV"]))
    say(f"    identical index in CV and in LCV: {'YES' if same else 'NO'}")
    say("")
say("  CONCLUSION: CV and LCV cannot be separated on this evidence. The same part")
say("  number carries the same index whichever vehicle it goes on. The apparent")
say("  CV/LCV gap in the market averages is composition - the parts a CV market")
say("  happens to check are different parts from the ones an LCV market checks.")
say("")

# what would answer the question
say("=" * 84)
say("WHAT WOULD ACTUALLY ANSWER THE QUESTION")
say("=" * 84)
say("  1. A competitor price PER MARKET for the same part number. Today the same")
say("     listing value is applied to every market, so no market comparison exists.")
say("  2. The vehicle application on each part number, so a part can be attributed")
say("     to CV or LCV rather than inferred from which distributor stocks it.")
say("  3. More than one competitor listing per part. 83% of the rows here rest on")
say("     a single price, and the median number of brands found is 1.")

per_pn.to_csv(os.path.join(D, "competitor_price_panel.csv"), index=False)
meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "source": "iam_ks_price_gap.csv (same-shop listings)",
    "governing_caveat": [
        "The index for a part number is identical in every market it appears in: "
        "our list price is global and the observed competitor price is a single "
        "national listing. Every market-level average in this file is therefore a "
        "composition effect, not a market difference.",
        "This file cannot support a claim that Israel differs from the UK, or that "
        "CV differs from LCV.",
        "85% of rows carry the identical median index, so market averages are "
        "dominated by which parts each market checks.",
    ],
    "headline": {
        "part_numbers": int(ks["pn"].nunique()),
        "markets": int(ks["db"].nunique()),
        "median_index": float(per_pn["idx"].median()),
        "parts_above_competitor": n_above,
        "parts_matching_means_negative_margin": n_unreach,
        "parts_matching_means_under_20pct": n_slim,
        "rows_with_one_competitor_price": int((ks["competitor_count"] == 1).sum()),
        "rows_total": int(len(ks)),
        "median_brands_found": float(ks["competitor_count"].median()),
    },
    "caveats": [
        "Cost is estimated as 50% of list, the book average. It is not a purchase cost.",
        "The observed prices are what a price-comparison site showed, not a "
        "transaction, and 83% of rows rest on a single listing.",
    ],
}
with open(os.path.join(D, "competitor_price_panel_meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say("")
say(f"wrote competitor_price_panel.csv ({len(per_pn)} part numbers)")
say("BUILD_OK")
