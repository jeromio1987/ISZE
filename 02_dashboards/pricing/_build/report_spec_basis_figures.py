# -*- coding: utf-8 -*-
"""Read the delivered, recalculated workbook and print the figures for the report."""
import io
import json
import sys
import time
from pathlib import Path

import win32com.client as win32

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
XLSX = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Simulation_Spec_Basis.xlsx"


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
    seg = wb.Worksheets("Increase by segment")

    blocks = []
    for rr in range(1, seg.UsedRange.Rows.Count + 1):
        lab = retry(lambda rr=rr: seg.Range(f"A{rr}").Value)
        if isinstance(lab, str) and lab in (
                "Captured-demand position",
                "How that position was arrived at",
                "Position against the independent aftermarket (price index)",
                "Evidence behind the benchmark",
                "The action the two gates point to (sign only - no change is made)"):
            blocks.append((rr, lab))
    print("=" * 78)
    print("SEGMENTATION CLASS COUNTS (recalculated)")
    print("=" * 78)
    for i, (rr, lab) in enumerate(blocks):
        end = blocks[i + 1][0] if i + 1 < len(blocks) else rr + 12
        print()
        print(lab)
        for r2 in range(rr + 2, end):
            v = retry(lambda r2=r2: seg.Range(f"A{r2}").Value)
            n = retry(lambda r2=r2: seg.Range(f"B{r2}").Value)
            step = retry(lambda r2=r2: seg.Range(f"G{r2}").Value)
            billed = retry(lambda r2=r2: seg.Range(f"H{r2}").Value)
            if v is None:
                continue
            n_s = f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)
            st_s = f"{step:,.2f}" if isinstance(step, (int, float)) else str(step)
            bl_s = f"{billed:,.2f}" if isinstance(billed, (int, float)) else str(billed)
            print(f"  {str(v):<32} lines={n_s:>7}  step=EUR {st_s:>14}  "
                  f"billed=EUR {bl_s:>15}")

    print()
    print("=" * 78)
    print("LANE TABLE")
    print("=" * 78)
    ov = wb.Worksheets("Overview")
    for rr in range(6, 11):
        lab = retry(lambda rr=rr: ov.Range(f"A{rr}").Value)
        if lab is None:
            continue
        print(f"  {str(lab):<34} lines={retry(lambda rr=rr: ov.Range(f'B{rr}').Value)}"
              f"  qty={retry(lambda rr=rr: ov.Range(f'C{rr}').Value)}"
              f"  move={retry(lambda rr=rr: ov.Range(f'H{rr}').Value)}"
              f"  step={retry(lambda rr=rr: ov.Range(f'I{rr}').Value)}")
finally:
    if wb is not None:
        wb.Close(SaveChanges=False)
    excel.Quit()
