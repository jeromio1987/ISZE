# -*- coding: utf-8 -*-
"""B2: discard the isuzu.pt false positive.

Searching competitor "P 34 013" on www.isuzu.pt returned the D-MAX homepage, whose
finance banner says "DESDE 345EUR +IVA/mes" (a monthly vehicle price, not a part
price). Not an observation of our competitor number.
"""
from __future__ import annotations
import csv, io, sys
from pathlib import Path
HERE = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\90_INBOX\scrape_targets\_probe\_u26\B2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rp = HERE / "_part_www.isuzu.pt.rows.csv"
with rp.open(encoding="utf-8") as f:
    rows = list(csv.reader(f))
with rp.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(rows[0])
print("isuzu.pt rows after discard:", 0)
tp = HERE / "_part_www.isuzu.pt.tried.csv"
with tp.open(encoding="utf-8") as f:
    tr = list(csv.DictReader(f)); fields = list(tr[0].keys())
for t in tr:
    if t["outcome"] == "priced":
        t["outcome"] = "false_positive_homepage_finance_banner"
with tp.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(tr)
p = HERE / "pages" / "www.isuzu.pt__P 34 013.html"
if p.exists(): p.unlink(); print("removed", p.name)
