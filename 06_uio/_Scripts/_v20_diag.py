"""V20 - diagnostics: negative cohorts, Ireland/Portugal acceptance test, SIMI."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

V19 = json.load(open(r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\_v20_v19_full.json', encoding='utf-8'))
BYROW = {r['row']: r for r in V19}
YEARS = list(range(1990, 2031))
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV_B = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}

def S(c, a): return c.get(a, 0.0) if a >= 1 else 0.0

def back(series, c):
    R = {}
    for i, t in enumerate(YEARS):
        known = sum(R[v] * S(c, t - v + 1) for v in YEARS[:i] if R.get(v))
        R[t] = series[t] - known
    return R

print("=" * 104)
print("A. NEGATIVE BACK-SOLVED COHORTS - where and how big")
print("=" * 104)
for r in [12, 15, 18, 21, 26, 29, 35, 42, 44, 51, 54, 60, 63, 66, 69, 75, 81, 88, 90, 58]:
    row = BYROW[r]
    mt = row['meta'][3]
    c = LCV_B if mt == 'LCV' else CV_DEV
    series = {t: (row['vals'].get(str(t)) or 0) for t in YEARS}
    R = back(series, c)
    negs = [(t, round(R[t], 1)) for t in range(1990, 2026) if R[t] < -0.5]
    tot_neg = sum(v for _, v in negs)
    # how much of 2026 do the negative cohorts contribute?
    contrib = sum(v * S(c, 2026 - t + 1) for t, v in negs)
    last_relevant = max([t for t in range(1990, 2026) if S(c, 2026 - t + 1) > 0] or [0])
    print("R%-3d %-9s %-9s  negs=%-2d total=%-10.1f  their 2026 contribution=%.1f   oldest cohort alive in 2026 = %d" % (
        r, str(row['meta'][1])[:9], str(mt)[:9], len(negs), tot_neg, contrib, last_relevant))
    if negs:
        print("      ", negs[:14])

print("\n" + "=" * 104)
print("B. IRELAND / PORTUGAL - full V19 series (the acceptance test rows)")
print("=" * 104)
for r in [26, 29, 51, 53, 54, 28]:
    row = BYROW[r]
    print("\nR%-3d %s / %s" % (r, row['meta'][1], row['meta'][3]))
    for t in range(2010, 2031):
        print("      %d: %s" % (t, row['vals'].get(str(t))))

print("\n" + "=" * 104)
print("C. SIMI Ireland (isuzuregdata.xlsx)")
print("=" * 104)
SIMI = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\07_UIO\isuzuregdata.xlsx"
wb = openpyxl.load_workbook(SIMI, data_only=True)
print("sheets:", wb.sheetnames)
from openpyxl.utils import get_column_letter
for sn in wb.sheetnames:
    ws = wb[sn]
    print("\n--- sheet %r (%dx%d)" % (sn, ws.max_row, ws.max_column))
    for r in range(1, min(ws.max_row, 40) + 1):
        cells = []
        for c in range(1, min(ws.max_column, 20) + 1):
            v = ws.cell(row=r, column=c).value
            if v is None or str(v).strip() == '':
                continue
            cells.append("%s=%s" % (get_column_letter(c), str(v)[:16]))
        if cells:
            print("  R%-3d %s" % (r, " | ".join(cells)))
