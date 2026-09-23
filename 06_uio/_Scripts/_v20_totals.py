"""V20 - grand total reconstruction and V19 vs V20 comparison."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

V19 = json.load(open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_v20_v19_full.json', encoding='utf-8'))
ENG = json.load(open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_v20_engine.json', encoding='utf-8'))
ENG = {int(k): v for k, v in ENG.items()}
FY = [2026, 2027, 2028, 2029, 2030]
MIDI_ROWS = {55, 56, 57, 58, 59, 60, 67, 68, 78}   # ASC/DB = MIDI
PLAN_ONLY = {27, 52, 80, 89}

def v19_val(r, y):
    row = next(x for x in V19 if x['row'] == r)
    return float(row['vals'].get(str(y)) or 0)

def v20_val(r, y):
    if r in ENG:
        return float(ENG[r]['v20'][FY.index(y)])
    return v19_val(r, y)      # untouched rows

ROWS = list(range(7, 91))

def total(vals, include_midi, drop_plan_only):
    t = 0.0
    for r in ROWS:
        if r in MIDI_ROWS and not include_midi:
            continue
        if r in PLAN_ONLY and drop_plan_only:
            continue
        t += vals(r)
    return t

print("=" * 104)
print("GRAND TOTAL - V19 vs V20")
print("=" * 104)
hdr = "%-6s %14s %14s %12s | %14s %14s %12s" % (
    "Year", "V19 incl MIDI", "V20 incl MIDI", "diff %", "V19 ex-MIDI", "V20 ex-MIDI", "diff %")
print(hdr)
print("-" * 104)
v19i, v20i, v19e, v20e = {}, {}, {}, {}
for y in FY:
    v19i[y] = total(lambda r: v19_val(r, y), True, False)
    v20i[y] = total(lambda r: v20_val(r, y), True, True)
    v19e[y] = total(lambda r: v19_val(r, y), False, False)
    v20e[y] = total(lambda r: v20_val(r, y), False, True)
    print("%-6d %14.0f %14.0f %11.1f%% | %14.0f %14.0f %11.1f%%" % (
        y, v19i[y], v20i[y], (v20i[y] / v19i[y] - 1) * 100,
        v19e[y], v20e[y], (v20e[y] / v19e[y] - 1) * 100))

print("\n" + "=" * 104)
print("WHAT MAKES UP THE DIFFERENCE (2026 and 2030) - by row")
print("=" * 104)
for y in (2026, 2030):
    deltas = []
    for r in ROWS:
        d = v20_val(r, y) - v19_val(r, y)
        if abs(d) > 0.5:
            deltas.append((d, r))
    deltas.sort()
    print("\n--- %d : rows that move (down first) ---" % y)
    print("%-5s %-10s %-6s %-11s %10s %10s %10s  %s" % ("R", "Country", "CV", "Model", "V19", "V20", "delta", "scope"))
    for d, r in deltas:
        row = next(x for x in V19 if x['row'] == r)
        scope = []
        if r in MIDI_ROWS: scope.append('MIDI')
        if r in PLAN_ONLY: scope.append('PLAN-ONLY->out of GT')
        if r == 25: scope.append('LOCKED row 25')
        print("%-5d %-10s %-6s %-11s %10.0f %10.0f %10.0f  %s" % (
            r, str(row['meta'][1])[:10], str(row['meta'][2])[:6], str(row['meta'][3])[:11],
            v19_val(r, y), v20_val(r, y), d, ", ".join(scope)))
    print("  sum of moves = %.0f" % sum(d for d, _ in deltas))

json.dump({'v19_incl': v19i, 'v20_incl': v20i, 'v19_ex': v19e, 'v20_ex': v20e},
          open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_v20_totals.json', 'w'), indent=1)
print("\nsaved _v20_totals.json")
