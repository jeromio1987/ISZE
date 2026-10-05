"""
_v20_engine.py - definitive V20 forecast engine (writes nothing; analysis + validation).

Handles the 2014 methodology break in the Ireland/Portugal history:
  V19 stitches an IML backbone (pre-2014) onto a real-registration cohort model (2014+).
  Back-solving across that seam produces a huge negative "cohort" that is not a vehicle.
  Fix: detect the seam, re-base the cohort state at the seam, and treat the legacy block
  as fully retired from the seam on - which is exactly what V19 itself already assumes.
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

V19 = json.load(open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_v20_v19_full.json', encoding='utf-8'))
YEARS = list(range(1990, 2031))
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV_B = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}

def S(c, a): return c.get(a, 0.0) if a >= 1 else 0.0
def curve(mt): return LCV_B if str(mt) == 'LCV' else CV_DEV

def back_solve(series, c, start):
    R = {}
    for t in YEARS:
        if t < start:
            R[t] = 0.0
            continue
        known = sum(R[v] * S(c, t - v + 1) for v in YEARS if start <= v < t)
        R[t] = series[t] - known
    return R

def reproduce(series, c, R, t):
    return sum(R[v] * S(c, t - v + 1) for v in YEARS if v <= t)

def detect_seam(series, c):
    """First year whose back-solved cohort is a large negative -> a source switch, not a vehicle."""
    R = back_solve(series, c, 1990)
    for t in range(1991, 2026):
        if series[t] > 0 and R[t] < 0 and abs(R[t]) > 0.25 * series[t]:
            return t, R
    return 1990, R

def build_state(row):
    mt = row['meta'][3]
    c = curve(mt)
    series = {t: float(row['vals'].get(str(t)) or 0) for t in YEARS}
    seam, _ = detect_seam(series, c)
    R = back_solve(series, c, seam)
    clipped = 0
    for v in YEARS:
        if R[v] < 0:
            R[v] = 0.0
            clipped += 1
    # residual: how well does the clipped state reproduce 2025?
    reb2025 = reproduce(series, c, R, 2025)
    residual = series[2025] - reb2025
    if abs(residual) > 0.5 and series[2025] > 0:
        # absorb into the oldest vintage still alive in 2025 (a legacy-stock term)
        oldest = min([v for v in YEARS if S(c, 2026 - v) > 0] or [2025])
        R[oldest] += residual / S(c, 2026 - oldest)
    return c, series, seam, R, clipped, residual

def recover_v19_regs(row):
    v = {int(k): x for k, x in row['vals'].items()}
    out = {}
    for t in range(2026, 2031):
        prev, cur = v.get(t - 1) or 0, v.get(t) or 0
        out[t] = round(cur - prev * 0.97)
    return out

def smooth_keep_level(x):
    n = len(x)
    sm = []
    for i in range(n):
        if i == 0:      sm.append((x[0] + x[1]) / 2.0)
        elif i == n - 1: sm.append((x[n - 2] + x[n - 1]) / 2.0)
        else:            sm.append((x[i - 1] + x[i] + x[i + 1]) / 3.0)
    tx, ts = sum(x), sum(sm)
    f = (tx / ts) if ts else 1.0
    return [z * f for z in sm]

def roll_forward(c, R, regs):
    """UIO[t] = surviving stock from cohorts < t  +  new cohort t."""
    out = {}
    for t in range(2026, 2031):
        stock = sum(R[v] * S(c, t - v + 1) for v in range(1990, t))
        R[t] = regs[t - 2026]
        out[t] = round(stock + R[t] * S(c, 1))
    return out

OUT_OF_SCOPE = {7, 8}
LEAVE_AS_V19 = {22, 24}
PLAN_ONLY_MD = {27, 52, 80, 89}
UK_LCV_REGS = {2026: 3020, 2027: 2400, 2028: 2400, 2029: 2400, 2030: 2400}

print("=" * 118)
print("%-4s %-9s %-9s %6s %9s %9s | %8s %8s | %9s %9s %9s %9s %9s | seam clip res" % (
    "R", "Country", "Model", "lifeyr", "2025V19", "2025reb", "V19_30", "V20_30",
    "2026", "2027", "2028", "2029", "2030"))
print("=" * 118)

results = {}
for row in V19:
    r = row['row']
    mt = row['meta'][3]
    if r in OUT_OF_SCOPE or r in LEAVE_AS_V19:
        continue
    v = {int(k): x for k, x in row['vals'].items()}
    if all((v.get(t) or 0) == 0 for t in range(2026, 2031)) and (v.get(2025) or 0) == 0:
        continue

    regs = recover_v19_regs(row)
    raw = [regs[t] for t in range(2026, 2031)]

    if r == 25:
        u = {2025: v[2025]}
        for t in range(2026, 2031):
            u[t] = round(u[t - 1] * (1 - 0.123) + UK_LCV_REGS[t])
        v20 = [u[t] for t in range(2026, 2031)]
        results[r] = {'country': row['meta'][1], 'model': mt, 'v20': v20,
                      'v19': [v[t] for t in range(2026, 2031)], 'regs': raw,
                      'regs_used': [UK_LCV_REGS[t] for t in range(2026, 2031)],
                      'seam': None, 'plan_only': False, 'life': sum(LCV_B.values()),
                      'note': 'LOCKED CY2026F=44,926 then 12.3% pickup scrap + IMIT regs'}
        print("%-4d %-9s %-9s %6.2f %9s %9s | %8s %8s | %9s %9s %9s %9s %9s | LOCKED" % (
            r, str(row['meta'][1])[:9], str(mt)[:9], sum(LCV_B.values()), v[2025], '=V19', v[2030], v20[-1],
            *[str(x) for x in v20]))
        continue

    c, series, seam, R, clipped, residual = build_state(row)
    reb2025 = reproduce(series, c, R, 2025)
    regs_used = smooth_keep_level(raw) if r not in PLAN_ONLY_MD else raw
    regs_used = [int(round(x)) for x in regs_used]
    u = roll_forward(c, R, regs_used)
    v20 = [u[t] for t in range(2026, 2031)]
    results[r] = {'country': row['meta'][1], 'model': mt, 'v20': v20,
                  'v19': [v[t] for t in range(2026, 2031)], 'regs': raw, 'regs_used': regs_used,
                  'seam': (seam if seam != 1990 else None), 'plan_only': r in PLAN_ONLY_MD,
                  'life': sum(c.values()), 'note': ''}
    print("%-4d %-9s %-9s %6.2f %9s %9.1f | %8s %8s | %9s %9s %9s %9s %9s | %-5s %-4d %.1f" % (
        r, str(row['meta'][1])[:9], str(mt)[:9], sum(c.values()), v[2025], reb2025,
        v[2030], v20[-1], *[str(x) for x in v20], str(seam if seam != 1990 else '-'), clipped, residual))
print("=" * 118)

json.dump(results, open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_v20_engine.json', 'w', encoding='utf-8'), indent=1)
print("saved _v20_engine.json")
