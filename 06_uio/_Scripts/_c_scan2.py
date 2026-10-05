"""_c_scan2.py - seam/mode scan for r88, r69, r59 (the other rows whose disclosed
input implies k>1 under candidate b's bump absorption)."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

C = json.load(open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_c_cache.json', encoding='utf-8'))
YEARS = list(range(1990, 2031)); FY = [2026, 2027, 2028, 2029, 2030]
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c, a): return c.get(a, 0.0) if a >= 1 else 0.0
def curve(mt): return LCV if str(mt) == 'LCV' else CV_DEV
def vals(tag, r):
    d = C[tag]['vals'][str(r)]
    return {y: (float(d[str(y)]) if d[str(y)] is not None else 0.0) for y in YEARS}
def meta(tag, r): return C[tag]['meta'][str(r)]
DISCLOSED = {}
for row in C['b']['extra']['V20 REGS USED']:
    if row and isinstance(row[0], (int, float)) and 7 <= row[0] <= 90:
        seg = row[5:10]
        if any(isinstance(x, (int, float)) for x in seg):
            DISCLOSED[int(row[0])] = [float(x) if isinstance(x, (int, float)) else 0.0 for x in seg]

def back_solve(s, c, start):
    R = {}
    for t in YEARS:
        if t < start:
            R[t] = 0.0; continue
        R[t] = s[t] - sum(R[v] * S(c, t - v + 1) for v in YEARS if start <= v < t)
    return R

def state(s, c, seam, mode):
    R = back_solve(s, c, seam)
    clipped = [v for v in YEARS if R[v] < 0]
    for v in clipped: R[v] = 0.0
    reb = sum(R[v] * S(c, 2026 - v) for v in YEARS if v <= 2025)
    resid = s[2025] - reb
    lam = None
    if mode == 'scale':
        lam = (s[2025] / reb) if reb else 1.0
        R = {v: (x * lam if v <= 2025 else x) for v, x in R.items()}
    elif abs(resid) > 0.5 and s[2025] > 0:
        oldest = min([v for v in YEARS if S(c, 2026 - v) > 0] or [2025])
        R[oldest] += resid / S(c, 2026 - oldest)
    return R, clipped, reb, resid, lam

def roll(c, R, regs):
    R = dict(R); out = {}
    for i, t in enumerate(FY):
        stock = sum(R[v] * S(c, t - v + 1) for v in range(1990, t))
        R[t] = regs[i]; out[t] = round(stock + R[t] * S(c, 1))
    return out

def kk(out, regs, base):
    ks, prev = [], base
    for i, t in enumerate(FY):
        ks.append((out[t] - regs[i]) / prev if prev else None); prev = out[t]
    return ks

for row in (88, 69, 59):
    m = meta('b', row); mt = m[3]; c = curve(mt)
    s = vals('v19', row)
    regs = DISCLOSED.get(row)
    print('\n' + '#' * 118)
    print('r%-3d %-9s %-4s  2025=%.0f  life=%.2f' % (row, m[1], mt, s[2025], sum(c.values())))
    print('    V19 2010-2025: %s' % [int(s[y]) for y in range(2010, 2026)])
    print('    disclosed input: %s' % ([round(x, 2) for x in regs] if regs else 'NO'))
    print('    candidate a 2026-30: %s' % [vals('a', row)[t] for t in FY])
    print('    candidate b 2026-30: %s' % [vals('b', row)[t] for t in FY])
    R0 = back_solve(s, c, 1990)
    print('    negatives from 1990 (pre-clip): %s' % [(t, round(R0[t], 1)) for t in range(1991, 2026)
                                                      if s[t] > 0 and R0[t] < -1.0] or 'none')
    for seam in (1990, 2005, 2013, 2014, 2015, 2019):
        Rs_raw = back_solve(s, c, seam)
        post = [(t, round(Rs_raw[t], 1)) for t in range(max(seam, 1991), 2026)
                if s[t] > 0 and Rs_raw[t] < -1.0]
        for mode in ('bump', 'scale'):
            R, cl, reb, resid, lam = state(s, c, seam, mode)
            out = roll(c, R, regs)
            ks = kk(out, regs, s[2025])
            bad = any(x > 1.0 or x < 0 for x in ks)
            print('    seam=%-5s %-5s post-neg=%-22s lam=%-7s k=%-34s fc=%-28s %s' % (
                seam if seam != 1990 else 'none', mode, str(post or 'none')[:22],
                ('%.3f' % lam) if lam else '-', ','.join('%.3f' % x for x in ks),
                str([out[t] for t in FY]), '<<< BAD' if bad else 'ok'))
