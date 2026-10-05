"""_c_patch_final.py - compute + verify the candidate-c repairs (dry: prints only).

Repairs applied relative to the candidate c on disk (= candidate b + the r79 fix):
  r54 PORTUGL LCV  -> revert to candidate a's values (b's seam repass raises k above
                      candidate a and makes the row non-monotonic; the seam is not
                      reconstructable from the sources on disk).
  r90 CYPRUS  LCV  -> already = candidate a's values in c. No change. Verified legal.
  r69 POLAND  LCV  -> clip + SCALE-to-2025 (bump absorption made k26 = 2.18).
  r88 CYPRUS  LD   -> clip + SCALE-to-2025 (bump absorption made k26 = 1.14).

Recipe: the parent's own - reconstruct the cohort state from the seam forward and
SCALE it to the 2025 level, instead of dumping the whole residual onto the single
oldest surviving vintage (which is what makes the 2026 step impossible).
"""
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

DECL = {}
SRC = {}
for row in C['b']['extra']['V20 REGS USED']:
    if row and isinstance(row[0], (int, float)) and 7 <= row[0] <= 90:
        seg = row[5:10]
        if any(isinstance(x, (int, float)) for x in seg):
            DECL[int(row[0])] = [float(x) if isinstance(x, (int, float)) else 0.0 for x in seg]
            SRC[int(row[0])] = row[11] if len(row) > 11 else ''

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

def state_scale(s, c, seam):
    """candidate a's seam rule, then SCALE the clipped state onto the 2025 level."""
    R = back_solve(s, c, seam)
    clipped = [v for v in YEARS if R[v] < 0]
    for v in clipped: R[v] = 0.0
    reb = sum(R[v] * S(c, 2026 - v) for v in YEARS if v <= 2025)
    lam = (s[2025] / reb) if reb else 1.0
    R = {v: (x * lam if v <= 2025 else x) for v, x in R.items()}
    return R, clipped, reb, lam

def roll(c, R, regs):
    R = dict(R); out = {}
    for i, t in enumerate(FY):
        stock = sum(R[v] * S(c, t - v + 1) for v in range(1990, t))
        R[t] = regs[i]; out[t] = round(stock + R[t] * S(c, 1))
    return out

def ks(out, regs, base):
    res, prev = [], base
    for i, t in enumerate(FY):
        res.append(round((out[t] - regs[i]) / prev, 6) if prev else None); prev = out[t]
    return res

print('=' * 126)
print('CANDIDATE C — repair values (values only; nothing written)')
print('=' * 126)

result = {}
for row in (69, 88):
    m = meta('b', row); mt = m[3]; c = curve(mt)
    s = vals('v19', row)
    seam = detect_seam_pct(s, c)
    R, clipped, reb, lam = state_scale(s, c, seam)
    declared = DECL.get(row) or [0.0] * 5
    regs = [max(x, 0.0) for x in declared]
    out = roll(c, R, regs)
    fc = [out[t] for t in FY]
    k_clamped = ks(out, regs, s[2025])
    k_declared = ks(out, declared, s[2025])
    result[row] = {'seam': seam if seam != 1990 else None, 'lambda': round(lam, 6),
                   'clipped': clipped, 'model_2025': round(reb, 1), 'level_2025': s[2025],
                   'declared': [round(x, 4) for x in declared], 'regs_used': regs,
                   'forecast': fc, 'k_on_regs_used': k_clamped, 'k_on_declared': k_declared,
                   'a': [vals('a', row)[t] for t in FY], 'b': [vals('b', row)[t] for t in FY]}
    print('\nr%-3d %-9s %-4s   life=%.2f' % (row, m[1], mt, sum(c.values())))
    print('    seam detected (candidate a rule) = %s ; negatives clipped = %s' % (
        seam if seam != 1990 else 'none', clipped))
    print('    model value at 2025 = %.1f ; row 2025 level = %.0f ; scale lam = %.4f' % (reb, s[2025], lam))
    print('    disclosed input      = %s' % [round(x, 4) for x in declared])
    if any(x < 0 for x in declared):
        print('    -> negative recovered "registration" (unphysical) -> clamped to 0 for the roll-forward: %s'
              % regs)
    print('    candidate a 2026-30  = %s   k=%s' % (
        [vals('a', row)[t] for t in FY], ','.join('%.3f' % x for x in ks(
            {y: vals('a', row)[y] for y in FY}, declared, s[2025]))))
    print('    candidate b 2026-30  = %s   k=%s' % (
        [vals('b', row)[t] for t in FY], ','.join('%.3f' % x for x in ks(
            {y: vals('b', row)[y] for y in FY}, declared, s[2025]))))
    print('    CANDIDATE C 2026-30  = %s   k=%s   %s' % (
        fc, ','.join('%.3f' % x for x in k_clamped),
        'OK' if all(0 <= x <= 1.0 for x in k_clamped) else '*** VIOLATION ***'))
    print('    k on the raw disclosed input = %s  %s' % (
        ','.join('%.3f' % x for x in k_declared),
        'OK' if all(0 <= x <= 1.0 for x in k_declared) else '*** VIOLATION ***'))

print()
print('=' * 126)
print('r54 / r90 — revert to candidate a (b\'s repass is not reconstructable)')
print('=' * 126)
for row in (54, 90):
    m = meta('a', row); s = vals('v19', row)
    declared = DECL.get(row) or [0.0] * 5
    ka = ks({y: vals('a', row)[y] for y in FY}, declared, s[2025])
    kb = ks({y: vals('b', row)[y] for y in FY}, declared, s[2025])
    print('r%-3d %-9s %-4s  a=%s k=%s | b=%s k=%s' % (
        row, m[1], m[3], [vals('a', row)[t] for t in FY], ','.join('%.3f' % x for x in ka),
        [vals('b', row)[t] for t in FY], ','.join('%.3f' % x for x in kb)))
    print('       verdict: %s' % ('candidate a is monotone and all k<=1 -> REVERT to a' if row == 54
                                  else 'candidate b violates k<=1 (1.365); candidate a does not -> REVERT to a'))
    result[row] = {'forecast': [vals('a', row)[t] for t in FY], 'k': ka, 'action': 'revert-to-a'}

json.dump(result, open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_c_patch_final.json', 'w',
                       encoding='utf-8'), indent=1)
print('\nsaved _c_patch_final.json')
