import openpyxl, sys, json, re
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- Warranty CV: ITUK / UTI sheets + per-DST EUR parts totals from Sheet1
wb = openpyxl.load_workbook(r"C:\Users\jerom\Desktop\claude\ISZE\Data\Warranty_CV_2025.xlsx", read_only=True)
for nm in ["ITUK", "UTI", "Sheet3", "Sheet4"]:
    ws = wb[nm]
    print(f"--- sheet {nm} ({ws.max_row} x {ws.max_column})")
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=8, max_col=10, values_only=True)):
        vals = ["" if v is None else str(v)[:22] for v in row]
        if any(v != "" for v in vals):
            print(" | ".join(vals))
    print()
wb.close()

# --- UIO v17 with E/F suffix years
wb = openpyxl.load_workbook(r"C:\Users\jerom\Desktop\claude\ISZE\Data\ISUZU_UIO_Overview_2026_v17.xlsx", data_only=True, read_only=True)
ws = wb["1.UIO Overview"]
all_rows = list(ws.iter_rows(values_only=True))
hdr_i = next(i for i, r in enumerate(all_rows) if r[0] is not None and "Ctry" in str(r[0]))
hdr = all_rows[hdr_i]
ycols = {}
for j, h in enumerate(hdr):
    m = re.match(r"^\s*(\d{4})[EF]?\s*$", str(h or ""))
    if m and 2024 <= int(m.group(1)) <= 2028:
        ycols[int(m.group(1))] = j
agg = defaultdict(lambda: defaultdict(float))
for r in all_rows[hdr_i+1:]:
    if r[1] is None or r[5] is None: continue
    key = (str(r[1]).strip(), str(r[5]).strip(), str(r[3] or "").strip())
    for y, j in ycols.items():
        if isinstance(r[j], (int, float)):
            agg[key][y] += r[j]
out = [{"country": k[0], "dist": k[1], "mtype": k[2], **{str(y): round(v, 1) for y, v in yv.items()}} for k, yv in sorted(agg.items())]
json.dump(out, open(r"C:\Users\jerom\Desktop\claude\ISZE\Data\_build\uio_2026.json", "w"), indent=0)
for o in out:
    print(o)
wb.close()
