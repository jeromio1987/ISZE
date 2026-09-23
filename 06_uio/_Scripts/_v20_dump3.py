"""V20 — dump Data Sources + Changelog + Cover (READ ONLY)."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl
from openpyxl.utils import get_column_letter

XL = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx"
wbv = openpyxl.load_workbook(XL, data_only=True)

def dump(name, maxr=200, maxc=14):
    ws = wbv[name]
    print("\n" + "=" * 100)
    print("SHEET: %s  (%sx%s)" % (name, ws.max_row, ws.max_column))
    print("=" * 100)
    for r in range(1, min(ws.max_row, maxr) + 1):
        cells = []
        for c in range(1, min(ws.max_column, maxc) + 1):
            v = ws.cell(row=r, column=c).value
            if v is None or str(v).strip() == '':
                continue
            cells.append("%s=%s" % (get_column_letter(c), str(v).replace('\n', ' ')[:90]))
        if cells:
            print("R%-3d %s" % (r, " | ".join(cells)))

dump('Data Sources')
dump('Changelog')
