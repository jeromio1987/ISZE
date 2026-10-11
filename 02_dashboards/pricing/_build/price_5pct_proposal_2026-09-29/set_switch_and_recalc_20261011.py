"""Set one or more cells in a workbook through Excel itself, recalculate, save, and close that Excel.

Used to move a switch without an openpyxl round trip (which would drop the cached formula results and
the chart on the 'Dealer response' sheet).

Run:  python set_switch_and_recalc_20261011.py <xlsx> "Summary!B76=1" ["Pricing grid!B26=1.2" ...]
"""
import os
import sys
import tempfile
import time
from pathlib import Path

import win32com

_gen = os.path.join(tempfile.gettempdir(), "isze_recalc_gen_py")
os.makedirs(_gen, exist_ok=True)
win32com.__gen_path__ = _gen
import win32com.gen_py  # noqa: E402

win32com.gen_py.__path__ = [_gen]

import pythoncom  # noqa: E402
import pywintypes  # noqa: E402
import win32api  # noqa: E402
import win32con  # noqa: E402
import win32process  # noqa: E402
import win32com.client.dynamic  # noqa: E402

path = str(Path(sys.argv[1]).resolve())
sets = []
for a in sys.argv[2:]:
    ref, _, val = a.partition("=")
    sheet, _, cell = ref.rpartition("!")
    try:
        val = float(val) if "." in val else int(val)
    except ValueError:
        pass
    sets.append((sheet, cell, val))

pythoncom.CoInitialize()
clsid = pywintypes.IID("{00024500-0000-0000-C000-000000000046}")
disp = pythoncom.CoCreateInstanceEx(clsid, None, pythoncom.CLSCTX_LOCAL_SERVER, None, (pythoncom.IID_IDispatch,))[0]
xl = win32com.client.dynamic.Dispatch(disp)
pid = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
xl.Visible = False
xl.DisplayAlerts = False
BUSY = (-2147418111, -2147417846)


def retry(fn, limit=900):
    for _ in range(limit):
        try:
            return fn()
        except pywintypes.com_error as e:
            if e.hresult not in BUSY:
                raise
            time.sleep(1)
    raise TimeoutError("Excel stayed busy")


try:
    t0 = time.time()
    wb = retry(lambda: xl.Workbooks.Open(path, UpdateLinks=0, ReadOnly=False, AddToMru=False))
    retry(lambda: setattr(xl, "Calculation", -4135))        # xlCalculationManual: one recalculation, not one per cell
    for sheet, cell, val in sets:
        retry(lambda s=sheet, c=cell, v=val: wb.Worksheets(s).Range(c).__setattr__("Value", v))
        print(f"set {sheet}!{cell} = {val!r}")
    retry(lambda: xl.CalculateFull())
    while retry(lambda: xl.CalculationState) != 0:
        time.sleep(1)
    retry(lambda: wb.Save())
    retry(lambda: wb.Close(False))
    print(f"set, recalculated and saved in {time.time() - t0:.1f}s: {path}")
finally:
    try:
        xl.Quit()
    except Exception:
        pass
    del xl, disp
    pythoncom.CoUninitialize()
    time.sleep(1.5)
    try:
        h = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
        win32api.TerminateProcess(h, 0)
        print(f"closed leftover Excel process {pid}")
    except pywintypes.error:
        pass
