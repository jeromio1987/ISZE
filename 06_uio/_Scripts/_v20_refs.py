"""V20 - inspect summary block rows 93-201 and cross-sheet references (READ ONLY)."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl
from openpyxl.utils import get_column_letter

XL = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx"
wbf = openpyxl.load_workbook(XL, data_only=False)
wbv = openpyxl.load_workbook(XL, data_only=True)

ws = wbf['1.UIO Overview']
ws2 = wbv['1.UIO Overview']
print("=== rows 93-130 : formulas (rows 93-201) ===")
for r in range(93, 131):
    cells = []
    for c in range(1, 14):
        v = ws.cell(row=r, column=c).value
        if v is None or str(v).strip() == '':
            continue
        cells.append("%s=%s" % (get_column_letter(c), str(v).replace('\n', ' ')[:60]))
    if cells:
        print("R%-3d %s" % (r, " | ".join(cells)))

print("\n=== any formula anywhere referencing AQ:AU of sheet 1, or other cross-sheet links ===")
import re
for sn in wbf.sheetnames:
    w = wbf[sn]
    hits = []
    for row in w.iter_rows():
        for cell in row:
            v = cell.value
            if isinstance(v, str) and v.startswith('='):
                if re.search(r"(AQ|AR|AS|AT|AU)\d", v) or "'1.UIO Overview'" in v or 'UIO Overview' in v:
                    hits.append((cell.coordinate, v[:110]))
    if hits:
        print("\n-- sheet %r : %d hits" % (sn, len(hits)))
        for co, v in hits[:25]:
            print("   %s: %s" % (co, v))
