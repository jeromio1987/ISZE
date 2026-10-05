"""Try to open the rebuilt workbook in Excel. Report honestly whether it opened.

The brief expects neither the parent agent nor Jerome to have a usable Excel here, and
to say so rather than imply a confirmation. This attempts the open on this machine and
prints what actually happened, including the failure if there is one.
"""
import os
import time
from pathlib import Path

XL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing"
          r"\ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx")

print("=" * 88)
print("ATTEMPTING TO OPEN THE REBUILT WORKBOOK IN EXCEL")
print("=" * 88)
print(f"  file: {XL}")
print(f"  size: {XL.stat().st_size:,} bytes")
try:
    import win32com.client as w
    print("  win32com: importable")
except Exception as e:
    print(f"  win32com NOT available -> {type(e).__name__}: {e}")
    print("  Cannot attempt the open. Reporting plainly, not implying a check.")
    raise SystemExit(0)

opened = False
try:
    app = w.Dispatch("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    print("  Excel application object created, version", app.Version)
    wbk = app.Workbooks.Open(str(XL))
    opened = True
    print("  OPENED OK:", wbk.Name)
    print("  sheets visible to Excel:", [s.Name for s in wbk.Sheets])
    # give it a moment, then read the headline values back through Excel itself
    time.sleep(6)
    for name in ("PR00", "UTI", "UMI", "CIS"):
        ws = wbk.Sheets(name)
        found = None
        for r in range(1, 40):
            lab = ws.Cells(r, 1).Value
            if lab and "whole market" in str(lab):
                found = (str(lab)[:52], ws.Cells(r, 2).Value)
                break
        print(f"    {name}: {found}")
    jb = wbk.Sheets("Legends")
    print("    Legends B6 (live rate) =", jb.Range("B6").Value,
          "| B8 (Japan discount) =", jb.Range("B8").Value)
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
