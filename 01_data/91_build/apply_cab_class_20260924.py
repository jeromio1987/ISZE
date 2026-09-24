# -*- coding: utf-8 -*-
"""Give the cab assembly its own class on AIM, the same shape the engine already uses.

Jerome 2026-09-24: "a cab is a truck cabine create a separate class for it".

Class created (one new leaf, two names that already exist):
    Accident & Body > Complete Assembly > Cab Assembly

Why that shape: the master's only complete assembly today is
    Engine > Complete Assembly > Engine Assembly   (45 rows)
so the master's own convention for a whole assembly is
    <family> > Complete Assembly > <X> Assembly
The family is Accident & Body because the cab is the truck's body, the master's own
top-level ACCIDENT & BODY group excludes Accident & Body > Panels > Door, the cab
already sits on Accident & Body > Panels > Panel, and the master's own figure key
604-002 is labelled "other body" (Accident parts / Body parts / Other body).

Scope: the cab as a UNIT, not every part with "cab" in its text. Placed only where
the part's own description says it is the assembly ("CAB ASM" / a cab panel), with the
identical description already used by another master row.

Safety: header must be identical, row count +N exactly, atomic os.replace, and a
cell-by-cell compare against a backup taken in the same folder.

    python 01_data/91_build/apply_cab_class_20260924.py            # dry run
    python 01_data/91_build/apply_cab_class_20260924.py --apply
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUTDIR = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
MASTER = DER / "aim_master_v2.csv"
EXPORT = ROOT / "01_data" / "EXPORT.XLSX"

STAMP = "cab_class_20260924"
L1 = "Accident & Body"
L2 = "Complete Assembly"
L3 = "Cab Assembly"

# The two columns whose whole point is to hold the governed family. Measured: for the
# engine assembly rows aim_l1/aim_l1_fixed carry the same text, so both are set to the
# whole path (l2_fixed carries the group, exactly as upstream fill/append does).
SET_COLS_EXISTING = ["aim_l1", "aim_l2", "aim_l3",
                     "aim_l1_fixed", "aim_l2_fixed",
                     "has_aim", "aim_source", "aim_changed"]

# The 19 rows that already exist. Role is the evidence, not a guess:
#   cab_asm        -> its own description reads "CAB ASM"
#   cab_panel      -> panel/structure of the cab, and the identical description already
#                     sits on the master (it just sits on a generic Panel leaf today)
PLACE_EXISTING: dict[str, str] = {
    "7551847570": "cab_asm",
    "7552044930": "cab_asm",
    "7552612100": "cab_asm",
    "7552625790": "cab_asm",
    "7552824860": "cab_asm",
    "7553142130": "cab_asm",
    "7551847580": "cab_asm",
    "7552060250": "cab_asm",
    "7552349740": "cab_asm",
    "7552427800": "cab_asm",
    "7552641820": "cab_asm",
    "7552650510": "cab_asm",
    "7552825890": "cab_asm",
    "8974877720": "cab_panel",
    "8980115942": "cab_panel",
    "8980115951": "cab_panel",
    "8980425220": "cab_panel",
    "8980554611": "cab_panel",
    "8980554621": "cab_panel",
}

# The part that started this: no row on the master at all.
ADD_PN = "7553266960"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_export_row(pn: str) -> dict[str, str]:
    import pandas as pd
    x = pd.read_excel(EXPORT, dtype=str)
    x = x[x["P/N"].astype(str).str.strip() == pn]
    if x.empty:
        raise SystemExit(f"{pn} is not in {EXPORT}")
    return {k: v for k, v in x.iloc[0].to_dict().items()}


def main() -> int:
    apply = "--apply" in sys.argv
    ts = datetime.now().strftime("%H%M%S")

    before_bytes = MASTER.read_bytes()
    before_sha = hashlib.sha256(before_bytes).hexdigest()
    with MASTER.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    idx = {c: i for i, c in enumerate(header)}
    print(f"master before: {len(data)} rows x {len(header)} cols, "
          f"{len(before_bytes):,} bytes, sha256 {before_sha}")
    if len(header) != 32:
        print("GUARD: unexpected column count. STOP.", file=sys.stderr)
        return 3

    by_pn = {r[0]: r for r in data}
    if len(by_pn) != len(data):
        print("GUARD: duplicate part numbers on the master. STOP.", file=sys.stderr)
        return 3

    # ---------------- the names must be measured, not assumed ----------------
    l1_vals = {r[idx["aim_l1"]] for r in data} | {r[idx["aim_l1_fixed"]] for r in data}
    l2_vals = {r[idx["aim_l2"]] for r in data} | {r[idx["aim_l2_fixed"]] for r in data}
    l3_vals = {r[idx["aim_l3"]] for r in data}
    print(f"  '{L1}' already on master : {L1 in l1_vals}")
    print(f"  '{L2}' already on master : {L2 in l2_vals}")
    print(f"  '{L3}' already on master : {L3 in l3_vals}   <-- the one new name")

    # ---------------- build the candidate in memory ----------------
    merged = [list(r) for r in data]
    for pn, role in PLACE_EXISTING.items():
        r = by_pn.get(pn)
        if r is None:
            print(f"GUARD: {pn} is not on the master. STOP.", file=sys.stderr)
            return 3
        if not r[idx["description"]].upper().startswith(("CAB ASM", "PANEL;")):
            print(f"GUARD: {pn} description is {r[idx['description']]!r}, "
                  f"not a cab assembly or cab panel. STOP.", file=sys.stderr)
            return 3

    existing_targets = set(PLACE_EXISTING)
    if ADD_PN in by_pn:
        print(f"GUARD: {ADD_PN} already has a master row. STOP.", file=sys.stderr)
        return 3

    # index of each row inside `merged` (merged preserves the original order, and the
    # new row is inserted by bisect so the text-sorted order holds)
    pos = {r[0]: i for i, r in enumerate(merged)}

    for pn, role in PLACE_EXISTING.items():
        r = merged[pos[pn]]
        r[idx["aim_l1"]] = L1
        r[idx["aim_l2"]] = L2
        r[idx["aim_l3"]] = L3
        r[idx["aim_l1_fixed"]] = L1
        r[idx["aim_l2_fixed"]] = L2
        r[idx["has_aim"]] = "1"
        r[idx["aim_source"]] = STAMP
        r[idx["aim_changed"]] = STAMP

    # ---------------- the added row ----------------
    e = read_export_row(ADD_PN)
    new = [""] * len(header)
    new[idx["part_number"]] = ADD_PN
    new[idx["description"]] = str(e["Description"]).strip()
    new[idx["aim_l1"]] = L1
    new[idx["aim_l2"]] = L2
    new[idx["aim_l3"]] = L3
    new[idx["aim_demand_type"]] = ""      # measured: every appended row carries blank
    new[idx["aim_core_noncore"]] = ""     # measured: every appended row carries blank
    new[idx["cat_l1"]] = ""               # the row is new, no catalogue node behind it
    new[idx["cat_l2"]] = ""
    new[idx["cat_l3"]] = ""
    new[idx["cat_pms_flag"]] = "0"
    fig_no, _, key_no = str(e["Fig No."]).strip().partition(".")
    fig_no = str(e["Fig No."]).strip()
    key_no = str(e["Key No."]).strip()
    fig_no_padded = fig_no.zfill(3) if fig_no.isdigit() else fig_no
    # master convention, measured on the 44 appended earlier: fig_key is built only
    # where the key number is numeric, otherwise it stays blank.
    new[idx["fig_key"]] = f"{fig_no_padded}-{key_no}" if key_no.isdigit() else ""
    new[idx["fig_no"]] = fig_no_padded
    new[idx["key_no"]] = key_no
    new[idx["price_class_iml"]] = ""      # not in the per-distributor pricing basis
    new[idx["aim_source"]] = STAMP
    new[idx["has_aim"]] = "1"
    new[idx["has_catalogue_node"]] = "0"  # no catalogue node exists for it
    new[idx["desc_ambiguous"]] = "0"
    new[idx["l12m_billed_eur"]] = "0.0"   # measured: the spine carries 0.0 for every
    new[idx["eur"]] = "0.0"               # row that has no catalogue node
    new[idx["aim_l1_fixed"]] = L1
    new[idx["aim_l2_fixed"]] = L2
    new[idx["aim_changed"]] = STAMP

    lo, hi = 0, len(merged)
    while lo < hi:
        mid = (lo + hi) // 2
        if merged[mid][0] < ADD_PN:
            lo = mid + 1
        else:
            hi = mid
    merged.insert(lo, new)
    print(f"  added row {ADD_PN} at index {lo}, between "
          f"{merged[lo - 1][0]} and {merged[lo + 1][0]}")

    # ---------------- write the candidate ----------------
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(header)
    w.writerows(merged)
    tmp = MASTER.with_suffix(".csv.cabtmp")
    tmp.write_bytes(buf.getvalue().encode("utf-8"))

    # ---------------- gate: cell by cell against the rows we hold ----------------
    with tmp.open(encoding="utf-8", newline="") as fh:
        got = list(csv.reader(fh))
    got_hdr, got_data = got[0], got[1:]
    after_by_pn = {r[0]: r for r in got_data}

    unexpected: list[tuple[str, int, str]] = []
    intended = 0
    for pn, old in by_pn.items():
        newr = after_by_pn.get(pn)
        if newr is None:
            unexpected.append((pn, -1, "row disappeared"))
            continue
        for i, (a, b) in enumerate(zip(old, newr)):
            if a == b:
                continue
            if pn in existing_targets and header[i] in SET_COLS_EXISTING:
                intended += 1
                continue
            unexpected.append((pn, i, header[i]))

    newr = after_by_pn.get(ADD_PN, [])
    new_ok = (
        bool(newr)
        and newr[idx["aim_l1"]] == L1
        and newr[idx["aim_l2"]] == L2
        and newr[idx["aim_l3"]] == L3
        and newr[idx["aim_source"]] == STAMP
        and newr[idx["has_aim"]] == "1"
    )

    checks = {
        "header_identical": got_hdr == header,
        "row_count_exactly_plus_1": len(got_data) == len(data) + 1,
        "no_unexpected_cell_changed": not unexpected,
        "every_placed_row_reads_the_new_class": all(
            (after_by_pn[p][idx["aim_l1"]], after_by_pn[p][idx["aim_l2"]],
             after_by_pn[p][idx["aim_l3"]]) == (L1, L2, L3) for p in existing_targets),
        "every_placed_row_stamped": all(
            after_by_pn[p][idx["aim_source"]] == STAMP for p in existing_targets),
        "added_row_present_and_classed": new_ok,
        "no_duplicate_part_numbers": len(after_by_pn) == len(got_data),
        "still_sorted": [r[0] for r in got_data] == sorted(r[0] for r in got_data),
        "no_bom": not tmp.read_bytes().startswith(b"\xef\xbb\xbf"),
    }
    print("\nGATE:")
    for k, v in checks.items():
        print(f"   {k:<42} {'PASS' if v else 'FAIL'}")
    print(f"   intended cells changed: {intended} "
          f"({len(existing_targets)} rows x {len(SET_COLS_EXISTING)} columns)")
    if unexpected:
        print("unexpected changes (first 20):", unexpected[:20], file=sys.stderr)

    if not all(checks.values()):
        tmp.unlink(missing_ok=True)
        print("GATE FAILED - master NOT replaced.", file=sys.stderr)
        return 4

    if not apply:
        tmp.unlink(missing_ok=True)
        print("\nDRY RUN - gate passed, nothing written. Re-run with --apply.")
        return 0

    # ---------------- backup, then atomic replace ----------------
    backup = DER / f"aim_master_v2.csv.bak_pre_cab_class_20260924_{ts}"
    shutil.copy2(MASTER, backup)
    if sha256_of(backup) != before_sha:
        tmp.unlink(missing_ok=True)
        print("GUARD: backup hash differs from the original. STOP.", file=sys.stderr)
        return 5
    tmp.replace(MASTER)          # os.replace, same folder
    after_sha = sha256_of(MASTER)

    summary = {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "stamp": STAMP,
        "class_created": [L1, L2, L3],
        "rows_placed_existing": sorted(existing_targets),
        "rows_added": [ADD_PN],
        "master": str(MASTER),
        "backup": str(backup),
        "rows_before": len(data),
        "rows_after": len(got_data),
        "sha256_before": before_sha,
        "sha256_after": after_sha,
        "bytes_before": len(before_bytes),
        "bytes_after": MASTER.stat().st_size,
        "cells_changed": intended,
        "checks": checks,
    }
    (OUTDIR / "cab_class_apply_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nbackup -> {backup}")
    print(f"master after: {len(got_data)} rows, {summary['bytes_after']:,} bytes")
    print(f"master after sha256: {after_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
