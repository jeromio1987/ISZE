"""_b_prov.py -- full provenance text + IML 1.UIO for the target countries."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
V19 = CUR + r"\ISUZU_UIO_Overview_2026.xlsx"
IML = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\IML calculation (1).xlsx"

wb = openpyxl.load_workbook(V19, data_only=True)
ws = wb["Assumptions & Mapping"]
print("### V19 'Assumptions & Mapping' — full text, rows 28-80, cols A-E ###")
for r in range(28, 80):
    cells = [ws.cell(r, c).value for c in range(1, 6)]
    if any(x not in (None, "") for x in cells):
        print("r%-3d %s" % (r, " || ".join("" if x is None else str(x) for x in cells)))
wb.close()

wb = openpyxl.load_workbook(IML, data_only=True)
ws = wb["1.UIO"]
print("\n### IML 1.UIO header rows 1-6 ###")
for r in range(1, 7):
    print("r%d %s" % (r, [ws.cell(r, c).value for c in range(1, 22)]))
print("\n### IML 1.UIO rows containing codes 230 / 233 / 217 / 208 ###")
for r in range(1, ws.max_row + 1):
    c1 = ws.cell(r, 1).value
    if isinstance(c1, (int, float)) and int(c1) in (230, 233, 217, 208, 206, 205):
        row = [ws.cell(r, c).value for c in range(1, 22)]
        print("  r%-4d %s" % (r, [None if x is None else (round(x, 1) if isinstance(x, float) else x) for x in row]))
wb.close()
