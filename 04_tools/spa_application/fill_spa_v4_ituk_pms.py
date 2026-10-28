r"""ITUK 2026 SPA (PMS basket) filled into the official ISZE_SPA_Optimizer_V4.xlsx template.

Internal only. Built 2026-10-26 for Jerome, for approval by Yoshimoto san.

Jerome needs the approval on the standard file, so this keeps the template's tabs, layout,
colours and formulas, and only:
  * writes ITUK's lines into the SPA Optimizer input columns (A-G, J, K), sized to the basket;
  * extends every per-line block that links to it (GM floor check, Customer View, IML brief)
    and moves every total/range reference from the template's 53 lines to this basket;
  * fills the context cells (customer, market, ref, dates, sold-to, approvers);
  * corrects the template's reference errors listed in TEMPLATE_FIXES below - each one would
    print a wrong figure on the approval form;
  * adds one sheet at the end, 'Profit Bridge' (the waterfall chart Jerome asked for).

The data basis is the same as build_spa_ituk_pms.py (L12 = SAP billing to sold-to 2575,
Sep 2025 - Aug 2026; cost = price-file FOB on the live FX and Japan discount; SPA price =
ITUK's proposal rounded to the cent). Lines with no purchase price stay out of the optimizer
and are listed on the Customer View and the approval form.

USAGE
-----
  python 04_tools/spa_application/fill_spa_v4_ituk_pms.py --basket <ITUK file.xlsx>
"""
from __future__ import annotations

import argparse
import re
import sys
from copy import copy
from datetime import date, datetime
from pathlib import Path

import openpyxl
import yaml
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.text import RichText
from openpyxl.drawing.text import CharacterProperties, Paragraph, ParagraphProperties
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.cell_range import CellRange

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared.paths import ISZE_ROOT  # noqa: E402
from build_spa_ituk_pms import PRICING_CONFIG, read_basket, read_cost, read_l12  # noqa: E402

TEMPLATE = ISZE_ROOT / "01_data" / "01_Pricing" / "ISZE_SPA_Optimizer_V4.xlsx"
FX_FILE, DISC_FILE_J = 163.7, 0.620

# template geometry
T_FIRST, T_LAST, T_TOTAL = 6, 58, 60          # SPA Optimizer
T_LINES = T_LAST - T_FIRST + 1                 # 53
GM_FIRST = 36                                  # Assumptions GM floor block, rows 36..88
CV_FIRST, CV_TOTAL = 5, 58                     # Customer View and IML brief

TEMPLATE_FIXES = [
    "MD Approval Request H35: SPA purchase cost read L12 revenue minus SPA profit (=D34-H36); now SPA revenue minus SPA profit (=H34-H36).",
    "MD Approval Request B26: the justification read the retention score from an empty cell (Assumptions!B20); the text is rewritten for this SPA.",
    "Scenario Planner B7: IML cut read a header (Assumptions!B3); now Assumptions!C4. B8: GBP rate read the volume growth cell; now Assumptions!B16.",
    "Scenario Planner C15/F15: growth read the health-check header (Assumptions!B21); now Assumptions!B19.",
    "Scenario Planner D12: 'profit vs L12' for the partial scenario summed revenue deltas (col P); now profit deltas (col Q).",
    "Scenario Planner B12-B15: line counts were typed text ('2 of 53'); now counted live.",
    "Assumptions health check and verdict: thresholds were fixed line counts for a 12-line basket (>=6, >=10 'of 12'); now the same shares of this basket (50%, 83%).",
    "IML_IMIT Brief: a stray merge A27:M27 sat across a data row; removed.",
]


def norm_rng_end(s: str, new_last: int, new_total: int) -> str:
    """Move template references to the template total row and data range end."""
    if not isinstance(s, str) or not s.startswith("="):
        return s
    s = re.sub(r"('SPA Optimizer'!\$?[A-Z]{1,2}\$?)" + str(T_TOTAL) + r"(?!\d)", r"\g<1>" + str(new_total), s)
    s = re.sub(r"((?:'SPA Optimizer'!)?\$?[A-Z]{1,2}\$?[46]:\$?[A-Z]{1,2}\$?)" + str(T_LAST) + r"(?!\d)",
               r"\g<1>" + str(new_last), s)
    return s


def style_from(src, dst):
    dst.font, dst.fill, dst.border = copy(src.font), copy(src.fill), copy(src.border)
    dst.number_format, dst.alignment, dst.protection = src.number_format, copy(src.alignment), copy(src.protection)


def move_block(ws, rows: range, offset: int, max_col: int):
    """Move a block of rows (values, styles, row heights, merges) down by offset."""
    merges = [m for m in list(ws.merged_cells.ranges) if m.min_row >= rows.start and m.max_row < rows.stop]
    for m in merges:
        ws.unmerge_cells(str(m))
    for r in reversed(rows):
        for c in range(1, max_col + 1):
            src, dst = ws.cell(r, c), ws.cell(r + offset, c)
            dst.value = src.value
            style_from(src, dst)
            src.value = None
            src.style = "Normal"
        if r in ws.row_dimensions and ws.row_dimensions[r].height:
            ws.row_dimensions[r + offset].height = ws.row_dimensions[r].height
            ws.row_dimensions[r].height = None
    for m in merges:
        ws.merge_cells(start_row=m.min_row + offset, start_column=m.min_col,
                       end_row=m.max_row + offset, end_column=m.max_col)


def clear_rows(ws, first: int, last: int, max_col: int):
    """Blank template rows a smaller basket no longer uses (values and styles)."""
    for r in range(first, last + 1):
        for c in range(1, max_col + 1):
            ws.cell(r, c).value = None
            ws.cell(r, c).style = "Normal"


def extend_cf(ws, new_last: int, old_last: int, first_rows=(T_FIRST, GM_FIRST)):
    """Stretch conditional formatting ranges that end on the template's last data row."""
    cf = ws.conditional_formatting
    new_rules = []
    for rng, rules in list(cf._cf_rules.items()):
        parts = []
        for cr in str(rng.sqref).split():
            c = CellRange(cr)
            if c.max_row in (old_last, 47):          # 47 = template GM block was only partly covered
                c = CellRange(min_col=c.min_col, min_row=c.min_row, max_col=c.max_col, max_row=new_last)
            parts.append(c.coord)
        new_rules.append((" ".join(parts), rules))
    cf._cf_rules.clear()
    for sq, rules in new_rules:
        for r in rules:
            cf.add(sq, r)


PMS_SCOPE = {  # PMS campaign scope agreed with ITUK / ISZJ on 18 Aug 2026 -> family
    "oil_filter": "Filters", "fuel_filter": "Filters", "air_filter": "Filters", "blower_filter": "Filters",
    "urea_filter": "Filters", "brake_pad": "Brakes", "brake_rotor": "Brakes", "clutch_kit": "Clutch",
    "clutch_disc": "Clutch", "clutch_pressure_plate": "Clutch", "release_bearing": "Clutch",
}


def pms_category(df):
    """PMS category per line: parts catalogue, then BVP dimension; an untagged caliper pad kit is a brake pad.
    King pins, shock absorbers, water pump and bushings carry catalogue tags but are outside the PMS scope."""
    import pandas as pd
    from build_spa_ituk_pms import DERIVED, norm_pn
    pc = pd.read_parquet(DERIVED / "parts_catalog_dimension.parquet", columns=["part_number", "pms_category"])
    bv = pd.read_parquet(DERIVED / "bvp_pn_dimension.parquet", columns=["part_number", "pms_category"])
    for d in (pc, bv):
        d["pn"] = d["part_number"].map(norm_pn)
    cat = df["pn"].map(pc.dropna().drop_duplicates("pn").set_index("pn")["pms_category"])
    cat = cat.fillna(df["pn"].map(bv.dropna().drop_duplicates("pn").set_index("pn")["pms_category"]))
    cat = cat.where(cat.notna() | ~df["desc"].str.contains("PAD KIT; CALIPER", regex=False), "brake_pad")
    return cat.where(cat.isin(PMS_SCOPE.keys()))


def build(args) -> Path:
    cfg = yaml.safe_load(PRICING_CONFIG.read_text(encoding="utf-8"))["formula"]
    fx_live = float(cfg["fx_rate"])
    disc_j = float(cfg["source_discount"]["J"])

    df = read_l12(read_cost(read_basket(Path(args.basket))))
    n_basket = len(df)
    if args.pms_only:
        df = df[pms_category(df).notna()].reset_index(drop=True)
    costed = df[df["fob_file"].notna()].reset_index(drop=True)
    pending = df[df["fob_file"].isna()].reset_index(drop=True)
    factor = costed["source"].map(lambda s: (FX_FILE / fx_live) * (disc_j / DISC_FILE_J) if s == "J" else FX_FILE / fx_live)
    costed["purchase"] = (costed["fob_file"] * factor).round(2)
    n = len(costed)
    last, total = T_FIRST + n - 1, T_FIRST + n + 1
    shift = total - T_TOTAL

    wb = openpyxl.load_workbook(TEMPLATE)

    # ---------- 1. every template formula onto the new size (before any new row is written)
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    c.value = norm_rng_end(c.value, last, total)

    # ---------- 2. SPA Optimizer
    wo = wb["SPA Optimizer"]
    style_row = {c: copy(wo.cell(T_FIRST, c)._style) for c in range(1, 29)}
    tpl_formula = {c: wo.cell(T_FIRST, c).value for c in range(1, 29)}
    if n < T_LINES:
        clear_rows(wo, T_FIRST + n, T_LAST, 28)
    move_block(wo, range(T_TOTAL - 1, 67), shift, 28)          # blank, total, notes
    for i, rec in costed.iterrows():
        r = T_FIRST + i
        inputs = {1: rec.pn, 2: rec.desc, 3: float(rec.purchase), 4: float(rec.list_eur),
                  5: float(rec.l12_qty), 6: round(float(rec.l12_rev), 2),
                  7: round(float(rec.l12_qty) * float(rec.purchase), 2),
                  10: float(rec.spa_price), 11: float(rec.spa_qty)}
        for c in range(1, 29):
            cell = wo.cell(r, c)
            cell._style = copy(style_row[c])
            if c in inputs:
                cell.value = inputs[c]
            else:
                cell.value = re.sub(r"(?<=[A-Z])6(?!\d)", str(r), tpl_formula[c]) if isinstance(tpl_formula[c], str) else None
    for c in range(1, 29):                                   # the total row's own refs to row 60
        v = wo.cell(total, c).value
        if isinstance(v, str) and v.startswith("="):
            wo.cell(total, c).value = re.sub(r"(?<=[A-Z])" + str(T_TOTAL) + r"(?!\d)", str(total), v)
    for r in range(T_FIRST + n, total - 1):                 # nothing left between data and total
        for c in range(1, 29):
            wo.cell(r, c).value = None
    wo.cell(total, 2).value = f"{n} part numbers"
    extend_cf(wo, last, T_LAST)
    note_r = total + 7
    derived = costed[costed["cost_from"] != "price file"]
    if len(pending):
        wo.cell(note_r, 1).value = "NOT IN THIS SHEET"
        wo.cell(note_r, 2).value = (f"{len(pending)} part numbers in ITUK's request have no purchase price in our price files: "
                                    + ", ".join(f"{p.pn} {p.desc}" for p in pending.itertuples())
                                    + ". They are on the Customer View and the approval form, and left out of all profit figures here.")
    else:
        wo.cell(note_r, 1).value = "COST NOTE"
        wo.cell(note_r, 2).value = (f"All {n} lines are costed. {len(derived)} purchase prices are not under their own number in the "
                                    "price file and were taken as follows: "
                                    + "; ".join(f"{p.pn} {p.desc.strip()}: {p.cost_from}" for p in derived.itertuples()) + ".")
    wo.cell(note_r, 1).font = Font(name="Arial", bold=True, size=10, color="C00000")
    wo.merge_cells(start_row=note_r, start_column=2, end_row=note_r, end_column=28)
    wo.cell(note_r, 2).alignment = Alignment(wrap_text=True, vertical="top")
    wo.row_dimensions[note_r].height = 60
    olds = costed[costed["l12_also_billed_as"].notna()]
    if len(olds):
        r2 = note_r + 1
        wo.cell(r2, 1).value = "L12 NOTE"
        wo.cell(r2, 1).font = Font(name="Arial", bold=True, size=10, color="C00000")
        wo.cell(r2, 2).value = (f"L12 includes ITUK billing under older numbers of the same part on {len(olds)} lines: "
                                + "; ".join(f"{p.pn} {p.desc.strip()} (also billed as {p.l12_also_billed_as})" for p in olds.itertuples())
                                + ".")
        wo.merge_cells(start_row=r2, start_column=2, end_row=r2, end_column=28)
        wo.cell(r2, 2).alignment = Alignment(wrap_text=True, vertical="top")
        wo.row_dimensions[r2].height = 45
    wo.cell(1, 1).value = "SPA OPTIMIZER  ·  ITUK  ·  ISZE"
    wo.freeze_panes = "C6"

    # ---------- 3. Assumptions
    wa = wb["Assumptions"]
    wa["C4"] = 0.0
    wa["C6"] = fx_live
    wa["D6"] = (f"Cost basis: price-file FOB re-struck at {fx_live} JPY/EUR and Japan discount {disc_j} "
                f"(price file sits on {FX_FILE} / {DISC_FILE_J}). Thailand parts on FX only.")
    ctx = {9: "Isuzu Truck (UK) Ltd — ITUK", 10: "United Kingdom", 11: "ITUK 2026 SPA – PMS",
           12: datetime(2026, 11, 1), 13: datetime(2027, 10, 31), 14: args.prepared_by,
           15: "EUR", 16: "Not applicable — EUR"}
    for r, v in ctx.items():
        wa.cell(r, 2).value = v
        if isinstance(v, datetime):
            wa.cell(r, 2).number_format = "dd-mmm-yyyy"
    gm_style = {c: copy(wa.cell(GM_FIRST, c)._style) for c in range(1, 5)}
    gm_tpl = {c: wa.cell(GM_FIRST, c).value for c in range(1, 5)}
    if n < T_LINES:
        clear_rows(wa, GM_FIRST + n, GM_FIRST + T_LINES - 1, 4)
    for i in range(n):
        r, opt = GM_FIRST + i, T_FIRST + i
        for c in range(1, 5):
            cell = wa.cell(r, c)
            cell._style = copy(gm_style[c])
            cell.value = re.sub(r"(?<=!)([A-Z]{1,2})6(?!\d)", rf"\g<1>{opt}", gm_tpl[c])
    extend_cf(wa, GM_FIRST + n - 1, GM_FIRST + T_LINES - 1)
    half, most = f"{n}*0.5", f"{n}*0.83"
    R, AB = f"'SPA Optimizer'!R6:R{last}", f"'SPA Optimizer'!AB6:AB{last}"
    wa["B27"] = f'=COUNTIF({R},"▲ BETTER")&" of {n}"'
    wa["C27"] = (f'=IF(COUNTIF({R},"▲ BETTER")>={half},"✔  Majority viable standalone",'
                 f'IF(COUNTIF({R},"▲ BETTER")>={n}*0.17,"⚠  Few viable standalone — IML needed for most","✖  None viable without IML"))')
    wa["B28"] = f'=COUNTIF({AB},"▲ BETTER")&" of {n}"'
    wa["C28"] = (f'=IF(COUNTIF({AB},"▲ BETTER")>={most},"✔  SPA approvable with IML support",'
                 f'IF(COUNTIF({AB},"▲ BETTER")>={half},"⚠  Partial approval possible — review weak lines","✖  Not viable even with IML — renegotiate"))')
    # Approval basis agreed with Jerome 2026-10-26: turnover above L12 (PMS market-share project).
    wa["C31"] = (f'=IF(\'SPA Optimizer\'!L{total}>\'SPA Optimizer\'!F{total},IF(\'SPA Optimizer\'!Y{total}>=0,'
                 f'"✔  APPROVABLE — turnover and gross profit above L12.",'
                 f'"⚠  APPROVABLE ON TURNOVER — turnover above L12, gross profit "&TEXT(-\'SPA Optimizer\'!Y{total},"#,##0")&" € below L12. PMS market-share investment, MD decision."),'
                 f'"✖  NOT READY — turnover below L12.")')

    # ---------- 4. Customer View and IML brief: per-line blocks
    def relink(ws, first, total_row, tail_rows: range, max_col, extra=None):
        style = {c: copy(ws.cell(first, c)._style) for c in range(1, max_col + 1)}
        tpl = {c: ws.cell(first, c).value for c in range(1, max_col + 1)}
        for m in [m for m in list(ws.merged_cells.ranges) if first <= m.min_row < total_row]:
            ws.unmerge_cells(str(m))
        n_rows = n + (len(extra) if extra is not None else 0)
        new_total = first + n_rows
        if new_total < total_row:
            clear_rows(ws, new_total, total_row - 1, max_col)
        move_block(ws, tail_rows, new_total - total_row, max_col)
        for c in range(1, max_col + 1):                      # totals: SUM(x5:x57) -> new range
            v = ws.cell(new_total, c).value
            if isinstance(v, str) and v.startswith("="):
                ws.cell(new_total, c).value = re.sub(r"([A-Z]{1,2})" + str(first) + r":([A-Z]{1,2})" + str(total_row - 1) + r"(?!\d)",
                                                     rf"\g<1>{first}:\g<2>{new_total - 1}", v)
        for i in range(n):
            r, opt = first + i, T_FIRST + i
            for c in range(1, max_col + 1):
                cell = ws.cell(r, c)
                cell._style = copy(style[c])
                v = tpl[c]
                cell.value = re.sub(r"(?<=!)([A-Z]{1,2})6(?!\d)", rf"\g<1>{opt}", v) if isinstance(v, str) else v
        return new_total, style

    wcv = wb["Customer View"]
    cv_total, cv_style = relink(wcv, CV_FIRST, CV_TOTAL, range(CV_TOTAL, 65), 12, extra=pending)
    for j, p in enumerate(pending.itertuples()):
        r = CV_FIRST + n + j
        vals = [p.pn, p.desc, float(p.list_eur), float(p.spa_price), f"=C{r}-D{r}", f"=IFERROR(E{r}/C{r},0)",
                float(p.spa_qty), f"=D{r}*G{r}", f"=C{r}*G{r}-H{r}",
                (f"=IFERROR(G{r}/{float(p.l12_qty)}-1,0)" if p.l12_qty > 0 else 0), f"=E{r}*G{r}", "Price confirmation pending"]
        for c, v in enumerate(vals, start=1):
            cell = wcv.cell(r, c)
            cell._style = copy(cv_style[c])
            cell.value = v
    wcv.cell(cv_total, 2).value = f"{n + len(pending)} part numbers"
    for col in ("H", "I", "K"):
        wcv[f"{col}{cv_total}"] = f"=SUM({col}{CV_FIRST}:{col}{cv_total - 1})"
    wcv["G" + str(cv_total)] = f"=SUM(G{CV_FIRST}:G{cv_total - 1})"
    wcv["G" + str(cv_total)]._style = copy(wcv["H" + str(cv_total)]._style)
    wcv["G" + str(cv_total)].number_format = "#,##0"
    wcv["A2"] = '=Assumptions!B9 & "  |  Market: " & Assumptions!B10 & "  |  Ref: " & Assumptions!B11 & "  |  Valid " & TEXT(Assumptions!B12,"dd-mmm-yyyy") & " to " & TEXT(Assumptions!B13,"dd-mmm-yyyy")'
    wcv.freeze_panes = "A5"

    wim = wb["IML_IMIT Brief"]
    im_total, _ = relink(wim, CV_FIRST, CV_TOTAL, range(CV_TOTAL, 69), 13)
    wim.cell(im_total, 2).value = f"{n} lines"
    im_text = {
        1: ("ITUK runs the UK Isuzu truck network. N75 fleet in operation: 9,359 units (DVLA 2024). ITUK's PMS campaign "
            "(Phase 1 N75, launch autumn 2026) was agreed with ISZJ in the meeting of 18 August 2026."),
        2: ("Not requested for this SPA (Assumptions C4 = 0%). ISZE carries the discount as an investment in the PMS market-share project. "
            "Column H shows, per line, the cut that would make that line profit-neutral; it is for reference only."),
        3: ("ITUK commits more units than its L12 purchases in total (column L vs column K), so IML / IMIT volume grows "
            "with no price sacrifice. Net IML revenue upside per line is in column M."),
        4: "=\"ITUK retention risk is rated \"&Assumptions!B17&\"/5 (Assumptions tab). Brake price vs aftermarket is ITUK dealers' first complaint.\"",
        5: "No split proposed: ISZE carries the SPA discount on its own margin.",
        6: "None. This brief is for information; no IML / IMIT purchase price reduction is asked.",
    }
    for k, v in im_text.items():
        wim.cell(im_total + 2 + k, 2).value = v
    wim.freeze_panes = "A5"

    # ---------- 5. Scenario Planner (reference errors only; layout kept)
    wsp = wb["Scenario Planner"]
    O = "'SPA Optimizer'!"
    Rr, Lr, Qr, Pr = (f"{O}{c}6:{c}{last}" for c in "RLQP")
    wsp["A2"] = f"Models SPA scenarios: Partial (lines with ▲ BETTER only) | Full (all {n} lines) | Full + IML cut | Enhanced (Full + volume growth assumption)"
    wsp["B7"] = "=Assumptions!C4"
    wsp["B8"] = "=Assumptions!B16"
    wsp["B12"] = f'=COUNTIF({Rr},"▲ BETTER")&" of {n}"'
    wsp["D12"] = f'=SUMIF({Rr},"▲ BETTER",{Qr})'
    for r in (13, 14, 15):
        wsp[f"B{r}"] = f'="{n} of {n}"'
    wsp["A13"] = f"Full — All {n} lines (no IML cut)"
    wsp["G13"] = "★ RECOMMENDED — ITUK's proposal in full, approved on turnover growth for the PMS market-share project. No IML / IMIT cut asked."
    wsp["A14"] = "Full + IML support (cut in Assumptions C4)"
    wsp["G14"] = "Only differs from Full when an IML cut is entered in Assumptions C4. Base case: 0%, not asked."
    wsp["C15"] = f"={O}L{total}*(1+Assumptions!B19)"
    wsp["F15"] = f"={O}L{total}*(1+Assumptions!B19)"
    _ = Pr

    # ---------- 6. MD Approval Request
    wmd = wb["MD Approval Request"]
    wmd["E4"] = args.manager
    wmd["J11"] = "2575"
    wmd["J12"] = "IE40"
    wmd["H15"] = "SPA PROPOSAL (no IML support)"
    wmd["H32"] = "After SPA\n(no IML support)"
    wmd["H35"] = "=H34-H36"
    for r in (33, 34, 35, 36, 37):
        wmd[f"F{r}"] = "-" if r > 33 else "No target set"
    wmd["B8"] = "PARTS CAMPAIGN — PMS (scheduled maintenance), Phase 1 N75"
    pend_txt = ("; ".join(f"{p.pn} {p.desc.strip()}" for p in pending.itertuples()))
    wmd["B26"] = (
        '=IFERROR("Special Pricing Agreement — "&Assumptions!B9&" | Market: "&Assumptions!B10,"")&CHAR(10)&CHAR(10)'
        f'&"This SPA covers "&COUNTA(\'SPA Optimizer\'!A6:A{last})&" part lines with a total SPA revenue commitment of "'
        f'&TEXT(\'SPA Optimizer\'!L{total},"#,##0")&" € vs a L12 baseline of "&TEXT(\'SPA Optimizer\'!F{total},"#,##0")&" €."&CHAR(10)'
        f'&"Gross margin moves from "&TEXT(\'SPA Optimizer\'!I{total},"0.0%")&" (L12) to "&TEXT(\'SPA Optimizer\'!O{total},"0.0%")'
        f'&" (SPA). Turnover "&TEXT(\'SPA Optimizer\'!P{total},"+#,##0;-#,##0")&" € ("&TEXT(\'SPA Optimizer\'!L{total}/\'SPA Optimizer\'!F{total}-1,"+0.0%;-0.0%")&"), gross profit "'
        f'&TEXT(\'SPA Optimizer\'!Q{total},"+#,##0;-#,##0")&" € vs L12. No IML / IMIT purchase support is requested."&CHAR(10)&CHAR(10)'
        f'&"Motivation: this SPA supports the ITUK PMS project (Phase 1 N75) to increase genuine market share on scheduled-maintenance parts '
        f'(target +1% PMS share by value, agreed with ITUK and ISZJ on 18 Aug 2026). ITUK commits "&TEXT(\'SPA Optimizer\'!K{total},"#,##0")'
        f'&" units vs "&TEXT(\'SPA Optimizer\'!E{total},"#,##0")&" in L12. We ask approval on the turnover growth; the margin given is the investment in share."&CHAR(10)'
        f'&"Risk: at L12 volume the SPA costs "&TEXT(-\'Profit Bridge\'!B13,"#,##0")&" € gross profit. Control: volume review at 6 months, SPA price withdrawn on lines under L12."&CHAR(10)'
        + (f'&"Not in the figures: {len(pending)} lines without a purchase price yet ({pend_txt}), SPA value "'
           f'&TEXT(SUMPRODUCT(\'Customer View\'!H{CV_FIRST + n}:H{cv_total - 1}),"#,##0")&" €."' if len(pending) else
           f'&"All {n} lines are costed; {len(derived)} purchase prices come from the predecessor number or the yen base price (note under the SPA Optimizer totals)."')
    )

    # ---------- 7. SPA Rationale: the template's generic distributor text, written for ITUK
    wr = wb["SPA Rationale"]
    low = costed.assign(gm=1 - costed.purchase / costed.spa_price).nsmallest(12, "gm")
    txt = {
        "A1": "SPA APPROVAL REQUEST — MANAGEMENT APPROVER",
        "A2": f"Customer: ITUK  ·  {n} part lines{f' (+{len(pending)} pending cost)' if len(pending) else ''}  ·  {date.today():%d-%b-%Y}  ·  Prepared by: {args.prepared_by}",
        "A5": ("This submission follows the agreed approval procedure:\n\n"
               "1.  ROI study completed in full on ITUK's own proposal (see Section C and the SPA Optimizer tab).\n"
               "2.  No price commitment made to ITUK pending your approval.\n"
               "3.  No IML / IMIT purchase support is requested. Approval is asked on turnover growth, as an investment in PMS market share.\n\n"
               "We are presenting this to you first."),
        "A10": (f"Price support on {n} part lines for ITUK's PMS project, to increase genuine market share on scheduled-maintenance "
                "parts (Phase 1 N75, launch autumn 2026; target +1% PMS share by value), agreed in the "
                "ITUK / ISZE / ISZJ meeting of 18 August 2026. Brake price is ITUK dealers' first complaint "
                "(April 2026 trip: one aftermarket brand's brake parts were 60–75% below ITUK wholesale). Price relief is linked to ITUK's committed "
                "volume and limited to 12 months."),
        "A12": "=\"• L12 baseline (SAP billing, sold-to 2575): gross profit \"&TEXT('SPA Optimizer'!H" + str(total)
               + ",\"#,##0 €\")&\" | GM \"&TEXT('SPA Optimizer'!I" + str(total) + ",\"0.0%\")&CHAR(10)"
               "&\"• SPA at committed volume, no IML support: gross profit \"&TEXT('SPA Optimizer'!N" + str(total)
               + ",\"#,##0 €\")&\" | GM \"&TEXT('SPA Optimizer'!O" + str(total) + ",\"0.0%\")&CHAR(10)"
               "&\"• Delta: turnover \"&TEXT('SPA Optimizer'!P" + str(total) + ",\"+#,##0 €;-#,##0 €\")&\", gross profit \"&TEXT('SPA Optimizer'!Q" + str(total) + ",\"+#,##0 €;-#,##0 €\")"
               "&CHAR(10)&CHAR(10)&\"GM% floor compliance per line is in Section D and the Assumptions tab.\"",
        "A14": "=\"No IML / IMIT purchase price reduction is requested. For reference, a 7% IML cut would add \"&TEXT('Profit Bridge'!B9,\"#,##0 €\")&\" to ISZE gross profit. ISZE carries the discount itself as an investment in PMS market share; approval is asked on the turnover growth.\"",
        "A19": "→ No IML sacrifice requested (0 €)",
        "C19": f"='SPA Optimizer'!N{total}",
        "F19": "Not applicable — no IML investment",
        "H19": f"='SPA Optimizer'!F{total}",
        "A20": "IML/IMIT investment (sacrifice)",
        "C20": "ISZE GP at SPA, no IML support",
        "F20": "Return ratio",
        "H20": "L12 revenue on these lines (at risk if ITUK moves PMS parts to IAM)",
        "A23": "All lines are checked in the Assumptions tab (GM% Floor Check) against a 25% floor. The 12 lowest SPA margins are below; none is under 30%.",
        "A39": ("We are requesting one approval:\n\n"
                "DECISION:  Approve the SPA with ITUK at the prices and volumes in the SPA Optimizer tab, valid 1 Nov 2026 to "
                "31 Oct 2027, with no IML / IMIT purchase support, on the basis that turnover grows above L12. The gross profit "
                "difference vs L12 is accepted as the investment in PMS market share.\n\n"
                "Bounded: 12-month SPA, volume reviewed at 6 months. On lines where ITUK stays under its L12 volume, ISZE "
                "withdraws SPA pricing."
                + (f" The {len(pending)} lines without a purchase price are loaded only after IML confirms their cost." if len(pending) else "")),
        "A43": ("ITUK runs the UK Isuzu truck network. Its PMS campaign targets scheduled-service parts on the N75 fleet "
                "(9,359 units, DVLA 2024), with brakes and filters as the core. ITUK's margin on N75 brake pads is about "
                "18% after logistics, so it cannot fund the price gap alone (meeting of 18 August 2026)."),
        "A46": ("An SPA links price relief to ITUK's committed volume per part number. A general price reduction would give "
                "the same discount with no volume commitment."),
        "A49": ("The PMS campaign goes live in autumn 2026. BVP brake parts are expected in the market only around the end "
                "of Q1 2027, so the SPA on genuine parts is the bridge until then."),
        "A52": ("=\"ISZE stays at current prices. ITUK's PMS campaign runs without price support on genuine parts. The "
                "L12 revenue on these lines is \"&TEXT('SPA Optimizer'!F" + str(total) + ",\"#,##0 €\")&\"; the downside "
                "case (ITUK takes the SPA prices but only buys its L12 volume) is \"&TEXT('Profit Bridge'!B13,\"+#,##0 €;-#,##0 €\")&\" gross profit vs L12.\""),
        "A55": ("1. Increases genuine market share on PMS parts in the UK, in line with the +1% PMS share target agreed with ITUK and ISZJ.\n"
                "2. Volume commitments per part number improve ISZE forecast and stock planning.\n"
                "3. Same structure can be reused for N35 (Phase 2)."),
        "A58": (f"• L12: SAP billing to sold-to 2575, Sep 2025–Aug 2026  •  Cost: price-file FOB at {fx_live} JPY/EUR and Japan "
                f"discount {disc_j}  •  SPA prices: ITUK proposal rounded to the cent  •  IML cut: 0% (Assumptions C4)  •  "
                + (f"{len(pending)} lines without purchase price excluded from figures" if len(pending) else
                 f"{len(derived)} costs via predecessor number or yen base price (see SPA Optimizer note)")),
    }
    for ref, v in txt.items():
        wr[ref] = v
    for i, rec in enumerate(low.itertuples()):
        r = 25 + i
        opt = T_FIRST + int(rec.Index)
        for col, v in zip("ABCDEF", [f"='SPA Optimizer'!A{opt}", f"='SPA Optimizer'!B{opt}", f"='SPA Optimizer'!I{opt}",
                                      f"='SPA Optimizer'!O{opt}", f'=IF(D{r}>=0.25,"✔ above","✖ below")',
                                      f'=IF(D{r}>=0.3,"✔ above","⚠ below")']):
            wr[f"{col}{r}"] = v
        wr[f"G{r}"] = "Above floor — no explanation needed"
        for col in "CD":
            wr[f"{col}{r}"].number_format = "0.0%"

    # ---------- 8. Profit Bridge (added sheet: the waterfall)
    wb_ = wb.create_sheet("Profit Bridge")
    navy = PatternFill("solid", fgColor="1F3864")
    wb_.merge_cells("A1:H1")
    wb_["A1"] = "PROFIT BRIDGE — L12 gross profit to SPA gross profit (ISZE, EUR)"
    wb_["A1"].font, wb_["A1"].fill = Font(name="Arial", bold=True, color="FFFFFF", size=12), navy
    for col, w in zip("ABCDEFGH", (46, 16, 3, 18, 14, 14, 14, 14)):
        wb_.column_dimensions[col].width = w
    hf = 30                                           # helper block (per line) starts here
    hl = hf + n - 1
    rows = [
        (3, "L12 gross profit (SAP billing, today's cost)", f"={O}H{total}"),
        (4, "Volume effect — ITUK commits more units", f"=SUM(L{hf}:L{hl})"),
        (5, "Price effect — SPA price vs L12 billed price", f"=SUM(M{hf}:M{hl})"),
        (6, "SPA gross profit — ISZE alone (no IML cut)", f"={O}N{total}"),
        (8, "What-if IML cut %", 0.07),
        (9, "What-if: IML purchase cut", f"=SUMPRODUCT({O}C6:C{last},{O}K6:K{last})*B8"),
        (10, "SPA gross profit — with what-if IML cut", "=B6+B9"),
        (12, "Check: L12 + volume + price − SPA (must be 0)", "=ROUND(B3+B4+B5-B6,2)"),
        (13, "Downside: SPA prices at L12 volume — Δ GP vs L12", f"=SUMPRODUCT({O}J6:J{last}-{O}C6:C{last},{O}E6:E{last})-{O}H{total}"),
    ]
    for r, lab, v in rows:
        wb_[f"A{r}"], wb_[f"B{r}"] = lab, v
        wb_[f"A{r}"].font = Font(name="Arial", size=10, bold=r in (3, 6, 10))
        wb_[f"B{r}"].font = Font(name="Arial", size=10, bold=r in (3, 6, 10), color="0000FF" if r == 8 else "000000")
        wb_[f"B{r}"].number_format = "0%" if r == 8 else '#,##0" €";-#,##0" €";"-"'
    for col, t in zip("DEFGH", ("Bar", "Base", "Increase", "Decrease", "Total")):
        wb_[f"{col}2"] = t
        wb_[f"{col}2"].font, wb_[f"{col}2"].fill = Font(name="Arial", bold=True, color="FFFFFF", size=9), PatternFill("solid", fgColor="595959")
    bars = [("L12 profit", "=0", "=0", "=0", "=B3"),
            ("Volume", "=B3+MIN(0,B4)", "=MAX(0,B4)", "=MAX(0,-B4)", "=0"),
            ("Price", "=B3+B4+MIN(0,B5)", "=MAX(0,B5)", "=MAX(0,-B5)", "=0"),
            ("SPA profit", "=0", "=0", "=0", "=B6"),
            ("IML cut (what-if)", "=B6+MIN(0,B9)", "=MAX(0,B9)", "=MAX(0,-B9)", "=0"),
            ("SPA + cut (what-if)", "=0", "=0", "=0", "=B10")]
    for i, (lab, *vals) in enumerate(bars):
        r = 3 + i
        wb_[f"D{r}"] = lab
        for col, v in zip("EFGH", vals):
            wb_[f"{col}{r}"] = v
            wb_[f"{col}{r}"].number_format = '#,##0;-#,##0;"-"'
        for col in "DEFGH":
            wb_[f"{col}{r}"].font = Font(name="Arial", size=9)
    ch = BarChart()
    ch.type, ch.grouping, ch.overlap, ch.gapWidth = "col", "stacked", 100, 60
    ch.title = "ITUK SPA — gross profit bridge (EUR)"
    ch.y_axis.numFmt = "#,##0"
    ch.y_axis.majorGridlines = None
    ch.add_data(Reference(wb_, min_col=5, max_col=8, min_row=2, max_row=8), titles_from_data=True)
    ch.set_categories(Reference(wb_, min_col=4, min_row=3, max_row=8))
    for s, colr in zip(ch.series, (None, "70AD47", "C00000", "1F3864")):
        if colr is None:
            s.graphicalProperties.noFill = True
            s.graphicalProperties.line.noFill = True
            continue
        s.graphicalProperties.solidFill = colr
        s.graphicalProperties.line.solidFill = colr
        s.dLbls = DataLabelList()
        s.dLbls.showVal = True
        s.dLbls.showSerName = s.dLbls.showCatName = s.dLbls.showLegendKey = s.dLbls.showPercent = False
        s.dLbls.numFmt = '"-"#,##0;;' if colr == "C00000" else "#,##0;-#,##0;"
        s.dLbls.txPr = RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=CharacterProperties(
            sz=900, b=True, solidFill="FFFFFF")), endParaRPr=CharacterProperties())])
    ch.legend = None
    ch.height, ch.width = 8, 22
    wb_.add_chart(ch, "A15")
    # helper block: per line, linked to the optimizer
    for col, t in zip("JKLM", ("P/N", "L12 billed €/unit", "Volume effect €", "Price effect €")):
        wb_[f"{col}{hf - 1}"] = t
        wb_[f"{col}{hf - 1}"].font = Font(name="Arial", bold=True, size=9)
    for i in range(n):
        r, opt = hf + i, T_FIRST + i
        wb_[f"J{r}"] = f"={O}A{opt}"
        wb_[f"K{r}"] = f"=IF({O}E{opt}>0,{O}F{opt}/{O}E{opt},{O}D{opt})"
        wb_[f"L{r}"] = f"=({O}K{opt}-{O}E{opt})*(K{r}-{O}C{opt})"
        wb_[f"M{r}"] = f"=({O}J{opt}-K{r})*{O}K{opt}"
        for col in "KLM":
            wb_[f"{col}{r}"].number_format = "#,##0.00"
    wb_["J28"] = "Helper — per line (do not edit)"
    wb_["J28"].font = Font(name="Arial", italic=True, size=9, color="808080")
    wb_.page_setup.orientation = "landscape"
    wb_.sheet_properties.pageSetUpPr.fitToPage = True
    wb_.page_setup.fitToWidth, wb_.page_setup.fitToHeight = 1, 1
    wb_.print_area = "A1:H32"

    if args.pms_only:
        pms_extract_text(wb, n, n_basket, total, last)
    wb.active = wb.sheetnames.index("MD Approval Request")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    for ws in wb.worksheets:
        if ws.title not in ("MD Approval Request", "Profit Bridge"):
            ws.sheet_state = "hidden"
    # PDF copy only: the template's form has no page setup, so fit it to one A4 page
    wmd.sheet_properties.pageSetUpPr.fitToPage = True
    wmd.page_setup.fitToWidth, wmd.page_setup.fitToHeight = 1, 1
    wmd.page_setup.orientation = "portrait"
    wmd.page_setup.paperSize = wmd.PAPERSIZE_A4
    wmd.print_area = "A1:M42"
    wb.active = wb.sheetnames.index("MD Approval Request")
    wb.save(out.with_name(out.stem + "_print.xlsx"))
    print(f"lines {len(df)} | in optimizer {n} (rows 6-{last}, total row {total}) | pending {len(pending)}")
    print("template fixes:\n  - " + "\n  - ".join(TEMPLATE_FIXES))
    print(f"wrote {out}")
    return out


def pms_extract_text(wb, n, n_basket, total, last):
    """PMS-only extract: neutral, figure-driven wording. The approval wording ('approval asked on turnover
    growth') is true for the full basket, not for the PMS subset, so it is replaced here."""
    O = "'SPA Optimizer'!"
    tag = f"PMS PARTS ONLY — {n} of {n_basket} part numbers in the ITUK SPA request. Analysis extract, not the approval request."
    wb["SPA Optimizer"]["A1"] = "SPA OPTIMIZER  ·  ITUK  ·  ISZE  ·  PMS PARTS ONLY"
    wb["SPA Optimizer"]["A2"] = tag
    wb["How to Use"]["A2"] = tag
    wb["MD Approval Request"]["B7"] = "Promotional Parts Price Change Request — PMS parts extract (for information)"
    wb["MD Approval Request"]["B26"] = (
        '="Special Pricing Agreement — "&Assumptions!B9&" | Market: "&Assumptions!B10&" | PMS parts only"&CHAR(10)&CHAR(10)'
        f'&"PMS parts in the ITUK SPA: "&COUNTA({O}A6:A{last})&" of {n_basket} part numbers (filters, brakes, clutch)."&CHAR(10)'
        f'&"Turnover: target "&TEXT({O}L{total},"#,##0")&" € vs "&TEXT({O}F{total},"#,##0")&" € in L12 ("&TEXT({O}P{total},"+#,##0;-#,##0")&" €, "'
        f'&TEXT({O}L{total}/{O}F{total}-1,"+0.0%;-0.0%")&"). Units: "&TEXT({O}K{total},"#,##0")&" vs "&TEXT({O}E{total},"#,##0")&"."&CHAR(10)'
        f'&"Gross profit: "&TEXT({O}N{total},"#,##0")&" € vs "&TEXT({O}H{total},"#,##0")&" € in L12 ("&TEXT({O}Q{total},"+#,##0;-#,##0")&" €). '
        f'Margin "&TEXT({O}I{total},"0.0%")&" → "&TEXT({O}O{total},"0.0%")&". No IML / IMIT support applied."&CHAR(10)'
        '&"L12 = SAP billing to ITUK, 1 Sep 2025 – 31 Aug 2026 (last 12 complete months available)."')
    wa = wb["Assumptions"]
    wa["C31"] = (f'=IF({O}L{total}>{O}F{total},"Turnover above L12","Turnover below L12")&", gross profit "'
                 f'&IF({O}Y{total}>=0,"above","below")&" L12 — PMS parts only, for information."')
    wsp = wb["Scenario Planner"]
    wsp["G13"] = "PMS parts only, ITUK's proposal as sent. For information."
    wr = wb["SPA Rationale"]
    wr["A1"] = "SPA ANALYSIS — PMS PARTS ONLY (for information)"
    wr["A5"] = (f"This sheet covers the {n} PMS part numbers of the ITUK SPA request ({n_basket} part numbers in total), "
                "for the PMS review requested by management. The approval request itself is the full-basket file.")
    wr["A12"] = (f"=\"• L12 (Sep 2025 – Aug 2026): turnover \"&TEXT({O}F{total},\"#,##0 €\")&\", gross profit \"&TEXT({O}H{total},\"#,##0 €\")"
                 f"&CHAR(10)&\"• SPA target: turnover \"&TEXT({O}L{total},\"#,##0 €\")&\", gross profit \"&TEXT({O}N{total},\"#,##0 €\")"
                 f"&CHAR(10)&\"• Delta: turnover \"&TEXT({O}P{total},\"+#,##0 €;-#,##0 €\")&\", gross profit \"&TEXT({O}Q{total},\"+#,##0 €;-#,##0 €\")")
    wr["A14"] = "=\"No IML / IMIT purchase support applied. For reference, a 7% IML cut on these parts would add \"&TEXT('Profit Bridge'!B9,\"#,##0 €\")&\" gross profit.\""
    wr["A39"] = "Not an approval request. Figures for information on the PMS part of the ITUK SPA."
    wr["A52"] = ""


def main() -> int:
    stamp = date.today().strftime("%Y%m%d")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--basket", required=True)
    ap.add_argument("--out", default=str(ISZE_ROOT / "01_data" / "90_INBOX" / f"_spa_application_ITUK_PMS_{stamp}"
                                         / f"SPA_Optimizer_V4_ITUK_2026_PMS_{stamp}.xlsx"))
    ap.add_argument("--prepared-by", default="Jerome Van der Pluym")
    ap.add_argument("--manager", default="Hadewijch Tibos")
    ap.add_argument("--pms-only", action="store_true", help="keep only the PMS parts (filters, brakes, clutch)")
    build(ap.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
