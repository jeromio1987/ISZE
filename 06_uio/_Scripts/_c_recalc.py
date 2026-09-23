"""_c_recalc.py - recalculate the candidate c Grand Total cached values via Excel COM (retry)."""
import io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import win32com.client

CAND = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22c.xlsx"
FYCOL = {2026: 43, 2027: 44, 2028: 45, 2029: 46, 2030: 47}

excel = win32com.client.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
excel.ScreenUpdating = False
last = None
for attempt in range(6):
    rr = None
    try:
        rr = excel.Workbooks.Open(CAND, UpdateLinks=0, ReadOnly=False)
        time.sleep(1.0)
        excel.CalculateFullRebuild()
        time.sleep(0.5)
        rr.Save()
        v = [rr.Worksheets("1.UIO Overview").Cell(2, FYCOL[y]).Value for y in (2026, 2027, 2028, 2029, 2030)]
        print("recalculated; Grand Total cached = %s" % [round(float(x), 2) for x in v])
        last = None
        break
    except Exception as ex:
        last = ex
        print("attempt %d failed: %s" % (attempt + 1, ex))
        time.sleep(3.0)
    finally:
        if rr is not None:
            try: rr.Close(SaveChanges=False)
            except Exception: pass
try:
    excel.Quit()
except Exception:
    pass
print("done" if last is None else "FAILED: %s" % last)
