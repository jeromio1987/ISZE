# -*- coding: utf-8 -*-
"""Append exactly one row to the change-log table in DELEGATOR_BOARD.md.

UTF-8 byte-level edit: decode -> insert one line -> encode back to UTF-8.
No PowerShell, no Set-Content, no WriteAllText. Every other character is preserved.
"""
import os
import shutil
import hashlib
import sys

P = r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md"
BAK = P + ".bak_pre_def_pump_row_20260924_183500"

EXPECT_EMDASH = 45
EXPECT_EURO = 24

ROW = (
    "| 2026-09-24 18:35 | cursor (AIM DEF Pump leaf) | "
    "**7552710010 (PUMP KIT, IE40) moved one leaf inside its own family. One row, one cell; "
    "a shelf change only, no family and no money moved.** It sat on Intake Exhaust Emission / "
    "DEF System / DEF Tank and now sits on the DEF Pump leaf of the same family. The leaf spelling "
    "was read off the master, not assumed: under Intake Exhaust Emission plus DEF System the master "
    "holds three leaves and only one pump leaf, DEF Pump, carrying five parts that read PUMP ASM; "
    "DEF,DCM SPLY. aim_source deliberately not restamped, because the family-level decision did not "
    "change and restamping would have lost where the classification came from. Master measured at "
    "28,611,807 bytes and mtime 17:01:53 before the write, so it had not moved since the 19-page "
    "dashboard rebuild; the write was staged in a temporary file and replaced onto the live path. "
    "Verification: master row count 165,289 before and after; a full cell-by-cell compare against "
    "the backup found exactly one differing cell across all 165,290 rows and 32 columns, the aim_l3 "
    "of that one row; the rebuilt csv and xlsx both print DEF Pump for it; the 2026-09-21 pair "
    "hashes unchanged. | "
    "`01_data/00_derived/aim_master_v2.csv` (+ backup `.bak_pre_def_pump_leaf_20260924_182731`), "
    "`01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260924.csv` and `.xlsx` (rebuilt), "
    "`01_data/00_derived/_backup_20260924_pair_before_def_pump/`, "
    "`01_data/91_build/export_aim_eq_20260924/DEF_PUMP_LEAF_REPORT_20260924.md`, "
    "`00_docs/agent/DELEGATOR_BOARD.md` | "
    "None. Same open point the 17:35 orphan append raised: the master builder does not read the "
    "master as an input, so a full spine rebuild would drop this move. |"
)

assert "\u2014" not in ROW, "no em dash in the new row"
assert "\u20ac" not in ROW, "no euro sign in the new row"
assert ROW.count("|") == 6, "new row must have 6 pipes = 5 cells"
assert "\n" not in ROW


def counts(t):
    return t.count("\u2014"), t.count("\u20ac"), t.count("\uFFFD")


raw = open(P, "rb").read()
before = raw.decode("utf-8")
em0, eu0, ff0 = counts(before)
print("BEFORE emdash/euro/fffd:", em0, eu0, ff0)
if (em0, eu0, ff0) != (EXPECT_EMDASH, EXPECT_EURO, 0):
    print("BASELINE MISMATCH - stopping, nothing written")
    sys.exit(1)

shutil.copy2(P, BAK)
print("backup:", BAK, os.path.getsize(BAK),
      hashlib.sha256(open(BAK, "rb").read()).hexdigest())

# Plain text append: file already ends in a single newline.
assert before.endswith("\n") and not before.endswith("\n\n")
after = before + ROW + "\n"

tmp = P + ".tmp_def_pump_row"
with open(tmp, "wb") as f:
    f.write(after.encode("utf-8"))
os.replace(tmp, P)
print("written via os.replace")

chk = open(P, "rb").read().decode("utf-8")
em1, eu1, ff1 = counts(chk)
print("AFTER emdash/euro/fffd:", em1, eu1, ff1)

lines = chk.split("\n")
hdr = "| Time | Agent | What changed | Files touched | Next step |"
bad = []
for i, l in enumerate(lines):
    if l.startswith("|") and l.count("|") - 1 != 5:
        bad.append((i, l.count("|") - 1, l[:60]))
print("rows not having 5 cells:", len(bad))
for b in bad:
    print("   line", b[0], "cells", b[1], b[2])
print("new row present once at end:", lines[-2] == ROW)
print("line count:", len(lines))
print("OK" if (em1 == EXPECT_EMDASH and eu1 == EXPECT_EURO and ff1 == 0
               and not bad and lines[-2] == ROW) else "CHECK FAILED")
