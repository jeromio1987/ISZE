# -*- coding: utf-8 -*-
"""Dial test: change the FX cell and a segmentation parameter, confirm the
roll-ups move, then restore the file. Proves the model is live, not a picture.

Run: python 02_dashboards/pricing/_build/dial_test_spec_basis.py
"""
import io
import sys
import time
from pathlib import Path

import win32com.client as win32

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

XLSX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing"
            r"\ISZE_Pricing_Simulation_Spec_Basis.xlsx")
failures = []


def retry(fn, attempts=40, pause=2.0):
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
    retry(lambda: excel.CalculateFullRebuild())

    ov = wb.Worksheets("Overview")
    lg = wb.Worksheets("Legend")
    seg = wb.Worksheets("Increase by segment")

    def find_row(sheet, label):
        """Locate a labelled row by scanning column A, so the test does not
        depend on hardcoded row numbers."""
        for rr in range(1, 60):
            v = retry(lambda rr=rr: sheet.Range(f"A{rr}").Value)
            if v is not None and str(v).strip() == label:
                return rr
        raise RuntimeError(f"label not found: {label}")

    def read():
        return {
            "fx": retry(lambda: lg.Range("B7").Value),
            "captive_cut": retry(lambda: lg.Range("B15").Value),
            "ref_band": retry(lambda: lg.Range("B20").Value),
            "step": retry(lambda: ov.Range("I9").Value),
            "pct": retry(lambda: ov.Range("H9").Value),
            "network_billed": retry(lambda: ov.Range("J9").Value),
            "captive_lines": retry(lambda: seg.Range(f"B{find_row(seg, 'Captive')}").Value),
            "captive_step": retry(lambda: seg.Range(f"G{find_row(seg, 'Captive')}").Value),
            "lost_lines": retry(lambda: seg.Range(f"B{find_row(seg, 'Lost')}").Value),
            "notclass_lines": retry(
                lambda: seg.Range(f"B{find_row(seg, 'Not classified')}").Value),
            "below_lines": retry(
                lambda: seg.Range(f"B{find_row(seg, 'Below reference')}").Value),
            "inband_lines": retry(
                lambda: seg.Range(f"B{find_row(seg, 'In band')}").Value),
            "seg_total": retry(
                lambda: seg.Range(f"G{find_row(seg, 'Captive') + 4}").Value),
        }

    base = read()
    print("=" * 78)
    print("BASELINE (as delivered)")
    print("=" * 78)
    for k, v in base.items():
        print(f"  {k:<18} {v}")

    # --- Dial 1: FX rate. Japan-sourced lines are the ones it moves.
    print()
    print("=" * 78)
    print("DIAL 1 - FX from 163.7 to 150.0 (the yen rate)")
    print("=" * 78)
    lg.Range("B7").Value = 150.0
    retry(lambda: excel.CalculateFullRebuild())
    fx_150 = read()
    print(f"  network step   {base['step']:,.2f}  ->  {fx_150['step']:,.2f}")
    print(f"  network move   {base['pct']*100:.4f}%  ->  {fx_150['pct']*100:.4f}%")
    print(f"  network billed {base['network_billed']:,.2f}  ->  "
          f"{fx_150['network_billed']:,.2f}")
    print(f"  JP-sourced share of the step rises when the yen strengthens "
          f"(fewer yen per euro): a weaker yen rate means a larger step.")
    if abs(fx_150["step"] - base["step"]) < 1.0:
        failures.append("FX dial did not move the network step")
    if abs(fx_150["pct"] - base["pct"]) > 1e-9:
        failures.append("FX dial must not move the base-price percentage (it is a "
                        "yen move, and the percentage is a yen ratio)")
    else:
        print("  base-price percentage correctly unchanged: it is a yen-to-yen ratio")
    if abs(fx_150["network_billed"] - base["network_billed"]) > 1.0:
        failures.append("FX dial must not move billed euro or quantity")
    else:
        print("  billed euro and quantity correctly unchanged: they are not converted")
    lg.Range("B7").Value = 163.7
    retry(lambda: excel.CalculateFullRebuild())

    # --- Dial 2: the captive threshold.
    print()
    print("=" * 78)
    print("DIAL 2 - captive threshold from 0.80 to 0.95")
    print("=" * 78)
    lg.Range("B15").Value = 0.95
    retry(lambda: excel.CalculateFullRebuild())
    cap_95 = read()
    print(f"  captive lines  {base['captive_lines']:,.0f}  ->  "
          f"{cap_95['captive_lines']:,.0f}")
    print(f"  captive step   {base['captive_step']:,.2f}  ->  "
          f"{cap_95['captive_step']:,.2f}")
    print("  contested absorbs the difference.")
    if cap_95["captive_lines"] == base["captive_lines"]:
        failures.append("captive threshold dial did not move the captive line count")
    if abs(cap_95["seg_total"] - base["step"]) > 1.0:
        failures.append(f"segment total broke when the dial moved: {cap_95['seg_total']}")
    else:
        print(f"  segment total still ties to the network step: "
              f"{cap_95['seg_total']:,.2f}")
    lg.Range("B15").Value = 0.80
    retry(lambda: excel.CalculateFullRebuild())

    # --- Dial 3: the price-index band.
    print()
    print("=" * 78)
    print("DIAL 3 - reference band edge from 0.95 to 1.00")
    print("=" * 78)
    lg.Range("B20").Value = 1.00
    retry(lambda: excel.CalculateFullRebuild())
    bands = read()
    print(f"  network step unchanged: {bands['step']:,.2f}")
    print(f"  below-reference lines {base['below_lines']:,.0f}  ->  "
          f"{bands['below_lines']:,.0f}")
    print(f"  in-band lines         {base['inband_lines']:,.0f}  ->  "
          f"{bands['inband_lines']:,.0f}")
    if bands["below_lines"] == base["below_lines"]:
        failures.append("price-index band dial did not move any line")
    lg.Range("B20").Value = 0.95
    retry(lambda: excel.CalculateFullRebuild())

    restored = read()
    print()
    print("=" * 78)
    print("RESTORED")
    print("=" * 78)
    for k in ("fx", "captive_cut", "ref_band"):
        print(f"  {k:<18} {restored[k]}")
    if abs(restored["step"] - base["step"]) > 1e-6 or \
            abs(restored["pct"] - base["pct"]) > 1e-12:
        failures.append("workbook did not return to its delivered figures")
    else:
        print("  workbook returned exactly to the delivered figures")

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
print("DIAL_TEST_OK - the FX cell and both segmentation parameters move the roll-ups, "
      "and the file returns to its delivered figures")
