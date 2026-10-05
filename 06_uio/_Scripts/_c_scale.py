"""_c_scale.py - compute the candidate-c values: revert r54/r90, and repair the rows whose
own disclosed input implies retention k > 1 (r59, r69, r88) by SCALING the inferred cohort
state to the 2025 level instead of bumping the oldest vintage (the parent's own recipe).
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
    R = back_solve(s, c, 1990)
    for t in range(1991, 2026):
        if s[t] > 0 and R[t] < 0 and abs(R[t]) > 0.25 * s[t]:
            return t
    return 1990

def detect_seam_abs(s, c, tol=1.0):
    R = back_solve(s, c, 1990)
    for t in range(1991, 2026):
        if s[t] > 0 and R[t] < -tol:
            return t
    return 1990

def build_state(s, c, seam, mode='bump'):
    R = back_solve(s, c, seam)
    clipped = [v for v in YEARS if R[v] < 0]
    for v in clipped:
        R[v] = 0.0
    reb = sum(R[v] * S(c, 2026 - v) for v in YEARS if v <= 2025)
    resid = s[2025] - reb
    lam = None
    if mode == 'scale':
        lam = (s[2025] / reb) if reb else 1.0
        R = {v: (x * lam if v <= 2025 else x) for v, x in R.items()}
    else:
        if abs(resid) > 0.5 and s[2025] > 0:
            oldest = min([v for v in YEARS if S(c, 2026 - v) > 0] or [2025])
            R[oldest] += resid / S(c, 2026 - oldest)
    return R, clipped, resid, reb, lam

def roll(c, R, regs):
    R = dict(R); out = {}
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

def kseq(out, regs, base):
    ks, prev = [], base
    for i, t in enumerate(FY):
        ks.append((out[t] - regs[i]) / prev if prev else None)
        prev = out[t]
    return ks

print('=' * 120)
print('STEP 1 — reproduce candidate a exactly (seam = 25%-rule, bump mode, smoothed input)')
print('=' * 120)
for row in (54, 90):
    m = meta('a', row); mt = m[3]; c = curve(mt)
    s = vals('v19', row)
    seam = detect_seam_pct(s, c)
    regs = smooth_level([s[t] - s[t-1]*0.97 for t in FY])
    R, cl, resid, reb, _ = build_state(s, c, seam, 'bump')
    out = roll(c, R, regs)
    got = [out[t] for t in FY]
    want = [vals('a', row)[t] for t in FY]
    print('r%-3d seam=%-5s regs=%s' % (row, seam if seam != 1990 else 'none', [round(x,2) for x in regs]))
    print('     engine=%s  a=%s  %s' % (got, want, 'MATCH' if got == want else 'MISMATCH'))
    print('     k on this input (a disclosed-basis) = %s' % ','.join('%.4f' % x for x in kseq(out, regs, s[2025])))

print()
print('=' * 120)
print('STEP 2 — SCALE-mode repair for every row whose own input implies k > 1')
print('=' * 120)
print('%-4s %-9s %-4s | %-26s | %-26s | %-26s | %-26s' % (
    'row','country','mod','k BUMP (b as shipped)','k SCALE','a 2030','c 2030 (SCALE)'))
TARGETS = [59, 69, 88, 90, 54]
patch = {}
for row in TARGETS:
    m = meta('b', row); mt = m[3]; c = curve(mt)
    s = vals('v19', row)
    regs = DISCLOSED.get(row) or smooth_level([s[t] - s[t-1]*0.97 for t in FY])
    seam_bump = detect_seam_abs(s, c) if row in (54, 90) else detect_seam_pct(s, c)
    seam_scale = seam_bump
    Rb, clb, residb, rebb, _ = build_state(s, c, seam_bump, 'bump')
    Rs, cls, resids, rebs, lam = build_state(s, c, seam_scale, 'scale')
    outb = roll(c, Rb, regs)
    outs = roll(c, Rs, regs)
    kb = kseq(outb, regs, s[2025])
    ksv = kseq(outs, regs, s[2025])
    a2030 = vals('a', row)[2030]
    bad_b = any(x > 1.0 or x < 0 for x in kb)
    bad_s = any(x > 1.0 or x < 0 for x in ksv)
    print('%-4d %-9s %-4s | %-26s | %-26s | %-26s | %-26s  %s' % (
        row, str(m[1])[:9], str(mt)[:4],
        ','.join('%.3f' % x for x in kb), ','.join('%.3f' % x for x in ksv),
        '%s' % a2030, '%s' % [outs[t] for t in FY],
        ('BUMP-BAD ' if bad_b else '') + ('SCALE-BAD' if bad_s else 'SCALE-OK')))
    print('      seam=%s  lam=%-8s resid=%-9s  c forecast = %s' % (
        seam_scale if seam_scale != 1990 else 'none',
        ('%.4f' % lam) if lam else 'n/a', round(resids, 1), [outs[t] for t in FY]))
    patch[row] = {'seam': seam_scale if seam_scale != 1990 else None,
                  'lam': lam, 'regs': [round(x, 4) for x in regs],
                  'k_scale': [round(x, 6) for x in ksv],
                  'forecast': [outs[t] for t in FY]}

print()
print('=' * 120)
print('STEP 3 — full-workbook k audit under SCALE mode for the rows at risk')
print('=' * 120)
print('rows with k>1 or k<0 in candidate b as shipped (bump mode):')
for row in sorted(DISCLOSED):
    va, vb = vals('a', row), vals('b', row)
    if not any(vb[t] for t in FY) and not any(va[t] for t in FY):
        continue
    regs = DISCLOSED[row]
    for tag, vv in (('a', va), ('b', vb)):
        pass
    # solve k from the workbook's own values, disclosed input
    ks = kseq(vb, regs, vb[2025])
    if any(x > 1.0 or x < 0 for x in ks):
        print('   r%-3d %-9s %-4s k=%s' % (row, meta('b', row)[1], meta('b', row)[3],
                                           ','.join('%.3f' % x for x in ks)))

json.dump(patch, open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_c_patch.json', 'w',
                      encoding='utf-8'), indent=1)
print('\nsaved _c_patch.json')
