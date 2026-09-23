"""_b_seam_diag2.py -- does re-basing reconcile 2025 exactly on r54 and r90?"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
V19W = CUR + r"\ISUZU_UIO_Overview_2026.xlsx"
YEARS = list(range(1990, 2031)); FY = [2026, 2027, 2028, 2029, 2030]
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c,a): return c.get(a,0.0) if a>=1 else 0.0

wb = openpyxl.load_workbook(V19W, data_only=True); ws = wb["1.UIO Overview"]
COLS = {y: 7+(y-1990) for y in YEARS}

def diag(r, c, tag):
    ser = {y: float(ws.cell(r, COLS[y]).value or 0) for y in YEARS}
    print("=" * 104)
    print("r%d %s   series 2025 = %.0f" % (r, tag, ser[2025]))
    rows = []
    for seam in (1990, None):
        if seam is None:
            # the material rule
            R0 = {}
            for t in YEARS:
                R0[t] = ser[t] - sum(R0[v]*S(c, t-v+1) for v in YEARS if 1990 <= v < t)
            seam2 = 1990
            for t in range(1991, 2026):
                if ser[t] > 0 and R0[t] < -1.0:
                    seam2 = t; break
            seam = seam2
        R = {}
        for t in YEARS:
            if t < seam: R[t] = 0.0; continue
            R[t] = ser[t] - sum(R[v]*S(c, t-v+1) for v in YEARS if seam <= v < t)
        negs = [(t, round(R[t],1)) for t in YEARS if R[t] < 0]
        for v in YEARS:
            if R[v] < 0: R[v] = 0.0
        reb = sum(R[v]*S(c, 2026-v) for v in YEARS if v <= 2025)
        resid = ser[2025] - reb
        oldest = min([v for v in YEARS if S(c, 2026-v) > 0] or [2025])
        add = resid / S(c, 2026-oldest) if S(c, 2026-oldest) else 0.0
        if abs(resid) > 0.5 and ser[2025] > 0:
            R[oldest] += add
        stock26 = sum(R[v]*S(c, 2026-v+1) for v in range(1990, 2026))
        rows.append((seam, negs, reb, resid, oldest, add, stock26))
    for seam, negs, reb, resid, oldest, add, stock26 in rows:
        print("  seam %-5s | negatives %-2d %-60s" % (
            seam, len(negs), str(negs)[:60]))
        print("             rebuild2025 %9.1f  series %7.0f  residual %+9.1f  -> vintage %d %+.0f" % (
            reb, ser[2025], resid, oldest, add))
        print("             2026 state = %9.1f" % stock26)

diag(90, LCV, "CYPRUS LCV")
diag(54, LCV, "PORTUGL LCV")
diag(88, CV_DEV, "CYPRUS CV LD")
diag(51, CV_DEV, "PORTUGL CV LD")
diag(26, CV_DEV, "IRELAND CV LD")
wb.close()
