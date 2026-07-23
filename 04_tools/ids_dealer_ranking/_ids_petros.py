import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import xlrd
from build_ids_result_report import COL_FIRST_DEALER, COL_MAX, COL_LABEL, COL_TEXT, ROW_META_START, ROW_SCORE_ORIG

# Petros_tb — find cell V41 (col 21, row 40 0-based) and surrounding context
p = Path(r"C:\Users\jerom\Downloads\2026 IDS Evaluation Result Report_Petros_tb.xls")
rb = xlrd.open_workbook(str(p))
sh = rb.sheet_by_index(0)
print("Petros_tb", sh.nrows, sh.ncols, "name", sh.name)
# Excel V41 = col 21 (0-based), row 40
r, c = 40, 21
print(f"V41 value={sh.cell_value(r,c)!r} type={sh.cell_type(r,c)}")
print(f"row41 label A={sh.cell_value(r,0)!r} text={str(sh.cell_value(r,1))[:80]!r} maxC={sh.cell_value(r,2)!r}")
# dealer names row
print("dealers:")
for col in range(COL_FIRST_DEALER, min(sh.ncols, COL_FIRST_DEALER+40)):
    name = str(sh.cell_value(ROW_META_START, col) or "").strip()
    if name:
        print(f"  col{col} ({xlrd.colname(col)}) {name}")
# show row 41 all dealer scores vs max
print("\nRow 41 (Excel 41) all dealer scores:")
mx = sh.cell_value(40, 2)
for col in range(COL_FIRST_DEALER, sh.ncols):
    name = str(sh.cell_value(ROW_META_START, col) or "").strip()
    if not name: continue
    v = sh.cell_value(40, col)
    if v != "" and v is not None:
        print(f"  {name[:30]:30} score={v} max={mx} over={isinstance(v,(int,float)) and isinstance(mx,(int,float)) and v>mx}")

# find any cells where score > max on question rows
print("\nOver-max count sample:")
over = 0
for r in range(14, sh.nrows):
    mx = sh.cell_value(r, 2)
    if not isinstance(mx, (int, float)) or mx <= 0: continue
    for col in range(COL_FIRST_DEALER, sh.ncols):
        v = sh.cell_value(r, col)
        if isinstance(v, (int, float)) and v > mx:
            over += 1
            if over <= 15:
                name = str(sh.cell_value(ROW_META_START, col) or "").strip()
                print(f"  r{r+1} {sh.cell_value(r,0)} {name[:25]} score={v} max={mx}")
print("total over-max cells", over)
