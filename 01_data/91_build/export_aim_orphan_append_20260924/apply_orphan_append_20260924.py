# -*- coding: utf-8 -*-
"""Append the 43 orphan IE40 part numbers to aim_master_v2.csv.

Jerome 2026-09-24, authorised: do not leave a part that exists on a live price list with
nowhere to sit. Scope is ONLY the 43 part numbers in
`01_data/91_build/export_aim_eq_20260924/orphans_43.csv` that have no row on the master.
The 25 carrying the Unknown marker and the 31 with a blank family are NOT touched.

The path for each row comes from `decision_orphans.csv`, written by `decide_orphans.py`:
route (a) the EPC figure name read through aim_rules.py, route (b) exact-description
agreement with the figure key as a veto, route (c) left unplaced.

Safety
  * backup first, hash-checked against the original before anything is replaced
  * candidate built in a temporary file in the same folder, then os.replace (atomic)
  * gate: header identical, row count +N, every pre-existing row unchanged by part number,
    the new rows carry the decided levels and the stamp, no duplicates, still sorted
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_orphan_append_20260924"
MASTER = DER / "aim_master_v2.csv"
DECISION = OUT / "decision_orphans.csv"
ORPHANS = EQ / "orphans_43.csv"
BLOCKED = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924" / "carried_out_blocked_precedence.txt"
FREE = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924" / "would_land_free.txt"
EARLIER44 = ROOT / "01_data" / "91_build" / "export_aim_append_20260924" / "decision_44_final.csv"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ts = datetime.now().strftime("%H%M%S")
    backup = DER / f"aim_master_v2.csv.bak_pre_orphan_append_20260924_{ts}"

    with DECISION.open(encoding="utf-8-sig", newline="") as fh:
        decisions = list(csv.DictReader(fh))
    placed = [d for d in decisions if d["place"].strip().lower() == "true"]
    print(f"decisions {len(decisions)} | placed {len(placed)} | unplaced {len(decisions) - len(placed)}")

    # every orphan must be decided, one row each
    with ORPHANS.open(encoding="utf-8-sig", newline="") as fh:
        orphans = list(csv.DictReader(fh))
    o_pns = sorted(r["part_number"].strip().upper() for r in orphans)
    d_pns = sorted(d["pn"].strip().upper() for d in decisions)
    if o_pns != d_pns or len(set(d_pns)) != 43:
        print("GUARD: decision file does not cover exactly the 43 orphans. STOP.", file=sys.stderr)
        return 3

    # never touch the 92 blocked, the 164 free, or the earlier 44
    def pns_of(path: Path) -> set[str]:
        if not path.exists():
            return set()
        if path.suffix == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as fh:
                return {r["pn"].strip().upper() for r in csv.DictReader(fh)}
        return {l.strip().upper() for l in path.read_text().splitlines() if l.strip()}

    forbidden = pns_of(BLOCKED) | pns_of(FREE) | pns_of(EARLIER44)
    overlap = {d["pn"].strip().upper() for d in decisions} & forbidden
    if overlap:
        print(f"GUARD: overlap with a set I must not touch: {sorted(overlap)}. STOP.", file=sys.stderr)
        return 3
    print(f"guard: no overlap with the {len(pns_of(BLOCKED))} blocked, "
          f"{len(pns_of(FREE))} free, or {len(pns_of(EARLIER44))} earlier-44 sets")

    # ---------------- read the master as bytes ----------------
    before_sha = sha256_of(MASTER)
    before_bytes = MASTER.stat().st_size
    with MASTER.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    print(f"master before: {len(data)} rows, {len(header)} cols, {before_bytes:,} bytes")
    print(f"master before sha256: {before_sha}")

    idx = {c: i for i, c in enumerate(header)}
    existing = {r[0] for r in data}
    already = {d["pn"] for d in placed} & existing
    if already:
        print(f"GUARD: already on the master: {sorted(already)}. STOP.", file=sys.stderr)
        return 3

    def cell(name: str) -> int:
        if name not in idx:
            raise SystemExit(f"missing column {name}")
        return idx[name]

    # ---------------- build the new rows ----------------
    new_rows = []
    for d in placed:
        row = [""] * len(header)
        pn = d["pn"].strip()
        fig_key = d["fig_key"].strip()
        fig_no, _, key_no = fig_key.partition("-")
        fig_no = fig_no.strip()
        key_no = key_no.strip()
        fig_no_padded = fig_no.zfill(3) if fig_no.isdigit() else fig_no
        # master convention, measured: fig_key is built fig_no-key_no only where the
        # key number is numeric; otherwise fig_key stays blank and fig_no/key_no carry it.
        master_fig_key = f"{fig_no_padded}-{key_no}" if key_no.isdigit() else ""

        row[cell("part_number")] = pn
        row[cell("description")] = d["description"].strip()
        row[cell("aim_l1")] = d["chosen_l1"].strip()
        row[cell("aim_l2")] = d["chosen_l2"].strip()
        row[cell("aim_l3")] = d["chosen_l3"].strip()
        row[cell("aim_demand_type")] = ""     # not unanimous; mirror the earlier appends
        row[cell("aim_core_noncore")] = ""
        row[cell("cat_l1")] = ""              # no upstream price-list catalogue row exists
        row[cell("cat_l2")] = ""
        row[cell("cat_l3")] = ""
        row[cell("cat_pms_flag")] = "0"       # master rule: 1 only when cat_l2 is a PMS family
        row[cell("fig_key")] = master_fig_key
        row[cell("fig_no")] = fig_no_padded
        row[cell("key_no")] = key_no
        row[cell("price_class_iml")] = ""     # not in the per-distributor pricing basis
        row[cell("aim_source")] = d["stamp"].strip()
        row[cell("has_aim")] = "1"
        row[cell("has_catalogue_node")] = "0"
        row[cell("desc_ambiguous")] = "0"
        row[cell("l12m_billed_eur")] = "0.0"  # measured: nothing billed inside the frozen window
        row[cell("eur")] = "0.0"
        row[cell("aim_l1_fixed")] = d["chosen_l1"].strip()
        row[cell("aim_l2_fixed")] = d["chosen_l2"].strip()
        row[cell("aim_changed")] = d["stamp"].strip()
        # the eight jp_* columns stay blank, as the earlier appends left them
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
    changed = [pn for pn, old in by_pn_before.items() if by_pn_after.get(pn) != old]

    aim_cols = ["aim_l1", "aim_l2", "aim_l3", "aim_source", "has_aim",
                "aim_l1_fixed", "aim_l2_fixed", "aim_changed"]
    aim_ok = all(by_pn_after[p][idx[c]] == by_pn_before[p][idx[c]]
                 for p in by_pn_before for c in aim_cols)

    new_ok = True
    for d in placed:
        r = by_pn_after.get(d["pn"])
        if r is None:
            new_ok = False
            break
        if (r[idx["aim_l1"]], r[idx["aim_l2"]], r[idx["aim_l3"]]) != (
                d["chosen_l1"].strip(), d["chosen_l2"].strip(), d["chosen_l3"].strip()):
            new_ok = False
            break
        if r[idx["aim_source"]] != d["stamp"].strip() or r[idx["has_aim"]] != "1":
            new_ok = False
            break

    # The two groups I must not touch: the 25 still carrying the marker on this price list
    # and the 31 whose family is blank. Measured now, from the master as it stood before.
    with (EQ / "queue.csv").open(encoding="utf-8-sig", newline="") as fh:
        q_pns = {(r["pn"] or "").strip().upper() for r in csv.DictReader(fh)}
    mine = {d["pn"].strip().upper() for d in decisions}
    marker_pns, blank_pns = set(), set()
    for r in data:
        pn = r[0]
        if pn not in q_pns:
            continue
        l1 = (r[idx["aim_l1_fixed"]] or "").strip() or (r[idx["aim_l1"]] or "").strip()
        if l1.lower().startswith("unknown"):
            marker_pns.add(pn)
        elif l1 == "":
            blank_pns.add(pn)
    print(f"on this price list: {len(marker_pns)} carry the marker, {len(blank_pns)} have a blank family")
    overlap_guarded = mine & (marker_pns | blank_pns)
    guarded_rows_unchanged = all(by_pn_after.get(p) == by_pn_before.get(p)
                                 for p in (marker_pns | blank_pns))
    untouched_ok = all(by_pn_after.get(p) == by_pn_before.get(p)
                       for p in forbidden
                       if p in by_pn_before or p in by_pn_after)

    checks = {
        "header_identical": got_hdr == header,
        "columns_identical": len(got_hdr) == len(header),
        "row_count_plus_n": len(got_data) == len(data) + len(placed),
        "every_preexisting_row_unchanged": not changed,
        "no_aim_column_changed_on_preexisting_rows": aim_ok,
        "no_duplicate_part_numbers": len({r[0] for r in got_data}) == len(got_data),
        "sorted_ascending": [r[0] for r in got_data] == sorted(r[0] for r in got_data),
        "new_rows_carry_levels_and_stamp": new_ok,
        "untouched_sets_unchanged": untouched_ok,
        "marker_and_blank_rows_unchanged": guarded_rows_unchanged,
        "no_overlap_with_marker_or_blank_rows": not overlap_guarded,
        "no_bom": not tmp.read_bytes().startswith(b"\xef\xbb\xbf"),
        "crlf_only": b"\r\n" in tmp.read_bytes() and b"\n" not in tmp.read_bytes().replace(b"\r\n", b""),
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

    # ---------------- backup, then replace atomically ----------------
    shutil.copy2(MASTER, backup)
    if sha256_of(backup) != before_sha:
        tmp.unlink(missing_ok=True)
        print("GUARD: backup hash does not match the original. STOP.", file=sys.stderr)
        return 5
    os.replace(tmp, MASTER)
    after_sha = sha256_of(MASTER)

    summary = {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "rows_before": len(data),
        "rows_after": len(got_data),
        "rows_added": len(placed),
        "unplaced": [d["pn"] for d in decisions if not d["place"].strip().lower().startswith("t")],
        "master": str(MASTER),
        "backup": str(backup),
        "sha256_before": before_sha,
        "sha256_after": after_sha,
        "bytes_before": before_bytes,
        "bytes_after": MASTER.stat().st_size,
        "checks": checks,
        "gate_pass": True,
        "placed": [
            {"pn": d["pn"], "description": d["description"],
             "aim": [d["chosen_l1"], d["chosen_l2"], d["chosen_l3"]],
             "route": d["route"], "stamp": d["stamp"],
             "evidence": d["evidence"]}
            for d in placed
        ],
    }
    (OUT / "apply_orphan_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nbackup -> {backup}")
    print(f"master after: {len(got_data)} rows, {summary['bytes_after']:,} bytes")
    print(f"master after sha256: {after_sha}")
    print(f"summary -> {OUT / 'apply_orphan_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
