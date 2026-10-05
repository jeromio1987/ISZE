# -*- coding: utf-8 -*-
"""Repair ONE row in 00_docs/agent/DELEGATOR_BOARD.md.

The change-log table takes 5 cells (6 pipes). The 2026-09-24 12:50 row carries 8 cells
(9 pipes): a later fragment was appended inside the same line instead of on a new line.
This script keeps cells 1-5 exactly as they are and drops the extra fragments after
'Eucon password still to change.' Nothing else in the file is touched.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")
MARKER = "Eucon password still to change."

raw = P.read_bytes()
before = raw.decode("utf-8")
lines = before.split("\n")

target = None
for i, l in enumerate(lines):
    if l.startswith("| 2026-09-24 12:50 | cursor (scraper Phase 0) |"):
        target = i
        break
if target is None:
    raise SystemExit("target row not found")

old = lines[target]
parts = old.split("|")
print(f"old pipes: {old.count('|')}  -> parts: {len(parts)}")
if len(parts) < 7:
    raise SystemExit("row already repaired")
if MARKER not in parts[5]:
    raise SystemExit(f"cell 5 does not end where expected: {parts[5][-80:]!r}")

new = "|".join(parts[:6]) + "|"
if new.count("|") != 6:
    raise SystemExit("repaired row does not have 6 pipes")

ts = datetime.now().strftime("%H%M%S")
backup = P.with_name(P.name + f".bak_pre_row_repair_20260924_{ts}")
shutil.copy2(P, backup)
lines[target] = new
P.write_bytes("\n".join(lines).encode("utf-8"))

after = P.read_text(encoding="utf-8")
print(f"backup -> {backup}")
print(f"lines before {len(before.split(chr(10)))} | after {len(after.split(chr(10)))}")
print(f"bytes  before {len(raw)} | after {len(after.encode('utf-8'))}")
print("\nrepaired row:")
print(new)
print(f"\n'{MARKER}' occurrences after: {after.count(MARKER)}")
