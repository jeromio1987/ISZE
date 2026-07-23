import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import xlrd
from build_ids_result_report import COL_FIRST_DEALER, ROW_META_START, COL_LABEL, COL_MAX

ours = Path(r"..\..\01_data\90_INBOX\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_Romania.xls")
tb = Path(r"C:\Users\jerom\Downloads\2026 IDS Evaluation Result Report_Romania_tb.xls")

def load(path):
    rb = xlrd.open_workbook(str(path))
    sh = rb.sheet_by_index(0)
    dealers = {}
    for c in range(COL_FIRST_DEALER, sh.ncols):
        name = str(sh.cell_value(ROW_META_START, c) or "").strip()
        if name: dealers[name] = c
    return sh, dealers

sh_o, d_o = load(ours)
sh_t, d_t = load(tb)
print("dealers match", set(d_o)==set(d_t), "n", len(d_o))
# compare all question cells
diffs = []
for name in sorted(d_o):
    co, ct = d_o[name], d_t[name]
    for r in range(14, min(sh_o.nrows, sh_t.nrows)):
        vo, vt = sh_o.cell_value(r, co), sh_t.cell_value(r, ct)
        # normalize blanks
        if vo == "": vo = None
        if vt == "": vt = None
        if vo != vt:
            # skip if both numeric equal
            try:
                if float(vo)==float(vt): continue
            except Exception:
                pass
            ref = sh_o.cell_value(r, 0)
            diffs.append((name, r+1, ref, vo, vt))
print("cell diffs", len(diffs))
for d in diffs[:40]:
    print(d)

# also compare vs source parse for 2 dealers
from build_ids_result_report import parse_dealer_workbook, collect_dealer_files
from ids_paths import resolve_input_dir
# find romania folder
ro = Path(r"..\..\01_data\90_INBOX\IDS_2026\Romania")
files = list(ro.rglob("*.xlsx")) + list(ro.rglob("*.xls"))
print("\nRomania source files", len(files))
for f in files[:5]:
    print(" ", f.name)
