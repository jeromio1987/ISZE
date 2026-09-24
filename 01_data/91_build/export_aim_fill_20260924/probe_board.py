# -*- coding: utf-8 -*-
"""Read-only: count cells per row in the DELEGATOR_BOARD change-log table."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")
text = P.read_text(encoding="utf-8")
lines = text.split("\n")
print("total lines:", len(lines))
print("bytes:", P.stat().st_size)
hdr_i = None
for i, l in enumerate(lines, 1):
    if l.strip() == "| Time | Agent | What changed | Files touched | Next step |":
        hdr_i = i
        break
print("header at line", hdr_i, "cells:", lines[hdr_i - 1].count("|") + 1 - 1)
# the separator line follows
sep = lines[hdr_i]
print("separator:", repr(sep))
n_hdr = lines[hdr_i - 1].strip().strip("|").count("|") + 1
print("header cells:", n_hdr)
bad = []
i = hdr_i + 1
while i < len(lines) and lines[i].lstrip().startswith("|"):
    cells = lines[i].strip().strip("|").count("|") + 1
    if cells != n_hdr:
        bad.append((i + 1, cells, lines[i][:90]))
    i += 1
print("table rows:", i - hdr_i - 1)
print("rows whose cell count differs from the header:", len(bad))
for b in bad:
    print("   line", b[0], "cells", b[1], "|", b[2])
print()
print("raw of line 22:")
print(repr(lines[21]))
print()
print("raw of line 27:")
print(repr(lines[26]))
