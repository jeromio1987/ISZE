# -*- coding: utf-8 -*-
"""Append the 44 PR00 IE40 part numbers that were absent from aim_master_v2.csv.

Jerome 2026-09-24, authorised. Scope:
  * ONLY the 44 part numbers in
    01_data/91_build/_tmp_apply_export_pr00_20260924/carried_out_not_in_master.txt
  * the 92 in carried_out_blocked_precedence.txt are NOT touched
  * the 164 in would_land_free.txt are NOT touched

Path for each row comes from the decision file written by finalise_decisions.py:
the exact description's own AIM path, where the master and the classified workbook
agree on ONE full path with >= 3 supporting parts. The figure key is used only as a
veto and never as the source (AIM_CLASSIFICATION_AUDIT_2026-09-17.md documents the
mis-filing traps).

Safety
  * backup written first
  * atomic replace (write .tmp, verify, then move)
  * gate: header identical, row count +N, every pre-existing cell unchanged, the new
    rows carry the decided levels and the stamp
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
OUTDIR = ROOT / "01_data" / "91_build" / "export_aim_append_20260924"
MASTER = D / "aim_master_v2.csv"
DECISION = OUTDIR / "decision_44_final.csv"
BLOCKED = A / "carried_out_blocked_precedence.txt"
FREE = A / "would_land_free.txt"
STAMP = "export_pr00_20260924"


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
    backup = D / f"aim_master_v2.csv.bak_pre_export_append_20260924_{ts}"

    # ---------------- read the decision ----------------
    with DECISION.open(encoding="utf-8-sig", newline="") as fh:
        decisions = list(csv.DictReader(fh))
    print(f"decisions: {len(decisions)}")

    blocked = {l.strip() for l in BLOCKED.read_text().splitlines() if l.strip()}
    free = {l.strip() for l in FREE.read_text().splitlines() if l.strip()}
    new_pns = {d["pn"] for d in decisions}
    print(f"blocked list {len(blocked)} | free list {len(free)} | overlap with my set: "
          f"{len(new_pns & blocked)} blocked, {len(new_pns & free)} free")
    if new_pns & blocked or new_pns & free:
        print("GUARD: my set overlaps a list I must not touch. STOP.", file=sys.stderr)
        return 3

    # ---------------- read the master exactly as bytes ----------------
    before_sha = sha256_of(MASTER)
    before_bytes = MASTER.stat().st_size
    with MASTER.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    print(f"master before: {len(data)} rows, {len(header)} cols, {before_bytes:,} bytes")
    print(f"master before sha256: {before_sha}")

    existing = {r[0] for r in data}
    already = new_pns & existing
    if already:
        print(f"GUARD: {len(already)} of my set are already on the master: "
              f"{sorted(already)}. STOP.", file=sys.stderr)
        return 3

    idx = {c: i for i, c in enumerate(header)}

    def cell(name: str) -> int:
        if name not in idx:
            raise SystemExit(f"missing column {name}")
        return idx[name]

    # ---------------- build the new rows ----------------
    new_rows = []
    for d in decisions:
        row = [""] * len(header)
        pn = d["pn"]
        fig_key = norm(d["fig_key"])                    # e.g. 377-134 or 001-HAA
        fig_no, _, key_no = fig_key.partition("-")
        fig_no = fig_no.strip()
        key_no = key_no.strip()
        # master convention (measured): fig_no/key_no zero-padded to 3; fig_key is built
        # as fig_no-key_no ONLY where key_no is numeric, else it stays blank.
        fig_no_padded = fig_no.zfill(3) if fig_no.isdigit() else fig_no
        master_fig_key = f"{fig_no_padded}-{key_no}" if key_no.isdigit() else ""

        row[cell("part_number")] = pn
        row[cell("description")] = norm(d["description"])
        row[cell("aim_l1")] = norm(d["chosen_l1"])
        row[cell("aim_l2")] = norm(d["chosen_l2"])
        row[cell("aim_l3")] = norm(d["chosen_l3"])
        row[cell("aim_demand_type")] = ""      # not unanimous for all 44; mirror prior applies
        row[cell("aim_core_noncore")] = ""
        row[cell("cat_l1")] = ""               # no upstream price-list catalogue row exists
        row[cell("cat_l2")] = ""
        row[cell("cat_l3")] = ""
        row[cell("cat_pms_flag")] = "0"        # master rule: 1 only if cat_l2 is a PMS family
        row[cell("fig_key")] = master_fig_key
        row[cell("fig_no")] = fig_no_padded
        row[cell("key_no")] = key_no
        row[cell("price_class_iml")] = ""      # not in the per-distributor pricing basis
        row[cell("aim_source")] = STAMP
        row[cell("has_aim")] = "1"
        row[cell("has_catalogue_node")] = "0"
        row[cell("desc_ambiguous")] = "0"
        row[cell("l12m_billed_eur")] = "0.0"   # measured: no billing inside the frozen window
        row[cell("eur")] = "0.0"
        row[cell("aim_l1_fixed")] = norm(d["chosen_l1"])
        row[cell("aim_l2_fixed")] = norm(d["chosen_l2"])
        row[cell("aim_changed")] = STAMP
        new_rows.append(row)

    # ---------------- insert keeping the master sorted by part_number ----------------
    merged = list(data)
    for row in new_rows:
        pn = row[0]
        lo, hi = 0, len(merged)
        while lo < hi:
            mid = (lo + hi) // 2
            if merged[mid][0] < pn:
                lo = mid + 1
            else:
                hi = mid
        merged.insert(lo, row)

    # ---------------- write the candidate ----------------
    tmp = MASTER.with_suffix(".csv.tmp")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(header)
    w.writerows(merged)
    tmp.write_bytes(buf.getvalue().encode("utf-8"))

    # ---------------- gate ----------------
    with tmp.open(encoding="utf-8", newline="") as fh:
        got = list(csv.reader(fh))
    got_hdr, got_data = got[0], got[1:]

    by_pn_before = {r[0]: r for r in data}
    by_pn_after = {r[0]: r for r in got_data}

    untouched_ok = True
    changed = []
    for pn, old in by_pn_before.items():
        new = by_pn_after.get(pn)
        if new is None or new != old:
            untouched_ok = False
            changed.append(pn)

    aim_cols = ["aim_l1", "aim_l2", "aim_l3", "aim_source", "has_aim",
                "aim_l1_fixed", "aim_l2_fixed", "aim_changed"]
    aim_ok = all(by_pn_after[p][idx[c]] == by_pn_before[p][idx[c]]
                 for p in by_pn_before for c in aim_cols)

    new_ok = True
    for d in decisions:
        r = by_pn_after.get(d["pn"])
        if r is None:
            new_ok = False
            break
        if (r[idx["aim_l1"]], r[idx["aim_l2"]], r[idx["aim_l3"]]) != (
                norm(d["chosen_l1"]), norm(d["chosen_l2"]), norm(d["chosen_l3"])):
            new_ok = False
            break
        if r[idx["aim_source"]] != STAMP or r[idx["has_aim"]] != "1":
            new_ok = False
            break

    checks = {
        "header_identical": got_hdr == header,
        "columns_identical": len(got_hdr) == len(header),
        "row_count_plus_n": len(got_data) == len(data) + len(decisions),
        "every_preexisting_row_unchanged": untouched_ok,
        "no_aim_column_changed_on_preexisting_rows": aim_ok,
        "no_duplicate_part_numbers": len({r[0] for r in got_data}) == len(got_data),
        "sorted_ascending": [r[0] for r in got_data] == sorted(r[0] for r in got_data),
        "new_rows_carry_levels_and_stamp": new_ok,
        "no_bom": not tmp.read_bytes().startswith(b"\xef\xbb\xbf"),
    }
    print("\nGATE:")
    for k, v in checks.items():
        print(f"   {k:<50} {'PASS' if v else 'FAIL'}")
    if not all(checks.values()):
        if changed:
            print(f"rows that changed (first 10): {changed[:10]}", file=sys.stderr)
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
        "rows_added": len(decisions),
        "sha256_before": before_sha,
        "sha256_after": after_sha,
        "bytes_before": before_bytes,
        "bytes_after": MASTER.stat().st_size,
        "checks": checks,
        "gate_pass": True,
        "placed": [
            {"pn": d["pn"], "description": d["description"],
             "aim": [d["chosen_l1"], d["chosen_l2"], d["chosen_l3"]],
             "support_master": d["support_master"],
             "support_classified_workbook": d["support_classified_workbook"]}
            for d in decisions
        ],
    }
    (OUTDIR / "apply_append_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nbackup -> {backup.name}")
    print(f"master after: {len(got_data)} rows, {summary['bytes_after']:,} bytes")
    print(f"master after sha256: {after_sha}")
    print(f"summary -> {OUTDIR / 'apply_append_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
