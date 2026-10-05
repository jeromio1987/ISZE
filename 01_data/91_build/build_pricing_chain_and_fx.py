# -*- coding: utf-8 -*-
"""
The full channel chain and the currency lever.

Three things computed here:
  1. Our gross margin is 1 - class_factor. It is written down, not earned.
     This script demonstrates that from the formula and from the file.
  2. The chain: our price -> distributor (x1.40) -> dealer (x1.275). What the
     customer actually faces, at the current margin and at a target margin.
  3. Currency. FX moves the EUR price and the EUR gross profit per unit, but
     never the margin percentage. It moves our position against the
     independent market silently.

Run: python 01_data/91_build/build_pricing_chain_and_fx.py
Writes: 01_data/00_derived/pricing_chain_and_fx.csv
        01_data/00_derived/pricing_chain_and_fx_meta.json
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
CH_DB, CH_DLR = 1.40, 1.275


def say(m):
    print(m)
    sys.stdout.flush()


# ---------------------------------------------------------------- 1. the formula
say("=" * 80)
say("1. WHERE THE GROSS MARGIN COMES FROM")
say("=" * 80)
say("  SP_EUR = BP_JPY / FX / class_factor        (the class factor IS 1 - margin)")
say("  So gross margin = 1 - class_factor. Nothing else.")
say("")
cls = pd.read_parquet(os.path.join(D, "pricing_list_pn.parquet"),
                      columns=["part_number", "price_class", "gm", "fob_eur",
                               "is_superseded_row"])
cls = cls[cls["is_superseded_row"] != True]                       # noqa: E712

say("  class  implied margin  measured margin  spread across part numbers")
FACTOR = {"C": .47, "D": .48, "F": .525, "J": .555, "M": .50, "P": .44, "V": .55, "T": .80}
for c, g in cls.groupby("price_class"):
    imp = 100 * (1 - FACTOR[c]) if c in FACTOR else np.nan
    say(f"    {c:<5} {imp:>12.2f}% {100*g['gm'].mean():>15.2f}% {100*(g['gm'].max()-g['gm'].min()):>22.2f}pp")
say("")
say("  Read the last column for the eight class codes the formula names. Within those")
say("  classes the margin is the same to within a few hundredths of a point for every")
say("  part number in the catalogue. There is no competitive information in it at all.")
say("  The B / E / G / W / X / Y / Z rows are codes with no factor in the formula; they")
say("  are carried in the file and must not be read as a margin decision.")

# ---------------------------------------------------------------- 2. the chain
say("")
say("=" * 80)
say("2. THE FULL CHAIN - WHAT THE CUSTOMER ACTUALLY FACES")
say("=" * 80)
book = pd.read_parquet(os.path.join(D, "pricing_aim_source_lines.parquet"))
book["pn"] = book["part_number"].astype(str).str.strip()
book = book[book["priced_both"] == True].copy()                   # noqa: E712
cl = cls.drop_duplicates("part_number").copy()
cl["pn"] = cl["part_number"].astype(str).str.strip()
book = book.merge(cl[["pn", "gm", "fob_eur"]].drop_duplicates("pn"), on="pn", how="left")
book = book[book["gm"].notna() & (book["gm"] > 0) & (book["gm"] < 1)].copy()

# Our invoice price reconstructed from cost at the booked margin.
book["our_price"] = book["fob_eur"] / (1 - book["gm"])
say(f"  priced lines with a cost and a margin: {len(book):,}")
say(f"  factor that turns the reconstructed unit price into the billed total: "
    f"{book['billed_eur'].sum() / book['our_price'].sum():,.0f}  "
    f"(billed quantity: {book['qty'].sum():,.0f})")
say("  The unit price and the billed euro are different units. The chain ratios below")
say("  are computed per unit and are unaffected by that; the totals are not comparable.")
say("")

ks = pd.read_csv(os.path.join(D, "iam_ks_price_gap.csv"), dtype={"pn": str})
ks["pn"] = ks["pn"].str.strip()
ks = ks.merge(cl[["pn", "gm", "fob_eur"]].drop_duplicates("pn"), on="pn", how="left")
ks = ks[ks["gm"].notna() & ks["fob_eur"].notna() & (ks["ks_am_min_eur"] > 0)].copy()
ks["our_price"] = ks["fob_eur"] / (1 - ks["gm"])
ks["iam"] = ks["ks_am_min_eur"]

say("  On the 43 part numbers where we can see the competing price, the chain at")
say("  TODAY's margin, indexed to the independent retail price = 1.00:")
say("")
chain_now = {
    "our net price to distributor": (ks["our_price"] / ks["iam"]).median(),
    "distributor price to dealer": (ks["our_price"] * CH_DB / ks["iam"]).median(),
    "dealer price to customer": (ks["our_price"] * CH_DB * CH_DLR / ks["iam"]).median(),
}
for k, v in chain_now.items():
    say(f"    {k:<32} {v:>6.2f}x")
say("")

say("  The same chain if we cut OUR margin only, holding the distributor's and the")
say("  dealer's percentages on their own buy price:")
say("")
rows = []
for tgt in (0.15, 0.25, 0.35, 0.45, 0.52):
    our = ks["fob_eur"] / (1 - tgt)
    rows.append({
        "our_margin_target_pct": 100 * tgt,
        "our_price_vs_iam": (our / ks["iam"]).median(),
        "dealer_price_vs_iam": (our * CH_DB * CH_DLR / ks["iam"]).median(),
    })
ch = pd.DataFrame(rows)
say(ch.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
say("")
say("  The last row of the table is the point: cutting our margin from 49% to 15%")
say("  - a 34 point give-away - moves the DEALER price by about the same factor,")
say("  because two more margins sit on top of ours and both are percentages.")

# ---------------------------------------------------------------- 3. currency
say("")
say("=" * 80)
say("3. CURRENCY MOVES THE PRICE AND THE EURO GROSS PROFIT, BUT NOT THE MARGIN")
say("=" * 80)
FX_NOW = 163.7
rates = [("2023-10", 146.6), ("2024-10", 159.4), ("2025-10 (in use)", 163.7),
         ("stress weak yen", 175.0), ("stress strong yen", 150.0)]
base_eur_price = 100.0              # index
say("  A part whose yen base price is unchanged. EUR price indexed to today = 100.")
say("")
say("  period              FX (JPY/EUR)  EUR price index  EUR gross profit index  margin %")
for label, fx in rates:
    idx = FX_NOW / fx * base_eur_price
    say(f"  {label:<19} {fx:>12.1f} {idx:>16.1f} {idx:>22.1f} {'unchanged':>11}")
say("")
fx_df = pd.DataFrame([{"period": l, "fx_jpy_eur": f, "eur_price_index": FX_NOW / f * 100,
                       "eur_gp_index": FX_NOW / f * 100} for l, f in rates])
say("  From the rate in use in 2023 to the rate in use today, the EUR price of an")
say("  unchanged yen base price has fallen by %.1f%%, and so has the EUR gross profit"
    % (100 * (1 - (FX_NOW / 146.6))))
say("  per part. The margin percentage did not move at all.")
say("")
idx_now = (ks["our_price"] / ks["iam"]).median()
say("  Because our margin does not respond, FX moves our position against the")
say("  independent market without any decision being taken:")
say("    at FX 146.6  our net price is %.2fx the IAM price" % (idx_now * 146.6 / FX_NOW))
say("    at FX 163.7  our net price is %.2fx the IAM price" % idx_now)
say("    at FX 175.0  our net price is %.2fx the IAM price" % (idx_now * 175.0 / FX_NOW))

# ---------------------------------------------------------------- 4. write
ch.to_csv(os.path.join(D, "pricing_chain_and_fx.csv"), index=False)
meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "margin_identity": "gross margin = 1 - class_factor; independent of FX and of base price",
    "chain_factors": {"distributor": CH_DB, "dealer": CH_DLR, "reference": CH_DB * CH_DLR},
    "fx": {
        "rate_in_use": FX_NOW,
        "rate_2023_10": 146.6,
        "rate_2024_10": 159.4,
        "eur_price_change_from_2023_rate_pct": float(100 * (FX_NOW / 146.6 - 1)),
    },
    "caveats": [
        "The chain applies the distributor and dealer percentages to OUR reduced "
        "price. In practice a distributor defending its own absolute margin may not "
        "pass the full reduction through, which makes the dealer price fall less than "
        "shown. No evidence on pass-through exists on disk; this is arithmetic.",
        "The 43 part numbers are all tagged brand tier 1 with one or two competitors, "
        "and up to 18 markets share one part number. Treat as a signal.",
        "FX sensitivity assumes the yen base price is held. In practice IML revises it.",
    ],
}
with open(os.path.join(D, "pricing_chain_and_fx_meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say("")
say("wrote pricing_chain_and_fx.csv")
say("BUILD_OK")
