"""V20 - why do some rows sit above their registration ceiling? Check the direction after 2030."""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
V = json.load(open(os.path.join(CUR, "UIO_V20_VERIFY_2026-09-22.json"), encoding='utf-8'))
ROWS = V['rows']
V19 = json.load(open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_v20_v19_full.json', encoding='utf-8'))
BYROW = {r['row']: r for r in V19}
YEARS = list(range(1990, 2031))
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c,a): return c.get(a,0.0) if a>=1 else 0.0
def curve(mt): return LCV if mt=='LCV' else CV_DEV

def state(r, mt):
    row = BYROW[r]; c = curve(mt)
    series = {t: float(row['vals'].get(str(t)) or 0) for t in YEARS}
    R = {}
    for t in YEARS:
        R[t] = series[t] - sum(R[v]*S(c,t-v+1) for v in YEARS if v < t)
    for v in YEARS:
        if R[v] < 0: R[v] = 0.0
    return c, R, series

print("=" * 112)
print("ROWS SITTING ABOVE THEIR REGISTRATION CEILING - is the direction correct?")
print("=" * 112)
for r, mt in [(18,'LCV'), (60,'LCV'), (81,'LCV'), (61,'LD'), (9,'LCV'), (25,'LCV'), (35,'LCV'), (44,'LCV')]:
    c, R, series = state(r, mt)
    p = ROWS[str(r)]
    used = p['regs_used']
    avg = sum(used)/len(used)
    ceil = avg*sum(c.values())
    # extend the model past 2030 holding the same registrations
    Rext = dict(R)
    path = {}
    for t in range(2026, 2041):
        stock = sum(Rext[v]*S(c,t-v+1) for v in range(1990, t))
        Rext[t] = avg
        path[t] = round(stock + Rext[t]*S(c,1))
    print("\nR%-3d %-9s %-6s  ceiling(avg regs x life) = %6.0f   (avg regs %.0f, life %.2f)" % (
        r, p['country'][:9], mt, ceil, avg, sum(c.values())))
    print("     big recent cohorts:", [(t, round(R[t])) for t in range(2018, 2026) if R[t] > 1.3*avg])
    print("     V20 path 2025-2040:", {t: path[t] for t in range(2026, 2041, 3)})
    peak = max(path, key=lambda t: path[t])
    print("     peak in %d, then direction = %s" % (peak, 'DOWN' if peak < 2040 else 'still rising'))
