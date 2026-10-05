# -*- coding: utf-8 -*-
"""Carry the cab class into the classification overlay.

The dated export pair reads AIM levels from `aim_pn_classification_20260920.csv`
first and only falls back to the master, so without this the pair would keep
printing Accident & Body > Panels > Panel for the cab parts.

What moves, on the 19 part numbers that already have a row here:
    aim_l1_fixed / aim_l2_fixed / aim_l3_fixed   ->  the cab class
    workbook_l1 / l2 / l3                        ->  the cab class
    workbook_axis_kind / workbook_source / aim_source ->  the new stamp

Deliberately NOT touched:

  * catalog_l1/l2/l3. Those are the identity axis (what the part is ordered as:
    "Body parts / Other body"), not the functional family. Moving them would be a
    different decision and would move the 177-leaf catalogue baseline.
  * axis_conflict. It says the identity axis and the workbook axis disagree. They
    still do on the group level, so it stays as it is. Clearing it here would shrink
    a counter the verifier reads ("must not grow"), and quietly shrinking a watched
    number is not mine to do.

    python 01_data/91_build/apply_cab_class_overlay_20260924.py            # dry run
    python 01_data/91_build/apply_cab_class_overlay_20260924.py --apply
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
OUTDIR = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OVERLAY = D / "aim_pn_classification_20260920.csv"

STAMP = "cab_class_20260924"
L1, L2, L3 = "Accident & Body", "Complete Assembly", "Cab Assembly"

PLACED = ["7551847570", "7552044930", "7552612100", "7552625790", "7552824860",
          "7553142130", "7551847580", "7552060250", "7552349740", "7552427800",
          "7552641820", "7552650510", "7552825890", "8974877720", "8980115942",
          "8980115951", "8980425220", "8980554611", "8980554621"]

SET = {
    "aim_l1_fixed": L1, "aim_l2_fixed": L2, "aim_l3_fixed": L3,
    "workbook_l1": L1, "workbook_l2": L2, "workbook_l3": L3,
    "workbook_axis_kind": "system",
    "workbook_source": STAMP,
    "aim_source": STAMP,
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    apply = "--apply" in sys.argv
    ts = datetime.now().strftime("%H%M%S")

    before_bytes = OVERLAY.read_bytes()
    before_sha = hashlib.sha256(before_bytes).hexdigest()
    with OVERLAY.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    idx = {c: i for i, c in enumerate(header)}
    print(f"overlay before: {len(data)} rows x {len(header)} cols, "
          f"{len(before_bytes):,} bytes, sha256 {before_sha}")

    by_pn = {r[0]: r for r in data}
    missing = [p for p in PLACED if p not in by_pn]
    if missing:
        print(f"GUARD: {len(missing)} part numbers have no overlay row: {missing}. "
              f"STOP.", file=sys.stderr)
        return 3

    merged = [list(r) for r in data]
    pos = {r[0]: i for i, r in enumerate(merged)}
    for pn in PLACED:
        r = merged[pos[pn]]
        for col, val in SET.items():
            r[idx[col]] = val

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(header)
    w.writerows(merged)
    tmp = OVERLAY.with_suffix(".csv.cabtmp")
    tmp.write_bytes(buf.getvalue().encode("utf-8"))

    with tmp.open(encoding="utf-8", newline="") as fh:
        got = list(csv.reader(fh))
    got_hdr, got_data = got[0], got[1:]
    after_by_pn = {r[0]: r for r in got_data}

    unexpected: list[str] = []
    changed: set[str] = set()
    cells = 0
    for pn, old in by_pn.items():
        new = after_by_pn.get(pn)
        if new is None:
            unexpected.append(f"{pn}: disappeared")
            continue
        for i, (a, b) in enumerate(zip(old, new)):
            if a == b:
                continue
            changed.add(pn)
            if pn in set(PLACED) and header[i] in SET:
                cells += 1
            else:
                unexpected.append(f"{pn}:{header[i]}: {a!r}->{b!r}")

    checks = {
        "header_identical": got_hdr == header,
        "row_count_unchanged": len(got_data) == len(data),
        "changed_rows_are_exactly_the_19": changed == set(PLACED),
        "no_unexpected_cell_changed": not unexpected,
        "every_placed_row_reads_the_class": all(
            (after_by_pn[p][idx["aim_l1_fixed"]], after_by_pn[p][idx["aim_l2_fixed"]],
             after_by_pn[p][idx["aim_l3_fixed"]]) == (L1, L2, L3) for p in PLACED),
        "catalogue_axis_untouched": all(
            after_by_pn[p][idx["catalog_l1"]] == by_pn[p][idx["catalog_l1"]]
            and after_by_pn[p][idx["catalog_l2"]] == by_pn[p][idx["catalog_l2"]]
            and after_by_pn[p][idx["catalog_l3"]] == by_pn[p][idx["catalog_l3"]]
            for p in PLACED),
        "no_duplicate_part_numbers": len(after_by_pn) == len(got_data),
        "no_bom": not tmp.read_bytes().startswith(b"\xef\xbb\xbf"),
    }
    print("\nGATE:")
    for k, v in checks.items():
        print(f"   {k:<44} {'PASS' if v else 'FAIL'}")
    print(f"   intended cells changed: {cells} ({len(PLACED)} rows x {len(SET)} columns)")
    if unexpected:
        print("unexpected (first 10):", unexpected[:10], file=sys.stderr)

    if not all(checks.values()):
        tmp.unlink(missing_ok=True)
        print("GATE FAILED - overlay NOT replaced.", file=sys.stderr)
        return 4

    if not apply:
        tmp.unlink(missing_ok=True)
        print("\nDRY RUN - gate passed, nothing written. Re-run with --apply.")
        return 0

    backup = D / f"aim_pn_classification_20260920.csv.bak_pre_cab_class_20260924_{ts}"
    shutil.copy2(OVERLAY, backup)
    if sha(backup) != before_sha:
        tmp.unlink(missing_ok=True)
        print("GUARD: backup hash differs. STOP.", file=sys.stderr)
        return 5
    tmp.replace(OVERLAY)
    after_sha = sha(OVERLAY)

    (OUTDIR / "cab_class_overlay_summary.json").write_text(json.dumps({
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "stamp": STAMP,
        "overlay": str(OVERLAY),
        "backup": str(backup),
        "rows": len(got_data),
        "cells_changed": cells,
        "sha256_before": before_sha,
        "sha256_after": after_sha,
        "checks": checks,
    }, indent=2), encoding="utf-8")

    print(f"\nbackup -> {backup}")
    print(f"overlay after: {len(got_data)} rows, sha256 {after_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
