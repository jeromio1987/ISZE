"""_c_final_table.py - final retention table for the report."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

CUR = r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT'
FY = [2026, 2027, 2028, 2029, 2030]
CO = {2026: 43, 2027: 44, 2028: 45, 2029: 46, 2030: 47}
FILES = {'a': CUR + r'\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx',
         'b': CUR + r'\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22b.xlsx',
         'c': CUR + r'\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22c.xlsx'}
ROWS = (54, 69, 88, 90)

D = {}
for tag, p in FILES.items():
    wb = openpyxl.load_workbook(p, data_only=True)
    ws = wb['1.UIO Overview']
    D[tag] = {r: [ws.cell(r, CO[y]).value for y in FY] for r in ROWS}
    D[tag]['base'] = {r: ws.cell(r, 42).value for r in ROWS}
    wb.close()

wb = openpyxl.load_workbook(FILES['c'], data_only=True)
ws = wb['V20 REGS USED']
h = None
for r in range(1, 20):
    if ws.cell(r, 1).value == 'Sheet-1 row':
        h = r
        break
REGS = {}
for r in range(h + 1, h + 60):
    k = ws.cell(r, 1).value
    if not isinstance(k, (int, float)):
        break
    if int(k) in ROWS:
        REGS[int(k)] = [ws.cell(r, 6 + j).value for j in range(5)]
wb.close()

def kseq(v, base, regs):
    out, prev = [], base
    for i in range(5):
        out.append((v[i] - regs[i]) / prev)
        prev = v[i]
    return out

print('%-4s %-9s %-23s %-23s %-23s %-22s' % ('row', 'market', 'candidate a  (k)',
                                             'candidate b  (k)', 'candidate c  (k)', 'regs used in c'))
print('-' * 118)
for r in ROWS:
    base = D['c']['base'][r]
    print('r%-3d' % r)
    # a and b are evaluated on the SAME disclosed input basis (candidate b's sheet),
    # otherwise the comparison is not like-for-like.
    regs_ab = [float(x) for x in (REGS.get(r) or [0] * 5)]
    for tag in ('a', 'b'):
        k = kseq(D[tag][r], base, regs_ab)
        print('     candidate %s  %-30s k = %s' % (
            tag, '[' + ', '.join('%g' % x for x in D[tag][r]) + ']',
            ', '.join('%.4f' % x for x in k)))
    kc = kseq(D['c'][r], base, [float(x) for x in (REGS.get(r) or [0] * 5)])
    print('     candidate c  %-30s k = %s' % (
        '[' + ', '.join('%g' % x for x in D['c'][r]) + ']',
        ', '.join('%.4f' % x for x in kc)))
    print('     regs used in c   %s' % [round(float(x), 3) for x in (REGS.get(r) or [])])
    print()
