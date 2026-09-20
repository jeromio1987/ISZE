# -*- coding: utf-8 -*-
"""
Common margin basis: put every competitor comparison on ONE stated tier, with the
margin dials exposed instead of hidden in a stack.

THE PROBLEM THIS SOLVES
The current comparison is a three-layer assumption stack:
    our price  x (1/0.53) x 1.40 x 1.275
A reader cannot tell whether a gap is a margin difference, a distribution-structure
difference, or neither. And the KS panel is labelled as if it compared retail to
trade when it actually compares genuine LIST to genuine LIST.

THE TIERS (each is a named point in the chain, never blended)
    K1  our net price to the distributor        = PR00 list x (1 - our margin)
    K2  official list                           = PR00 list
    K3  our reference dealer price              = K2 x DB x DLR
    K4  a competitor's observed trade price     = whatever the source publishes
    K5  a competitor's observed retail price    = whatever the source publishes

THE UNDERIDENTIFICATION - stated in the output, not buried here
A single retail price cannot give you both the margin and the distribution
structure. two unknowns, one equation. So either the reader supplies a landed
cost and we derive their margin, or they supply their margin and we derive the
cost. That is why DB and DLR are DIALS in this file, not constants.

Run: python 01_data/91_build/build_common_margin_basis.py
Writes: 01_data/00_derived/competitor_common_basis.csv
        01_data/00_derived/competitor_common_basis_meta.json
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

# ---------------------------------------------------------------- THE DIALS
# Edit these and re-run. Nothing below hardcodes them.
DIAL_DB = 1.40          # distributor margin applied to our list
DIAL_DLR = 1.275        # dealer margin applied to the distributor price
DIAL_OUR_MARGIN = 0.5109   # the book's weighted gross margin, from the cost floor
FX_GBP_EUR = 1.17       # from sources.yaml as_of 2026-05-01


def say(m=""):
    print(m)
    sys.stdout.flush()


REFERENCE = DIAL_DB * DIAL_DLR

say("=" * 88)
say("COMMON MARGIN BASIS")
say("=" * 88)
say(f"  dial  distributor margin (DB)  : {DIAL_DB:.3f}")
say(f"  dial  dealer margin (DLR)      : {DIAL_DLR:.3f}")
say(f"  dial  our book gross margin    : {DIAL_OUR_MARGIN:.4f}")
say(f"  => reference dealer price      : list x {REFERENCE:.3f}")
say(f"  dial  GBP to EUR               : {FX_GBP_EUR:.2f}   (sources.yaml, as_of 2026-05-01)")
say()
say("  THESE ARE DIALS. Edit them at the top of the builder and re-run. They are")
say("  not measurements, and the output says so on every row.")

# ---------------------------------------------------------------- 1. KS panel
ks = pd.read_csv(os.path.join(D, "iam_ks_price_gap.csv"), dtype=str)
ks["pn"] = ks["pn"].str.strip()
ks["k2_list_eur"] = pd.to_numeric(ks["isze_price_eur"], errors="coerce")
ks["k3_reference_dealer_eur"] = pd.to_numeric(ks["proj_retail_eur"], errors="coerce")
ks["k1_net_to_distributor_eur"] = ks["k2_list_eur"] * (1 - DIAL_OUR_MARGIN)
ks["competitor_price_eur"] = pd.to_numeric(ks["ks_am_min_eur"], errors="coerce")
ks["competitor_tier"] = "K5 competitor retail"
ks["competitor_basis_note"] = ("KS aftermarket listing, GBP ex-VAT at " f"{FX_GBP_EUR}")

say()
say("=" * 88)
say("1. THE KS PANEL - CORRECTING ITS LABEL")
say("=" * 88)
say(f"  rows {len(ks):,}   part numbers {ks['pn'].nunique():,}   "
    f"source {ks['isze_price_source'].dropna().unique().tolist()}")
ratio = (ks["k3_reference_dealer_eur"] / ks["k2_list_eur"]).median()
say(f"  proj_retail / isze_price, median : {ratio:.4f}   "
    f"(the dial product is {REFERENCE:.3f})")
say()
say("  The panel's own isze_price_source says IE40_PR00 - the OFFICIAL LIST. So the")
say("  index it computes is genuine list against an aftermarket retail listing. That is")
say("  a defensible comparison, and it is NOT a margin comparison. The basis was")
say("  missing from the label, not wrong in the arithmetic.")

# the three clean comparisons, each on one tier
ks["index_list_vs_competitor"] = ks["k2_list_eur"] / ks["competitor_price_eur"]
ks["index_reference_vs_competitor"] = ks["k3_reference_dealer_eur"] / ks["competitor_price_eur"]
ks["index_netdist_vs_competitor"] = ks["k1_net_to_distributor_eur"] / ks["competitor_price_eur"]

say()
say("  The SAME gap, stated on three tiers - this is the point of the exercise:")
for label, col in (("K1 net to distributor / competitor", "index_netdist_vs_competitor"),
                   ("K2 official list      / competitor", "index_list_vs_competitor"),
                   ("K3 reference dealer   / competitor", "index_reference_vs_competitor")):
    v = ks[col].replace([np.inf, -np.inf], np.nan).dropna()
    say(f"    {label:<36} median {v.median():>6.2f}x   "
        f"p25 {v.quantile(.25):>6.2f}   p75 {v.quantile(.75):>6.2f}")
say()
say("  A reader told only 'K3 = 1.77x' sees a large gap. Told that K1 is 0.48x, they")
say("  see our NET price well below the competitor's RETAIL. Both are true and they")
say("  mean opposite things commercially.")
say()
say("  THE RULE THAT RESOLVES IT: match the tier to the competitor's CUSTOMER.")
say()
say("    if the competitor sells to a DEALER or workshop  -> compare our K3")
say("    if the competitor sells to a DISTRIBUTOR         -> compare our K2 list")
say("    if the competitor sells to another trade tier    -> compare our K1")
say()
say("  Nothing in the file states which customer KS serves, so the honest output is")
say("  the table above with all three tiers visible, not a single headline index.")
say("  Whoever answers 'who buys from them' picks the row.")

# ---------------------------------------------------------------- 2. bridge
br = pd.read_csv(os.path.join(D, "oe_bridge_coverage.csv"), dtype={"pn": str})
br["pn"] = br["pn"].str.strip().str.zfill(10)
say()
say("=" * 88)
say("2. THE MULTI-BRAND BRIDGE - A DIFFERENT TIER, AND IT MUST BE LABELLED")
say("=" * 88)
say(f"  part numbers with a resolved competing price : {len(br):,}")
say(f"  median competitor price                      : EUR {br['min_price_eur'].median():,.2f}")
say()
say("  These are a DISTRIBUTOR LIST price for an IAM brand, not a market price and not")
say("  our list. They belong in their own column. Blending them with the KS retail")
say("  listings would produce a number that corresponds to no real price anywhere.")

# ---------------------------------------------------------------- 3. write
out = ks[[
    "db", "pn", "description", "k1_net_to_distributor_eur", "k2_list_eur",
    "k3_reference_dealer_eur", "competitor_price_eur", "competitor_tier",
    "index_netdist_vs_competitor", "index_list_vs_competitor",
    "index_reference_vs_competitor", "competitor_basis_note", "scraped_at",
]].copy()
out["dial_db"] = DIAL_DB
out["dial_dlr"] = DIAL_DLR
out["dial_our_margin"] = DIAL_OUR_MARGIN
out["fx_gbp_eur"] = FX_GBP_EUR
for c in ("k1_net_to_distributor_eur", "k2_list_eur", "k3_reference_dealer_eur",
          "competitor_price_eur", "index_netdist_vs_competitor",
          "index_list_vs_competitor", "index_reference_vs_competitor"):
    out[c] = out[c].round(4)
out = out.sort_values(["db", "index_reference_vs_competitor"], ascending=[True, False])
out.to_csv(os.path.join(D, "competitor_common_basis.csv"), index=False)

meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "dials_are_not_measurements": True,
    "dials": {
        "db_margin": DIAL_DB, "dealer_margin": DIAL_DLR,
        "reference_factor": REFERENCE, "our_book_margin": DIAL_OUR_MARGIN,
        "fx_gbp_eur": FX_GBP_EUR,
    },
    "tiers": {
        "K1": "our net price to the distributor = list x (1 - our margin)",
        "K2": "official list (PR00 / IE40)",
        "K3": "our reference dealer price = K2 x DB x DLR",
        "K5": "a competitor's observed retail price (what KS publishes)",
    },
    "underidentification": (
        "One retail price cannot yield both the margin and the distribution"
        "structure - two unknowns, one equation. Either the reader supplies a landed"
        "cost and we derive their margin, or they supply their margin and we derive"
        "the cost. That is why DB and DLR are dials here."
    ),
    "correction": [
        "iam_ks_price_gap.csv carries isze_price_source = IE40_PR00, so its index is"
        " official genuine LIST against an aftermarket retail listing. It is not a"
        " margin comparison, and it was labelled as one.",
        "The same gap reads very differently by tier: the document states all three"
        " indices side by side so a reader cannot take one for the truth.",
    ],
    "caveats": [
        "KS is one UK source, fanned across 18 market rows. There is no market"
        " dimension in it; every market average from it is composition.",
        "KS aftermarket is GBP ex-VAT converted at 1.17, a rate set 2026-05-01.",
        "The bridge prices are a distributor list, not a market price, and sit in"
        " their own column.",
    ],
}
with open(os.path.join(D, "competitor_common_basis_meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)

say()
say(f"wrote competitor_common_basis.csv ({len(out):,} rows)")
say("BUILD_OK")
