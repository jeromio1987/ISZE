"""Pull the Israel rows (LD / MD / LCV) out of the live workbook's 1.UIO Overview by year."""
from __future__ import annotations

import csv
from pathlib import Path

WB = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922\_wb\1-UIO_Overview.tsv")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922")

rows = list(csv.reader(WB.open(encoding="utf-8"), delimiter="\t"))
print("total rows:", len(rows))

hdr = rows[5]  # row 6 = header
print("header:", hdr[:12], "...", hdr[-6:])
year_col = {}
for i, h in enumerate(hdr):
    try:
        year_col[int(str(h).strip())] = i
    except Exception:
        pass
print("years found:", min(year_col), "->", max(year_col), "count", len(year_col))

targets = {"ISRAEL"}
out = {}
for ri, r in enumerate(rows, start=1):
    if len(r) > 3 and str(r[1]).strip() in targets:
        key = f"{r[2]}_{r[3]}"
        out[key] = {y: (r[c] if c < len(r) else "") for y, c in year_col.items()}
        print(f"\nrow {ri}: ctry={r[0]} {r[1]} {r[2]} {r[3]} dist={r[5]}")

all_years = sorted(year_col)
print("\nYears:", all_years)
for key, series in out.items():
    print(f"\n=== ISRAEL {key} ===")
    for y in all_years:
        v = series.get(y, "")
        print(f"  {y}: {v}")

with (OUT / "israel_model_rows.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["segment"] + all_years)
    for key, series in out.items():
        w.writerow([key] + [series.get(y, "") for y in all_years])
print("\nwrote:", OUT / "israel_model_rows.csv")
