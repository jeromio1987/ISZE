# -*- coding: utf-8 -*-
"""Append one change-log row to DELEGATOR_BOARD.md, in bytes, never via PowerShell.

The file was damaged earlier today by a PowerShell [IO.File]::WriteAllText that read it
as the local code page. So this script:
  * reads the whole file as bytes and decodes it as UTF-8,
  * asserts it already holds zero replacement characters,
  * appends one line as bytes (the old content must stay a byte prefix of the new file),
  * proves afterwards that nothing was replaced, only added.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BOARD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")
REPL = "\ufffd"
EMDASH = "\u2014"
EURO = "\u20ac"

ROW = (
    "| 2026-09-24 19:20 | cursor (cab class) | "
    "**The cab assembly now has its own class: Accident & Body > Complete Assembly > "
    "Cab Assembly. 20 parts placed, 1 row added, and 264 cab-related rows deliberately "
    "left where they are.** One new name, \"Cab Assembly\"; the family \"Accident & Body\" "
    "and the group \"Complete Assembly\" were already on the master, and the shape copies "
    "the master's only other complete assembly, Engine > Complete Assembly > "
    "Engine Assembly (45 rows). The family is Accident & Body because the cab is the "
    "truck's body, the master's own top-level Accident & Body group excludes "
    "Accident & Body > Panels > Door, the cab already sat on Accident & Body > Panels > "
    "Panel, and the master's own figure key 604-002 is labelled \"other body\" "
    "(Accident parts / Body parts / Other body). Scope is the cab as a unit, not every "
    "part with cab in its text: I placed the 13 CAB ASM assemblies (6 wrongly on "
    "Panels > Panel, 7 on Unknown) and the 6 cab rear-panel and side-sill parts whose "
    "identical description another master row already uses, and I added 7553266960 "
    "CAB ASM; SERVICE,W/ELECT (7,603.44 euro list price, no master row at all). "
    "Deliberately NOT moved: 93 cab mounting brackets and rubbers on Chassis Frame and "
    "Suspension, 23 cab harness connectors on Electrical, 9 cab locks and hinges, 8 "
    "silencer mats, 5 emblems, 56 harnesses, 10 decals, 5 latches, 4 fenders and the "
    "rest of the 283 rows that merely mention a cab part. Those sit sensibly where they "
    "are, and several were put there on purpose today by the 177 wording rules that name "
    "cab mounting. One other cab assembly was left on Intake Exhaust Emission > DEF "
    "System, and no cab part sits on Cabin Interior, which holds the seats, dashboard "
    "and trim. This is bigger than it looks: it moves part of one of the 23 top-level "
    "families, and every pack that groups by family reads it. Two files written, each "
    "backed up first and each staged in a temporary file then replaced onto the live "
    "path: the master 165,289 to 165,290 rows, 116 cells on 19 rows, and the "
    "classification overlay, 135 cells on the same 19 rows, because the export pair "
    "reads its levels from the overlay first. The pair named 2026-09-24 was rebuilt and "
    "now prints the new class on all 20 parts; the 2026-09-21 pair is byte-identical. "
    "Open count on the IE40 price list 79 to 78. A full cell-by-cell compare against the "
    "backup found exactly the intended cells and nothing else, 16 of 16 checks passed. "
    "`Accident & Body` goes 4,380 to 4,388 rows and the `Unknown` marker 3,603 to 3,596. | "
    "`01_data/00_derived/aim_master_v2.csv` (+ backup "
    "`.bak_pre_cab_class_20260924_191700`), `aim_pn_classification_20260920.csv` "
    "(+ backup `.bak_pre_cab_class_20260924_192113`), "
    "`AIM_Master_PN_Categories_Figkey_20260924.csv` and `.xlsx` (rebuilt), "
    "`_backup_20260924_pair_before_cab_class/`, "
    "`01_data/91_build/apply_cab_class_20260924.py`, "
    "`apply_cab_class_overlay_20260924.py`, "
    "`export_aim_eq_20260924/CAB_CLASS_REPORT_20260924.md` | "
    "Three things are not mine to decide. (1) A taxonomy class reaches every dashboard "
    "that groups by family and the Power BI file; they were all rebuilt today, so they "
    "need a deliberate refresh before they show this. (2) The AIM classification "
    "verifier now reports the approved 177-leaf catalogue baseline against a 176-leaf "
    "file, so it exits 1 on a drift check unrelated to this change; that baseline was "
    "left alone on purpose. (3) Whether to fold this into the master builder so a full "
    "spine rebuild cannot drop it, the same open point the appends raised. |"
)


def counts(text: str) -> tuple[int, int, int]:
    return text.count(REPL), text.count(EMDASH), text.count(EURO)


def main() -> int:
    before_bytes = BOARD.read_bytes()
    before = before_bytes.decode("utf-8")
    b_rep, b_dash, b_euro = counts(before)
    print(f"before : {len(before_bytes):,} bytes, sha256 "
          f"{hashlib.sha256(before_bytes).hexdigest()[:24]}")
    print(f"before : replacement={b_rep}  em-dash={b_dash}  euro={b_euro}")

    if b_rep != 0:
        print("GUARD: the file already holds replacement characters. STOP.", file=sys.stderr)
        return 3
    if b"\xef\xbf\xbd" in before_bytes:
        print("GUARD: replacement bytes present. STOP.", file=sys.stderr)
        return 3
    if not before.endswith("\n"):
        print("GUARD: file does not end with a newline. STOP.", file=sys.stderr)
        return 3
    if ROW.count("|") != 6:
        print(f"GUARD: my row has {ROW.count('|')} pipes, expected 6 "
              f"(5 cells). STOP.", file=sys.stderr)
        return 3
    if ROW.count("\n") != 0:
        print("GUARD: my row contains a newline. STOP.", file=sys.stderr)
        return 3

    after_bytes = before_bytes + ROW.encode("utf-8") + b"\n"
    after = after_bytes.decode("utf-8")
    a_rep, a_dash, a_euro = counts(after)

    # every table row must keep 5 cells, ignoring the file's small 2-cell sub-tables
    def bad_rows(text: str) -> list[int]:
        bad = []
        for i, line in enumerate(text.split("\n"), 1):
            s = line.strip()
            if not (s.startswith("|") and s.endswith("|")):
                continue
            n = len(s.split("|")) - 2
            if n not in (2, 5):
                bad.append(i)
        return bad

    checks = {
        "before_is_a_byte_prefix_of_after": after_bytes.startswith(before_bytes),
        "length_grew_by_exactly_my_row": len(after_bytes) - len(before_bytes)
            == len(ROW.encode("utf-8")) + 1,
        "zero_replacement_chars_after": a_rep == 0,
        "no_replacement_bytes_after": b"\xef\xbf\xbd" not in after_bytes,
        "em_dash_count_unchanged": a_dash == b_dash,
        "euro_count_unchanged": a_euro == b_euro,
        "no_table_row_has_a_wrong_cell_count": not bad_rows(after),
        "my_row_present_exactly_once": after.count(ROW) == 1,
        "line_count_grew_by_one": after.count("\n") == before.count("\n") + 1,
    }
    print("\nGATE:")
    for k, v in checks.items():
        print(f"   {k:<46} {'PASS' if v else 'FAIL'}")
    print(f"   my row: {ROW.count('|')} pipes = 5 cells, "
          f"{len(ROW)} characters")
    bad = bad_rows(after)
    if bad:
        print("rows with a wrong cell count:", bad[:10], file=sys.stderr)

    if not all(checks.values()):
        print("GATE FAILED - board NOT changed.", file=sys.stderr)
        return 4

    if "--apply" not in sys.argv:
        print("\nDRY RUN - gate passed, nothing written. Re-run with --apply.")
        return 0

    BOARD.write_bytes(after_bytes)
    final = BOARD.read_bytes()
    f_rep, f_dash, f_euro = counts(final.decode("utf-8"))
    print(f"\nafter  : {len(final):,} bytes, sha256 "
          f"{hashlib.sha256(final).hexdigest()[:24]}")
    print(f"after  : replacement={f_rep}  em-dash={f_dash}  euro={f_euro}")
    print(f"board  : {BOARD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
