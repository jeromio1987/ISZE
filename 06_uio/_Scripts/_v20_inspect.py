"""V20 build — inspection of the live V19 workbook. READ ONLY."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl
from openpyxl.utils import get_column_letter

XL = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx"
wb = openpyxl.load_workbook(XL, data_only=False, read_only=False)
print("SHEETS:", wb.sheetnames)
ws = wb['1.UIO Overview']
print("dims rows=%d cols=%d" % (ws.max_row, ws.max_column))

# header rows
for r in range(1, 8):
    vals = []
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=r, column=c).value
        if v is not None:
            s = str(v)
            vals.append("%s:%s" % (get_column_letter(c), s[:40]))
    print("ROW %d (%d cells): %s" % (r, len(vals), " | ".join(vals)))

print("\n--- rows 7..95 meta + last years ---")
for r in range(7, 96):
    meta = [ws.cell(row=r, column=c).value for c in range(1, 7)]
    print("R%-3d %s" % (r, " | ".join("" if m is None else str(m) for m in meta)))
