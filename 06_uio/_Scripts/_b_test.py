"""_b_test.py -- test the rounding hypothesis + seam variants against the candidate."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
V19W = CUR + r"\ISUZU_UIO_Overview_2026.xlsx"
CAND = CUR + r"\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx"
YEARS = list(range(1990, 2031))
FY = [2026, 2027, 2028, 2029, 2030]
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c,a): return c.get(a,0.0) if a>=1 else 0.0
def curve(mt): return LCV if str(mt) == 'LCV' else CV_DEV
OUT_OF_SCOPE={7,8}; LEAVE_AS_V19={22,24}; PLAN_ONLY_MD={27,52,80,89}
UK_LCV_REGS={2026:3020,2027:2400,2028:2400,2029:2400,2030:2400}

wb = openpyxl.load_workbook(V19W, data_only=True)
ws = wb["1.UIO Overview"]
COLS = {y: 7 + (y-1990) for y in YEARS}
ROWS = []
for r in range(7, 91):
    ROWS.append({'row': r, 'meta': [ws.cell(r, c).value for c in range(1, 7)],
                 'vals': {y: ws.cell(r, COLS[y]).value for y in YEARS}})
GT = {y: ws.cell(2, COLS[y]).value for y in YEARS}
wb.close()

def back_solve(series, c, start):
    R = {}
    for t in YEARS:
        if t < start:
            R[t] = 0.0; continue
        R[t] = series[t] - sum(R[v]*S(c, t-v+1) for v in YEARS if start <= v < t)
    return R

def detect_seam(series, c):                       # ORIGINAL (25% of series)
    R = back_solve(series, c, 1990)
    for t in range(1991, 2026):
        if series[t] > 0 and R[t] < 0 and abs(R[t]) > 0.25 * series[t]:
            return t
    return 1990

def detect_seam_material(series, c, abs_tol=1.0):
    """FIRST year whose implied cohort is a materially negative vehicle count.
    A cohort model cannot have negative sales; the seam is where the source switches."""
    R = back_solve(series, c, 1990)
    for t in range(1991, 2026):
        if series[t] > 0 and R[t] < -abs_tol:
            return t, R
    return 1990, R

def build_state(series, c, seam):
    R = back_solve(series, c, seam)
    clipped = 0
    for v in YEARS:
        if R[v] < 0:
            R[v] = 0.0; clipped += 1
    reb = sum(R[v]*S(c, 2026-v) for v in YEARS if v <= 2025)
    resid = series[2025] - reb
    if abs(resid) > 0.5 and series[2025] > 0:
        oldest = min([v for v in YEARS if S(c, 2026-v) > 0] or [2025])
        R[oldest] += resid / S(c, 2026-oldest)
    return R, clipped, resid

def regs_raw(v, round_first):
    out = {}
    for t in FY:
        x = (v.get(t) or 0) - (v.get(t-1) or 0)*0.97
        out[t] = round(x) if round_first else x
    return out

def smooth_keep_level(x):
    n = len(x); sm = []
    for i in range(n):
        if i == 0:       sm.append((x[0]+x[1])/2.0)
        elif i == n-1:   sm.append((x[n-2]+x[n-1])/2.0)
        else:            sm.append((x[i-1]+x[i]+x[i+1])/3.0)
    tx, ts = sum(x), sum(sm)
    f = (tx/ts) if ts else 1.0
    return [z*f for z in sm]

def roll_forward(c, R, used, round_out=True):
    R = dict(R); out = {}
    for i, t in enumerate(FY):
        stock = sum(R[v]*S(c, t-v+1) for v in range(1990, t))
        R[t] = used[i]
        v = stock + R[t]*S(c, 1)
        out[t] = int(round(v)) if round_out else v
    return out

def run(round_first, seam_mode, round_out=True, regs_round=0):
    res = {}
    for row in ROWS:
        r = row['row']; mt = row['meta'][3]
        if r in OUT_OF_SCOPE or r in LEAVE_AS_V19: continue
        v = {y: float(row['vals'].get(y) or 0) for y in YEARS}
        if all(v[t] == 0 for t in FY) and v[2025] == 0: continue
        c = curve(mt)
        raw = regs_raw(v, round_first)
        if r == 25:
            used = [UK_LCV_REGS[t] for t in FY]
            u = {2025: v[2025]}; out = {}
            for t in FY:
                u[t] = int(round(u[t-1]*(1-0.123)+UK_LCV_REGS[t])); out[t] = u[t]
            res[r] = {'meta': row['meta'], 'used': used, 'raw': [raw[t] for t in FY], 'v20': [out[t] for t in FY],
                      'v19': [v[t] for t in FY], 'seam': None, 'labels': 'LOCKED'}
            continue
        if r in PLAN_ONLY_MD:
            res[r] = {'meta': row['meta'], 'used': [0]*5, 'raw': [0]*5, 'v20': [0]*5,
                      'v19': [v[t] for t in FY], 'seam': None, 'labels': 'PLAN ONLY'}
            continue
        if seam_mode == 'material':
            seam, _ = detect_seam_material(v, c, abs_tol=1.0)
        else:
            seam = detect_seam(v, c)
        R, clipped, resid = build_state(v, c, seam)
        sm = smooth_keep_level([raw[t] for t in FY])
        if regs_round:
            sm = [round(z, regs_round) for z in sm]
        out = roll_forward(c, R, sm, round_out)
        res[r] = {'meta': row['meta'], 'used': sm, 'raw': [raw[t] for t in FY],
                  'v20': [out[t] for t in FY], 'v19': [v[t] for t in FY],
                  'seam': (seam if seam != 1990 else None), 'labels': 'CURVE'}
    return res

def ratio5(v20):
    d = [v20[i+1]-v20[i] for i in range(4)]
    if len(set(1 if x>0 else (-1 if x<0 else 0) for x in d)) > 2: return None
    rs = [d[i+1]/d[i] for i in range(3) if abs(d[i])>1e-9]
    return (sum(rs)/len(rs), rs, d) if rs else None

def gt(res, y):
    return sum(r['v20'][FY.index(y)] for r in res.values())

for tag, kw in (("A baseline (round-first, seam 25%)", dict(round_first=True,  seam_mode='pct')),
                ("B float input      , seam 25%", dict(round_first=False, seam_mode='pct')),
                ("C float input      , seam material", dict(round_first=False, seam_mode='material')),
                ("D float in + float out, seam material", dict(round_first=False, seam_mode='material', round_out=False))):
    res = run(**kw)
    print("\n" + "=" * 108)
    print("### %s" % tag)
    for r in (33, 54, 79, 90):
        if r not in res: continue
        o = res[r]
        rr = ratio5(o['v20'])
        print("  r%-3d %-9s used=%-42s v20=%s" % (r, o['meta'][1], str([round(x,3) for x in o['used']]), [round(x,2) for x in o['v20']]))
        if rr: print("        deltas=%s ratios=%s mean=%.4f  [0.97 hit %s | 1.0 hit %s]" % (
            [round(x,2) for x in rr[2]], [round(x,4) for x in rr[1]], rr[0],
            abs(rr[0]-0.97)<=0.01, abs(rr[0]-1.0)<=0.01))
    print("  seam r54=%s r90=%s" % (res[54]['seam'], res[90]['seam']))
    print("  GrandTotal: " + "  ".join("%d=%.2f" % (y, gt(res, y)) for y in FY))
