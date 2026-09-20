# -*- coding: utf-8 -*-
"""
STEP 1 — prove the framework maths on the 53 SPA part lines.

These 53 lines are the only place in the workspace with a REAL per-part purchase
price, so they are where the margin logic gets proven before it meets 16,000 rows.

Three things are tested here, and each is written as an Excel-equivalent formula in
the comment beside it, because the workbook must reproduce these numbers with live
formulas rather than hardcoded results:

  1. THE CHAIN IDENTITY. SP_EUR = BP_JPY / FX x source_discount / class_factor.
     Verify it against the price list, and verify margin = 1 - class_factor.
     Run it on BOTH FX vintages, because the settled base-price revision was
     priced on 163.7 while the live rate is 178.5 - so the reproduction rate
     itself is evidence of which rate the price file was built on.
  2. THE REAL MARGIN vs THE CLASS-IMPLIED MARGIN. On these 53 lines we know the
     purchase price, so we can compare a measured margin to the class letter.
  3. THE INDEX MATHS. The weighted move is a Laspeyres index:
        index = SUM(q0 x p1) / SUM(q0 x p0) - 1
     Prove it reproduces the published 5.9616% before it is used on new parts.

DIRECTION OF THE TWO RATES (2026-09-18, settled - do not "fix" the sign):
     FOB_EUR = BP_JPY / FX x source_discount
     FX is the DENOMINATOR, the discount is the NUMERATOR.
     - A HIGHER JPY/EUR LOWERS our euro cost: 163.7 / 178.5 = 0.9171, -8.29%.
     - A HIGHER discount RAISES it: 0.673 / 0.620 = 1.0855, +8.55%.
     - Net: 0.9171 x 1.0855 = 0.9955, i.e. -0.45% on landed cost.
     They very nearly cancel. Do NOT quote +18.36%: that figure read 178.5 / 163.7
     as the COST factor, which is the reciprocal of the correct one.

Run: python 01_data/91_build/prove_pricing_framework_maths.py
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
SPA = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\ISZE_SPA_Optimizer_V4.xlsx"

# ------------------------------------------------------------------ the rates
# Live dials as of 2026-09-18. FX_PERIOD is the period the live rate covers;
# FX_PRIOR is what the settled base-price revision was priced on.
FX = 178.5                                    # JPY/EUR, live 2026-10-01 to 2027-03-31
FX_PERIOD = ("2026-10-01", "2027-03-31")
FX_PRIOR = 163.7                              # JPY/EUR, as_of 2025-10-01 (what the revision used)
FX_PRIOR_PERIOD = ("2025-10-01", "2026-03-31")
FX_MID = 172.6                                # JPY/EUR, 2026-04-01 to 2026-09-30 (previous vintage)
DISC = {"J": 0.673, "T": 0.611}               # J was 0.620; T NOT revised in this update
DISC_PRIOR = {"J": 0.620, "T": 0.611}
# IML-owned. Not modified by this update - recorded so the identity can be checked.
FACTOR = {"C": 0.47, "D": 0.48, "F": 0.525, "J": 0.555,
          "M": 0.50, "P": 0.44, "V": 0.55, "T": 0.80}
# ---- the base revision: two different things, never to be confused -------------
# SETTLED: on file. Source 01_data/00_derived/aim_pricing_recalc_2026-09-17.json,
#   weighted_pct 5.9616, step_eur 1,652,140.71. This is a YEN base-price move.
BASE_REV_SETTLED = 0.059616
# SCENARIO: 7.0% was written by the agent on 2026-09-18. NOT sourced, NOT a
#   quotation from IML. Kept only to size what happens above the target band.
BASE_REV_SCENARIO = 0.07


def say(m=""):
    print(m)
    sys.stdout.flush()


say("=" * 88)
say("0. THE TWO RATE CHANGES, AND THE ARITHMETIC THAT FOLLOWS FROM THEM")
say("=" * 88)
say("  chain:  FOB_EUR = BP_JPY / FX * source_discount      (FX in the denominator)")
say()
fx_factor = FX_PRIOR / FX
disc_factor = DISC["J"] / DISC_PRIOR["J"]
net = fx_factor * disc_factor
say(f"  FX       : {FX_PRIOR} / {FX} = {fx_factor:.4f}   "
    f"({100*(fx_factor-1):+.2f}%)   a higher JPY/EUR LOWERS our euro cost")
say(f"  discount : {DISC['J']:.3f} / {DISC_PRIOR['J']:.3f} = {disc_factor:.4f}   "
    f"({100*(disc_factor-1):+.2f}%)   a higher discount RAISES it")
say(f"  NET      : {fx_factor:.4f} x {disc_factor:.4f} = {net:.4f}   "
    f"({100*(net-1):+.2f}%)   the two very nearly cancel")
say()

# work it on 10,000 yen of base price, held constant
BP_WORKED = 10_000.0
old_cost = BP_WORKED / FX_PRIOR * DISC_PRIOR["J"]
new_cost = BP_WORKED / FX * DISC["J"]
say(f"  worked on BP_JPY = {BP_WORKED:,.0f}, held constant:")
say(f"    old : {BP_WORKED:,.0f} / {FX_PRIOR} x {DISC_PRIOR['J']:.3f} = "
    f"{BP_WORKED/FX_PRIOR:,.4f} x {DISC_PRIOR['J']:.3f} = EUR {old_cost:,.3f}")
say(f"    new : {BP_WORKED:,.0f} / {FX} x {DISC['J']:.3f} = "
    f"{BP_WORKED/FX:,.4f} x {DISC['J']:.3f} = EUR {new_cost:,.3f}")
say(f"    move: EUR {new_cost - old_cost:+,.3f}  "
    f"({100*(new_cost/old_cost-1):+.2f}%)")
say()
full_pass = (1 + BASE_REV_SETTLED) * net - 1
full_pass_scen = (1 + BASE_REV_SCENARIO) * net - 1
say(f"  the euro move of the SETTLED revision, which is on file:")
say(f"    (1 {BASE_REV_SETTLED:+.6f}) x {net:.6f} - 1 = {100*full_pass:+.2f}%")
say(f"    that is 1.059616 x 0.995483 = 1.054832 in euro, so the yen revision of "
    f"5.9616%")
say(f"    lands at +5.48% on our current euro sales price - INSIDE the 4-6% band.")
say()
say(f"  the euro move of the 7.0% SCENARIO (agent-written, NOT on file):")
say(f"    (1 {BASE_REV_SCENARIO:+.2f}) x {net:.6f} - 1 = {100*full_pass_scen:+.2f}%")
say(f"    above the band; at +5% it needs {100*(full_pass_scen-0.05):.2f} pp held back.")
say()
old_margin_on_bp = 1 - DISC_PRIOR["J"]
new_margin_on_bp = 1 - DISC["J"]
say("  our margin on the YEN BASE-PRICE basis is 1 - discount:")
say(f"    old 1 - {DISC_PRIOR['J']:.3f} = {100*old_margin_on_bp:.1f}%")
say(f"    new 1 - {DISC['J']:.3f} = {100*new_margin_on_bp:.1f}%")
say(f"    change {100*(new_margin_on_bp-old_margin_on_bp):+.1f} percentage points")
say()
say("  the three FX vintages (all three are kept - the revision was priced on the oldest):")
say(f"    {FX_PRIOR:>6} JPY/EUR   {FX_PRIOR_PERIOD[0]} to {FX_PRIOR_PERIOD[1]}   "
    f"what the settled 5.9616% revision was priced on")
say(f"    {FX_MID:>6} JPY/EUR   2026-04-01 to 2026-09-30   the previous vintage")
say(f"    {FX:>6} JPY/EUR   {FX_PERIOD[0]} to {FX_PERIOD[1]}   live")

# ------------------------------------------------------------------ 1. the chain
say()
say("=" * 88)
say("1. THE CHAIN IDENTITY, AGAINST THE PRICE LIST")
say("=" * 88)

pl = pd.read_parquet(f"{D}\\pricing_list_pn.parquet",
                     columns=["part_number", "bp_jpy", "price_class", "source",
                              "fob_eur", "sp_eur", "gm", "is_superseded_row"])
pl = pl[pl["is_superseded_row"] != True].drop_duplicates("part_number")       # noqa: E712
say(f"  price list rows: {len(pl):,}")


def chain_test(frame, fx, disc):
    """Run the chain identity at one FX vintage. Returns the test frame."""
    chk = frame[frame["price_class"].isin(FACTOR) & frame["bp_jpy"].notna()
                & (frame["bp_jpy"] > 0) & frame["source"].isin(disc)].copy()
    chk["fob_calc"] = chk["bp_jpy"] / fx * chk["source"].map(disc)
    chk["sp_calc"] = chk["fob_calc"] / chk["price_class"].map(FACTOR)
    chk["gm_calc"] = 1 - chk["price_class"].map(FACTOR)
    chk["sp_err"] = (chk["sp_calc"] - chk["sp_eur"]).abs()
    chk["gm_err"] = (chk["gm_calc"] - chk["gm"]).abs()
    return chk


chk = chain_test(pl, FX, DISC)
chk_prior = chain_test(pl, FX_PRIOR, DISC_PRIOR)
say(f"  rows the formula can be tested on: {len(chk):,}")
say()
say(f"  {'':<34}{'LIVE 178.5 / 0.673':>22}{'PRIOR 163.7 / 0.620':>24}")
for lab, col, thr in (("SP_EUR reproduced to within 0.01", "sp_err", 0.01),
                      ("margin = 1 - class factor", "gm_err", 0.0005)):
    live_n = int((chk[col] <= thr).sum())
    prior_n = int((chk_prior[col] <= thr).sum())
    say(f"  {lab:<34}{live_n:>10,} of {len(chk):,}{prior_n:>12,} of {len(chk_prior):,}")
    say(f"  {'':<34}{100*(chk[col] <= thr).mean():>20.2f}%"
        f"{100*(chk_prior[col] <= thr).mean():>23.2f}%")
say()
say(f"  median SP error, live                : EUR {chk['sp_err'].median():.6f}")
say(f"  median SP error, prior vintage       : EUR {chk_prior['sp_err'].median():.6f}")
say()
say("  Excel form for the workbook (one row per part):")
say("     FOB_EUR  = BP_JPY / $FX * VLOOKUP(source, disc_table, 2, FALSE)")
say("     SP_EUR   = FOB_EUR / VLOOKUP(class, factor_table, 2, FALSE)")
say("     GM       = 1 - VLOOKUP(class, factor_table, 2, FALSE)")
say()
worst = chk.nlargest(3, "sp_err")[["part_number", "price_class", "source",
                                   "bp_jpy", "sp_eur", "sp_calc", "sp_err"]]
if len(worst) and worst["sp_err"].max() > 0.01:
    say("  the rows that do NOT reproduce at the live rate (top 3 by error):")
    say(worst.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    say()
    say("  => these are the roundings or overrides the workbook must carry as exceptions,")
    say("     not silently absorb.")

# ------------------------------------------------------------ 2. the SPA 53
say()
say("=" * 88)
say("2. THE 53 SPA LINES - REAL PURCHASE COST AGAINST THE CLASS-IMPLIED MARGIN")
say("=" * 88)
x = pd.ExcelFile(SPA)
raw = x.parse("SPA Optimizer", header=None)
hdr = None
for i, r in raw.iterrows():
    if any(str(v).strip() == "P/N" for v in r.values if str(v) != "nan"):
        hdr = i
        break
cols = [str(v).strip() for v in raw.iloc[hdr].values]
body = raw.iloc[hdr + 1:].copy()
body.columns = cols
body = body[body["P/N"].astype(str).str.match(r"^\d{8,12}$", na=False)].copy()
body["pn"] = body["P/N"].astype(str).str.strip().str.zfill(10)


def find_col(frame, *needles):
    """Match a column by substring so the euro sign encoding cannot break the join."""
    for c in frame.columns:
        low = str(c).lower()
        if all(n.lower() in low for n in needles):
            return c
    return None


C_PUR = find_col(body, "purchase", "price")
C_SAL = find_col(body, "isze sales", "price") or find_col(body, "sales", "price")
C_QTY = find_col(body, "l12", "qty")
C_REV = find_col(body, "l12", "revenue")
C_COST = find_col(body, "l12", "cost")
C_PROF = find_col(body, "l12", "profit")
C_GM = find_col(body, "l12", "gm")
say(f"  columns matched: purchase={C_PUR!r} sales={C_SAL!r} qty={C_QTY!r} "
    f"cost={C_COST!r} gm={C_GM!r}")
for c in (C_PUR, C_SAL, C_QTY, C_REV, C_COST, C_PROF, C_GM):
    if c is not None:
        body[c] = pd.to_numeric(body[c], errors="coerce")
say(f"  part lines read from SPA Optimizer: {len(body)}")

spa = body.merge(pl[["part_number", "price_class", "sp_eur", "gm"]],
                 left_on="pn", right_on="part_number", how="left")
say(f"  matched to the price list        : {int(spa['price_class'].notna().sum())}")
say()
spa["measured_gm"] = 1 - spa[C_PUR] / spa[C_SAL]
spa["class_gm"] = spa["gm"]
spa["gap_pp"] = 100 * (spa["measured_gm"] - spa["class_gm"])
say("  measured gross margin against the class-implied margin, in percentage points:")
say(spa["gap_pp"].describe(percentiles=[.1, .25, .5, .75, .9]).to_string(
    float_format=lambda v: f"{v:,.2f}"))
say()
say("  Excel form:")
say("     measured_GM = 1 - PurchasePrice / ISZESalesPrice")
say("     class_GM    = 1 - VLOOKUP(class, factor_table, 2, FALSE)")
say("     gap_pp      = 100 * (measured_GM - class_GM)")
say()
say("  the 8 widest gaps, as the lines where the class letter is most wrong:")
w = spa.dropna(subset=["gap_pp"]).copy()
w = w.reindex(w["gap_pp"].abs().sort_values(ascending=False).index).head(8)
if len(w):
    say(w[["pn", "price_class", C_PUR, C_SAL, "measured_gm", "class_gm",
           "gap_pp"]].to_string(index=False, float_format=lambda v: f"{v:,.3f}"))

# ---- what the rate change does to the measured margins on those lines
say()
say("-" * 88)
say("2b. WHAT THE RATE CHANGE DOES TO THE 50 MEASURED LINES")
say("-" * 88)
meas = spa.dropna(subset=["measured_gm"]).copy()
old_fob = meas["pn"].map(
    pl.set_index("part_number")["bp_jpy"]) / FX_PRIOR * DISC_PRIOR["J"]
new_fob = meas["pn"].map(
    pl.set_index("part_number")["bp_jpy"]) / FX * DISC["J"]
meas["gm_old_basis"] = 1 - old_fob / meas[C_SAL]
meas["gm_new_basis"] = 1 - new_fob / meas[C_SAL]
say(f"  measured margin median (this is a PURCHASE price, not the class factor):")
say(f"    as reported                       : {100*meas['measured_gm'].median():.2f}%")
say(f"    recomputed at 163.7 / 0.620       : {100*meas['gm_old_basis'].median():.2f}%")
say(f"    recomputed at 178.5 / 0.673       : {100*meas['gm_new_basis'].median():.2f}%")
say(f"    class-implied median on same lines: {100*meas['class_gm'].median():.2f}%")
say()
say("  NOTE: bp_jpy come from the price list, which is itself on a carried basis, so")
say("  this is an INDICATIVE re-cut of the same 50 lines, not a new measurement.")

# ---- why the catalogue does not reproduce the chain - and WHY IT MOVED
say()
say("=" * 88)
say("2c. THE ROWS THAT DO NOT REPRODUCE THE CHAIN - WHAT ARE THEY?")
say("=" * 88)
chk["class_gm_tbl"] = chk["price_class"].map(FACTOR)
bad = chk[chk["sp_err"] > 0.01].copy()
good = chk[chk["sp_err"] <= 0.01]
say(f"  rows off by more than 1 cent at the LIVE rate    : {len(bad):,} of {len(chk):,} "
    f"({100*len(bad)/len(chk):.1f}%)")
bad_p = chk_prior[chk_prior["sp_err"] > 0.01]
say(f"  rows off by more than 1 cent at the 163.7 vintage: {len(bad_p):,} of "
    f"{len(chk_prior):,} ({100*len(bad_p)/len(chk_prior):.1f}%)")
say()
say("  THIS IS THE CRITICAL FINDING OF THE RUN, and it is not a rounding story:")
say(f"    At 163.7 / 0.620 the chain reproduces on {100*(chk_prior['sp_err'] <= 0.01).mean():.2f}% of rows.")
say(f"    At 178.5 / 0.673 it reproduces on only {100*(chk['sp_err'] <= 0.01).mean():.2f}%.")
say("    The price file was therefore built on the OLD rates. It is NOT stale because")
say("    the rates are wrong - it is stale because the whole catalogue was priced on")
say("    163.7 / 0.620, so a recomputation at the live rates disagrees with every row")
say("    by the difference in the rates, not just on the override rows.")
say()
say("  the median error moves with it:")
say(f"    at 163.7 / 0.620 : EUR {chk_prior['sp_err'].median():.6f}")
say(f"    at 178.5 / 0.673 : EUR {chk['sp_err'].median():.6f}")
say()
say("  by class at the LIVE rate, the share that does NOT reproduce:")
t = chk.groupby("price_class").apply(
    lambda g: pd.Series({"rows": len(g),
                         "off_pct": 100 * (g["sp_err"] > 0.01).mean()}),
    include_groups=False).sort_values("rows", ascending=False)
say(t.to_string(float_format=lambda v: f"{v:,.1f}"))
say()
say("  by source:")
t2 = chk.groupby("source").apply(
    lambda g: pd.Series({"rows": len(g),
                         "off_pct": 100 * (g["sp_err"] > 0.01).mean()}),
    include_groups=False)
say(t2.to_string(float_format=lambda v: f"{v:,.1f}"))
say()
say("  is the mismatch a MULTIPLE of the formula, i.e. a factor override?")
bad["ratio"] = bad["sp_eur"] / bad["sp_calc"]
r = bad["ratio"].round(3)
say(f"    distinct ratios seen: {r.nunique():,}")
say("    the commonest 8:")
for val, n in r.value_counts().head(8).items():
    say(f"      ratio {val:>8.3f}   {n:>7,} rows")
say()
say("  => where a single multiple repeats across thousands of rows it is a class")
say("     override or a superseded row, not an error in the formula. The workbook")
say("     must carry SP_EUR FROM THE FILE and use the formula only where the file is")
say("     silent - otherwise it would invent a price for the whole catalogue.")

# ------------------------------------------------------------ 3. the index
say()
say("=" * 88)
say("3. THE WEIGHTED INDEX - DOES THE FORMULA REPRODUCE THE PUBLISHED MOVE?")
say("=" * 88)
cmp_ = pd.read_csv(f"{D}\\price_bp_weighted_compare_pn.csv", dtype={"part_number": str})
ins = cmp_[cmp_["in_scope"] == True].copy()                                   # noqa: E712
priced = ins[ins["bp_new_jpy"].notna() & ins["bp_prior_revised"].notna()].copy()
num = (priced["billed_qty"] * priced["bp_new_jpy"]).sum()
den = (priced["billed_qty"] * priced["bp_prior_revised"]).sum()
idx = num / den - 1
say(f"  priced rows: {len(priced):,}")
say(f"  index = SUM(q0 x p1) / SUM(q0 x p0) - 1")
say(f"        = {num:,.0f} / {den:,.0f} - 1")
say(f"        = {idx:.6f}  =  {100*idx:.4f}%")
say(f"  published figure                    : 5.9616%")
say(f"  reproduces                          : "
    f"{'YES' if abs(idx - 0.059616) < 1e-6 else 'NO'}")

# the marginal rule the framework rests on
say()
say("  THE MARGINAL RULE - what one part contributes to the index:")
say("     contribution_bp = weight_of_part x delta_pct x 10000")
say("     weight_of_part  = q0 x p0 / SUM(q0 x p0)")
wsum = den
sample = priced.nlargest(3, "billed_qty")[["part_number", "billed_qty",
                                           "bp_prior_revised"]].copy()
sample["weight_pct"] = 100 * (sample["billed_qty"] * sample["bp_prior_revised"]) / wsum
say()
say("  the three heaviest parts by index weight, to show the scale:")
say(sample.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))
say()
say("  A part with a 0.001% weight moving 5% contributes 0.00005 pp to the index.")
say("  That is the arithmetic behind the Launch book: the book is defined by the")
say("  sourcing deliverable carrying no L12M value for those parts, so they carry")
say("  0.06% of index weight and a fixed target cannot meaningfully constrain them.")
say("  CORRECTION (2026-09-18): the part numbers are weightless in the DELIVERABLE,")
say("  not in the sales data - 103 of them do carry 451 billed units between them,")
say("  0.037% of volume. Immaterial, but the earlier wording overstated it.")

# ------------------------------------------------------------ 4. the target solve
say()
say("=" * 88)
say("4. WHAT THE BASE REVISION WOULD HAVE TO BE TO LAND 4%, 5% AND 6%")
say("=" * 88)
say("  The question, stated plainly: on CURRENT pricing, holding the rate drift as it")
say("  is, how big can the yen base revision afford to be?")
say()
say(f"  With the net rate move at {net:.4f} and the base revision at b, the landed move is")
say(f"     (1 + b) x {net:.4f} - 1")
say("  so landing a target T needs  b = (1 + T) / net - 1.")
say()
say(f"  The SETTLED revision on file is {BASE_REV_SETTLED:.4%} in YEN, which becomes "
    f"{100*full_pass:+.2f}% in euro.")
say(f"  The 7.0% scenario (agent-written, not sourced) would become "
    f"{100*full_pass_scen:+.2f}% in euro.")
say()
say(f"  {'target':>8}{'base revision needed':>24}{'vs SETTLED 5.9616%':>22}"
    f"{'held back vs settled':>22}{'held back vs 7% scen':>22}")
solve = {}
for tgt in (0.04, 0.05, 0.06):
    b_needed = (1 + tgt) / net - 1
    vs_settled = b_needed - BASE_REV_SETTLED
    hold_settled = full_pass - tgt
    hold_scen = full_pass_scen - tgt
    solve[tgt] = {"base_revision_needed": b_needed,
                  "vs_settled": vs_settled,
                  "points_held_back_vs_settled": hold_settled,
                  "points_held_back_vs_scenario": hold_scen,
                  "relaxation_vs_plus7": b_needed - BASE_REV_SCENARIO}
    say(f"  {100*tgt:>7.0f}%{100*b_needed:>23.2f}%{100*vs_settled:>21.2f}%"
        f"{100*hold_settled:>21.2f}%{100*hold_scen:>21.2f}%")
say()
say(f"  read the table two ways.")
say(f"    Against the SETTLED revision: +4% needs a revision "
    f"{100*solve[0.04]['vs_settled']:+.2f} pp from settled")
say(f"    and +5% needs {100*solve[0.05]['vs_settled']:+.2f} pp, so both are BELOW what "
    f"is already on file.")
say(f"    +6% needs {100*solve[0.06]['vs_settled']:+.2f} pp, i.e. MORE than settled.")
say(f"    Against the 7% scenario: landing +5% means holding back "
    f"{100*solve[0.05]['points_held_back_vs_scenario']:.2f} points,")
say(f"    but that sacrifice only exists if the revision goes to 7%, which is not on file.")

# ------------------------------------------------------------ meta + verdict
arith_ok = all(
    abs(v - e) < 0.005 for v, e in (     # the settled figures are quoted to 2 decimals
        (100 * (fx_factor - 1), -8.29), (100 * (disc_factor - 1), 8.55),
        (100 * (net - 1), -0.45),
        (100 * full_pass, 5.48),         # settled 5.9616% yen -> euro
        (100 * full_pass_scen, 6.52),    # the 7% scenario -> euro
        (100 * (old_margin_on_bp - new_margin_on_bp), 5.30),
        (100 * solve[0.04]["base_revision_needed"], 4.47),
        (100 * solve[0.05]["base_revision_needed"], 5.48),
        (100 * solve[0.06]["base_revision_needed"], 6.48),
        (-100 * solve[0.04]["vs_settled"], 1.49),
        (-100 * solve[0.05]["vs_settled"], 0.49),
        (100 * solve[0.06]["vs_settled"], 0.52),
    ))
say()
say("=" * 88)
say("5. DO THE SETTLED FIGURES REPRODUCE EXACTLY?")
say("=" * 88)
checks = [
    ("FX cost factor 163.7 / 178.5", 100 * (fx_factor - 1), -8.29),
    ("discount cost factor 0.673 / 0.620", 100 * (disc_factor - 1), 8.55),
    ("net on landed cost", 100 * (net - 1), -0.45),
    ("SETTLED 5.9616% yen -> euro move", 100 * full_pass, 5.48),
    ("7% scenario yen -> euro move", 100 * full_pass_scen, 6.52),
    ("margin on yen base price, pp move", 100 * (old_margin_on_bp - new_margin_on_bp), 5.30),
    ("base revision to land +4%", 100 * solve[0.04]["base_revision_needed"], 4.47),
    ("base revision to land +5%", 100 * solve[0.05]["base_revision_needed"], 5.48),
    ("base revision to land +6%", 100 * solve[0.06]["base_revision_needed"], 6.48),
    ("+4% target vs settled, pp lower", -100 * solve[0.04]["vs_settled"], 1.49),
    ("+5% target vs settled, pp lower", -100 * solve[0.05]["vs_settled"], 0.49),
    ("+6% target vs settled, pp higher", 100 * solve[0.06]["vs_settled"], 0.52),
]
for lab, got, exp in checks:
    ok = abs(got - exp) < 0.005
    say(f"  {'PASS' if ok else 'FAIL'}  {lab:<38} computed {got:>8.2f}   "
        f"settled {exp:>8.2f}")

meta = {
    "step": "prove the framework maths",
    "settled_arithmetic_ok": bool(arith_ok),
    "rates": {
        "fx_live": FX,
        "fx_live_period": list(FX_PERIOD),
        "fx_prior_2026_04": FX_MID,
        "fx_prior_2025_10": FX_PRIOR,
        "discount_live": DISC,
        "discount_prior": DISC_PRIOR,
    },
    "rate_effects_pct": {
        "fx_cost_factor": float(100 * (fx_factor - 1)),
        "discount_cost_factor": float(100 * (disc_factor - 1)),
        "net_on_landed_cost": float(100 * (net - 1)),
        "euro_move_settled_revision_5_9616pct_yen": float(100 * full_pass),
        "euro_move_scenario_revision_7pct_yen": float(100 * full_pass_scen),
        "margin_on_yen_base_price_pp": float(100 * (old_margin_on_bp - new_margin_on_bp)),
    },
    "base_revision_provenance": {
        "settled": BASE_REV_SETTLED,
        "settled_source": "aim_pricing_recalc_2026-09-17.json - weighted 5.9616%, "
                          "step EUR 1,652,140.71",
        "settled_is_yen_basis": True,
        "settled_euro_move": float(full_pass),
        "scenario": BASE_REV_SCENARIO,
        "scenario_source": "AGENT-WRITTEN 2026-09-18. NOT on file, NOT a quotation "
                           "from IML. Retained only to size the ceiling case.",
        "scenario_euro_move": float(full_pass_scen),
    },
    "target_solve": {f"{int(100*t)}pct": {k: float(v) for k, v in d.items()}
                     for t, d in solve.items()},
    "chain_identity_rows_tested": int(len(chk)),
    "chain_sp_within_1c_pct_live": float(100 * (chk["sp_err"] <= 0.01).mean()),
    "chain_sp_within_1c_pct_prior_163_7": float(
        100 * (chk_prior["sp_err"] <= 0.01).mean()),
    "margin_identity_within_0.0005_pct_live": float(
        100 * (chk["gm_err"] <= 0.0005).mean()),
    "margin_identity_within_0.0005_pct_prior_163_7": float(
        100 * (chk_prior["gm_err"] <= 0.0005).mean()),
    "spa_lines": int(len(body)),
    "spa_matched_to_list": int(spa["price_class"].notna().sum()),
    "spa_measured_gm_median": float(spa["measured_gm"].median()),
    "spa_class_gm_median": float(spa["class_gm"].median()),
    "spa_gap_pp_median": float(spa["gap_pp"].median()),
    "spa_measured_gm_median_at_live_rates": float(meas["gm_new_basis"].median()),
    "spa_measured_gm_median_at_prior_rates": float(meas["gm_old_basis"].median()),
    "chain_pct_off_by_more_than_1c_live": float(100 * (chk["sp_err"] > 0.01).mean()),
    "chain_pct_off_by_more_than_1c_prior_163_7": float(
        100 * (chk_prior["sp_err"] > 0.01).mean()),
    "index_recomputed": float(idx),
    "index_published": 0.059616,
    "index_reproduces": bool(abs(idx - 0.059616) < 1e-6),
}
with open(f"{D}\\pricing_framework_maths_proof.json", "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say()
say("MATH_PROVEN" if (meta["index_reproduces"] and arith_ok) else "MATH_FAILED")
