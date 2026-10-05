"""
V20 - adjudicate the 3 remaining harness failures.

The harness classifies a row as "still on the 3% rule" by testing whether the
successive first differences of 2026-2030 form a constant ratio near 0.97.
During the fleet ACCUMULATION phase (constant registration input, fleet still far
below its ceiling) the survival curve produces near-linear growth with mild
deceleration, whose difference ratio also lands near 0.97-1.00.

So the difference-ratio test cannot distinguish those two. The decisive test is
CONVERGENCE: with constant registrations, a curve row converges to
regs x mean_life (35 x 9.85 = 345); a flat-3% row converges to regs / 0.03
(35 / 0.03 = 1,166). We project both ways and read the asymptote.
"""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
CAND = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx")
V19P = os.path.join(CUR, "ISUZU_UIO_Overview_2026.xlsx")
COLS = {y: 7 + (y - 1990) for y in range(1990, 2031)}
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c,a): return c.get(a,0.0) if a>=1 else 0.0

wc = openpyxl.load_workbook(CAND, data_only=True)['1.UIO Overview']
v19 = openpyxl.load_workbook(V19P, data_only=True)['1.UIO Overview']
V = json.load(open(os.path.join(CUR, "UIO_V20_VERIFY_2026-09-22.json"), encoding='utf-8'))['rows']

FLAGGED = [(33, 'CV'), (54, 'LCV'), (79, 'CV'), (90, 'LCV')]
print("=" * 108)
print("CONVERGENCE TEST - does the row converge to regs x mean_life or to regs / 0.03 ?")
print("=" * 108)
for r, leg in FLAGGED:
    c = LCV if leg == 'LCV' else CV_DEV
    life = sum(c.values())
    p = V[str(r)]
    regs = p['regs_used']
    avg = sum(regs)/len(regs)
    curve_asymptote = avg * life
    flat_asymptote = avg / 0.03
    # project the CANDIDATE's own state forward with constant registrations
    series = {t: float(v19.cell(row=r, column=COLS[t]).value or 0) for t in range(1990, 2031)}
    R = {}
    for t in range(1990, 2031):
        R[t] = series[t] - sum(R[v]*S(c, t-v+1) for v in range(1990, t))
    for v in range(1990, 2031):
        if R[v] < 0: R[v] = 0.0
    for t in range(2026, 2031):
        R[t] = p['v20'][t-2026] - sum(R[v]*S(c, t-v+1) for v in range(1990, t))
    path = {}
    for t in range(2031, 2071):
        stock = sum(R[v]*S(c, t-v+1) for v in range(1990, t))
        R[t] = avg
        path[t] = stock + R[t]*S(c, 1)
    print("\nR%-3d %-9s %-6s  avg regs %6.1f  mean life %.2f" % (r, p['country'][:9], leg, avg, life))
    print("      curve asymptote (regs x life) = %8.0f      flat-3%% asymptote (regs/0.03) = %8.0f" % (
        curve_asymptote, flat_asymptote))
    for t in (2035, 2045, 2055, 2060):
        print("      projected %d: %8.1f" % (t, path[t]))
    nearest = 'CURVE' if abs(path[2060]-curve_asymptote) < abs(path[2060]-flat_asymptote) else 'FLAT 3% RULE'
    print("      => converges to the %s asymptote  %s" % (
        nearest, 'FALSE POSITIVE' if nearest == 'CURVE' else '*** REAL DEFECT ***'))
    # also: is the row still rising because it is below its ceiling?
    print("      candidate 2025=%s 2030=%s ; ceiling=%.0f -> %s" % (
        int(series[2025]), p['v20'][4], curve_asymptote,
        'still accumulating (below ceiling)' if p['v20'][4] < curve_asymptote*0.95 else 'at/near ceiling'))

print("\n" + "=" * 108)
print("CHECK 7 - is the tolerance gap explained by the plan-only MD removal?")
print("=" * 108)
PLAN_ONLY = {27, 52, 80, 89}
MW = {2026: 1, 2027: 2, 2028: 3, 2029: 4, 2030: 5}
print("%-6s %11s %11s %8s | %11s %11s %8s | %s" % (
    "Year", "V19", "V20 as-is", "over%", "V19", "V20 keepMD", "over%", "spec"))
for i, y in enumerate([2026, 2027, 2028, 2029, 2030]):
    a = sum((v19.cell(row=r, column=COLS[y]).value or 0) for r in range(7, 91))
    b = sum((wc.cell(row=r, column=COLS[y]).value or 0) for r in range(7, 91))
    b2 = b + sum(p['v19'][i] for k, p in V.items() if int(k) in PLAN_ONLY)
    print("%-6d %11.0f %11.0f %7.1f%% | %11.0f %11.0f %7.1f%% | %.1f%%" % (
        y, a, b, (a/b-1)*100, a, b2, (a/b2-1)*100, {2026:7.8,2027:15.6,2028:23.2,2029:30.6,2030:37.7}[y]))
