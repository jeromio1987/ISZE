# -*- coding: utf-8 -*-
"""Fill the AIM levels for the PR00 IE40 part numbers that are already on aim_master_v2.csv
with an empty family (the 164 in would_land_free.txt).

Jerome 2026-09-24, authorised. Scope:
  * ONLY the part numbers in
    01_data/91_build/_tmp_apply_export_pr00_20260924/would_land_free.txt
  * ONLY rows whose current aim_l1 is empty, 'Unknown' or 'Unknown Review'
  * the 92 in carried_out_blocked_precedence.txt are NOT touched
  * the 44 appended earlier (stamp export_pr00_20260924, aim_clear = ...) are NOT touched

This is a FILL, not an append: the row count must not change.
Path for each row comes from decision_164_final.csv (derive_paths_164.py): the exact
description's own AIM path where the MASTER alone agrees on one full path with >= 3
supporting parts, with the workbook's AIM axis as a cross-check and the figure key as a
veto only.

Safety
  * backup written first, hash re-checked before the replace
  * atomic replace (write .tmp, verify, then move)
  * gate: header identical, row count identical, every row I did not target byte-identical,
    each targeted row changed ONLY in the AIM columns, the 92 and the 44 untouched
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
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"
F = ROOT / "01_data" / "91_build" / "export_aim_fill_20260924"
MASTER = D / "aim_master_v2.csv"
DECISION = F / "decision_164_final.csv"
BLOCKED = A / "carried_out_blocked_precedence.txt"
FREE = A / "would_land_free.txt"
NOTIN = A / "carried_out_not_in_master.txt"
STAMP = "export_pr00_20260924"

# the only columns this fill is allowed to change
TOUCHABLE = ["aim_l1", "aim_l2", "aim_l3", "aim_l1_fixed", "aim_l2_fixed",
             "has_aim", "aim_source", "aim_changed"]
PLACEHOLDER = {"", "Unknown", "Unknown Review"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(s: str) -> str:
    return (s or "").strip()


def main() -> int:
    ts = datetime.now().strftime("%H%M%S")
    backup = D / f"aim_master_v2.csv.bak_pre_export_fill_20260924_{ts}"

    # ---------------- the decisions ----------------
    with DECISION.open(encoding="utf-8-sig", newline="") as fh:
        decisions = list(csv.DictReader(fh))
    placed = [d for d in decisions if norm(d["chosen_l1"])]
    unplaced = [d for d in decisions if not norm(d["chosen_l1"])]
    placed_pns = {d["pn"] for d in placed}
    print(f"decisions: {len(decisions)} | placed {len(placed)} | unplaced {len(unplaced)}")

    blocked = {l.strip() for l in BLOCKED.read_text().splitlines() if l.strip()}
    free = {l.strip() for l in FREE.read_text().splitlines() if l.strip()}
    notin = {l.strip() for l in NOTIN.read_text().splitlines() if l.strip()}
    print(f"lists: blocked {len(blocked)} | free {len(free)} | not_in_master {len(notin)}")

    if placed_pns - free:
        print("GUARD: a decision is outside would_land_free.txt. STOP.", file=sys.stderr)
        return 3
    if placed_pns & blocked:
        print("GUARD: my set overlaps the blocked 92. STOP.", file=sys.stderr)
        return 3
    if placed_pns & notin:
        print("GUARD: my set overlaps the 44 appended earlier. STOP.", file=sys.stderr)
        return 3

    # ---------------- the master ----------------
    before_sha = sha256_of(MASTER)
    before_bytes = MASTER.stat().st_size
    with MASTER.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    idx = {c: i for i, c in enumerate(header)}
    print(f"master before: {len(data)} rows, {len(header)} cols, {before_bytes:,} bytes")
    print(f"master before sha256: {before_sha}")

    for c in TOUCHABLE:
        if c not in idx:
            print(f"GUARD: missing column {c}. STOP.", file=sys.stderr)
            return 3

    by_pn = {r[0]: r for r in data}
    missing = sorted(p for p in placed_pns if p not in by_pn)
    if missing:
        print(f"GUARD: {len(missing)} decisions are not on the master: {missing[:5]}. STOP.",
              file=sys.stderr)
        return 3

    # only fill a placeholder row; everything else is skipped and reported
    to_fill, skipped = [], []
    for d in placed:
        pn = d["pn"]
        r = by_pn[pn]
        cur = norm(r[idx["aim_l1"]])
        if cur in PLACEHOLDER:
            to_fill.append(d)
        else:
            skipped.append((pn, cur, r[idx["aim_l2"]], r[idx["aim_l3"]]))
    print(f"rows to fill: {len(to_fill)} | skipped (aim_l1 already set): {len(skipped)}")
    for s in skipped[:10]:
        print("   skipped:", s)

    # snapshot the 92 and the 44 as they are now
    snap_blocked = {p: list(by_pn[p]) for p in blocked if p in by_pn}
    snap_44 = {p: list(by_pn[p]) for p in notin if p in by_pn}
    print(f"snapshot: {len(snap_blocked)} blocked rows, {len(snap_44)} appended rows")

    # ---------------- write the candidate ----------------
    out_rows = [list(r) for r in data]
    pos = {r[0]: i for i, r in enumerate(out_rows)}
    for d in to_fill:
        r = out_rows[pos[d["pn"]]]
        r[idx["aim_l1"]] = norm(d["chosen_l1"])
        r[idx["aim_l2"]] = norm(d["chosen_l2"])
        r[idx["aim_l3"]] = norm(d["chosen_l3"])
        r[idx["aim_l1_fixed"]] = norm(d["chosen_l1"])
        r[idx["aim_l2_fixed"]] = norm(d["chosen_l2"])
        r[idx["has_aim"]] = "1"
        r[idx["aim_source"]] = STAMP
        r[idx["aim_changed"]] = STAMP

    tmp = MASTER.with_suffix(".csv.tmp")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(header)
    w.writerows(out_rows)
    tmp.write_bytes(buf.getvalue().encode("utf-8"))

    # ---------------- gate ----------------
    with tmp.open(encoding="utf-8", newline="") as fh:
        got = list(csv.reader(fh))
    got_hdr, got_data = got[0], got[1:]

    touched = {d["pn"] for d in to_fill}
    untargeted_changed = []
    targeted_unchanged = []
    wrong_cols = []
    for before_row, after_row in zip(data, got_data):
        pn = before_row[0]
        if pn in touched:
            if before_row == after_row:
                targeted_unchanged.append(pn)
                continue
            for i in range(len(header)):
                if before_row[i] != after_row[i] and header[i] not in TOUCHABLE:
                    wrong_cols.append((pn, header[i], before_row[i], after_row[i]))
        elif before_row != after_row:
            untargeted_changed.append(pn)

    after_by = {r[0]: r for r in got_data}
    bad_fill = []
    for d in to_fill:
        r = after_by.get(d["pn"])
        want = (norm(d["chosen_l1"]), norm(d["chosen_l2"]), norm(d["chosen_l3"]))
        if r is None:
            bad_fill.append((d["pn"], "row missing"))
            continue
        if (r[idx["aim_l1"]], r[idx["aim_l2"]], r[idx["aim_l3"]]) != want:
            bad_fill.append((d["pn"], "levels wrong"))
        if r[idx["aim_l1_fixed"]] != want[0] or r[idx["aim_l2_fixed"]] != want[1]:
            bad_fill.append((d["pn"], "fixed columns wrong"))
        if r[idx["aim_source"]] != STAMP or r[idx["has_aim"]] != "1":
            bad_fill.append((d["pn"], "stamp/has_aim wrong"))
        if r[idx["aim_changed"]] != STAMP:
            bad_fill.append((d["pn"], "aim_changed wrong"))

    blocked_changed = [p for p, old in snap_blocked.items() if after_by.get(p) != old]
    stamped_blocked = [p for p in blocked if p in after_by and after_by[p][idx["aim_source"]] == STAMP]
    appended_changed = [p for p, old in snap_44.items() if after_by.get(p) != old]
    appended_stamp_ok = sum(1 for p in notin
                            if p in after_by and after_by[p][idx["aim_source"]] == STAMP)

    checks = {
        "header_identical": got_hdr == header,
        "row_count_unchanged": len(got_data) == len(data),
        "no_untargeted_row_changed": not untargeted_changed,
        "every_targeted_row_changed": not targeted_unchanged,
        "only_the_eight_aim_columns_changed": not wrong_cols,
        "no_duplicate_part_numbers": len({r[0] for r in got_data}) == len(got_data),
        "sorted_ascending": [r[0] for r in got_data] == sorted(r[0] for r in got_data),
        "all_targets_carry_levels_and_stamp": not bad_fill,
        "the_92_blocked_rows_unchanged": not blocked_changed,
        "none_of_the_92_carries_the_fill_stamp": not stamped_blocked,
        "the_44_appended_rows_unchanged": not appended_changed,
        "all_44_still_carry_the_append_stamp": appended_stamp_ok == len(notin),
        "no_bom": not tmp.read_bytes().startswith(b"\xef\xbb\xbf"),
        "crlf_only": (tmp.read_bytes().count(b"\n") == tmp.read_bytes().count(b"\r\n")),
    }
    print("\nGATE:")
    for k, v in checks.items():
        print(f"   {k:<50} {'PASS' if v else 'FAIL'}")
    if not all(checks.values()):
        if untargeted_changed:
            print(f"untargeted rows changed (first 10): {untargeted_changed[:10]}", file=sys.stderr)
        if targeted_unchanged:
            print(f"targeted rows unchanged (first 10): {targeted_unchanged[:10]}", file=sys.stderr)
        if wrong_cols:
            print(f"wrong columns (first 10): {wrong_cols[:10]}", file=sys.stderr)
        if bad_fill:
            print(f"bad fills (first 10): {bad_fill[:10]}", file=sys.stderr)
        tmp.unlink(missing_ok=True)
        print("GATE FAILED — master NOT replaced.", file=sys.stderr)
        return 4

    # ---------------- backup, then replace ----------------
    shutil.copy2(MASTER, backup)
    if sha256_of(backup) != before_sha:
        tmp.unlink(missing_ok=True)
        print("GUARD: backup hash does not match the original. STOP.", file=sys.stderr)
        return 5
    MASTER.unlink()
    tmp.replace(MASTER)
    after_sha = sha256_of(MASTER)

    summary = {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "stamp": STAMP,
        "master": str(MASTER),
        "backup": str(backup),
        "rows_before": len(data),
        "rows_after": len(got_data),
        "rows_filled": len(to_fill),
        "rows_skipped_already_set": len(skipped),
        "sha256_before": before_sha,
        "sha256_after": after_sha,
        "bytes_before": before_bytes,
        "bytes_after": MASTER.stat().st_size,
        "checks": checks,
        "gate_pass": True,
        "placed": [
            {"pn": d["pn"], "description": d["description"], "fig_key": d["fig_key"],
             "aim": [d["chosen_l1"], d["chosen_l2"], d["chosen_l3"]],
             "support_master": int(d["support_master"]),
             "support_classified_workbook_aim_axis": int(d["support_classified_workbook"]),
             "figure_key_top_path": d["fig_key_top_path"],
             "figure_key_n": int(d["fig_key_n"]),
             "figure_key_disagrees_with_chosen_path": d["fig_key_disagrees"] == "True"}
            for d in to_fill
        ],
        "unplaced": [
            {"pn": d["pn"], "description": d["description"], "fig_key": d["fig_key"],
             "list_eur": d["list_eur"], "reason": d["unplaced_reason"],
             "evidence": d["evidence"]}
            for d in unplaced
        ],
        "skipped": [{"pn": p, "current_aim_l1": c, "aim_l2": l2, "aim_l3": l3}
                    for p, c, l2, l3 in skipped],
    }
    (F / "apply_fill_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nbackup -> {backup.name}")
    print(f"master after: {len(got_data)} rows, {summary['bytes_after']:,} bytes")
    print(f"master after sha256: {after_sha}")
    print(f"filled {len(to_fill)} rows; skipped {len(skipped)}; unplaced {len(unplaced)}")
    print(f"summary -> {F / 'apply_fill_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
