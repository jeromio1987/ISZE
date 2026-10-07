"""Read the harness matrix.json and write _qa_charts/matrix.csv plus a PASS/FAIL summary."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ops\_qa_charts")
rows = json.loads((QA / "matrix.json").read_text(encoding="utf-8"))

COLS = ["tab", "dimension", "canvas", "datasets", "points", "data_max", "scale_max",
        "arcs_drawn", "waited_a_frame", "rows_lines", "rows_pieces", "applied", "status"]

with (QA / "matrix.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)

c = Counter(r["status"] for r in rows)
print(f"combinations (tab, dimension, canvas): {len(rows)}")
print(f"PASS {c.get('PASS', 0)}   FAIL {c.get('FAIL', 0)}")
print()
fails = [r for r in rows if r["status"] == "FAIL"]
if fails:
    print("FAIL rows:")
    for r in fails:
        print(f"   {r['tab']:<7} {r['dimension']:<10} {r['canvas']:<12} "
              f"datasets {r['datasets']} points {r['points']} data_max {r['data_max']} "
              f"scale_max {r['scale_max']} rows {r['rows_lines']}")
else:
    print("no FAIL rows")
print()
print("per tab:")
for t in sorted({r["tab"] for r in rows}):
    sub = [r for r in rows if r["tab"] == t]
    cc = Counter(r["status"] for r in sub)
    dims = sorted({str(r["dimension"]) for r in sub})
    print(f"   {t:<7} {len(sub):>3} rows  PASS {cc.get('PASS', 0):>3}  FAIL {cc.get('FAIL', 0):>2}  "
          f"dimensions: {', '.join(dims)}")
print()
print("csv:", QA / "matrix.csv")
