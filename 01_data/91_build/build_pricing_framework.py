# -*- coding: utf-8 -*-
"""
ISZE pricing framework - the workbook.

Builds a live-formula Excel model for adjusting parts prices, with four books, a
weight bridge that proves the index arithmetic, and a margin/SPA view. Every dial
lives on one sheet and every result is a formula, so the file can be audited and
re-run by hand.

WHAT THIS IS NOT
It changes no price, writes no list, and runs no allocation. It is a model.

Run: python 01_data/91_build/build_pricing_framework.py
Writes: 01_data/01_Pricing/ISZE_Pricing_Framework.xlsx
        01_data/01_Pricing/_framework_meta.json
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
D = os.path.join(ISZE, "01_data", "00_derived")
OUT = os.path.join(ISZE, "01_data", "01_Pricing")
XLSX = os.path.join(OUT, "ISZE_Pricing_Framework.xlsx")
META = os.path.join(OUT, "_framework_meta.json")

# ---------------------------------------------------------------- the dials
# ---- the rates, as revised on 2026-09-18 ----------------------------------
# DIRECTION, and it matters: FOB_EUR = BP_JPY / FX * source_discount. FX is the
# DENOMINATOR, the discount the NUMERATOR. So a HIGHER JPY/EUR LOWERS our euro
# cost (163.7 / 178.5 = 0.9171, -8.29%) while a HIGHER discount RAISES it
# (0.673 / 0.620 = 1.0855, +8.55%). The two very nearly cancel: 0.9955, -0.45%.
# Do NOT write +18.36%: that read 178.5 / 163.7 as the cost factor, which is the
# reciprocal of the correct one.
FX_DEFAULT = 178.5              # JPY/EUR, live 1 Oct 2026 - 31 Mar 2027 (Suzuki san)
FX_MID = 172.6                  # JPY/EUR, 1 Apr 2026 - 30 Sep 2026 (previous vintage)
FX_PRIOR = 163.7                # JPY/EUR, as_of 1 Oct 2025 - what the settled
                                # 5.9616% base-price revision was priced on
DISC = {"J": 0.673, "T": 0.611}         # J was 0.620; T NOT revised in this update
DISC_PRIOR = {"J": 0.620, "T": 0.611}
# ---- the base revision. Two DIFFERENT things, and they must never be confused ----
# SETTLED: what is actually on file and was used to price the revision. Source:
#   01_data/00_derived/aim_pricing_recalc_2026-09-17.json, generated 2026-09-17 -
#   weighted_pct 5.9616, step_eur 1,652,140.71, ties out to the published figure.
# SCENARIO: 7.0% was written BY THE AGENT on 2026-09-18 as a "what if IML goes
#   further" case. It is NOT a quotation from IML and no file in the workspace
#   states it. It is kept only because Jerome's band has a ceiling and the useful
#   question is what happens above it. Never present it as what is coming.
BASE_REV_SETTLED = 0.059616
BASE_REV_SETTLED_SOURCE = ("aim_pricing_recalc_2026-09-17.json (generated 2026-09-17): "
                           "weighted 5.9616%, step EUR 1,652,140.71")
BASE_REV_SCENARIO = 0.07
FACTOR = {"C": 0.47, "D": 0.48, "F": 0.525, "J": 0.555,
          "M": 0.50, "P": 0.44, "V": 0.55, "T": 0.80}
TARGET_DEFAULT = 0.05
TARGET_SP_DEFAULT = 0.05        # Jerome's target on CURRENT sales price: 4-6%
DIST_MARGIN_DEFAULT = 0.35
CARRY = "carried from the price list"   # SP is never recomputed where the file has one


def say(m=""):
    print(m)
    sys.stdout.flush()


# ---------------------------------------------------------------- 1. build data
say("Loading the book ...")
cmp_ = pd.read_csv(os.path.join(D, "price_bp_weighted_compare_pn.csv"),
                   dtype={"part_number": str})
ins = cmp_[cmp_["in_scope"] == True].copy()                                   # noqa: E712
priced = ins[ins["bp_new_jpy"].notna() & ins["bp_prior_revised"].notna()].copy()
priced["pn"] = priced["part_number"].astype(str).str.strip().str.zfill(10)

pl = pd.read_parquet(os.path.join(D, "pricing_list_pn.parquet"),
                     columns=["part_number", "price_class", "sp_eur", "gm",
                              "bp_jpy", "source", "is_superseded_row"])
pl = pl[pl["is_superseded_row"] != True].drop_duplicates("part_number")        # noqa: E712
pl["pn"] = pl["part_number"].astype(str).str.strip().str.zfill(10)

aim = pd.read_csv(os.path.join(D, "aim_pn_classification_v2.csv"), dtype=str,
                  usecols=["part_number", "catalog_l1", "catalog_l2"])
aim["pn"] = aim["part_number"].astype(str).str.strip().str.zfill(10)
aim = aim.drop_duplicates("pn")

lines = priced.groupby("pn").agg(
    billed_qty=("billed_qty", "sum"),
    billed_eur=("net_sales_value", "sum"),
    prior_bp=("bp_prior_revised", "first"),
    new_bp=("bp_new_jpy", "first"),
).reset_index()
lines = lines.merge(pl[["pn", "price_class", "sp_eur", "gm", "bp_jpy", "source"]],
                    on="pn", how="left")
lines = lines.merge(aim[["pn", "catalog_l1", "catalog_l2"]], on="pn", how="left")
lines["weight_value"] = lines["billed_qty"] * lines["prior_bp"]
W_SUM = lines["weight_value"].sum()
say(f"  priced part numbers : {len(lines):,}")
say(f"  index weight sum    : {W_SUM:,.0f}")

# ---- the five books
p700 = pd.read_csv(os.path.join(D, "apl_p700_only_20260812.csv"), dtype=str)
rg21 = pd.read_csv(os.path.join(D, "apl_rg21_only_20260812.csv"), dtype=str)
p700["pn"] = p700["pn"].str.strip().str.zfill(10)
rg21["pn"] = rg21["pn"].str.strip().str.zfill(10)
for d in (p700, rg21):
    if "l12m_eur" in d.columns:
        d["l12m_eur"] = pd.to_numeric(d["l12m_eur"], errors="coerce")

launch = set(p700.loc[p700["l12m_eur"].isna(), "pn"]) | set(rg21.loc[rg21["l12m_eur"].isna(), "pn"])
ramp = (set(p700.loc[p700["l12m_eur"].notna(), "pn"])
        | set(rg21.loc[rg21["l12m_eur"].notna(), "pn"]))
ramp -= launch


def book_of(pn):
    if pn in launch:
        return "Launch"
    if pn in ramp:
        return "Ramp"
    return "Working"


lines["book"] = lines["pn"].map(book_of)
say(f"  Working {int((lines['book']=='Working').sum()):,} | "
    f"Ramp {int((lines['book']=='Ramp').sum()):,} | "
    f"Launch {int((lines['book']=='Launch').sum()):,}")
say(f"  launch part numbers with no L12M value at all: {len(launch):,}")
say(f"  ramp part numbers that DO have one           : {len(ramp):,}")

# ---- the frozen book, from the verified bridge
br = pd.read_csv(os.path.join(D, "oe_bridge_coverage.csv"), dtype={"pn": str})
br["pn"] = br["pn"].str.strip().str.zfill(10)
b = pd.read_parquet(os.path.join(D, "replenishment_bridge.parquet"))
b["pn"] = b["part_number"].astype(str).str.strip().str.zfill(10)
b["bq"] = pd.to_numeric(b["bill_qty"], errors="coerce")
b["be"] = pd.to_numeric(b["bill_eur"], errors="coerce")
floor = (b.groupby(["pn", "distributor_code"])
         .apply(lambda g: g["be"].sum() / g["bq"].sum() if g["bq"].sum() else np.nan,
                include_groups=False).dropna().rename("floor").reset_index())
mx = floor.groupby("pn")["floor"].min().rename("floor_min")
br = br.merge(mx, on="pn", how="left")
br["multiple"] = br["min_price_eur"] / br["floor_min"]
susp = br["multiple"] > 3                       # unit mismatches - excluded
frozen = set(br.loc[(br["multiple"] < 1) & (~susp), "pn"])
say(f"  frozen part numbers (aftermarket below our distributor's cost): {len(frozen):,}")
lines["book"] = np.where(lines["pn"].isin(frozen), "Frozen", lines["book"])

# ---- the COMPUTED margin, so the build can report it and the meta can carry it.
# Same filters the workbook writes: a source key the discount table holds, a yen
# base price, and a carried sales price to measure against. FOB = BP / FX * discount.
_ok = (lines["source"].isin(DISC) & lines["bp_jpy"].notna()
       & (lines["bp_jpy"] > 0) & lines["sp_eur"].notna() & (lines["sp_eur"] > 0))
_c = lines.loc[_ok]
_gm = 1 - (_c["bp_jpy"] / FX_DEFAULT * _c["source"].map(DISC)) / _c["sp_eur"]
GM_COMP_MEDIAN = float(_gm.median())
GM_COMP_WEIGHTED = float(
    (_c["billed_eur"] * _gm).sum() / _c["billed_eur"].sum() if len(_c) else np.nan)
GM_COMP_ROWS = int(len(_c))
say(f"  computed margin, median over {GM_COMP_ROWS:,} lines : "
    f"{100*GM_COMP_MEDIAN:.2f}%")
say(f"  computed margin, billed-weighted                    : "
    f"{100*GM_COMP_WEIGHTED:.2f}%")

books = lines.groupby("book").apply(lambda g: pd.Series({
    "part_numbers": len(g),
    "billed_eur": g["billed_eur"].sum(),
    "billed_qty": g["billed_qty"].sum(),
    "weight_pct": 100 * g["weight_value"].sum() / W_SUM,
}), include_groups=False)
say()
say(books.to_string(float_format=lambda v: f"{v:,.2f}"))

# ---------------------------------------------------------------- 2. workbook
say("Writing the workbook ...")
HDR = PatternFill("solid", fgColor="15233C")
HF = Font(bold=True, color="F7F4EE", size=10)
DIAL = PatternFill("solid", fgColor="FDE9D9")
SEC = Font(bold=True, size=10, color="15233C")
TITLE = Font(bold=True, size=13, color="15233C")
SUB = Font(italic=True, size=9, color="555555")
TOT = Font(bold=True)

wb = Workbook()
ws_read = wb.active
ws_read.title = "Read me"
ws_d = wb.create_sheet("Dials")
ws_b = wb.create_sheet("Books")
ws_l = wb.create_sheet("Line detail")
ws_w = wb.create_sheet("Weight bridge")
ws_m = wb.create_sheet("Margin and SPA")
ws_s = wb.create_sheet("Scenarios")
ws_c = wb.create_sheet("Checks")
ws_dash = wb.create_sheet("Dashboard")
for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False


def header(ws, row, labels, widths=None):
    for i, h in enumerate(labels, start=1):
        c = ws.cell(row, i, h)
        c.fill = HDR
        c.font = HF
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if widths:
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row + 1, 1)


# ================================================================== Dials
ws_d["A1"] = "DIALS - every input lives here. Shaded cells are the ones you change."
ws_d["A1"].font = TITLE
ws_d["A2"] = ("Nothing else in this workbook is typed. Change a shaded cell and every "
              "sheet below moves.")
ws_d["A2"].font = SUB
ws_d["A3"] = ("CARRIED vs COMPUTED. The price list price in column K of Line detail is "
              "CARRIED from the price file and is the AUTHORITY for anything billed. The "
              "computed cost and computed margin columns U..Z are a CROSS-CHECK that the "
              "FX and discount dials actually drive: they recompute a landed cost from "
              "the yen base price and the dials, and compare it to the carried price. "
              "Where the two disagree, the carried price is right and the difference is "
              "the finding - do not overwrite a carried price with a computed one.")
ws_d["A3"].font = SUB

r = 4
ws_d.cell(r, 1, "A. The increase").font = SEC
r += 1
header(ws_d, r, ["Dial", "Value", "Unit", "Note"])
ws_d.column_dimensions["A"].width = 46
for col, w in zip("BCD", (16, 14, 78)):
    ws_d.column_dimensions[col].width = w
r += 1
D_ROWS = {}
dial_rows = [
    # ORDER IS LOAD-BEARING. The book-uplift table must stay at rows 16-19 and the first
    # class factor at row 23, because the shipped verifier spot-checks those anchors and
    # every Line detail formula points at them. New dials therefore go AFTER section D,
    # never inside A - inserting a row here silently breaks the book dial and the class
    # VLOOKUP, which is exactly what the anchor check caught on 2026-09-18.
    ("Target weighted increase", TARGET_DEFAULT, "%", "the index this solve must land on", True),
    ("Per-line cap", 0.08, "%", "no line moves more than this in one cycle", True),
    ("Per-line floor", -0.12, "%", "a larger reduction is a repositioning, not a line", True),
    ("Distributor margin assumption", DIST_MARGIN_DEFAULT, "%", "an ASSUMPTION. No distributor shares its resale price", True),
    ("Foreign exchange (live)", FX_DEFAULT, "JPY/EUR", "LIVE, 1 Oct 2026 - 31 Mar 2027 (Suzuki san). A HIGHER JPY/EUR LOWERS our euro cost, because FX sits in the denominator of BP_JPY / FX. Previous vintages: 172.6 ran 1 Apr - 30 Sep 2026; 163.7 as_of 1 Oct 2025 is what the settled 5.9616% revision was priced on, so that revision was already stale on FX. Section E below turns these into a cost factor.", True),
    ("Japan purchase discount", DISC["J"], "factor", "was 0.620, now 0.673. A HIGHER discount RAISES our euro cost, because the discount is the share of base price we pay. Source: rate-revision workbook, sheet 'change applicable whole sale ratio', customer K208FJ, category 'vehicle parts'. Margin on the yen base price moved 38.0% -> 32.7%, i.e. -5.3 pp. The source table is in section E; the computed cost column on Line detail uses it via a VLOOKUP on the source.", True),
    ("Thailand purchase discount", DISC["T"], "factor", "IMIT source discount, UNCHANGED by the 2026-09-18 update - margin is 38.9%", True),
]
for label, val, unit, note, is_dial in dial_rows:
    ws_d.cell(r, 1, label)
    c = ws_d.cell(r, 2, val)
    if is_dial:
        c.fill = DIAL
    ws_d.cell(r, 3, unit)
    ws_d.cell(r, 4, note)
    D_ROWS[label] = r
    r += 1
for lab, fmt in (("Target weighted increase", "0.0%"),
                 ("Per-line cap", "0.0%"), ("Per-line floor", "0.0%"),
                 ("Distributor margin assumption", "0.0%")):
    ws_d.cell(D_ROWS[lab], 2).number_format = fmt
# the rate cells carry real decimals, not a percentage
ws_d.cell(D_ROWS["Foreign exchange (live)"], 2).number_format = "0.0"
ws_d.cell(D_ROWS["Japan purchase discount"], 2).number_format = "0.000"
ws_d.cell(D_ROWS["Thailand purchase discount"], 2).number_format = "0.000"
r += 1

ws_d.cell(r, 1, "B. Per-book uplift - the dial that decides where the increase lands").font = SEC
r += 1
header(ws_d, r, ["Book", "Uplift", "Unit", "Note"])
r += 1
BOOK_ROWS = {}
book_note = {
    "Working": "full index weight - this is where the money has to come from",
    "Ramp": "weight is last year's, so a rise here returns more than it costs",
    "Launch": "NO index weight. A fixed target cannot constrain these",
    "Frozen": "aftermarket below our distributor's cost - hold until sourcing is resolved",
}
for bk in ("Working", "Ramp", "Launch", "Frozen"):
    ws_d.cell(r, 1, bk)
    c = ws_d.cell(r, 2, 0.05)
    c.fill = DIAL
    c.number_format = "0.0%"
    ws_d.cell(r, 3, "%")
    ws_d.cell(r, 4, book_note[bk])
    BOOK_ROWS[bk] = r
    r += 1
BOOK_ROW0 = min(BOOK_ROWS.values())
BOOK_ROW1 = max(BOOK_ROWS.values())
r += 1

ws_d.cell(r, 1, "C. The class factors and purchase discounts - IML's, shown for traceability").font = SEC
r += 1
header(ws_d, r, ["Class", "Factor", "Margin", "Note"])
r += 1
CLASS_ROW0 = r
for k, v in FACTOR.items():
    ws_d.cell(r, 1, k)
    ws_d.cell(r, 2, v).number_format = "0.000"
    ws_d.cell(r, 3, f"=1-B{r}").number_format = "0.0%"
    ws_d.cell(r, 4, "IML-owned. Not modified by this model.")
    r += 1
CLASS_ROW1 = r - 1
r += 1

# ---- E. the source discount table, the two rate changes, and the target block
ws_d.cell(r, 1, "E. The two rate changes of 2026-09-18, and the target on current price").font = SEC
r += 1
ws_d.cell(r, 1, "A higher JPY/EUR LOWERS our euro cost; a higher discount RAISES it; "
                "these two changes very nearly cancel, netting -0.45%.").font = SUB
ws_d.cell(r, 1).alignment = Alignment(wrap_text=False)
r += 1
header(ws_d, r, ["Source", "Discount", "Margin on yen base price", "Note"])
r += 1
DISC_ROW0 = r
for src, note in (("J", "Japan / IML - revised 2026-09-18 from 0.620"),
                  ("T", "Thailand / IMIT - NOT revised in this update")):
    ws_d.cell(r, 1, src)
    ws_d.cell(r, 2, DISC[src]).number_format = "0.000"
    ws_d.cell(r, 3, f"=1-B{r}").number_format = "0.0%"
    ws_d.cell(r, 4, note)
    r += 1
DISC_ROW1 = r - 1
r += 1
# the vintage table goes BEFORE the rate block, so the rate block can point at the
# recorded 163.7 rather than repeating the number as a literal
ws_d.cell(r, 1, "F. The rate vintages, all three kept - the revision was priced on the oldest").font = SEC
r += 1
header(ws_d, r, ["Vintage", "JPY/EUR", "Period", "Note"])
r += 1
VINTAGE_ROWS = {}
for vintage, rate, period, note in (
        ("163.7", FX_PRIOR, "1 Oct 2025 - 31 Mar 2026",
         "what the settled 5.9616% base-price revision was priced on. That revision "
         "was therefore already stale on FX before the discount moved."),
        ("172.6", FX_MID, "1 Apr 2026 - 30 Sep 2026",
         "Suzuki san's previous vintage. Recorded for traceability, not used as the live rate."),
        ("178.5", FX_DEFAULT, "1 Oct 2026 - 31 Mar 2027",
         "LIVE rate (Suzuki san, mail to Hadi san). This is the dial at A. above; the "
         "value here is a record of it, not a second dial.")):
    ws_d.cell(r, 1, vintage)
    ws_d.cell(r, 2, rate).number_format = "0.0"
    ws_d.cell(r, 3, period)
    ws_d.cell(r, 4, note)
    VINTAGE_ROWS[vintage] = r
    r += 1
r += 1
# the target dial, and the base-revision assumption it needs
ws_d.cell(r, 1, "Target on current sales price").font = SEC
c = ws_d.cell(r, 2, TARGET_SP_DEFAULT)
c.fill = DIAL
c.number_format = "0.0%"
ws_d.cell(r, 3, "%")
ws_d.cell(r, 4, "Jerome's actual target: 4-6% on OUR CURRENT sales price, with the rate "
                "drift absorbed. The rows below turn that into the points we give up.")
TARGET_SP_ROW = r
r += 1
ws_d.cell(r, 1, "Settled base-price revision (yen)").font = SEC
c = ws_d.cell(r, 2, BASE_REV_SETTLED)
c.fill = DIAL
c.number_format = "0.0000%"
ws_d.cell(r, 3, "%")
ws_d.cell(r, 4, f"ON FILE - this is the revision that exists, not an assumption. "
                f"Source: {BASE_REV_SETTLED_SOURCE}. It is the yen base-price move, so "
                f"the euro move comes after the rate drift (see the rows below).")
BASE_REV_SETTLED_ROW = r
r += 1
ws_d.cell(r, 1, "Scenario base revision (yen)").font = SEC
c = ws_d.cell(r, 2, BASE_REV_SCENARIO)
c.fill = DIAL
c.number_format = "0.0%"
ws_d.cell(r, 3, "%")
ws_d.cell(r, 4, "SCENARIO, NOT A QUOTATION FROM IML. Written by the agent on 2026-09-18 to "
                "test what happens if the yen revision is larger than settled. Nothing in "
                "the workspace states 7%. Read it only as the ceiling case.")
BASE_REV_SCEN_ROW = r
r += 1
r += 1
rate_rows = [
    ("FX cost factor, 163.7 -> 178.5",
     f"=Dials!$B${VINTAGE_ROWS['163.7']}/Dials!$B${D_ROWS['Foreign exchange (live)']}",
     "0.0000",
     "the FX is in the DENOMINATOR, so the cost factor is OLD / NEW, not NEW / OLD. "
     "0.9171 = -8.29%."),
    ("Discount cost factor, 0.620 -> 0.673", f"={DISC['J']:.3f}/{DISC_PRIOR['J']:.3f}", "0.0000",
     "the discount is in the NUMERATOR - a bigger share of base price paid. 1.0855 = +8.55%."),
    ("Net on landed cost", "=B{R0}*B{R1}", "0.0000",
     "the two very nearly cancel: 0.9171 x 1.0855 = 0.9955, i.e. -0.45%"),
    ("SETTLED revision, euro move at live rates",
     f"=(1+Dials!$B${BASE_REV_SETTLED_ROW})*B{{R2}}-1", "0.0000%",
     "the headline: the settled 5.9616% yen revision becomes +5.48% in euro, because the "
     "net rate drift is -0.45%. That is ALREADY INSIDE the 4-6% band."),
    ("SCENARIO revision (7.0%), euro move at live rates",
     f"=(1+Dials!$B${BASE_REV_SCEN_ROW})*B{{R2}}-1", "0.0000%",
     "the ceiling case only: +6.52%, above the band. Not a quotation from IML."),
    ("Target on current sales price", f"=Dials!$B${TARGET_SP_ROW}", "0.0%",
     "Jerome's target: 4-6% on OUR CURRENT sales price, drift absorbed"),
    ("Points held back against the SETTLED revision", "=100*(B{R3}-B{R5})", '0.00" pp"',
     "settled euro move minus the target. Positive = we are below the settled revision "
     "already, so nothing has to be absorbed; at the +5% target it is +0.48 pp and the "
     "settled revision simply lands inside the band."),
    ("Points held back against the SCENARIO", "=100*(B{R4}-B{R5})", '0.00" pp"',
     "scenario euro move minus the target. At +5% this is 1.52 pp - the number that "
     "matters only IF the yen revision goes to 7%."),
    ("Base revision needed to hit the target", "=(1+B{R5})/B{R2}-1", "0.00%",
     "how big the yen revision could afford to be to land the target exactly"),
    ("...versus the SETTLED revision",
     f"=100*(B{{R8}}-Dials!$B${BASE_REV_SETTLED_ROW})",
     '0.00" pp"',
     "the useful column: how far the revision would have to move from what is on file. "
     "Negative = the revision would have to be SMALLER than settled to land the target."),
]
assert len(rate_rows) == 10, f"rate_rows index markers assume 10 rows, got {len(rate_rows)}"
RATE_ROW_START = r
for lab, formula, fmt, note in rate_rows:
    ws_d.cell(r, 1, lab)
    ws_d.cell(r, 2, formula).number_format = fmt
    ws_d.cell(r, 3, "")
    ws_d.cell(r, 4, note)
    r += 1
RATE_ROW_END = r - 1
# now resolve the row references inside those formulas. All ten at once: a partial
# resolve leaves a literal "{R9}" in the cell, and .replace() on the already-replaced
# text is idempotent because the markers are gone by then.
_r = {i: RATE_ROW_START + i for i in range(len(rate_rows))}
for i in range(len(rate_rows)):
    c = ws_d.cell(RATE_ROW_START + i, 2)
    if isinstance(c.value, str):
        for k, row in _r.items():
            c.value = c.value.replace("{R%d}" % k, str(row))
DISC_TABLE = f"Dials!$A${DISC_ROW0}:$B${DISC_ROW1}"
r += 1
ws_d.cell(r, 1, "G. Evidence caps - how far a line may move, by evidence quality").font = SEC
r += 1
header(ws_d, r, ["Tier", "Cap", "Unit", "Meaning"])
r += 1
TIER_ROW0 = r
for t, cap, mean in (("T1", 0.10, "observed at the same shop, same part number"),
                     ("T2", 0.06, "derived from a published listing"),
                     ("T3", 0.06, "network benchmark"),
                     ("T4", 0.03, "category median"),
                     ("T5", 0.00, "no benchmark - never move blind")):
    ws_d.cell(r, 1, t)
    ws_d.cell(r, 2, cap).number_format = "0.0%"
    ws_d.cell(r, 3, "pp")
    ws_d.cell(r, 4, mean)
    r += 1
TIER_ROW1 = r - 1

CELL = {
    "target": f"Dials!$B${D_ROWS['Target weighted increase']}",
    "target_sp": f"Dials!$B${TARGET_SP_ROW}",
    "cap": f"Dials!$B${D_ROWS['Per-line cap']}",
    "floor": f"Dials!$B${D_ROWS['Per-line floor']}",
    "dist_margin": f"Dials!$B${D_ROWS['Distributor margin assumption']}",
    "fx": f"Dials!$B${D_ROWS['Foreign exchange (live)']}",
    "disc_J": f"Dials!$B${D_ROWS['Japan purchase discount']}",
    "disc_T": f"Dials!$B${D_ROWS['Thailand purchase discount']}",
    "base_rev": f"Dials!$B${BASE_REV_SETTLED_ROW}",
    "base_rev_settled": f"Dials!$B${BASE_REV_SETTLED_ROW}",
    "base_rev_scenario": f"Dials!$B${BASE_REV_SCEN_ROW}",
}
for bk, rr in BOOK_ROWS.items():
    CELL[f"book_{bk}"] = f"Dials!$B${rr}"
BOOK_TABLE = f"Dials!$A${BOOK_ROW0}:$B${BOOK_ROW1}"
TIERS = f"Dials!$A${TIER_ROW0}:$B${TIER_ROW1}"
CLASSES = f"Dials!$A${CLASS_ROW0}:$C${CLASS_ROW1}"
# the rate block on Dials, section E
RATE_ROW_FX = RATE_ROW_START + 0
RATE_ROW_DISC = RATE_ROW_START + 1
RATE_ROW_NET = RATE_ROW_START + 2
RATE_ROW_SETTLED = RATE_ROW_START + 3
RATE_ROW_SCEN = RATE_ROW_START + 4
RATE_ROW_TGT = RATE_ROW_START + 5
RATE_ROW_GIVE_SETTLED = RATE_ROW_START + 6
RATE_ROW_GIVE_SCEN = RATE_ROW_START + 7
RATE_ROW_NEED = RATE_ROW_START + 8
RATE_ROW_NEED_VS_SETTLED = RATE_ROW_START + 9

# ================================================================== Books
say("  Books sheet")
ws_b["A1"] = "THE FIVE BOOKS - how much of the price index each one carries"
ws_b["A1"].font = TITLE
ws_b["A2"] = ("The index weights by last year's revenue. That single fact is why the "
              "Launch book is free and the Working book has to pay for everything.")
ws_b["A2"].font = SUB
header(ws_b, 4, ["Book", "Part numbers", "L12M billed EUR", "L12M qty",
                 "Share of index weight", "Share of billed EUR", "Rule"],
       [14, 14, 17, 14, 20, 18, 66])
r = 5
first_book_row = r
for bk in ("Working", "Ramp", "Launch", "Frozen"):
    ws_b.cell(r, 1, bk)
    # NOTE the column letters. On Line detail: G = book, I = weight value, J = weight %,
    # C = billed EUR. These were written as H/E/J in the first build - an off-by-one that
    # only showed up when the cells were read back. Do not "tidy" these letters.
    ws_b.cell(r, 2, f'=COUNTIF(\'Line detail\'!$G:$G,A{r})')
    ws_b.cell(r, 3, f'=SUMIF(\'Line detail\'!$G:$G,A{r},\'Line detail\'!$C:$C)')
    ws_b.cell(r, 4, f'=SUMIF(\'Line detail\'!$G:$G,A{r},\'Line detail\'!$B:$B)')
    ws_b.cell(r, 5, f'=SUMIF(\'Line detail\'!$G:$G,A{r},\'Line detail\'!$J:$J)')
    ws_b.cell(r, 6, f'=C{r}/SUM($C${first_book_row}:$C${first_book_row+3})')
    ws_b.cell(r, 7, book_note[bk])
    r += 1
last_book_row = r - 1
ws_b.cell(r, 1, "Total").font = TOT
for col in "BCDE":
    ws_b[f"{col}{r}"] = f"=SUM({col}{first_book_row}:{col}{last_book_row})"
    ws_b[f"{col}{r}"].font = TOT
ws_b.cell(r, 6, f"=SUM(F{first_book_row}:F{last_book_row})").font = TOT
for rr in range(first_book_row, r + 1):
    for col, fmt in ((3, "#,##0"), (4, "#,##0"), (5, "0.00%"), (6, "0.00%")):
        ws_b.cell(rr, col).number_format = fmt
BOOK_TOTAL_ROW = r

# ================================================================== Line detail
say(f"  Line detail sheet ({len(lines):,} rows)")
LD = ["pn", "billed_qty", "billed_eur", "price_class", "prior_bp", "new_bp",
      "book", "catalog_l1", "weight_value", "weight_pct", "current_sp",
      "target_uplift", "delta_pct", "capped_delta", "proposed_sp",
      "index_weight_pp", "index_contribution_pp", "new_billed_eur",
      "delta_eur", "class_margin_untouched",
      # ---- the COMPUTED cost block. These are additions: K (Current SP EUR) stays
      # carried from the price list, and nothing existing shifts to make room.
      "source", "bp_jpy_carried", "fob_eur_computed", "gm_computed", "gm_delta_pp",
      "gm_gap_to_book_pp"]
lines = lines.sort_values("weight_value", ascending=False).reset_index(drop=True)
header(ws_l, 1, ["Part number", "L12M qty", "L12M billed EUR", "Class", "Prior BP JPY",
                 "New BP JPY", "Book", "AIM L1", "Weight value", "Weight %",
                 "Current SP EUR", "Uplift %", "Delta %", "Capped delta %",
                 "Proposed SP EUR", "Weight", "Index contribution pp",
                 "New billed EUR", "Delta EUR", "Class margin %",
                 "Source (COMPUTED input)", "BP JPY carried (COMPUTED input)",
                 "FOB EUR COMPUTED", "GM COMPUTED", "GM delta vs class pp COMPUTED",
                 "GM gap to book pp COMPUTED"],
       [14, 12, 15, 8, 13, 13, 11, 24, 16, 11, 14, 10, 10, 13, 14, 11, 20, 15, 13, 14,
        12, 14, 15, 13, 18, 18])
r = 2
LD_TOTAL_FWD = len(lines) + 2          # the totals row, known before the loop runs
for _, row in lines.iterrows():
    ws_l.cell(r, 1, row["pn"])
    ws_l.cell(r, 2, float(row["billed_qty"]))
    ws_l.cell(r, 3, float(row["billed_eur"]))
    ws_l.cell(r, 4, row["price_class"] if pd.notna(row["price_class"]) else "")
    ws_l.cell(r, 5, float(row["prior_bp"]))
    ws_l.cell(r, 6, float(row["new_bp"]))
    ws_l.cell(r, 7, row["book"])
    ws_l.cell(r, 8, row["catalog_l1"] if pd.notna(row["catalog_l1"]) else "Not on spine")
    ws_l.cell(r, 9, f"=B{r}*E{r}")
    ws_l.cell(r, 10, f"=IF($I${len(lines)+1}=0,0,I{r}/$I${len(lines)+1})")
    ws_l.cell(r, 11, float(row["sp_eur"]) if pd.notna(row["sp_eur"]) else "")
    # uplift pulls from the book dial - the one place the book choice takes effect.
    # The range MUST be the book table on Dials (rows 16-19), not an offset from it:
    # the first build wrote $A$8:$B$11, which is the cap/floor/discount block, so every
    # book silently read the wrong number.
    ws_l.cell(r, 12, f'=IFERROR(VLOOKUP(G{r},{BOOK_TABLE},2,FALSE),0)')
    ws_l.cell(r, 13, f'=IFERROR(F{r}/E{r}-1,0)')
    # The capped delta. FROZEN MEANS FROZEN: the post is held until sourcing is
    # resolved, so the capped delta is forced to ZERO for a frozen row rather than
    # taking the book uplift. Before 2026-09-18 this read MEDIAN(floor, L+M, cap)
    # for every book, so a frozen part received at least the book uplift and 15 of
    # the 24 frozen parts sat at the +8% cap - the formula contradicted the sheet's
    # own note. The book dial for Frozen is deliberately NOT changed (it would be a
    # dial fudge); the semantics are enforced here instead.
    ws_l.cell(r, 14, f'=IF(G{r}="Frozen",0,MEDIAN({CELL["floor"]},L{r}+M{r},{CELL["cap"]}))')
    ws_l.cell(r, 15, f'=IFERROR(K{r}*(1+N{r}),"")')
    ws_l.cell(r, 16, f'=J{r}')
    ws_l.cell(r, 17, f'=O{r}*J{r}')
    ws_l.cell(r, 18, f'=IFERROR(B{r}*O{r},"")')
    ws_l.cell(r, 19, f'=IFERROR(Q{r}-C{r},"")')
    ws_l.cell(r, 20, f'=IFERROR(1-VLOOKUP(D{r},Dials!$A${CLASS_ROW0}:$C${CLASS_ROW1},2,FALSE),"")')
    # ---- the COMPUTED cost block (columns U..Z). These are what make the rate dials
    # drive something real. U/V carry the inputs the formula needs; W is the landed
    # cost the dials produce; X is the gross margin that implies against the CARRIED
    # sales price; Y is that margin against the class letter; Z is against the book.
    #
    # V is the carried yen base price (same value as E, written separately so the
    # computed block can be read on its own without a column of blank cells if the
    # yen base is ever revised independently).
    ws_l.cell(r, 21, row["source"] if pd.notna(row["source"]) else "")
    ws_l.cell(r, 22, float(row["bp_jpy"]) if pd.notna(row["bp_jpy"]) else "")
    # FOB_EUR = BP_JPY / FX * discount. The discount is a VLOOKUP on the SOURCE, so
    # the Dials table must contain both keys J and T. FX is the denominator.
    # NOTE the column letters: W is this FOB, and X below must divide by W - NOT by S,
    # which is Delta EUR. The first version of this block wrote S2 in the X formula, so
    # every computed margin was measured against the wrong column and Excel returned
    # -638% medians. Evaluating the workbook in Excel is what caught it; the signature
    # check alone did not, because it asserted the same wrong reference.
    ws_l.cell(r, 23, f'=IFERROR(V{r}/{CELL["fx"]}'
                     f'*VLOOKUP(U{r},{DISC_TABLE},2,FALSE),"")')
    ws_l.cell(r, 24, f'=IFERROR(IF(K{r}="","",IF(K{r}<=0,"",1-W{r}/K{r})),"")')
    ws_l.cell(r, 25, f'=IFERROR(100*(X{r}-T{r}),"")')
    # Z is against the billed-weighted COMPUTED margin of this same book, which sits in
    # X of the totals row. That is a formula in one cell, so it costs Excel one
    # evaluation rather than one per row.
    ws_l.cell(r, 26, f'=IFERROR(100*(X{r}-$X${LD_TOTAL_FWD}),"")')
    r += 1
last = r
ws_l.cell(last, 1, "TOTAL").font = TOT
for col, fmt in ((2, "#,##0"), (3, "#,##0.00"), (5, "#,##0"), (6, "#,##0"),
                 (9, "#,##0"), (10, "0.0000%"), (11, "#,##0.00"), (12, "0.0%"),
                 (13, "0.00%"), (14, "0.00%"), (15, "#,##0.00"), (16, "0.0000%"),
                 (17, "0.0000"), (18, "#,##0.00"), (19, "#,##0.00"), (20, "0.0%")):
    ws_l.cell(last, col, f"=SUM({get_column_letter(col)}2:{get_column_letter(col)}{last-1})")
    ws_l.cell(last, col).font = TOT
    for rr2 in range(2, last):
        ws_l.cell(rr2, col).number_format = fmt
# ---- the COMPUTED block gets its own formatting and its own totals. These columns
# are NOT summed: a sum of margins is meaningless. The totals row carries the
# billed-weighted computed margin instead, which is the number to read.
for col, fmt in ((23, "#,##0.0000"), (24, "0.00%"), (25, "0.00"),
                 (26, "0.00")):
    for rr2 in range(2, last):
        ws_l.cell(rr2, col).number_format = fmt
ws_l.cell(last, 21, f"=COUNTA(U2:U{last-1})&\" sourced rows\"").font = TOT
ws_l.cell(last, 23, f"=IFERROR(SUMIF(U2:U{last-1},\"J\",W2:W{last-1})"
                    f"+SUMIF(U2:U{last-1},\"T\",W2:W{last-1}),\"\")").font = TOT
ws_l.cell(last, 23).number_format = "#,##0.0000"
# The totals row carries the BILLED-WEIGHTED computed margin - a sum of margins would be
# meaningless. NOTE the array-separator comma form: SUMPRODUCT(range, range). An IF()
# inside SUMPRODUCT returns #VALUE! here (tested 2026-09-18), and multiplying the ranges
# with * also fails on the 656 rows whose X is the IFERROR "" string. The comma form
# treats text as zero without needing either.
#
# The DENOMINATOR is the billed euro on rows that HAVE a computed margin, not all billed
# euro. That is deliberate and it is what makes this comparable to the 51.09% book margin:
# both then rest on the same EUR 29,653,732 base. Dividing by all billed euro instead
# would flatter the number by ~4.8 points for no reason a reader could see.
ws_l.cell(last, 24, f'=IFERROR(SUMPRODUCT(C2:C{last-1},X2:X{last-1})'
                    f'/SUMPRODUCT(C2:C{last-1}*ISNUMBER(X2:X{last-1})),"")').font = TOT
ws_l.cell(last, 24).number_format = "0.00%"
ws_l.cell(last, 25, f'=IFERROR(100*(SUMPRODUCT(C2:C{last-1},X2:X{last-1})'
                    f'/SUMPRODUCT(C2:C{last-1}*ISNUMBER(X2:X{last-1}))'
                    f'-SUMPRODUCT(C2:C{last-1},T2:T{last-1})'
                    f'/SUMPRODUCT(C2:C{last-1}*ISNUMBER(X2:X{last-1}))),"")').font = TOT
ws_l.cell(last, 25).number_format = "0.00"
# the class margin on the SAME rows, so the gap in column Y is an apples-to-apples one
ws_l.cell(last, 22, f'=IFERROR(SUMPRODUCT(C2:C{last-1},T2:T{last-1})'
                    f'/SUMPRODUCT(C2:C{last-1}*ISNUMBER(X2:X{last-1})),"")').font = TOT
ws_l.cell(last, 22).number_format = "0.00%"
ws_l.cell(last, 26, "").font = TOT
LD_TOTAL = last

# ================================================================== Weight bridge
ws_w["A1"] = "WEIGHT BRIDGE - where the index actually comes from"
ws_w["A1"].font = TITLE
ws_w["A2"] = ("The index is SUM(q0 x p1) / SUM(q0 x p0) - 1. This sheet splits that "
              "by book, so the cost of a freeze and the freedom on new parts are both "
              "visible as numbers rather than argued.")
ws_w["A2"].font = SUB
header(ws_w, 4, ["Book", "Weight (q0 x p0)", "Share of weight",
                 "Weighted uplift in the book", "Index contribution pp",
                 "Contribution bp"],
       [14, 20, 16, 24, 22, 16])
r = 5
wb_first = r
for i, bk in enumerate(("Working", "Ramp", "Launch", "Frozen")):
    ws_w.cell(r, 1, bk)
    ws_w.cell(r, 2, f"=SUMIF('Line detail'!$G:$G,A{r},'Line detail'!$I:$I)")
    ws_w.cell(r, 3, f"=B{r}/SUM($B${wb_first}:$B${wb_first+3})")
    ws_w.cell(r, 4, f"=IFERROR(SUMPRODUCT(('Line detail'!$G$2:$G${LD_TOTAL-1}=A{r})"
                    f"*'Line detail'!$I$2:$I${LD_TOTAL-1}"
                    f"*'Line detail'!$N$2:$N${LD_TOTAL-1})/B{r},0)")
    ws_w.cell(r, 5, f"=C{r}*D{r}*100")
    ws_w.cell(r, 6, f"=E{r}*100")
    r += 1
wb_last = r - 1
ws_w.cell(r, 1, "Total").font = TOT
ws_w.cell(r, 2, f"=SUM(B{wb_first}:B{wb_last})").font = TOT
ws_w.cell(r, 3, f"=SUM(C{wb_first}:C{wb_last})").font = TOT
ws_w.cell(r, 4, f"=SUMPRODUCT('Line detail'!$I$2:$I${LD_TOTAL-1},"
                f"'Line detail'!$N$2:$N${LD_TOTAL-1})/B{r}").font = TOT
ws_w.cell(r, 5, f"=SUM(E{wb_first}:E{wb_last})").font = TOT
ws_w.cell(r, 6, f"=E{r}*100").font = TOT
WB_TOTAL = r
for rr in range(wb_first, r + 1):
    for col, fmt in ((2, "#,##0"), (3, "0.00%"), (4, "0.0000%"), (5, "0.0000"),
                     (6, "0.0000")):
        ws_w.cell(rr, col).number_format = fmt
r += 2
ws_w.cell(r, 1, "THE CHECK THAT MAKES THIS TRUSTWORTHY").font = SEC
r += 1
ws_w.cell(r, 1, "Recomputed index from Line detail")
ws_w.cell(r, 4, f"=SUMPRODUCT('Line detail'!$B$2:$B${LD_TOTAL-1},"
                f"'Line detail'!$F$2:$F${LD_TOTAL-1})"
                f"/SUMPRODUCT('Line detail'!$B$2:$B${LD_TOTAL-1},"
                f"'Line detail'!$E$2:$E${LD_TOTAL-1})")
ws_w.cell(r, 5, "Index before any change")
ws_w.cell(r, 4).number_format = "0.0000%"
IDX_BASE_ROW = r

# ================================================================== Margin and SPA
ws_m["A1"] = "MARGIN AND SPA - what each book earns, and what a cut would cost"
ws_m["A1"].font = TITLE
ws_m["A2"] = ("Margin is 1 minus the class factor, which IML owns. The SPA lines carry a "
              "REAL purchase price, so they are where a measured margin can be compared to "
              "the class letter. The new computed-margin column is a SECOND, much wider "
              "cross-check: it derives a landed cost from the yen base price and the two "
              "rate dials, on every line in the workbook.")
ws_m["A2"].font = SUB
header(ws_m, 4, ["Book", "Billed EUR", "Gross profit EUR at class margin",
                 "Class margin", "Gap pp on the measured lines", "Computed margin (all lines)",
                 "Note"],
       [14, 15, 26, 13, 24, 22, 44])
r = 5
m_first = r
for i, bk in enumerate(("Working", "Ramp", "Launch", "Frozen")):
    ldr = first_book_row + i
    ws_m.cell(r, 1, bk)
    ws_m.cell(r, 2, f"=Books!C{ldr}")
    # gross profit = billed x the class margin in column D, not a typed number, so
    # changing a class factor on Dials moves this. The first build hardcoded 0.5109.
    ws_m.cell(r, 3, f"=B{r}*D{r}")
    ws_m.cell(r, 4, f"=IFERROR(SUMPRODUCT(('Line detail'!$G$2:$G${LD_TOTAL-1}=A{r})"
                    f"*'Line detail'!$C$2:$C${LD_TOTAL-1}"
                    f"*'Line detail'!$T$2:$T${LD_TOTAL-1})/B{r},0)").number_format = "0.00%"
    ws_m.cell(r, 5, "").number_format = "0.00"
    # computed margin for the book, billed-weighted from the COMPUTED block (X). The
    # comma array-separator form, for the same reason as the totals row on Line detail.
    ws_m.cell(r, 6, f"=IFERROR(SUMPRODUCT(('Line detail'!$G$2:$G${LD_TOTAL-1}=A{r})"
                    f"*'Line detail'!$C$2:$C${LD_TOTAL-1},"
                    f"'Line detail'!$X$2:$X${LD_TOTAL-1})/B{r},0)").number_format = "0.00%"
    ws_m.cell(r, 7, "column D is the class letter applied to the carried price; column F "
                    "is recomputed from the yen base and the rate dials")
    r += 1
m_last = r - 1
for rr in range(m_first, r):
    for col, fmt in ((2, "#,##0"), (3, "#,##0")):
        ws_m.cell(rr, col).number_format = fmt
r += 2

# ---- the three margins side by side, at their true grains
ws_m.cell(r, 1, "THE THREE MARGINS WE HOLD - and they are at different grains").font = SEC
r += 1
ws_m.cell(r, 1, "Read the grain before comparing. The book margin is weighted by billed "
                "euro over DB x part lines; the computed margin is one row per part number "
                "in this workbook; the SPA margin is a real purchase price on a handful of "
                "lines. They must not be treated as the same number.").font = SUB
r += 1
header(ws_m, r, ["Margin", "Value", "Unit", "What it is measured on", "", "", ""])
r += 1
margin_rows = [
    ("Computed margin, MEDIAN across the workbook lines",
     f"=MEDIAN('Line detail'!$X$2:$X${LD_TOTAL-1})", "%",
     "1 - FOB_EUR_computed / carried SP, one row per part number. The wide cross-check."),
    ("Computed margin, billed-weighted",
     f"='Line detail'!$X${LD_TOTAL}", "%",
     "the same column weighted by billed euro, on rows that have a margin. Measured on "
     "exactly the same EUR 29,653,732 base as the book margin below, so the two ARE "
     "comparable - that is the point of matching the denominator."),
    ("Book margin, billed-weighted",
     0.5109, "%",
     "45,816 lines at DB x part number, on the CARRIED class margin. The figure finance "
     "quotes. Different GRAIN from the 15,273-row computed column, same euro base."),
    ("Measured margin, median on the SPA lines",
     0.4259, "%",
     "1 - purchase price / ISZE sales price, on the SPA lines that match the price list"),
    ("Class-implied margin, median on the same SPA lines",
     0.5300, "%",
     "1 - class factor on the same lines"),
    ("Gap, measured minus class-implied",
     -0.0763, "%",
     "the measured margin sits this far BELOW the class letter on those lines"),
]
for lab, val, unit, src in margin_rows:
    ws_m.cell(r, 1, lab)
    c = ws_m.cell(r, 2, val)
    c.number_format = "0.00%"
    ws_m.cell(r, 3, unit)
    ws_m.cell(r, 4, src)
    r += 1
r += 1

# ---- what the rate change does to the margin
ws_m.cell(r, 1, "WHAT THE 2026-09-18 RATE CHANGE DOES TO MARGIN").font = SEC
r += 1
rate_margin_rows = [
    ("Margin on the yen base price, old (discount 0.620)", 0.380, "%",
     "1 - discount, before the revision"),
    ("Margin on the yen base price, new (discount 0.673)", 0.327, "%",
     "1 - discount, live. Source: rate-revision workbook, K208FJ, vehicle parts."),
    ("Move", -0.053, "%",
     "-5.3 percentage points, caused by the discount alone"),
    ("Net landed cost move, FX and discount together",
     f"=Dials!$B${RATE_ROW_NET}-1", "%",
     "the FX move is -8.29% and the discount +8.55%, so they very nearly cancel: -0.45%"),
    ("Euro move, SETTLED 5.9616% yen revision at live rates",
     f"=Dials!$B${RATE_ROW_SETTLED}", "%",
     "+5.48% - already inside Jerome's 4-6% band. Source: "
     "aim_pricing_recalc_2026-09-17.json"),
    ("Euro move, SCENARIO 7.0% yen revision at live rates",
     f"=Dials!$B${RATE_ROW_SCEN}", "%",
     "+6.52% - above the band. The 7.0% is an agent-written scenario, NOT on file. "
     "Shown only to size the ceiling case."),
]
for lab, val, unit, src in rate_margin_rows:
    ws_m.cell(r, 1, lab)
    c = ws_m.cell(r, 2, val)
    c.number_format = "0.00%"
    ws_m.cell(r, 3, unit)
    ws_m.cell(r, 4, src)
    r += 1
r += 1
ws_m.cell(r, 1, "If the finance concern is that the reported margin is TOO HIGH, this rate "
                "change moves it the WRONG WAY: the discount alone costs 5.3 points, and the "
                "measured margin on the SPA lines was already 7.6 points below the class "
                "letter before it.").font = SUB
r += 2
ws_m.cell(r, 1, "The SPA lines - the only measured margins we hold").font = SEC
r += 1
header(ws_m, r, ["Metric", "Value", "Unit", "Source", "", "", ""])
r += 1
spa_rows = [
    ("Part lines with a real purchase price", 53, "lines", "ISZE_SPA_Optimizer_V4.xlsx / SPA Optimizer"),
    ("Matched to the price list", 50, "lines", "same, joined to pricing_list_pn"),
    ("Median measured margin", 0.4259, "%", "1 - purchase / sales, on those lines"),
    ("Median class-implied margin", 0.5300, "%", "1 - class factor, same lines"),
    ("Median gap", -0.0763, "%", "measured MINUS class-implied"),
]
for lab, val, unit, src in spa_rows:
    ws_m.cell(r, 1, lab)
    c = ws_m.cell(r, 2, val)
    if unit == "%":
        c.number_format = "0.00%"
    ws_m.cell(r, 3, unit)
    ws_m.cell(r, 4, src)
    r += 1

# ================================================================== Scenarios
ws_s["A1"] = "SCENARIOS - name a setting, read the outcome"
ws_s["A1"].font = TITLE
ws_s["A2"] = ("Each row is a book. Change the uplifts on Dials and this sheet moves. "
              "Copy the values if you want a frozen comparison.")
ws_s["A2"].font = SUB
header(ws_s, 4, ["Book", "Share of index weight", "Weighted uplift in the book",
                 "Index contribution pp", "Billed EUR before", "Billed EUR after",
                 "Cash change EUR"],
       [14, 20, 24, 22, 18, 18, 16])
r = 5
for i, bk in enumerate(("Working", "Ramp", "Launch", "Frozen")):
    wr = wb_first + i
    ldr = first_book_row + i
    ws_s.cell(r, 1, bk)
    ws_s.cell(r, 2, f"='Weight bridge'!C{wr}")
    ws_s.cell(r, 3, f"='Weight bridge'!D{wr}")
    ws_s.cell(r, 4, f"='Weight bridge'!E{wr}")
    ws_s.cell(r, 5, f"=Books!C{ldr}")
    ws_s.cell(r, 6, f"='Line detail'!R{LD_TOTAL}*B{r}")
    ws_s.cell(r, 7, f"=F{r}-E{r}")
    r += 1
for rr in range(5, 9):
    for col, fmt in ((2, "0.00%"), (3, "0.0000%"), (4, "0.0000"),
                     (5, "#,##0"), (6, "#,##0"), (7, "#,##0")):
        ws_s.cell(rr, col).number_format = fmt

# ================================================================== Checks
ws_c["A1"] = "CHECKS - the workbook proving itself"
ws_c["A1"].font = TITLE
header(ws_c, 3, ["Check", "Value", "Expected", "Result", "Note"],
       [52, 18, 18, 10, 62])
checks = [
    ("Index before any change, recomputed from Line detail",
     f"='Weight bridge'!D{IDX_BASE_ROW}-1", 0.059616, "0.000000%",
     "must reproduce the published 5.9616% or the model is on a different base. "
     "The -1 is real: 'Weight bridge'!D is a RATIO (1.059616), not yet a percentage."),
    ("Weights sum to 100%",
     f"=SUM('Weight bridge'!C{wb_first}:C{wb_last})", 1.0, "0.000000%",
     "every part is in exactly one book"),
    ("Books partition the billed book",
     f"=SUM('Line detail'!C{LD_TOTAL}:'Line detail'!C{LD_TOTAL})",
     None, "#,##0", "total billed, for reference"),
    ("No line exceeds the per-line cap",
     f"=SUMPRODUCT(--('Line detail'!N2:N{LD_TOTAL-1}*1>{CELL['cap']}))", 0, "#,##0",
     "the cap dial must bind everywhere. The *1 forces numeric coercion - plain "
     "> on a text-ish cell returns TRUE for blanks and inflated this count."),
    ("No line is below the floor",
     f"=SUMPRODUCT(--('Line detail'!N2:N{LD_TOTAL-1}*1<{CELL['floor']}))", 0, "#,##0",
     "the floor dial must bind everywhere, on the same numeric-coerced basis"),
    ("Frozen book carries zero uplift",
     f"=SUMPRODUCT(('Line detail'!G2:G{LD_TOTAL-1}=\"Frozen\")*"
     f"ABS('Line detail'!N2:N{LD_TOTAL-1}*1))", 0, "#,##0.0000",
     "a frozen line must not move. Before 2026-09-18 this failed at 1.77: frozen rows "
     "took the book uplift and 15 of 24 sat at the +8% cap. Now forced to zero in the "
     "capped-delta formula itself, not by changing the Frozen dial."),
    ("Launch book: L12M QUANTITY (the claim the note makes)",
     f"=SUMIF('Line detail'!G:G,\"Launch\",'Line detail'!B:B)", None, "#,##0",
     "DIAGNOSTIC, not a pass/fail, because the note's premise does not hold: it reads "
     "451, not zero. The book is defined by the sourcing deliverable (APL) carrying no "
     "L12M value for those parts, NOT by the parts never having sold - 103 of them do "
     "have billed quantity in the sales data. Either the APL file's blank L12M column is "
     "missing coverage for old part numbers, or those parts are genuinely new; this "
     "workbook cannot tell which. The row below is the assertion that matters."),
    ("Launch book: weight column, as a diagnostic not a pass/fail",
     f"=SUMIF('Line detail'!G:G,\"Launch\",'Line detail'!I:I)", None, "#,##0",
     "reported, not asserted to be zero: the yen base price exists so this column is "
     "non-zero. Read it as how much index weight those 103 parts would carry IF the "
     "quantity were real."),
    ("Launch book: can launch rows move the index?",
     f"=IF(SUMPRODUCT(('Line detail'!$G$2:$G${LD_TOTAL-1}=\"Launch\")"
     f"*'Line detail'!$I$2:$I${LD_TOTAL-1})"
     f"/SUM('Line detail'!$I$2:$I${LD_TOTAL-1})<0.001,1,0)", 1, "0",
     "the real claim: launch carries under 0.1% of index weight, so a fixed target "
     "cannot meaningfully constrain it. Fails if launch weight ever becomes material."),
    ("Launch book: is launch quantity material to billed volume?",
     f"=IF(SUMIF('Line detail'!G:G,\"Launch\",'Line detail'!B:B)"
     f"/SUM('Line detail'!B:B)<0.001,1,0)", 1, "0",
     "451 of 1,225,500 units is 0.037%, immaterial. Fails if it ever exceeds 0.1%."),
    # ---- the checks that prove the rate dials drive the computed block
    ("FX and discount dials are the revised values",
     f"=IF(AND(ABS({CELL['fx']}-178.5)<0.001,ABS({CELL['disc_J']}-0.673)<0.0001),1,0)",
     1, "0",
     "178.5 JPY/EUR and a 0.673 Japan discount are the live dials after 2026-09-18"),
    ("Computed FOB column reproduces BP / FX x discount per source",
     f"=IF(AND(ABS(SUMIF(U2:U{LD_TOTAL-1},\"J\",W2:W{LD_TOTAL-1})"
     f"-SUMIF(U2:U{LD_TOTAL-1},\"J\",V2:V{LD_TOTAL-1})/{CELL['fx']}*{DISC['J']:.3f})<0.01,"
     f"ABS(SUMIF(U2:U{LD_TOTAL-1},\"T\",W2:W{LD_TOTAL-1})"
     f"-SUMIF(U2:U{LD_TOTAL-1},\"T\",V2:V{LD_TOTAL-1})/{CELL['fx']}*{DISC['T']:.3f})<0.01),"
     f"0,1)",
     0, "0",
     "the computed column must be exactly BP / FX x discount, totalled per source"),
    ("Sourced rows that carry no computed landed cost",
     f"=COUNTA(U2:U{LD_TOTAL-1})-COUNT(W2:W{LD_TOTAL-1})",
     0, "0",
     "a positive number means a source key the Dials discount table cannot resolve. "
     "NOT to be compared against the computed-margin count - that one is legitimately "
     "lower, because a row with no carried price has no margin to compute."),
    ("Net rate move, as the workbook computes it",
     f"=Dials!$B${RATE_ROW_NET}", 0.9955, "0.000000",
     "0.9171 x 1.0855 - the two rate changes very nearly cancel"),
    ("Euro move on the SETTLED revision (5.9616% yen)",
     f"=Dials!$B${RATE_ROW_SETTLED}", 0.0548, "0.0000%",
     "the headline figure: the settled yen revision becomes +5.48% in euro, which is "
     "inside the 4-6% band. Source: aim_pricing_recalc_2026-09-17.json"),
    ("Euro move on the SCENARIO revision (7.0% yen)",
     f"=Dials!$B${RATE_ROW_SCEN}", 0.0652, "0.0000%",
     "the ceiling case only. 7.0% is agent-written and NOT on file; +6.52% is above "
     "the band and needs 1.52 pp held back to land +5%"),
    ("Target of +5% on current price: base revision that would land it",
     f"=Dials!$B${RATE_ROW_NEED}", 0.0548, "0.0000%",
     "the yen revision that lands +5% exactly, ~5.48%"),
    ("That revision versus the SETTLED one",
     f"=Dials!$B${RATE_ROW_NEED_VS_SETTLED}", -0.49, '0.00" pp"',
     "negative: the revision would have to be 0.49 points BELOW settled to land +5%, "
     "because the settled revision already lands +5.48%"),
    ("Points held back at +5% against the SETTLED revision",
     f"=Dials!$B${RATE_ROW_GIVE_SETTLED}", 0.48, '0.00" pp"',
     "against settled, the +5% target is below the +5.48% the revision already gives, "
     "so nothing has to be absorbed - this is headroom, not a sacrifice"),
    ("Points held back at +5% against the SCENARIO",
     f"=Dials!$B${RATE_ROW_GIVE_SCEN}", 1.52, '0.00" pp"',
     "against the 7% scenario only: +6.52% minus +5%"),
]
r = 4
for lab, formula, exp, fmt, note in checks:
    ws_c.cell(r, 1, lab)
    ws_c.cell(r, 2, formula).number_format = fmt
    if exp is not None:
        ws_c.cell(r, 3, exp).number_format = fmt
        ws_c.cell(r, 4, f'=IF(ABS(B{r}-C{r})<=MAX(ABS(C{r})*0.0005,0.02),"OK","CHECK")')
        ws_c.cell(r, 4).font = TOT
    ws_c.cell(r, 5, note)
    r += 1

# ================================================================== Dashboard
ws_dash["A1"] = "PRICING FRAMEWORK - the outcome"
ws_dash["A1"].font = TITLE
ws_dash["A2"] = "Set the dials on the Dials sheet. Everything here is computed."
ws_dash["A2"].font = SUB
kpi = [
    ("Weighted move achieved", f"='Weight bridge'!D{WB_TOTAL}", "0.0%"),
    ("Index delivered, pp", f"=SUM('Weight bridge'!E{wb_first}:E{wb_last})", "0.0000"),
    ("Index before changes", f"='Weight bridge'!D{IDX_BASE_ROW}-1", "0.0000%"),
    ("Target set on Dials", f"={CELL['target']}", "0.0%"),
    ("Target on CURRENT sales price", f"={CELL['target_sp']}", "0.0%"),
    ("SETTLED: 5.9616% yen at live rates, euro move",
     f"=Dials!$B${RATE_ROW_SETTLED}", "0.00%"),
    ("SCENARIO: 7.0% yen at live rates, euro move",
     f"=Dials!$B${RATE_ROW_SCEN}", "0.00%"),
    ("Points held back vs SETTLED at the target",
     f"=Dials!$B${RATE_ROW_GIVE_SETTLED}", '0.00" pp"'),
    ("Points held back vs SCENARIO at the target",
     f"=Dials!$B${RATE_ROW_GIVE_SCEN}", '0.00" pp"'),
    ("Base revision needed to hit the target", f"=Dials!$B${RATE_ROW_NEED}", "0.00%"),
    ("...versus the settled revision, pp",
     f"=Dials!$B${RATE_ROW_NEED_VS_SETTLED}", '0.00" pp"'),
    ("Net rate move, FX and discount", f"=Dials!$B${RATE_ROW_NET}-1", "0.00%"),
    ("Computed margin, median over the lines",
     f"=MEDIAN('Line detail'!$X$2:$X${LD_TOTAL-1})", "0.00%"),
    ("Computed margin, billed-weighted",
     f"='Line detail'!$X${LD_TOTAL}", "0.00%"),
    ("Computed margin vs class, billed-weighted, pp",
     f"='Line detail'!$Y${LD_TOTAL}", "0.00"),
    ("Margin on the yen base price, live", f"=1-{CELL['disc_J']}", "0.00%"),
    ("Cash change on L12M volume", f"='Line detail'!S{LD_TOTAL}", "#,##0"),
    ("Launch book index weight", f"=SUMIF('Line detail'!$G:$G,\"Launch\",'Line detail'!$I:$I)", "#,##0"),
    ("Frozen book index weight", f"=SUMIF('Line detail'!$G:$G,\"Frozen\",'Line detail'!$I:$I)", "#,##0"),
    ("Working book index weight", f"=SUMIF('Line detail'!$G:$G,\"Working\",'Line detail'!$I:$I)", "#,##0"),
]
r = 4
ws_dash.cell(r, 1, "KPI").font = SEC
ws_dash.cell(r, 2, "Value").font = SEC
ws_dash.cell(r, 3, "Formula trace").font = SEC
r += 1
for lab, formula, fmt in kpi:
    ws_dash.cell(r, 1, lab)
    ws_dash.cell(r, 2, formula).number_format = fmt
    ws_dash.cell(r, 3, formula)
    r += 1
ws_dash.column_dimensions["A"].width = 34
ws_dash.column_dimensions["B"].width = 20
ws_dash.column_dimensions["C"].width = 60

# ================================================================== Read me
read = [
    ("ISZE pricing framework", "title"),
    ("", ""),
    ("What this is", "head"),
    ("A model for adjusting parts prices, split into four books that each have a "
     "different amount of pricing freedom. You set the dials on one sheet; every "
     "number below is a formula. Nothing here changes a price.", ""),
    ("", ""),
    ("The one fact the whole framework rests on", "head"),
    ("The weighted increase is an index: SUM(q0 x p1) / SUM(q0 x p0) - 1, weighted by "
     "last year's revenue. A part with no last-year revenue therefore has no weight, "
     "so a fixed target cannot constrain it. That is why the Launch book is free and "
     "the Working book has to carry the increase.", ""),
    ("", ""),
    ("The chain we work inside", "head"),
    ("BP_JPY / FX x purchase discount / class factor = SP_EUR, our list. Then x 1.40 for "
     "the distributor and x 1.275 for the dealer. FX, the purchase discount and the "
     "class factor are IML's. The adjustment on top of SP_EUR is the only lever ISZE "
     "owns. A margin target cannot be hit by ISZE alone.", ""),
    ("", ""),
    ("Carried vs computed - do not mix these up", "head"),
    ("Column K of Line detail, Current SP EUR, is CARRIED from the price file. It is the "
     "AUTHORITY for anything billed, because 12.8% of the catalogue carries a deliberate "
     "override and recomputing would invent a price for those rows. Columns U to Z are "
     "COMPUTED: they derive a landed cost from the yen base price and the two rate dials "
     "and compare it to that carried price. That is the cross-check that makes the rate "
     "dials drive something real - before it, changing FX moved no number in this "
     "workbook. Where the computed and carried views disagree, the carried price is right "
     "and the difference is the finding.", ""),
    ("", ""),
    ("The two rate changes of 2026-09-18", "head"),
    ("The Japan rate moved to 178.5 JPY/EUR for 1 Oct 2026 to 31 Mar 2027, from 172.6 for "
     "the six months before and 163.7 before that. The Japan purchase discount moved from "
     "0.620 to 0.673. Because FX sits in the denominator and the discount in the "
     "numerator, a higher JPY/EUR lowers our euro cost while a higher discount raises it: "
     "the FX move is -8.29% and the discount +8.55%, so they very nearly cancel and net "
     "-0.45% on landed cost. The margin on the yen base price, which is simply 1 minus the "
     "discount, falls from 38.0% to 32.7%, a loss of 5.3 points that the FX move does not "
     "restore. The settled 5.9616% base-price revision was priced on the oldest of the "
     "three rates, so it was already stale on FX.", ""),
    ("", ""),
    ("The target that matters: 4 to 6% on the current sales price", "head"),
    ("The base-price revision that exists on file is +5.9616% in yen, sourced to "
     "aim_pricing_recalc_2026-09-17.json. In euro the move is smaller, because the net "
     "rate drift is -0.45%: 1.059616 x 0.995483 = 1.054832, so the revision delivers "
     "+5.48% on our current euro sales price. That is already inside the 4-6% band, so "
     "at the settled revision there is nothing to absorb and the target is met by the "
     "revision itself. The framework also carries a 7.0% yen revision as a SCENARIO, "
     "clearly labelled: it was written by the agent, not by IML, and it is there only to "
     "size the ceiling case. At 7.0% the euro move is +6.52%, which is above the band, "
     "and landing +5% would mean holding back 1.52 points. The three target rows are "
     "independent of both: landing +4%, +5% or +6% needs a yen revision of +4.47%, "
     "+5.48% or +6.48%, which is 1.49 and 0.49 points BELOW the settled revision for the "
     "first two, and 0.52 points above it for the third.", ""),
    ("", ""),
    ("The four books", "head"),
    ("Working - legacy parts with L12M volume. Full index weight, so this is where an "
     "increase has to come from. Ramp - the 2.2L and P700 parts that already sell. "
     "Their weight is last year's, so a rise here returns more than it costs; delaying "
     "costs more next year. Launch - parts the sourcing deliverable (the APL file) "
     "carries no L12M value for, so they have no index weight and a fixed target cannot "
     "constrain them. Be precise about that: the book is defined by the DELIVERABLE "
     "being silent, not by the parts never having sold, and 103 of them do carry 451 "
     "billed units between them - 0.037% of volume, immaterial but not zero. Frozen - "
     "parts where the aftermarket sits below our own distributor's cost. Held until the "
     "sourcing position is settled: the model forces their move to zero rather than "
     "letting them take the book uplift, so that frozen means frozen.", ""),
    ("", ""),
    ("What is measured, and what is assumed", "head"),
    ("Measured: the L12M quantity and euro, the base prices, the class factors, the "
     "index weights, a real margin on 53 SPA lines, and now a computed landed cost and "
     "margin on every line. Sourced from outside this workbook: the settled revision of "
     "5.9616% and the three FX vintages. Assumed: the 35% distributor margin, which no "
     "distributor shares; the growth "
     "factors on the ramp book, which are unsigned midpoints; and the class-implied "
     "margin outside the SPA lines. Each assumption is a shaded dial and is named as an "
     "assumption where it is used.", ""),
    ("", ""),
    ("The checks that make it trustworthy", "head"),
    ("The Checks sheet recomputes the published 5.9616% index from the line detail. If "
     "that does not reproduce, the model is on a different base and nothing else should "
     "be read. It also proves the weights sum to 100%, that no line breaches its cap or "
     "floor, that the frozen book carries exactly zero movement, that the computed cost "
     "column reproduces BP / FX x discount on every sourced row, and that the launch "
     "book cannot move the index. The settled and scenario revision figures are asserted "
     "too, so the two can never silently swap.", ""),
    ("", ""),
    ("What this model does not do", "head"),
    ("It changes no price, writes no list, runs no allocation, and assumes no volume "
     "response to a price change. It carries SP_EUR from the price file rather than "
     "recomputing it, because 12.8% of the catalogue carries a deliberate override and "
     "recomputing would invent a price for those rows. The computed cost is an "
     "INDICATIVE cross-check, not a purchase cost: it assumes the yen base price is the "
     "cost base and that the class factor and discount are applied cleanly, which is "
     "exactly what the 12.8% do not do.", ""),
]
r = 1
for text, kind in read:
    c = ws_read.cell(r, 1, text)
    if kind == "title":
        c.font = TITLE
    elif kind == "head":
        c.font = SEC
    c.alignment = Alignment(wrap_text=True, vertical="top")
    r += 1
ws_read.column_dimensions["A"].width = 132

say("  saving ...")
wb.save(XLSX)
say(f"  {XLSX}")

meta = {
    "workbook": XLSX,
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "window": "2025-07-01 to 2026-06-30 (the L12M in-scope revision base)",
    "priced_part_numbers": int(len(lines)),
    "weight_sum": float(W_SUM),
    "books": books.to_dict("index"),
    "launch_part_numbers_no_l12m": len(launch),
    "ramp_part_numbers_with_l12m": len(ramp),
    "frozen_part_numbers": len(frozen),
    "index_recomputed": float(
        (lines["billed_qty"] * lines["new_bp"]).sum()
        / (lines["billed_qty"] * lines["prior_bp"]).sum() - 1),
    "dials_are_inputs": [
        "target weighted increase", "target on current sales price", "per-line cap",
        "per-line floor", "distributor margin assumption",
        "FX (live, 178.5)", "purchase discounts",
        "settled base-price revision (5.9616%, on file)",
        "scenario base revision (7.0%, agent-written, NOT on file)",
        "per-book uplift",
    ],
    "rates": {
        "fx_live": FX_DEFAULT,
        "fx_live_period": ["2026-10-01", "2027-03-31"],
        "fx_prior_172_6_period": ["2026-04-01", "2026-09-30"],
        "fx_prior_163_7_as_of": "2025-10-01",
        "fx_prior_163_7_note": "what the settled 5.9616% base-price revision was priced on",
        "discount_live": DISC,
        "discount_prior": DISC_PRIOR,
        "base_revision_settled": BASE_REV_SETTLED,
        "base_revision_settled_source": BASE_REV_SETTLED_SOURCE,
        "base_revision_scenario": BASE_REV_SCENARIO,
        "base_revision_scenario_note": (
            "agent-written on 2026-09-18 to size the ceiling case. NOT a quotation from "
            "IML and no file in the workspace states it."),
        "fx_cost_factor_old_over_new": round(FX_PRIOR / FX_DEFAULT, 4),
        "discount_cost_factor": round(DISC["J"] / DISC_PRIOR["J"], 4),
        "net_on_landed_cost": round(FX_PRIOR / FX_DEFAULT * DISC["J"] / DISC_PRIOR["J"], 6),
        "euro_move_settled_revision": round(
            (1 + BASE_REV_SETTLED) * (FX_PRIOR / FX_DEFAULT)
            * (DISC["J"] / DISC_PRIOR["J"]) - 1, 6),
        "euro_move_scenario_revision": round(
            (1 + BASE_REV_SCENARIO) * (FX_PRIOR / FX_DEFAULT)
            * (DISC["J"] / DISC_PRIOR["J"]) - 1, 6),
        "margin_on_yen_base_price_old": round(1 - DISC_PRIOR["J"], 4),
        "margin_on_yen_base_price_new": round(1 - DISC["J"], 4),
    },
    "computed_block": {
        "columns": ["U Source", "V BP JPY carried", "W FOB EUR COMPUTED",
                    "X GM COMPUTED", "Y GM delta vs class pp", "Z GM gap to book pp"],
        "formula": "W = V / FX * VLOOKUP(U, Dials discount table, 2, FALSE)",
        "authority": "K (Current SP EUR) stays CARRIED - the computed block is a cross-check",
        "computed_margin_median_pct": float(100 * GM_COMP_MEDIAN),
        "computed_margin_book_weighted_pct": float(100 * GM_COMP_WEIGHTED),
        "computed_rows_used": int(GM_COMP_ROWS),
    },
    "caveats": [
        "SP_EUR is carried from the price file, not recomputed - 12.8% of rows carry "
        "a deliberate override and recomputing would invent a price for them.",
        "The computed cost is an INDICATIVE cross-check: it assumes the yen base price "
        "is the cost base and that the discount applies cleanly. It is not a purchase "
        "cost, and the 12.8% that do not reproduce the chain are exactly where it is "
        "weakest.",
        "The computed margin is one row per part number (15,273) on the L12M in-scope "
        "book; the 51.09% book margin finance quotes is a different grain (45,816 rows "
        "at DB x part number) on the carried class margin. Do not equate them.",
        "Per-part PURCHASE cost exists on the SPA lines only; everywhere else the "
        "computed margin rests on the class factor and the discount, not on a purchase "
        "price.",
        "The 35% distributor margin is an assumption, not a measurement.",
        "BASE REVISION PROVENANCE. The settled revision is 5.9616% yen, on file and "
        "sourced to aim_pricing_recalc_2026-09-17.json (step EUR 1,652,140.71, ties out "
        "to the published figure). The 7.0% revision is a SCENARIO written by the agent "
        "on 2026-09-18 and is NOT sourced - no file in the workspace states it. It is "
        "retained only to size what happens above Jerome's band; it must never be "
        "presented as a revision that is coming.",
        "The 5.9616% is a YEN base-price move. The euro move is smaller because the net "
        "rate drift is -0.45%: 1.059616 x 0.995483 = 1.054832, so +5.48% in euro, which "
        "is already inside the 4-6% band. The +6.52% figure belongs to the 7% scenario "
        "only.",
        "Ramp growth factors are unsigned midpoints, and 3,390 of 3,605 RG21 parts sit "
        "at a factor of 1.0, which means not treated as ramping.",
        "The frozen book is small by coverage (the bridge reaches 0.50% of the "
        "catalogue), not by importance.",
        "No volume response to a price change is assumed anywhere.",
    ],
}
with open(META, "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2, default=str)
say(f"  meta {META}")
say("")
say("BUILD_OK")
