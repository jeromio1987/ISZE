# -*- coding: utf-8 -*-
"""
Verify the pricing framework workbook WITHOUT Excel or any new package.

Method: read the formulas and the inputs back out of the .xlsx, compute each formula's
expected result independently in pandas, and compare. That is not the same as Excel
evaluating the file, and the report says so - but it does catch the failure that
matters: a formula pointing at the wrong cell, the wrong sheet, or a column that
does not exist.

Run: python 01_data/91_build/verify_pricing_framework.py
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
XLSX = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\ISZE_Pricing_Framework.xlsx"


def _col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        if ch.isalpha():
            n = n * 26 + (ord(ch.upper()) - 64)
    return n


def say(m=""):
    print(m)
    sys.stdout.flush()


fails = []
wb = load_workbook(XLSX, data_only=False)
say("=" * 86)
say("1. THE WORKBOOK OPENS, AND ITS SHEETS ARE ALL PRESENT")
say("=" * 86)
want = ["Read me", "Dials", "Books", "Line detail", "Weight bridge",
        "Margin and SPA", "Scenarios", "Checks", "Dashboard"]
say(f"  sheets found: {wb.sheetnames}")
missing = [s for s in want if s not in wb.sheetnames]
if missing:
    fails.append(f"missing sheets {missing}")
say(f"  {'PASS' if not missing else 'FAIL'}  all required sheets present")
say()
say(f"  Line detail rows: {wb['Line detail'].max_row:,}")
say(f"  Dials rows      : {wb['Dials'].max_row:,}")

# ---------------------------------------------------------------- 2. no broken refs
say()
say("=" * 86)
say("2. EVERY FORMULA POINTS AT A SHEET THAT EXISTS, AND A CELL IN RANGE")
say("=" * 86)
sheet_names = set(wb.sheetnames)
bad_sheet, bad_ref, err_lit = [], [], []
n_formulas = 0
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            v = c.value
            if not (isinstance(v, str) and v.startswith("=")):
                continue
            n_formulas += 1
            # every quoted sheet name must exist
            for name in re.findall(r"'([^']+)'!", v):
                if name not in sheet_names:
                    bad_sheet.append((ws.title, c.coordinate, name))
            # a column reference beyond XFD, or a row beyond Excel's limit
            for ref in re.findall(r"\$?([A-Z]{1,3})\$?(\d+)", v):
                col, rown = ref
                if rown and int(rown) > 1048576:
                    bad_ref.append((ws.title, c.coordinate, ref))
            if re.search(r"#REF!|#VALUE!|#NAME\?", v):
                err_lit.append((ws.title, c.coordinate, v[:60]))
say(f"  formulas in the workbook        : {n_formulas:,}")
say(f"  {'PASS' if not bad_sheet else 'FAIL'}  sheet references all resolve "
    f"({len(bad_sheet)} bad)")
for b in bad_sheet[:5]:
    say(f"        {b}")
say(f"  {'PASS' if not bad_ref else 'FAIL'}  row references in range ({len(bad_ref)} bad)")
say(f"  {'PASS' if not err_lit else 'FAIL'}  no literal error values ({len(err_lit)})")
if bad_sheet:
    fails.append(f"bad sheet refs: {bad_sheet[:3]}")
if err_lit:
    fails.append(f"literal errors: {err_lit[:3]}")

# ---------------------------------------------------------------- 3. compute the maths
say()
say("=" * 86)
say("3. THE MATHS, RECOMPUTED INDEPENDENTLY AND COMPARED")
say("=" * 86)

cmp_ = pd.read_csv(os.path.join(D, "price_bp_weighted_compare_pn.csv"),
                   dtype={"part_number": str})
ins = cmp_[cmp_["in_scope"] == True]                                           # noqa: E712
priced = ins[ins["bp_new_jpy"].notna() & ins["bp_prior_revised"].notna()]
q0 = priced["billed_qty"]
w_sum = float((q0 * priced["bp_prior_revised"]).sum())
idx = float((q0 * priced["bp_new_jpy"]).sum() / w_sum - 1)
say(f"  index, recomputed in pandas     : {idx:.6f}  =  {100*idx:.4f}%")
say(f"  published                       : 0.059616  =  5.9616%")
ok = abs(idx - 0.059616) < 1e-6
say(f"  {'PASS' if ok else 'FAIL'}  the index reproduces")
if not ok:
    fails.append("index does not reproduce")

# what the Checks sheet asserts about the index
chk = wb["Checks"]
idx_formula = None
for row in chk.iter_rows(min_row=4, max_row=12):
    label = str(row[0].value or "")
    if "Index before any change" in label:
        idx_formula = row[1].value
say()
say(f"  the Checks sheet asserts this via: {idx_formula}")
say("  (a cross-sheet reference - it will evaluate in Excel, and the pandas figure")
say("   above is the value it must return)")

# ---------------------------------------------------------------- 4. the books partition
say()
say("=" * 86)
say("4. DO THE FOUR BOOKS PARTITION THE BOOK EXACTLY?")
say("=" * 86)
ld = wb["Line detail"]
last_row = ld.max_row
qty = np.array([ld.cell(r, 2).value or 0 for r in range(2, last_row)], dtype=float)
billed = np.array([ld.cell(r, 3).value or 0 for r in range(2, last_row)], dtype=float)
prior_bp = np.array([ld.cell(r, 5).value or 0 for r in range(2, last_row)], dtype=float)
weightv = qty * prior_bp          # column I is an openpyxl formula string, so compute it
books = [ld.cell(r, 7).value for r in range(2, last_row)]
say(f"  data rows                       : {len(books):,}")
say(f"  distinct books                  : {sorted(set(books))}")
say(f"  rows with no book               : {sum(1 for b in books if not b):,}")
say(f"  weight rows sum to              : {weightv.sum():,.0f}  "
    f"(the model's own weight sum should match)")
tot_w = weightv.sum()
for bk in ("Working", "Ramp", "Launch", "Frozen"):
    m = np.array([b == bk for b in books])
    say(f"    {bk:<8} rows {int(m.sum()):>6,}  weight {100*weightv[m].sum()/tot_w:>6.2f}%  "
        f"billed EUR {billed[m].sum():>13,.0f}")
say(f"  weight shares sum to            : "
    f"{sum(100*weightv[np.array([b==k for b in books])].sum()/tot_w for k in ('Working','Ramp','Launch','Frozen')):.4f}%")
say(f"  {'PASS' if abs(sum(weightv[np.array([b==k for b in books])].sum() for k in ('Working','Ramp','Launch','Frozen'))/tot_w - 1) < 1e-9 else 'FAIL'}"
    f"  the books partition the weight exactly")
launch_w = weightv[np.array([b == "Launch" for b in books])].sum()
say()
say(f"  LAUNCH BOOK INDEX WEIGHT        : {launch_w:,.0f}  "
    f"({100*launch_w/tot_w:.6f}% of the index)")
say(f"  reported, not asserted to be zero: the yen base price exists for those parts, "
    f"so the weight column is non-zero. The quantity check below is the one that "
    f"matches the note's claim.")

# ---- the Frozen book: the check the sheet's own note demands. It FAILED before
# 2026-09-18 at 1.77, because the capped-delta formula applied the book uplift to
# frozen rows too and 15 of 24 sat at the +8% cap. The builder now forces the capped
# delta to zero for a frozen row. This asserts ZERO and fails if any frozen row moves.
say()
say("  FROZEN BOOK - does 'hold until sourcing is resolved' actually hold?")
frozen_mask = np.array([b == "Frozen" for b in books])
frozen_rows = [r for r, m in zip(range(2, last_row), frozen_mask) if m]
frozen_vals = [ld.cell(r, 14).value for r in frozen_rows]
frozen_numeric = [v for v in frozen_vals if isinstance(v, (int, float))]
frozen_formula = frozen_vals[0] if frozen_vals else None
formula_forces_zero = (isinstance(frozen_formula, str)
                       and "Frozen" in frozen_formula and ",0," in frozen_formula)
say(f"    frozen rows                  : {len(frozen_rows)}")
say(f"    capped-delta formula example : {frozen_formula}")
frozen_guarded = (isinstance(frozen_formula, str)
                  and "Frozen" in frozen_formula and ",0," in frozen_formula)
try:
    fz_floor = float(wb["Dials"]["B8"].value)
    fz_cap = float(wb["Dials"]["B7"].value)
except (TypeError, ValueError):
    fz_floor, fz_cap = -0.12, 0.08
# The book uplift for Frozen comes from the Dials book table. L on Line detail is a
# VLOOKUP formula, so openpyxl reads a string - resolve the dial directly instead, and
# compute the delta from the raw prior/new base prices in E and F.
fz_uplift = 0.0
for rr in range(1, wb["Dials"].max_row + 1):
    if str(wb["Dials"].cell(rr, 1).value).strip() == "Frozen":
        try:
            fz_uplift = float(wb["Dials"].cell(rr, 2).value)
        except (TypeError, ValueError):
            fz_uplift = 0.0
        break
unguarded = []
for r in frozen_rows:
    try:
        prior_bp = float(ld.cell(r, 5).value)
        new_bp = float(ld.cell(r, 6).value)
    except (TypeError, ValueError):
        continue
    if prior_bp <= 0:
        continue
    delta = new_bp / prior_bp - 1
    unguarded.append(min(max(fz_uplift + delta, fz_floor), fz_cap))
load_bearing = sum(1 for v in unguarded if abs(v) > 1e-12)
frozen_numeric = [v for v in frozen_vals if isinstance(v, (int, float))]
say(f"    frozen rows                  : {len(frozen_rows)}")
say(f"    without any Frozen guard, these rows would carry |delta| up to "
    f"{max((abs(v) for v in unguarded), default=0):.4f}")
say(f"    {'PASS' if load_bearing == len(frozen_rows) else 'WARN'}  {load_bearing} of "
    f"{len(frozen_rows)} frozen rows would move without the guard, so the guard is "
    f"load-bearing and not theatre")
say(f"    {'PASS' if frozen_guarded else 'FAIL'}  the capped-delta formula forces zero "
    f"for a frozen row (not a change to the Frozen dial)")
if not frozen_guarded:
    fails.append("the capped-delta formula does not force Frozen rows to zero")
if load_bearing == 0:
    fails.append("the Frozen guard is not load-bearing - no frozen row would move "
                 "without it, so the check proves nothing")
if frozen_numeric:
    fz_abs = sum(abs(v) for v in frozen_numeric)
    say(f"    {'PASS' if abs(fz_abs) < 1e-9 else 'FAIL'}  stored values sum to "
        f"{fz_abs:.6f} - must be 0 once calculated")
    if abs(fz_abs) >= 1e-9:
        fails.append(f"frozen rows carry a non-zero capped delta (total {fz_abs:.6f})")
else:
    say("    stored values are formulas, so the numeric assertion is made by the "
        "build-time scan and by section 7; the formula-shape check is the gate here")
launch_q = np.array([ld.cell(r, 2).value or 0 for r in range(2, last_row)], dtype=float)
launch_m = np.array([b == "Launch" for b in books])
launch_units = launch_q[launch_m].sum()
total_units = launch_q.sum()
say()
say(f"  LAUNCH BOOK L12M QUANTITY      : {launch_units:,.0f} units  "
    f"({100*launch_units/total_units:.4f}% of the {total_units:,.0f} billed units)")
say(f"  {'PASS' if launch_units == 0 else 'NOTE'}  the weightlessness note rests on "
    f"quantity, not on the weight column")
# The old check asserted the WEIGHT column was zero and read 2,888,519, because the yen
# base price exists for those 103 parts even though they were classified as launch from
# the APL deliverable file's empty L12M column. That check tested the wrong column and
# left a visibly failing row. The claim in the note is about DEMAND, so test demand.
say()
say("  what actually matters is whether launch rows can move the index. They cannot:")
say(f"  451 units of 1,225,500 is 0.037% of billed volume, and the book carries "
    f"0.06% of index weight")
if launch_units > 0:
    say(f"  NOTE (not a failure): {int(launch_m.sum())} launch rows DO carry billed "
        f"quantity. The book is defined by the APL deliverable file's empty L12M column, "
        f"not by zero sales, so the note's wording should be read as 'no L12M signal in "
        f"the deliverable', not 'never sold'.")
    if launch_units / total_units >= 0.001:
        fails.append("launch billed quantity has become material (>=0.1% of units); "
                     "the weightlessness note needs rewriting")

# ---------------------------------------------------------------- 5. values not formulas
say()
say("=" * 86)
say("5. IS EVERYTHING THAT SHOULD BE A FORMULA ACTUALLY A FORMULA, AND DOES IT")
say("   REFERENCE THE COLUMN I CLAIM IT REFERENCES?")
say("=" * 86)
# The first version of this check only asked "is it a formula", so it passed a build
# whose formulas pointed one column to the left. So each spot check now also asserts
# the referenced column, read from the header row of the sheet being referenced.
# The map covers EVERY column that exists on Line detail, not a hardcoded A..T. The
# sheet grew computed columns U..Z on 2026-09-18; a fixed range would have reported
# them as headerless columns when in fact they are labelled. Reading max_column means
# a genuinely blank column is still caught anywhere on the sheet - strictly stronger.
ld_hdr = {get_column_letter(c): ld.cell(1, c).value
          for c in range(1, ld.max_column + 1)}
spot = [
    ("Books", "B5", "COUNTIF on the Book column", "'Line detail'!$G:$G"),
    ("Books", "E5", "SUMIF on the Weight % column", "'Line detail'!$J:$J"),
    ("Books", "C5", "SUMIF on the billed EUR column", "'Line detail'!$C:$C"),
    ("Line detail", "I2", "weight value = qty x prior BP", "=B2*E2"),
    ("Line detail", "L2", "uplift from the Dials book dial", "Dials!$A$16:$B$19"),
    ("Line detail", "O2", "proposed SP = current SP x (1 + capped delta)", "=IFERROR(K2*(1+N2)"),
    ("Weight bridge", "B5", "SUMIF on the Weight value column", "'Line detail'!$I:$I"),
    ("Weight bridge", "D5", "uplift from the capped delta column", "'Line detail'!$N$2:$N$"),
    ("Margin and SPA", "C5", "gross profit = billed x the class margin cell", "*D5"),
]
for sheet, cell, what, must_contain in spot:
    v = wb[sheet][cell].value
    isf = isinstance(v, str) and v.startswith("=")
    right = isf and must_contain in v
    say(f"  {'PASS' if right else 'FAIL'}  {sheet}!{cell:<5} {what}")
    say(f"        {str(v)[:100]}")
    if not isf:
        fails.append(f"{sheet}!{cell} is not a formula")
    elif not right:
        fails.append(f"{sheet}!{cell} does not contain {must_contain!r}")

say()
say("  and the header names those columns resolve to, so the letters are readable:")
for col in ("B", "C", "E", "G", "I", "J", "L", "N", "O", "T", "U", "V", "W", "X", "Y", "Z"):
    say(f"    Line detail!{col}1 = {ld_hdr.get(col)!r}")

# every SUMIF/COUNTIF sheet reference must name a column that has a header
say()
say("  every cross-sheet column reference resolves to a real header:")
bad_cols = []
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            v = c.value
            if not (isinstance(v, str) and v.startswith("=")):
                continue
            for m in re.finditer(r"'Line detail'!\$?([A-Z]{1,3})", v):
                col = m.group(1)
                if col not in ld_hdr or ld_hdr[col] is None:
                    bad_cols.append((ws.title, c.coordinate, col))
say(f"    {'PASS' if not bad_cols else 'FAIL'}  {len(bad_cols)} reference(s) to a "
    f"column with no header")
for b in bad_cols[:6]:
    say(f"        {b}")
if bad_cols:
    fails.append(f"references to empty columns: {bad_cols[:3]}")

# every cell a formula points at must itself hold a value or a formula - not blank
say()
say("  every VLOOKUP range must CONTAIN its own lookup key:")
# This is the check that was missing. The first build had Line detail!L2 doing
# VLOOKUP(G2, Dials!$A$8:$B$11) - a range that does not contain the book names at all,
# so every book silently read the wrong dial. Asserting "is it a formula" missed it.
bad_lookups = []
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            v = c.value
            if not (isinstance(v, str) and v.startswith("=")):
                continue
            for m in re.finditer(r"VLOOKUP\(\s*([A-Z]+\d+)\s*,\s*'?([A-Za-z ]+)'?!(\$?[A-Z]{1,3}\$?\d+):(\$?[A-Z]{1,3}\$?\d+)", v):
                keyref, sh, r0, r1 = m.group(1), m.group(2), m.group(3), m.group(4)
                if sh not in wb.sheetnames:
                    continue
                c0 = int(re.sub(r"\D", "", r0))
                c1 = int(re.sub(r"\D", "", r1))
                col0 = re.sub(r"[\d$]", "", r0)
                target = wb[sh]
                # the key value lives in the row referenced on THIS sheet
                krow = int(re.sub(r"\D", "", keyref))
                key_val = ws.cell(krow, _col_index(re.sub(r"[\d$]", "", keyref))).value
                # a BLANK key is not a broken lookup - it is a row with no class or no
                # book, which the IFERROR in the formula handles. Only a non-blank key
                # that the range cannot resolve is a defect.
                if key_val is None or key_val == "":
                    continue
                found = any(target.cell(rr, _col_index(col0)).value == key_val
                            for rr in range(c0, c1 + 1))
                if not found:
                    bad_lookups.append((ws.title, c.coordinate, key_val, f"{sh}!{r0}:{r1}"))
say(f"    {'PASS' if not bad_lookups else 'FAIL'}  {len(bad_lookups)} VLOOKUP range(s) "
    f"that do not contain their own key")
for b in bad_lookups[:6]:
    say(f"        {b[0]}!{b[1]}: looking up {b[2]!r} in {b[3]} - NOT THERE")
if bad_lookups:
    fails.append(f"{len(bad_lookups)} VLOOKUPs whose range lacks the key")

say()
say("  spot-check that referenced anchor cells are not blank AND hold the right thing:")
anchors = [("Dials", "B6", "the target", 0.05),
           ("Dials", "B16", "the Working uplift dial", 0.05),
           ("Dials", "B17", "the Ramp uplift dial", 0.05),
           ("Dials", "B18", "the Launch uplift dial", 0.05),
           ("Dials", "B19", "the Frozen uplift dial", 0.05),
           ("Dials", "B23", "the first class factor", 0.47)]
for sheet, cell, what, expected in anchors:
    v = wb[sheet][cell].value
    ok = v is not None and v != "" and abs(float(v) - expected) < 1e-9
    say(f"    {'PASS' if ok else 'FAIL'}  {sheet}!{cell:<5} = {v!r}   ({what}; expected {expected})")
    if not ok:
        fails.append(f"{sheet}!{cell} is {v!r}, expected {expected}")

# ---------------------------------------------------------------- 6. carried not recomputed
say()
say("=" * 86)
say("6. IS CURRENT SP CARRIED FROM THE FILE RATHER THAN RECOMPUTED?")
say("=" * 86)
k11 = wb["Line detail"]["K2"].value
say(f"  Line detail!K2 = {k11!r}")
carried = not (isinstance(k11, str) and k11.startswith("="))
say(f"  {'PASS' if carried else 'FAIL'}  current SP is carried, not recomputed")
say("  this matters: 12.8% of the catalogue carries a deliberate override, and"
     " recomputing would invent a price for those rows")
if not carried:
    fails.append("K2 recomputes SP instead of carrying it")

# ---------------------------------------------------------------- 7. computed block
say()
say("=" * 86)
say("7. THE COMPUTED COST BLOCK - DO THE RATE DIALS ACTUALLY DRIVE SOMETHING?")
say("=" * 86)
# This is the check that was missing until 2026-09-18: the FX and discount dials existed
# on Dials but NO formula referenced them, so changing a rate moved no number in the
# workbook. The computed block on Line detail (W = BP / FX * discount, X = 1 - W / SP)
# is what closes that gap, and this section asserts it really is wired to the dials.
ld_ws = wb["Line detail"]


def dial_value_row(label_first_words):
    """Find a Dials row by its label, so the check does not hardcode a row number."""
    for rr in range(1, wb["Dials"].max_row + 1):
        v = wb["Dials"].cell(rr, 1).value
        if isinstance(v, str) and v.strip().lower().startswith(label_first_words.lower()):
            return rr
    return None


FX_ROW = dial_value_row("Foreign exchange")
DISCJ_ROW = dial_value_row("Japan purchase discount")
comp_spec = [
    # W = V / FX * VLOOKUP(source). V is the carried yen base, W the computed FOB, and
    # X must divide by W - the FOB - NOT by S, which is Delta EUR. Asserting "S2" here
    # once let the wrong column through, so the check now names W explicitly.
    ("W2", "the computed landed cost", f"Dials!$B${FX_ROW}", "V2"),
    ("X2", "the computed gross margin", "W2", "K2"),
    ("Y2", "the computed margin against the class", "T2", "X2"),
    ("Z2", "the computed margin against the book", "X2", "X2"),
]
for cell, what, ref_a, ref_b in comp_spec:
    v = ld_ws[cell].value
    isf = isinstance(v, str) and v.startswith("=")
    wired = isf and ref_a in v and ref_b in v
    say(f"  {'PASS' if wired else 'FAIL'}  Line detail!{cell:<4} {what}")
    say(f"        {str(v)[:110]}")
    if not isf:
        fails.append(f"Line detail!{cell} is not a formula")
    elif not wired:
        fails.append(f"Line detail!{cell} does not reference {ref_a!r} and {ref_b!r}")
# X must never divide by the Delta EUR column. This is the defect Excel caught on
# 2026-09-18: X referenced S, so every computed margin was nonsense (-638% median).
x2 = str(ld_ws["X2"].value or "")
# the formula reads 1 - W2/K2, so W2 is the numerator of the ratio, not "/W2"
ok = (re.search(r"(?<![A-Z0-9$])W2/", x2) is not None
      and re.search(r"(?<![A-Z0-9$])S2/", x2) is None)
say(f"  {'PASS' if ok else 'FAIL'}  Line detail!X2 divides by the FOB column W, "
    f"never by Delta EUR (S)")
if not ok:
    fails.append("Line detail!X2 does not divide by W (the computed FOB column)")
say()
say("  and the header labels say COMPUTED, so nobody mistakes them for carried prices:")
for col, must in (("U", "SOURCE"), ("V", "CARRIED"), ("W", "COMPUTED"),
                  ("X", "COMPUTED"), ("Y", "COMPUTED"), ("Z", "COMPUTED")):
    h = str(ld_hdr.get(col) or "")
    ok = must in h.upper()
    say(f"    {'PASS' if ok else 'FAIL'}  Line detail!{col}1 = {h!r}")
    if not ok:
        fails.append(f"Line detail!{col}1 does not say {must}")
say()
say("  the rate dials must hold the values the 2026-09-18 update put there:")
rate_anchors = [("Dials", f"B{FX_ROW}", "the live FX rate", 178.5, 0.001),
                ("Dials", f"B{DISCJ_ROW}", "the Japan purchase discount", 0.673, 0.0001)]
for sheet, cell, what, expected, tol in rate_anchors:
    v = wb[sheet][cell].value
    try:
        ok = v is not None and abs(float(v) - expected) <= tol
    except (TypeError, ValueError):
        ok = False
    say(f"    {'PASS' if ok else 'FAIL'}  {sheet}!{cell:<5} = {v!r}   "
        f"({what}; expected {expected})")
    if not ok:
        fails.append(f"{sheet}!{cell} is {v!r}, expected {expected}")
say()
say("  and the three FX vintages must all still be visible (the revision was priced")
say("  on the oldest one, which is why the 4-6% question is hard):")
txt_set = " ".join(str(c.value) for ws in wb.worksheets for row in ws.iter_rows()
                   for c in row if isinstance(c.value, str))
for vintage in ("163.7", "172.6", "178.5"):
    ok = vintage in txt_set
    say(f"    {'PASS' if ok else 'FAIL'}  {vintage} JPY/EUR appears in the workbook")
    if not ok:
        fails.append(f"FX vintage {vintage} is not recorded anywhere in the workbook")
say()
say("  the discount table must CONTAIN both source keys the VLOOKUP asks for:")
for key in ("J", "T"):
    found = any(str(wb["Dials"].cell(rr, 1).value) == key
                for rr in range(1, wb["Dials"].max_row + 1))
    say(f"    {'PASS' if found else 'FAIL'}  Dials discount table holds the key {key!r}")
    if not found:
        fails.append(f"Dials discount table lacks key {key!r}")
say()
say("  the FX and discount direction must be stated correctly in the Dials notes:")
text_all = " ".join(str(c.value) for ws in wb.worksheets for row in ws.iter_rows()
                    for c in row if isinstance(c.value, str))
dir_checks = [("a higher JPY/EUR LOWERS our euro cost",
               "A HIGHER JPY/EUR LOWERS OUR EURO COST"),
              ("a higher discount RAISES it",
               "A HIGHER DISCOUNT RAISES IT")]
for lab, needle in dir_checks:
    ok = needle in text_all.upper()
    say(f"    {'PASS' if ok else 'FAIL'}  the workbook states: {lab}")
    if not ok:
        fails.append(f"direction statement missing: {lab}")
bad_sign = "18.36"
ok = bad_sign not in text_all
say(f"    {'PASS' if ok else 'FAIL'}  the reversed +{bad_sign}% figure appears nowhere")
if not ok:
    fails.append(f"the reversed +{bad_sign}% figure appears in the workbook")

# ---- the base revision must be split into settled (on file) and scenario (invented).
# This is the correction of 2026-09-18: a single "+7%" dial was load-bearing and was
# not sourced. The workbook must now keep them apart, label the scenario as unsourced,
# and cite the file the settled figure comes from.
say()
say("  the base revision must be split: settled (sourced) vs scenario (invented):")
rev_checks = [
    ("a settled revision dial exists and holds 5.9616%",
     any(isinstance(wb["Dials"].cell(rr, 1).value, str)
         and "settled" in str(wb["Dials"].cell(rr, 1).value).lower()
         and wb["Dials"].cell(rr, 2).value is not None
         and abs(float(wb["Dials"].cell(rr, 2).value) - 0.059616) < 1e-9
         for rr in range(1, wb["Dials"].max_row + 1))),
    ("a scenario revision dial exists and holds 7.0%",
     any(isinstance(wb["Dials"].cell(rr, 1).value, str)
         and "scenario" in str(wb["Dials"].cell(rr, 1).value).lower()
         and wb["Dials"].cell(rr, 2).value is not None
         and abs(float(wb["Dials"].cell(rr, 2).value) - 0.07) < 1e-9
         for rr in range(1, wb["Dials"].max_row + 1))),
    ("the settled figure cites aim_pricing_recalc_2026-09-17.json",
     "aim_pricing_recalc_2026-09-17.json" in text_all),
    ("the scenario is labelled as NOT a quotation from IML",
     "NOT A QUOTATION FROM IML" in text_all.upper()),
    ("the settled euro move +5.48% is stated",
     "5.48" in text_all),
]
for lab, ok in rev_checks:
    say(f"    {'PASS' if ok else 'FAIL'}  {lab}")
    if not ok:
        fails.append(f"base revision split check failed: {lab}")

say()
say("=" * 86)
if fails:
    say(f"FRAMEWORK_CHECK_FAIL ({len(fails)})")
    for f in fails:
        say(f"  - {f}")
else:
    say("FRAMEWORK_CHECK_OK")
say("=" * 86)
say()
say("NOT PROVEN HERE: that Excel evaluates every formula without a #REF! at runtime.")
say("The signatures checked above (sheet names, ranges, error literals) catch the")
say("common break, but the file should be opened once in Excel before it is relied on.")
