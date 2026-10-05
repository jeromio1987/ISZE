"""Negative tests for schema_guard: prove it FAILS on a lost column and PASSES on an added one.

Uses a scratch copy of the derived directory so the live files are never touched.
"""
from __future__ import annotations

import csv
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
sys.path.insert(0, str(REPO / "03_analytics" / "Isuzu" / "prism"))

import yaml  # noqa: E402

from modules import schema_guard  # noqa: E402

fx = yaml.safe_load((REPO / "03_analytics/Isuzu/prism/data/verification_fixtures.yaml")
                    .read_text(encoding="utf-8"))
FILES = fx["schema_required"]["files"]
LIVE = REPO / "01_data" / "00_derived"

failures: list[str] = []


def flat(envelope):
    out = []
    for e in envelope["files"]:
        out.append((e["file"], e["status"], tuple(e["missing"]), tuple(e["added"])))
    return out


with tempfile.TemporaryDirectory() as td:
    scratch = Path(td)
    for spec in FILES:
        src = LIVE / spec["file"]
        if src.exists():
            shutil.copy2(src, scratch / spec["file"])

    print("=== TEST 1: baseline on the scratch copy (repo_root=None, so no git arm) ===")
    res = schema_guard.evaluate(FILES, scratch, None)
    for row in flat(res):
        print("   ", row)
    if any(r[1] != "ok" for r in flat(res)):
        failures.append("baseline scratch copy did not read ok")
    print("   ->", "PASS" if not failures else "FAIL")

    print("\n=== TEST 2: drop `coverage_note` from the scratch gps file (the real incident) ===")
    p = scratch / "gps_spu_by_distributor.csv"
    raw = p.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(raw)))
    idx = rows[0].index("coverage_note")
    rows[0].pop(idx)
    for r in rows[1:]:
        r.pop(idx)
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    (scratch / "gps_spu_by_distributor.csv").write_text(buf.getvalue(), encoding="utf-8")
    res = schema_guard.evaluate(FILES, scratch, None)
    got = dict((e["file"], e) for e in res["files"])["gps_spu_by_distributor.csv"]
    print("    status:", got["status"], "missing:", got["missing"])
    ok = got["status"] == "column_lost" and got["missing"] == ["coverage_note"]
    print("   ->", "PASS" if ok else "FAIL")
    if not ok:
        failures.append("guard did not catch a dropped coverage_note column")

    print("\n=== TEST 3: drop `period_basis` too (both columns lost, as on 2026-09-21) ===")
    raw = p.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(raw)))
    idx = rows[0].index("period_basis")
    rows[0].pop(idx)
    for r in rows[1:]:
        r.pop(idx)
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    (scratch / "gps_spu_by_distributor.csv").write_text(buf.getvalue(), encoding="utf-8")
    res = schema_guard.evaluate(FILES, scratch, None)
    got = dict((e["file"], e) for e in res["files"])["gps_spu_by_distributor.csv"]
    print("    status:", got["status"], "missing:", got["missing"])
    ok = got["status"] == "column_lost" and set(got["missing"]) == {"period_basis", "coverage_note"}
    print("   ->", "PASS" if ok else "FAIL")
    if not ok:
        failures.append("guard did not catch both annotation columns vanishing")

    print("\n=== TEST 4: an ADDED column must not fail ===")
    # Restore the file first: tests 2 and 3 deliberately removed columns from this copy.
    shutil.copy2(LIVE / "gps_spu_by_distributor.csv", scratch / "gps_spu_by_distributor.csv")
    p = scratch / "gps_spu_by_distributor.csv"
    raw = p.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(raw)))
    rows[0].append("some_new_note")
    for r in rows[1:]:
        r.append("x")
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    (scratch / "gps_spu_by_distributor.csv").write_text(buf.getvalue(), encoding="utf-8")
    res = schema_guard.evaluate(FILES, scratch, None)
    got = dict((e["file"], e) for e in res["files"])["gps_spu_by_distributor.csv"]
    print("    status:", got["status"], "added:", got["added"])
    ok = got["status"] == "ok" and "some_new_note" in got["added"]
    print("   ->", "PASS" if ok else "FAIL")
    if not ok:
        failures.append("an added column wrongly failed the guard")

    print("\n=== TEST 5: metrics_snapshot.json — drop one metric key ===")
    sp = scratch / "metrics_snapshot.json"
    doc = json.loads(sp.read_text(encoding="utf-8"))
    doc["metrics"].pop("verify.fail", None)
    sp.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    res = schema_guard.evaluate(FILES, scratch, None)
    got = dict((e["file"], e) for e in res["files"])["metrics_snapshot.json"]
    print("    status:", got["status"], "missing:", got["missing"])
    ok = got["status"] == "column_lost" and "verify.fail" in got["missing"]
    print("   ->", "PASS" if ok else "FAIL")
    if not ok:
        failures.append("guard did not catch a dropped metrics_snapshot key")

    print("\n=== TEST 6: missing file is a fail, not a silent skip ===")
    (scratch / "network_percentile.csv").unlink()
    res = schema_guard.evaluate(FILES, scratch, None)
    got = dict((e["file"], e) for e in res["files"])["network_percentile.csv"]
    print("    status:", got["status"])
    ok = got["status"] == "missing_file"
    print("   ->", "PASS" if ok else "FAIL")
    if not ok:
        failures.append("a declared file that vanished was not flagged")

print()
if failures:
    print("RESULT: FAIL")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("RESULT: PASS - all 6 schema_guard behaviours verified on a scratch copy")
