# -*- coding: utf-8 -*-
"""Append the billed parts the release 2026-10-04 added that are absent from aim_master_v2.csv.

Jerome 2026-10-04 ("yes please": rebuild the export and ship the four AIM pages on release
2026-10-04, with the master refresh for the added parts). Same method as
apply_export_pr00_append_20260924.py: the master is the spine of the AIM export, a part that
is not on it cannot reach the export or a page, whatever the release says.

Scope: release rows whose aim_source is 'missing_billed_20261004' AND whose part number is not
on the master. Labels are taken from the release (aim_l1_fixed / aim_l2_fixed / aim_l3_fixed);
nothing is decided here. Caveat carried from 24 Sep: build_aim_master.py does not read the
master as an input, so a future spine rebuild would drop these rows.

Safety: backup first; atomic replace (write .tmp, verify, then move); gate = header identical,
row count +N, every pre-existing row byte-identical, new rows carry the release levels and stamp.
"""
from __future__ import annotations

import csv
import hashlib
import io
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
MASTER = D / "aim_master_v2.csv"
RELEASE = D / "_releases" / "aim_pn_classification_release_2026-10-04.csv"
STAMP = "missing_billed_20261004"


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for ch in iter(lambda: fh.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def main() -> int:
    ts = datetime.now().strftime("%H%M%S")
    backup = D / f"aim_master_v2.csv.bak_pre_release_append_20261004_{ts}"
    with RELEASE.open(encoding="utf-8", newline="") as fh:
        rel = list(csv.DictReader(fh))
    raw_before = MASTER.read_bytes()
    crlf = b"\r\n" in raw_before[:5000]
    with MASTER.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    idx = {c: i for i, c in enumerate(header)}
    existing = {r[0] for r in data}
    todo = [r for r in rel if r["aim_source"] == STAMP and r["part_number"] not in existing]
    allstamped = [r for r in rel if r["aim_source"] == STAMP]
    print(f"release rows stamped {STAMP}: {len(allstamped)}; not on master: {len(todo)}")
    print(f"master before: {len(data)} rows, {len(header)} cols, crlf={crlf}, sha256 {sha256_of(MASTER)}")
    if len(allstamped) != 24 or len(todo) != 20:
        print("GUARD: expected 24 stamped / 20 missing. STOP.", file=sys.stderr)
        return 3

    new_rows = []
    for r in todo:
        row = [""] * len(header)
        fk = (r["fig_key"] or "").strip()
        fig_no, _, key_no = fk.partition("-")
        fig_no = fig_no.zfill(3) if fig_no.isdigit() else fig_no
        mfk = f"{fig_no}-{key_no}" if key_no.isdigit() else ""
        row[idx["part_number"]] = r["part_number"]
        row[idx["description"]] = (r["description_norm"] or "").strip()
        row[idx["aim_l1"]] = r["aim_l1_fixed"]
        row[idx["aim_l2"]] = r["aim_l2_fixed"]
        row[idx["aim_l3"]] = r["aim_l3_fixed"]
        row[idx["cat_pms_flag"]] = "0"
        row[idx["fig_key"]] = mfk
        row[idx["fig_no"]] = fig_no
        row[idx["key_no"]] = key_no
        row[idx["aim_source"]] = STAMP
        row[idx["has_aim"]] = "1"
        row[idx["has_catalogue_node"]] = "0"
        row[idx["desc_ambiguous"]] = "0"
        row[idx["l12m_billed_eur"]] = r["l12m_billed_eur"] or "0.0"
        row[idx["eur"]] = "0.0"
        row[idx["aim_l1_fixed"]] = r["aim_l1_fixed"]
        row[idx["aim_l2_fixed"]] = r["aim_l2_fixed"]
        row[idx["aim_changed"]] = STAMP
        new_rows.append(row)

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

    shutil.copy2(MASTER, backup)
    assert sha256_of(backup) == sha256_of(MASTER), "backup does not match"
    tmp = MASTER.with_suffix(".csv.tmp")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n" if crlf else "\n")
    w.writerow(header)
    w.writerows(merged)
    tmp.write_bytes(buf.getvalue().encode("utf-8"))

    with tmp.open(encoding="utf-8", newline="") as fh:
        got = list(csv.reader(fh))
    gh, gd = got[0], got[1:]
    before = {r[0]: r for r in data}
    after = {r[0]: r for r in gd}
    ok_hdr = gh == header
    ok_n = len(gd) == len(data) + len(new_rows)
    ok_old = all(after.get(pn) == r for pn, r in before.items())
    ok_new = all(
        (after[r["part_number"]][idx["aim_l1"]], after[r["part_number"]][idx["aim_l2"]], after[r["part_number"]][idx["aim_l3"]],
         after[r["part_number"]][idx["aim_source"]]) == (r["aim_l1_fixed"], r["aim_l2_fixed"], r["aim_l3_fixed"], STAMP)
        for r in todo)
    ok_sorted = [r[0] for r in gd] == sorted(r[0] for r in gd) or [r[0] for r in gd] == [r[0] for r in merged]
    print(f"gate: header {ok_hdr} | rows +{len(new_rows)} {ok_n} | pre-existing rows identical {ok_old} | new rows carry release levels {ok_new}")
    if not (ok_hdr and ok_n and ok_old and ok_new):
        tmp.unlink(missing_ok=True)
        print("GATE FAILED: master untouched, backup kept.", file=sys.stderr)
        return 1
    tmp.replace(MASTER)
    print(f"master after: {len(gd)} rows, sha256 {sha256_of(MASTER)}; backup {backup.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())