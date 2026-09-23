"""_c_analyze.py - read-only seam / retention analysis for UIO V20 candidate c.

Answers, from workbook VALUES only:
  A. For r54 (PORTUGL LCV) and r90 (CYPRUS LCV) [plus r26/r29/r51/r88 as controls]:
     is there ANY seam year from which a non-negative cohort history exists?
  B. Can the "reconstruct from the seam and scale to the seam level" recipe produce
     a credible registration input, and what retention k does it imply?
  C. Retention k per row per year, using candidate b's DISCLOSED input sheet.
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

def series(tag, r):
    d = C[tag]['vals'][str(r)]
    return {y: float(d[str(y)] or 0) for y in YEARS}

def meta(tag, r):
    return C[tag]['meta'][str(r)]

def back_solve(s, c, start):
    R = {}
    for t in YEARS:
        if t < start:
            R[t] = 0.0; continue
        R[t] = s[t] - sum(R[v] * S(c, t - v + 1) for v in YEARS if start <= v < t)
    return R

def neg_years(R, s, lo=1991, hi=2025):
    return [(t, round(R[t], 1)) for t in range(lo, hi + 1) if s[t] > 0 and R[t] < -1.0]

ROWS = {54: ('PORTUGL', 'LCV'), 90: ('CYPRUS', 'LCV'), 26: ('IRELAND', 'CV'),
        29: ('IRELAND', 'LCV'), 51: ('PORTUGL', 'CV'), 88: ('CYPRUS', 'CV'),
        33: ('BELGIUM', 'CV'), 79: ('GREECE', 'CV')}

print('=' * 120)
print('A. IS THERE A SEAM YEAR FROM WHICH A NON-NEGATIVE COHORT HISTORY EXISTS?')
print('=' * 120)
for r, (ctry, mt) in ROWS.items():
    s = series('v19', r)
    c = curve(mt)
    R = back_solve(s, c, 1990)
    neg_all = neg_years(R, s)
    print('\nr%-3d %-9s %-4s  V19 series 2010-2025: %s' % (
        r, ctry, mt, [int(s[y]) for y in range(2010, 2026)]))
    print('   back-solve from 1990: negative implied cohorts (|.|>1 unit): %s' % (neg_all or 'none'))
    # try every seam in 1991..2020 and report the negative profile after it
    best = None
    for seam in range(1991, 2021):
        Rs = back_solve(s, c, seam)
        post = neg_years(Rs, s, lo=seam, hi=2025)
        if best is None or len(post) < len(best[1]):
            best = (seam, post)
    print('   best seam (fewest negatives strictly after it): seam=%d, still-negative years after it: %s'
          % (best[0], best[1] or 'none'))
    # any seam at all with ZERO negatives after it?
    clean = [seam for seam in range(1991, 2021)
             if not neg_years(back_solve(s, c, seam), s, lo=seam, hi=2025)]
    print('   seams that leave NO negative cohort anywhere after them: %s' % (clean or 'NONE'))

print()
print('=' * 120)
print('B. "RECONSTRUCT FROM THE SEAM AND SCALE TO THE SEAM LEVEL" - what input/k does it imply?')
print('=' * 120)
DISCLOSED = {}
for row in C['b']['extra']['V20 REGS USED']:
    if row and isinstance(row[0], (int, float)) and 7 <= row[0] <= 90 and any(
            isinstance(x, (int, float)) for x in row[5:10]):
        DISCLOSED[int(row[0])] = [float(x) if isinstance(x, (int, float)) else 0.0 for x in row[5:10]]

def k_table(vals, regs, base_year=2025):
    """k_t = (UIO_t - regs_t)/UIO_{t-1}, t = 2026..2030."""
    out = []
    prev = vals.get(base_year)
    for i, t in enumerate(FY):
        cur = vals.get(t)
        if prev and cur is not None:
            out.append((t, round((cur - regs[i]) / prev, 4)))
        prev = cur
    return out

for r in (54, 90):
    ctry, mt = ROWS[r]
    s = series('v19', r)
    c = curve(mt)
    print('\n--- r%-3d %s %s ---' % (r, ctry, mt))
    # candidate a engine: 25%-rule seam
    def seam_pct(s, c):
        R = back_solve(s, c, 1990)
        for t in range(1991, 2026):
            if s[t] > 0 and R[t] < 0 and abs(R[t]) > 0.25 * s[t]:
                return t, R
        return 1990, R
    seam_p = seam_pct(s, c)[0]
    print('   candidate-a seam rule (neg > 25%% of fleet) = %s' % (seam_p if seam_p != 1990 else 'none'))
    for seam in [2014, 2015, 2005, 2006]:
        Rs = back_solve(s, c, seam)
        for v in YEARS:
            if Rs[v] < 0: Rs[v] = 0.0
        stock26 = sum(Rs[v] * S(c, 2026 - v + 1) for v in range(1990, 2026))
        scale = s[2025] / stock26 if stock26 else None
        regs = DISCLOSED.get(r) or [0] * 5
        # scaled forecast: each forecast year gets (stock + regs*S(1)) * scale
        fc, prev = [], s[2025]
        for i, t in enumerate(FY):
            stock_t = sum(Rs[v] * S(c, t - v + 1) for v in range(1990, t))
            val = (stock_t + regs[i] * S(c, 1)) 
            fc.append(val)
        print('   seam %d: pre-2026 stock from post-seam cohorts = %.1f ; 2025 level = %.0f ; '
              'scale to 2025 = %s' % (seam, stock26, s[2025], ('%.3f' % scale) if scale else 'n/a'))
        if scale:
            fcs = [v * scale for v in fc]
            print('        scaled forecast = %s ; scaled input = %s ; k with scaled input = %s'
                  % ([round(x) for x in fcs], [round(x * scale) for x in regs],
                     [(t, round((fcs[i + 1] - regs[i + 1] * scale) / fcs[i], 3)) for i, t in enumerate(FY[1:])]))
            print('        unscaled forecast = %s ; k with disclosed input = %s'
                  % ([round(x) for x in fc], k_table({y: round(x) for y, x in zip(FY, fc)},
                                                     regs, base_year=2025)))

print()
print('=' * 120)
print('C. RETENTION k FOR EVERY ROW, USING CANDIDATE b\'s DISCLOSED INPUT')
print('=' * 120)
print('%-4s %-9s %-4s %-28s | %-38s | %-38s' % ('row', 'country', 'L/C', '2030 value a -> b', 'k (candidate a)', 'k (candidate b)'))
for r in sorted(DISCLOSED):
    m = meta('b', r)
    if not m or not m[1]:
        continue
    mt = m[3]
    va = {y: C['a']['vals'][str(r)][str(y)] for y in FY + [2025]}
    vb = {y: C['b']['vals'][str(r)][str(y)] for y in FY + [2025]}
    va = {k: (float(v) if v is not None else None) for k, v in va.items()}
    vb = {k: (float(v) if v is not None else None) for k, v in vb.items()}
    if not any(va[y] for y in FY) and not any(vb[y] for y in FY):
        continue
    ka, kb = k_table(va, DISCLOSED[r]), k_table(vb, DISCLOSED[r])
    bad_a = [x for x in ka if x[1] > 1.0 or x[1] < 0]
    bad_b = [x for x in kb if x[1] > 1.0 or x[1] < 0]
    flag = ''
    if bad_a: flag += ' A-VIOLATION'
    if bad_b: flag += ' B-VIOLATION'
    print('%-4d %-9s %-4s %-28s | %-38s | %-38s%s' % (
        r, str(m[1])[:9], mt, '%s -> %s' % (va[2030], vb[2030]),
        ','.join('%.3f' % x[1] for x in ka), ','.join('%.3f' % x[1] for x in kb), flag))
    if bad_a:
        print('      A violations: %s' % bad_a)
    if bad_b:
        print('      B violations: %s' % bad_b)
