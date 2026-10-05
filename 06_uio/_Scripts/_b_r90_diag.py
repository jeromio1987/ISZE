"""_b_r90_diag.py -- why does the seam repair inflate r90 Cyprus LCV by +55% in one year?"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
V19W = CUR + r"\ISUZU_UIO_Overview_2026.xlsx"
YEARS = list(range(1990, 2031)); FY = [2026, 2027, 2028, 2029, 2030]
LCV = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c,a): return c.get(a,0.0) if a>=1 else 0.0
c = LCV

wb = openpyxl.load_workbook(V19W, data_only=True); ws = wb["1.UIO Overview"]
COLS = {y: 7+(y-1990) for y in YEARS}
ser = {y: float(ws.cell(90, COLS[y]).value or 0) for y in YEARS}
wb.close()

def bs(start):
    R = {}
    for t in YEARS:
        if t < start: R[t] = 0.0; continue
        R[t] = ser[t] - sum(R[v]*S(c, t-v+1) for v in YEARS if start <= v < t)
    return R

for seam in (1990, 2014):
    print("=" * 100)
    print("SEAM = %s" % seam)
    R = bs(seam)
    raw = {t: round(R[t], 1) for t in range(2010, 2026) if abs(R[t]) > 1e-9}
    print("  raw implied cohorts 2010-2025:", raw)
    negs = [t for t in YEARS if R[t] < 0]
    print("  negative cohorts:", [(t, round(R[t],1)) for t in negs])
    for v in YEARS:
        if R[v] < 0: R[v] = 0.0
    reb = sum(R[v]*S(c, 2026-v) for v in YEARS if v <= 2025)
    resid = ser[2025] - reb
    print("  rebuild 2025 = %.2f ; series 2025 = %.0f ; RESIDUAL = %.2f" % (reb, ser[2025], resid))
    oldest = min([v for v in YEARS if S(c, 2026-v) > 0] or [2025])
    print("  oldest live vintage in 2026 = %d (age %d, S=%.2f)" % (oldest, 2026-oldest, S(c, 2026-oldest)))
    if abs(resid) > 0.5 and ser[2025] > 0:
        add = resid / S(c, 2026-oldest)
        print("  -> residual absorbed into vintage %d as %+.1f extra cohort units" % (oldest, add))
        R[oldest] += add
    live = {v: round(R[v],1) for v in YEARS if v <= 2025 and abs(R[v]) > 1e-9}
    print("  final state (vintages):", live)
    stock26 = sum(R[v]*S(c, 2026-v+1) for v in range(1990, 2026))
    print("  state contribution to 2026 = %.1f" % stock26)
    # with the same smoothed input, what does 2026-2030 look like?
    prof = [899.87, 879.84, 859.97, 840.19, 840.39]  # from the A->B report (r54) not used; placeholder
print()
print("NOTE: placeholder input not used; the point is the 2026 state level, above.")
