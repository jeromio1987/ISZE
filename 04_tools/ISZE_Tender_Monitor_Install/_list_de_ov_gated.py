import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import openpyxl

wb = openpyxl.load_workbook("isuzu_tenders_v3_de.xlsx", read_only=True)
ws = wb["Germany OV"]
rows = list(ws.iter_rows(values_only=True))
h = rows[0]
ti = h.index("Title")
ci = h.index("CPV Code")
print(f"n={len(rows)-1}")
for i, r in enumerate(rows[1:], 1):
    title = (r[ti] or "")[:100]
    print(f"{i:02d} cpv={r[ci]} | {title}")
