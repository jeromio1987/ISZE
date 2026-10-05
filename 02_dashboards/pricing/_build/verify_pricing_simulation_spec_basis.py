# -*- coding: utf-8 -*-
"""Verify the specification-basis workbook: recalculate in Excel, then read back.

A formula-driven workbook nobody opened is an unverified workbook. This opens it
in Excel, forces a full rebuild, reads the Overview, the segment pivots, the
Checks sheet and the class view back, and compares them to the build meta. Any
disagreement is a failure, not a warning - including a single error value.

Run: python 02_dashboards/pricing/_build/verify_pricing_simulation_spec_basis.py
"""
import io
import json
import sys
from pathlib import Path

import win32com.client as win32

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
XLSX = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Simulation_Spec_Basis.xlsx"
META = ISZE / "02_dashboards" / "pricing" / "_build" / "_spec_basis_meta.json"

meta = json.loads(META.read_text(encoding="utf-8"))
failures = []
notes = []


def retry(fn, attempts=25, pause=1.5):
    """Excel refuses calls while it is still loading a large workbook."""
    import time
    last = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as exc:                     # noqa: BLE001
            last = exc
            time.sleep(pause)
    raise last


excel = win32.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
excel.ScreenUpdating = False
wb = None
try:
    wb = excel.Workbooks.Open(str(XLSX))
    retry(lambda: excel.CalculateFullRebuild(), attempts=40, pause=2.0)

    def val(sheet, addr):
        return retry(lambda: wb.Worksheets(sheet).Range(addr).Value)

    print("=" * 78)
    print("EXCEL RECALCULATION - live values")
    print("=" * 78)

    ov_total = meta["overview_total_row"]
    print("Overview")
    for rr in range(6, ov_total + 1):
        label = val("Overview", f"A{rr}")
        pct = val("Overview", f"H{rr}")
        step = val("Overview", f"I{rr}")
        billed = val("Overview", f"J{rr}")
        qty = val("Overview", f"C{rr}")
        cover = val("Overview", f"E{rr}")
        if label is None:
            continue
        pct_s = f"{pct*100:.4f}%" if isinstance(pct, (int, float)) else str(pct)
        step_s = f"{step:,.2f}" if isinstance(step, (int, float)) else str(step)
        billed_s = f"{billed:,.2f}" if isinstance(billed, (int, float)) else str(billed)
        cov_s = f"{cover*100:.2f}%" if isinstance(cover, (int, float)) else str(cover)
        print(f"  {str(label)[:34]:<34} qty={qty:>10,.0f}  cover={cov_s:>7}  "
              f"move={pct_s:>9}  step={step_s:>14}  billed={billed_s:>15}")

    net_pct = val("Overview", f"H{ov_total}")
    net_step = val("Overview", f"I{ov_total}")
    net_billed = val("Overview", f"J{ov_total}")
    print()
    print(f"  NETWORK base-price move : {net_pct*100:.4f}%")
    print(f"  NETWORK value of step   : EUR {net_step:,.2f}")
    print(f"  NETWORK priced billing  : EUR {net_billed:,.2f}")

    if abs(net_pct - meta["weighted_pct"]) > 5e-7:
        failures.append(f"network move {net_pct:.8f} != meta {meta['weighted_pct']:.8f}")
    if abs(net_step - meta["step_eur"]) > 1.0:
        failures.append(f"network step {net_step:,.2f} != meta {meta['step_eur']:,.2f}")
    if abs(net_billed - meta["billed_eur_priced"]) > 1.0:
        failures.append(f"network billed {net_billed:,.2f} != meta "
                        f"{meta['billed_eur_priced']:,.2f}")
    if abs(net_pct - 0.059616) > 5e-6:
        failures.append(f"network move {net_pct:.6f} != published 0.059616")
    if abs(net_step - 1652140.71) > 1.0:
        failures.append(f"network step {net_step:,.2f} != published 1,652,140.71")

    # Israel must stay two rows and tie to the lane.
    print()
    print("Israel (two rows, never blended)")
    il_rows = []
    for rr in range(ov_total + 1, ov_total + 12):
        lab = val("Overview", f"A{rr}")
        if isinstance(lab, str) and ("UMI" in lab or "UTI" in lab):
            il_rows.append(rr)
            print(f"  {lab:<12} move={val('Overview', f'H{rr}')*100:.4f}%  "
                  f"step=EUR {val('Overview', f'I{rr}'):,.2f}  "
                  f"cover={val('Overview', f'E{rr}')*100:.2f}%")
    if len(il_rows) != 2:
        failures.append(f"expected two Israel rows, found {len(il_rows)}")

    # Segment pivots must each sum to the network step.
    print()
    print("Segment pivots (each block total must equal the network step)")
    seg_heads = []
    for rr in range(1, meta["seg_total_rows"][-1] + 1):
        lab = val("Increase by segment", f"A{rr}")
        if isinstance(lab, str) and ("Captured-demand" in lab or
                                     "How that position" in lab or
                                     "Position against" in lab or
                                     "Evidence behind" in lab or
                                     "two gates" in lab):
            seg_heads.append((rr, lab))
    for i, rr in enumerate(meta["seg_total_rows"]):
        tot = val("Increase by segment", f"G{rr}")
        label = next((h[1] for h in seg_heads if h[0] < rr), f"block {i + 1}")
        ok = isinstance(tot, (int, float)) and abs(tot - meta["step_eur"]) <= 1.0
        tot_s = f"{tot:,.2f}" if isinstance(tot, (int, float)) else str(tot)
        print(f"  {str(label)[:58]:<58} step={tot_s:>14}  "
              f"{'OK' if ok else 'MISMATCH'}")
        if not ok:
            failures.append(f"segment block '{label}' step {tot} != {meta['step_eur']}")

    print()
    print("Segment detail (captured-demand position)")
    for rr in range(meta["seg_total_rows"][0] - 5, meta["seg_total_rows"][0] + 1):
        lab = val("Increase by segment", f"A{rr}")
        if not lab:
            continue
        n = val("Increase by segment", f"B{rr}")
        step = val("Increase by segment", f"G{rr}")
        billed = val("Increase by segment", f"H{rr}")
        n_s = f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)
        step_s = f"{step:,.2f}" if isinstance(step, (int, float)) else str(step)
        billed_s = f"{billed:,.2f}" if isinstance(billed, (int, float)) else str(billed)
        print(f"  {str(lab):<24} lines={n_s:>6}  step={step_s:>14}  "
              f"billed={billed_s:>15}")

    print()
    print("Segment detail (evidence tier)")
    b3 = meta["seg_total_rows"][3]
    for rr in range(b3 - 7, b3 + 1):
        lab = val("Increase by segment", f"A{rr}")
        if not lab:
            continue
        n = val("Increase by segment", f"B{rr}")
        step = val("Increase by segment", f"G{rr}")
        n_s = f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)
        step_s = f"{step:,.2f}" if isinstance(step, (int, float)) else str(step)
        print(f"  {str(lab):<24} lines={n_s:>6}  step={step_s:>14}")

    print()
    print("Segment detail (two-gate sign)")
    b5 = meta["seg_total_rows"][4]
    for rr in range(b5 - 9, b5 + 1):
        lab = val("Increase by segment", f"A{rr}")
        if not lab:
            continue
        n = val("Increase by segment", f"B{rr}")
        step = val("Increase by segment", f"G{rr}")
        n_s = f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)
        step_s = f"{step:,.2f}" if isinstance(step, (int, float)) else str(step)
        print(f"  {str(lab):<30} lines={n_s:>6}  step={step_s:>14}")

    # The class view must tie as well.
    print()
    print("Retained class view")
    cls_total = meta["cls_total_row"]
    for rr in range(5, cls_total + 1):
        lab = val("Increase by class", f"A{rr}")
        if not lab:
            continue
        pct = val("Increase by class", f"F{rr}")
        step = val("Increase by class", f"D{rr}")
        pct_s = f"{pct*100:.3f}%" if isinstance(pct, (int, float)) else str(pct)
        print(f"  {str(lab):<6} move={pct_s:>10}  step={step:>14,.2f}")
    cls_step = val("Increase by class", f"D{cls_total}")
    if abs(cls_step - meta["step_eur"]) > 1.0:
        failures.append(f"class total {cls_step:,.2f} != {meta['step_eur']:,.2f}")

    # Checks sheet: every row must read OK.
    print()
    print("Checks")
    for rr in meta["check_rows"] + [meta["error_check_row"]]:
        lab = val("Checks", f"A{rr}")
        v = val("Checks", f"B{rr}")
        exp = val("Checks", f"C{rr}")
        res = val("Checks", f"D{rr}")
        if lab is None:
            continue
        print(f"  [{str(res):>5}] {str(lab)[:56]:<56} value={v} expected={exp}")
        if res != "OK":
            failures.append(f"check failed: {lab} (value={v}, expected={exp})")

    # Where the two axes cross: the interesting cells.
    print()
    print("Axis-crossing cells")
    for off, lab in [(2, "T1"), (3, "T2"), (4, "T3"), (5, "T4"), (6, "T5")]:
        rr = meta["seg_total_rows"][3] - 7 + off
        n = val("Increase by segment", f"B{rr}")
        eur = val("Increase by segment", f"H{rr}")
        n_s = f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)
        eur_s = f"{eur:,.2f}" if isinstance(eur, (int, float)) else str(eur)
        print(f"  {lab}: lines={n_s:>7}  billed EUR {eur_s:>15}")

    # Excluded sheet must be populated and add up.
    print()
    print("Excluded")
    for rr in range(5, 22):
        lab = val("Excluded", f"A{rr}")
        n = val("Excluded", f"B{rr}")
        eur = val("Excluded", f"D{rr}")
        if lab is None:
            continue
        eur_s = f"{eur:,.2f}" if isinstance(eur, (int, float)) else str(eur)
        n_s = f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)
        print(f"  {str(lab)[:52]:<52} lines={n_s:>7}  billed EUR {eur_s:>15}")

    # Error-value scan over the whole visible surface.
    print()
    print("Error-value scan")
    bad = []
    for nm in ["Read me", "Overview", "Legend", "Increase by segment",
               "Increase by class", "Israel", "CIS", "Excluded", "Checks"]:
        used = retry(lambda nm=nm: wb.Worksheets(nm).UsedRange)
        data = retry(lambda used=used: used.Value)
        if data is None:
            continue
        for row in (data if isinstance(data, tuple) else (data,)):
            cells = row if isinstance(row, tuple) else (row,)
            for cell in cells:
                if isinstance(cell, str) and any(
                        e in cell for e in ("#REF!", "#VALUE!", "#DIV/0!", "#NAME?",
                                            "#N/A", "#NUM!", "Err:")):
                    bad.append(f"{nm}: {cell}")
    if bad:
        failures.extend(bad[:20])
        print(f"  {len(bad)} error values found")
    else:
        print("  none")

    # PN data spot checks: the computed columns must be live, not blank.
    print()
    print("PN data spot checks")
    ws_pn = wb.Worksheets("PN data")
    total_pn = ws_pn.UsedRange.Rows.Count
    print(f"  used rows: {total_pn:,}")
    for rr in (2, 3, total_pn // 2, total_pn - 1, total_pn):
        pn = ws_pn.Cells(rr, 5).Value
        step = ws_pn.Cells(rr, 15).Value
        idx = ws_pn.Cells(rr, 19).Value
        zone = ws_pn.Cells(rr, 25).Value
        kind = ws_pn.Cells(rr, 26).Value
        action = ws_pn.Cells(rr, 28).Value
        print(f"  row {rr}: pn={pn} step={step} index={idx} zone={zone} "
              f"kind={kind} action={action}")
        if not isinstance(step, (int, float)):
            failures.append(f"PN row {rr}: step is not numeric ({step!r})")
        if zone is None or action is None:
            failures.append(f"PN row {rr}: zone or action is blank")
    if total_pn != meta["last_pn_row"]:
        failures.append(f"PN data rows {total_pn} != expected {meta['last_pn_row']}")

finally:
    if wb is not None:
        wb.Close(SaveChanges=False)
    excel.Quit()

print()
print("=" * 78)
if failures:
    print(f"FAILED ({len(failures)}):")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("SPEC_BASIS_VERIFY_OK - every formula recalculates, every check reads OK, "
      "and the headline reconciles to 5.9616% / EUR 1,652,140.71")
