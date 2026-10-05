"""_c_diag2.py - full retention diagnostic: which rows can violate k<=1 on which basis."""
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
    return {y: (float(d[str(y)]) if d[str(y)] is not None else None) for y in YEARS}
def meta(tag, r): return C[tag]['meta'][str(r)]

# b's disclosed input
DISCLOSED = {}
for row in C['b']['extra']['V20 REGS USED']:
    if row and isinstance(row[0], (int, float)) and 7 <= row[0] <= 90:
        seg = row[5:10]
        if any(isinstance(x, (int, float)) for x in seg):
            DISCLOSED[int(row[0])] = [float(x) if isinstance(x, (int, float)) else 0.0 for x in seg]

def v19_implied(r):
    v = vals('v19', r)
    out = []
    for t in FY:
        a, b = v.get(t - 1), v.get(t)
        if a is None or b is None:
            out.append(None)
        else:
            out.append(b - a * 0.97)
    return out

def k_of(v, regs):
    out = []
    prev = v.get(2025)
    for i, t in enumerate(FY):
        cur = v.get(t)
        if prev is None or cur is None or regs[i] is None or prev == 0:
            out.append(None)
        else:
            out.append((cur - regs[i]) / prev)
        prev = cur
    return out

def back_solve(s, c, start):
    R = {}
    for t in YEARS:
        if t < start:
            R[t] = 0.0; continue
        R[t] = (s[t] or 0.0) - sum(R[v] * S(c, t - v + 1) for v in YEARS if start <= v < t)
    return R

print('=' * 128)
print('RETENTION k VIOLATIONS (k > 1.0 or k < 0) — every row with a non-empty forecast')
print('Basis D = the workbook\'s own disclosed input (b only).  Basis V = V19-implied plan UIO(t)-0.97*UIO(t-1)')
print('=' * 128)
hdr = '%-4s %-9s %-9s | %-30s | %-30s | %-30s' % ('row','country','model','k on basis V (cand a)','k on basis V (cand b)','k on basis D (cand b)')
print(hdr)
print('-' * len(hdr))
viol = {'aV': [], 'bV': [], 'bD': []}
for r in range(7, 91):
    m = meta('b', r)
    if not m or not m[1]:
        continue
    mt = m[3]
    va, vb = vals('a', r), vals('b', r)
    if not any(va[t] for t in FY) and not any(vb[t] for t in FY):
        continue
    regsV = v19_implied(r)
    regsD = DISCLOSED.get(r)
    ka, kb = k_of(va, regsV), k_of(vb, regsV)
    kd = k_of(vb, regsD) if regsD else None
    def bad(k): return k is not None and any(x is not None and (x > 1.0 or x < 0) for x in k)
    f = []
    if bad(ka): f.append('aV')
    if bad(kb): f.append('bV')
    if bad(kd): f.append('bD')
    for x in f: viol[x].append(r)
    if f:
        def fmt(k): return ','.join('%.3f' % x if x is not None else '--' for x in (k or []))
        print('%-4d %-9s %-9s | %-30s | %-30s | %-30s  %s' % (
            r, str(m[1])[:9], str(mt)[:9], fmt(ka), fmt(kb), fmt(kd), ' '.join(f)))
        print('        2025=%s  a=%s  b=%s' % (va.get(2025), [va[t] for t in FY], [vb[t] for t in FY]))
        print('        regs V19-implied=%s' % [None if x is None else round(x, 2) for x in regsV])
        if regsD: print('        regs disclosed  =%s' % [round(x, 2) for x in regsD])

print()
print('=' * 128)
print('SUMMARY: violations per basis')
print('=' * 128)
for k, v in viol.items():
    print('  %-4s : %d rows %s' % (k, len(v), v))

print()
print('=' * 128)
print('INPUT-FREE: negative implied cohorts in the FORECAST years 2026-2030 (back-solve from 1990, no clipping)')
print('=' * 128)
for tag in ('a', 'b'):
    hits = []
    for r in range(7, 91):
        m = meta(tag, r)
        if not m or not m[1]:
            continue
        mt = m[3]
        v = vals(tag, r)
        if not any(v[t] for t in FY):
            continue
        c = curve(mt)
        s = {y: (v[y] or 0.0) for y in YEARS}
        R = back_solve(s, c, 1990)
        neg = [(t, round(R[t], 1)) for t in FY if s[t] > 0 and R[t] < -1.0]
        if neg:
            hits.append((r, str(m[1]), str(mt), neg))
    print('candidate %s: %d row(s) with a negative implied cohort in 2026-2030' % (tag, len(hits)))
    for h in hits:
        print('   r%-3d %-9s %-4s %s' % h)
