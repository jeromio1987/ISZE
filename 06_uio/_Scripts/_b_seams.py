"""_b_seams.py -- analyse r79 / r54 / r90 against the IML registration source."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

SCR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts"
CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
CAND = CUR + r"\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx"

vol = json.load(open(SCR + r"\_b_iml_vol.json"))
CV = {int(k): {int(y): v for y, v in d.items()} for k, d in vol['cv_vol'].items()}
LCV = {int(k): {int(y): v for y, v in d.items()} for k, d in vol['lcv_vol'].items()}

CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCVC = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c,a): return c.get(a,0.0) if a>=1 else 0.0

wb = openpyxl.load_workbook(CAND, data_only=True)
ws = wb["1.UIO Overview"]
COLS = {y: 7 + (y-1990) for y in range(1990, 2031)}
YEARS = list(range(1990, 2031))

def series(r):
    return {y: ws.cell(r, COLS[y]).value for y in YEARS}

def back_solve(ser, c, start):
    R = {}
    for t in YEARS:
        if t < start:
            R[t] = 0.0; continue
        R[t] = (ser.get(t) or 0.0) - sum(R[v]*S(c, t-v+1) for v in YEARS if start <= v < t)
    return R

CASES = [
    (79, 230, "CV",  CV, "GREECE CV LD  (Petros Petropoulos)"),
    (54, 217, "LCV", LCV, "PORTUGL LCV LCV (Imotors)"),
    (90, 233, "LCV", LCV, "CYPRUS LCV LCV (Loutsios & Sons)"),
    (88, 233, "CV",  CV, "CYPRUS CV LD   (Loutsios & Sons)"),
    (51, 217, "CV",  CV, "PORTUGL CV LD  (Imotors)"),
    (26, 206, "CV",  CV, "IRELAND CV LD (Isuzu Ireland)"),
    (33, 208, "CV",  CV, "BELGIUM CV LD  (IBX)"),
]

for r, code, mt, src, label in CASES:
    c = CV_DEV if mt == "CV" else LCVC
    ser = {y: float(series(r).get(y) or 0.0) for y in YEARS}
    print("=" * 104)
    print("r%-3d %s   ctry code %d" % (r, label, code))
    R = back_solve(ser, c, 1990)
    neg = {t: round(R[t], 1) for t in range(1990, 2026) if R[t] < 0}
    print("  A) back-solve from 1990 -> negative implied births:", neg if neg else "none")
    regs = {y: src.get(code, {}).get(y) for y in range(1990, 2027)}
    print("  IML Vol registration series (source):")
    print("    ", {y: regs[y] for y in range(1990, 2027) if regs.get(y) is not None})
    # rebuild from IML regs and compare to candidate history
    print("  rebuild from IML regs vs candidate history:")
    for y in range(1990, 2026):
        want = ser[y]
        got = sum((regs.get(v) or 0.0)*S(c, y-v+1) for v in range(1990, y+1))
        flag = "" if abs(got-want) < 0.6 else "  <-- diff %+.1f" % (got-want)
        print("    %d  IML-rebuild %9.1f   candidate %9.1f%s" % (y, got, want, flag))
wb.close()
