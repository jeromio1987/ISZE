"""_b_dedupe.py -- check/report duplicate blocks in the V20 ASSUMPTIONS sheet."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl
CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
CAND_B = CUR + r"\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22b.xlsx"
wb = openpyxl.load_workbook(CAND_B, data_only=True)
wa = wb["V20 ASSUMPTIONS"]
print("dims", wa.dimensions)
for i, row in enumerate(wa.iter_rows(min_row=1, max_row=wa.max_row, max_col=1, values_only=True), 1):
    v = row[0]
    if v:
        print("%3d| %s" % (i, str(v)[:150]))
wb.close()
