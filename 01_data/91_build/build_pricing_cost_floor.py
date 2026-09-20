# -*- coding: utf-8 -*-
"""
Cost floor and margin consequence, on the in-scope price-revision book.

Three questions, all answered from files on disk:
  1. What gross margin does the book actually earn, by AIM family?
  2. Where we can see the competing price, what margin would we need to MATCH it?
  3. What does a margin-differentiated policy do to gross profit and to price?

Cost is taken as the ISZE landed cost (FOB EUR) implied by the class factor,
which is the only cost basis on disk. It is NOT a true purchase cost.

Run: python 01_data/91_build/build_pricing_cost_floor.py
Writes: 01_data/00_derived/pricing_cost_floor_by_family.csv
        01_data/00_derived/pricing_cost_floor_reach.csv
        01_data/00_derived/pricing_cost_floor_meta.json
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


# ---------------------------------------------------------------- 1. line book
say("Loading the in-scope priced book ...")
d = pd.read_parquet(os.path.join(D, "pricing_aim_source_lines.parquet"))
d["pn"] = d["part_number"].astype(str).str.strip()
d = d[d["priced_both"] == True].copy()                       # noqa: E712

cls = pd.read_parquet(os.path.join(D, "pricing_list_pn.parquet"),
                      columns=["part_number", "price_class", "gm", "fob_eur", "sp_eur",
                               "is_superseded_row"])
cls = cls[cls["is_superseded_row"] != True].drop_duplicates("part_number")   # noqa: E712
cls["pn"] = cls["part_number"].astype(str).str.strip()

book = d.merge(cls[["pn", "gm", "fob_eur", "sp_eur", "price_class"]], on="pn", how="left",
               suffixes=("", "_list"))
withgm = book[book["gm"].notna() & (book["gm"] > 0) & (book["gm"] < 1)].copy()
withgm["gp"] = withgm["billed_eur"] * withgm["gm"]
say(f"  priced lines: {len(book):,}  |  with a usable margin: {len(withgm):,} "
    f"({100*len(withgm)/len(book):.1f}%)")
say(f"  billed euro with margin: EUR {withgm['billed_eur'].sum():,.0f}")
say(f"  weighted gross margin  : {100*withgm['gp'].sum()/withgm['billed_eur'].sum():.2f}%")


def fam(g):
    b = g["billed_eur"].sum()
    return pd.Series({
        "part_numbers": g["pn"].nunique(),
        "billed_eur": b,
        "weighted_gm_pct": 100 * g["gp"].sum() / b if b else np.nan,
        "gross_profit_eur": g["gp"].sum(),
        "median_gm_pct": 100 * g["gm"].median(),
        "gm_spread_pp": 100 * (g["gm"].quantile(.9) - g["gm"].quantile(.1)),
    })


say("")
say("=" * 80)
say("1. WHAT THE BOOK EARNS TODAY, BY AIM FAMILY")
say("=" * 80)
byfam = withgm.groupby("aim_l1").apply(fam, include_groups=False)
byfam = byfam.sort_values("billed_eur", ascending=False)
say(byfam.to_string(float_format=lambda v: f"{v:,.2f}"))
say("")
say("  Read the spread column. A flat class-factor mechanism still produces a spread "
    "because the factors differ by letter.")
say("")

byclass = withgm.groupby("price_class_list").apply(fam, include_groups=False)
say("--- the same, by price class (the mechanism) ---")
say(byclass.sort_values("billed_eur", ascending=False).to_string(float_format=lambda v: f"{v:,.2f}"))

# ---------------------------------------------------------------- 2. reach
say("")
say("=" * 80)
say("2. CAN A MARGIN TARGET REACH THE COMPETING PRICE?")
say("=" * 80)
ks = pd.read_csv(os.path.join(D, "iam_ks_price_gap.csv"), dtype={"pn": str})
ks["pn"] = ks["pn"].str.strip()
ks = ks.merge(cls[["pn", "gm", "fob_eur"]], on="pn", how="left")
ks = ks[ks["gm"].notna() & ks["fob_eur"].notna() & (ks["ks_am_min_eur"] > 0)].copy()

# Our price at a given margin, holding cost fixed: SP = cost / (1 - gm)
ks["gm_to_match_iam"] = 1 - ks["fob_eur"] / ks["ks_am_min_eur"]
ks["idx_retail_vs_iam"] = ks["proj_retail_eur"] / ks["ks_am_min_eur"]

per_pn = ks.groupby("pn").agg(
    description=("description", "first"),
    gm_today=("gm", "first"),
    pr00=("isze_price_eur", "first"),
    cost_fob=("fob_eur", "first"),
    iam=("ks_am_min_eur", "median"),
    gm_to_match=("gm_to_match_iam", "median"),
    idx=("idx_retail_vs_iam", "median"),
).reset_index()

unreachable = per_pn[per_pn["gm_to_match"] < 0]
thin = per_pn[(per_pn["gm_to_match"] >= 0) & (per_pn["gm_to_match"] < 0.20)]
workable = per_pn[per_pn["gm_to_match"] >= 0.20]

say(f"  part numbers where we can see the competing price: {len(per_pn)}")
say(f"    cost already ABOVE the competing retail price : {len(unreachable):>3}  "
    f"(no margin reaches it)")
say(f"    reachable only at under 20% margin           : {len(thin):>3}  "
    f"(thin, and inside the dealer's own margin)")
say(f"    reachable at 20% margin or better            : {len(workable):>3}")
say("")
say(f"  median margin needed to MATCH the competing price : {100*per_pn['gm_to_match'].median():.0f}%")
say(f"  median margin we hold today                       : {100*per_pn['gm_today'].median():.0f}%")
say(f"  median ratio, our reference dealer price / IAM    : {per_pn['idx'].median():.2f}x")


def price_at(gm_target):
    """Median competing-price multiple implied by a uniform margin target."""
    sp = per_pn["cost_fob"] / (1 - gm_target)
    return (sp / per_pn["iam"]).median()


say("")
say("  Price implied by a margin target, as a multiple of the competing price:")
for t in (0.15, 0.20, 0.30, 0.40, 0.50):
    say(f"    at {100*t:>3.0f}% margin -> {price_at(t):.2f}x the competing price")

# ---------------------------------------------------------------- 3. scenario
say("")
say("=" * 80)
say("3. WHAT A MARGIN-DIFFERENTIATED POLICY DOES TO GROSS PROFIT")
say("=" * 80)


def scenario(label, target_fn):
    """target_fn(aim_l1) -> margin target or None to leave the line alone."""
    g = withgm.copy()
    tgt = g["aim_l1"].map(target_fn)
    moved = tgt.notna()
    gm_new = np.where(moved, tgt, g["gm"])
    # price ratio holding cost fixed: SP = cost/(1-gm), cost = billed*(1-gm_today)
    cost = g["billed_eur"] * (1 - g["gm"])
    price_old = g["billed_eur"]
    price_new = np.where(moved, cost / (1 - np.clip(gm_new, 0.01, 0.95)), price_old)
    gp_old = g["gp"].sum()
    gp_new = (cost / (1 - np.clip(gm_new, 0.01, 0.95)) * np.clip(gm_new, 0.01, 0.95)).sum()
    return {
        "scenario": label,
        "lines_moved": int(moved.sum()),
        "price_index": price_new.sum() / price_old.sum(),
        "gm_before_pct": 100 * gp_old / price_old.sum(),
        "gm_after_pct": 100 * gp_new / price_new.sum(),
        "gp_before_eur": gp_old,
        "gp_after_eur": gp_new,
        "gp_delta_eur": gp_new - gp_old,
    }


scen = []
scen.append(scenario("Jerome: brakes 15%, sensors/emissions 65%",
                     lambda f: 0.15 if f == "Brakes"
                     else 0.65 if f == "Intake Exhaust Emission" else None))
scen.append(scenario("Brakes 25%, emissions 60%",
                     lambda f: 0.25 if f == "Brakes"
                     else 0.60 if f == "Intake Exhaust Emission" else None))
scen.append(scenario("Whole competitive book to 30%, rest unchanged",
                     lambda f: 0.30 if f in ("Brakes", "Maintenance Service", "Fuel System",
                                             "Steering", "Wheels Hub") else None))
scen.append(scenario("Whole book to 40%", lambda f: 0.40))
scen.append(scenario("Whole book to 50%", lambda f: 0.50))
sc = pd.DataFrame(scen)
say(sc.to_string(index=False, float_format=lambda v: f"{v:,.3f}"))
say("")
say("  price_index = the change in the book's total price level across moved lines.")
say("  A target BELOW the margin we hold cuts price; ABOVE raises it.")

# ---------------------------------------------------------------- 4. write
byfam.to_csv(os.path.join(D, "pricing_cost_floor_by_family.csv"))
per_pn.to_csv(os.path.join(D, "pricing_cost_floor_reach.csv"), index=False)

meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "basis": {
        "lines": "pricing_aim_source_lines.parquet, priced_both == True",
        "margin": "pricing_list_pn.gm (class-implied), superseded rows dropped",
        "cost": "fob_eur from pricing_list_pn — the class-implied landed cost, NOT a purchase cost",
        "competitor": "iam_ks_price_gap.csv, median across distributors, same-shop listings",
    },
    "headline": {
        "priced_lines": int(len(book)),
        "lines_with_margin": int(len(withgm)),
        "billed_eur_with_margin": float(withgm["billed_eur"].sum()),
        "weighted_gm_pct": float(100 * withgm["gp"].sum() / withgm["billed_eur"].sum()),
        "gross_profit_eur": float(withgm["gp"].sum()),
    },
    "reach": {
        "part_numbers_visible": int(len(per_pn)),
        "cost_above_competing_retail": int(len(unreachable)),
        "reachable_under_20pct_margin": int(len(thin)),
        "reachable_at_20pct_or_better": int(len(workable)),
        "median_gm_to_match_pct": float(100 * per_pn["gm_to_match"].median()),
        "median_gm_today_pct": float(100 * per_pn["gm_today"].median()),
    },
    "caveats": [
        "Cost is the class-implied landed cost from the class factor, not a purchase price. "
        "Where the class factor is generous the 'cost' is understated and the headroom "
        "overstated; where it is aggressive the reverse. The direction of the error is not "
        "known per part.",
        "The reach analysis rests on 43 part numbers across up to 18 markets, all tagged "
        "brand tier 1 with one or two competitors. It is a signal, not a measurement of "
        "the book.",
        "The Autodoc risk file (298 part numbers) was NOT used: its price column carries the "
        "identical value 2.34 on 277 of 298 rows and is not usable as a competitor price.",
        "The scenario table holds cost fixed and ignores supersession, mix and volume "
        "response. It prices the arithmetic of a margin target, not its consequence.",
    ],
}
with open(os.path.join(D, "pricing_cost_floor_meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)

say("")
say(f"wrote {len(byfam)} family rows, {len(per_pn)} reach rows")
say("BUILD_OK")
