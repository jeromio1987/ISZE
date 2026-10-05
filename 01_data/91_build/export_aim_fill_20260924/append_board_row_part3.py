# -*- coding: utf-8 -*-
"""Append exactly ONE 5-cell row to the DELEGATOR_BOARD change-log for the 164 fill."""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BOARD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")

row = (
    "| 2026-09-24 14:15 | cursor (AIM master write-back part 3) | "
    "**PR00 IE40 — the 164 already on the master with an empty family: 162 filled, 2 left unplaced.** "
    "A fill, not an append: master stays at **165,257 rows**, 32 columns, same order, UTF-8 no BOM, "
    "CRLF. Only 8 columns changed on each of the 162 (`aim_l1/l2/l3`, `aim_l1_fixed/l2_fixed`, "
    "`has_aim` 0→1, `aim_source` and `aim_changed` → `export_pr00_20260924`); every other column on "
    "every other row is byte-identical to the backup. Method is the part-2 rule: one full AIM path "
    "with **>= 3 supporting parts on the master alone** (min 3, median 17, max 171; zero needed the "
    "workbook to reach three), figure key as a veto, and no new class name created. **The guard that "
    "had to be read carefully: the classified workbook carries two axes, and its catalogue buckets "
    "(Repair parts / Competitive parts / …) are not AIM families. Pooling them wrongly left 41 rows "
    "unplaced on my first run; separating them gave the correct 162.** Unplaced and named: "
    "`8976863171` and `8976863181` (`BAR; BACK,RR`), both ± EUR 40, because the master splits that "
    "text across two leaves — flat. **The 92 blocked rows are untouched and carry no stamp; the 44 "
    "appended in part 2 are byte-identical and still stamped.** Also repaired the broken 12:50 "
    "change-log row (9 pipes → 6); two fragments that had been appended inside that line were "
    "dropped, and only that row was changed. | "
    "`01_data/00_derived/aim_master_v2.csv` (+ backup `.bak_pre_export_fill_20260924_140856`), "
    "`01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260924.csv` and `.xlsx` (both rebuilt; "
    "pre-rebuild copy in `_backup_20260924_pair_before_fill/`), "
    "`01_data/91_build/apply_export_pr00_fill_20260924.py`, "
    "`01_data/91_build/export_aim_fill_20260924/`, "
    "`01_data/91_build/export_aim_eq_20260924/APPLY_FILL_REPORT_20260924.md`, "
    "`00_docs/agent/DELEGATOR_BOARD.md` | "
    "Jerome: (1) the 92 `Unknown` markers are still his decision; (2) the rebuilt pair prints "
    "`aim_source` = `pr00_catalog` for these rows because the builder prefers the classification "
    "overlay's source — if the new stamp must show there, the fix is in the pair builder and that is "
    "his call; (3) the board's 2026-09-18 21:05 row still has 3 cells (pre-existing, outside this "
    "brief); (4) whether to fold parts 2 and 3 into the master builder so a rebuild cannot drop "
    "them; (5) the remaining ~1,003 queue rows still wait on the EPC lookup. |"
)

print("pipe count:", row.count("|"), "-> a 5-cell row needs 6")
if row.count("|") != 6:
    print("GUARD: row is not 5 cells. STOP.", file=sys.stderr)
    raise SystemExit(3)

text = BOARD.read_text(encoding="utf-8")
if "AIM master write-back part 3" in text:
    print("row already present, not appending again")
    raise SystemExit(0)
if not text.endswith("\n"):
    text += "\n"
BOARD.write_text(text + row + "\n", encoding="utf-8", newline="")

lines = BOARD.read_text(encoding="utf-8").splitlines()
print("appended. board now", BOARD.stat().st_size, "bytes")
print("last line pipes:", lines[-1].count("|"))
print("last line starts:", lines[-1][:40])
