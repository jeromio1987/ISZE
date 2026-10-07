# -*- coding: utf-8 -*-
"""B2: discard the spareparts.pt false positives (no product for the number).

spareparts.pt is a domestic-appliance spares shop; its search page shows a price
FILTER widget ("o preco mais alto e EUR x") plus a hard-coded "EUR1.234,56" money
format string. Those are not product prices for our numbers and must not become rows.
"""
from __future__ import annotations
import csv, io, sys
from pathlib import Path
HERE = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\90_INBOX\scrape_targets\_probe\_u26\B2")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
src = HERE / "_part_spareparts.pt.rows.csv"
cols = None
kept = []
with src.open(encoding="utf-8") as f:
    r = csv.reader(f); rows = list(r)
rows = [rows[0]]
with src.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerows(rows)
print("spareparts.pt rows after discard:", len(rows) - 1)
# mark the tried rows for those 3 as false_positive
tp = HERE / "_part_spareparts.pt.tried.csv"
with tp.open(encoding="utf-8") as f:
    tr = list(csv.DictReader(f))
fields = list(tr[0].keys()) if tr else []
n = 0
for t in tr:
    if t["outcome"] == "priced":
        t["outcome"] = "false_positive_price_filter_widget"; n += 1
with tp.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(tr)
print("marked false positives:", n)
# remove the saved pages
for pn in ["116277", "6007306", "14459"]:
    p = HERE / "pages" / f"spareparts.pt__{pn}.html"
    if p.exists(): p.unlink(); print("removed page", p.name)
