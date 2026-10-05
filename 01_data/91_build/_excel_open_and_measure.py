"""Open the rebuilt workbook in Excel and MEASURE whether the rows are normal height.

The defect was ~11,000 rows auto-fitted to their tallest wrapped content. Row height is
the observable symptom, and Excel is the only thing that computes it. This reads the
actual rendered row heights back from Excel.
"""
import time
from pathlib import Path

XL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing"
          r"\ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx")

print("=" * 94)
print("OPENING THE REBUILT WORKBOOK IN EXCEL: FREEZE PANES, SCROLLABLE ROWS, SOURCES")
print("=" * 94)
print(f"  file: {XL.name}  ({XL.stat().st_size:,} bytes)")
import win32com.client as w                                              # noqa: E402
app = w.Dispatch("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
opened = False
try:
    wbk = app.Workbooks.Open(str(XL))
    opened = True
    print("  OPENED OK:", wbk.Name)
    print("  sheets:", [s.Name for s in wbk.Sheets])
    time.sleep(8)
    print()
    print(f"  {'sheet':<9}{'used rows':>10}{'FreezePanes':>13}{'SplitRow':>10}"
          f"{'SplitCol':>10}{'row2 h':>8}{'row500 h':>9}")
    for nm in ("Legends", "PR00", "UTI", "UMI", "CIS"):
        ws = wbk.Sheets(nm)
        wbk.Activate()
        ws.Activate()
        win = app.ActiveWindow
        used = ws.UsedRange.Rows.Count
        h2 = ws.Rows(2).RowHeight
        h500 = ws.Rows(500).RowHeight if used > 500 else 0
        print(f"  {nm:<9}{used:>10,}{str(win.FreezePanes):>13}"
              f"{win.SplitRow:>10}{win.SplitColumn:>10}{h2:>8.1f}{h500:>9.1f}")
    print()
    # the freeze must be one frame, not a bottom row
    for nm in ("PR00", "UTI", "UMI", "CIS"):
        ws = wbk.Sheets(nm)
        ws.Activate()
        win = app.ActiveWindow
        used = ws.UsedRange.Rows.Count
        scrollable = used - win.SplitRow
        print(f"  {nm}: FreezePanes={win.FreezePanes}  SplitRow={win.SplitRow}  "
              f"scrollable rows={scrollable:,}")
    print()
    # the Source column, as Excel sees it
    for nm in ("PR00", "UTI", "UMI", "CIS"):
        ws = wbk.Sheets(nm)
        used = ws.UsedRange.Rows.Count
        seen = set()
        for r in range(2, min(used, 4000)):
            if ws.Cells(r, 1).Value == "TOTAL":
                break
            v = ws.Cells(r, 4).Value
            seen.add(v if v not in (None, "") else "(blank)")
        print(f"  {nm}: Source distinct values (first 4000 rows) = {sorted(map(str, seen))}")
    print()
    for nm in ("PR00", "UTI", "UMI", "CIS"):
        ws = wbk.Sheets(nm)
        used = ws.UsedRange.Rows.Count
        found = None
        for r in range(1, used + 30):
            lab = ws.Cells(r, 1).Value
            if lab and "whole market" in str(lab):
                found = (str(lab)[:34], round(ws.Cells(r, 2).Value, 6))
                break
        print(f"  {nm}: {found}")
    wbk.Close(SaveChanges=False)
except Exception as e:
    print(f"  COULD NOT OPEN -> {type(e).__name__}: {e}")
finally:
    try:
        app.Quit()
    except Exception:
        pass
print()
print("EXCEL_OPEN_CONFIRMED" if opened else "EXCEL_OPEN_NOT_AVAILABLE_HERE")
