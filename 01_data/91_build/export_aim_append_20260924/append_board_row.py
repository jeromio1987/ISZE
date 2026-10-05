# -*- coding: utf-8 -*-
"""Append exactly ONE 5-cell row to the change-log table at the end of DELEGATOR_BOARD.md."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BOARD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")

row = (
    "| 2026-09-24 14:05 | cursor (AIM master write-back part 2) | "
    "**PR00 IE40 — the 44 not-on-master part numbers appended. 44 of 44 placed, 0 left unplaced.** "
    "All 44 resolved by exact-description agreement (one full AIM path, minimum 6 supporting parts; "
    "0 needed the classified workbook to reach three). The figure key was used only as a veto and "
    "fired zero times. **The engine assembly `8981422000` now sits on `Engine > Complete Assembly > "
    "Engine Assembly`** — the leaf the master's own 27 ENGINE ASM rows already use; I reused that "
    "spelling and created no new class. Master 165,213 to **165,257 rows**, 32 columns in the "
    "original order, encoding and line endings unchanged; all 165,213 pre-existing rows "
    "byte-identical to the backup by part number; every new row stamped `aim_source = "
    "export_pr00_20260924`. **The 92 blocked by `aim_l1_fixed` = Unknown are untouched, verified row "
    "by row; none carries the stamp.** No sanctioned append path exists — the builder "
    "`build_aim_master.py` does not read the master as an input, so a future spine rebuild would "
    "drop these rows. | "
    "`01_data/00_derived/aim_master_v2.csv` (+ backup "
    "`.bak_pre_export_append_20260924_135923`), "
    "`01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260924.csv` and `.xlsx`, "
    "`01_data/91_build/apply_export_pr00_append_20260924.py`, "
    "`01_data/91_build/export_aim_append_20260924/`, "
    "`01_data/91_build/export_aim_eq_20260924/APPLY_APPEND_REPORT_20260924.md` | "
    "Jerome: (1) the 92 `Unknown` markers are still his decision; (2) whether to fold this append "
    "into the master builder so a future rebuild cannot drop it; (3) the remaining ~1,003 queue "
    "rows still wait on the EPC lookup. |"
)

cells = [c for c in row.split("|")]
print(f"cells (including the empty edges): {len(cells)}")
print("pipe count:", row.count("|"), "-> 5-cell row needs 6")
if row.count("|") != 6:
    print("GUARD: row is not 5 cells. STOP.", file=sys.stderr)
    raise SystemExit(3)

text = BOARD.read_text(encoding="utf-8")
if "export_pr00_20260924" in text and "AIM master write-back part 2" in text:
    print("row already present, not appending again")
    raise SystemExit(0)
if not text.endswith("\n"):
    text += "\n"
BOARD.write_text(text + row + "\n", encoding="utf-8", newline="")
print("appended. board now", BOARD.stat().st_size, "bytes")

# re-read and confirm
lines = BOARD.read_text(encoding="utf-8").splitlines()
print("last line:", lines[-1][:140])
print("last line pipes:", lines[-1].count("|"))
