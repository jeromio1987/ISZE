"""Pricing grid draft on a NEW copy of the +5% proposal (brief 2026-10-11_P1_pricing_grid).

Package A starts as a faithful copy of build_market_layer_20261004.py (paper settings reproduce
EUR 1,629,793 / given-up 388,914 / ceiling cut 7,654 / recovered 396,568 / extra 3.727 OFF / 4.837 ON).
Later packages add hold switches, stance by price basis, 12-cell grid solver, reason codes, margin view,
test design, and label fixes. Never writes the live workbook, paper, config.yaml, or price ledger.

Run:  python build_pricing_grid_20261011.py
Then: python recalc_excel.py <staged workbook>
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).resolve().parent
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(HERE))
from evidence_lib import load_base  # noqa: E402

LIVE = ISZE / "01_data" / "01_Pricing" / "Price_Increase_5pct_Proposal_2026-09-29.xlsx"
STAGE = HERE / "stage_grid_2026-10-11"
OUT = Path(os.environ.get("PROPOSAL_OUT", STAGE / "Price_Increase_5pct_Proposal_GRID_DRAFT_2026-10-11.xlsx"))
RR = HERE / "room_to_raise_2026-10-02"
DERIVED = ISZE / "01_data" / "00_derived"
DEC = json.loads((HERE / "market_exercise_decisions_2026-09-30.json").read_text(encoding="utf-8"))
PUB = json.loads((RR / "room_to_raise_variant_B_iuk_exempt_2026-10-02.json").read_text(encoding="utf-8"))
PSUM = json.loads((HERE / "price_5pct_proposal_summary_2026-09-29.json").read_text(encoding="utf-8"))

EXPECT = {"parts": 15273, "pm_rows": 45581, "billed": 32595852.63, "lines": 47617, "pad_kits": 29}
CIS = ["ARMENIA", "KAZAKHSTAN"]
EXEMPT = "IUK"
CEILING_PTS = 0.05

REASON = {"service hold (market exercise)": "Service parts held at today's price",
          "UMI body/collision hold": "Body and collision parts held at today's price (Israel D-Max distributor)",
          "UMI lighting hold": "Lighting held at today's price (Israel D-Max distributor)",
          "UTI lighting hold": "Lighting held at today's price (Israel trucks distributor)"}
R_SERVICE = REASON["service hold (market exercise)"]
NAMES = {"ITUK": "UK trucks distributor (ITUK)", "IUK": "Isuzu UK, D-Max (IUK)", "UTI": "Israel trucks distributor (UTI)",
         "UMI": "Israel D-Max distributor (UMI)"}

# =================================================================== data
t0 = time.time()
ins = load_base()
L = ins[ins.movable].copy()
assert len(L) == EXPECT["lines"], len(L)
dd = pd.read_csv(DERIVED / "distributor_dimension.csv", dtype=str)
L["db"] = L.customer_code.astype(str).map(dict(zip(dd.sold_to_sap, dd.distributor_code)))
assert L.db.notna().all()
pm = L.groupby(["pn", "db"], as_index=False).net_sales_value.sum().rename(columns={"net_sales_value": "billed"})
pm["billed"] = pm.billed.round(2)
csv_pm = pd.read_csv(RR / "room_to_raise_by_part_market_2026-10-02.csv", dtype={"pn": str}, usecols=["pn", "db", "billed_eur", "hold_reason"])
pm = pm.merge(csv_pm, on=["pn", "db"], how="left", validate="1:1")
assert pm.billed_eur.notna().all() and len(pm) == EXPECT["pm_rows"], len(pm)
assert abs(pm.billed.sum() - EXPECT["billed"]) < 0.005, pm.billed.sum()
assert (pm.billed - pm.billed_eur).abs().max() <= 0.5 + 1e-9          # the CSV keeps 6 significant digits only
pm["reason"] = pm.hold_reason.fillna("").map(lambda x: REASON.get(x, x))
assert set(pm.reason.unique()) <= set(REASON.values()) | {""}
pm = pm.sort_values(["pn", "db"], kind="stable").reset_index(drop=True)

live_p = pd.read_excel(LIVE, sheet_name="Proposal", dtype={"Part number": str},
                       usecols=["Part number", "Description", "Billed EUR (Jul 25-Jun 26)"])
live_p["pn"] = live_p["Part number"].astype(str)
assert len(live_p) == EXPECT["parts"] and live_p.pn.is_unique
bp = pd.read_csv(RR / "room_to_raise_by_part_2026-10-02.csv", dtype={"pn": str},
                 usecols=["pn", "segment", "captive_strict", "lubricant", "padkit"], low_memory=False)
bp = bp.set_index("pn")
parts = pd.DataFrame({"pn": live_p.pn.to_numpy(), "desc": live_p.Description.fillna("").astype(str).to_numpy()})
for c in ["segment", "captive_strict", "lubricant", "padkit"]:
    parts[c] = parts.pn.map(bp[c])
assert parts.segment.notna().all()
assert set(parts.segment.unique()) == {"service", "repair", "body"}
assert int(parts.padkit.sum()) == EXPECT["pad_kits"]
assert set(pm.pn) == set(parts.pn)
parts = parts.sort_values("pn", kind="stable").reset_index(drop=True)
# pointers: part rows sit contiguously in the part x market list (both sorted by part number)
PM_FIRST, LP_FIRST = 5, 5
grp = pm.groupby("pn", sort=False).size()
first_idx = pm.reset_index().groupby("pn", sort=False)["index"].min()
assert (parts.pn.to_numpy() == grp.index.to_numpy()).all()
parts["first"] = (first_idx.reindex(parts.pn).to_numpy() + PM_FIRST).astype(int)
parts["nrows"] = grp.reindex(parts.pn).to_numpy().astype(int)
NP, NM = len(parts), len(pm)
LP_LAST, PM_LAST = LP_FIRST + NP - 1, PM_FIRST + NM - 1
markets = pm.groupby("db").billed.sum().sort_values(ascending=False).index.tolist()
assert len(markets) == 22 and set(CIS) <= set(markets) and EXEMPT in markets
print(f"data ready in {time.time() - t0:.0f}s: {NP} parts, {NM} part x market rows, {len(markets)} markets")

# decided treatment, from the decisions file (service) and the 2 Oct paper (Israel body/lighting)
held_service = sorted(k for k, v in DEC["decisions"].items() if v["service"].startswith("hold"))
assert held_service == ["BELGIUM", "CYPRUS", "GERMANY", "HUNGARY", "IUK", "MALTA", "NORWAY", "UMI"], held_service
for mkt in markets:      # the matrix below is data-checked against the hold flags
    rs = set(pm.reason[(pm.db == mkt) & (pm.reason != "")])
    exp_rs = set()
    if mkt in held_service:
        exp_rs.add(R_SERVICE)
    if mkt == "UMI":
        exp_rs |= {REASON["UMI body/collision hold"], REASON["UMI lighting hold"]}
    if mkt == "UTI":
        exp_rs.add(REASON["UTI lighting hold"])
    assert rs == exp_rs, (mkt, rs, exp_rs)

# =================================================================== styles (as the 29 Sep builder)
NAVY, CREAM = "15233C", "F7F4EE"
F = "Arial"
HFILL = PatternFill("solid", fgColor=NAVY)
HFILL_HELP = PatternFill("solid", fgColor="6B7280")
HFONT = Font(name=F, bold=True, color=CREAM, size=10)
TITLE = Font(name=F, bold=True, size=14, color=NAVY)
SUB = Font(name=F, italic=True, size=9, color="555555")
SEC = Font(name=F, bold=True, size=11, color=NAVY)
BODY = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
INPUT = Font(name=F, size=10, color="0000FF", bold=True)
DATA = Font(name=F, size=10, color="0000FF")          # imported values: blue, as in modelling convention
LINK = Font(name=F, size=10, color="008000")
YELLOW = PatternFill("solid", fgColor="FFFF00")
PALE = PatternFill("solid", fgColor="F3EFE6")
WRAP = Alignment(wrap_text=True, vertical="top")
PCT1, PCT2, PCT3, EUR0, EUR2 = "0.0%;-0.0%;-", "0.00%;-0.00%;-", "0.000%;-0.000%;-", "#,##0;(#,##0);-", "#,##0.00;(#,##0.00);-"
PTS = "+0.00%;-0.00%;-"
RED = Font(name=F, size=10, bold=True, color="C00000")
GREEN = Font(name=F, size=10, bold=True, color="2E7D32")


def header(ws, row, labels, col=1, height=30, fills=None):
    for i, h in enumerate(labels):
        c = ws.cell(row, col + i, h)
        c.fill = (fills or {}).get(i, HFILL)
        c.font = HFONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = height


def put(ws, row, col, value, font=BODY, fmt=None, align=None, fill=None):
    c = ws.cell(row, col, value)
    c.font = font
    if fmt:
        c.number_format = fmt
    if align:
        c.alignment = align
    if fill:
        c.fill = fill
    return c


# =================================================================== open a copy of the live workbook
tmpd = Path(tempfile.mkdtemp(prefix="market_layer_"))
src_copy = tmpd / LIVE.name
shutil.copy2(LIVE, src_copy)
wb = load_workbook(src_copy)
assert wb.sheetnames == ["Read me", "Summary", "Proposal", "Review lists", "Dealer response", "Not in proposal", "Checks"], wb.sheetnames
assert len(wb["Dealer response"]._charts) == 1
ws_sum, ws_prop, ws_ck, ws_read = wb["Summary"], wb["Proposal"], wb["Checks"], wb["Read me"]
assert ws_prop.max_row == EXPECT["parts"] + 1
PROP_LAST = ws_prop.max_row                                    # 15274
assert ws_sum["B9"].value == 1 and ws_sum["D5"].value is None

ws_ml = wb.create_sheet("Market layer", index=2)
ws_pm = wb.create_sheet("Layer by part and market")
ws_lp = wb.create_sheet("Layer by part")
ws_sv = wb.create_sheet("Layer solver")
for w_ in (ws_ml, ws_lp, ws_pm, ws_sv):
    w_.sheet_view.showGridLines = False
ML, LPN, PMN, SVN = "'Market layer'!", "'Layer by part'!", "'Layer by part and market'!", "'Layer solver'!"
SW = "Summary!$D$5"                                         # the IUK exemption switch

# column registries (letters come from one place, so formulas cannot drift)
LP_COLS = ["pn", "desc", "cat", "noalt", "lub", "list_now", "inc_now", "list_new", "own_fact", "own_inc", "padheld", "ceil",
           "floor", "elig", "room", "free_b", "free_ex", "w_off", "w_on", "inc_off", "inc_on", "first", "nrows", "ptr", "prow"]
PM_COLS = ["pn", "mkt", "cat", "billed", "cond", "own", "inc", "pts", "eur", "eur_vs", "state", "lprow", "free_b",
           "free_ex", "inc_off", "inc_on", "reason"]
lc = {n: get_column_letter(i + 1) for i, n in enumerate(LP_COLS)}
pc = {n: get_column_letter(i + 1) for i, n in enumerate(PM_COLS)}


def lp_rng(n, a=LP_FIRST, b=LP_LAST):
    return f"{LPN}${lc[n]}${a}:${lc[n]}${b}"


def pm_rng(n, a=PM_FIRST, b=PM_LAST):
    return f"{PMN}${pc[n]}${a}:${pc[n]}${b}"


def lp_idx(n, rowref):                                     # INDEX from the top of the sheet, so the row number is absolute
    return f"INDEX({LPN}${lc[n]}$1:${lc[n]}${LP_LAST},{rowref})"


def pm_idx_rng(n):
    return f"{PMN}${pc[n]}$1:${pc[n]}${PM_LAST}"


# cells on 'Market layer' that the other sheets read (rows fixed here, the sheet is laid out around them)
R_SET_CEIL, R_SET_EXEMPT, R_SET_CIS = 7, 8, 9
CEIL = f"{ML}$B${R_SET_CEIL}"
EXC = f"{ML}$B${R_SET_EXEMPT}"
CIS1, CIS2 = f"{ML}$B${R_SET_CIS}", f"{ML}$C${R_SET_CIS}"
T_OFF, T_ON = f"{SVN}$B$12", f"{SVN}$C$12"

# =================================================================== sheet: Layer by part
ws = ws_lp
put(ws, 1, 1, "Layer by part: one list price per part, and what the market layer does to it", TITLE)
put(ws, 2, 1, ("One row per part number, in part number order. Blue = values copied in (sources on the 'Market layer' sheet); "
               "black = formulas. The list increase is one number per part; holds and exemptions are distributor conditions "
               "applied on the part x market sheet."), SUB)
LP_HEAD = {
    "pn": "Part number", "desc": "Description", "cat": "Parts category (service, repair, body)",
    "noalt": "No aftermarket alternative found (1 = yes)", "lub": "Lubricant (1 = yes): kept at today's price",
    "list_now": "Current list EUR (PR00)", "inc_now": "List increase now (switch as set)", "list_new": "New list EUR now",
    "own_fact": "Own factory increase (IML/IMIT)", "own_inc": "Own increase in the +5% proposal",
    "padheld": "Brake pad kit held at today's price (1 = yes)", "ceil": "Ceiling: own factory increase + 5 points",
    "floor": "Own increase limited by the ceiling", "elig": "Carries the recovery extra (1 = yes)",
    "room": "Room for the extra below the ceiling", "free_b": "Billed in markets with no hold, excluding Armenia and Kazakhstan",
    "free_ex": "Of which in the exempt market (Isuzu UK)", "w_off": "Billed that carries the extra: switch OFF",
    "w_on": "Billed that carries the extra: switch ON", "inc_off": "List increase: switch OFF",
    "inc_on": "List increase: switch ON", "first": "First row on 'Layer by part and market'", "nrows": "Rows on 'Layer by part and market'",
    "ptr": "Row pointer check (0 = ok)", "prow": "Row on Proposal sheet"}
HELP_LP = {"first", "nrows", "ptr", "prow", "padheld", "free_b", "free_ex", "w_off", "w_on", "floor", "room", "ceil", "elig"}
header(ws, 4, [LP_HEAD[n] for n in LP_COLS], height=92, fills={i: HFILL_HELP for i, n in enumerate(LP_COLS) if n in HELP_LP})
PM_FREE = pm_idx_rng("free_b")
PM_FREEX = pm_idx_rng("free_ex")
PM_PN_TOP = pm_idx_rng("pn")
for i, r_ in enumerate(parts.itertuples(index=False)):
    r = LP_FIRST + i
    f = {n: f"{lc[n]}{r}" for n in LP_COLS}
    ws[f["pn"]] = r_.pn
    ws[f["desc"]] = r_.desc
    ws[f["cat"]] = r_.segment
    ws[f["noalt"]] = int(r_.captive_strict)
    ws[f["lub"]] = int(r_.lubricant)
    ws[f["first"]] = int(r_.first)
    ws[f["nrows"]] = int(r_.nrows)
    ws[f["prow"]] = f"=MATCH({f['pn']},Proposal!$A$2:$A${PROP_LAST},0)+1"
    ws[f["own_fact"]] = f"=INDEX(Proposal!$L$1:$L${PROP_LAST},{f['prow']})"
    ws[f["own_inc"]] = f"=INDEX(Proposal!$P$1:$P${PROP_LAST},{f['prow']})"
    ws[f["padheld"]] = f"=IF(AND(INDEX(Proposal!$AD$1:$AD${PROP_LAST},{f['prow']})=1,Summary!$B$9=1),1,0)"
    ws[f["ceil"]] = f"=IF(OR({f['padheld']}=1,{f['lub']}=1),0,MAX({f['own_fact']},0)+{CEIL})"
    ws[f["floor"]] = f"=MIN({f['ceil']},{f['own_inc']})"
    ws[f["elig"]] = f'=IF(AND(OR({f["cat"]}="repair",{f["cat"]}="body"),{f["noalt"]}=1,{f["padheld"]}=0,{f["lub"]}=0),1,0)'
    ws[f["room"]] = f"=IF({f['elig']}=1,MAX({f['ceil']}-{f['own_inc']},0),0)"
    ws[f["free_b"]] = f"=SUM(INDEX({PM_FREE},{f['first']}):INDEX({PM_FREE},{f['first']}+{f['nrows']}-1))"
    ws[f["free_ex"]] = f"=SUM(INDEX({PM_FREEX},{f['first']}):INDEX({PM_FREEX},{f['first']}+{f['nrows']}-1))"
    ws[f["w_off"]] = f"={f['free_b']}"
    ws[f["w_on"]] = f"={f['free_b']}-{f['free_ex']}"
    ws[f["inc_off"]] = f"={f['floor']}+MIN({f['room']},{T_OFF})"
    ws[f["inc_on"]] = f"={f['floor']}+MIN({f['room']},{T_ON})"
    ws[f["inc_now"]] = f"=IF({SW}=1,{f['inc_on']},{f['inc_off']})"
    ws[f["list_now"]] = f'=IF(INDEX(Proposal!$I$1:$I${PROP_LAST},{f["prow"]})>0,INDEX(Proposal!$I$1:$I${PROP_LAST},{f["prow"]}),"")'
    ws[f["list_new"]] = f'=IF({f["list_now"]}="","",ROUND({f["list_now"]}*(1+{f["inc_now"]}),2))'
    ws[f["ptr"]] = (f"=IF(AND(INDEX({PM_PN_TOP},{f['first']})={f['pn']},"
                    f"INDEX({PM_PN_TOP},{f['first']}+{f['nrows']}-1)={f['pn']}),0,1)")
fmt_lp = {"list_now": EUR2, "inc_now": PCT2, "list_new": EUR2, "own_fact": PCT2, "own_inc": PCT2, "ceil": PCT2, "floor": PCT2,
          "room": PCT2, "free_b": EUR0, "free_ex": EUR0, "w_off": EUR0, "w_on": EUR0, "inc_off": PCT2, "inc_on": PCT2,
          "first": "0", "nrows": "0", "ptr": "0", "prow": "0"}
data_lp = {"pn", "desc", "cat", "noalt", "lub", "first", "nrows"}
for row in ws.iter_rows(min_row=LP_FIRST, max_row=LP_LAST):
    for j, c in enumerate(row):
        n = LP_COLS[j]
        c.font = DATA if n in data_lp else (BOLD if n in ("inc_now", "list_new") else BODY)
        if n in fmt_lp:
            c.number_format = fmt_lp[n]
for n, wd in zip(LP_COLS, [13, 34, 11, 12, 12, 12, 12, 12, 11, 11, 11, 11, 11, 11, 11, 14, 12, 14, 14, 11, 11, 11, 10, 10, 10]):
    ws.column_dimensions[lc[n]].width = wd
ws.freeze_panes = f"C{LP_FIRST}"
ws.auto_filter.ref = f"A4:{get_column_letter(len(LP_COLS))}{LP_LAST}"

# =================================================================== sheet: Layer by part and market
ws = ws_pm
put(ws, 1, 1, "Layer by part and market: the condition each distributor gets on each part", TITLE)
put(ws, 2, 1, ("One row per part number and market (45,581 rows). Condition = hold at today's price, own increase, own increase plus "
               "the recovery extra, or own increase only. Blue = values copied in (sources on the 'Market layer' sheet); black = "
               "formulas. Grey headers are helper columns."), SUB)
PM_HEAD = {
    "pn": "Part number", "mkt": "Market", "cat": "Parts category", "billed": "Billed EUR (Jul 25-Jun 26)",
    "cond": "Condition now (switch as set)", "own": "Own increase", "inc": "Increase in this market now",
    "pts": "Hold or extra vs own increase (points)", "eur": "EUR at this increase", "eur_vs": "EUR vs own increase",
    "reason": "Hold applied (decided)", "state": "Line type (hold, own only, free)", "lprow": "Row on 'Layer by part'",
    "free_b": "Billed in a line with no hold (not Armenia or Kazakhstan)", "free_ex": "Of which exempt market",
    "inc_off": "Increase if switch OFF", "inc_on": "Increase if switch ON"}
HELP_PM = {"reason", "state", "lprow", "free_b", "free_ex", "inc_off", "inc_on"}
header(ws, 4, [PM_HEAD[n] for n in PM_COLS], height=80, fills={i: HFILL_HELP for i, n in enumerate(PM_COLS) if n in HELP_PM})
LPA = lp_rng("pn")
for i, r_ in enumerate(pm.itertuples(index=False)):
    r = PM_FIRST + i
    f = {n: f"{pc[n]}{r}" for n in PM_COLS}
    ws[f["pn"]] = r_.pn
    ws[f["mkt"]] = r_.db
    ws[f["billed"]] = float(r_.billed)
    ws[f["reason"]] = r_.reason if r_.reason else None
    ws[f["lprow"]] = f"=MATCH({f['pn']},{LPA},0)+{LP_FIRST - 1}"
    ws[f["cat"]] = f"={lp_idx('cat', f['lprow'])}"
    ws[f["state"]] = f'=IF(OR({f["mkt"]}={CIS1},{f["mkt"]}={CIS2}),"own only",IF({f["reason"]}<>"","hold","free"))'
    ws[f["free_b"]] = f'=IF({f["state"]}="free",{f["billed"]},0)'
    ws[f["free_ex"]] = f"=IF({f['mkt']}={EXC},{f['free_b']},0)"
    ws[f["own"]] = f"={lp_idx('own_inc', f['lprow'])}"
    ws[f["inc_off"]] = f'=IF({f["state"]}="hold",0,IF({f["state"]}="own only",{f["own"]},{lp_idx("inc_off", f["lprow"])}))'
    ws[f["inc_on"]] = (f'=IF({f["state"]}="hold",0,IF({f["state"]}="own only",{f["own"]},IF({f["mkt"]}={EXC},'
                       f'{lp_idx("floor", f["lprow"])},{lp_idx("inc_on", f["lprow"])})))')
    ws[f["inc"]] = f"=IF({SW}=1,{f['inc_on']},{f['inc_off']})"
    ws[f["pts"]] = f"={f['inc']}-{f['own']}"
    ws[f["cond"]] = (f'=IF({f["state"]}="hold",{f["reason"]},IF({f["state"]}="own only","Own increase only: no hold, no extra (option A)",'
                     f'IF({f["inc"]}>{f["own"]},"Own increase + recovery extra",IF({f["inc"]}<{f["own"]},'
                     f'"Own increase, held down by the ceiling",IF(AND({SW}=1,{f["mkt"]}={EXC},{lp_idx("elig", f["lprow"])}=1),'
                     f'"Own increase only: exempt from the extra","Own increase")))))')
    ws[f["eur"]] = f"={f['billed']}*{f['inc']}"
    ws[f["eur_vs"]] = f"={f['billed']}*{f['pts']}"
fmt_pm = {"billed": EUR2, "own": PCT2, "inc": PCT2, "pts": PTS, "eur": EUR2, "eur_vs": EUR2, "lprow": "0", "free_b": EUR2,
          "free_ex": EUR2, "inc_off": PCT2, "inc_on": PCT2}
data_pm = {"pn", "mkt", "billed", "reason"}
for row in ws.iter_rows(min_row=PM_FIRST, max_row=PM_LAST):
    for j, c in enumerate(row):
        n = PM_COLS[j]
        c.font = DATA if n in data_pm else (BOLD if n in ("inc", "cond") else BODY)
        if n in fmt_pm:
            c.number_format = fmt_pm[n]
for n, wd in zip(PM_COLS, [13, 12, 10, 13, 40, 10, 12, 14, 13, 13, 10, 9, 15, 12, 11, 11, 44]):
    ws.column_dimensions[pc[n]].width = wd
ws.freeze_panes = f"C{PM_FIRST}"
ws.auto_filter.ref = f"A4:{get_column_letter(len(PM_COLS))}{PM_LAST}"

# =================================================================== sheet: Layer solver
ws = ws_sv
put(ws, 1, 1, "Layer solver: the extra points on repair and body parts, solved live", TITLE)
put(ws, 2, 1, ("The recovery extra is one number of points added to every part that carries it, up to its ceiling. It is found by "
               "halving the search range 60 times until the total lands on the target (no macro, no Goal Seek). Change any switch "
               "and it re-solves."), SUB)
BFC = pm_rng("billed")
STc = pm_rng("state")
OWNc = pm_rng("own")
put(ws, 4, 1, "Target total increase, EUR (Summary target x billed base)", BODY)
put(ws, 4, 2, f"=Summary!$B$5*SUM({BFC})", BOLD, EUR2)
put(ws, 5, 1, "Own increase on Armenia and Kazakhstan lines (option A, fixed), EUR", BODY)
put(ws, 5, 2, f'=SUMPRODUCT(--({STc}="own only"),{BFC},{OWNc})', BOLD, EUR2)
put(ws, 6, 1, "All other lines with no hold, at their own increase limited by the ceiling, EUR", BODY)
put(ws, 6, 2, f"=SUMPRODUCT({lp_rng('free_b')},{lp_rng('floor')})", BOLD, EUR2)
put(ws, 7, 1, "Recovery the extra has to deliver, EUR (target - fixed lines - lines at their floor)", BOLD)
put(ws, 7, 2, "=B4-B5-B6", BOLD, EUR2)
put(ws, 8, 1, "Largest room below any ceiling (upper end of the search range)", BODY)
put(ws, 8, 2, f"=MAX({lp_rng('room')})", BODY, PCT2)
header(ws, 10, ["Item", "Switch OFF (paper)", "Switch ON (Isuzu UK exempt)"], height=32)
ROOM = lp_rng("room")
WOFF, WON = lp_rng("w_off"), lp_rng("w_on")
BIS0 = 20                                                   # first bisection row
BISN = 60
last_b = BIS0 + BISN - 1
put(ws, 11, 1, "Billed that carries the extra, EUR", BODY)
put(ws, 11, 2, f"=SUMPRODUCT({WOFF},--({ROOM}>0))", BODY, EUR0)
put(ws, 11, 3, f"=SUMPRODUCT({WON},--({ROOM}>0))", BODY, EUR0)
put(ws, 12, 1, "Extra points on top of own increase (t)", BOLD)
put(ws, 12, 2, f"=C{last_b}", BOLD, "0.000000")
put(ws, 12, 3, f"=G{last_b}", BOLD, "0.000000")
put(ws, 13, 1, "Recovery delivered at t, EUR", BODY)
put(ws, 13, 2, f"=SUMPRODUCT({WOFF},({ROOM}<B12)*{ROOM}+({ROOM}>=B12)*B12)", BODY, EUR2)
put(ws, 13, 3, f"=SUMPRODUCT({WON},({ROOM}<C12)*{ROOM}+({ROOM}>=C12)*C12)", BODY, EUR2)
put(ws, 14, 1, "Recovery needed, EUR", BODY)
put(ws, 14, 2, "=$B$7", BODY, EUR2)
put(ws, 14, 3, "=$B$7", BODY, EUR2)
put(ws, 15, 1, "Difference, EUR (should be 0.00)", BOLD)
put(ws, 15, 2, "=ROUND(B13-B14,2)", BOLD, EUR2)
put(ws, 15, 3, "=ROUND(C13-C14,2)", BOLD, EUR2)
put(ws, 16, 1, "Can the ceiling deliver it?", BODY)
put(ws, 16, 2, f'=IF(SUMPRODUCT({WOFF},{ROOM})>=B14-0.01,"yes","no: ceiling too tight")', BOLD)
put(ws, 16, 3, f'=IF(SUMPRODUCT({WON},{ROOM})>=C14-0.01,"yes","no: ceiling too tight")', BOLD)
header(ws, BIS0 - 1, ["Step", "Low (OFF)", "High (OFF)", "Middle (OFF)", "Recovery at middle (OFF)",
                       "Low (ON)", "High (ON)", "Middle (ON)", "Recovery at middle (ON)"], height=32)
for k in range(BISN):
    r = BIS0 + k
    put(ws, r, 1, k + 1, BODY, "0")
    for base_col, W in ((2, WOFF), (6, WON)):
        lo, hi, mid, g = (get_column_letter(base_col + j) for j in range(4))
        if k == 0:
            put(ws, r, base_col, 0, BODY, "0.000000")
            put(ws, r, base_col + 1, "=$B$8", BODY, "0.000000")
        else:
            put(ws, r, base_col, f"=IF({g}{r - 1}<$B$7,{mid}{r - 1},{lo}{r - 1})", BODY, "0.000000")
            put(ws, r, base_col + 1, f"=IF({g}{r - 1}<$B$7,{hi}{r - 1},{mid}{r - 1})", BODY, "0.000000")
        put(ws, r, base_col + 2, f"=({lo}{r}+{hi}{r})/2", BODY, "0.000000")
        put(ws, r, base_col + 3, f"=SUMPRODUCT({W},({ROOM}<{mid}{r})*{ROOM}+({ROOM}>={mid}{r})*{mid}{r})", BODY, EUR2)
for col, wd in zip("ABCDEFGHI", [74, 20, 20, 16, 22, 14, 14, 14, 22]):
    ws.column_dimensions[col].width = wd
ws.freeze_panes = "A4"

# =================================================================== sheet: Market layer
ws = ws_ml
mk_name = lambda m: NAMES.get(m, m.title())
put(ws, 1, 1, "Market layer: how the market decisions of the 2 October 2026 paper land per part and per market", TITLE)
put(ws, 2, 1, ("A proposal on paper. Nothing published, no price file or price list changed. The list stays one price per part; "
               "the market treatment is a distributor condition per market and parts category. The total stays on the target."), SUB)
put(ws, 4, 1, "Terms used on this sheet", SEC)
legend = ("Own increase = the +5% proposal's increase for that part (its own IML/IMIT factory increase, scaled so the book lands on "
          "+5.00%). Hold = the distributor keeps paying today's price for that parts category. Recovery extra = extra points on "
          "top of own increase, only on repair and body parts with no aftermarket alternative found, up to the part's own factory "
          "increase + 5 points; service parts get nothing extra.")
put(ws, 5, 1, legend, BODY, align=WRAP)
ws.merge_cells("A5:H5")
ws.row_dimensions[5].height = 56
put(ws, 6, 1, "Switch and settings", SEC)
put(ws, R_SET_CEIL, 1, "Ceiling above a part's own factory (IML/IMIT) increase, points (decided 30 Sep and 2 Oct, not a switch)", BODY, align=WRAP)
put(ws, R_SET_CEIL, 2, CEILING_PTS, INPUT, PCT1, fill=PALE)
put(ws, R_SET_EXEMPT, 1, "Market code the switch exempts from the recovery extra", BODY, align=WRAP)
put(ws, R_SET_EXEMPT, 2, EXEMPT, INPUT, fill=PALE)
put(ws, R_SET_EXEMPT, 3, "Isuzu UK (D-Max)", SUB)
put(ws, R_SET_CIS, 1, "Markets left on their own increase, no hold, no extra (option A)", BODY, align=WRAP)
put(ws, R_SET_CIS, 2, CIS[0], INPUT, fill=PALE)
put(ws, R_SET_CIS, 3, CIS[1], INPUT, fill=PALE)
put(ws, 10, 1, "Isuzu UK (D-Max) exempt from the recovery extra: switch on the Summary sheet, cell D5 (0 = off, 1 = on)", BOLD, align=WRAP)
put(ws, 10, 2, f'=IF({SW}=1,"ON","OFF")', BOLD)
put(ws, 10, 3, (f'=IF({SW}=1,"ON: Isuzu UK repair and body parts keep their own increase; the extra moves to the other markets '
                f'(suggested, not decided).","OFF (default): Isuzu UK carries the extra, as in the 2 October paper. The exemption is not '
                f'decided: leave open.")'), BODY)
for r in (R_SET_CEIL, R_SET_EXEMPT, R_SET_CIS, 10):
    ws.row_dimensions[r].height = 28
    for c_ in range(1, 4):
        a_ = ws.cell(r, c_).alignment
        ws.cell(r, c_).alignment = Alignment(wrap_text=a_.wrap_text, vertical="center", horizontal=a_.horizontal)

# ---- reconciliation
RR0 = 12
put(ws, RR0, 1, "Reconciliation: the total stays exactly on the target in both switch positions", SEC)
header(ws, RR0 + 1, ["Item", "Switch OFF (paper)", "Switch ON (Isuzu UK exempt)", "Now (switch as set)", "Published: OFF",
                      "Published: ON", "Matches published", "Where the published figure comes from"], height=44)
cols_state = {"B": "inc_off", "C": "inc_on", "D": "inc"}
Bc, Dc, Gc, Cc, Mc = pm_rng("billed"), pm_rng("own"), pm_rng("state"), pm_rng("cat"), pm_rng("mkt")
rec = {}                                                    # name -> row


def sp(expr_inc, kind):
    X = pm_rng(expr_inc)
    if kind == "total":
        return f"=SUMPRODUCT({Bc},{X})"
    if kind == "own":
        return f"=SUMPRODUCT({Bc},{Dc})"
    if kind == "given":
        return f'=SUMPRODUCT(--({Gc}="hold"),{Bc},{Dc})'
    if kind == "cut":
        return f'=SUMPRODUCT(--({Gc}="free"),{Bc},--(({Dc}-{X})>0),{Dc}-{X})'
    if kind == "extra":
        return f'=SUMPRODUCT(--({Gc}="free"),{Bc},--(({X}-{Dc})>0),{X}-{Dc})'
    if kind.startswith("extra_cat:"):
        cat = kind.split(":")[1]
        return f'=SUMPRODUCT(--({Gc}="free"),--({Cc}="{cat}"),{Bc},--(({X}-{Dc})>0),{X}-{Dc})'
    if kind == "extra_exempt":
        return (f'=SUMPRODUCT(--({Gc}="free"),--({Mc}={EXC}),--(({Cc}="repair")+({Cc}="body")>0),{Bc},--(({X}-{Dc})>0),{X}-{Dc})')
    raise ValueError(kind)


pubB, pubE = PUB["B_as_published"], PUB["B_iuk_exempt"]
rows = [
    ("own", "Own increase on all parts and markets (the +5% proposal), EUR", "own", EUR0, None, None,
     "Proposal sheet: Summary B13 (EUR 1,629,793)"),
    ("given", "Less: given up by the holds, EUR", "given", EUR0, 388914.0, 388914.0,
     "Paper of 2 Oct 2026 (EUR 388,914); room_to_raise_scenarios_2026-10-02.csv held_step_given_up_eur"),
    ("cut", "Less: cut by the ceiling (own increase above own factory increase + 5 points), EUR", "cut", EUR0,
     7654.0, 7654.0, "room_to_raise_scenarios_2026-10-02.csv cut_below_proposal_by_ceiling_eur (7,654)"),
    ("extra", "Plus: recovery extra on repair and body parts with no aftermarket alternative, EUR", "extra", EUR0,
     pubB["uplift_above_proposal_eur"], pubE["uplift_above_proposal_eur"], "room_to_raise_variant_B_iuk_exempt_2026-10-02.json"),
    ("total", "Total increase after market treatment, EUR", "total", EUR0, pubB["total_step_eur"], pubE["total_step_eur"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json total_step_eur"),
]
r = RR0 + 2
for key, label, kind, nf, pOFF, pON, src in rows:
    rec[key] = r
    put(ws, r, 1, label, BOLD if key == "total" else BODY, align=WRAP)
    for col, inc in cols_state.items():
        put(ws, r, "ABCDEFGH".index(col) + 1, sp(inc, kind), BOLD if key == "total" else BODY, nf)
    if pOFF is not None:
        put(ws, r, 5, pOFF, DATA, nf)
        put(ws, r, 6, pON, DATA, nf)
        put(ws, r, 7, f'=IF(AND(Summary!$B$5=0.05,Summary!$B$6=1,Summary!$B$7=1,Summary!$B$8=0,Summary!$B$9=1),'
                      f'IF(AND(ABS(B{r}-E{r})<=1,ABS(C{r}-F{r})<=1),"OK","CHECK"),"n/a: settings changed")', BOLD)
    put(ws, r, 8, src, SUB)
    ws.row_dimensions[r].height = 28 if len(label) > 70 else 16
    r += 1
more = [
    ("target", "Target: Summary target x billed base, EUR", lambda c: f"=Summary!$B$5*SUM({Bc})", EUR0, None, None, "Summary B5 x billed base"),
    ("diff", "Difference to target, EUR (should be 0)", lambda c: f"={c}{rec['total']}-{c}{rec['total'] + 1}", EUR2, None, None, ""),
    ("pct", "Weighted increase after market treatment", lambda c: f"={c}{rec['total']}/SUM({Bc})", PCT3, 0.05, 0.05,
     "Target +5.00% (published total_pct 0.05 in the variant json)"),
    ("base", "Billed base, EUR (Jul 2025 - Jun 2026)", lambda c: f"=SUM({Bc})", EUR2, None, None, "price_bp_weighted_compare_pn.csv, in scope and movable: EUR 32,595,852.63"),
    ("t", "Extra points on top of own increase (solved on 'Layer solver')", None, "0.0000%", pubB["solver_t_pts"], pubE["solver_t_pts"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json solver_t_pts"),
    ("rep", "Recovery extra on repair parts, EUR", "extra_cat:repair", EUR0, pubB["uplift_repair_eur"], pubE["uplift_repair_eur"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json"),
    ("body", "Recovery extra on body parts, EUR", "extra_cat:body", EUR0, pubB["uplift_body_eur"], pubE["uplift_body_eur"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json"),
    ("svc", "Recovery extra on service parts, EUR (must be 0)", "extra_cat:service", EUR0, 0.0, 0.0,
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json uplift_service_eur"),
    ("iuk", "Recovery extra on Isuzu UK (D-Max) repair and body parts, EUR", "extra_exempt", EUR0,
     pubB["uplift_on_iuk_repair_body_eur"], pubE["uplift_on_iuk_repair_body_eur"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json uplift_on_iuk_repair_body_eur"),
    ("nparts", "Part numbers that carry the extra (repair or body, no aftermarket alternative, billed where it applies)", None, "#,##0",
     pubB["eligible_parts_with_flex_billing"], pubE["eligible_parts_with_flex_billing"],
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json eligible_parts_with_flex_billing (the paper says 8,447: it also counts one part kept at today's price)"),
]
for key, label, fn, nf, pOFF, pON, src in more:
    rec[key] = r
    put(ws, r, 1, label, BOLD if key in ("diff", "pct") else BODY, align=WRAP)
    for col, inc in cols_state.items():
        ci = "ABCDEFGH".index(col) + 1
        if key == "target":
            put(ws, r, ci, fn(col), BODY, nf)
        elif key in ("diff", "pct", "base"):
            put(ws, r, ci, fn(col), BOLD if key != "base" else BODY, nf)
        elif key == "t":
            put(ws, r, ci, {"B": f"={SVN}$B$12", "C": f"={SVN}$C$12", "D": f"=IF({SW}=1,C{r},B{r})"}[col], BODY, nf)
        elif key == "nparts":
            wcol = {"B": WOFF, "C": WON, "D": None}[col]
            put(ws, r, ci, (f"=SUMPRODUCT(--({lp_rng('elig')}=1),--({wcol}>0))" if wcol else f"=IF({SW}=1,C{r},B{r})"), BODY, nf)
        else:
            put(ws, r, ci, sp(inc, fn), BODY, nf)
    if pOFF is not None:
        put(ws, r, 5, pOFF, DATA, nf)
        put(ws, r, 6, pON, DATA, nf)
        tol = "0.0000015" if key == "t" else ("0.0000001" if key == "pct" else ("0" if key == "nparts" else "1"))
        put(ws, r, 7, f'=IF(AND(Summary!$B$5=0.05,Summary!$B$6=1,Summary!$B$7=1,Summary!$B$8=0,Summary!$B$9=1),'
                      f'IF(AND(ABS(B{r}-E{r})<={tol},ABS(C{r}-F{r})<={tol}),"OK","CHECK"),"n/a: settings changed")', BOLD)
    put(ws, r, 8, src, SUB)
    ws.row_dimensions[r].height = 28 if len(label) > 70 else 16
    r += 1
rec["target_row"] = rec["target"]
# fix 'diff' (needs the target row, which is the row right above it)
for col in "BCD":
    ws[f"{col}{rec['diff']}"] = f"=ROUND({col}{rec['total']}-{col}{rec['target']},2)"
rec["ident"] = r
put(ws, r, 1, "Identity: own - given up - cut + extra - total, EUR (should be 0)", BODY)
for col in "BCD":
    put(ws, r, "ABCD".index(col) + 1, f"=ROUND({col}{rec['own']}-{col}{rec['given']}-{col}{rec['cut']}+{col}{rec['extra']}-{col}{rec['total']},2)", BODY, EUR2)
r += 2

# ---- per-market totals
MT0 = r
put(ws, MT0, 1, "Per market: average increase, euro given up, euro recovered", SEC)
put(ws, MT0 + 1, 1, ("Active columns follow the switch; the last four columns show both switch positions side by side. "
                     "Armenia and Kazakhstan: own increase only (see below)."), SUB)
header(ws, MT0 + 2, ["Market", "Code", "Billed EUR", "Own increase (average)", "Given up by holds, EUR", "of which service parts",
                      "of which Israel body, collision, lighting", "Cut by ceiling, EUR", "Recovered by extra, EUR",
                      "Increase after treatment (average)", "Total increase after treatment, EUR", "Switch OFF: increase",
                      "Switch OFF: recovered, EUR", "Switch ON: increase", "Switch ON: recovered, EUR"], height=58)
mt_rows = {}
first_m = MT0 + 3
for i, m in enumerate(markets):
    rr = first_m + i
    mt_rows[m] = rr
    A = f"$B{rr}"
    put(ws, rr, 1, mk_name(m), BODY)
    put(ws, rr, 2, m, DATA)
    put(ws, rr, 3, f"=SUMIF({Mc},{A},{Bc})", BODY, EUR0)
    put(ws, rr, 4, f"=SUMPRODUCT(--({Mc}={A}),{Bc},{Dc})/C{rr}", BODY, PCT2)
    put(ws, rr, 5, f'=SUMPRODUCT(--({Mc}={A}),--({Gc}="hold"),{Bc},{Dc})', BODY, EUR0)
    put(ws, rr, 6, f'=SUMPRODUCT(--({Mc}={A}),--({pm_rng("reason")}="{R_SERVICE}"),{Bc},{Dc})', BODY, EUR0)
    put(ws, rr, 7, f"=E{rr}-F{rr}", BODY, EUR0)
    X = pm_rng("inc")
    put(ws, rr, 8, f'=SUMPRODUCT(--({Mc}={A}),--({Gc}="free"),{Bc},--(({Dc}-{X})>0),{Dc}-{X})', BODY, EUR0)
    put(ws, rr, 9, f'=SUMPRODUCT(--({Mc}={A}),--({Gc}="free"),{Bc},--(({X}-{Dc})>0),{X}-{Dc})', BODY, EUR0)
    put(ws, rr, 10, f"=K{rr}/C{rr}", BOLD, PCT2)
    put(ws, rr, 11, f"=SUMIF({Mc},{A},{pm_rng('eur')})", BODY, EUR0)
    for col, inc in ((12, "inc_off"), (14, "inc_on")):
        XX = pm_rng(inc)
        put(ws, rr, col, f"=SUMPRODUCT(--({Mc}={A}),{Bc},{XX})/C{rr}", BODY, PCT2)
        put(ws, rr, col + 1, f'=SUMPRODUCT(--({Mc}={A}),--({Gc}="free"),{Bc},--(({XX}-{Dc})>0),{XX}-{Dc})', BODY, EUR0)
last_m = first_m + len(markets) - 1
rt_ = last_m + 1
mt_total = rt_
put(ws, rt_, 1, "All markets", BOLD)
put(ws, rt_, 3, f"=SUM(C{first_m}:C{last_m})", BOLD, EUR0)
put(ws, rt_, 4, f"=SUMPRODUCT(C{first_m}:C{last_m},D{first_m}:D{last_m})/C{rt_}", BOLD, PCT2)
for col in (5, 6, 7, 8, 9, 11, 13, 15):
    cl = get_column_letter(col)
    put(ws, rt_, col, f"=SUM({cl}{first_m}:{cl}{last_m})", BOLD, EUR0)
put(ws, rt_, 10, f"=K{rt_}/C{rt_}", BOLD, PCT2)
put(ws, rt_, 12, f"=SUMPRODUCT(C{first_m}:C{last_m},L{first_m}:L{last_m})/C{rt_}", BOLD, PCT2)
put(ws, rt_, 14, f"=SUMPRODUCT(C{first_m}:C{last_m},N{first_m}:N{last_m})/C{rt_}", BOLD, PCT2)
for c in range(1, 16):
    ws.cell(rt_, c).border = Border(top=Side(style="thin", color="15233C"))
r = rt_ + 2

# ---- distributor conditions
DC0 = r
put(ws, DC0, 1, "Distributor conditions per market and parts category (decided)", SEC)
put(ws, DC0 + 1, 1, ("Hold = pays today's price. Own + extra = own increase plus the recovery extra, on parts with no aftermarket alternative "
                     "found only. Own = own increase only. Where Lighting says Hold, lighting parts are held whatever their category. "
                     "The list itself stays one price per part."), SUB)
header(ws, DC0 + 2, ["Market", "Code", "Service parts", "Repair parts", "Body and collision parts", "Lighting", "Note"], height=32)
note_of = {
    "UMI": "Service parts stay at today's price until UMI's share of leasing fleets is known (open, per the paper).",
    "UTI": "Lighting only (EUR 133,712 billed on 87 part numbers). Truck body panels are not held (delivery times, not price).",
    "IUK": "Exemption from the extra is the Summary switch (default OFF: carries the extra).",
    "UKRAINE": "Ukraine takes the normal treatment (decided).",
    "ARMENIA": "Own increase only. Whether it reaches Armenia depends on the open price-basis decision.",
    "KAZAKHSTAN": "Own increase only. Whether it reaches Kazakhstan depends on the open price-basis decision.",
}
for i, m in enumerate(markets):
    rr = DC0 + 3 + i
    put(ws, rr, 1, mk_name(m), BODY)
    put(ws, rr, 2, m, DATA)
    if m in CIS:
        vals = ["Own, no extra"] * 3 + ["Own, no extra"]
    else:
        svc = "Hold" if m in held_service else "Own"
        if m == EXEMPT:
            ext = f'=IF({SW}=1,"Own","Own + extra")'
        else:
            ext = "Own + extra"
        rep = ext
        body = "Hold" if m == "UMI" else ext
        light = "Hold" if m in ("UMI", "UTI") else "As its category"
        vals = [svc, rep, body, light]
    for j, v in enumerate(vals):
        put(ws, rr, 3 + j, v, BOLD if v == "Hold" else BODY)
    put(ws, rr, 7, note_of.get(m, ""), SUB)
r = DC0 + 3 + len(markets)
put(ws, r, 1, ("'Own + extra' applies only to repair and body parts with no aftermarket alternative found; every other part in that "
               "column carries its own increase. The extra is the same number of points on every such part, up to its ceiling "
               "(own factory increase + 5 points)."), SUB, align=WRAP)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
ws.row_dimensions[r].height = 30
r += 2

# ---- Armenia and Kazakhstan
AK0 = r
put(ws, AK0, 1, "Armenia and Kazakhstan: own increase only (Jerome chose option A)", SEC)
c1, c2 = mt_rows[CIS[0]], mt_rows[CIS[1]]
note_ak = [
    ("What the layer does", "Armenia and Kazakhstan keep their own IML/IMIT-based increase. No hold and no recovery extra applies to "
                            "them, in either switch position."),
    ("What is open", "Whether that increase actually reaches them depends on the separate decision on their price basis, which is "
                     "still open. Until it is decided, the layer counts their increase inside the +5.00% total as if it reaches them."),
]
for i, (a, b) in enumerate(note_ak):
    put(ws, AK0 + 1 + i, 1, a, BOLD)
    put(ws, AK0 + 1 + i, 2, b, BODY, align=WRAP)
    ws.merge_cells(start_row=AK0 + 1 + i, start_column=2, end_row=AK0 + 1 + i, end_column=8)
    ws.row_dimensions[AK0 + 1 + i].height = 30
header(ws, AK0 + 4, ["", "Billed EUR", "Own increase", "EUR at own increase"], height=30)
for k, (rr_src, m) in enumerate(((c1, CIS[0]), (c2, CIS[1]))):
    put(ws, AK0 + 5 + k, 1, mk_name(m), BODY)
    put(ws, AK0 + 5 + k, 2, f"=C{rr_src}", BODY, EUR0)
    put(ws, AK0 + 5 + k, 3, f"=J{rr_src}", BODY, PCT2)
    put(ws, AK0 + 5 + k, 4, f"=K{rr_src}", BODY, EUR0)
put(ws, AK0 + 7, 1, "Both", BOLD)
put(ws, AK0 + 7, 2, f"=B{AK0 + 5}+B{AK0 + 6}", BOLD, EUR0)
put(ws, AK0 + 7, 3, f"=D{AK0 + 7}/B{AK0 + 7}", BOLD, PCT2)
put(ws, AK0 + 7, 4, f"=D{AK0 + 5}+D{AK0 + 6}", BOLD, EUR0)
put(ws, AK0 + 8, 1, "If it does not reach them: total increase would be, EUR", BODY)
put(ws, AK0 + 8, 2, f"=D{rec['total']}-D{AK0 + 7}", BOLD, EUR0)
put(ws, AK0 + 8, 3, f"=B{AK0 + 8}/D{rec['base']}", BOLD, PCT3)
put(ws, AK0 + 8, 4, "weighted increase on the whole billed base", SUB)
ak_total_row, ak_nocis_row = AK0 + 7, AK0 + 8
r = AK0 + 10

# ---- checks
CK0 = r
put(ws, CK0, 1, "Checks: every line should read OK", SEC)
header(ws, CK0 + 1, ["Check", "Value", "Expected", "Result"], height=24)
SVc = SVN
ck = [
    ("Billed base in the layer equals the billed base of the proposal (EUR)", f"=SUM({Bc})", f"=SUM(Proposal!$G$2:$G${PROP_LAST})", EUR2,
     "ABS({v}-{e})<0.05"),
    ("Every part number of the proposal is on 'Layer by part'", f"=COUNTA({lp_rng('pn')})", f"=COUNTA(Proposal!$A$2:$A${PROP_LAST})", "#,##0",
     "{v}={e}"),
    ("Every part x market row finds its part (rows with an error)", f"=SUMPRODUCT(--ISERROR({pm_rng('lprow')}))", 0, "0", "{v}={e}"),
    ("Every part finds its rows on the part x market sheet (pointers off)", f"=SUM({lp_rng('ptr')})", 0, "0", "{v}={e}"),
    ("Own increase in the layer adds up to the proposal's extra euro (Summary B13)", f"=SUMPRODUCT({Bc},{Dc})", "=Summary!$B$13", EUR2,
     "ABS({v}-{e})<0.05"),
    ("Total after market treatment equals the target: switch OFF (EUR)", f"=B{rec['total']}", f"=B{rec['target']}", EUR2, "ABS({v}-{e})<0.5"),
    ("Total after market treatment equals the target: switch ON (EUR)", f"=C{rec['total']}", f"=C{rec['target']}", EUR2, "ABS({v}-{e})<0.5"),
    ("Weighted increase equals the Summary target: switch OFF", f"=B{rec['pct']}", "=Summary!$B$5", PCT3, "ABS({v}-{e})<0.000000001"),
    ("Weighted increase equals the Summary target: switch ON", f"=C{rec['pct']}", "=Summary!$B$5", PCT3, "ABS({v}-{e})<0.000000001"),
    ("Own - given up - cut + extra = total, both positions (largest gap, EUR)", f"=MAX(ABS(B{rec['ident']}),ABS(C{rec['ident']}))", 0, EUR2,
     "{v}<0.01"),
    ("Solver lands on the recovery needed: switch OFF and ON (largest gap, EUR)", f"=MAX(ABS({SVc}$B$15),ABS({SVc}$C$15))", 0, EUR2, "{v}<0.01"),
    ("Solver can reach the target within the ceiling (both positions)", f'=IF(AND({SVc}$B$16="yes",{SVc}$C$16="yes"),1,0)', 1, "0", "{v}={e}"),
    ("Service parts get no extra, both positions (EUR)", f"=B{rec['svc']}+C{rec['svc']}", 0, EUR2, "ABS({v})<0.005"),
    ("Armenia and Kazakhstan: no hold, no extra, own increase, both positions (EUR vs own increase)",
     (f'=SUMPRODUCT(--({Gc}="own only"),{Bc},ABS({pm_rng("inc_off")}-{Dc}))+SUMPRODUCT(--({Gc}="own only"),{Bc},ABS({pm_rng("inc_on")}-{Dc}))'),
     0, EUR2, "ABS({v})<0.005"),
    ("Exempt market gets no extra when the switch is ON (EUR)", f"=C{rec['iuk']}", 0, EUR2, "ABS({v})<0.005"),
    ("Per-market table adds up to the reconciliation (recovered, given up, total; largest gap EUR)",
     f"=ROUND(MAX(ABS(I{mt_total}-D{rec['extra']}),ABS(E{mt_total}-D{rec['given']}),ABS(K{mt_total}-D{rec['total']})),2)", 0, EUR2, "{v}<0.5"),
    ("Published figures reproduced at the default settings (rows marked in column G above)",
     f'=COUNTIF(G{RR0 + 2}:G{rec["nparts"]},"CHECK")', 0, "0", "{v}={e}"),
    ("Summary switch holds 0 or 1", f"={SW}", "0 or 1", "0", "OR({v}=0,{v}=1)"),
]
ck_first = CK0 + 2
for i, (lab, v, e, nf, cond) in enumerate(ck):
    rr = ck_first + i
    put(ws, rr, 1, lab, BODY, align=WRAP)
    put(ws, rr, 2, v, BODY, nf)
    put(ws, rr, 3, e, BODY, nf)
    put(ws, rr, 4, '=IF(' + cond.format(v=f"B{rr}", e=f"C{rr}") + ',"OK","CHECK")', BOLD)
    ws.row_dimensions[rr].height = 28 if len(lab) > 78 else 16
ck_last = ck_first + len(ck) - 1
put(ws, ck_last + 1, 1, "All market layer checks", BOLD)
put(ws, ck_last + 1, 4, f'=IF(COUNTIF(D{ck_first}:D{ck_last},"OK")={len(ck)},"OK","CHECK")', BOLD)
ALLCK = f"{ML}$D${ck_last + 1}"
ws.conditional_formatting.add(f"D{ck_first}:D{ck_last + 1}", CellIsRule(operator="equal", formula=['"CHECK"'], font=RED))
ws.conditional_formatting.add(f"D{ck_first}:D{ck_last + 1}", CellIsRule(operator="equal", formula=['"OK"'], font=GREEN))
ws.conditional_formatting.add(f"G{RR0 + 2}:G{rec['nparts']}", CellIsRule(operator="equal", formula=['"CHECK"'], font=RED))
ws.conditional_formatting.add(f"G{RR0 + 2}:G{rec['nparts']}", CellIsRule(operator="equal", formula=['"OK"'], font=GREEN))
r = ck_last + 3

# ---- sources and how to read
SR0 = r
put(ws, SR0, 1, "Where each block of values comes from", SEC)
sources = [
    ("Part numbers and descriptions (blue, 'Layer by part')", "Copied as values from the Proposal sheet of this workbook, in part number order. Own increase, own factory increase, "
     "current list and pad kit flag are read live from the Proposal sheet by part number."),
    ("Parts category, 'no aftermarket alternative found', lubricant flag (blue, 'Layer by part')",
     "Copied as values from 02_dashboards/pricing/_build/price_5pct_proposal_2026-09-29/room_to_raise_2026-10-02/room_to_raise_by_part_2026-10-02.csv "
     "(columns segment, captive_strict, lubricant), built by build_room_to_raise_20261002.py on the approved parts categories of 2 October 2026. "
     "Checked on 4 October against the current approved release 2026-10-02-chassis-frame: 0 of 15,273 parts change between service, repair and body. "
     "Service = scheduled-service parts (BVP cross-reference service categories and the master service flag); body = family Accident and Body; repair = the rest. "
     "No aftermarket alternative found = no usable competitor part number, no aftermarket price, no BVP alternative, not a competitive family, not measured lost or contested."),
    ("Billed EUR per part and market (blue, 'Layer by part and market')",
     "Copied as values: 47,617 in-scope lines of 01_data/00_derived/price_bp_weighted_compare_pn.csv (both factory prices present), summed per part number and "
     "distributor code (distributor_dimension.csv): 45,581 rows, EUR 32,595,852.63. Agrees with room_to_raise_by_part_market_2026-10-02.csv within its 6-significant-digit rounding."),
    ("Hold applied (blue, 'Layer by part and market')",
     "Copied as values from room_to_raise_by_part_market_2026-10-02.csv (column hold_reason): service parts in 8 markets (market_exercise_decisions_2026-09-30.json), "
     "Israel D-Max distributor body, collision and lighting, Israel trucks distributor lighting (2 Oct 2026 paper). 7,833 rows."),
    ("Published figures for comparison (blue, columns E and F above)",
     "room_to_raise_variant_B_iuk_exempt_2026-10-02.json (as published and Isuzu UK exempt), the 2 Oct 2026 paper (EUR 388,914) and "
     "room_to_raise_scenarios_2026-10-02.csv (ceiling cut EUR 7,654). They are compared only while Summary B5 to B9 are at their delivered values."),
]
for i, (a, b) in enumerate(sources):
    rr = SR0 + 1 + i
    put(ws, rr, 1, a, BOLD, align=WRAP)
    put(ws, rr, 2, b, BODY, align=WRAP)
    ws.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=8)
    ws.row_dimensions[rr].height = 14 * max(2, -(-len(b) // 95)) + 4
r = SR0 + 1 + len(sources) + 1
put(ws, r, 1, "How it works", SEC)
how = [
    "1. Every line on 'Layer by part and market' is one of: held (pays today's price), Armenia or Kazakhstan (own increase only), or free (own increase, plus the extra where the part carries it).",
    "2. The extra is one number of points (t), the same on every part that carries it, limited by the part's ceiling (own factory increase + 5 points). 'Layer solver' finds t so the total lands on the target.",
    "3. Switch OFF: Isuzu UK pays the list increase like everyone else. Switch ON: Isuzu UK pays its own increase (limited by the ceiling) on every part and the other free markets carry a higher t.",
    "4. The list price per part (sheet 'Layer by part', column New list EUR) is one price; holds and the exemption are distributor conditions on top of it.",
    "5. Pad kits stay at today's price (Summary B9); the two lubricant part numbers in the base carry no increase and no extra. If Summary B5 to B9 are changed, everything re-solves.",
]
for i, t in enumerate(how):
    rr = r + 1 + i
    put(ws, rr, 1, t, BODY, align=WRAP)
    ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=8)
    ws.row_dimensions[rr].height = 30
for col, wd in zip("ABCDEFGHIJKLMNO", [66, 16, 18, 17, 16, 16, 18, 22, 16, 16, 18, 14, 16, 14, 16]):
    ws.column_dimensions[col].width = wd
ws.freeze_panes = "A4"

# =================================================================== Summary: the switch and a read-out
ws = ws_sum
put(ws, 4, 4, "Market treatment of the 2 October 2026 paper (sheet 'Market layer')", SEC)
c = put(ws, 5, 4, 0, INPUT, "0", fill=YELLOW)
c.alignment = Alignment(horizontal="center", vertical="center")
dv = DataValidation(type="list", formula1='"0,1"', allow_blank=False, showErrorMessage=True,
                    errorTitle="Switch", error="Enter 0 (off) or 1 (on).")
ws.add_data_validation(dv)
dv.add("D5")
sum_rows = [
    (5, "Isuzu UK (D-Max) exempt from the recovery extra (1 = on, 0 = off). Default 0 = as in the paper: Isuzu UK carries the extra. Not decided.", None, None),
    (6, "Total increase after market treatment, EUR (equals the target in both positions)", f"={ML}D{rec['total']}", EUR0),
    (7, "Weighted increase after market treatment", f"={ML}D{rec['pct']}", PCT2),
    (8, "Recovery extra on repair and body parts, EUR", f"={ML}D{rec['extra']}", EUR0),
    (9, "Market layer checks (all must read OK)", f"={ALLCK}", None),
]
for rr, lab, fx, nf in sum_rows:
    put(ws, rr, 5, lab, BODY, align=WRAP)
    ws.merge_cells(start_row=rr, start_column=5, end_row=rr, end_column=8)
    if fx:
        cc = put(ws, rr, 4, fx, BOLD, nf)
        cc.alignment = Alignment(horizontal="center", vertical="center")
ws.conditional_formatting.add("D9", CellIsRule(operator="equal", formula=['"CHECK"'], font=RED))
ws.conditional_formatting.add("D9", CellIsRule(operator="equal", formula=['"OK"'], font=GREEN))

# Checks sheet: one extra line (row 13 was empty)
assert ws_ck["A13"].value is None and ws_ck["A14"].value is not None
put(ws_ck, 13, 1, "Market layer: all checks on the 'Market layer' sheet", BODY, align=WRAP)
put(ws_ck, 13, 2, f'=COUNTIF({ML}$D${ck_first}:$D${ck_last},"OK")', BODY, "0")
put(ws_ck, 13, 3, len(ck), BODY, "0")
put(ws_ck, 13, 4, '=IF(B13=C13,"OK","CHECK")', BOLD)

# Read me: appended section (the original text is untouched)
ws = ws_read
rr0 = ws.max_row + 2
add = [
    ("Market layer (added 4 October 2026)", SEC),
    ("Sheet 'Market layer' shows how the market decisions of the 2 October 2026 paper land per part and per market, on top of the same +5.00% "
     "proposal: holds at today's price (service parts in 8 markets, Israel body, collision and lighting), the recovery extra on repair and body parts "
     "with no aftermarket alternative, and Armenia and Kazakhstan on their own increase. The total stays exactly on the target.", BODY),
    ("Summary D5 is the Isuzu UK (D-Max) exemption switch (0 = Isuzu UK carries the extra, as in the paper; 1 = exempt, the other markets carry more). "
     "The layer sheets are 'Layer by part and market', 'Layer by part' and 'Layer solver'. Their checks are at the bottom of 'Market layer'.", BODY),
]
for i, (t, f_) in enumerate(add):
    cc = put(ws, rr0 + i, 1, t, f_, align=WRAP)
    if f_ is BODY:
        ws.row_dimensions[rr0 + i].height = 13.5 * -(-len(t) // 140) + 4

# sheet order: Read me, Summary, Market layer, Proposal, ..., Checks, Layer by part and market, Layer by part, Layer solver
OUT.parent.mkdir(parents=True, exist_ok=True)
t1 = time.time()
wb.save(OUT)
print(f"saved {OUT} in {time.time() - t1:.0f}s ({OUT.stat().st_size / 1e6:.1f} MB)")

# =================================================================== write the layer addresses the verifier needs
addr = {"market_layer": {"rec": rec, "mt_first": first_m, "mt_last": last_m, "mt_total": mt_total, "markets": markets,
                          "dc0": DC0, "ak0": AK0, "ak_total_row": ak_total_row, "ak_nocis_row": ak_nocis_row, "ck_first": ck_first,
                          "ck_last": ck_last, "rr0": RR0, "settings": {"ceil": R_SET_CEIL, "exempt": R_SET_EXEMPT, "cis": R_SET_CIS}},
        "lp": {"first": LP_FIRST, "last": LP_LAST, "cols": lc}, "pm": {"first": PM_FIRST, "last": PM_LAST, "cols": pc},
        "built": time.strftime("%Y-%m-%d %H:%M"), "xlsx": str(OUT)}
(OUT.parent / "grid_addresses_2026-10-11.json").write_text(json.dumps(addr, indent=1), encoding="utf-8")
(OUT.parent / "OPEN_Price_Increase_5pct_Proposal_GRID_DRAFT_2026-10-11.cmd").write_text(
    '@echo off\r\nstart "" "%~dp0Price_Increase_5pct_Proposal_GRID_DRAFT_2026-10-11.xlsx"\r\n', encoding="ascii")
shutil.rmtree(tmpd, ignore_errors=True)
print("done", round(time.time() - t0), "s")
print("PACKAGE_A_REPRO: run recalc_excel.py then verify against "
      "EUR 1629793 total / 388914 given up / 7654 ceiling cut / 396568 recovered / t 3.727 OFF / 4.837 ON")
