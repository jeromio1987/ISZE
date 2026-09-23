"""_c_dump.py - read-only dump of candidate a/b rows of interest + V20 REGS USED."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

CUR = r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT'
FILES = {
    'a': CUR + r'\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx',
    'b': CUR + r'\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22b.xlsx',
    'v19': CUR + r'\ISUZU_UIO_Overview_2026.xlsx',
}
ROWS = [26, 29, 51, 54, 79, 88, 90, 33, 25]
Y0 = 1990
C0 = 7  # col G = 1990

def coly(y): return C0 + (y - Y0)

out = {}
for tag, p in FILES.items():
    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    ws = wb['1.UIO Overview']
    grid = {}
    for r in range(1, 91):
        grid[r] = {}
        for y in range(1990, 2031):
            grid[r][y] = ws.cell(r, coly(y)).value
    rows = {}
    for r in ROWS:
        meta = [ws.cell(r, c).value for c in range(1, 7)]
        rows[r] = {'meta': meta, 'vals': {y: grid[r][y] for y in range(1990, 2031)}}
    out[tag] = rows
    wb.close()

for tag in ['v19', 'a', 'b']:
    print('=' * 140)
    print('CANDIDATE', tag)
    print('=' * 140)
    for r in ROWS:
        m = out[tag][r]['meta']
        v = out[tag][r]['vals']
        print('r%-3d %s' % (r, m))
        hist = [v[y] for y in range(2005, 2026)]
        fc = [v[y] for y in range(2026, 2031)]
        print('   2005-2025:', hist)
        print('   2026-2030:', fc)
        # retention k solved with regs recovered from V19 flat rule
        k = []
        for y in range(2027, 2031):
            prev = v.get(y - 1) or 0
            cur = v.get(y) or 0
            if prev:
                k.append((y, round(cur / prev, 6)))
        print('   raw k (UIO_t/UIO_t-1):', k)
    print()

# V20 REGS USED sheet in b
wb = openpyxl.load_workbook(FILES['b'], data_only=True)
print('=' * 140)
print('b sheet: V20 REGS USED  (dims %s)' % wb['V20 REGS USED'].dimensions)
print('=' * 140)
ws = wb['V20 REGS USED']
for r in range(1, ws.max_row + 1):
    vals = [ws.cell(r, c).value for c in range(1, min(ws.max_column, 30) + 1)]
    if any(x is not None for x in vals):
        print(r, vals)
