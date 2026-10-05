"""V20 - check whether AQ:AU are formulas or hardcoded, per row (READ ONLY)."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl
from openpyxl.utils import get_column_letter

XL = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx"
wb = openpyxl.load_workbook(XL, data_only=False)
ws = wb['1.UIO Overview']
AQ, AU = 43, 47
print("Row  Country    Model       AQ..AU content")
for r in range(7, 91):
    vals = []
    for c in range(AQ, AU + 1):
        v = ws.cell(row=r, column=c).value
        vals.append(v)
    kinds = set('FORMULA' if isinstance(v, str) and str(v).startswith('=') else ('blank' if v in (None, '') else 'value') for v in vals)
    if kinds - {'blank'}:
        print("%-4d %-10s %-11s %s  [%s]" % (r, str(ws.cell(row=r, column=2).value)[:10],
              str(ws.cell(row=r, column=4).value)[:11], " | ".join(str(v)[:26] for v in vals), ",".join(sorted(kinds))))
print("\n-- rows 22/24 exact formulas --")
for r in (22, 24):
    for c in range(42, 48):
        print("  row %d col %s = %r" % (r, get_column_letter(c), ws.cell(row=r, column=c).value))
print("\n-- row 2 formulas AQ:AU --")
for c in range(AQ, AU + 1):
    print("  %s2 = %s" % (get_column_letter(c), ws.cell(row=2, column=c).value))
print("\n-- row 5 formulas AQ:AU --")
for c in range(43, 44):
    print("  %s5 = %s" % (get_column_letter(c), ws.cell(row=5, column=c).value))
print("\n-- row 6 headers --")
for c in range(40, 50):
    print("  %s6 = %r" % (get_column_letter(c), ws.cell(row=6, column=c).value))
