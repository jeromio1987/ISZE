"""Render the top of each sheet to PNG (Excel PDF export of a scratch copy, then PyMuPDF) for a visual check."""
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import fitz
import win32com

_gen = os.path.join(tempfile.gettempdir(), "isze_recalc_gen_py")
os.makedirs(_gen, exist_ok=True)
win32com.__gen_path__ = _gen
import win32com.gen_py  # noqa: E402

win32com.gen_py.__path__ = [_gen]
import pythoncom  # noqa: E402
import pywintypes  # noqa: E402
import win32com.client.dynamic  # noqa: E402

src = Path(sys.argv[1])
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
tmp = Path(tempfile.gettempdir()) / "isze_aim_level_qa.xlsx"
shutil.copy(src, tmp)
AREAS = {"Read me": "A1:A32", "Settings": "A1:R56", "By L1": "A1:V33", "By L3": "A1:X40", "Parts": "A1:AB45",
         "Checks": "A1:D18"}
pythoncom.CoInitialize()
disp = pythoncom.CoCreateInstanceEx(pywintypes.IID("{00024500-0000-0000-C000-000000000046}"), None,
                                    pythoncom.CLSCTX_LOCAL_SERVER, None, (pythoncom.IID_IDispatch,))[0]
xl = win32com.client.dynamic.Dispatch(disp)
xl.Visible, xl.DisplayAlerts = False, False
try:
    wb = xl.Workbooks.Open(str(tmp), UpdateLinks=0, ReadOnly=False, AddToMru=False)
    for name, area in AREAS.items():
        ws = wb.Worksheets(name)
        ps = ws.PageSetup
        ps.PrintArea = area
        ps.Orientation = 2
        ps.Zoom = False
        ps.FitToPagesWide = 1
        ps.FitToPagesTall = 1
        pdf = out / f"{name.replace(' ', '_')}.pdf"
        ws.ExportAsFixedFormat(0, str(pdf))
        doc = fitz.open(pdf)
        doc[0].get_pixmap(dpi=150).save(str(out / f"{name.replace(' ', '_')}.png"))
        doc.close()
        pdf.unlink()
        print("rendered", name)
    wb.Close(False)
finally:
    xl.Quit()
    time.sleep(1)
    pythoncom.CoUninitialize()
