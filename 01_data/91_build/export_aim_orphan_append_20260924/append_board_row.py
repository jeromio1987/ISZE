# -*- coding: utf-8 -*-
"""Append exactly ONE 5-cell row to the change-log table at the end of DELEGATOR_BOARD.md.

The board file is not valid UTF-8 (it carries stray 0x9d bytes from an earlier writer), so it is
read and appended as bytes and nothing already in it is decoded, re-encoded or reformatted. LF line
endings, matching the file.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BOARD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")

row = (
    "| 2026-09-24 17:35 | cursor (AIM orphan append) | "
    "**PR00 IE40 - the 43 part numbers still with no row on the AIM master now appended. "
    "32 of 43 placed, 11 left unplaced and named.** All 32 were settled by the EPC figure name read "
    "through the authored 177 wording rules, and for all 32 my own reading of the rules gives the "
    "same answer the earlier run recorded, so the stamp is `export_aim_eq_20260924`. Description "
    "agreement with the figure key as a veto was run in full and placed none, because the figure "
    "name is the stronger source and wins wherever both were available. The 11 unplaced are five "
    "parts the EPC does not hold, three whose wording has never appeared on the master, and three "
    "connectors whose figure key is shared - none guessed. Master 165,257 to **165,289 rows**, "
    "32 columns in the original order, no BOM, CRLF only in the master, and all 165,257 pre-existing "
    "rows byte-identical to the backup by part number, not by row position. The write was staged in "
    "a temporary file and replaced onto the live path, never written onto it directly. The 25 marker "
    "rows and the 31 wording rows on this price list are untouched, proved part number by part "
    "number. Open on the price list falls from 111 to 79 on the master reading, or 99 to 67 the way "
    "the brief counts it. No sanctioned append path exists - the master builder does not read the "
    "master as an input, so a future spine rebuild will drop these 32 rows and the 44 before them. | "
    "`01_data/00_derived/aim_master_v2.csv` (+ backup `.bak_pre_orphan_append_20260924_170151`), "
    "`01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260924.csv` and `.xlsx` (rebuilt), "
    "`01_data/00_derived/_backup_20260924_pair_before_orphans/`, "
    "`01_data/91_build/export_aim_eq_20260924/orphans_43.csv` and "
    "`ORPHAN_APPEND_REPORT_20260924.md`, `01_data/91_build/export_aim_orphan_append_20260924/` | "
    "Jerome: (1) the 11 unplaced are named in the report - three connectors would land on the "
    "harness-connector leaf at 47 supporting parts if a bare CONNECTOR rule were added; (2) whether "
    "to fold these appends into the master builder so a rebuild cannot drop them; (3) the marker "
    "rows and blank rows on this list are still your call, and the brief's 25 and 31 do not "
    "reconcile with the master - both readings are in the report. |"
)

pipes = row.count("|")
print(f"pipes: {pipes} (a 5-cell row needs 6)")
if pipes != 6:
    print("GUARD: row is not 5 cells. STOP.", file=sys.stderr)
    raise SystemExit(3)
if not row.isascii():
    print("GUARD: row carries a non-ASCII byte. STOP.", file=sys.stderr)
    raise SystemExit(3)

raw = BOARD.read_bytes()
print(f"board before: {len(raw):,} bytes, sha256 not taken (non-UTF-8)")
if b"AIM orphan append" in raw:
    print("row already present, not appending again")
    raise SystemExit(0)

lf_only = raw.count(b"\n") == raw.count(b"\r\n") + raw.count(b"\n") - raw.count(b"\r\n")
print(f"lf count {raw.count(b'\n')}, crlf count {raw.count(b'\r\n')}")

payload = (b"" if raw.endswith(b"\n") else b"\n") + row.encode("ascii") + b"\n"
BOARD.write_bytes(raw + payload)
after = BOARD.read_bytes()
print(f"board after : {len(after):,} bytes (+{len(after) - len(raw)})")
print("everything before the new row is byte-identical:", after[:len(raw)] == raw)
print("last line:", after.split(b"\n")[-2].decode("ascii")[:110])
print("last line pipes:", after.split(b"\n")[-2].count(b"|"))
print("re-read of the file succeeds as bytes; the stray 0x9d bytes were left exactly as they were")
