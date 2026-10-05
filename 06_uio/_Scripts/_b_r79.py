"""_b_r79.py -- diagnose r79 exactly, and read IML CV Vol for Greece / Cyprus / Portugal."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

SCR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts"
CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
CAND = CUR + r"\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx"
IML = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\IML calculation (1).xlsx"

# ---------- 1) IML CV/LCV Vol with N/F/C sub-columns kept separate
def parse_vol(ws):
    """row3 = years (merged label every 3 cols); row4 = N/F/C; row5+ = codes."""
    hdr = {}          # col -> (year, bucket)
    for c in range(2, ws.max_column + 1):
        v = ws.cell(3, c).value
        b = ws.cell(4, c).value
        # merged cells: carry the last seen year forward
        if isinstance(v, (int, float)) and 1990 <= v <= 2035:
            last_year = int(v)
        else:
            v2 = None
        yr = int(v) if isinstance(v, (int, float)) and 1990 <= v <= 2035 else None
        hdr[c] = (yr, b)
    # forward-fill years (merged header)
    cury = None
    for c in sorted(hdr):
        y, b = hdr[c]
        if y is not None:
            cury = y
        hdr[c] = (cury, b)
    out = {}
    for r in range(5, ws.max_row + 1):
        raw = ws.cell(r, 1).value
        code = int(raw) if isinstance(raw, (int, float)) else (int(raw) if isinstance(raw, str) and raw.strip().isdigit() else None)
        if code is None:
            continue
        d = {}
        for c, (y, b) in hdr.items():
            v = ws.cell(r, c).value
            if isinstance(v, (int, float)) and y:
                key = str(b).strip() if isinstance(b, str) else '?'
                d.setdefault(y, {})[key] = float(v)
        if d:
            out.setdefault(code, {}).update(d)
    return out

wb = openpyxl.load_workbook(IML, data_only=True)
CVVOL = parse_vol(wb["6.CV Vol"])
LCVVOL = parse_vol(wb["7.LCV Vol"])
# country names
names = {}
for r in range(1, 260):
    for c in range(1, 7):
        v = wb["4.Ctry Code"].cell(r, c).value
        if isinstance(v, (int, float)):
            row = [wb["4.Ctry Code"].cell(r, cc).value for cc in range(1, 7)]
            names[int(v)] = " | ".join(str(x) for x in row if x is not None)
wb.close()

print("codes present:", len(CVVOL), "| name lookup sample:", {k: names.get(k) for k in (205, 206, 208, 217, 230, 233)})
for code in (230, 233, 217):
    print("\n### code %d  %s  --- IML CV Vol by bucket ---" % (code, names.get(code)))
    for y in range(2013, 2027):
        print("   %d  %s" % (y, CVVOL.get(code, {}).get(y)))
    print("   LCV:")
    for y in range(2013, 2027):
        print("   %d  %s" % (y, LCVVOL.get(code, {}).get(y)))

# ---------- 2) reproduce the engine for r79 exactly
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCVC = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c,a): return c.get(a,0.0) if a>=1 else 0.0
YEARS = list(range(1990, 2031))
FY = [2026, 2027, 2028, 2029, 2030]

wb = openpyxl.load_workbook(CAND, data_only=True)
ws = wb["1.UIO Overview"]
COLS = {y: 7 + (y-1990) for y in YEARS}
ser = {y: float(ws.cell(79, COLS[y]).value or 0) for y in YEARS}
wb.close()

def detect_seam(series, c):
    R = {}
    for t in YEARS:
        R[t] = series[t] - sum(R[v]*S(c, t-v+1) for v in YEARS if 1990 <= v < t)
    for t in range(1991, 2026):
        if series[t] > 0 and R[t] < 0 and abs(R[t]) > 0.25*series[t]:
            return t
    return 1990

c = CV_DEV
seam = detect_seam(ser, c)
print("\n### r79 engine reproduction ###")
print("  detected seam:", seam)
R = {}
for t in YEARS:
    if t < seam:
        R[t] = 0.0; continue
    R[t] = ser[t] - sum(R[v]*S(c, t-v+1) for v in YEARS if seam <= v < t)
print("  raw R (1990-2025), non-zero only:")
print("   ", {t: round(R[t],2) for t in YEARS if t <= 2025 and abs(R[t]) > 1e-9})
clipped = 0
for v in YEARS:
    if R[v] < 0:
        R[v] = 0.0; clipped += 1
print("  clipped:", clipped)
reb2025 = sum(R[v]*S(c, 2026-v) for v in YEARS if v <= 2025)
resid = ser[2025] - reb2025
print("  rebuild 2025 = %.2f ; series 2025 = %.0f ; residual = %.2f" % (reb2025, ser[2025], resid))
oldest = min([v for v in YEARS if S(c, 2026-v) > 0] or [2025])
print("  oldest live vintage in 2026 = %d (age %d, S=%.2f)" % (oldest, 2026-oldest, S(c, 2026-oldest)))
if abs(resid) > 0.5 and ser[2025] > 0:
    R[oldest] += resid / S(c, 2026 - oldest)
print("  R after residual absorb:", {t: round(R[t],2) for t in YEARS if t <= 2025 and abs(R[t]) > 1e-9})

regs = {2026: 20, 2027: 20, 2028: 20, 2029: 20, 2030: 20}
print("  roll-forward with flat 20/yr:")
for t in FY:
    stock = sum(R[v]*S(c, t-v+1) for v in range(1990, t))
    R[t] = regs[t]
    print("    %d  stock %.3f  + new %d*1.0  = UIO %.3f" % (t, stock, regs[t], stock + regs[t]*S(c,1)))
print("  state contribution by vintage in 2026:")
contrib = {v: R[v]*S(c, 2026-v+1) for v in YEARS if v <= 2025 and abs(R[v]) > 1e-9}
print("   ", {v: round(x,2) for v, x in contrib.items()})
print("  sum of state in 2026 = %.2f" % sum(contrib.values()))
print("  same-vintage decay path (absolute decrement per year):")
for v in sorted(contrib, key=lambda z: -contrib[z])[:4]:
    path = [R[v]*S(c, 2026+i-v+1) for i in range(5)]
    print("    vintage %d: %s" % (v, [round(x,2) for x in path]))
