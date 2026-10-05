# -*- coding: utf-8 -*-
"""Verify the Excel workbook: recalculate in Excel, then read the live values.

A formula-driven workbook that nobody opened is an unverified workbook. This
opens it in Excel, forces a full recalculation, reads the Check sheet and the
headline figures back, and compares them to the meta JSON the data builder
wrote. Any disagreement is a failure, not a warning.

Run: python 02_dashboards/pricing/_build/verify_price_bp_weighted_xlsx.py
"""
import io
import json
import sys
from pathlib import Path

import win32com.client as win32

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
XLSX = ISZE / "02_dashboards" / "pricing" / "ISZE_Price_BP_Weighted_Compare.xlsx"
META = ISZE / "01_data" / "00_derived" / "price_bp_weighted_compare_meta.json"

meta = json.loads(META.read_text(encoding="utf-8"))
net_pct = meta["coverage"] and None  # placeholder, real value read below

failures = []
excel = win32.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
wb = None
try:
    wb = excel.Workbooks.Open(str(XLSX))
    excel.CalculateFullRebuild()

    ws_ov = wb.Worksheets("Overview")
    ws_ch = wb.Worksheets("Checks")
    ws_cl = wb.Worksheets("By class")
    ws_pn = wb.Worksheets("PN data")

    # The PN data sheet must carry a Description column next to the part number.
    pn_head = [str(ws_pn.Cells(1, c).Value or "").strip() for c in range(1, 14)]
    if pn_head[3].lower() != "part_number" or pn_head[4].lower() != "description":
        failures.append(f"PN data column order unexpected: {pn_head}")
    blank_d = sum(1 for r in range(2, min(ws_pn.UsedRange.Rows.Count, 2000) + 1)
                  if not str(ws_pn.Cells(r, 5).Value or "").strip())
    if blank_d:
        failures.append(f"{blank_d} blank descriptions in the first rows of PN data")
    print(f"PN data description column: E={pn_head[4]!r}, "
          f"{ws_pn.UsedRange.Rows.Count - 1:,} rows, {blank_d} blank")

    # Find the NETWORK row on Overview.
    net_row = None
    for r in range(7, 40):
        if str(ws_ov.Cells(r, 1).Value or "").strip() == "NETWORK":
            net_row = r
            break
    if net_row is None:
        failures.append("NETWORK row not found on Overview")
        net_row = 999

    net_pct_x = ws_ov.Cells(net_row, 2).Value
    net_step_x = ws_ov.Cells(net_row, 3).Value

    print("=" * 78)
    print("EXCEL RECALCULATION - live values")
    print("=" * 78)
    print(f"Overview NETWORK weighted increase : {net_pct_x:.6f}  "
          f"({net_pct_x*100:.4f}%)")
    print(f"Overview NETWORK value of the step : EUR {net_step_x:,.2f}")
    print()

    # Every check row must read OK. A row whose OK cell errors is not a pass: an
    # Excel error such as #VALUE! used to be skipped here in silence, which is how
    # three half-working checks survived a previous ship.
    print("Checks sheet:")
    for r in range(5, 12):
        lab = ws_ch.Cells(r, 1).Value
        if not lab:
            continue
        val = ws_ch.Cells(r, 2).Value
        exp = ws_ch.Cells(r, 3).Value
        ok = ws_ch.Cells(r, 4).Value
        print(f"  [{str(ok):>7}] {str(lab)[:58]:<58} value={val} expected={exp}")
        if ok == "CHECK":
            failures.append(f"check failed: {lab} (value={val}, expected={exp})")
        elif ok != "OK":
            failures.append(
                f"check row {r} did not return OK or CHECK: {str(lab)[:50]} -> {ok!r} "
                f"(value={val}, expected={exp})")
        elif not isinstance(exp, (int, float)):
            failures.append(
                f"check row {r} compares against a non-numeric expectation: {exp!r}")

    # The L12M basket on Overview is euro, not quantity. Read it against the live
    # euro column on PN data in a single COM call (47k cell-by-cell reads are
    # rejected by Excel), so a column shift cannot pass unnoticed: the basket row
    # above compares two copies of the same formula and would agree regardless.
    net_basket = ws_ov.Cells(net_row, 4).Value
    pn_rows = int(ws_pn.UsedRange.Rows.Count) - 1
    euro_col = ws_pn.Range(f"H2:H{pn_rows + 1}").Value
    pn_basket = sum(float(c[0]) for c in euro_col
                    if c and isinstance(c[0], (int, float)))
    shown = f"{net_basket:,.2f}" if isinstance(net_basket, (int, float)) else "n/a"
    print(f"  Overview L12M basket EUR {shown} vs PN data euro column {pn_basket:,.2f}")
    if isinstance(net_basket, (int, float)):
        if abs(net_basket - pn_basket) > 1.0:
            failures.append(
                f"Overview L12M basket EUR {net_basket:,.2f} != PN data euro column {pn_basket:,.2f}")
        if net_basket < 1_000_000:
            failures.append(
                f"Overview L12M basket looks like a quantity, not euro: {net_basket:,.0f}")

    print()
    print("By class (recalculated):")
    for r in range(5, 20):
        cls = ws_cl.Cells(r, 1).Value
        if not cls:
            continue
        pct = ws_cl.Cells(r, 2).Value
        step = ws_cl.Cells(r, 3).Value
        pcts = f"{pct*100:.3f}%" if isinstance(pct, (int, float)) else str(pct)
        steps = f"EUR {step:,.0f}" if isinstance(step, (int, float)) else str(step)
        print(f"  {str(cls):<6} {pcts:>10}  {steps:>14}")

    # The billed-quantity basis is what this workbook computes.
    exp_pct = meta["sensitivity"]["weight_base"]["weighted_increase_pct_billing_qty"] / 100
    if isinstance(net_pct_x, (int, float)) and abs(net_pct_x - exp_pct) > 5e-6:
        failures.append(
            f"Overview network {net_pct_x:.6f} != meta billed-basis {exp_pct:.6f}")
    exp_step = meta["sensitivity"]["prior_vintage"]["value_step_eur_revised_basis"]
    if isinstance(net_step_x, (int, float)) and abs(net_step_x - exp_step) > 1.0:
        failures.append(
            f"Overview step {net_step_x:,.2f} != meta {exp_step:,.2f}")

    # NaN / error scan across the used range of the sheets a reader sees.
    for nm in ["Overview", "By class", "Checks", "Read me"]:
        ws = wb.Worksheets(nm)
        used = ws.UsedRange
        for row in used.Value or []:
            if row is None:
                continue
            for cell in (row if isinstance(row, tuple) else (row,)):
                if isinstance(cell, str) and any(
                        e in cell for e in ("#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#N/A")):
                    failures.append(f"error value in {nm}: {cell}")
finally:
    if wb is not None:
        wb.Close(SaveChanges=False)
    excel.Quit()

print()
print("=" * 78)
if failures:
    print("FAILED:")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("XLSX_VERIFY_OK - every check resolves OK and the headline matches the meta")
