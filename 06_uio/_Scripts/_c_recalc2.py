"""_c_recalc2.py - recalculate candidate c Grand Total via Excel COM (Cells(row,col))."""
import io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import win32com.client

CAND = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22c.xlsx"
FYCOL = {2026: 43, 2027: 44, 2028: 45, 2029: 46, 2030: 47}
excel = win32com.client.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
excel.ScreenUpdating = False
ok = False
rr = None
try:
    rr = excel.Workbooks.Open(CAND, UpdateLinks=0, ReadOnly=False)
    time.sleep(1.0)
    excel.CalculateFullRebuild()
    time.sleep(0.5)
    rr.Save()
    sh = rr.Worksheets("1.UIO Overview")
    v = [sh.Cells(2, FYCOL[y]).Value for y in (2026, 2027, 2028, 2029, 2030)]
    print("recalculated; Grand Total cached = %s" % [round(float(x), 2) for x in v])
    # a couple of spot cells
    for r in (54, 69, 88, 90):
        print("  r%-3d AQ:AU = %s" % (r, [sh.Cells(r, FYCOL[y]).Value for y in (2026, 2027, 2028, 2029, 2030)]))
    ok = True
except Exception as ex:
    print("FAILED: %s" % ex)
finally:
    if rr is not None:
        try: rr.Close(SaveChanges=False)
        except Exception: pass
    try: excel.Quit()
    except Exception: pass
print("done" if ok else "NOT DONE")
