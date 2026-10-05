"""_c_seam3.py - decisive seam-recipe analysis for r54 / r90 (+ r26, r29, r51 controls).

For each recipe (seam year, legacy retained/clipped, scaled-to-2025-level) compute:
  - the pre-2026 stock from post-seam cohorts only
  - the scale needed to put that stock ON the 2025 level
  - the resulting forecast and the implied retention k_t = (UIO_t - regs_t)/UIO_{t-1}
  - flags: k>1, k<0, and |k-0.97|<=0.01 (the check5 3%-rule signature)
  - whether any negative implied cohort remains AFTER the seam
  - the reproduction error of the 2025 level from post-seam cohorts alone
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

def negs(R, s, lo, hi=2025):
    return [(t, round(R[t], 1)) for t in range(lo, hi + 1) if s[t] > 0 and R[t] < -1.0]

def stock_pre2026(R, c):
    return sum(R[v] * S(c, 2026 - v + 1) for v in range(1990, 2026))

def kseq(valsmap, regs, base=2025):
    out, prev = [], valsmap.get(base)
    for i, t in enumerate(FY):
        cur = valsmap.get(t)
        out.append((cur - regs[i]) / prev if prev else None)
        prev = cur
    return out

print('=' * 130)
print('RECIPE TABLE — "reconstruct from the seam year forward and scale to the seam level"')
print('k_t = (UIO_t - regs_t) / UIO_{t-1}   [scale-invariant, so it is the same for scaled and unscaled series]')
print('=' * 130)

for r in (26, 29, 51, 54, 90):
    m = meta('v19', r)
    mt = m[3]
    c = curve(mt)
    s = vals('v19', r)
    regsD = DISCLOSED.get(r) or []
    regsV = [(s[t] - s[t - 1] * 0.97) for t in FY]
    print('\n' + '#' * 130)
    print('r%-3d %-9s %-4s   2025 level = %.0f   curve life = %.2f yr' % (r, m[1], mt, s[2025], sum(c.values())))
    print('    V19 2010-2025: %s' % [int(s[y]) for y in range(2010, 2026)])
    R0 = back_solve(s, c, 1990)
    print('    back-solve from 1990 -> negative implied cohorts: %s' % (negs(R0, s, 1991) or 'none'))
    for seam in (1990, 2005, 2013, 2014, 2015, 2019):
        if seam == 1990:
            Rs = dict(R0)
        else:
            Rs = back_solve(s, c, seam)
        post_negs = negs(Rs, s, max(seam, 1991)) if seam != 1990 else negs(Rs, s, 1991)
        Rc = {v: (x if x > 0 else 0.0) for v, x in Rs.items()}
        sp = stock_pre2026(Rc, c)
        scale = s[2025] / sp if sp else None
        # forecast: stock from post-seam cohorts, decayed, + this year's new cohort
        fc = []
        for t in FY:
            stock_t = sum(Rc[v] * S(c, t - v + 1) for v in range(1990, t))
            fc.append(stock_t)
        # forecast series WITHOUT the new cohort is the wrong basis; k uses regs explicitly,
        # so use the standard engine form: UIO_t = stock_t + regs_t * S(1)
        fcfull = [sum(Rc[v] * S(c, t - v + 1) for v in range(1990, t)) + regsD[i] * S(c, 1)
                  for i, t in enumerate(FY)] if regsD else None
        kD = kseq({y: v for y, v in zip(FY, fcfull)}, regsD) if fcfull else None
        kV = kseq({y: v for y, v in zip(FY, fcfull)}, regsV) if fcfull else None
        flags = []
        for lbl, kk in (('kD', kD), ('kV', kV)):
            if kk and all(x is not None for x in kk):
                if any(x > 1.0 for x in kk): flags.append(lbl + '>1')
                if any(x < 0 for x in kk): flags.append(lbl + '<0')
                if any(abs(x - 0.97) <= 0.01 for x in kk): flags.append(lbl + '=3%rule')
        print('    seam=%-4s  negatives after seam: %-28s  post-seam 2025 stock=%9.1f  scale to 2025=%s' % (
            seam if seam != 1990 else 'none', str(post_negs or 'none')[:28], sp,
            ('%.3f' % scale) if scale else 'n/a'))
        if fcfull:
            print('              forecast = %s' % [round(x) for x in fcfull])
            print('              k (disclosed regs) = %s' % (
                ','.join('%.3f' % x if x is not None else '--' for x in kD) if kD else 'n/a'))
            print('              k (V19-implied regs)= %s   %s' % (
                ','.join('%.3f' % x if x is not None else '--' for x in (kV or [])),
                ('FLAGS: ' + ' '.join(flags)) if flags else 'no flags'))

print()
print('=' * 130)
print('CANDIDATE c AS SHIPPED BY THE SIBLING PASS — what is on disk now')
print('=' * 130)
print('r54 forecast = %s ; r90 forecast = %s' % (
    [C['b']['vals']['54'][str(y)] for y in FY] if False else 'see _c_cache (c not cached)', ''))
