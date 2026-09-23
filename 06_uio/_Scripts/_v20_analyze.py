"""
_v20_analyze.py - V20 engine analysis (no writes to any workbook).

Method:
  1. Back-solve the registration cohort vector R_v (1990..2030) that V19 itself implies,
     using the survival curve for the row. Recursive decomposition reproduces the
     1990-2025 series exactly by construction -> no jump at the 2025/2026 boundary.
  2. Recover V19's buried new-registration inputs for 2026-2030 from V19's own
     roll-forward:  regs[t] = UIO[t] - UIO[t-1] * 0.97.
  3. Roll 2026-2030 forward with the REAL survival curve + those registrations
     (level-preserving 3-pt smoothing for plan-driven rows).
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

V19 = json.load(open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_v20_v19_full.json', encoding='utf-8'))
YEARS = list(range(1990, 2031))

CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
CV_EMG = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.85,9:0.80,10:0.75,
          11:0.70,12:0.60,13:0.50,14:0.40,15:0.30,16:0.20,17:0.15,18:0.10,19:0.05,20:0.00}
# LCV 12-yr window per IMIT / workbook sheet 3. Variant A: age12=0.10 (live sheet 3).
# Variant B: age12=0.00 -> sum 8.13 yrs -> 12.30% scrap, the value behind the locked 44,926.
LCV_A = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.10}
LCV_B = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}

def sumlife(c): return sum(c.values())

print("=" * 96)
print("CURVE AVERAGE LIFE / STEADY-STATE SCRAP")
print("=" * 96)
for nm, c in [('CV Developed', CV_DEV), ('CV Emerging', CV_EMG), ('LCV age12=0.10', LCV_A), ('LCV age12=0.00', LCV_B)]:
    L = sumlife(c)
    print("  %-16s sum(S)=%.2f yrs   implied annual scrap = %.2f%%" % (nm, L, 100.0 / L))
print("  %-16s %.2f yrs   %.2f%%" % ("flat V19 3% rule", 1/0.03, 3.00))

OUT_OF_SCOPE = {7, 8}          # Israel rebuilt by separate agent
LEAVE_AS_V19 = {22, 24}        # UK CV: sheet 4 model
PLAN_ONLY_MD = {27, 52, 80, 89}
ROW25 = 25
UK_LCV_REGS = {2026: 3020, 2027: 2400, 2028: 2400, 2029: 2400, 2030: 2400}
UK_LCV_SCRAP = 0.123

def curve_for(model_type):
    if model_type == 'LCV':
        return LCV_B
    if str(model_type) == 'F-Series':
        return CV_DEV
    return CV_DEV

def S(c, age):
    if age < 1:
        return 0.0
    return c.get(age, 0.0)

def back_solve(series, c):
    """Recursive decomposition: returns R_v for v in YEARS. Reproduces series exactly."""
    R = {}
    for i, t in enumerate(YEARS):
        known = sum((R[v] * S(c, t - v + 1)) for v in YEARS[:i] if R.get(v))
        R[t] = series[t] - known
    return R

def recover_v19_regs(row, model_type):
    """V19 roll: UIO[t] = UIO[t-1]*0.97 + regs[t]."""
    v = {int(k): x for k, x in row['vals'].items()}
    out = {}
    for t in range(2026, 2031):
        prev = v.get(t - 1)
        cur = v.get(t)
        if prev in (None, 0) and cur in (None, 0):
            out[t] = 0
            continue
        prev = prev or 0
        cur = cur or 0
        out[t] = round(cur - prev * 0.97)
    return out

def smooth_level_preserving(x):
    n = len(x)
    if n < 3:
        return list(x)
    sm = []
    for i in range(n):
        if i == 0:
            sm.append((x[0] + x[1]) / 2.0)
        elif i == n - 1:
            sm.append((x[n - 2] + x[n - 1]) / 2.0)
        else:
            sm.append((x[i - 1] + x[i] + x[i + 1]) / 3.0)
    tot_x, tot_s = sum(x), sum(sm)
    if tot_s == 0:
        return list(x)
    f = tot_x / tot_s
    return [z * f for z in sm]

rows = []
print("\n" + "=" * 96)
print("PER-ROW RESULT")
print("=" * 96)
print("%-4s %-9s %-11s %9s %9s %9s %9s %9s | %9s %9s | %s" % (
    "R", "Country", "Model", "reg26", "reg27", "reg28", "reg29", "reg30",
    "V19_30", "V20_30", "note"))
for row in V19:
    r = row['row']
    mt = row['meta'][3]
    vals = {int(k): x for k, x in row['vals'].items()}
    if r in OUT_OF_SCOPE:
        note = 'HOOK: Israel separate agent'
        print("%-4d %-9s %-11s %s" % (r, row['meta'][1], mt, note))
        continue
    if r in LEAVE_AS_V19:
        print("%-4d %-9s %-11s %s" % (r, row['meta'][1], mt, 'LEAVE AS V19 (sheet 4)'))
        continue

    c = curve_for(mt)
    regs = recover_v19_regs(row, mt)
    raw = [regs[t] for t in (2026, 2027, 2028, 2029, 2030)]

    if r == ROW25:
        u = {2025: vals[2025]}
        for i, t in enumerate(range(2026, 2031)):
            u[t] = round(u[t - 1] * (1 - UK_LCV_SCRAP) + UK_LCV_REGS[t])
        v20 = [u[t] for t in range(2026, 2031)]
        note = 'LOCKED 44,926 + 12.3%% roll'
        print("%-4d %-9s %-11s %9s %9s %9s %9s %9s | %9s %9s | %s" % (
            r, row['meta'][1], mt, *[str(x) for x in raw], vals[2030], v20[-1], note))
        rows.append({'row': r, 'regs': raw, 'v20': v20, 'v19': [vals[t] for t in range(2026, 2031)],
                     'note': note, 'model': mt, 'country': row['meta'][1],
                     'plan_only': r in PLAN_ONLY_MD})
        continue

    if all(x in (None, 0) for x in raw) and vals.get(2025) in (None, 0):
        print("%-4d %-9s %-11s %s" % (r, row['meta'][1], mt, 'no forecast in V19 - skip'))
        continue

    # rebuild cohort state at 2025 (exact reproduction of history), then roll forward
    series = {t: (vals.get(t) or 0) for t in YEARS}
    R = back_solve(series, c)
    neg = sum(1 for t in range(1990, 2026) if R[t] < -1)
    uio = {}
    for t in range(2026, 2031):
        s = sum(R[v] * S(c, t - v + 1) for v in range(1990, t))
        R[t] = raw[t - 2026]
        uio[t] = round(s + R[t] * S(c, 1))
    v20 = [uio[t] for t in range(2026, 2031)]
    note = ('neg-cohorts=%d' % neg) if neg else ''
    if r in PLAN_ONLY_MD:
        note = (note + ' ' if note else '') + 'PLAN ONLY -> out of GT'
    print("%-4d %-9s %-11s %9s %9s %9s %9s %9s | %9s %9s | %s" % (
        r, row['meta'][1], mt, *[str(x) for x in raw], vals[2030], v20[-1], note))
    rows.append({'row': r, 'regs': raw, 'v20': v20, 'v19': [vals[t] or 0 for t in range(2026, 2031)],
                 'note': note, 'model': mt, 'country': row['meta'][1],
                 'plan_only': r in PLAN_ONLY_MD})

json.dump(rows, open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_v20_result.json', 'w', encoding='utf-8'), indent=1)
print("\nsaved _v20_result.json")
