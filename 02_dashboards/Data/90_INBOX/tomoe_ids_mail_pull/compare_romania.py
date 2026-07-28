import sys
from pathlib import Path

import xlrd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOMOE = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\tomoe_ids_mail_pull\20260724_1543_2026_IDS_Evaluation_Result_Report_Romania_tb.xls"
)
OURS = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\reports\evaluation_result\2026 IDS Evaluation Result Report_Romania.xls"
)
RO_SRC = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_2026\Romania")


def col_letter(c0: int) -> str:
    s = ""
    c = c0 + 1
    while c:
        c, r = divmod(c - 1, 26)
        s = chr(65 + r) + s
    return s


def main_sheet(path: Path):
    wb = xlrd.open_workbook(str(path))
    for sn in wb.sheet_names():
        if "oman" in sn.lower() or sn.endswith("26"):
            return wb.sheet_by_name(sn), sn, wb
    return wb.sheet_by_index(0), wb.sheet_names()[0], wb


sh_t, n_t, _ = main_sheet(TOMOE)
sh_o, n_o, _ = main_sheet(OURS)
print("tomoe", n_t, sh_t.nrows, sh_t.ncols)
print("ours", n_o, sh_o.nrows, sh_o.ncols)

print("\nDealer headers:")
for c in range(3, min(sh_t.ncols, 20)):
    vt = sh_t.cell_value(2, c)
    vo = sh_o.cell_value(2, c) if c < sh_o.ncols else ""
    print(f"  {col_letter(c)} ({c}): tomoe={vt!r} ours={vo!r}")

# Full cell diffs
diffs = []
for r in range(min(sh_t.nrows, sh_o.nrows)):
    for c in range(min(sh_t.ncols, sh_o.ncols)):
        vt = sh_t.cell_value(r, c)
        vo = sh_o.cell_value(r, c)
        # normalize
        if isinstance(vt, float) and isinstance(vo, float):
            if abs(vt - vo) < 1e-6:
                continue
        elif str(vt).strip() == str(vo).strip():
            continue
        elif vt == "" and vo == "":
            continue
        label = sh_t.cell_value(r, 0)
        diffs.append((r, c, col_letter(c), label, vt, vo))

print(f"\nTotal cell diffs: {len(diffs)}")
for d in diffs[:80]:
    print(f"  r{d[0]} {d[2]} {d[3]!r}: tomoe={d[4]!r} ours={d[5]!r}")

# Focus column P (=15)
print("\n=== Column P detail (blank vs points) ===")
for r in range(sh_t.nrows):
    vt = sh_t.cell_value(r, 15) if 15 < sh_t.ncols else ""
    vo = sh_o.cell_value(r, 15) if 15 < sh_o.ncols else ""
    label = sh_t.cell_value(r, 0)
    code = sh_t.cell_value(r, 1) if sh_t.ncols > 1 else ""
    if vt != "" or vo != "":
        mark = "DIFF" if vt != vo and not (
            isinstance(vt, float) and isinstance(vo, float) and abs(vt - vo) < 1e-6
        ) else "ok"
        if mark == "DIFF" or r < 20:
            print(f"  {mark} r{r} {label!r}: tomoe={vt!r} ours={vo!r}")

# List Romania source files
print("\nRomania source files:")
for f in sorted(RO_SRC.glob("*")):
    if f.is_file() and not f.name.startswith("~"):
        print(" ", f.name, f.stat().st_size)
