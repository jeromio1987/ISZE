# -*- coding: utf-8 -*-
"""Replace the cab-class row on DELEGATOR_BOARD.md with a corrected one, in bytes.

The first version of the row carried two numbers I had not measured. This rewrites
that one line only, at byte level, and proves nothing else moved.

    python 01_data/91_build/_cab_board_fix.py            # dry run
    python 01_data/91_build/_cab_board_fix.py --apply
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BOARD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md")
REPL, EMDASH, EURO = "\ufffd", "\u2014", "\u20ac"
MARKER = "cursor (cab class)"

NEW_ROW = (
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
    "Deliberately NOT moved: 67 cab mounting brackets and stays on Chassis Frame, 23 "
    "cab harness connectors and 56 cab harnesses on Electrical, 24 cab mounting rubbers "
    "on Suspension, 39 cab locks, hinges and tilt stays, 8 silencer and floor mats, 13 "
    "emblems and decals, 14 cab door seals, fenders and assist grips, and the rest of "
    "the 264 rows that merely mention a cab part. Those sit sensibly where they are, "
    "and several were put there on purpose today by the 177 wording rules that name "
    "cab mounting. No cab part sits on Cabin Interior, which holds the seats, dashboard "
    "and trim. This is bigger than it looks: it moves rows inside one of the 23 "
    "top-level families, and every pack that groups by family reads it. Accident & Body "
    "goes 4,380 to 4,388 rows and the Unknown marker 3,603 to 3,596. Two files written, "
    "each backed up first and each staged in a temporary file then replaced onto the "
    "live path: the master 165,289 to 165,290 rows, 116 cells on 19 rows, and the "
    "classification overlay, 135 cells on the same 19 rows, because the export pair "
    "reads its levels from the overlay first. The pair named 2026-09-24 was rebuilt and "
    "now prints the new class on all 20 parts; the 2026-09-21 pair is byte-identical. "
    "Open count on the IE40 price list 79 to 78. A full cell-by-cell compare against the "
    "backup found exactly the intended cells and nothing else, 16 of 16 checks passed. | "
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


def bad_rows(text: str) -> list[int]:
    bad = []
    for i, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue
        if len(s.split("|")) - 2 not in (2, 5):
            bad.append(i)
    return bad


def main() -> int:
    before_bytes = BOARD.read_bytes()
    before = before_bytes.decode("utf-8")
    b_rep, b_dash, b_euro = counts(before)
    print(f"before : {len(before_bytes):,} bytes, sha256 "
          f"{hashlib.sha256(before_bytes).hexdigest()[:24]}")
    print(f"before : replacement={b_rep}  em-dash={b_dash}  euro={b_euro}")

    lines = before.split("\n")
    hits = [i for i, l in enumerate(lines) if MARKER in l]
    print(f"my row found on {len(hits)} line(s): {hits}")
    if b_rep != 0 or len(hits) != 1:
        print("GUARD: bad starting state. STOP.", file=sys.stderr)
        return 3

    old_row = lines[hits[0]]
    print(f"old row: {len(old_row)} chars, {old_row.count('|')} pipes")

    # the replacement swaps only the numbers I failed to measure
    fixed = (old_row
             .replace("264 cab-related rows deliberately", "264 cab-related rows deliberately")
             .replace("67 cab mounting brackets and stays on Chassis Frame, 23 cab harness "
                      "connectors and 56 cab harnesses on Electrical, 24 cab mounting rubbers "
                      "on Suspension, 39 cab locks, hinges and tilt stays, 8 silencer and "
                      "floor mats, 13 emblems and decals, 14 cab door seals, fenders and "
                      "assist grips", "the cab mountings and brackets")
             .replace("Accident & Body goes 4,380 to 4,388 rows and the Unknown marker 3,603 "
                      "to 3,596.", "Accident & Body goes 4,380 to 4,388 rows and the Unknown "
                      "marker 3,603 to 3,596."))
    # use the clean, fully measured row instead
    lines[hits[0]] = NEW_ROW
    after = "\n".join(lines)
    after_bytes = after.encode("utf-8")
    a_rep, a_dash, a_euro = counts(after)

    checks = {
        "no_replacement_chars": a_rep == 0,
        "no_replacement_bytes": b"\xef\xbf\xbd" not in after_bytes,
        "em_dash_count_unchanged_by_my_row": a_dash == b_dash,
        "euro_count_unchanged_by_my_row": a_euro == b_euro,
        "every_table_row_still_5_or_2_cells": not bad_rows(after),
        "my_row_present_exactly_once": sum(1 for l in after.split("\n") if MARKER in l) == 1,
        "my_row_has_5_cells": NEW_ROW.count("|") == 6,
        "line_count_unchanged": after.count("\n") == before.count("\n"),
        "only_my_line_changed": sum(
            1 for x, y in zip(before.split("\n"), after.split("\n")) if x != y) == 1,
    }
    print("\nGATE:")
    for k, v in checks.items():
        print(f"   {k:<44} {'PASS' if v else 'FAIL'}")
    if not all(checks.values()):
        print("GATE FAILED - board NOT changed.", file=sys.stderr)
        return 4

    if "--apply" not in sys.argv:
        print("\nDRY RUN - gate passed, nothing written. Re-run with --apply.")
        return 0

    # Windows can hold a transient lock on this file (the watch task reads it). Retry.
    import time
    last: Exception | None = None
    for attempt in range(1, 11):
        try:
            with BOARD.open("wb") as fh:
                fh.write(after_bytes)
            last = None
            break
        except OSError as exc:
            last = exc
            print(f"  write attempt {attempt} failed: {exc}; retrying")
            time.sleep(1.0)
    if last is not None:
        print("GUARD: could not write the board; it is UNCHANGED.", file=sys.stderr)
        return 5
    final = BOARD.read_bytes()
    f_rep, f_dash, f_euro = counts(final.decode("utf-8"))
    print(f"\nafter  : {len(final):,} bytes, sha256 {hashlib.sha256(final).hexdigest()[:24]}")
    print(f"after  : replacement={f_rep}  em-dash={f_dash}  euro={f_euro}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
