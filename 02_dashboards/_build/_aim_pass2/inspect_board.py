"""Inspect the change-log table in DELEGATOR_BOARD.md without touching it."""
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

P = r"00_docs\agent\DELEGATOR_BOARD.md"
t = open(P, "rb").read().decode("utf-8")
lines = t.split("\n")

# find every markdown table header row and what follows it
starts = []
for i, l in enumerate(lines):
    s = l.strip()
    if s.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set("|-: "):
        starts.append(i)

print(f"tables found: {len(starts)}")
for st in starts:
    # collect the table
    j = st
    rows = []
    while j < len(lines) and lines[j].strip().startswith("|"):
        rows.append(lines[j])
        j += 1
    cells = Counter(len(r.strip().strip("|").split("|")) for r in rows)
    print(f"  line {st + 1}: {len(rows)} rows, cells {dict(cells)}")
    print(f"     header: {rows[0][:150]}")

# the change-log table: header contains Time
for st in starts:
    if "time" in lines[st].lower():
        j = st
        rows = []
        while j < len(lines) and lines[j].strip().startswith("|"):
            rows.append(j)
            j += 1
        print(f"\nchange-log table starts at line {st + 1}, {len(rows)} rows, "
              f"last row is line {rows[-1] + 1}")
        print("last three rows:")
        for k in rows[-3:]:
            print(f"  {k + 1}: {lines[k][:300]}")
        print(f"line after the table: {j + 1}: {lines[j][:120]!r}")
