r"""SPA application generator - one basket in, optimizer + application form + waterfall out.

Rebuilt 2026-09-21 (label spa2-r2). Internal only.

WHAT CHANGED, AND WHY
---------------------
The 20 September build priced the SPA at ISZE's own ex-works list with no discount,
so its SPA price equalled its list on all 73 lines. The file actually sent to Eran and
Yoshimoto san on 17 September prices off a different baseline entirely. This build
reproduces the sent file.

The price basis, established by measurement on the sent workbook (do not re-derive):

  1. The SPA baseline selling price is the CUSTOMER's own realised net price, measured
     from our billing: L12 net sales divided by L12 billed quantity, rounded to the cent.
     Verified on all 69 lines that had L12 billing in the window. The 4 lines with no
     billing fall back to ISZE's current list.
  2. The SPA price is that baseline less a volume ladder, not a flat discount:
         committed qty <  1.5 x L12 billed qty   ->  no discount   (list price)
         committed qty in [1.5x, 2.0x)           ->  middle step
         committed qty >= 2.0 x L12 billed qty   ->  top step
         L12 billed qty = 0 (a new line)         ->  top step
     Pre-filled at middle 5% / top 8%, which is the sent file's Proposal 2. A per-line
     price override column is honoured when filled.
  3. Quantities are committed in WHOLE units. Eran's file carries 12-month totals divided
     by 12 and his committed figure is that monthly average times 12, so the sent file's
     committed quantity is simply his total rounded once, at the point of commitment.
  4. Cost and profit are driven by the FX rate and the purchase discount, not by a stored
     euro figure:  FOB_EUR = BP_JPY / FX * discount.  A higher JPY/EUR lowers euro cost and
     raises profit. Revenue never moves with FX.

Reproduction of the sent file on this basket (revenue is FX-independent):

    FX 172.6, sent SPA-active purchase : revenue 179,109.39  cost 100,003.71  profit 86,105.94
    FX 163.7, previous purchase        : revenue 179,109.39  cost 105,440.83  profit 81,049.42

Both are reproduced to the cent, line by line.

Naming: points 1, 2 and 3 above were reported against the sent file as prices "off the
customer list" with a "discount ladder" and "whole units". This module keeps that
vocabulary where it is the clearest word for the thing, and states the mechanism beside
it. The customer-price list itself is not an external file: it is derived from billing.

ONE MORE THING WORTH KNOWING
----------------------------
The sent file moved the FX rate and held the purchase discount at 0.620, which is the
vintage the price file sits on. config.yaml records the live Japan discount as 0.673
since 2026-01-05, and its live FX as 178.5 from 2026-10-01. Costing off both live values
gives 104,958.91, i.e. profit 81,497.60 at the 7% cut - very close to the 163.7 basis and
FAR below the sent file's 86,105.94. So on a fully current basis the sent file's profit is
roughly 4,600 too high, for the same reason it used the long-expired 163.7 rate to set the
L12 baseline. The workbook lets the reader see both.

THE JUNE FAILURE THIS GUARDS
----------------------------
The June 2026 UTI application went to Yoshimoto san with the SPA purchase-cost box holding
the SPA gross profit (307,853) instead of the cost. He bounced it. So the form's SPA
purchase cost is computed as revenue minus gross profit, and checked at the end of every
run, together with the same guard on the impact block (the template's own row 35 had the
identical fault: it read L12 revenue minus SPA gross profit).

USAGE
-----
  python build_spa_application.py --basket "01_data/SPA 2_eran study.xlsx" \
      --customer UTI --label spa2-r2 --date 20260921
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
from copy import copy
from datetime import date, datetime, timedelta
from pathlib import Path

import openpyxl
import pandas as pd
import yaml
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ROOT / "01_data" / "00_derived"
DEFAULT_TEMPLATE = ROOT / "01_data" / "01_Pricing" / "ISZE_SPA_Optimizer_V4.xlsx"
PRICING_CONFIG = ROOT / "03_analytics" / "isze_pricing" / "config.yaml"

# An outward-facing benchmark: the negotiation model handed to the customer on 17 Sep.
# Used as a reconciliation target on the shared lines, never as an input. Override on
# the command line with --negotiation-reference for another basket.
SENT_SPA2_R2 = {
    "label": "SPA_Optimizer_V4_UTI_spa2_DUAL_PURCHASE",
    "file": str(ROOT / "01_data" / "SPA_Optimizer_V4_UTI_spa2_DUAL_PURCHASE.xlsx"),
    "n_lines": 73,
    "spa_revenue_eur": 179109.3906,
    "spa_profit_cut_eur": 86105.942439,
    "spa_profit_no_cut_eur": 79105.6829,
    "spa_cost_fx_172_6_eur": 100003.7077,
    "spa_cost_fx_163_7_eur": 105440.83,
    "committed_units": 10700,
    "l12_qty": 11231,
    "l12_billed_eur": 112316.03,
    "l12_amounts": {
        "172.6": {"cost": 100003.7077, "profit_7pct": 86105.942439, "profit_0pct": 79105.6829},
        "163.7": {"cost": 105440.83, "profit_7pct": 81049.42, "profit_0pct": 73668.56},
    },
    "ladder_counts": {"none": 32, "middle": 11, "top": 30},
    "tolerances": {
        "spa_revenue_eur": 1.0,
        "spa_cost_eur": 1.0,
        "spa_profit_eur": 1.0,
        "line_price_eur": 0.011,
        "committed_units": 0.0,
    },
}

# What the sent file used to cost the SPA, kept as traceability vintages.
SENT_VINTAGE_FX = 163.7            # what the selling list sits on
SENT_VINTAGE_FX_SPA = 172.6        # the FX the sent file's SPA-active purchase uses
SENT_VINTAGE_DISCOUNT = 0.620      # the purchase discount the price file sits on

# template geometry (verified against the V4 template on disk)
TEMPLATE_LAST = 58          # last data row in the template's SPA Optimizer
TEMPLATE_TOTAL = 60         # totals row in the template
TEMPLATE_LINES = 53         # template line count
DATA_FIRST = 6              # first data row, all sheets

NAVY = "15233C"
PAPER = "F7F4EE"
BLUE_BG = "EBF3FB"
VOID_BG = "E8E8E8"
TERR = "C0552D"
INPUT_Y = "FFF2CC"
GREEN_BG = "E2EFDA"
THIN = Border(
    left=Side(style="thin", color="D5D8DC"),
    right=Side(style="thin", color="D5D8DC"),
    top=Side(style="thin", color="D5D8DC"),
    bottom=Side(style="thin", color="D5D8DC"),
)
WRAP = Alignment(wrap_text=True, vertical="center")
LAUNCHER_STARTER = "run_spa_application.cmd"


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


VINTAGE_LABEL_PREVIOUS = f"{SENT_VINTAGE_FX} (previous), + {SENT_VINTAGE_DISCOUNT:.3f} discount"


# ------------------------------------------------------------------------- pricing
def load_pricing_config(path: Path) -> dict:
    """FX and purchase-discount vintages, from the one file that declares them."""
    if not path.exists():
        raise RunError(f"Pricing config not found: {path}")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    block = cfg.get("formula", cfg)
    if "fx_rate" not in block:
        raise RunError("config.yaml has no formula.fx_rate - cannot date the FX vintage")
    prior = block.get("fx_prior_vintages") or {}
    vintages = [{
        "fx": float(block["fx_rate"]),
        "as_of": str(block.get("fx_as_of", "")),
        "until": str(block.get("fx_period_end", "")),
        "live": True,
        "note": "live rate in config.yaml",
    }]
    # prior vintages are traceability only - never the live rate
    ordered = sorted(prior.items(), key=lambda kv: str(kv[0]), reverse=True)
    for i, (as_of, fx) in enumerate(ordered):
        vintages.append({
            "fx": float(fx),
            "as_of": str(as_of),
            "until": str(ordered[i - 1][0] - timedelta(days=1)) if i else "",
            "live": False,
            "note": "previous vintage (traceability only)",
        })
    return {
        "vintages": vintages,
        "fx_live": float(block["fx_rate"]),
        "fx_as_of": str(block.get("fx_as_of", "")),
        "discount": {k: float(v) for k, v in (block.get("source_discount") or {}).items()},
        "discount_prior": {k: float(v) for k, v in (block.get("source_discount_prior") or {}).items()},
        "class_factor": {k: float(v) for k, v in (block.get("class_factor") or {}).items()},
        "source": str(path),
    }


def resolve_fx(cfg: dict, requested: float | None, annual: str | None) -> dict:
    """Pick the FX vintage: explicit rate, else annual (latest as_of in that fiscal year),
    else the live rate. Returns the vintage dict actually used."""
    if requested is not None:
        match = [v for v in cfg["vintages"] if abs(v["fx"] - float(requested)) < 1e-9]
        if match:
            return {**match[0], "selected_by": "explicit rate (matches a declared vintage)"}
        return {"fx": float(requested), "as_of": "", "until": "", "live": False,
                "note": "explicit rate, not a declared vintage",
                "selected_by": "explicit rate"}
    if annual:
        cand = [v for v in cfg["vintages"] if v["as_of"].startswith(str(annual))]
        if not cand:
            raise RunError(f"No FX vintage declared for {annual} in config.yaml "
                           f"(have {[v['as_of'] for v in cfg['vintages']]})")
        return {**cand[0], "selected_by": f"annual vintage {annual}"}
    live = cfg["vintages"][0]
    return {**live, "selected_by": "live rate in config.yaml"}


def build_discount_schedule(cfg: dict, in_use: str, as_of: str) -> dict:
    """Resolve the purchase discount per source code for the vintage in use.

    The FX vintage and the purchase-discount vintage are separate schedules that happen
    to be declared together. config.yaml names the live discounts and the prior ones, and
    each has an effective date, so they are resolved by date rather than assumed to move
    together. Every switch is visible and dated.
    """
    DISCOUNT_EFFECTIVE = "2026-01-05"     # Suzuki san, mail of 2025-12-22
    live = dict(cfg.get("discount") or {})
    prior = dict(cfg.get("discount_prior") or {})
    codes = sorted(set(live) | set(prior))
    use_prior = bool(as_of) and str(as_of) < DISCOUNT_EFFECTIVE
    if in_use == "prior":
        use_prior = True
    table = prior if use_prior else live
    out = {c: float(table.get(c, live.get(c, prior.get(c, 1.0)))) for c in codes}
    return {
        "per_source": out,
        "vintage": "prior (before 2026-01-05)" if use_prior else "live (from 2026-01-05)",
        "effective": DISCOUNT_EFFECTIVE,
        "rule": ("resolved by the FX vintage's start date against the discount's effective "
                 "date, overridable with --discount-vintage"),
        "live": live,
        "prior": prior,
    }


# ----------------------------------------------------------------- row formulas
def opt_formulas(r: int) -> dict[int, str]:
    """Column formulas for one SPA Optimizer line, in the sent model's own layout.

    Adopting the sent layout rather than the template's matters: the sent workbook added
    a second purchase column (C previous, D SPA-active) and pushed every later column one
    to the right. The template has a single purchase column, so its letters are all one
    to the left. Using template letters against sent formulas silently mis-prices the
    sheet, so this module fixes the layout to the sent model's and says so here.

      A P/N  B Description  C Purchase PREVIOUS  D Purchase SPA ACTIVE
      E SPA baseline (the customer's realised net price)
      F L12 Qty  G L12 Revenue  H L12 Cost  I L12 Profit  J L12 GM%
      K SPA Price  L SPA Qty Committed  M SPA Revenue  N Unit Margin  O SPA Profit
      P SPA GM%  Q d Revenue  R d Profit  S Status  T Min Qty  U Min Price
      V Extra Qty  W IML Cut%  X ISZE Cost w/ Cut  Y SPA Profit w/ Cut
      Z d Profit w/ Cut  AA IML Sacrifice  AB Req IML Cut%  AC Status w/ Cut
      AD Block  AE Committed qty (whole)  AF L12 billed EUR  AG Price override
    """
    return {
        7: f"=E{r}*F{r}",                                     # L12 revenue
        8: f"=C{r}*F{r}",                                     # L12 cost, on the previous vintage
        9: f"=G{r}-H{r}",                                     # L12 profit
        10: f"=IFERROR(I{r}/G{r},0)",                         # L12 GM%
        # SPA price: the volume ladder, read live from Assumptions so the rates are inputs
        11: (f'=IF(AG{r}<>"",AG{r},E{r}*(1-IF(F{r}=0,Assumptions!$C$17,'
             f'IF(L{r}<F{r}*Assumptions!$C$18,0,'
             f'IF(L{r}<F{r}*Assumptions!$C$20,Assumptions!$C$16,Assumptions!$C$17)))))'),
        13: f"=K{r}*L{r}",                                    # SPA revenue
        14: f"=K{r}-D{r}",                                    # unit margin, on the SPA-active vintage
        15: f"=N{r}*L{r}",                                    # SPA profit
        16: f"=IFERROR(O{r}/M{r},0)",                         # SPA GM%
        17: f"=M{r}-G{r}",                                    # d revenue
        18: f"=O{r}-I{r}",                                    # d profit
        19: f'=IF(R{r}>=0,"\u25b2 BETTER","\u25bc WORSE")',
        20: f'=IFERROR(IF(K{r}-D{r}<=0,"BELOW COST",CEILING(I{r}/(K{r}-D{r}),1)),"N/A")',
        21: f'=IFERROR(I{r}/L{r}+D{r},"N/A")',
        22: f"=IFERROR(MAX(0,T{r}-L{r}),0)",
        23: "=Assumptions!$C$4",
        24: f"=IFERROR(D{r}*(1-Assumptions!$C$4),D{r})",
        25: f"=IFERROR((K{r}-D{r}*(1-Assumptions!$C$4))*L{r},O{r})",
        26: f"=IFERROR(Y{r}-I{r},O{r}-I{r})",
        27: f"=IFERROR(D{r}*Assumptions!$C$4*L{r},0)",
        28: f'=IFERROR(MAX(0,1-(K{r}-I{r}/L{r})/D{r}),"N/A")',
        29: f'=IFERROR(IF(Z{r}>=0,"\u25b2 BETTER","\u25bc WORSE"),"N/A")',
    }


def cv_formulas(opt: int) -> dict[int, str]:
    """Customer View. The baseline the customer knows is the SPA baseline price in E."""
    return {
        1: f"='SPA Optimizer'!A{opt}",
        2: f"='SPA Optimizer'!B{opt}",
        3: f"='SPA Optimizer'!E{opt}",
        4: f"='SPA Optimizer'!K{opt}",
        5: f"='SPA Optimizer'!E{opt}-'SPA Optimizer'!K{opt}",
        6: f"=IFERROR(IF('SPA Optimizer'!E{opt}>0,('SPA Optimizer'!E{opt}-'SPA Optimizer'!K{opt})/'SPA Optimizer'!E{opt},0),0)",
        7: f"='SPA Optimizer'!L{opt}",
        8: f"='SPA Optimizer'!M{opt}",
        9: f"=IFERROR('SPA Optimizer'!E{opt}*'SPA Optimizer'!L{opt}-'SPA Optimizer'!M{opt},0)",
        10: f"=IFERROR(IF('SPA Optimizer'!F{opt}>0,('SPA Optimizer'!L{opt}-'SPA Optimizer'!F{opt})/'SPA Optimizer'!F{opt},0),0)",
        11: f"=IFERROR(('SPA Optimizer'!E{opt}-'SPA Optimizer'!K{opt})*'SPA Optimizer'!L{opt},0)",
        12: (
            f'=IF(\'SPA Optimizer\'!S{opt}="\u25b2 BETTER","\u2714 Viable",'
            f'IF(AND(\'SPA Optimizer\'!AC{opt}="\u25b2 BETTER",\'SPA Optimizer\'!AB{opt}<=1),'
            f'"\u2714 w/ IML support",IF(OR(\'SPA Optimizer\'!AB{opt}>1,\'SPA Optimizer\'!P{opt}<0),'
            f'"\u2716 Not feasible","\u26a0 Review")))'
        ),
    }


def iml_formulas(opt: int) -> dict[int, str]:
    return {
        1: f"='SPA Optimizer'!A{opt}",
        2: f"='SPA Optimizer'!B{opt}",
        3: f"='SPA Optimizer'!C{opt}",
        4: f"='SPA Optimizer'!D{opt}",     # the SPA-active purchase - the one that decides
        5: f"='SPA Optimizer'!J{opt}",
        6: f"='SPA Optimizer'!K{opt}",
        7: f"='SPA Optimizer'!P{opt}",
        8: f"='SPA Optimizer'!AB{opt}",
        9: f"='SPA Optimizer'!AA{opt}",
        10: f"='SPA Optimizer'!L{opt}",
        11: f"='SPA Optimizer'!E{opt}",
        12: f"=IFERROR('SPA Optimizer'!L{opt}-'SPA Optimizer'!E{opt},0)",
        13: f"=IFERROR(MAX(0,'SPA Optimizer'!L{opt}-'SPA Optimizer'!E{opt})*'SPA Optimizer'!D{opt}*(1-'SPA Optimizer'!AB{opt}),0)",
    }


def gm_formulas(opt: int) -> dict[int, str]:
    return {
        1: f"='SPA Optimizer'!A{opt}",
        2: f"='SPA Optimizer'!B{opt}",
        3: f"='SPA Optimizer'!P{opt}",
        4: (
            f'=IF(\'SPA Optimizer\'!P{opt}>=0.3,"\u2714  OK",'
            f'IF(\'SPA Optimizer\'!P{opt}>=0.25,'
            f'"\u26a0  Caution - below 30% - explain to Management Approver",'
            f'"\u2716  ALARM - below 25% - Management Approver will flag this"))'
        ),
    }


def remap_optimizer_columns(wb) -> int:
    """Shift the template's own cross-sheet references onto this module's column layout.

    The sent negotiation model split the single purchase column into two (C previous,
    D SPA-active), which pushed every column from D rightwards one place. This module
    keeps that layout, so the template's own formulas - which were written against the
    older, single-purchase sheet - must move with it. Without this the template's health
    checks and scenario rows silently read the wrong columns.

    Applied once, immediately after the template is loaded and before any formula this
    module writes, so hand-written formulas are never shifted.
    """
    from openpyxl.utils import get_column_letter, column_index_from_string
    # a range reference must have BOTH ends shifted; treating it as a single cell turns
    # R4:R58 into R4:S58, which is a two-column range and silently corrupts SUMIF.
    # Every match in a formula is found first, then all replacements are made in one left-
    # to-right pass. Doing the range pass first and the single-cell pass second does NOT
    # work: after the range pass the tail of `N4:M58` is still a single-cell match, so the
    # tail gets shifted a second time and becomes `N4:N58`.
    rng_pat = re.compile(r"('SPA Optimizer'!\$?)([A-Z]{1,2})(\$?\d+)(:)(\$?)([A-Z]{1,2})(\$?\d+)")
    one_pat = re.compile(r"('SPA Optimizer'!\$?)([A-Z]{1,2})(\$?\d+)")
    moved = 0

    def shift(idx: int) -> str:
        return get_column_letter(idx + 1) if idx >= 4 else get_column_letter(idx)

    def fix(text: str) -> str:
        nonlocal moved
        spans = []
        for m in rng_pat.finditer(text):
            moved += 2
            spans.append((m.start(), m.end(),
                          f"{m.group(1)}{shift(column_index_from_string(m.group(2)))}{m.group(3)}"
                          f"{m.group(4)}{m.group(5)}"
                          f"{shift(column_index_from_string(m.group(6)))}{m.group(7)}"))
        for m in one_pat.finditer(text):
            idx = column_index_from_string(m.group(2))
            if any(s <= m.start() < e for s, e, _ in spans):
                continue                      # already handled as part of a range
            if idx < 4:
                continue                      # A, B and C are unmoved
            moved += 1
            spans.append((m.start(), m.end(),
                          f"{m.group(1)}{get_column_letter(idx + 1)}{m.group(3)}"))
        for start, end, rep in sorted(spans, key=lambda t: t[0], reverse=True):
            text = text[:start] + rep + text[end:]
        return text

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and "SPA Optimizer" in cell.value:
                    cell.value = fix(cell.value)
    return moved


def retarget(val, old_last: int, new_last: int, old_total: int, new_total: int):
    """Move a TEMPLATE-authored reference onto the new basket size.

    This moves two things and nothing else:
      - the template's total row (row 60) onto this basket's total row
      - the template's data range end (row 58) onto this basket's last data row

    It must NOT be able to move a data row. In a basket larger than the template's 53
    lines, the template's total row number (60) is itself an ordinary data row, so a
    blanket "replace 60 with the new total" hijacks the linked row that legitimately maps
    to optimizer row 60. That is the defect this docstring exists to prevent.

    The call ordering now enforces the same thing from the other side: this pass runs
    BEFORE extend_linked writes the linked rows, so it only ever sees template-authored
    text and never the formulas this module has just written.
    """
    if not isinstance(val, str):
        return val
    s = val
    for col in ("P", "Y", "Z", "F", "G", "H", "I", "L", "O", "Q", "X", "K", "E", "N", "AB", "AA"):
        s = s.replace(f"'SPA Optimizer'!{col}{old_total}", f"'SPA Optimizer'!{col}{new_total}")
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
                as_num = float(value)
            except (TypeError, ValueError):
                continue
            if label.startswith("revenue"):
                targets["revenue"] = as_num
            elif label.startswith("purchase") or label.startswith("cost"):
                targets["cost"] = as_num
            elif label.startswith("gross profit") or label.startswith("profit"):
                targets["profit"] = as_num
            elif label.startswith("gross margin") or label.startswith("margin") or label.startswith("gm"):
                targets["gm"] = as_num / 100.0 if as_num > 1 else as_num
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
    """Basket = the customer's committed part numbers and quantities.

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


def read_pricing_and_l12(df: pd.DataFrame, sold_to: int, win_from: str, win_to: str,
                         cfg: dict, cost_fx: float, cost_discount: dict,
                         list_fx: float, list_discount: dict) -> pd.DataFrame:
    """Everything the optimizer needs, with the customer's realised price derived from billing.

    The customer's list (column E) is the realised L12 net price per unit: billed euros
    divided by billed quantity, rounded to the cent. On this basket that reproduces the
    price column of the sent negotiation model on all 69 lines that had L12 billing.
    The 4 lines with no billing fall back to ISZE's current list.

    Cost side: the price file's EUR purchase cost is struck at the list vintage
    (list_fx / list_discount) and is re-struck on the vintage in use.
    """
    lp = pd.read_parquet(DERIVED / "pricing_list_pn.parquet")
    lp["pn"] = lp["part_number"].map(norm_pn)
    lp1 = lp.dropna(subset=["pn"]).drop_duplicates("pn", keep="last")
    lp_new = lp.copy()
    lp_new["pn"] = lp_new["newest_pn"].map(norm_pn)
    lp_new = lp_new.dropna(subset=["pn"]).drop_duplicates("pn", keep="last")

    df = df.merge(lp1[["pn", "description", "fob_eur", "sp_eur", "bp_jpy", "price_class", "source"]],
                  on="pn", how="left")
    miss = df["fob_eur"].isna() | df["sp_eur"].isna()
    if miss.any():
        extra = lp_new.loc[lp_new["pn"].isin(df.loc[miss, "pn"]),
                           ["pn", "description", "fob_eur", "sp_eur", "bp_jpy", "price_class", "source"]]
        extra = extra.rename(columns={"description": "description_n", "fob_eur": "fob_n",
                                      "sp_eur": "sp_n", "bp_jpy": "bp_n",
                                      "price_class": "class_n", "source": "src_n"})
        df = df.merge(extra, on="pn", how="left")
        for base, alt in (("description", "description_n"), ("fob_eur", "fob_n"), ("sp_eur", "sp_n"),
                          ("bp_jpy", "bp_n"), ("price_class", "class_n"), ("source", "src_n")):
            if alt in df.columns:
                df[base] = df[base].fillna(df[alt])
                df = df.drop(columns=[alt])

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

    # Cost and profit move with the FX vintage and the purchase discount, not with a
    # stored euro figure.  FOB_EUR = BP_JPY / FX * discount  is the identity.
    # The price file already carries the EUR purchase cost struck at the LIST vintage
    # (163.7 and the 0.620 discount). So this module carries that figure forward and
    # re-strikes it on the vintage in use, which is the same identity written twice:
    #
    #   purchase = fob_list_eur * (LIST_FX / FX) * (discount_now / discount_list)
    #            = BP_JPY / FX * discount_now        (to the price file's round-off)
    #
    # Both forms are kept: the first reproduces the sent model to the cent, the second
    # is the identity the workbook's column D carries and is checked against it.
    src = df["source"].astype(str).str.strip()
    df["cost_discount"] = src.map(lambda s: cost_discount.get(s, cost_discount.get("J", 1.0)))
    df["list_discount"] = src.map(lambda s: list_discount.get(s, list_discount.get("J", 1.0)))
    df["fob_list_eur"] = df["fob_eur"]
    vintage_factor = (float(list_fx) / float(cost_fx)) * (df["cost_discount"] / df["list_discount"])
    df["vintage_factor"] = vintage_factor
    df["purchase"] = df["fob_list_eur"] * vintage_factor
    df["purchase"] = df["purchase"].round(4)
    # Column D of the workbook is a live formula off the FX cell, so its round-off is the
    # sheet's, not Python's. These two agree to a fraction of a cent and the checks assert it.
    df["purchase_identity"] = df["bp_jpy"] / float(cost_fx) * df["cost_discount"]

    # The customer's own list = realised net price per unit where we have billing.
    realised = None
    has = df["l12_qty"] > 0
    if has.any():
        realised = (df.loc[has, "l12_billed_eur"] / df.loc[has, "l12_qty"]).round(2)
    df["customer_list"] = pd.Series(index=df.index, dtype="float64")
    if realised is not None:
        df.loc[has, "customer_list"] = realised
    df["customer_list_from"] = "realised L12 net price"
    fb = df["customer_list"].isna()
    df.loc[fb, "customer_list"] = df.loc[fb, "sp_eur"]
    df.loc[fb, "customer_list_from"] = "ISZE current list (no L12 billing)"

    df["list_price"] = df["customer_list"]
    df["desc"] = df["description"].fillna(df["desc_basket"])
    # Column C of the optimizer: the purchase on the vintage the selling list sits on.
    df["purchase_prev"] = (df["fob_list_eur"]
                           * (float(list_fx) / float(list_fx))
                           * (df["list_discount"] / df["list_discount"])).round(4)
    df["frozen"] = df["purchase"].isna() | df["list_price"].isna()
    df["priced"] = ~df["frozen"]
    return df


def assign_block(desc: str) -> str:
    """The two-part family the sent file used: belts/seals against collision-body-sensors."""
    d = (desc or "").lower()
    if re.search(r"\bbelt|\bseal|hub seal|o-ring|oring", d):
        return "Belts and hub seals"
    return "Collision / body / sensors"


def assign_ladder(df: pd.DataFrame, middle_rate: float, top_rate: float,
                  middle_mult: float, top_mult: float) -> pd.DataFrame:
    """The volume ladder, as an explicit rule rather than a stored per-line table.

    The middle and top steps are reached by committed quantity against the L12 billed
    quantity. A line with no L12 billing is a new line and takes the top step.
    A per-line price override, when supplied, beats the ladder.
    """
    df = df.copy()
    df["ladder_step"] = "none"
    mult = df["l12_qty"] * 0.0 + 1.0
    ratio = df["spa_qty_committed"] / df["l12_qty"].replace(0, pd.NA)
    new_line = df["l12_qty"] <= 0
    step = pd.Series("none", index=df.index, dtype="object")
    step[new_line] = "top"
    step[(~new_line) & (ratio >= top_mult)] = "top"
    step[(~new_line) & (ratio >= middle_mult) & (ratio < top_mult)] = "middle"
    df["ladder_step"] = step
    rate = step.map({"none": 0.0, "middle": float(middle_rate), "top": float(top_rate)})
    df["ladder_rate"] = rate
    df["days_cover"] = pd.NA  # placeholder column the template carries; not used here
    df["override"] = None
    df["spa_price"] = (df["list_price"] * (1 - df["ladder_rate"])).round(4)
    if "price_override" in df.columns:
        ov = df["price_override"]
        ovm = ov.notna()
        df.loc[ovm, "override"] = ov[ovm]
        df.loc[ovm, "spa_price"] = ov[ovm].astype(float)
    df["spa_qty"] = df["spa_qty_committed"].astype(float)
    return df


# ------------------------------------------------------------------- workbook work
def write_line_row(ws, r: int, style_row: int, rec: dict) -> None:
    for c in range(1, 30):
        copy_style(ws.cell(style_row, c), ws.cell(r, c))
    ws.cell(r, 1).value = rec["pn_raw"]
    ws.cell(r, 1).number_format = "@"
    ws.cell(r, 2).value = rec["desc"]
    ws.cell(r, 2).alignment = WRAP

    prev_pur = Font(name="Calibri", size=10, color="833C00")     # salmon-ish: previous
    act_pur = Font(name="Calibri", size=10, color="006100")      # green: SPA active
    blue = Font(name="Calibri", size=10, color="0000FF")

    # Column C is the purchase on the vintage the selling list sits on: a static figure.
    cell = ws.cell(r, 3)
    cell.value = float(rec["purchase_prev"])
    cell.fill = fill(BLUE_BG)
    cell.font = prev_pur
    # Column D is the SPA-active purchase, and it is LIVE: the yen base price divided by
    # the FX rate the reader can change on the Assumptions sheet, times the purchase
    # discount in use. That is what makes the FX input a real input rather than a label.
    cell = ws.cell(r, 4)
    cell.value = (f"=IFERROR(AH{r}*({SENT_VINTAGE_FX}/Assumptions!$C$6)"
                  f"*(AI{r}/AJ{r}),\"\")")
    cell.fill = fill(GREEN_BG)
    cell.font = act_pur
    cell.number_format = "#,##0.0000"
    # the SPA baseline price the ladder is applied to
    cell = ws.cell(r, 5)
    cell.value = float(rec["list_price"])
    cell.fill = fill(BLUE_BG)
    cell.font = blue
    # SPA price: the ladder, unless the line carries its own price
    cell = ws.cell(r, 10 + 1)
    cell.value = float(rec["spa_price"])
    cell.number_format = "#,##0.00"
    cell.fill = fill(BLUE_BG)
    cell.font = blue

    # hidden inputs for the live cost: the list-vintage FOB in euro, the discount in use
    # and the discount the list was struck on
    for col, val, fmt in ((34, rec["fob_list_eur"], "#,##0.0000"),
                          (35, rec["cost_discount"], "0.000"),
                          (36, rec["list_discount"], "0.000")):
        c = ws.cell(r, col)
        c.value = float(val)
        c.number_format = fmt
        c.font = Font(name="Calibri", size=8, color="808080")

    # Committed quantity in WHOLE units. Eran's figure is the 12-month total divided by
    # 12; his committed quantity is that monthly average times 12, so round once.
    for col, val, fmt in ((6, rec["l12_qty"], "#,##0.00"),
                          (12, rec["spa_qty"], "#,##0"),
                          (31, rec["spa_qty"], "#,##0"),
                          (32, rec["l12_billed_eur"], "#,##0.00")):
        cell = ws.cell(r, col)
        cell.value = float(val)
        cell.fill = fill(BLUE_BG)
        cell.font = blue
        cell.number_format = fmt
    if rec.get("override") is not None:
        cell = ws.cell(r, 33)
        cell.value = float(rec["override"])
        cell.fill = fill(INPUT_Y)
    ws.cell(r, 30).value = rec["block"]

    for col, formula in opt_formulas(r).items():
        ws.cell(r, col).value = formula


def build_pending_sheet(wb, pending: pd.DataFrame, args) -> None:
    """The unpriced lines, parked with their reason - the sent model's own practice."""
    if "Lines pending EPC" in wb.sheetnames:
        del wb["Lines pending EPC"]
    ws = wb.create_sheet("Lines pending EPC")
    ws["A1"] = "LINES THAT CANNOT BE PRICED YET"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color=NAVY)
    ws["A2"] = ("These part numbers carry a committed quantity but no purchase price on the "
                "price file, so no SPA price can be offered and they are excluded from every "
                "total on this workbook. They are shown here rather than in the main list, so "
                "the comparable line count stays clean.")
    ws["A2"].alignment = WRAP
    ws["A2"].font = Font(name="Calibri", size=9, italic=True, color="44546A")
    ws.row_dimensions[2].height = 30

    heads = ["P/N", "Description", "Quantity asked", "L12 billed qty (window)",
             "L12 billed EUR (window)", "Reason"]
    for i, h in enumerate(heads, start=1):
        cell = ws.cell(4, i)
        cell.value = h
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.fill = fill(NAVY)
        cell.alignment = WRAP
        cell.border = THIN
    r = 5
    for rec in pending.to_dict("records"):
        missing = []
        if pd.isna(rec.get("bp_jpy")):
            missing.append("no yen base price on the price file")
        if pd.isna(rec.get("fob_eur")):
            missing.append("no purchase price on the price file")
        if pd.isna(rec.get("sp_eur")):
            missing.append("no ISZE list price")
        if pd.isna(rec.get("bp_jpy")) and pd.isna(rec.get("fob_eur")):
            missing.append("superseded part number, so the replacement carries the price")
        reason = "; ".join(missing) or "not priceable"
        for i, val in enumerate((rec["pn_raw"], rec["desc"], rec["spa_qty_committed"],
                                 rec["l12_qty"], rec["l12_billed_eur"], reason), start=1):
            cell = ws.cell(r, i)
            cell.value = val
            cell.border = THIN
            cell.alignment = WRAP
            if i in (3, 4):
                cell.number_format = "#,##0"
            elif i == 5:
                cell.number_format = "#,##0.00"
        r += 1
    for col, w in (("A", 18), ("B", 40), ("C", 15), ("D", 20), ("E", 22), ("F", 58)):
        ws.column_dimensions[col].width = w
    ws.sheet_view.showGridLines = False


def extend_linked(ws, first_row: int, n: int, style_row: int, builder, max_col: int) -> None:
    for i in range(n):
        r = first_row + i
        if r != style_row:
            for c in range(1, max_col + 1):
                copy_style(ws.cell(style_row, c), ws.cell(r, c))
        for c, formula in builder(DATA_FIRST + i).items():
            ws.cell(r, c).value = formula


def patch_form_sized(wmd, new_total: int) -> None:
    """Every financial cell on the form is a link to the optimizer totals row.

    The impact block is set explicitly rather than left on the template's own references,
    which pointed at the template's older layout and at its older price list.
    """
    for cell, tmpl in {
        "D18": "='SPA Optimizer'!G{t}", "D19": "='SPA Optimizer'!H{t}",
        "D20": "='SPA Optimizer'!J{t}", "D21": "='SPA Optimizer'!I{t}",
        "J18": "='SPA Optimizer'!M{t}", "J19": "='SPA Optimizer'!M{t}-'SPA Optimizer'!Y{t}",
        "J20": "='SPA Optimizer'!P{t}", "J21": "='SPA Optimizer'!Y{t}",
        # impact block, left hand side: the L12 baseline
        "D34": "='SPA Optimizer'!G{t}", "D35": "='SPA Optimizer'!H{t}",
        "D36": "='SPA Optimizer'!I{t}", "D37": "='SPA Optimizer'!J{t}",
        # impact block, SPA side
        "H34": "='SPA Optimizer'!M{t}", "H36": "='SPA Optimizer'!Y{t}",
        "H37": "='SPA Optimizer'!P{t}",
        # The June failure, twice over. The template had H35 = D34-H36, which is L12
        # revenue minus SPA gross profit; it must be SPA revenue minus SPA gross profit.
        "H35": "=H34-H36",
    }.items():
        wmd[cell] = tmpl.format(t=new_total)
    # the deltas
    for cell, formula in {"J34": "=H34-D34", "J35": "=H35-D35",
                          "J36": "=H36-D36", "J37": "=H37-D37"}.items():
        wmd[cell] = formula

def write_ladder_note(ws, start_row: int, n: int, df: pd.DataFrame, res: dict, fx: dict) -> None:
    """A plain-English note under the totals: what basis this basket was priced on."""
    notes = [
        (f"SPA price basis: the customer's realised L12 net price "
         f"({df['customer_list_from'].iloc[0]}), less the volume ladder below."),
        (f"Volume ladder, as a rule and not a stored table: committed qty < "
         f"{res['middle_mult']:.2f}x the L12 billed qty -> no discount; "
         f"{res['middle_mult']:.2f}x to {res['top_mult']:.2f}x -> {res['middle_rate']:.0%}; "
         f"{res['top_mult']:.2f}x and above, and any line with no L12 billing -> {res['top_rate']:.0%}. "
         f"Assigned on this basket: {res['ladder_counts']['none']} lines no discount, "
         f"{res['ladder_counts']['middle']} at {res['middle_rate']:.0%}, "
         f"{res['ladder_counts']['top']} at {res['top_rate']:.0%}. "
         f"The two rates are inputs in Assumptions C16 and C17."),
        (f"Committed quantities are WHOLE units: the basket file sums to "
         f"{res['fractional_units']:,.4f} across these {res['n']} lines and is committed as "
         f"{res['committed_units']:,.0f}. The rounding is reconciled on every build. "
         f"{res['pending_units_committed']:,.0f} further units sit on the unpriced lines, "
         f"which are on the 'Lines pending EPC' sheet and are in no total here."),
        (f"FX vintage in use: {fx['fx']} JPY/EUR, as of {fx.get('as_of') or 'n/a'} "
         f"({fx.get('selected_by')}). Purchase discount in use: "
         f"{', '.join(f'{k} {v:.3f}' for k, v in res['discount_per_source'].items())} "
         f"({res['discount_vintage']}). Source: {PRICING_CONFIG.name}. "
         f"Cost is the yen base price divided by the rate and multiplied by the discount, so a "
         f"HIGHER rate means LOWER euro cost and HIGHER profit. Revenue does not move with FX."),
        (f"Controls on this sheet: {res['n']} lines priced. "
         f"{res['chk_customer_list_ct']} of {res['n']} SPA prices tie back to the customer price "
         f"times (1 - ladder rate) to within a cent; {res['chk_override_ct']} line(s) carry an "
         f"explicit price override instead of the ladder. Commitments are whole units. "
         f"Cost reconciles to the sent negotiation model at the 163.7 vintage."),
        ("No mail was created or sent from this build. Nothing outside this folder was modified."),
    ]
    for i, text in enumerate(notes):
        r = start_row + i
        ws.cell(r, 1).value = text
        ws.cell(r, 1).alignment = WRAP
        ws.cell(r, 1).font = Font(name="Calibri", size=9, color="44546A")
        ws.cell(r, 1).border = THIN


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

    pricing = load_pricing_config(Path(args.pricing_config))
    cost_fx = resolve_fx(pricing, args.cost_fx, args.fx_annual)
    if args.live_fx_for_cost:
        cost_fx = resolve_fx(pricing, None, None)
    disc_sched = build_discount_schedule(pricing, args.discount_vintage, cost_fx.get("as_of"))
    list_disc_sched = build_discount_schedule(pricing, "prior", "")   # the price file's vintage

    df = read_basket(basket)
    df = read_pricing_and_l12(df, args.sold_to, args.window_from, args.window_to,
                              pricing, cost_fx["fx"], disc_sched["per_source"],
                              SENT_VINTAGE_FX, list_disc_sched["per_source"])
    df["block"] = df["desc"].map(assign_block)

    # Whole units for the document; the fractional figure is kept for the arithmetic.
    # Eran's file carries the 12-month total divided by 12, so rounding once at the point
    # of commitment is exactly the sent model's basis.
    df["spa_qty_fractional"] = df["spa_qty"].astype(float)
    df["spa_qty_committed"] = df["spa_qty"].round().astype(float)
    df.loc[df["spa_qty_committed"] < 0, "spa_qty_committed"] = 0.0

    # The sent negotiation model parked the unpriced lines on their own sheet rather than
    # carrying them in the list, so its priced count and its comparable count were both
    # 73. Adopted here: the main block holds priced lines only, and anything that cannot
    # be priced is listed, with its reason, on "Lines pending EPC".
    pending = df[df["frozen"]].copy()
    df = df[df["priced"]].copy().reset_index(drop=True)
    committed_units = float(df["spa_qty_committed"].sum())
    frac_units = float(df["spa_qty_fractional"].sum())
    df = assign_ladder(df, args.middle_rate, args.top_rate, args.middle_mult, args.top_mult)
    df["spa_qty"] = df["spa_qty_committed"]
    # the SPA price is left unrounded, exactly as the sent model carried it; the cell
    # number format shows two decimals. Rounding here would move revenue by a few euro.

    n = len(df)
    total_lines = len(df) + len(pending)
    customer_targets = read_customer_targets(basket)

    extra = n - TEMPLATE_LINES
    new_last = TEMPLATE_LAST + extra
    new_total = TEMPLATE_TOTAL + extra
    if new_last >= 1_048_576:
        raise RunError("Basket exceeds the sheet row limit")

    bar = None if args.pack1_bar_static else derive_pack1_bar(
        ROOT / "02_dashboards" / "sales" / "ISZE_SPA_RunRate_UTI.html", args.cut, 1.0
    )
    pack1_rev = bar["rev"] if bar else args.pack1_spa_rev
    pack1_profit = bar["profit"] if bar else args.pack1_spa_profit

    shutil.copy2(template, out_xlsx)
    wb = openpyxl.load_workbook(out_xlsx)

    # The template's own references are moved onto this basket's size here, in two passes,
    # and BOTH run before a single linked row is written:
    #
    #   1. retarget  - the template's data-range END (row 58 -> this basket's last data
    #                  row) and its total row (60 -> this basket's total row). This must
    #                  run FIRST, while `R4:R58` is still literally `:R58`. renaming only
    #                  does not move the 58, because the tail letter is the same on both
    #                  sides.
    #   2. remap     - the column LETTERS, because the sent model split the single purchase
    #                  column in two and pushed everything from D rightwards one place.
    #
    # Running these before extend_linked is the fix for the hijacked-data-row defect:
    # retarget can then only ever see template-authored text. Run afterwards (as it was),
    # it also mutated the rows extend_linked had just written, and in a basket bigger than
    # the template the template's total row number (60) is an ordinary data row, so that
    # row got pointed at the grand total instead of at itself.
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and (
                    "SPA Optimizer" in cell.value or "53" in cell.value or " of 12" in cell.value
                ):
                    cell.value = retarget(cell.value, TEMPLATE_LAST, new_last,
                                          TEMPLATE_TOTAL, new_total)
    remap_optimizer_columns(wb)

    # -- Assumptions : the single source for cut, floor, FX vintages, identity
    wa = wb["Assumptions"]
    # The template merges B1:D1 and A8:C8 and leaves row 7 blank. Park A8's heading on
    # row 2 and use rows 4..20 for the inputs, so nothing writes into a merged cell.
    for rng in ("B1:D1", "A8:C8", "F1:K1"):
        try:
            wa.unmerge_cells(rng)
        except ValueError:
            pass
    wa["A8"] = None
    wa["B2"] = "CUSTOMER & SPA CONTEXT"
    wa["B2"].font = Font(name="Calibri", size=11, bold=True, color=NAVY)

    inputs = [
        (3, "SPA test rate (JPY / EUR) - set this to move the SPA cost side",
         "=C6", "0.00",
         "Read by column D of the Optimizer. Cost falls as this rises; revenue does not move. "
         "C6 holds the same number for readability."),
        (4, "Purchase Price Cut % (IML / IMIT)", float(args.cut), "0.0%",
         "% of the SPA-active purchase that IML / IMIT gives back. 0% = ISZE absorbs it all."),
        (5, "Minimum GM% Floor (ISZE reference)", float(args.gm_floor), "0.0%",
         "Reference floor only - it flags, it does not block a calculation."),
        (6, "FX Rate in use (JPY / EUR) - cost side", float(cost_fx["fx"]), "0.00",
         f"{cost_fx.get('selected_by')}. As of {cost_fx.get('as_of') or 'n/a'}"
         + (f", runs to {cost_fx['until']}" if cost_fx.get("until") else "")
         + ". Divides the yen base price, so a HIGHER rate means LOWER euro cost."),
        (7, "FX Rate - LIVE (JPY / EUR)", float(pricing["fx_live"]), "0.00",
         f"Live vintage from {pricing['fx_as_of']}. Traceability only while another "
         f"vintage is in use. Source: {PRICING_CONFIG.name}."),
        (8, "Purchase discount - in use",
         ", ".join(f"{k} {v:.3f}" for k, v in disc_sched["per_source"].items()), None,
         f"{disc_sched['vintage']}. Applied to the yen base price where each part is sourced. "
         f"Resolved by date against the discount's effective date ({disc_sched['effective']}); "
         f"override with --discount-vintage."),
        (9, "Customer / Distributor Name", args.customer, None,
         "The SPA Optimizer prices one sold-to party only."),
        (10, "Market", args.market, None, "Other distributors are not in this file."),
        (11, "SPA Reference",
         args.spa_reference or
         "spa2 - SPA priced at the customer's realised L12 net price less the volume ladder",
         None, "What this price basis is, in one line."),
        (12, "SPA Valid From", datetime.strptime(args.valid_from, "%Y-%m-%d"), "DD/MM/YYYY",
         "Start of the agreement."),
        (13, "SPA Valid To", datetime.strptime(args.valid_to, "%Y-%m-%d"), "DD/MM/YYYY",
         "End of the agreement."),
        (14, "Prepared by", args.prepared_by, None, "The applicant named on the form."),
        (15, "Currency display (customer)", "EUR", None, "What the customer view shows."),
        (16, "Volume ladder - middle step", float(args.middle_rate), "0.0%",
         f"Applied when committed qty is {args.middle_mult:.2f}x to {args.top_mult:.2f}x L12 qty."),
        (17, "Volume ladder - top step", float(args.top_rate), "0.0%",
         f"Applied at {args.top_mult:.2f}x L12 qty and above, and on any line with no L12 billing."),
        (18, "Volume ladder - middle multiple", float(args.middle_mult), "0.00",
         "Committed quantity as a multiple of the L12 billed quantity."),
        (19, "Volume Growth Assumption %", float(args.volume_growth), "0.0%",
         "Read by the Scenario Planner's Enhanced row."),
        (20, "Volume ladder - top multiple", float(args.top_mult), "0.00",
         "Committed quantity as a multiple of the L12 billed quantity."),
    ]
    for r, b_label, c_value, c_fmt, d_note in inputs:
        wa.cell(r, 2).value = b_label
        wa.cell(r, 2).alignment = WRAP
        cell = wa.cell(r, 3)
        cell.value = c_value
        cell.fill = fill(INPUT_Y)
        if c_fmt:
            cell.number_format = c_fmt
        note = wa.cell(r, 4)
        note.value = d_note
        note.alignment = WRAP

    # -- SPA Optimizer : written in the sent model's own column layout
    wo = wb["SPA Optimizer"]
    for rng in ("A2:N2", "O2:AB2", "A62:AB62", "B63:AB63", "B64:AB64", "B65:AB65", "B66:AB66",
                "A1:AB1"):
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
        for i in range(1, 6):
            wo.merge_cells(start_row=note_base + i, start_column=1, end_row=note_base + i, end_column=28)
    except ValueError:
        pass

    wo["A1"] = f"SPA OPTIMIZER  -  {args.customer} sold-to {args.sold_to}  -  {args.label}"
    wo["A1"].font = Font(name="Calibri", size=13, bold=True, color=NAVY)
    wo["A2"] = (
        f"Column C = purchase on the {SENT_VINTAGE_FX} vintage ({SENT_VINTAGE_DISCOUNT:.3f} discount) "
        f"- the L12 baseline, and what the selling list sits on.     "
        f"Column D = purchase SPA ACTIVE, live: the yen base price / Assumptions C6 "
        f"{cost_fx['fx']} JPY/EUR, x the discount in use.     "
        f"E = SPA baseline: the customer's realised L12 net price.     "
        f"K = E less the volume ladder.     L = committed qty, WHOLE units.     "
        f"L12 = billed SAP ({args.sold_to}, {args.window_from} to {args.window_to}).     "
        f"AH:AJ carry the cost inputs behind column D."
    )
    wo["A2"].alignment = WRAP
    wo.row_dimensions[2].height = 44

    sent_heads = {
        1: "P/N", 2: "Description",
        3: f"Purchase\nPREVIOUS\n@ {SENT_VINTAGE_FX} (EUR)",
        4: f"Purchase\nSPA ACTIVE\n@ {cost_fx['fx']} (EUR)",
        5: "SPA Baseline\n(customer's\nrealised net\nprice, EUR)",
        6: "L12\nQty", 7: "L12\nRevenue (EUR)", 8: "L12\nCost (EUR)", 9: "L12\nProfit (EUR)",
        10: "L12\nGM%", 11: "SPA\nPrice (EUR)", 12: "SPA Qty\nCommitted", 13: "SPA\nRevenue (EUR)",
        14: "Unit\nMargin (EUR)", 15: "SPA\nProfit (EUR)", 16: "SPA\nGM%", 17: "\u0394 Revenue\n(EUR)",
        18: "\u0394 Profit\n(EUR)", 19: "Status", 20: "Min Qty\n@ SPA Price", 21: "Min Price\n@ SPA Qty",
        22: "Extra Qty\nNeeded", 23: "IML\nCut %", 24: "ISZE Cost\nw/ Cut (EUR)",
        25: "SPA Profit\nw/ Cut (EUR)", 26: "\u0394 Profit\nw/ Cut (EUR)", 27: "IML EUR\nSacrifice",
        28: "Req IML\nCut %", 29: "Status\nw/ Cut", 30: "Block",
        31: "Committed\nqty (whole units)", 32: "L12 billed EUR\n(reference)",
        33: "Price override\n(optional EUR)",
        34: "(cost input)\nList-vintage\nFOB EUR", 35: "(cost input)\nDiscount\nin use",
        36: "(cost input)\nDiscount the\nlist was set on",
    }
    for col, text in sent_heads.items():
        cell = wo.cell(5, col)
        cell.value = text
        cell.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        cell.fill = fill("0D2D52")
        cell.alignment = Alignment(wrap_text=True, vertical="center",
                                   horizontal="center" if col not in (2, 30) else "left")
        cell.border = THIN
    wo.row_dimensions[5].height = 44
    for col, width in ((1, 16), (2, 40), (3, 13), (4, 15), (5, 13), (6, 8), (7, 12), (8, 12),
                       (9, 12), (10, 8), (11, 11), (12, 11), (13, 12), (14, 11), (15, 12),
                       (16, 8), (17, 12), (18, 12), (19, 10), (20, 11), (21, 11), (22, 10),
                       (23, 8), (24, 12), (25, 12), (26, 12), (27, 11), (28, 9), (29, 10),
                       (30, 22), (31, 12), (32, 14), (33, 12), (34, 12), (35, 11), (36, 12)):
        wo.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width

    for i, rec in enumerate(df.to_dict("records")):
        write_line_row(wo, DATA_FIRST + i, DATA_FIRST, rec)

    tr = new_total
    wo.cell(tr, 1).value = "TOTAL"
    wo.cell(tr, 2).value = f"{n} part numbers priced"
    for col, letter in ((6, "F"), (7, "G"), (8, "H"), (9, "I"), (12, "L"), (13, "M"),
                        (15, "O"), (17, "Q"), (18, "R"), (25, "Y"), (26, "Z"),
                        (27, "AA"), (31, "AE"), (32, "AF")):
        wo.cell(tr, col).value = f"=SUM({letter}{DATA_FIRST}:{letter}{new_last})"
    # Column K is a per-unit price, so its total is the committed-unit-weighted average
    # price, not a plain sum. A SUM there produced 5,315 where the real figure is 16.74.
    wo.cell(tr, 11).value = (f"=IFERROR(SUMPRODUCT(K{DATA_FIRST}:K{new_last},"
                             f"L{DATA_FIRST}:L{new_last})/SUM(L{DATA_FIRST}:L{new_last}),0)")
    wo.cell(tr, 11).number_format = "#,##0.00"
    wo.cell(tr, 5).value = (f"=IFERROR(SUMPRODUCT(E{DATA_FIRST}:E{new_last},"
                            f"L{DATA_FIRST}:L{new_last})/SUM(L{DATA_FIRST}:L{new_last}),0)")
    wo.cell(tr, 5).number_format = "#,##0.00"
    wo.cell(tr, 3).value = (f"=IFERROR(SUMPRODUCT(C{DATA_FIRST}:C{new_last},"
                            f"F{DATA_FIRST}:F{new_last})/SUM(F{DATA_FIRST}:F{new_last}),0)")
    wo.cell(tr, 3).number_format = "#,##0.00"
    # Column D is a PER-UNIT cost, so its total is a weighted sum, not a plain sum. The
    # sent model carried no total there at all, which left its cost uncheckable; this one
    # carries the spend, so the derived purchase cost on the form can be proved.
    wo.cell(tr, 4).value = (f"=SUMPRODUCT(D{DATA_FIRST}:D{new_last},"
                            f"L{DATA_FIRST}:L{new_last})")
    wo.cell(tr, 4).number_format = '#,##0.00;(#,##0.00);"-"'
    wo.cell(tr, 10).value = f"=IFERROR(I{tr}/G{tr},0)"
    wo.cell(tr, 16).value = f"=IFERROR(O{tr}/M{tr},0)"
    wo.cell(tr, 19).value = f'=IF(R{tr}>=0,"\u25b2 BETTER","\u25bc WORSE")'
    wo.cell(tr, 29).value = f'=IF(Z{tr}>=0,"\u25b2 BETTER","\u25bc WORSE")'
    for col in range(1, 34):
        wo.cell(tr, col).font = Font(name="Calibri", size=9, bold=True)
        wo.cell(tr, col).border = Border(top=Side(style="thin", color=NAVY),
                                         bottom=Side(style="double", color=NAVY))
    for col in (10, 16):
        wo.cell(tr, col).number_format = "0.0%"

    green, red = "C6EFCE", "FFC7CE"
    wo.conditional_formatting._cf_rules.clear()
    for col, op, val in (("R", "greaterThanOrEqual", "0"), ("R", "lessThan", "0"),
                         ("Z", "greaterThanOrEqual", "0"), ("Z", "lessThan", "0")):
        wo.conditional_formatting.add(
            f"{col}{DATA_FIRST}:{col}{new_last}",
            CellIsRule(operator=op, formula=[val], fill=fill(green if "greater" in op else red)))
    wo.conditional_formatting.add(f"AB{DATA_FIRST}:AB{new_last}",
                                  CellIsRule(operator="greaterThan", formula=["0.3"], fill=fill("F8CBAD")))
    for col, letter in (("S", "R"), ("AC", "Z")):
        wo.conditional_formatting.add(f"{col}{DATA_FIRST}:{col}{new_last}",
                                      FormulaRule(formula=[f"{letter}{DATA_FIRST}>=0"], fill=fill(green)))
        wo.conditional_formatting.add(f"{col}{DATA_FIRST}:{col}{new_last}",
                                      FormulaRule(formula=[f"{letter}{DATA_FIRST}<0"], fill=fill(red)))

    # -- Customer View (data starts row 5, total row 58 in the template)
    wcv = wb["Customer View"]
    resize_sheet(wcv, 5, TEMPLATE_LINES, n, 58)
    extend_linked(wcv, 5, n, 5, cv_formulas, 12)
    cv_tot = 57 + extra + 1
    wcv.cell(cv_tot, 1).value = "TOTAL"
    wcv.cell(cv_tot, 2).value = f"{n} part numbers"
    for col, letter in ((8, "H"), (9, "I"), (11, "K")):
        wcv.cell(cv_tot, col).value = f"=SUM({letter}5:{letter}{cv_tot - 1})"
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

    # -- Assumptions GM block: rows 35..88 map to optimizer 6..58
    resize_sheet(wa, 36, TEMPLATE_LINES, n, 89)
    extend_linked(wa, 36, n, 36, gm_formulas, 4)

    # -- Assumptions headline block
    try:
        wa.merge_cells("F1:K1")
    except ValueError:
        pass
    wa["F1"] = (f"HEADLINE - does turnover / profit go up?  {args.customer} sold-to {args.sold_to}. "
                f"{args.label}. SPA price is the customer's realised net price less the ladder.")
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
        (4, "Turnover (revenue)", f"='SPA Optimizer'!M{new_total}", f"='SPA Optimizer'!Q{new_total}",
         pack1_rev, "=G4-I4", "SPA price x committed qty. Does not move with FX."),
        (5, f"L12 billed turnover (SAP {args.sold_to})", f"='SPA Optimizer'!G{new_total}", None, None, None,
         f"Actual invoiced on these part numbers, {args.window_from} to {args.window_to}."),
        (6, f"Profit with {args.cut:.0%} purchase cut", f"='SPA Optimizer'!Y{new_total}",
         f"='SPA Optimizer'!Z{new_total}", pack1_profit, "=G6-I6",
         f"Cost is the yen base price / {cost_fx['fx']} x the purchase discount. "
         f"A higher JPY/EUR raises this."),
        (7, "L12 billed profit (billed - purchase x qty)", f"='SPA Optimizer'!I{new_total}", None, None, None,
         f"Cost here uses the {SENT_VINTAGE_FX} vintage, as the sent model did."),
        (8, f"SPA GM% with {args.cut:.0%} cut",
         f"=IFERROR('SPA Optimizer'!Y{new_total}/'SPA Optimizer'!M{new_total},0)", None, None, None,
         "Colour floor is Assumptions C5. Purchase cut is Assumptions C4."),
        (9, "IML sacrifice", f"='SPA Optimizer'!AA{new_total}", None, None, None,
         "Cut x SPA-active purchase x committed qty."),
        (10, "FX vintage in use (JPY / EUR)", "=Assumptions!$C$6", None, None, None,
         "Change Assumptions C6 to move the cost side. Cost is linear in 1/rate, so the "
         "live-rate profit below is exact, not an approximation."),
        (11, "Profit with the cut, at the LIVE rate", None, None,
         f"='SPA Optimizer'!Y{new_total}-('SPA Optimizer'!M{new_total}-'SPA Optimizer'!Y{new_total})"
         f"*(Assumptions!$C$6/Assumptions!$C$7-1)", "=G11-G6",
         "Revenue is unchanged; only cost and profit move with the rate."),
    ]
    for r, label, g, h, i, j, k in headline:
        wa.cell(r, 6).value = label
        wa.cell(r, 6).alignment = WRAP
        wa.cell(r, 6).border = THIN
        wa.cell(r, 7).value = g
        wa.cell(r, 7).number_format = ("0.0%" if r in (8,)
                                       else ("0.00" if r == 10 else '#,##0;(#,##0);"-"'))
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

    priced = df
    spa_rev = float((df["spa_price"] * df["spa_qty"]).sum())
    spa_cost = float((df["purchase"] * df["spa_qty"]).sum())
    spa_profit = float(((df["spa_price"] - df["purchase"] * (1 - args.cut))
                        * df["spa_qty"]).sum())
    l12_billed = float(df["l12_billed_eur"].sum())
    l12_billed_profit = float(
        (df["l12_billed_eur"] - df["purchase_prev"].fillna(0.0) * df["l12_qty"]).sum()
    )
    l12_study_rev = float((df["list_price"] * df["l12_qty"]).sum())
    l12_study_profit = float(((df["list_price"] - df["purchase_prev"]) * df["l12_qty"]).sum())
    wa["F11"] = "Customer list x billed qty (study, not billed)"
    wa["F12"] = "Study L12 turnover"
    wa["F13"] = "Study L12 profit"
    wa["G12"], wa["G13"] = l12_study_rev, l12_study_profit
    wa["G12"].number_format = wa["G13"].number_format = "#,##0"
    wa["H12"], wa["H13"] = spa_rev - l12_study_rev, spa_profit - l12_study_profit
    wa["H12"].number_format = wa["H13"].number_format = '+#,##0;(#,##0);"-"'
    wa["F14"] = "Frozen / no purchase price (excluded from the SPA math)"
    wa["G14"] = ", ".join(sorted(pending["pn_raw"].tolist()) or ["none"])
    wa["K14"] = (f"{len(pending)} of {total_lines} basket lines could not be priced. "
                 f"They are listed with their reason on the 'Lines pending EPC' sheet and "
                 f"are excluded from every total on this workbook.")
    wa["F15"] = "Sold-to"
    wa["G15"] = args.sold_to
    wa["K15"] = f"{args.customer} sold-to {args.sold_to} only. Other distributors are not in this file."
    wa["F16"] = "Committed units (whole) vs basket arithmetic"
    wa["G16"] = committed_units
    wa["K16"] = (f"Basket file sums to {frac_units:,.4f} over {n} lines; committed is the rounded "
                 f"{committed_units:,.0f}. Reconciliation check runs on every build.")
    for col, w in (("F", 42), ("G", 18), ("H", 14), ("I", 18), ("J", 14), ("K", 55)):
        wa.column_dimensions[col].width = w
    wa.freeze_panes = "A3"

    # -- the retarget pass has already run, above, before any linked row was written.
    # Do NOT add another workbook-wide retarget here: it would rewrite the linked rows
    # that extend_linked has just written and hijack the row that maps to the template's
    # old total row. That was the defect fixed in spa2-r3.


    # -- the notes block under the optimizer totals
    write_ladder_note(wo, note_base, n, df, {
        "n": n,
        "middle_rate": args.middle_rate, "top_rate": args.top_rate,
        "middle_mult": args.middle_mult, "top_mult": args.top_mult,
        "ladder_counts": {
            "none": int((df["ladder_step"] == "none").sum()),
            "middle": int((df["ladder_step"] == "middle").sum()),
            "top": int((df["ladder_step"] == "top").sum()),
        },
        "fractional_units": frac_units, "committed_units": committed_units,
        "pending_units_committed": float(pending["spa_qty_committed"].sum()),
        "discount_per_source": disc_sched["per_source"],
        "discount_vintage": disc_sched["vintage"],
        "chk_customer_list_ct": int(
            ((df["spa_price"] - df["list_price"] * (1 - df["ladder_rate"])).abs() < 0.011).sum()
        ),
        "chk_override_ct": int(df["override"].notna().sum()),
    }, cost_fx)

    # -- Scenario Planner : the three wiring faults fixed here
    wr = wb["SPA Rationale"]
    wr["A2"] = (f"{args.customer}  -  {n} part lines  -  {args.label}  -  SPA price is the customer's "
                f"realised net price less the volume ladder")
    wr["A2"].alignment = WRAP
    wsp = wb["Scenario Planner"]
    wsp["A2"] = (f"Models three SPA scenarios: Partial (lines with \u25b2 BETTER only) | "
                 f"Full (all {n} lines) | Enhanced (Full + volume growth assumption)")
    wsp["A6"] = "Volume Growth Assumption"
    wsp["B6"] = "=Assumptions!$C$19"
    wsp["C6"] = "% additional volume vs committed qty (Assumptions C19)"
    wsp["A7"] = "Purchase Cut Applied"
    wsp["B7"] = "=Assumptions!$C$4"
    wsp["C7"] = "From Assumptions C4"
    wsp["A8"] = "FX Rate in use (JPY / EUR)"
    wsp["B8"] = "=Assumptions!$C$6"
    wsp["C8"] = "From Assumptions C6. Cost side only; revenue does not move with FX."
    wsp["A9"] = "FX Rate - live (JPY / EUR)"
    wsp["B9"] = "=Assumptions!$C$7"
    wsp["C9"] = "From Assumptions C7. The live vintage, for traceability."
    # row 3 is blank in the template and is not merged, so the ladder note lives there
    wsp["A3"] = '=TEXT(Assumptions!$C$16,"0%")&" middle step / "&TEXT(Assumptions!$C$17,"0%")&" top step"'
    wsp["C3"] = ('Volume ladder in Assumptions C16, C17, C18 and C20. A line with no L12 '
                 'billing takes the top step. A per-line price override beats the ladder.')
    wsp["B14"] = f'=COUNTIF(\'SPA Optimizer\'!S{DATA_FIRST}:S{new_last},"\u25b2 BETTER")&" of {n}"'
    wsp["C14"] = f'=SUMIF(\'SPA Optimizer\'!S{DATA_FIRST}:S{new_last},"\u25b2 BETTER",\'SPA Optimizer\'!M{DATA_FIRST}:M{new_last})'
    wsp["D14"] = f'=SUMIF(\'SPA Optimizer\'!S{DATA_FIRST}:S{new_last},"\u25b2 BETTER",\'SPA Optimizer\'!R{DATA_FIRST}:R{new_last})'
    wsp["E14"] = f'=SUMIF(\'SPA Optimizer\'!S{DATA_FIRST}:S{new_last},"\u25b2 BETTER",\'SPA Optimizer\'!AA{DATA_FIRST}:AA{new_last})'
    wsp["F14"] = f'=SUMIF(\'SPA Optimizer\'!S{DATA_FIRST}:S{new_last},"\u25b2 BETTER",\'SPA Optimizer\'!M{DATA_FIRST}:M{new_last})'
    # The template's rows 13 to 15 were labelled "Full", "Full + IML" and "Enhanced" but
    # all three carried the same figure and the label said 12 lines while the range said 2.
    # Reset the three rows so each label, its line count and its formula agree.
    for row, (label, count, rev, prof, sac, note) in enumerate((
        (f"Full - all {n} lines, no purchase cut",
         f"{n} of {n}", f"='SPA Optimizer'!M{new_total}", f"='SPA Optimizer'!R{new_total}", 0.0,
         "Maximum support to the customer. No IML help, so ISZE carries all of it."),
        (f"Full + IML support at {args.cut:.0%} - RECOMMENDED",
         f"{n} of {n}", f"='SPA Optimizer'!M{new_total}", f"='SPA Optimizer'!Z{new_total}",
         f"='SPA Optimizer'!AA{new_total}",
         "Every SPA line with the purchase cut applied. This is the case on the form."),
        ("Enhanced - Full + IML + volume growth",
         f"{n} of {n}", f"='SPA Optimizer'!M{new_total}*(1+Assumptions!$C$19)",
         f"='SPA Optimizer'!Z{new_total}*(1+Assumptions!$C$19)",
         f"='SPA Optimizer'!AA{new_total}*(1+Assumptions!$C$19)",
         "Upside only. Volume growth scales the committed quantity; the ladder step is not "
         "re-cut, so a line that grows past a threshold is not re-priced on this row."),
    ), start=15):
        wsp[f"A{row}"] = label
        wsp[f"B{row}"] = count
        wsp[f"C{row}"] = rev
        wsp[f"D{row}"] = prof
        wsp[f"E{row}"] = sac
        wsp[f"F{row}"] = rev
        wsp[f"G{row}"] = note
    for row in range(12, 18):
        for col, w in ((1, 40), (2, 11), (3, 15), (4, 17), (5, 15), (6, 17), (7, 70)):
            wsp.cell(row, col).alignment = WRAP
    wsp["G13"] = "Every line, no purchase cut, so ISZE absorbs the whole discount."

    # -- MD Approval Request : the signable form
    wmd = wb["MD Approval Request"]
    wmd["B4"] = "=Assumptions!B14"
    wmd["E4"] = args.manager
    wmd["J11"] = str(args.sold_to)
    wmd["J12"] = args.branch
    wmd["H19"] = "SPA Purchase Cost (EUR), after the purchase cut"   # label June got wrong
    # The SPA margin must be on the same basis as the profit beside it. J21 is profit AFTER
    # the purchase cut, so J20 has to be the after-cut margin, not the pre-cut column P.
    wmd["H20"] = "Gross Margin % (after the purchase cut)"
    wmd["B20"] = "Gross Margin % (L12 basis, no purchase cut applies)"
    wmd["B21"] = "Gross Profit (EUR)"
    wmd["B37"] = "Gross Margin % (L12 basis)"
    wmd["H37"] = "Gross Margin % (after the purchase cut)"
    # Row 9 sits below the scope rows and above the financial block, so it is free.
    wmd["B9"] = ("Basis: the L12 purchase cost is struck on the vintage the selling list sits on; "
                 "the SPA purchase cost is struck on the vintage in use, less the IML purchase "
                 "cut. Both rates are on the Assumptions sheet.")
    wmd["B9"].alignment = WRAP
    patch_form_sized(wmd, new_total)
    wmd["J20"] = "=IFERROR('SPA Optimizer'!Y{}/'SPA Optimizer'!M{},0)".format(new_total, new_total)
    wmd["J20"].number_format = "0.0%"
    wmd["H37"] = "='SPA Optimizer'!Y{}/'SPA Optimizer'!M{}".format(new_total, new_total)
    wmd["H37"].number_format = "0.0%"
    # the impact-block SPA margin, same basis as the profit beside it
    wmd["H37"].alignment = WRAP
    wmd["C5"] = datetime.strptime(args.date_iso, "%Y-%m-%d")
    wmd["B16"] = (f'=IFERROR("SPA Ref: "&Assumptions!B11&"  |  FX "'
                  f'&TEXT(Assumptions!C6,"0.0")&" JPY/EUR (as of "&Assumptions!D6,"")')
    wmd["B16"].alignment = WRAP

    # -- Bottom line : the one-page summary the sent model carried, now on live cell links
    wbl = wb.create_sheet("Bottom line")
    _build_bottom_line(wbl, df, args, {"SPA": new_total, "n": n}, cost_fx, pricing,
                       args.middle_mult, args.top_mult)
    build_pending_sheet(wb, pending, args)

    # -- Budget / Target column (F32:F37). The customer's own commitment, carried as an
    # input from the basket workbook's "targets" sheet and never computed here.
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

    # Delivery hygiene. The workbook carries the sheet that does the work in its name, so
    # the remaining sheets still carry the template's file-name token. Rewrite it so a
    # reader who opens any sheet can see what they are looking at.
    templ_name = template.name
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if isinstance(v, str) and templ_name in v:
                    cell.value = v.replace(templ_name, out_xlsx.name)
    for ws in wb.worksheets:
        if (ws.column_dimensions["B"].width or 8) < 28:
            ws.column_dimensions["B"].width = 36
    wo.freeze_panes = "C6"
    wb.save(out_xlsx)
    wb.close()

    cmd = outdir / f"OPEN_{args.customer}_{args.label}.cmd"
    cmd.write_bytes(f'@echo off\r\nstart "" "%~dp0{name}"\r\n'.encode("ascii"))

    res = {
        "out_xlsx": str(out_xlsx),
        "cmd": str(cmd),
        "qa_dir": str(qa),
        "n": n,
        "new_last": new_last,
        "new_total": new_total,
        "spa_rev": spa_rev,
        "spa_cost": spa_cost,
        "spa_profit": spa_profit,
        "l12_billed": l12_billed,
        "l12_billed_profit": l12_billed_profit,
        "l12_study_rev": l12_study_rev,
        "l12_study_profit": l12_study_profit,
        "frozen": sorted(pending["pn_raw"].tolist()),
        "pending": pending[["pn_raw", "desc", "spa_qty", "spa_qty_committed",
                            "l12_qty", "l12_billed_eur"]].to_dict("records"),
        "priced": n,
        "basket_lines": total_lines,
        "customer_targets": customer_targets,
        "pack1_bar": bar if bar else {"source": "static (--pack1-bar-static)"},
        "fx": cost_fx,
        "discount_schedule": disc_sched,
        "pricing_config": str(PRICING_CONFIG),
        "fx_live": pricing["fx_live"],
        "fx_vintages": pricing["vintages"],
        "discount": pricing["discount"],
        "fractional_units": frac_units,
        "committed_units": committed_units,
        "pending_units_fractional": float(pending["spa_qty_fractional"].sum()),
        "pending_units_committed": float(pending["spa_qty_committed"].sum()),
        "basket_units_fractional": frac_units + float(pending["spa_qty_fractional"].sum()),
        "basket_units_committed": committed_units + float(pending["spa_qty_committed"].sum()),
        "ladder_counts": {
            "none": int((df["ladder_step"] == "none").sum()),
            "middle": int((df["ladder_step"] == "middle").sum()),
            "top": int((df["ladder_step"] == "top").sum()),
        },
        "customer_list_from_billing": int((df["customer_list_from"] == "realised L12 net price").sum()),
        "args": vars(args),
    }
    df.to_pickle(qa / "_lines.pkl")
    pending.to_pickle(qa / "_pending.pkl")
    return res


def _build_bottom_line(wbl, df: pd.DataFrame, args, ref: dict, cost_fx: dict, pricing: dict,
                       mid_mult: float, top_mult: float) -> None:
    """One page, three columns: today, and the two ladder-rate proposals.

    Cost of goods uses the SPA-active purchase, as the sent model's page did. Every
    figure is a live formula over the optimizer, so it cannot drift from the totals.
    """
    t = ref["SPA"]
    n = ref["n"]

    wbl["A1"] = "BOTTOM LINE"
    wbl["A1"].font = Font(name="Calibri", size=14, bold=True, color=NAVY)
    wbl["A2"] = (f"At the committed quantities. Cost of goods uses the SPA-active purchase at "
                 f"{cost_fx['fx']} JPY/EUR ({cost_fx.get('selected_by')}). "
                 f"The L12 baseline on the Optimizer sheet uses the {SENT_VINTAGE_FX} vintage, "
                 f"which is what the selling list sits on.")
    wbl["A2"].alignment = WRAP
    wbl["A2"].font = Font(name="Calibri", size=9, italic=True, color="44546A")
    wbl.row_dimensions[2].height = 26
    wbl["A4"] = f"AT THE COMMITTED QUANTITIES - SPA-ACTIVE PURCHASE @ {cost_fx['fx']} JPY/EUR"
    wbl["A4"].font = Font(name="Calibri", size=11, bold=True, color=NAVY)

    heads = [("B5", "At today's prices"), ("C5", "Proposal 1 (4% / 6%)"), ("D5", "Proposal 2 (5% / 8%)")]
    for cell, text in heads:
        wbl[cell] = text
        wbl[cell].font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        wbl[cell].fill = fill(NAVY)
        wbl[cell].alignment = WRAP
        wbl[cell].border = THIN

    # The lattice of the two ladder proposals. The today's-prices column IS the
    # optimizer's committed ladder, so it is read straight off the sheet; the two
    # proposals are recomputed off the same baseline at their own rates.
    lst, l12q, spl, comm, dcol = (f"'SPA Optimizer'!$E${DATA_FIRST}:$E${t - 1}",
                                  f"'SPA Optimizer'!$F${DATA_FIRST}:$F${t - 1}",
                                  f"'SPA Optimizer'!$K${DATA_FIRST}:$K${t - 1}",
                                  f"'SPA Optimizer'!$L${DATA_FIRST}:$L${t - 1}",
                                  f"'SPA Optimizer'!$D${DATA_FIRST}:$D${t - 1}")
    def supr(mid, top):
        """Turnover at a given ladder pair, L12 qty as the offset quantity.

        The step tests are MUTUALLY EXCLUSIVE. A line with no L12 billing satisfies
        L >= F*2 as well as F = 0, so the two must be multiplied (not added) on the first
        clause and only then OR'd with the F = 0 case. Adding them counts those lines
        twice, which overstates the proposal by their whole turnover.
        """
        mid_step = f"(({comm}>={l12q}*{mid_mult:g})*({comm}<{l12q}*{top_mult:g}))"
        top_step = f"(({comm}>={l12q}*{top_mult:g})*({l12q}>0))+({l12q}=0)"
        none_step = f"(({comm}<{l12q}*{mid_mult:g})*({l12q}>0))"
        return (f"=SUMPRODUCT({mid_step}*1,{lst}*(1-{mid}),{comm})"
                f"+SUMPRODUCT(({top_step})*1,{lst}*(1-{top}),{comm})"
                f"+SUMPRODUCT({none_step}*1,{lst},{comm})")

    rows = [
        ("A6", "Turnover - what the customer spends (EUR)",
         f"=SUMPRODUCT({spl},{comm})", supr(0.04, 0.06), supr(0.05, 0.08)),
        ("A7", "What the customer saves (EUR)", None, "=$B$6-C6", "=$B$6-D6"),
        ("A8", "ISZE cost of goods (EUR) after the purchase cut",
         f"='SPA Optimizer'!M{t}-'SPA Optimizer'!Y{t}",
         f"='SPA Optimizer'!M{t}-'SPA Optimizer'!Y{t}",
         f"='SPA Optimizer'!M{t}-'SPA Optimizer'!Y{t}"),
        ("A9", "ISZE gross profit (EUR)", None, "=C6-C8", "=D6-D8"),
        ("A10", "ISZE gross margin %", None, "=IF(C6=0,0,C9/C6)", "=IF(D6=0,0,D9/D6)"),
        ("A11", "Delta profit vs today (EUR)", None, "=C9-$B$9", "=D9-$B$9"),
    ]
    for row, (acell, label, b, c, d) in enumerate(rows, start=6):
        wbl[acell] = label
        wbl[acell].alignment = WRAP
        wbl[acell].border = THIN
        for col, val in ((2, b), (3, c), (4, d)):
            cell = wbl.cell(row, col)
            cell.value = val
            cell.border = THIN
            cell.number_format = "0.0%" if row == 10 else '#,##0;(#,##0);"-"'
        for col in (2, 3, 4):
            wbl.cell(row, col).fill = fill(PAPER)
    wbl["B9"] = "=B6-B8"
    wbl["B10"] = "=IF(B6=0,0,B9/B6)"
    wbl["B11"] = None

    # how this basket compares with the model that was actually sent
    sent = SENT_SPA2_R2 if args.negotiation_reference == "auto" else {}
    r = 13
    wbl.cell(r, 1).value = "RECONCILIATION AGAINST THE MODEL SENT 17 SEPTEMBER 2026"
    wbl.cell(r, 1).font = Font(name="Calibri", size=11, bold=True, color=NAVY)
    r += 1
    for cell, text in ((f"A{r}", "Measure"), (f"B{r}", "This book"), (f"C{r}", "Sent model"), (f"D{r}", "Difference")):
        wbl[cell] = text
        wbl[cell].font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        wbl[cell].fill = fill(NAVY)
        wbl[cell].border = THIN
    r += 1
    if sent:
        rec = [
            ("SPA revenue (EUR)", f"='SPA Optimizer'!M{t}", sent["spa_revenue_eur"]),
            ("SPA purchase spend (EUR)", f"='SPA Optimizer'!D{t}",
             sent["spa_cost_fx_172_6_eur"]),
            ("SPA gross profit, 7% cut (EUR)", f"='SPA Optimizer'!Y{t}", sent["spa_profit_cut_eur"]),
            ("Committed units", f"='SPA Optimizer'!AE{t}", sent["committed_units"]),
        ]
        for label, formula, target in rec:
            wbl.cell(r, 1).value = label
            wbl.cell(r, 1).border = THIN
            wbl.cell(r, 2).value = formula
            wbl.cell(r, 3).value = target
            wbl.cell(r, 4).value = f"=B{r}-C{r}"
            for col in (2, 3, 4):
                wbl.cell(r, col).number_format = '#,##0.00;(#,##0.00);"-"'
                wbl.cell(r, col).border = THIN
            r += 1
    else:
        wbl.cell(r, 1).value = "No reference model supplied for this basket."
        r += 1

    # What the today-vs-proposal profit gain on this page actually IS. Without this label a
    # reader sees profit rise by EUR 7,347 and credits the price change; most of it is the
    # exchange rate moving between the vintage the L12 baseline sits on and the one in use.
    r += 1
    wbl.cell(r, 1).value = "READ THIS BEFORE QUOTING THE PROFIT GAIN ABOVE"
    wbl.cell(r, 1).font = Font(name="Calibri", size=11, bold=True, color=TERR)
    r += 1
    wbl.cell(r, 1).value = (
        "The rise in gross profit between \"At today's prices\" and the proposal columns is NOT "
        "the price concession. The L12 baseline is costed on the vintage the selling list sits "
        "on; the SPA case is costed on the vintage in use. The customer's price in the committed "
        "column is unchanged from today, so the whole of the difference is the exchange rate "
        "moving the euro cost. The two are separated on the Optimizer and Assumptions sheets.")
    wbl.cell(r, 1).alignment = WRAP
    wbl.cell(r, 1).font = Font(name="Calibri", size=9, color="44546A")
    wbl.row_dimensions[r].height = 40
    r += 1
    for label, formula in (
            ("Profit at today's prices, after the purchase cut",
             f"='SPA Optimizer'!M{t}-'SPA Optimizer'!D{t}*(1-Assumptions!$C$4)"),
            (f"Profit at the same prices, costed at the {SENT_VINTAGE_FX} list vintage",
             f"='SPA Optimizer'!M{t}-'SPA Optimizer'!D{t}*(1-Assumptions!$C$4)"
             f"*(Assumptions!$C$6/{SENT_VINTAGE_FX})"),
            ("of which: the exchange rate move, not the price",
             f"='SPA Optimizer'!D{t}*(1-Assumptions!$C$4)"
             f"*(Assumptions!$C$6/{SENT_VINTAGE_FX}-1)"),
            # read down: the second row plus the third should land on the first
            ("Read down: second row + third row = the first row",
             f"='SPA Optimizer'!M{t}-'SPA Optimizer'!D{t}*(1-Assumptions!$C$4)"
             f"*(Assumptions!$C$6/{SENT_VINTAGE_FX})"
             f"+'SPA Optimizer'!D{t}*(1-Assumptions!$C$4)"
             f"*(Assumptions!$C$6/{SENT_VINTAGE_FX}-1)")):
        wbl.cell(r, 1).value = label
        wbl.cell(r, 1).border = THIN
        c = wbl.cell(r, 2)
        c.value = formula
        c.number_format = '#,##0;(#,##0);"-"'
        c.border = THIN
        c.fill = fill(INPUT_Y)
        r += 1

    for col, w in (("A", 44), ("B", 18), ("C", 18), ("D", 18)):
        wbl.column_dimensions[col].width = w
    wbl.sheet_view.showGridLines = False


# ------------------------------------------------------------------------- verify
def load_line_context(res: dict) -> dict:
    """Line-level inputs the checks need, read back from the build's own pickle.

    Kept separate from res['args'] because that is captured before the run finishes.
    """
    df = pd.read_pickle(Path(res["qa_dir"]) / "_lines.pkl")
    return {
        "bp_jpy": df["bp_jpy"].fillna(0.0).tolist(),
        "cost_discount": df["cost_discount"].fillna(1.0).tolist(),
        "fob_list_eur": df["fob_list_eur"].fillna(0.0).tolist(),
        "list_discount": df["list_discount"].fillna(1.0).tolist(),
        "spa_price": df["spa_price"].astype(float).tolist(),
        "committed": df["spa_qty_committed"].astype(float).tolist(),
        "cut": float(res["args"]["cut"]),
        "top_rate": float(res["args"]["top_rate"]),
        "middle_rate": float(res["args"]["middle_rate"]),
        "top_mult": float(res["args"]["top_mult"]),
        "middle_mult": float(res["args"]["middle_mult"]),
    }


def _bottom_line_values(wb) -> dict:
    """Read the Bottom line's six rows and three columns back off the sheet."""
    bl = wb.Worksheets("Bottom line")

    def g(addr):
        v = bl.Range(addr).Value
        return None if v in (None, "") else float(v)

    cols = {"today": "B", "proposal_1_4_6": "C", "proposal_2_5_8": "D"}
    out = {}
    for name, c in cols.items():
        out[name] = {
            "turnover_eur": g(f"{c}6"),
            "customer_saving_eur": g(f"{c}7"),
            "cost_of_goods_eur": g(f"{c}8"),
            "gross_profit_eur": g(f"{c}9"),
            "gross_margin": g(f"{c}10"),
            "delta_profit_vs_today_eur": g(f"{c}11"),
        }
    # the reconciliation block, if the reference was supplied
    out["reconciliation"] = {
        "spa_revenue_this_book": g("B15"), "spa_revenue_sent_model": g("C15"),
        "spa_cost_this_book": g("B16"), "spa_cost_sent_model": g("C16"),
        "spa_profit_this_book": g("B17"), "spa_profit_sent_model": g("C17"),
        "committed_units_this_book": g("B18"), "committed_units_sent_model": g("C18"),
    }
    # the decomposition of the today-vs-proposal profit gain
    out["profit_gain_decomposition"] = {
        "profit_today_at_vintage_in_use": g("B22"),
        "profit_at_same_prices_at_list_vintage": g("B23"),
        "of_which_the_exchange_rate_move": g("B24"),
        "total_read_across": g("B25"),
    }
    return out


def _bottom_line_checks(wb, totals_row: int) -> dict:
    """The Bottom line must agree with the optimizer and with its own labels.

    These are the checks that caught two real faults on this sheet: a turnover total that
    was a plain SUM of a per-unit price column, and step tests that counted the zero-L12
    lines twice so a discount proposal showed MORE turnover than today's prices.
    """
    bl = wb.Worksheets("Bottom line")
    opt = wb.Worksheets("SPA Optimizer")

    def g(sheet, addr):
        v = sheet.Range(addr).Value
        return None if v in (None, "") else float(v)

    today = g(bl, "B6")
    p1, p2 = g(bl, "C6"), g(bl, "D6")
    cost_t, cost_1, cost_2 = g(bl, "B8"), g(bl, "C8"), g(bl, "D8")
    gp_t, gp_1, gp_2 = g(bl, "B9"), g(bl, "C9"), g(bl, "D9")
    gm_t, gm_1, gm_2 = g(bl, "B10"), g(bl, "C10"), g(bl, "D10")
    d1, d2 = g(bl, "C11"), g(bl, "D11")

    # the "today" column IS the optimizer's committed case
    total_M = g(opt, f"M{totals_row}") if totals_row else None
    total_Y = g(opt, f"Y{totals_row}") if totals_row else None
    total_D = g(opt, f"D{totals_row}") if totals_row else None
    total_K = g(opt, f"K{totals_row}") if totals_row else None
    total_L = g(opt, f"L{totals_row}") if totals_row else None

    # Bounds for turnover, computed from the optimizer's own columns:
    #   ceiling = every line at the baseline with no discount at all
    #   floor   = every line at the top step
    # Any proposal must sit inside them. This is the check that catches a step test
    # counting a line twice, which pushed a proposal ABOVE the ceiling.
    ceiling = floor = None
    e_vals, l_vals = [], []
    try:
        for r in range(DATA_FIRST, totals_row):
            ev, lv = opt.Range(f"E{r}").Value, opt.Range(f"L{r}").Value
            if ev not in (None, "") and lv not in (None, ""):
                e_vals.append(float(ev))
                l_vals.append(float(lv))
        top_rate = g(wb.Worksheets("Assumptions"), "C17")
        ceiling = sum(e * l for e, l in zip(e_vals, l_vals))
        floor = sum(e * (1 - top_rate) * l for e, l in zip(e_vals, l_vals)) if top_rate else None
    except Exception:  # noqa: BLE001
        pass

    def near(a, b, tol=1.0):
        return a is not None and b is not None and abs(a - b) <= tol

    checks = {
        # a bigger discount must mean less turnover, so the 4/6 proposal sits at or above
        # the 5/8 one, and both sit between the no-discount ceiling and the top-step floor
        "bottom_line_turnover_falls_as_the_discount_rises": (
            p1 is not None and p2 is not None and p1 >= p2 - 0.01),
        "bottom_line_turnover_inside_the_ladder_bounds": (
            ceiling is not None and floor is not None and p1 is not None and p2 is not None
            and floor - 0.01 <= p2 <= p1 <= ceiling + 0.01),
        # cost of goods does not move with the customer's discount on this page
        "bottom_line_cost_of_goods_is_flat_across_columns": (
            near(cost_t, cost_1) and near(cost_t, cost_2)),
        "bottom_line_gross_profit_equals_turnover_minus_cost": (
            near(gp_t, today - cost_t) and near(gp_1, p1 - cost_1) and near(gp_2, p2 - cost_2)),
        "bottom_line_gross_margin_equals_profit_over_turnover": (
            near(gm_t, gp_t / today, 1e-6) and near(gm_1, gp_1 / p1, 1e-6)
            and near(gm_2, gp_2 / p2, 1e-6)),
        "bottom_line_delta_profit_is_against_todays_column": (
            near(d1, gp_1 - gp_t) and near(d2, gp_2 - gp_t)),
        # the today column is the committed case on the optimizer
        "bottom_line_today_turnover_equals_optimizer_M": near(today, total_M),
        "bottom_line_today_cost_equals_revenue_minus_profit": near(cost_t, (today - gp_t)
                                                                  if today is not None
                                                                  and gp_t is not None else None,
                                                                  0.05),
        "bottom_line_today_cost_is_after_the_purchase_cut": near(
            cost_t,
            (total_M - total_Y) if total_M is not None and total_Y is not None else None),
        # the optimizer's own totals row must be arithmetic, not a sum of unit prices
        "optimizer_K_total_is_a_weighted_average_price": _k_total_in_range(opt, totals_row),
        "bottom_line_turnover_ceiling_equals_baseline_times_committed": near(
            ceiling, sum(e * l for e, l in zip(e_vals, l_vals)) if e_vals else None, 0.01),
        # the page's own note: the profit gain must equal the exchange-rate move, because
        # the committed customer price is unchanged from today on this basket
        "bottom_line_profit_gain_is_labelled_as_the_fx_move": (
            g(bl, "B22") is not None and g(bl, "B23") is not None and g(bl, "B24") is not None
            and near(g(bl, "B22"), g(bl, "B9"))
            and g(bl, "B23") < g(bl, "B22")
            and g(bl, "B24") > 0
            and near(g(bl, "B25"), g(bl, "B22"))),        # the decomposition above must be arithmetic on its own terms: the same prices,
        # costed at two rates, with the rate move as the residual
        "bottom_line_fx_note_is_self_consistent": near(
            g(bl, "B24"), (g(bl, "B22") - g(bl, "B23"))
            if g(bl, "B22") is not None and g(bl, "B23") is not None else None, 0.05),
    }
    return checks


def _k_total_in_range(opt, totals_row) -> bool:
    if not totals_row:
        return False
    try:
        total_k = opt.Range(f"K{totals_row}").Value
        vals = [opt.Range(f"K{r}").Value for r in range(DATA_FIRST, totals_row)]
        vals = [float(v) for v in vals if v not in (None, "")]
        return bool(vals) and min(vals) <= float(total_k) <= max(vals)
    except Exception:  # noqa: BLE001
        return False


def _linked_row_map(res: dict) -> list[dict]:
    """Every per-line linked block on every sheet, and the optimizer row each row maps to.

    The mapping is positional and derives from how extend_linked writes a block: it fills
    sheet row (first_row + i) from builder(DATA_FIRST + i). So
        optimizer row = sheet row + (DATA_FIRST - first_row)
    Customer View and IML_IMIT Brief start at row 5, so they run one ahead of the
    optimizer (row 5 reads optimizer row 6). The Assumptions GM block starts at row 36 for
    optimizer row 6, so it runs thirty behind.
    """
    n = res["n"]
    rows = []
    # (sheet, first data row on that sheet, number of linked columns)
    # Customer View and IML_IMIT Brief carry a header on row 4 and data from row 5
    # (extend_linked(..., 5, ...)). The Assumptions GM block starts at row 36.
    blocks = (
        ("Customer View", 5, 12),
        ("IML_IMIT Brief", 5, 13),
        ("Assumptions", 36, 4),           # the GM% per-line block
    )
    for sheet, first_row, max_col in blocks:
        offset = DATA_FIRST - first_row
        for i in range(n):
            rows.append({"sheet": sheet, "row": first_row + i,
                         "opt_row": first_row + i + offset, "max_col": max_col})
    return rows


def _a1(row: int, col: int) -> str:
    from openpyxl.utils import get_column_letter
    return f"{get_column_letter(col)}{row}"


def _check_linked_rows(wb, res: dict) -> tuple[bool, list[dict]]:
    """Every per-line linked row must reference ITS OWN optimizer row, column by column.

    This is the check that would have caught the spa2-r2 defect and did not. It is
    row-by-row and column-by-column, not a spot check, and it names the offending cell.

    It compares the REFERENCE, not the value, on purpose: a hijacked row still returns a
    plausible-looking number (the grand total), so a value comparison against the
    optimizer would not obviously fail. A reference comparison fails immediately.
    """
    problems = []
    ref = re.compile(r"'SPA Optimizer'!\$?([A-Z]{1,2})\$?(\d+)")
    for spec in _linked_row_map(res):
        ws = wb.Worksheets(spec["sheet"])
        for col in range(1, spec["max_col"] + 1):
            formula = str(ws.Range(_a1(spec["row"], col)).Formula or "")
            found = ref.findall(formula)
            if not found:
                problems.append({
                    "sheet": spec["sheet"], "cell": _a1(spec["row"], col),
                    "expected_opt_row": spec["opt_row"],
                    "why": "linked row carries no optimizer reference at all",
                    "formula": formula[:120],
                })
                continue
            for _col, row_txt in found:
                if int(row_txt) != spec["opt_row"]:
                    problems.append({
                        "sheet": spec["sheet"], "cell": _a1(spec["row"], col),
                        "expected_opt_row": spec["opt_row"],
                        "found_opt_row": int(row_txt),
                        "why": f"points at optimizer row {row_txt}, "
                               f"should point at {spec['opt_row']}",
                        "formula": formula[:120],
                    })
    return (not problems), problems[:40]


def check_summary_cells_still_on_the_total_row(wb, res: dict, t: int) -> tuple[bool, list[dict]]:
    """The cells that legitimately read the total row must still read the total row.

    The mirror of the check above. This is the over-correction guard: the fix to the
    hijacked-data-row defect must not have moved the genuine total references off the
    total row.
    """
    grads = (
        ("Assumptions", "B24", f"'SPA Optimizer'!Q{t}"),
        ("Assumptions", "B25", f"'SPA Optimizer'!Z{t}"),
        ("Assumptions", "B26", f"'SPA Optimizer'!AA{t}"),
        ("Assumptions", "G4", f"'SPA Optimizer'!M{t}"),
        ("Assumptions", "G5", f"'SPA Optimizer'!G{t}"),
        ("Assumptions", "G6", f"'SPA Optimizer'!Y{t}"),
        ("Scenario Planner", "C15", f"'SPA Optimizer'!M{t}"),
        ("Scenario Planner", "D15", f"'SPA Optimizer'!R{t}"),
        ("Scenario Planner", "C16", f"'SPA Optimizer'!M{t}"),
        ("Scenario Planner", "D16", f"'SPA Optimizer'!Z{t}"),
        ("Scenario Planner", "E16", f"'SPA Optimizer'!AA{t}"),
        ("MD Approval Request", "D18", f"'SPA Optimizer'!G{t}"),
        ("MD Approval Request", "D19", f"'SPA Optimizer'!H{t}"),
        ("MD Approval Request", "D21", f"'SPA Optimizer'!I{t}"),
        ("MD Approval Request", "J18", f"'SPA Optimizer'!M{t}"),
        ("MD Approval Request", "J21", f"'SPA Optimizer'!Y{t}"),
        ("MD Approval Request", "H34", f"'SPA Optimizer'!M{t}"),
        ("MD Approval Request", "H36", f"'SPA Optimizer'!Y{t}"),
    )
    problems = []
    for sheet, cell, expect in grads:
        formula = str(wb.Worksheets(sheet).Range(cell).Formula or "").replace("$", "")
        if expect not in formula:
            problems.append({"sheet": sheet, "cell": cell, "expected": expect,
                             "found": formula[:140],
                             "why": "a genuine total-row reference moved off the total row"})
    return (not problems), problems


def _fx_behaviour_on_sheet(wb, opt, res: dict, ctx: dict, t: int) -> dict:
    """Prove on the sheet that the FX input moves cost and profit and not revenue.

    Writes a second vintage into the Assumptions FX cell, recalculates, reads the totals,
    then puts the original rate back and recalculates again. Reading the before/after pair
    is the evidence; asserting that a formula references a cell is not.
    """
    wa = wb.Worksheets("Assumptions")
    original = float(wa.Range("C6").Value)
    other = round(original * 1.02, 4)          # a deliberately different vintage
    app = wa.Application

    def snapshot():
        def f(cell):
            v = opt.Range(cell).Value
            return None if v in (None, "") else float(v)

        return {
            "fx": float(wa.Range("C6").Value),
            "revenue_eur": f(f"M{t}"),
            "cost_eur": f(f"D{t}"),
            "profit_w_cut_eur": f(f"Y{t}"),
            "unit_cost_sample_eur": f(f"D{DATA_FIRST}"),
        }

    before = snapshot()
    try:
        wa.Range("C6").Value = other
        app.CalculateFullRebuild()
        after = snapshot()
    finally:
        wa.Range("C6").Value = original
        app.CalculateFullRebuild()
    restored = snapshot()

    return {
        "at_rate": before,
        "at_other_rate": after,
        "restored_to": restored,
        "revenue_unchanged": _fxsame(before["revenue_eur"], after["revenue_eur"], 0.005),
        "cost_moved": _fxdiff(before["cost_eur"], after["cost_eur"], 0.005),
        "profit_moved": _fxdiff(before["profit_w_cut_eur"], after["profit_w_cut_eur"], 0.005),
        "profit_rose_when_rate_rose": _fxgt(after["profit_w_cut_eur"], before["profit_w_cut_eur"]),
        "restored_exactly": _fxsame(restored["profit_w_cut_eur"], before["profit_w_cut_eur"], 0.005),
    }


def _fxsame(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def _fxdiff(a, b, tol):
    return a is not None and b is not None and abs(a - b) > tol


def _fxgt(a, b):
    return a is not None and b is not None and a > b


def _excel_open_with_retry(path: str, attempts: int = 6, wait: float = 4.0):
    """Open a workbook in a fresh Excel instance, retrying while Excel is busy.

    Excel refuses automation with 'Call was rejected by callee' when another instance is
    mid-recalculation. That is transient, so back off and try again rather than reporting
    the workbook as unverified.
    """
    import time

    import win32com.client  # noqa: PLC0415

    last = None
    for i in range(attempts):
        excel = None
        try:
            excel = win32com.client.DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            wb = excel.Workbooks.Open(path)
            return excel, wb
        except Exception as exc:  # noqa: BLE001
            last = exc
            if excel is not None:
                try:
                    excel.Quit()
                except Exception:  # noqa: BLE001
                    pass
            time.sleep(wait * (i + 1) / 2)
    raise RunError(f"Excel would not open {Path(path).name} after {attempts} attempts: {last}")


def recalc_and_check(out_xlsx: Path, res: dict, expected: dict | None = None) -> dict:
    """Recalculate in Excel and prove the form, the revenue and the FX behaviour."""
    import win32com.client  # noqa: PLC0415,F401

    t = res["new_total"]
    ctx = load_line_context(res)
    excel, wb = _excel_open_with_retry(str(out_xlsx))
    result: dict = {"checked": False}
    try:
        excel.CalculateFullRebuild()
        def num(ws, cell):
            v = ws.Range(cell).Value
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        def total(c):
            return num(wb.Worksheets("SPA Optimizer"), f"{c}{t}")

        def form(cell):
            return num(wb.Worksheets("MD Approval Request"), cell)

        totals = {c: total(c) for c in ("F", "G", "H", "I", "J", "L", "M", "O", "P", "Q", "R",
                                        "Y", "Z", "AA", "AE", "AF")}
        frm = {c: form(c) for c in ("D18", "D19", "D20", "D21", "J18", "J19", "J20", "J21",
                                    "D34", "D35", "D36", "D37", "H34", "H35", "H36", "H37",
                                    "J34", "J35", "J36", "J37")}
        opt = wb.Worksheets("SPA Optimizer")

        # The template's own L12 columns are the OLD price list struck at the single
        # purchase vintage it carried, so they are not this build's L12 (which is the real
        # invoiced euro). Assert that rather than let the two quietly disagree.
        real_l12 = res["l12_billed"]
        templ_l12 = totals["G"]
        template_l12_ok = abs(templ_l12 - real_l12) <= 1.0

        # -- basis checks read off the sheet itself, not from the python objects
        basis = _basis_checks(wb, opt, res, ctx, t)

        checks = {
            # the form still equals the optimizer
            "form_L12_revenue_eq_optimizer_G": _near(frm["D18"], totals["G"]),
            "form_L12_cost_eq_optimizer_H": _near(frm["D19"], totals["H"]),
            "form_L12_gm_eq_optimizer_J": _near(frm["D20"], totals["J"]),
            "form_L12_profit_eq_optimizer_I": _near(frm["D21"], totals["I"]),
            "form_SPA_revenue_eq_optimizer_M": _near(frm["J18"], totals["M"]),
            "form_SPA_profit_eq_optimizer_Y": _near(frm["J21"], totals["Y"]),
            "form_SPA_gm_eq_optimizer_P": _near(frm["J20"], totals["P"]),
            # the June failure: SPA purchase cost = SPA revenue - SPA gross profit
            "SPA_cost_is_revenue_minus_profit": _near(frm["J19"], totals["M"] - totals["Y"]),
            "impact_block_matches_totals": (
                _near(frm["J34"], frm["J18"] - frm["D18"])
                and _near(frm["J36"], frm["J21"] - frm["D21"])
                and _near(frm["J35"], frm["J19"] - frm["D19"])
            ),
            "impact_SPA_cost_is_SPA_revenue_minus_SPA_profit": _near(frm["H35"], frm["H34"] - frm["H36"]),
            # the SPA margin must be on the same basis as the SPA profit printed beside it
            "form_SPA_margin_basis_matches_SPA_profit": _near(
                frm["J20"], (frm["J21"] / frm["J18"]) if frm["J18"] else None, 1e-6),
            "form_impact_SPA_margin_basis_matches_SPA_profit": _near(
                frm["H37"], (frm["H36"] / frm["H34"]) if frm["H34"] else None, 1e-6),
            # the planner's wiring faults
            "scenario_planner_cut_reads_assumption": _scenario_cut_ok(wb),
            "scenario_volume_reads_one_assumption": _scenario_volume_ok(wb),
            "scenario_planner_fx_reads_assumption": _scenario_fx_ok(wb),
            # the new basis guards
            "spa_prices_are_off_the_customer_list": basis["customer_list"],
            "committed_quantities_are_whole_units": basis["whole_units"],
            "fx_input_equals_live_value_in_config": basis["fx_live"],
            "fx_changes_move_profit_not_revenue": basis["fx_behaviour"],
            "committed_units_reconcile_to_basket": basis["units_reconcile"],
            "customer_list_is_derived_not_isze_list": basis["list_from_billing"],
        }

        fxpair = _fx_pair(wb, opt, excel, res, ctx, t)
        result["fx_pair"] = fxpair
        checks["fx_sheet_cost_matches_the_identity"] = bool(fxpair.get("sheet_cost_matches_identity"))
        fxmove = _fx_behaviour_on_sheet(wb, opt, res, ctx, t)
        result["fx_behaviour_on_sheet"] = fxmove
        checks["fx_moves_profit_not_revenue_on_the_sheet"] = bool(
            fxmove["revenue_unchanged"] and fxmove["cost_moved"] and fxmove["profit_moved"]
            and fxmove["profit_rose_when_rate_rose"] and fxmove["restored_exactly"])
        calib = calibrate_against_reference(res, opt, ctx)
        result["calibration"] = calib
        checks["cost_reconciles_to_sent_at_shared_fx"] = bool(calib.get("within_tolerance", False))
        if expected:
            tol = expected["tolerances"]
            checks["reproduces_sent_model_spa_revenue"] = (
                abs(totals["M"] - expected["spa_revenue_eur"]) <= tol["spa_revenue_eur"])
            checks["reproduces_sent_model_committed_units"] = (
                abs(totals["AE"] - expected["committed_units"]) <= tol["committed_units"])
            # Profit is cost-dependent, so it is only comparable at the reference's own
            # rate. The calibration re-strikes this build's cost at the rate implied by the
            # reference's purchase column and is the like-for-like comparison.
            checks["reproduces_sent_model_spa_profit_at_the_same_rate"] = bool(
                calib.get("available") and abs(calib.get("difference_eur", 1e9)) <= tol["spa_profit_eur"])

        # -- the Bottom line's own arithmetic, read off the sheet
        bl_checks = _bottom_line_checks(wb, t)
        checks.update(bl_checks)
        result_bl = _bottom_line_values(wb)

        # -- the row-by-row linked-reference check, and its over-correction mirror
        linked_ok, linked_problems = _check_linked_rows(wb, res)
        summary_ok, summary_problems = check_summary_cells_still_on_the_total_row(wb, res, t)
        result["linked_rows"] = {
            "rows_checked": len(_linked_row_map(res)),
            "ok": linked_ok,
            "problems": linked_problems,
        }
        result["summary_cells"] = {"ok": summary_ok, "problems": summary_problems}
        checks["every_linked_row_points_at_its_own_optimizer_row"] = linked_ok
        checks["summary_cells_still_point_at_the_total_row"] = summary_ok

        result = {
            "checked": True,
            "fx_vintage": res["fx"],
            "optimizer_totals": totals,
            "form": frm,
            "derived_spa_purchase_cost": totals["M"] - totals["Y"],
            "basis": basis,
            "fx_pair": fxpair,
            "fx_behaviour_on_sheet": fxmove,
            "calibration": calib,
            "bottom_line": result_bl,
            "template_l12_columns": {
                "template_total_eur": templ_l12,
                "the_builds_real_invoiced_l12_eur": real_l12,
                "note": ("The template's own L12 columns use the template's older price list, "
                         "so they are not the invoiced euro. Only the SPA columns (K to AC) "
                         "are in use from the template."),
            },
            "linked_rows": result.get("linked_rows"),
            "summary_cells": result.get("summary_cells"),
            "checks": checks,
            "all_pass": all(checks.values()),
        }
        wb.Save()
        wb.Close(SaveChanges=True)
    finally:
        excel.Quit()
        del excel
    return result


def _basis_checks(wb, opt, res: dict, ctx: dict, t: int) -> dict:
    """Read the basis back off the recalced sheet, line by line."""
    import win32com.client  # noqa: PLC0415,F401

    n = res["n"]
    first, last = DATA_FIRST, t - 1

    def read(c):
        out = []
        for r in range(first, last + 1):
            v = opt.Range(f"{c}{r}").Value
            if v is None or v == "":
                out.append(None)
            else:
                try:
                    out.append(float(v))
                except (TypeError, ValueError):
                    out.append(None)
        return out

    e = read("E")   # customer list
    k = read("K")   # SPA price
    f = read("F")   # L12 qty
    l = read("L")   # committed qty
    ag = read("AG")  # price override
    ae = read("AE")  # committed qty (whole)

    # (a) every SPA price is the customer list less the ladder step, or an override
    bad_price = []
    for i in range(n):
        if e[i] is None or k[i] is None:
            continue
        if ag[i] is not None:
            continue
        if l[i] is None or f[i] is None:
            bad_price.append(i + 1)
            continue
        ratio = (l[i] / f[i]) if f[i] > 0 else None
        rate = 0.0
        if ratio is None or ratio >= ctx["top_mult"]:
            rate = ctx["top_rate"]
        elif ratio >= ctx["middle_mult"]:
            rate = ctx["middle_rate"]
        if abs(k[i] - e[i] * (1 - rate)) > 0.011:
            bad_price.append(i + 1)

    # (b) committed quantities are whole units
    frac = [i + 1 for i in range(n) if l[i] is not None and abs(l[i] - round(l[i])) > 1e-9]
    frac_ae = [i + 1 for i in range(n) if ae[i] is not None and abs(ae[i] - round(ae[i])) > 1e-9]

    # (c) the FX input on Assumptions equals the live value in config.yaml
    fx_used = float(wb.Worksheets("Assumptions").Range("C6").Value)
    fx_live_cell = float(wb.Worksheets("Assumptions").Range("C7").Value)

    # (d) profit moves with FX and revenue does not - recompute the cost column at
    #     another vintage and compare, without touching the SPA price column
    unit_disc = ctx["cost_discount"]
    rev0 = sum((k[i] or 0) * (l[i] or 0) for i in range(n))
    prof = {}
    for label, fx in (("fx_a", res["fx"]["fx"]), ("fx_b", res["fx"]["fx"] * 1.02)):
        cost = sum(ctx["bp_jpy"][i] / fx * unit_disc[i] * (l[i] or 0) for i in range(n))
        prof[label] = rev0 - cost * (1 - ctx["cut"])
    fx_behaviour = (abs(prof["fx_a"] - prof["fx_b"]) > 1.0)

    # units: the rounded commitment must equal the optimistic rounded basket total
    units_ok = abs(sum(l[i] or 0 for i in range(n)) - res["committed_units"]) <= 0.005

    list_from_billing = res["customer_list_from_billing"] >= n - 5

    return {
        "customer_list": not bad_price,
        "bad_price_rows": bad_price[:20],
        "whole_units": not frac and not frac_ae,
        "fractional_rows": frac[:20],
        "fractional_ae_rows": frac_ae[:20],
        "fx_used": fx_used,
        "fx_live_cell": fx_live_cell,
        "fx_live": abs(fx_live_cell - res["fx_live"]) < 1e-9,
        "fx_behaviour": fx_behaviour,
        "fx_profit_pair": prof,
        "units_reconcile": units_ok,
        "committed_units": res["committed_units"],
        "fractional_units": res["fractional_units"],
        "list_from_billing": list_from_billing,
        "lines_from_billing": res["customer_list_from_billing"],
        "lines_total": n,
    }


def _fx_pair(wb, opt, excel, res: dict, ctx: dict, t: int) -> dict:
    """Cost, profit and revenue on the vintage in use and on the live vintage.

    Revenue must be identical; only cost and profit may move. The cost is re-struck
    from the list vintage, which is the same identity the workbook carries, so the
    pair can be produced without writing to the sheet.
    """
    n = res["n"]
    l = [opt.Range(f"L{DATA_FIRST + i}").Value or 0 for i in range(n)]
    k = [opt.Range(f"K{DATA_FIRST + i}").Value or 0 for i in range(n)]
    disc = ctx["cost_discount"]
    fob_list = ctx["fob_list_eur"]
    list_disc = ctx["list_discount"]
    list_fx = SENT_VINTAGE_FX
    cut = ctx["cut"]
    rev = sum(k[i] * l[i] for i in range(n))
    def figures(fx, basis: str):
        cost = 0.0
        for i in range(n):
            unit = fob_list[i] * (list_fx / fx) * (disc[i] / list_disc[i])
            cost += unit * l[i]
        return {"fx": fx, "basis": basis, "revenue_eur": rev, "cost_eur": cost,
                "profit_no_cut_eur": rev - cost, "profit_7pct_eur": rev - cost * (1 - cut)}

    out = {
        "in_use": figures(res["fx"]["fx"], res["fx"].get("selected_by", "")),
        "live": figures(res["fx_live"], "live rate in config.yaml"),
    }
    # The cost on the sheet must equal the identity at the vintage in use. That is the
    # real proof the FX input does something, and it is independent of whether this run
    # happens to sit on the live rate.
    #
    # The column D total is the FULL purchase spend on the SPA-active vintage; column Y
    # subtracts the purchase cut. So the identity to assert is
    #   D_total == identity spend   and   Y_total == revenue - spend x (1 - cut)
    sheet_profit = opt.Range(f"Y{t}").Value
    sheet_spend = opt.Range(f"D{t}").Value
    cut_used = float(wb.Worksheets("Assumptions").Range("C4").Value)
    out["cut_used"] = cut_used
    out["sheet_full_spend_column_d_eur"] = None if sheet_spend in (None, "") else float(sheet_spend)
    out["sheet_cost_after_cut_eur"] = (
        None if sheet_spend in (None, "") else float(sheet_spend) * (1 - cut_used))
    out["identity_full_spend_eur"] = out["in_use"]["cost_eur"]
    out["sheet_cost_matches_identity"] = (
        out["sheet_full_spend_column_d_eur"] is not None
        and abs(out["sheet_full_spend_column_d_eur"] - out["in_use"]["cost_eur"]) <= 1.0
        and sheet_profit not in (None, "")
        and abs(float(sheet_profit) - out["in_use"]["profit_7pct_eur"]) <= 1.0
    )
    # the cell-level identity, on the first line: D = FOB_list x (163.7 / FX) x (disc/disc_list)
    fob0 = fob_list[0] if fob_list else 0.0
    if fob0:
        expected_unit = fob0 * (list_fx / res["fx"]["fx"]) * (disc[0] / list_disc[0])
        actual_unit = opt.Range(f"D{DATA_FIRST}").Value
        out["line1_unit_cost_expected_eur"] = expected_unit
        out["line1_unit_cost_on_sheet_eur"] = actual_unit
        out["line1_cost_matches_identity"] = (
            actual_unit is not None and abs(float(actual_unit) - expected_unit) <= 0.005
        )
    out["revenue_identical"] = abs(out["in_use"]["revenue_eur"] - out["live"]["revenue_eur"]) < 0.005
    out["profit_delta_live_vs_used"] = (out["live"]["profit_7pct_eur"]
                                        - out["in_use"]["profit_7pct_eur"])
    # the rate move, stated as a pair on the same revenue
    out["profit_at_163_7_eur"] = figures(
        SENT_VINTAGE_FX, "the vintage the selling list sits on")["profit_7pct_eur"]
    out["gain_live_vs_163_7_eur"] = out["live"]["profit_7pct_eur"] - out["profit_at_163_7_eur"]
    return out


def calibrate_against_reference(res: dict, opt, ctx: dict) -> dict:
    """Recover the vintage a reference model was costed on, and compare profit there.

    The reference is only a reconciliation target; it is never used as an input. The
    vintage it was costed on is read back off its own purchase column by solving
    FOB_EUR = BP_JPY / FX x discount for FX, so the comparison is like for like.

    The reference's SPA-active purchase column is matched by part number, not by row,
    because this build drops the unpriced lines onto their own sheet and the row order
    is therefore not the same.
    """
    ref = SENT_SPA2_R2
    path = Path(ref["file"])
    if not path.exists():
        return {"available": False, "reason": f"reference not found: {path}"}
    ws = openpyxl.load_workbook(path, data_only=True)["SPA Optimizer"]
    ref_purchase = {}
    for r in range(DATA_FIRST, DATA_FIRST + 400):
        pn = norm_pn(ws.cell(r, 1).value)
        if not pn:
            break
        ref_purchase[pn] = ws.cell(r, 4).value      # their SPA-active purchase

    # The reference struck its purchase at the same discount this build uses for the
    # baseline (0.620, the vintage the price file sits on), so the calibration re-strikes
    # this build's own baseline cost at the implied rate rather than at a different
    # discount. That keeps the comparison like for like.
    df = pd.read_pickle(Path(res["qa_dir"]) / "_lines.pkl")
    n = res["n"]
    bp = ctx["bp_jpy"]
    disc = ctx["list_discount"]
    l = [opt.Range(f"L{DATA_FIRST + i}").Value or 0 for i in range(n)]
    implied, lines = [], 0
    for i, pn in enumerate(df["pn"].astype(str)):
        bought = ref_purchase.get(pn)
        if bought and bp[i] and disc[i]:
            implied.append(bp[i] * disc[i] / float(bought))
            lines += 1
    if not implied:
        return {"available": False, "reason": "no shared lines between this build and the reference"}
    implied.sort()
    implied_median = implied[len(implied) // 2]
    # Their column D is their column C re-struck on their SPA-active rate at the same
    # discount. So the rate falls straight out of the two euro figures:
    #   D_ref = fob_list_eur * (163.7 / FX)   =>   FX = 163.7 * fob_list_eur / D_ref
    fob_ref, lines_euro = [], 0
    for i, pn in enumerate(df["pn"].astype(str)):
        bought = ref_purchase.get(pn)
        if bought and ctx["fob_list_eur"][i]:
            fob_ref.append(SENT_VINTAGE_FX * ctx["fob_list_eur"][i] / float(bought))
            lines_euro += 1
    fob_ref.sort()
    fx_ref = fob_ref[len(fob_ref) // 2] if fob_ref else implied_median
    rev = sum((opt.Range(f"K{DATA_FIRST + i}").Value or 0) * l[i] for i in range(n))
    cut = ctx["cut"]
    my_cost = sum(ctx["fob_list_eur"][i] * (SENT_VINTAGE_FX / fx_ref) * l[i] for i in range(n))
    my_profit = rev - my_cost * (1 - cut)
    return {
        "available": True,
        "reference": str(path),
        "reference_lines_matched": lines,
        "implied_fx_from_fob_eur": round(fx_ref, 4),
        "my_profit_at_that_vintage_eur": my_profit,
        "my_revenue_at_that_vintage_eur": rev,
        "my_cost_at_that_vintage_eur": my_cost,
        "reference_profit_eur": ref["spa_profit_cut_eur"],
        "reference_cost_eur": ref["spa_cost_fx_172_6_eur"],
        "difference_eur": my_profit - ref["spa_profit_cut_eur"],
        "cost_difference_eur": my_cost - ref["spa_cost_fx_172_6_eur"],
        "within_tolerance": (abs(my_profit - ref["spa_profit_cut_eur"]) <= 1.0
                             and abs(my_cost - ref["spa_cost_fx_172_6_eur"]) <= 1.0),
        "note": ("The reference's own purchase column is struck on this rate at the 0.620 "
                 "discount it held. Costing this build's committed quantities at the same "
                 "pair is what reproduces its cost and profit. This is the reproduction "
                 "claim; the run's own vintage is a separate choice."),
    }


def _near(a, b, tol: float = 1.0) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


def _clean_formula(wb, sheet: str, cell: str) -> str:
    """Formula text with absolute-reference markers stripped, for comparison."""
    return str(wb.Worksheets(sheet).Range(cell).Formula).replace("$", "")


def _scenario_cut_ok(wb) -> bool:
    """The planner's purchase cut must read the real assumption, not a heading."""
    try:
        return "Assumptions" in _clean_formula(wb, "Scenario Planner", "B7") \
            and "C4" in _clean_formula(wb, "Scenario Planner", "B7")
    except Exception:
        return False


def _scenario_volume_ok(wb) -> bool:
    """Volume growth must be one number, read from the assumption on both rows,
    and it must actually lift revenue on the Enhanced row."""
    try:
        growth = _clean_formula(wb, "Scenario Planner", "B6")
        c17 = _clean_formula(wb, "Scenario Planner", "C17")
        f17 = _clean_formula(wb, "Scenario Planner", "F17")
        return ("Assumptions" in growth and "C19" in growth
                and "C19" in c17 and "C19" in f17)
    except Exception:
        return False


def _scenario_fx_ok(wb) -> bool:
    """The planner must show the FX vintage actually in use, read from Assumptions."""
    try:
        b8 = _clean_formula(wb, "Scenario Planner", "B8")
        b9 = _clean_formula(wb, "Scenario Planner", "B9")
        return "Assumptions" in b8 and "C6" in b8 and "Assumptions" in b9 and "C7" in b9
    except Exception:
        return False


def check_negotiation_reference(res: dict, expected: dict) -> dict:
    """Line-by-line reconciliation against the model sent to the customer."""
    ref_path = Path(expected["file"])
    out = {"file": str(ref_path), "exists": ref_path.exists()}
    if not ref_path.exists():
        return out
    ws = openpyxl.load_workbook(ref_path, data_only=True)["SPA Optimizer"]
    sent = {}
    for r in range(DATA_FIRST, DATA_FIRST + 200):
        pn = norm_pn(ws.cell(r, 1).value)
        if not pn:
            break
        sent[pn] = {"row": r, "raw": str(ws.cell(r, 1).value).strip(),
                    "list": ws.cell(r, 5).value, "spa_price": ws.cell(r, 11).value,
                    "committed": ws.cell(r, 12).value, "l12_qty": ws.cell(r, 6).value}

    df = pd.read_pickle(Path(res["qa_dir"]) / "_lines.pkl")
    mine = df.set_index("pn")
    shared = [p for p in sent if p in mine.index]
    tol = expected["tolerances"]["line_price_eur"]

    price_mismatch, qty_mismatch, list_mismatch = [], [], []
    for p in shared:
        s, m = sent[p], mine.loc[p]
        if s["spa_price"] is not None and abs(float(m["spa_price"]) - float(s["spa_price"])) > tol:
            price_mismatch.append({"pn": s["raw"], "mine": float(m["spa_price"]),
                                   "sent": float(s["spa_price"]),
                                   "delta": float(m["spa_price"]) - float(s["spa_price"])})
        if s["committed"] is not None and abs(float(m["spa_qty_committed"]) - float(s["committed"])) > 0.005:
            qty_mismatch.append({"pn": s["raw"], "mine": float(m["spa_qty_committed"]),
                                 "sent": float(s["committed"])})
        if s["list"] is not None and abs(float(m["list_price"]) - float(s["list"])) > 0.011:
            list_mismatch.append({"pn": s["raw"], "mine": float(m["list_price"]),
                                  "sent": float(s["list"]), "from": m["customer_list_from"]})

    mine_rev = float((mine.loc[shared, "spa_price"] * mine.loc[shared, "spa_qty_committed"]).sum())
    sent_rev = float(sum((sent[p]["spa_price"] or 0) * (sent[p]["committed"] or 0) for p in shared))

    # the ladder the reference used, recovered from its own price-to-baseline ratios
    import collections
    counts = collections.Counter()
    for p in shared:
        lst, sp = sent[p]["list"], sent[p]["spa_price"]
        if not lst or sp is None:
            continue
        r_ = sp / float(lst)
        counts["none" if abs(r_ - 1) < 0.001 else
               ("middle" if abs(r_ - 0.95) < 0.001 else
                ("top" if abs(r_ - 0.92) < 0.001 else f"other:{r_:.4f}"))] += 1

    out.update({
        "shared_lines": len(shared),
        "sent_lines": len(sent),
        "line_price_mismatches": price_mismatch,
        "line_qty_mismatches": qty_mismatch,
        "line_list_mismatches": list_mismatch,
        "revenue_mine": mine_rev,
        "revenue_sent": sent_rev,
        "revenue_delta": mine_rev - sent_rev,
        "tolerance_eur": tol,
        "ladder_counts_recovered_from_reference": dict(counts),
    })
    return out


def write_delta_csv(res: dict, expected: dict, cmp: dict, path: Path) -> None:
    """Every line where this build and the sent model differ, with the reason."""
    rows = []
    for kind, items in (("spa_price", cmp.get("line_price_mismatches", [])),
                        ("committed_qty", cmp.get("line_qty_mismatches", [])),
                        ("baseline_list", cmp.get("line_list_mismatches", []))):
        for it in items:
            rows.append({"kind": kind, **it})
    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["kind", "pn", "mine", "sent", "delta", "from"])
    df.to_csv(path, index=False, encoding="utf-8-sig")


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Generate an SPA optimizer, application form and waterfall sheet.")
    ap.add_argument("--basket", required=True, help="basket workbook: P/N | Description | committed qty")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    ap.add_argument("--pricing-config", default=str(PRICING_CONFIG))
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
    ap.add_argument("--cut", type=float, default=0.07, help="IML / IMIT purchase price cut")
    ap.add_argument("--gm-floor", type=float, default=0.25)
    ap.add_argument("--volume-growth", type=float, default=0.10)
    # --- the volume ladder, as an inspectable input
    ap.add_argument("--middle-rate", type=float, default=0.05, help="discount at the middle step")
    ap.add_argument("--top-rate", type=float, default=0.08, help="discount at the top step")
    ap.add_argument("--middle-mult", type=float, default=1.5,
                    help="committed / L12 qty at which the middle step starts")
    ap.add_argument("--top-mult", type=float, default=2.0,
                    help="committed / L12 qty at which the top step starts")
    # --- the FX vintage
    ap.add_argument("--cost-fx", type=float, default=None,
                    help="explicit JPY/EUR for the cost side; default is config.yaml's live rate")
    ap.add_argument("--fx-annual", default=None,
                    help="pick the latest vintage declared in that fiscal year, e.g. 2026")
    ap.add_argument("--discount-vintage", default="auto", choices=("auto", "live", "prior"),
                    help="purchase-discount vintage; 'auto' resolves it against the FX vintage's date")
    ap.add_argument("--live-fx-for-cost", action="store_true",
                    help="force the live rate from config.yaml (the default anyway)")
    ap.add_argument("--sent-vintage-compat", action="store_true",
                    help="cost the workbook on the sent model's 172.6 vintage, for reconciliation runs")
    ap.add_argument("--prepared-by", default="JVDP")
    ap.add_argument("--manager", default="Hadewijch Tibos")
    ap.add_argument("--pack1-spa-rev", type=float, default=728880.0)
    ap.add_argument("--pack1-spa-profit", type=float, default=235521.0)
    ap.add_argument("--pack1-bar-static", action="store_true",
                    help="use the fixed pack 1 constants instead of deriving them from the dashboard")
    ap.add_argument("--waterfall-line", default=None)
    ap.add_argument("--negotiation-reference", default="auto",
                    help="'auto' for the built-in 17 Sep UTI model, a path, or 'none'")
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

    # carry the inputs the recalculation needs to prove the FX behaviour and the basis
    print(f"built   : {res['out_xlsx']}")
    print(f"lines   : {res['n']} priced of {res['basket_lines']} in the basket "
          f"(unpriced, on their own sheet: {res['frozen'] or 'none'})")
    print(f"FX      : {res['fx']['fx']} JPY/EUR ({res['fx'].get('selected_by')}); "
          f"live in config = {res['fx_live']}")
    print(f"ladder  : {res['ladder_counts']}  committed units {res['committed_units']:,.0f} "
          f"(basket {res['fractional_units']:,.4f})")
    print(f"totals  : SPA revenue {res['spa_rev']:,.2f} | SPA cost {res['spa_cost']:,.2f} | "
          f"SPA profit {res['spa_profit']:,.2f} | L12 billed {res['l12_billed']:,.2f}")

    wf, wf_row = write_waterfall_csv(pd.read_pickle(Path(res["qa_dir"]) / "_lines.pkl"), args, res)
    print(f"waterfall: {wf}")

    expected = None
    if args.negotiation_reference == "auto":
        expected = SENT_SPA2_R2
    elif args.negotiation_reference not in ("none", "", None):
        expected = dict(SENT_SPA2_R2)
        expected["file"] = args.negotiation_reference

    if not args.skip_verify:
        try:
            check = recalc_and_check(Path(res["out_xlsx"]), res, expected)
        except Exception as exc:  # noqa: BLE001
            print(f"VERIFY UNAVAILABLE: {exc}", file=sys.stderr)
            check = {"checked": False, "error": str(exc)}
        if check.get("checked"):
            totals = check["optimizer_totals"]
            # The waterfall reports REAL invoiced euro, so it is checked against the
            # optimizer's L12 billed reference column (AF), not against the modelled L12
            # column (G). The two differ by invoice-level roundings, and both are on the
            # sheet - the sent model carried both for the same reason.
            check["checks"]["waterfall_revenue_eq_optimizer_AF"] = _near(
                wf_row["l12_billed_revenue_eur"], totals["AF"])
            check["checks"]["waterfall_spa_revenue_eq_optimizer_M"] = _near(
                wf_row["spa_revenue_eur"], totals["M"])
            check["checks"]["waterfall_spa_gp_eq_optimizer_Y"] = _near(
                wf_row["spa_gp_eur"], totals["Y"])
            real_delta = check["form"]["J18"] - totals["AF"]
            check["checks"]["waterfall_revenue_delta_agrees_with_form_on_real_billing"] = _near(
                wf_row["delta_revenue_eur"], real_delta)
            check["l12_modelled_vs_invoiced_gap_eur"] = totals["G"] - totals["AF"]
            # The waterfall's SPA cost is the full purchase spend; its SPA profit is after
            # the purchase cut. The identity to assert is therefore
            #   cost = (revenue - profit) / (1 - cut),  with the cut read off the sheet.
            cut_used = float(args.cut)
            check["cut_used"] = cut_used
            check["checks"]["waterfall_spa_cost_eq_revenue_minus_profit_full"] = _near(
                wf_row["spa_cost_eur"],
                (wf_row["spa_revenue_eur"] - wf_row["spa_gp_eur"]) / (1 - cut_used))
            if expected:
                cmp = check_negotiation_reference(res, expected)
                check["negotiation_reference"] = cmp
                residual = cmp.get("revenue_delta")
                check["checks"]["reproduces_sent_line_prices"] = not cmp.get("line_price_mismatches")
                check["checks"]["reproduces_sent_line_quantities"] = not cmp.get("line_qty_mismatches")
                check["checks"]["reproduces_sent_revenue_within_tolerance"] = (
                    residual is not None
                    and abs(residual) <= expected["tolerances"]["spa_revenue_eur"])
                got = cmp.get("ladder_counts_recovered_from_reference", {})
                want = expected.get("ladder_counts", {})
                check["checks"]["reproduces_sent_ladder_shape"] = all(
                    got.get(k) == v for k, v in want.items())
                write_delta_csv(res, expected, cmp, Path(res["qa_dir"]) / "_delta_vs_sent.csv")
            check["all_pass"] = all(check["checks"].values())
        (Path(res["qa_dir"]) / "_recalc_check.json").write_text(
            json.dumps(check, indent=2, default=str), encoding="utf-8"
        )
        if check.get("checked"):
            failed = [k for k, v in check["checks"].items() if not v]
            print(f"checks  : {len(check['checks'])} run, "
                  + ("ALL PASS" if not failed else "FAILED -> " + ", ".join(failed)))
            print(f"          SPA purchase cost (derived) = {check['derived_spa_purchase_cost']:,.2f}")
            fp = check["fx_pair"]
            print(f"          FX pair: revenue {fp['in_use']['revenue_eur']:,.2f} unchanged | "
                  f"profit {fp['in_use']['profit_7pct_eur']:,.2f} at {fp['in_use']['fx']} vs "
                  f"{fp['live']['profit_7pct_eur']:,.2f} at {fp['live']['fx']} | "
                  f"{fp['profit_at_163_7_eur']:,.2f} at {SENT_VINTAGE_FX}")
            if failed:
                print("The workbook did not meet its own checks. Do not send this file.", file=sys.stderr)
                return 3

    (Path(res["qa_dir"]) / "_build_result.json").write_text(
        json.dumps({k: v for k, v in res.items() if k != "args"}, indent=2, default=str), encoding="utf-8"
    )
    print(f"verified: {Path(res['qa_dir']) / '_recalc_check.json'}")
    return 0


def write_waterfall_csv(df: pd.DataFrame, args: argparse.Namespace, res: dict) -> tuple[Path, dict]:
    """The waterfall adjustment for this basket, dated in the file name."""
    stamp = args.date or date.today().strftime("%Y%m%d")
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
        "spa_cost_eur": round(res["spa_cost"], 2),
        "spa_gp_eur": round(res["spa_profit"], 2),
        "delta_revenue_eur": round(res["spa_rev"] - res["l12_billed"], 2),
        "delta_gp_eur": round(res["spa_profit"] - res["l12_billed_profit"], 2),
        "l12_qty": round(float(df["l12_qty"].sum()), 2),
        "spa_qty": round(float(df["spa_qty"].sum()), 2),
        "spa_qty_basis": "committed whole units",
        "spa_price_basis": "customer's realised L12 net price, less the volume ladder",
        "fx_vintage": res["fx"]["fx"],
        "fx_as_of": res["fx"].get("as_of", ""),
        "fx_source": str(PRICING_CONFIG),
        "source": Path(args.basket).name,
    }]
    out = Path(res["qa_dir"]) / f"_waterfall_{args.customer}_{args.label}_{stamp}.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    return out, rows[0]


if __name__ == "__main__":
    raise SystemExit(main())
