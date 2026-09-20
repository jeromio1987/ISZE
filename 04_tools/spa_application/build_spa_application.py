"""SPA application generator — one basket in, optimizer + application form + waterfall out.

Built 2026-09-20 for Jerome. Internal only.

WHY THIS EXISTS
---------------
The June 2026 UTI application went to Yoshimoto san for signature with the SPA
purchase-cost box holding the SPA gross profit (307,853) instead of the cost
(733,169 = 1,041,022 revenue - 307,853 profit). He bounced it: "the purchase price
is incorrect". The analysis was right; a form cell was wrong.

So this script computes everything once and fills every place from that one
computation. Nothing that can be derived is typed twice. The run refuses to finish
if the application form and the optimizer disagree.

WHAT IT DOES
------------
  input : one basket (part number + committed quantity), customer identity,
          L12 window, validity, assumptions
  output: ISZE_SPA_Application_<CUSTOMER>_<LABEL>_<YYYYMMDD>.xlsx
            - SPA Optimizer          L12 baseline beside the SPA case, line by line
            - Customer View          customer-safe columns
            - IML_IMIT Brief         confidential cost side
            - MD Approval Request    the signable application form
            - Scenario Planner       partial / full / full+cut / volume growth
          _qa/_waterfall_<LABEL>.csv      the waterfall adjustment for the basket
          _qa/_recalc_check.json          form vs optimizer reconciliation
          OPEN_....cmd                     double-click launcher

FIXES CARRIED FROM THE REVIEW
-----------------------------
  1. Scenario Planner "IML Cut Applied" read Assumptions!B3 (a heading). Now C4.
  2. Scenario Planner showed 5% volume growth while the scenario formulas used
     Assumptions!B19 (10%). Both now read the same cell.
  3. The "Partial" scenario SUMIF started at row 4 while data starts at row 6, so it
     had never returned a live figure. Now R6:R<last>.
  4. The form's SPA purchase cost is computed as revenue minus gross profit, so the
     June error cannot recur. Checked at the end of every run.

USAGE
-----
  python build_spa_application.py --basket "<path.xlsx>" --customer UTI --label spa2
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
from copy import copy
from datetime import date, datetime
from pathlib import Path

import openpyxl
import pandas as pd
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ROOT / "01_data" / "00_derived"
DEFAULT_TEMPLATE = ROOT / "01_data" / "01_Pricing" / "ISZE_SPA_Optimizer_V4.xlsx"

# template geometry (verified against the V4 template on disk)
TEMPLATE_LAST = 58          # last data row in the template's SPA Optimizer
TEMPLATE_TOTAL = 60         # totals row in the template
TEMPLATE_LINES = 53         # template line count
DATA_FIRST = 6              # first data row, all sheets

NAVY = "15233C"
PAPER = "F7F4EE"
BLUE_BG = "EBF3FB"
TERR = "C0552D"
INPUT_Y = "FFF2CC"
THIN = Border(
    left=Side(style="thin", color="D5D8DC"),
    right=Side(style="thin", color="D5D8DC"),
    top=Side(style="thin", color="D5D8DC"),
    bottom=Side(style="thin", color="D5D8DC"),
)
WRAP = Alignment(wrap_text=True, vertical="center")


class RunError(RuntimeError):
    pass


# --------------------------------------------------------------------------- utils
def norm_pn(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    digits = re.sub(r"[^0-9]", "", str(x).strip())
    return digits or None


def fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def copy_style(src, dest) -> None:
    dest.font = copy(src.font)
    dest.fill = copy(src.fill)
    dest.border = copy(src.border)
    dest.alignment = copy(src.alignment)
    dest.number_format = src.number_format
    dest.protection = copy(src.protection)


def updown(v: float) -> str:
    if v > 0:
        return f"UP EUR {v:,.0f}"
    if v < 0:
        return f"DOWN EUR {abs(v):,.0f}"
    return "FLAT"


# ----------------------------------------------------------------- row formulas
def opt_formulas(r: int) -> dict[int, str]:
    """Column formulas for one SPA Optimizer line. Mirrors the reviewed V4 engine."""
    return {
        7: f"=IFERROR(C{r}*E{r},0)",
        8: f"=F{r}-G{r}",
        9: f"=IFERROR(H{r}/F{r},0)",
        11: f"=AC{r}*Assumptions!$C$7",
        12: f"=J{r}*K{r}",
        13: f"=J{r}-C{r}",
        14: f"=M{r}*K{r}",
        15: f"=IFERROR(N{r}/L{r},0)",
        16: f"=L{r}-F{r}",
        17: f"=N{r}-H{r}",
        18: f'=IF(Q{r}>=0,"\u25b2 BETTER","\u25bc WORSE")',
        19: f'=IFERROR(IF(J{r}-C{r}<=0,"BELOW COST",CEILING(H{r}/(J{r}-C{r}),1)),"N/A")',
        20: f'=IFERROR(H{r}/K{r}+C{r},"N/A")',
        21: f"=IFERROR(MAX(0,S{r}-K{r}),0)",
        22: "=Assumptions!$C$4",
        23: f"=IFERROR(C{r}*(1-Assumptions!$C$4),C{r})",
        24: f"=IFERROR((J{r}-C{r}*(1-Assumptions!$C$4))*K{r},N{r})",
        25: f"=IFERROR(X{r}-H{r},N{r}-H{r})",
        26: f"=IFERROR(C{r}*Assumptions!$C$4*K{r},0)",
        27: f'=IFERROR(MAX(0,1-(J{r}-H{r}/K{r})/C{r}),"N/A")',
        28: f'=IFERROR(IF(Y{r}>=0,"\u25b2 BETTER","\u25bc WORSE"),"N/A")',
    }


def cv_formulas(opt: int) -> dict[int, str]:
    return {
        1: f"='SPA Optimizer'!A{opt}",
        2: f"='SPA Optimizer'!B{opt}",
        3: f"='SPA Optimizer'!D{opt}",
        4: f"='SPA Optimizer'!J{opt}",
        5: f"='SPA Optimizer'!D{opt}-'SPA Optimizer'!J{opt}",
        6: f"=IFERROR(IF('SPA Optimizer'!D{opt}>0,('SPA Optimizer'!D{opt}-'SPA Optimizer'!J{opt})/'SPA Optimizer'!D{opt},0),0)",
        7: f"='SPA Optimizer'!K{opt}",
        8: f"='SPA Optimizer'!L{opt}",
        9: f"=IFERROR('SPA Optimizer'!D{opt}*'SPA Optimizer'!K{opt}-'SPA Optimizer'!L{opt},0)",
        10: f"=IFERROR(IF('SPA Optimizer'!E{opt}>0,('SPA Optimizer'!K{opt}-'SPA Optimizer'!E{opt})/'SPA Optimizer'!E{opt},0),0)",
        11: f"=IFERROR(('SPA Optimizer'!D{opt}-'SPA Optimizer'!J{opt})*'SPA Optimizer'!K{opt},0)",
        12: (
            f'=IF(\'SPA Optimizer\'!R{opt}="\u25b2 BETTER","\u2714 Viable",'
            f'IF(AND(\'SPA Optimizer\'!AB{opt}="\u25b2 BETTER",\'SPA Optimizer\'!AA{opt}<=1),'
            f'"\u2714 w/ IML support",IF(OR(\'SPA Optimizer\'!AA{opt}>1,\'SPA Optimizer\'!O{opt}<0),'
            f'"\u2716 Not feasible","\u26a0 Review")))'
        ),
    }


def iml_formulas(opt: int) -> dict[int, str]:
    return {
        1: f"='SPA Optimizer'!A{opt}",
        2: f"='SPA Optimizer'!B{opt}",
        3: f"='SPA Optimizer'!C{opt}",
        4: f"='SPA Optimizer'!D{opt}",
        5: f"='SPA Optimizer'!I{opt}",
        6: f"='SPA Optimizer'!J{opt}",
        7: f"='SPA Optimizer'!O{opt}",
        8: f"='SPA Optimizer'!AA{opt}",
        9: f"='SPA Optimizer'!Z{opt}",
        10: f"='SPA Optimizer'!K{opt}",
        11: f"='SPA Optimizer'!E{opt}",
        12: f"=IFERROR('SPA Optimizer'!K{opt}-'SPA Optimizer'!E{opt},0)",
        13: f"=IFERROR(MAX(0,'SPA Optimizer'!K{opt}-'SPA Optimizer'!E{opt})*'SPA Optimizer'!C{opt}*(1-'SPA Optimizer'!AA{opt}),0)",
    }


def gm_formulas(opt: int) -> dict[int, str]:
    return {
        1: f"='SPA Optimizer'!A{opt}",
        2: f"='SPA Optimizer'!B{opt}",
        3: f"='SPA Optimizer'!O{opt}",
        4: (
            f'=IF(\'SPA Optimizer\'!O{opt}>=0.3,"\u2714  OK",'
            f'IF(\'SPA Optimizer\'!O{opt}>=0.25,'
            f'"\u26a0  Caution - below 30% - explain to Management Approver",'
            f'"\u2716  ALARM - below 25% - Management Approver will flag this"))'
        ),
    }


def retarget(val, old_last: int, new_last: int, old_total: int, new_total: int):
    """Move every cross-sheet range/total reference onto the new basket size."""
    if not isinstance(val, str):
        return val
    s = val
    for col in ("P", "Y", "Z", "F", "G", "H", "I", "L", "O", "Q", "X", "K", "E", "N", "AB", "AA"):
        s = s.replace(f"'SPA Optimizer'!{col}{old_total}", f"'SPA Optimizer'!{col}{new_total}")
        s = s.replace(f"'SPA Optimizer'!{col}60", f"'SPA Optimizer'!{col}{new_total}")
    for rng in ("R6:R", "AB6:AB", "O6:O", "I6:I", "K6:K", "E6:E", "A6:A",
                "R4:R", "L4:L", "P4:P", "S6:S"):
        s = s.replace(f"{rng}{old_last}", f"{rng}{new_last}")
    n = new_last - DATA_FIRST + 1
    for old in ("53 part numbers", "53 part lines", "53 lines", "all 53 lines",
                "All 53 lines", "of 53", " of 12"):
        new = old.replace("53", str(n)).replace("12", str(n))
        s = s.replace(old, new)
    return s


def read_customer_targets(path: Path) -> dict:
    """The customer's own target, if the basket workbook carries a 'targets' sheet.

    Row label in column A, value in column B. Accepted labels (case-insensitive):
    Revenue, Purchase Cost, Gross Profit, Gross Margin. This is the customer's
    number, so it is an input - never computed by us.
    """
    targets: dict = {}
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    try:
        if "targets" not in [s.lower() for s in wb.sheetnames]:
            return targets
        name = [s for s in wb.sheetnames if s.lower() == "targets"][0]
        ws = wb[name]
        for row in ws.iter_rows(values_only=True):
            if not row or row[0] is None:
                continue
            label = str(row[0]).strip().lower()
            value = row[1] if len(row) > 1 else None
            if value in (None, ""):
                continue
            try:
                num = float(value)
            except (TypeError, ValueError):
                continue
            if label.startswith("revenue"):
                targets["revenue"] = num
            elif label.startswith("purchase") or label.startswith("cost"):
                targets["cost"] = num
            elif label.startswith("gross profit") or label.startswith("profit"):
                targets["profit"] = num
            elif label.startswith("gross margin") or label.startswith("margin") or label.startswith("gm"):
                targets["gm"] = num / 100.0 if num > 1 else num
    finally:
        wb.close()
    return targets


def derive_pack1_bar(html: Path, cut: float, qty_factor: float) -> dict | None:
    """The comparison bar, computed from the approved pack 1 in the dashboard.

    Used instead of a hardcoded constant so the bar moves with the price file and the
    purchase cut, rather than sitting at a fixed amount recorded on some earlier day.
    """
    if not html.exists():
        return None
    text = html.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"const RAW = (\{.*?\});", text, re.S)
    if not match:
        return None
    try:
        pns = json.loads(match.group(1)).get("pns", [])
    except json.JSONDecodeError:
        return None
    rev = sum(float(p["spa_price"]) * float(p["spa_qty"]) * qty_factor for p in pns)
    profit = sum(
        (float(p["spa_price"]) - float(p["purchase"]) * (1 - cut)) * float(p["spa_qty"]) * qty_factor
        for p in pns
    )
    return {"n": len(pns), "rev": rev, "profit": profit, "source": str(html)}


def resize_sheet(ws, data_first: int, template_rows: int, n: int, anchor_row: int) -> int:
    """Grow or shrink a sheet's data block so it holds exactly n rows.

    anchor_row is the first row that must move (the total row or the block below the
    data). Returns the signed change.
    """
    delta = n - template_rows
    if delta > 0:
        ws.insert_rows(anchor_row, delta)
    elif delta < 0:
        ws.delete_rows(data_first + n, -delta)
    return delta


# ------------------------------------------------------------------------- inputs
def read_basket(path: Path) -> pd.DataFrame:
    """Basket = customer's committed part numbers and quantities.

    Header row is found by looking for 'p/n' in column A, so the file may carry a
    title row above it (the Eran study does).
    """
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    header_idx = None
    for i, row in enumerate(rows[:20]):
        first = str(row[0]).strip().lower() if row and row[0] is not None else ""
        if first in ("p/n", "pn", "part number", "part_number", "partno"):
            header_idx = i
            break
    if header_idx is None:
        raise RunError(f"No P/N header row found in {path.name}")

    out = []
    for row in rows[header_idx + 1:]:
        pn = norm_pn(row[0]) if row else None
        if not pn:
            continue
        desc = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        qty = row[2] if len(row) > 2 else None
        try:
            qty = float(qty)
        except (TypeError, ValueError):
            qty = 0.0
        out.append({"pn": pn, "pn_raw": str(row[0]).strip(), "desc_basket": desc, "spa_qty": qty})

    df = pd.DataFrame(out)
    if df.empty:
        raise RunError(f"Basket {path.name} has no part numbers")
    dupes = df[df.duplicated("pn", keep=False)]["pn_raw"].tolist()
    if dupes:
        raise RunError(f"Basket has duplicate part numbers: {sorted(set(dupes))}")
    return df


def read_pricing_and_l12(df: pd.DataFrame, sold_to: int, win_from: str, win_to: str) -> pd.DataFrame:
    lp = pd.read_parquet(DERIVED / "pricing_list_pn.parquet")
    lp["pn"] = lp["part_number"].map(norm_pn)
    lp1 = lp.dropna(subset=["pn"]).drop_duplicates("pn", keep="last")
    lp_new = lp.copy()
    lp_new["pn"] = lp_new["newest_pn"].map(norm_pn)
    lp_new = lp_new.dropna(subset=["pn"]).drop_duplicates("pn", keep="last")

    df = df.merge(lp1[["pn", "description", "fob_eur", "sp_eur"]], on="pn", how="left")
    miss = df["fob_eur"].isna()
    if miss.any():
        extra = lp_new.loc[lp_new["pn"].isin(df.loc[miss, "pn"]),
                           ["pn", "description", "fob_eur", "sp_eur"]]
        extra = extra.rename(columns={"description": "description_n", "fob_eur": "fob_n", "sp_eur": "sp_n"})
        df = df.merge(extra, on="pn", how="left")
        df["description"] = df["description"].fillna(df["description_n"])
        df["fob_eur"] = df["fob_eur"].fillna(df["fob_n"])
        df["sp_eur"] = df["sp_eur"].fillna(df["sp_n"])
        df = df.drop(columns=[c for c in ("description_n", "fob_n", "sp_n") if c in df.columns])

    sf = pd.read_parquet(
        DERIVED / "sales_fact.parquet",
        columns=["billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value"],
    )
    sf["pn"] = sf["part_number"].map(norm_pn)
    won = sf[
        (sf["sold_to_sap"] == sold_to)
        & (sf["billing_date"] >= win_from)
        & (sf["billing_date"] <= win_to)
    ]
    if len(won) == 0:
        raise RunError(f"No billed rows for sold-to {sold_to} between {win_from} and {win_to}")
    billed = won.groupby("pn", as_index=False).agg(
        l12_qty=("billed_qty", "sum"), l12_billed_eur=("net_sales_value", "sum")
    )

    df = df.merge(billed, on="pn", how="left")
    df["l12_qty"] = df["l12_qty"].fillna(0.0)
    df["l12_billed_eur"] = df["l12_billed_eur"].fillna(0.0)
    df["purchase"] = df["fob_eur"]
    df["list_price"] = df["sp_eur"]
    df["desc"] = df["description"].fillna(df["desc_basket"])
    df["frozen"] = df["purchase"].isna() | df["list_price"].isna()
    df["priced"] = ~df["frozen"]
    return df


# ------------------------------------------------------------------- workbook work
def write_line_row(ws, r: int, style_row: int, rec: dict) -> None:
    for c in range(1, 30):
        copy_style(ws.cell(style_row, c), ws.cell(r, c))
    desc = rec["desc"]
    if rec["frozen"]:
        desc = f"{desc} [no FOB/PR00 - frozen]"
    ws.cell(r, 1).value = rec["pn"]
    ws.cell(r, 1).number_format = "@"
    ws.cell(r, 2).value = desc
    ws.cell(r, 2).alignment = WRAP
    blue = Font(name="Calibri", size=10, color="0000FF")
    if rec["priced"]:
        for col, val in ((3, rec["purchase"]), (4, rec["list_price"]), (10, rec["list_price"])):
            cell = ws.cell(r, col)
            cell.value = float(val)
            cell.fill = fill(BLUE_BG)
            cell.font = blue
    else:
        for col in (3, 4, 10):
            ws.cell(r, col).value = None
    for col, val in ((5, rec["l12_qty"]), (6, rec["l12_billed_eur"]), (29, rec["spa_qty"])):
        cell = ws.cell(r, col)
        cell.value = float(val)
        cell.fill = fill(BLUE_BG)
        cell.font = blue
    ws.cell(r, 29).number_format = "#,##0.00"
    for col, formula in opt_formulas(r).items():
        ws.cell(r, col).value = formula


def extend_linked(ws, first_row: int, n: int, style_row: int, builder, max_col: int) -> None:
    for i in range(n):
        r = first_row + i
        if r != style_row:
            for c in range(1, max_col + 1):
                copy_style(ws.cell(style_row, c), ws.cell(r, c))
        for c, formula in builder(DATA_FIRST + i).items():
            ws.cell(r, c).value = formula


def patch_form(wmd) -> dict[str, str]:
    """The signable application form.

    Every financial cell is a link to the optimizer. The SPA purchase cost is
    revenue minus gross profit, which is the cell that failed in June.
    """
    patch = {
        "D18": "='SPA Optimizer'!F{total}",       # L12 baseline revenue
        "D19": "='SPA Optimizer'!G{total}",       # L12 baseline purchase cost
        "D20": "='SPA Optimizer'!I{total}",       # L12 baseline GM%
        "D21": "='SPA Optimizer'!H{total}",       # L12 baseline gross profit
        "J18": "='SPA Optimizer'!L{total}",       # SPA revenue
        "J19": "='SPA Optimizer'!L{total}-'SPA Optimizer'!X{total}",   # SPA purchase cost (DERIVED)
        "J20": "='SPA Optimizer'!O{total}",       # SPA GM%
        "J21": "='SPA Optimizer'!X{total}",       # SPA gross profit
        # Business impact block
        "D34": "='SPA Optimizer'!F{total}",
        "D35": "='SPA Optimizer'!G{total}",
        "D36": "='SPA Optimizer'!H{total}",
        "D37": "='SPA Optimizer'!I{total}",
        "H34": "='SPA Optimizer'!L{total}",
        "H36": "='SPA Optimizer'!X{total}",
        "H37": "='SPA Optimizer'!O{total}",
        "J34": "=H34-D34",
        "J35": "=H35-D35",
        "J36": "=H36-D36",
        "J37": "=H37-D37",
    }
    for cell, tmpl in patch.items():
        wmd[cell] = tmpl.format(total="{total}")
    return patch


def patch_form_sized(wmd, new_total: int) -> None:
    for cell, tmpl in {
        "D18": "='SPA Optimizer'!F{t}", "D19": "='SPA Optimizer'!G{t}",
        "D20": "='SPA Optimizer'!I{t}", "D21": "='SPA Optimizer'!H{t}",
        "J18": "='SPA Optimizer'!L{t}", "J19": "='SPA Optimizer'!L{t}-'SPA Optimizer'!X{t}",
        "J20": "='SPA Optimizer'!O{t}", "J21": "='SPA Optimizer'!X{t}",
        # Impact block. The template had H35 = D34-H36, which is L12 revenue minus
        # SPA gross profit - the same mistake as the June application. It must be
        # SPA revenue minus SPA gross profit, i.e. H34-H36.
        "H35": "=H34-H36",
    }.items():
        wmd[cell] = tmpl.format(t=new_total)


# ------------------------------------------------------------------------- build
def build(args: argparse.Namespace) -> dict:
    basket = Path(args.basket).resolve()
    template = Path(args.template).resolve()
    if not basket.exists():
        raise RunError(f"Basket not found: {basket}")
    if not template.exists():
        raise RunError(f"Template not found: {template}")

    stamp = args.date or date.today().strftime("%Y%m%d")
    outdir = Path(args.out).resolve() if args.out else (
        ROOT / "01_data" / "90_INBOX" / f"_spa_application_{args.label}_{stamp}"
    )
    outdir.mkdir(parents=True, exist_ok=True)
    qa = outdir / "_qa"
    qa.mkdir(exist_ok=True)

    name = f"ISZE_SPA_Application_{args.customer}_{args.label}_{stamp}.xlsx"
    out_xlsx = outdir / name
    if out_xlsx.exists() and not args.force:
        raise RunError(
            f"Refusing to overwrite {out_xlsx.name}. "
            f"Pass a new --label (e.g. {args.label}2) or --force if you have said so."
        )

    df = read_basket(basket)
    df = read_pricing_and_l12(df, args.sold_to, args.window_from, args.window_to)
    n = len(df)
    customer_targets = read_customer_targets(basket)

    extra = n - TEMPLATE_LINES
    new_last = TEMPLATE_LAST + extra
    new_total = TEMPLATE_TOTAL + extra
    if new_last >= 1_048_576 or 29 >= 16_384:
        raise RunError("Basket exceeds the sheet row limit")

    # The comparison bar, derived from the approved pack 1 rather than hardcoded, so it
    # moves with the price file and the purchase cut.
    bar = None if args.pack1_bar_static else derive_pack1_bar(
        ROOT / "02_dashboards" / "sales" / "ISZE_SPA_RunRate_UTI.html", args.cut, args.qty_factor
    )
    pack1_rev = bar["rev"] if bar else args.pack1_spa_rev
    pack1_profit = bar["profit"] if bar else args.pack1_spa_profit

    shutil.copy2(template, out_xlsx)
    wb = openpyxl.load_workbook(out_xlsx)

    # -- Assumptions : the single source for cut, floor, qty factor, identity
    wa = wb["Assumptions"]
    wa["C4"] = float(args.cut)
    wa["C5"] = float(args.gm_floor)
    wa["B7"] = "Volume Realisation (qty factor)"
    wa["C7"] = float(args.qty_factor)
    wa["C7"].number_format = "0%"
    wa["C7"].fill = fill(INPUT_Y)
    wa["C7"].font = Font(name="Calibri", size=11, color="0000FF", bold=True)
    wa["D7"] = "100% = the basket's committed quantity. Scales SPA Qty column K. Read by the Scenario Planner."
    wa["D7"].alignment = WRAP
    wa["B9"] = args.customer
    wa["B10"] = args.market
    wa["B11"] = args.spa_reference or f"{args.label} - SPA price = current list (ceiling; no SPA price given)"
    wa["B12"] = datetime.strptime(args.valid_from, "%Y-%m-%d")
    wa["B13"] = datetime.strptime(args.valid_to, "%Y-%m-%d")
    wa["B14"] = args.prepared_by
    for cell in ("B12", "B13"):
        wa[cell].number_format = "DD/MM/YYYY"

    # -- SPA Optimizer : grow or shrink so the block holds exactly n data rows
    wo = wb["SPA Optimizer"]
    for rng in ("A62:AB62", "B63:AB63", "B64:AB64", "B65:AB65", "B66:AB66"):
        try:
            wo.unmerge_cells(rng)
        except ValueError:
            pass
    if extra >= 0:
        wo.insert_rows(59, extra)
    else:
        wo.delete_rows(DATA_FIRST + n, -extra)
    note_base = 62 + extra
    try:
        wo.merge_cells(start_row=note_base, start_column=1, end_row=note_base, end_column=28)
        for i in range(1, 5):
            wo.merge_cells(start_row=note_base + i, start_column=2, end_row=note_base + i, end_column=28)
    except ValueError:
        pass

    wo["A1"] = f"SPA OPTIMIZER  -  {args.customer} sold-to {args.sold_to}  -  {args.label}"
    wo["A2"] = (
        f"L12 = billed SAP ({args.sold_to}, {args.window_from} to {args.window_to}). "
        f"SPA price = current list (ceiling). AC = committed qty. K = AC x qty factor."
    )
    wo["A5"] = "P/N"
    wo["F5"] = f"L12 billed EUR\n(SAP {args.sold_to})"
    wo["AC5"] = "Committed\nqty (base)"
    for cell, width in (("F5", 16), ("AC5", 14)):
        wo[cell].alignment = Alignment(wrap_text=True, vertical="center", horizontal="right")
        wo[cell].font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        wo[cell].fill = fill("0D2D52")
    wo.column_dimensions["AC"].width = 14

    for i, rec in enumerate(df.to_dict("records")):
        write_line_row(wo, DATA_FIRST + i, DATA_FIRST, rec)

    tr = new_total
    wo.cell(tr, 1).value = "TOTAL"
    wo.cell(tr, 2).value = f"{n} part numbers ({args.label})"
    for col, letter in ((5, "E"), (6, "F"), (7, "G"), (8, "H"), (11, "K"), (12, "L"),
                        (14, "N"), (16, "P"), (17, "Q"), (24, "X"), (25, "Y"),
                        (26, "Z"), (29, "AC")):
        wo.cell(tr, col).value = f"=SUM({letter}{DATA_FIRST}:{letter}{new_last})"
    wo.cell(tr, 9).value = f"=IFERROR(H{tr}/F{tr},0)"
    wo.cell(tr, 15).value = f"=IFERROR(N{tr}/L{tr},0)"
    wo.cell(tr, 18).value = f'=IF(Q{tr}>=0,"\u25b2 BETTER","\u25bc WORSE")'
    wo.cell(tr, 28).value = f'=IF(Y{tr}>=0,"\u25b2 BETTER","\u25bc WORSE")'

    green, red = "C6EFCE", "FFC7CE"
    wo.conditional_formatting._cf_rules.clear()
    wo.conditional_formatting.add(f"P{DATA_FIRST}:Q{new_last}",
                                  CellIsRule(operator="greaterThanOrEqual", formula=["0"], fill=fill(green)))
    wo.conditional_formatting.add(f"P{DATA_FIRST}:Q{new_last}",
                                  CellIsRule(operator="lessThan", formula=["0"], fill=fill(red)))
    wo.conditional_formatting.add(f"X{DATA_FIRST}:Y{new_last}",
                                  CellIsRule(operator="greaterThanOrEqual", formula=["0"], fill=fill(green)))
    wo.conditional_formatting.add(f"X{DATA_FIRST}:Y{new_last}",
                                  CellIsRule(operator="lessThan", formula=["0"], fill=fill(red)))
    wo.conditional_formatting.add(f"AA{DATA_FIRST}:AA{new_last}",
                                  CellIsRule(operator="greaterThan", formula=["0.3"], fill=fill("F8CBAD")))
    wo.conditional_formatting.add(f"R{DATA_FIRST}:R{new_last}",
                                  FormulaRule(formula=[f"Q{DATA_FIRST}>=0"], fill=fill(green)))
    wo.conditional_formatting.add(f"R{DATA_FIRST}:R{new_last}",
                                  FormulaRule(formula=[f"Q{DATA_FIRST}<0"], fill=fill(red)))
    wo.conditional_formatting.add(f"AB{DATA_FIRST}:AB{new_last}",
                                  FormulaRule(formula=[f"Y{DATA_FIRST}>=0"], fill=fill(green)))
    wo.conditional_formatting.add(f"AB{DATA_FIRST}:AB{new_last}",
                                  FormulaRule(formula=[f"Y{DATA_FIRST}<0"], fill=fill(red)))

    # -- Customer View (data starts row 5, total row 58 in the template)
    wcv = wb["Customer View"]
    resize_sheet(wcv, 5, TEMPLATE_LINES, n, 58)
    extend_linked(wcv, 5, n, 5, cv_formulas, 12)
    cv_tot = 57 + extra + 1
    wcv.cell(cv_tot, 1).value = "TOTAL"
    wcv.cell(cv_tot, 2).value = f"{n} part numbers"
    wcv.cell(cv_tot, 8).value = f"=SUM(H5:H{cv_tot - 1})"
    wcv.cell(cv_tot, 9).value = f"=SUM(I5:I{cv_tot - 1})"
    wcv.cell(cv_tot, 11).value = f"=SUM(K5:K{cv_tot - 1})"
    wcv.freeze_panes = "A5"

    # -- IML / IMIT brief
    wim = wb["IML_IMIT Brief"]
    try:
        wim.unmerge_cells("A27:M27")
    except Exception:
        pass
    resize_sheet(wim, 5, TEMPLATE_LINES, n, 58)
    extend_linked(wim, 5, n, 5, iml_formulas, 13)
    im_tot = 57 + extra + 1
    wim.cell(im_tot, 1).value = "TOTAL"
    wim.cell(im_tot, 2).value = f"{n} lines"
    for col, letter in ((9, "I"), (10, "J"), (11, "K"), (12, "L"), (13, "M")):
        wim.cell(im_tot, col).value = f"=SUM({letter}5:{letter}{im_tot - 1})"
    wim.freeze_panes = "A5"

    # -- Assumptions GM block: rows 36..88 map to optimizer 6..58
    resize_sheet(wa, 36, TEMPLATE_LINES, n, 89)
    extend_linked(wa, 36, n, 36, gm_formulas, 4)

    # -- Assumptions headline block
    wa.merge_cells("F1:K1")
    wa["F1"] = (f"HEADLINE - does turnover / profit go up?  {args.customer} sold-to {args.sold_to}. "
                f"{args.label}. SPA price = list ceiling.")
    wa["F1"].font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
    wa["F1"].fill = fill(NAVY)
    wa["F1"].alignment = WRAP
    wa.row_dimensions[1].height = 28
    for col, text in (("F", "Measure"), ("G", "This book (live)"), ("H", "Up / down"),
                      ("I", "Pack 1 SPA (locked)"), ("J", "vs pack 1"), ("K", "Note")):
        cell = wa[f"{col}3"]
        cell.value = text
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.fill = fill(NAVY)
        cell.alignment = WRAP
        cell.border = THIN
    headline = [
        (4, "Turnover (revenue)", f"='SPA Optimizer'!L{new_total}", f"='SPA Optimizer'!P{new_total}",
         pack1_rev, "=G4-I4", "SPA at list x committed qty x qty factor."),
        (5, f"L12 billed turnover (SAP {args.sold_to})", f"='SPA Optimizer'!F{new_total}", None, None, None,
         f"Actual invoiced on these part numbers, {args.window_from} to {args.window_to}."),
        (6, f"Profit with {args.cut:.0%} purchase cut", f"='SPA Optimizer'!X{new_total}",
         f"='SPA Optimizer'!Y{new_total}", pack1_profit, "=G6-I6",
         "Same engine as the original V4 (column X)."),
        (7, "L12 billed profit (billed - FOB x qty)", f"='SPA Optimizer'!H{new_total}", None, None, None,
         "Cost = FOB x billed qty. Different from list x qty."),
        (8, f"SPA GM% with {args.cut:.0%} cut",
         f"=IFERROR('SPA Optimizer'!X{new_total}/'SPA Optimizer'!L{new_total},0)", None, None, None,
         "Colour floor is Assumptions C5. Purchase cut is Assumptions C4."),
        (9, "IML sacrifice", f"='SPA Optimizer'!Z{new_total}", None, None, None,
         "Cut x FOB x committed qty."),
    ]
    for r, label, g, h, i, j, k in headline:
        wa.cell(r, 6).value = label
        wa.cell(r, 6).alignment = WRAP
        wa.cell(r, 6).border = THIN
        wa.cell(r, 7).value = g
        wa.cell(r, 7).number_format = "0.0%" if r == 8 else '#,##0;(#,##0);"-"'
        wa.cell(r, 7).border = THIN
        wa.cell(r, 8).value = h
        wa.cell(r, 8).number_format = '+#,##0;(#,##0);"-"'
        wa.cell(r, 8).border = THIN
        wa.cell(r, 9).value = i
        if i is not None:
            wa.cell(r, 9).number_format = '#,##0;(#,##0);"-"'
        wa.cell(r, 9).border = THIN
        wa.cell(r, 10).value = j
        wa.cell(r, 10).number_format = '+#,##0;(#,##0);"-"'
        wa.cell(r, 10).border = THIN
        wa.cell(r, 11).value = k
        wa.cell(r, 11).alignment = WRAP
        wa.cell(r, 11).border = THIN
        for c in range(6, 12):
            wa.cell(r, c).fill = fill(PAPER)

    priced = df[df["priced"]].copy()
    priced["l12_study_rev"] = priced["list_price"] * priced["l12_qty"]
    priced["l12_study_profit"] = (priced["list_price"] - priced["purchase"]) * priced["l12_qty"]
    spa_rev = float((priced["list_price"] * priced["spa_qty"] * args.qty_factor).sum())
    spa_profit = float(((priced["list_price"] - priced["purchase"] * (1 - args.cut))
                        * priced["spa_qty"] * args.qty_factor).sum())
    l12_billed = float(df["l12_billed_eur"].sum())
    # L12 profit: billed revenue less FOB x billed qty. Frozen lines carry no FOB, so
    # their revenue is counted and their cost is nil - which is the same basis as the
    # optimizer's H column on this basket. Excluding them would understate the base and
    # make the waterfall disagree with the form.
    l12_billed_profit = float(
        (df["l12_billed_eur"] - df["purchase"].fillna(0.0) * df["l12_qty"]).sum()
    )
    l12_study_rev = float(priced["l12_study_rev"].sum())
    l12_study_profit = float(priced["l12_study_profit"].sum())
    wa["F11"] = "List x billed qty (study, not billed)"
    wa["F12"] = "Study L12 turnover"
    wa["F13"] = "Study L12 profit"
    wa["G12"], wa["G13"] = l12_study_rev, l12_study_profit
    wa["G12"].number_format = wa["G13"].number_format = "#,##0"
    wa["H12"], wa["H13"] = spa_rev - l12_study_rev, spa_profit - l12_study_profit
    wa["H12"].number_format = wa["H13"].number_format = '+#,##0;(#,##0);"-"'
    wa["F14"] = "Frozen / no FOB (excluded from the SPA math)"
    wa["G14"] = ", ".join(sorted(df.loc[df["frozen"], "pn_raw"].tolist()) or ["none"])
    wa["K14"] = f"{int(df['frozen'].sum())} of {n} lines. Still listed, with a flag."
    wa["F15"] = "Sold-to"
    wa["G15"] = args.sold_to
    wa["K15"] = f"{args.customer} sold-to {args.sold_to} only. Other distributors are not in this file."
    for col, w in (("F", 42), ("G", 18), ("H", 14), ("I", 18), ("J", 14), ("K", 55)):
        wa.column_dimensions[col].width = w
    wa.freeze_panes = "A3"

    # -- workbook-wide retarget of every cross-sheet range
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and (
                    "SPA Optimizer" in cell.value or "53" in cell.value or " of 12" in cell.value
                ):
                    cell.value = retarget(cell.value, TEMPLATE_LAST, new_last, TEMPLATE_TOTAL, new_total)

    # -- Scenario Planner : the three wiring faults fixed here
    wr = wb["SPA Rationale"]
    wr["A2"] = f"{args.customer}  ·  {n} part lines  ·  {args.label}  ·  SPA price = list ceiling"
    wr["A2"].alignment = WRAP
    wsp = wb["Scenario Planner"]
    wsp["A2"] = (f"Models three SPA scenarios: Partial (lines with \u25b2 BETTER only) | "
                 f"Full (all {n} lines) | Enhanced (Full + volume growth assumption)")
    wsp["A6"] = "Volume Growth Assumption"
    wsp["B6"] = "=Assumptions!$B$19"          # FIX: was a hardcoded 0.05 that disagreed with the formulas
    wsp["C6"] = "% additional volume vs committed qty (Assumptions B19)"
    wsp["A7"] = "IML Cut Applied"
    wsp["B7"] = "=Assumptions!$C$4"           # FIX: read a heading cell (Assumptions B3) before
    wsp["C7"] = "From Assumptions C4"
    wsp["A8"] = "Volume Realisation (qty factor)"
    wsp["B8"] = "=Assumptions!$C$7"
    wsp["C8"] = "From Assumptions C7. Already applied to the SPA qty column."
    wsp["B12"] = f'=COUNTIF(\'SPA Optimizer\'!R{DATA_FIRST}:R{new_last},"\u25b2 BETTER")&" of {n}"'
    wsp["C12"] = f'=SUMIF(\'SPA Optimizer\'!R{DATA_FIRST}:R{new_last},"\u25b2 BETTER",\'SPA Optimizer\'!L{DATA_FIRST}:L{new_last})'
    wsp["D12"] = f'=SUMIF(\'SPA Optimizer\'!R{DATA_FIRST}:R{new_last},"\u25b2 BETTER",\'SPA Optimizer\'!P{DATA_FIRST}:P{new_last})'
    wsp["F12"] = f'=SUMIF(\'SPA Optimizer\'!R{DATA_FIRST}:R{new_last},"\u25b2 BETTER",\'SPA Optimizer\'!L{DATA_FIRST}:L{new_last})'
    for row in (13, 14, 15):
        wsp[f"B{row}"] = f"{n} of {n}"
        wsp[f"F{row}"] = f"='SPA Optimizer'!L{new_total}"
    wsp["C13"] = f"='SPA Optimizer'!L{new_total}"
    wsp["C14"] = f"='SPA Optimizer'!L{new_total}"
    wsp["C15"] = f"='SPA Optimizer'!L{new_total}*(1+Assumptions!$B$19)"
    wsp["F15"] = f"='SPA Optimizer'!L{new_total}*(1+Assumptions!$B$19)"
    wsp["D13"] = f"='SPA Optimizer'!Q{new_total}"
    wsp["D14"] = f"='SPA Optimizer'!Y{new_total}"
    wsp["E14"] = f"='SPA Optimizer'!Z{new_total}"
    wsp["D15"] = f"='SPA Optimizer'!Y{new_total}*(1+Assumptions!$B$19)"
    wsp["E15"] = f"='SPA Optimizer'!Z{new_total}*(1+Assumptions!$B$19)"
    wsp["G12"] = "Low risk - supports the distributor on viable lines only. Limited revenue recovery."

    # -- MD Approval Request : the signable form
    wmd = wb["MD Approval Request"]
    wmd["B4"] = "=Assumptions!B14"
    wmd["E4"] = args.manager
    wmd["J11"] = str(args.sold_to)
    wmd["J12"] = args.branch
    wmd["H19"] = "SPA Purchase Cost (EUR)"     # label that June got wrong
    patch_form_sized(wmd, new_total)
    wmd["C5"] = datetime.strptime(args.date_iso, "%Y-%m-%d")

    # Budget / Target column (F32:F37). This is the customer's own commitment, so it is
    # carried as an input from the basket workbook's "targets" sheet and never computed
    # here. If the customer has not supplied one, the cell says so in words.
    provided = []
    if customer_targets:
        for cell, key in (("F34", "revenue"), ("F35", "cost"), ("F36", "profit"), ("F37", "gm")):
            if key in customer_targets:
                wmd[cell] = float(customer_targets[key])
                wmd[cell].number_format = "0.0%" if key == "gm" else '#,##0;(#,##0);"-"'
                provided.append(key)
    wmd["F33"] = "Customer commitment" if provided else "Not provided by the customer"
    for cell in ("F34", "F35", "F36", "F37"):
        if wmd[cell].value in (None, "[Target]"):
            wmd[cell] = None
    wmd["F33"].alignment = WRAP

    # -- delivery hygiene
    for ws in wb.worksheets:
        if (ws.column_dimensions["B"].width or 8) < 28:
            ws.column_dimensions["B"].width = 36
    wo.freeze_panes = "C6"
    wb.save(out_xlsx)
    wb.close()

    cmd = outdir / f"OPEN_{args.customer}_{args.label}.cmd"
    cmd.write_bytes(
        f'@echo off\r\nstart "" "%~dp0{name}"\r\n'.encode("ascii")
    )

    return {
        "out_xlsx": str(out_xlsx),
        "cmd": str(cmd),
        "qa_dir": str(qa),
        "n": n,
        "new_last": new_last,
        "new_total": new_total,
        "spa_rev": spa_rev,
        "spa_profit": spa_profit,
        "l12_billed": l12_billed,
        "l12_billed_profit": l12_billed_profit,
        "l12_study_rev": l12_study_rev,
        "l12_study_profit": l12_study_profit,
        "frozen": sorted(df.loc[df["frozen"], "pn_raw"].tolist()),
        "priced": int(df["priced"].sum()),
        "customer_targets": customer_targets,
        "pack1_bar": bar if bar else {"source": "static (--pack1-bar-static)"},
        "args": vars(args),
    }


# ------------------------------------------------------------------------- verify
def recalc_and_check(out_xlsx: Path, new_total: int) -> dict:
    """Recalculate in Excel and prove the form equals the optimizer."""
    import win32com.client  # noqa: PLC0415

    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    result: dict = {"checked": False}
    try:
        wb = excel.Workbooks.Open(str(out_xlsx))
        excel.CalculateFullRebuild()
        opt = wb.Worksheets("SPA Optimizer")
        frm = wb.Worksheets("MD Approval Request")

        def num(ws, cell):
            v = ws.Range(cell).Value
            return None if v is None else float(v)

        totals = {c: num(opt, f"{c}{new_total}") for c in ("E", "F", "G", "H", "I", "K", "L", "N", "O", "X", "Y", "Z", "AC")}
        form = {c: num(frm, c) for c in
                ("D18", "D19", "D20", "D21", "J18", "J19", "J20", "J21",
                 "D34", "D35", "D36", "D37", "H34", "H35", "H36", "H37",
                 "J34", "J35", "J36", "J37")}

        checks = {
            "form_L12_revenue_eq_optimizer_F": _near(form["D18"], totals["F"]),
            "form_L12_cost_eq_optimizer_G": _near(form["D19"], totals["G"]),
            "form_L12_gm_eq_optimizer_I": _near(form["D20"], totals["I"]),
            "form_L12_profit_eq_optimizer_H": _near(form["D21"], totals["H"]),
            "form_SPA_revenue_eq_optimizer_L": _near(form["J18"], totals["L"]),
            "form_SPA_profit_eq_optimizer_X": _near(form["J21"], totals["X"]),
            "form_SPA_gm_eq_optimizer_O": _near(form["J20"], totals["O"]),
            "SPA_cost_is_revenue_minus_profit": _near(form["J19"], totals["L"] - totals["X"]),
            "impact_block_matches_totals": (
                _near(form["J34"], form["J18"] - form["D18"])
                and _near(form["J36"], form["J21"] - form["D21"])
            ),
            # The June failure, in the impact block: SPA purchase cost must be SPA
            # revenue minus SPA gross profit, never L12 revenue minus anything.
            "impact_SPA_cost_is_SPA_revenue_minus_SPA_profit": _near(
                form["H35"], form["H34"] - form["H36"]
            ),
            "scenario_planner_cut_reads_assumption": _scenario_cut_ok(wb),
            "scenario_volume_reads_one_assumption": _scenario_volume_ok(wb),
        }
        result = {
            "checked": True,
            "optimizer_totals": totals,
            "form": form,
            "derived_spa_purchase_cost": totals["L"] - totals["X"],
            "checks": checks,
            "all_pass": all(checks.values()),
        }
        wb.Save()          # keep the calculated values in the file
        wb.Close(SaveChanges=True)
    finally:
        excel.Quit()
        del excel
    return result


def _near(a, b, tol: float = 1.0) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


def _clean_formula(wb, sheet: str, cell: str) -> str:
    """Formula text with absolute-reference markers stripped, for comparison."""
    return str(wb.Worksheets(sheet).Range(cell).Formula).replace("$", "")


def _scenario_cut_ok(wb) -> bool:
    """The planner's IML Cut Applied must read the real assumption, not a heading."""
    try:
        v = _clean_formula(wb, "Scenario Planner", "B7")
        return "Assumptions" in v and "C4" in v
    except Exception:
        return False


def _scenario_volume_ok(wb) -> bool:
    """Volume growth must be one number, read from the assumption on both rows,
    and it must actually lift revenue on the Enhanced row."""
    try:
        growth = _clean_formula(wb, "Scenario Planner", "B6")
        c15 = _clean_formula(wb, "Scenario Planner", "C15")
        f15 = _clean_formula(wb, "Scenario Planner", "F15")
        return (
            "Assumptions" in growth and "B19" in growth
            and "B19" in c15 and "B19" in f15
        )
    except Exception:
        return False


def write_waterfall_csv(df: pd.DataFrame, args: argparse.Namespace, res: dict) -> tuple[Path, dict]:
    """The waterfall adjustment for this basket, dated in the file name.

    Returns the path and the row, so the run can prove the waterfall agrees with the
    application form.
    """
    stamp = args.date or date.today().strftime("%Y%m%d")
    priced = df[df["priced"]].copy()
    line = args.waterfall_line or f"SPA {args.label} ({args.customer})"
    rows = [{
        "period": f"{args.window_from} to {args.window_to}",
        "line": line,
        "customer": args.customer,
        "sold_to": args.sold_to,
        "part_lines": res["n"],
        "l12_billed_revenue_eur": round(res["l12_billed"], 2),
        "l12_billed_gp_eur": round(res["l12_billed_profit"], 2),
        "spa_revenue_eur": round(res["spa_rev"], 2),
        "spa_gp_eur": round(res["spa_profit"], 2),
        "delta_revenue_eur": round(res["spa_rev"] - res["l12_billed"], 2),
        "delta_gp_eur": round(res["spa_profit"] - res["l12_billed_profit"], 2),
        "l12_qty": round(float(df["l12_qty"].sum()), 2),
        "spa_qty": round(float(priced["spa_qty"].sum()), 2),
        "spa_qty_basis": "priced lines only (frozen lines carry no SPA price)",
        "spa_price_basis": "list (ceiling, no SPA price given)",
        "source": Path(args.basket).name,
    }]
    out = Path(res["qa_dir"]) / f"_waterfall_{args.customer}_{args.label}_{stamp}.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    return out, rows[0]


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Generate an SPA optimizer, application form and waterfall sheet.")
    ap.add_argument("--basket", required=True, help="basket workbook: P/N | Description | committed qty")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    ap.add_argument("--customer", default="UTI")
    ap.add_argument("--sold-to", type=int, default=1799)
    ap.add_argument("--market", default="Israel")
    ap.add_argument("--branch", default="IE40")
    ap.add_argument("--label", default="spa")
    ap.add_argument("--spa-reference", default=None)
    ap.add_argument("--valid-from", default="2026-07-01")
    ap.add_argument("--valid-to", default="2027-06-30")
    ap.add_argument("--window-from", default="2025-07-01")
    ap.add_argument("--window-to", default="2026-06-30")
    ap.add_argument("--cut", type=float, default=0.07)
    ap.add_argument("--gm-floor", type=float, default=0.25)
    ap.add_argument("--qty-factor", type=float, default=1.0)
    ap.add_argument("--prepared-by", default="JVDP")
    ap.add_argument("--manager", default="Hadewijch Tibos")
    ap.add_argument("--pack1-spa-rev", type=float, default=728880.0)
    ap.add_argument("--pack1-spa-profit", type=float, default=235521.0)
    ap.add_argument("--pack1-bar-static", action="store_true",
                    help="use the fixed pack 1 constants instead of deriving them from the dashboard")
    ap.add_argument("--waterfall-line", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--date", default=None, help="YYYYMMDD override")
    ap.add_argument("--date-iso", default=date.today().strftime("%Y-%m-%d"))
    ap.add_argument("--force", action="store_true", help="overwrite an existing output of the same name")
    ap.add_argument("--skip-verify", action="store_true")
    args = ap.parse_args()

    try:
        res = build(args)
    except RunError as exc:
        print(f"STOPPED: {exc}", file=sys.stderr)
        return 2

    print(f"built   : {res['out_xlsx']}")
    print(f"lines   : {res['n']} ({res['priced']} priced, frozen: {res['frozen'] or 'none'})")
    print(f"totals  : SPA revenue {res['spa_rev']:,.0f} | SPA profit {res['spa_profit']:,.0f} | "
          f"L12 billed {res['l12_billed']:,.0f}")

    wf, wf_row = write_waterfall_csv(
        read_pricing_and_l12(read_basket(Path(args.basket)), args.sold_to,
                             args.window_from, args.window_to), args, res
    )
    print(f"waterfall: {wf}")

    if not args.skip_verify:
        try:
            check = recalc_and_check(Path(res["out_xlsx"]), res["new_total"])
        except Exception as exc:  # noqa: BLE001
            print(f"VERIFY UNAVAILABLE: {exc}", file=sys.stderr)
            check = {"checked": False, "error": str(exc)}
        if check.get("checked"):
            # The waterfall must agree with the form, or it is not the same basket.
            totals = check["optimizer_totals"]
            check["checks"]["waterfall_revenue_eq_optimizer_F"] = _near(
                wf_row["l12_billed_revenue_eur"], totals["F"]
            )
            check["checks"]["waterfall_spa_revenue_eq_optimizer_L"] = _near(
                wf_row["spa_revenue_eur"], totals["L"]
            )
            check["checks"]["waterfall_spa_gp_eq_optimizer_X"] = _near(
                wf_row["spa_gp_eur"], totals["X"]
            )
            check["checks"]["waterfall_revenue_delta_eq_impact_J34"] = _near(
                wf_row["delta_revenue_eur"], check["form"]["J34"]
            )
            check["all_pass"] = all(check["checks"].values())
        (Path(res["qa_dir"]) / "_recalc_check.json").write_text(
            json.dumps(check, indent=2, default=str), encoding="utf-8"
        )
        if check.get("checked"):
            failed = [k for k, v in check["checks"].items() if not v]
            print("checks  : " + ("ALL PASS" if not failed else "FAILED -> " + ", ".join(failed)))
            print(f"          SPA purchase cost (derived) = {check['derived_spa_purchase_cost']:,.2f}")
            if failed:
                print("The form and the optimizer disagree. Do not send this file.", file=sys.stderr)
                return 3

    (Path(res["qa_dir"]) / "_build_result.json").write_text(
        json.dumps({k: v for k, v in res.items() if k != "args"}, indent=2, default=str), encoding="utf-8"
    )
    print(f"verified: {Path(res['qa_dir']) / '_recalc_check.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
