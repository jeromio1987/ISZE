# -*- coding: utf-8 -*-
"""Step 8 verification — every row in the change-log table vs the header cell count."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")
lines = P.read_text(encoding="utf-8").split("\n")

hdr_i = next(i for i, l in enumerate(lines) if l.strip() == "| Time | Agent | What changed | Files touched | Next step |")
n_hdr = lines[hdr_i].strip().strip("|").count("|") + 1
print(f"header line {hdr_i + 1}: {n_hdr} cells")
print(f"separator line {hdr_i + 2}: {lines[hdr_i + 1].strip()}")
sep_cells = lines[hdr_i + 1].strip().strip("|").count("|") + 1
print(f"separator cells: {sep_cells}")

i = hdr_i + 2
rows = []
while i < len(lines) and lines[i].lstrip().startswith("|"):
    cells = lines[i].strip().strip("|").count("|") + 1
    rows.append((i + 1, cells, lines[i]))
    i += 1

print(f"table rows: {len(rows)}")
bad = [(ln, c, t) for ln, c, t in rows if c != n_hdr]
print(f"rows whose cell count differs from the header: {len(bad)}")
for ln, c, t in bad:
    print(f"   line {ln}: {c} cells -> {t[:120]}")

print(f"\nthe repaired row (line 22): {rows[0][1]} cells")

# the row I was told to repair, checked specifically
tgt = [t for _, _, t in rows if t.startswith("| 2026-09-24 12:50 | cursor (scraper Phase 0) |")]
print(f"\ntarget row pipe count: {tgt[0].count('|')} (the table takes 6)")
print(f"target row still names its time/agent: {tgt[0].split('|')[1].strip()!r}, {tgt[0].split('|')[2].strip()!r}")
print(f"'Eucon password still to change.' kept: {'Eucon password still to change.' in tgt[0]}")
