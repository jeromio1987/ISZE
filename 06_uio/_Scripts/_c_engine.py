"""_c_engine.py - faithful re-implementation of the V20 engine, validated against
candidate a and candidate b, then used to score seam-recipe variants for r54/r90.

Engine (from build_uio_v20_candidate.py / build_v20b_fix.py, reproduced verbatim):
    R = back_solve(series, curve, seam)      # R[t]=0 for t<seam
    clip R<0 -> 0
    reb  = sum(R[v]*S(c,2026-v) for v<=2025)     # model value at 2025
    resid= series[2025] - reb  -> absorbed into the oldest vintage alive in 2026
    for t in 2026..2030:
        stock = sum(R[v]*S(c,t-v+1) for v in 1990..t-1)
        R[t]  = regs[t]
        out[t]= round(stock + R[t]*S(c,1))
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

C = json.load(open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_c_cache.json', encoding='utf-8'))
YEARS = list(range(1990, 2031))
FY = [2026, 2027, 2028, 2029, 2030]
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

def detect_seam_pct(s, c):
    """candidate a's rule: negative cohort worth > 25% of that year's fleet."""
    R = back_solve(s, c, 1990)
    for t in range(1991, 2026):
        if s[t] > 0 and R[t] < 0 and abs(R[t]) > 0.25 * s[t]:
            return t
    return 1990

def detect_seam_abs(s, c, tol=1.0):
    """candidate b's rule: first cohort materially negative (< -1 unit)."""
    R = back_solve(s, c, 1990)
    for t in range(1991, 2026):
        if s[t] > 0 and R[t] < -tol:
            return t
    return 1990

def build_state(s, c, seam):
    R = back_solve(s, c, seam)
    clipped = [v for v in YEARS if R[v] < 0]
    for v in clipped:
        R[v] = 0.0
    reb = sum(R[v] * S(c, 2026 - v) for v in YEARS if v <= 2025)
    resid = s[2025] - reb
    if abs(resid) > 0.5 and s[2025] > 0:
        oldest = min([v for v in YEARS if S(c, 2026 - v) > 0] or [2025])
        R[oldest] += resid / S(c, 2026 - oldest)
    return R, clipped, resid, reb

def roll_forward(c, R, regs, R_is_copy=True):
    R = dict(R)
    out = {}
    for i, t in enumerate(FY):
        stock = sum(R[v] * S(c, t - v + 1) for v in range(1990, t))
        R[t] = regs[i]
        out[t] = round(stock + R[t] * S(c, 1))
    return out

def smooth_level(x):
    n = len(x); sm = []
    for i in range(n):
        if i == 0:       sm.append((x[0] + x[1]) / 2.0)
        elif i == n - 1: sm.append((x[n-2] + x[n-1]) / 2.0)
        else:            sm.append((x[i-1] + x[i] + x[i+1]) / 3.0)
    tx, ts = sum(x), sum(sm)
    f = (tx / ts) if ts else 1.0
    return [z * f for z in sm]

def kseq(out, regs, base=2025.0):
    out = []
    prev = base
    for i, t in enumerate(FY):
        out.append((t, (valsmap[t] - regs[i]) / prev))
        prev = valsmap[t]
    return out

print('=' * 118)
print('VALIDATION 1 — reproduce candidate a exactly using candidate a\'s own rule (25%-of-fleet seam)')
print('=' * 118)
ok = True
for tag_src, row in (('a', 54), ('a', 90)):
    m = meta('a', row); mt = m[3]; c = curve(mt)
    s = vals('v19', row)
    seam = detect_seam_pct(s, c)
    R, clipped, resid, reb = build_state(s, c, seam)
    regsV = [s[t] - s[t-1]*0.97 for t in FY]
    regs = [int(round(x)) for x in regsV]
    out = roll_forward(c, R, regs)
    got = [out[t] for t in FY]
    want = [vals('a', row)[t] for t in FY]
    print('r%-3d %-9s seam=%-5s regs(rounded)=%-34s' % (row, m[1], seam if seam != 1990 else 'none', regs))
    print('     engine=%s   candidate a=%s   %s' % (got, want, 'MATCH' if got == want else '*** MISMATCH ***'))
    if got != want: ok = False
print('validation:', 'OK' if ok else 'FAILED')

print()
print('=' * 118)
print('VALIDATION 2 — reproduce candidate b exactly (r54 seam=2005, r90 seam=2014, full-precision smoothed input)')
print('=' * 118)
ok2 = True
for row, seam_want in ((54, 2005), (90, 2014)):
    m = meta('b', row); mt = m[3]; c = curve(mt)
    s = vals('v19', row)
    seam = detect_seam_abs(s, c)
    R, clipped, resid, reb = build_state(s, c, seam)
    used = smooth_level([s[t] - s[t-1]*0.97 for t in FY])
    out = roll_forward(c, R, used)
    got = [out[t] for t in FY]
    want = [vals('b', row)[t] for t in FY]
    print('r%-3d %-9s seam=%s (want %s)  clipped=%s  resid=%.1f  reb=%.1f' % (
        row, m[1], seam if seam != 1990 else 'none', seam_want, clipped, resid, reb))
    print('     engine=%s   candidate b=%s   %s' % (got, want, 'MATCH' if got == want else '*** MISMATCH ***'))
    print('     regs_used (smoothed) = %s' % [round(x, 2) for x in used])
    if got != want: ok2 = False
print('validation:', 'OK' if ok2 else 'FAILED')

print()
print('=' * 118)
print('VARIANT SCAN — every seam the sources permit, with the FULL-PRECISION disclosed input')
print('=' * 118)
for row in (54, 90, 51, 26, 29):
    m = meta('b', row); mt = m[3]; c = curve(mt)
    s = vals('v19', row)
    regs = DISCLOSED.get(row)
    print('\n--- r%-3d %-9s %-4s  2025=%.0f  life=%.2f ---' % (row, m[1], mt, s[2025], sum(c.values())))
    if not regs:
        print('    no disclosed input; V19-implied = %s' % [round(s[t]-s[t-1]*0.97, 2) for t in FY])
        regs = [s[t]-s[t-1]*0.97 for t in FY]
    rows_printed = 0
    for seam in range(0, 21):           # 0 = no seam (1990), else the year
        sm = 1990 if seam == 0 else seam
        R, clipped, resid, reb = build_state(s, c, sm)
        # negatives that REMAIN strictly after the seam (pre-clip, from a fresh back-solve)
        Rs = back_solve(s, c, sm)
        post = [(t, round(Rs[t], 1)) for t in range(max(sm, 1991), 2026) if s[t] > 0 and Rs[t] < -1.0]
        scale = s[2025] / reb if reb else None
        out = roll_forward(c, R, regs)
        kk = []
        prev = s[2025]
        for i, t in enumerate(FY):
            kk.append((out[t] - regs[i]) / prev)
            prev = out[t]
        flags = []
        if any(x > 1.0 for x in kk): flags.append('k>1')
        if any(x < 0 for x in kk): flags.append('k<0')
        if all(abs(x-0.97) <= 0.01 for x in kk): flags.append('FLAT-3%')
        if not flags:
            print('    seam=%-5s post-seam negatives=%-26s scale=%-7s k=%s  fc=%s' % (
                'none' if seam == 0 else seam, str(post or 'none')[:26],
                ('%.3f' % scale) if scale else 'n/a',
                ','.join('%.3f' % x for x in kk), [out[t] for t in FY]))
            rows_printed += 1
        else:
            print('    seam=%-5s post-seam negatives=%-26s scale=%-7s k=%s  fc=%s  <<< %s' % (
                'none' if seam == 0 else seam, str(post or 'none')[:26],
                ('%.3f' % scale) if scale else 'n/a',
                ','.join('%.3f' % x for x in kk), [out[t] for t in FY], ' '.join(flags)))
    print('    -> %d candidate seam(s) with no retention violation' % rows_printed)
