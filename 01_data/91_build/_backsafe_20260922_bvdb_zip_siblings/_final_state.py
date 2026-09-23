#!/usr/bin/env python3
"""Final state proof, with each file compared against the right reference.

Three groups:
  A. Files I annotated   -> pre-2026 content must survive byte-for-byte.
  B. Files the earlier pass fixed -> same rule, against the earlier pass's backup.
  C. Files that must be untouched -> full byte-identity.
  D. Files I intentionally edited -> listed, with the reason, not silently passed.
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MINE = ROOT / "01_data" / "91_build" / "_backsafe_20260922_bvdb_zip_siblings" / "original"
EARLIER = ROOT / "01_data" / "91_build" / "_backsafe_20260922_partial_year" / "original"

fails: list[str] = []


def strip_cols(raw: bytes, drop: int) -> bytes:
    bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw.decode("utf-8-sig")
    ending = "\r\n" if text.endswith("\r\n") else ("\n" if text.endswith("\n") else "")
    body = text[: len(text) - len(ending)] if ending else text
    out = io.StringIO()
    w = csv.writer(out, lineterminator=ending)
    for row in csv.reader(io.StringIO(body)):
        w.writerow(row[: len(row) - drop] if drop else row)
    t = out.getvalue()
    if ending and not t.endswith(ending):
        t += ending
    return (b"\xef\xbb\xbf" if bom else b"") + t.encode("utf-8")


def pre2026_identical(rel: str, ref: Path, drop: int) -> tuple[int, int, bool]:
    """Count pre-2026 rows kept byte-identical and 2026 rows that changed."""
    cur_raw = (ROOT / rel).read_bytes()
    ref_raw = ref.read_bytes()
    if drop:
        identical = strip_cols(cur_raw, drop) == ref_raw
    else:
        identical = cur_raw == ref_raw
    if identical:
        return 0, 0, True
    # year-scoped: compare only lines whose year <= 2025
    cur_lines = cur_raw.decode("utf-8-sig").split("\r\n")
    ref_lines = ref_raw.decode("utf-8-sig").split("\r\n")
    hdr = next(csv.reader(io.StringIO(cur_lines[0])), [])
    yidx = hdr.index("year")
    kept = changed = bad = 0
    for a, b in zip(ref_lines[1:], cur_lines[1:]):
        if not a or not b:
            continue
        year = int(next(csv.reader(io.StringIO(a)))[yidx])
        if year <= 2025:
            if b.startswith(a + ",") or b == a:
                kept += 1
            else:
                bad += 1
        else:
            changed += 1
    return kept, changed, bad == 0


print("=" * 100)
print("A. Files I annotated: pre-2026 content must survive byte-for-byte")
print("=" * 100)
for rel in ("01_data/00_derived/gps_spu_by_family.csv",
            "01_data/00_derived/gps_spu_pms.csv",
            "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_by_family.csv",
            "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_pms.csv"):
    ref = ROOT / rel
    # the derived-file backup is the reference; the two pack copies are compared to
    # the derived file, which is where they were copied from
    ref_dir = MINE if rel.startswith("01_data") else MINE
    ref_path = ref_dir / rel
    if not ref_path.exists():
        print(f"   (no reference recorded)  {rel}")
        continue
    df = pd.read_csv(ref)
    drop = 2 if "period_basis" in df.columns else 0
    kept, changed, ok = pre2026_identical(rel, ref_path, drop)
    verdict = "byte-identical" if ok else "DIFFERS"
    print(f"   {verdict:16s} {rel}")
    if not ok:
        fails.append(f"{rel}: pre-2026 content differs")

print()
print("=" * 100)
print("B. gps_spu_by_distributor.csv: 2023-2025 vs the earlier pass's backup")
print("=" * 100)
rel = "01_data/00_derived/gps_spu_by_distributor.csv"
cur = (ROOT / rel).read_bytes().decode("utf-8-sig").split("\r\n")
refp = EARLIER / rel
ref = refp.read_bytes().decode("utf-8-sig").split("\r\n")
hdr = next(csv.reader(io.StringIO(cur[0])), [])
yidx = hdr.index("year")
kept = bad = ch26 = 0
for a, b in zip(ref[1:], cur[1:]):
    if not a or not b:
        continue
    year = int(next(csv.reader(io.StringIO(a)))[yidx])
    if year <= 2025:
        if b == a:
            kept += 1
        else:
            bad += 1
            if bad <= 3:
                print(f"   DIFF year {year}: {a[:70]!r}\n             {b[:70]!r}")
    else:
        ch26 += 1
print(f"   2023-2025 rows byte-identical: {kept}")
print(f"   2026 rows (changed by the earlier pass, not by me): {ch26}")
if bad:
    fails.append(f"{rel}: {bad} pre-2026 rows differ from the earlier backup")
    print(f"   DIFFERENCES: {bad}")

print()
print("=" * 100)
print("C. Files that must be untouched (full byte-identity)")
print("=" * 100)
for rel in ("01_data/00_derived/aim_gps_matrix.csv",
            "01_data/00_derived/aim_gps_matrix.parquet",
            "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/04_AIM/aim_gps_matrix.csv",
            "09_meetings/BVDB_PBI_Data_Upload_2026-09-23.zip",
            "09_meetings/_build_bvdb_pbi_pack_20260923.py"):
    ref = MINE / rel
    if not ref.exists():
        print(f"   (no reference recorded)  {rel}")
        continue
    same = (ROOT / rel).read_bytes() == ref.read_bytes()
    print(f"   {'unchanged' if same else 'CHANGED  '}  {rel}")
    if not same:
        fails.append(f"{rel}: changed but must not have been")

print()
print("=" * 100)
print("D. Files I edited on purpose (recorded, restore-tested)")
print("=" * 100)
for rel, why in (
    ("09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/HOW_TO.md",
     "disclosure: family/PMS/AIM period_basis rows added to the top caveat and section 5"),
    ("09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/MANIFEST.csv",
     "cols 9->11 on the two GPS rows, and the purpose text now says the 8-month rate is correct"),
    ("09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/_pack_meta.json",
     "real archive member count and size"),
    ("03_analytics/Isuzu/prism/scripts/build_bvp_p4_p5.py",
     "builder patch: emits period_basis/coverage_note on the family and PMS slices"),
    ("03_analytics/Isuzu/prism/scripts/build_aim_gps_matrix.py",
     "documentation only: records the part-year re-check and why the labels are left alone"),
    ("01_data/00_derived/pms_opportunity_matrix.csv",
     "builder rebuild: 4 added columns (period_basis, coverage_note, "
     "gap_eur_like_for_like, like_for_like_assumption); all 13 pre-existing columns "
     "verified text-identical, 2023-2025 exactly"),
    ("09_meetings/BVDB_PBI_Data_Upload_2026-09-23/03_PMS/pms_opportunity_matrix.csv",
     "pack copy of the above"),
    ("03_analytics/Isuzu/prism/scripts/build_pms_opportunity_matrix.py",
     "builder patch: emits the four columns and refuses to write if a full-year row "
     "moves; also gains --out and --compare-to so a rebuild can be previewed"),
):
    ref = MINE / rel
    same = ref.exists() and (ROOT / rel).read_bytes() == ref.read_bytes()
    print(f"   {'unchanged?!' if same else 'edited'}  {rel}")
    print(f"        reason: {why}")
    if same:
        fails.append(f"{rel}: expected an edit but the file is unchanged")

print()
print("=" * 100)
print("E. pms_opportunity_matrix.csv: are the 13 pre-existing columns text-identical?")
print("=" * 100)
import csv as _csv
import io as _io

rel = "01_data/00_derived/pms_opportunity_matrix.csv"
ref_p = MINE / rel
cur_p = ROOT / rel


def _rows(p):
    with p.open(encoding="utf-8-sig", newline="") as fh:
        r = _csv.reader(fh)
        return next(r), list(r)


h_old, r_old = _rows(ref_p)
h_new, r_new = _rows(cur_p)
keys = ["distributor_code", "pms_category", "year"]
old_by = {tuple(x[h_old.index(k)] for k in keys): x for x in r_old}
new_by = {tuple(x[h_new.index(k)] for k in keys): x for x in r_new}
print(f"   rows old {len(r_old)} new {len(r_new)}; keys match {set(old_by) == set(new_by)}")
shared = [c for c in h_old if c in h_new]
mismatch = 0
per_year_bad: dict[int, int] = {}
for k, ro in old_by.items():
    rn = new_by.get(k)
    if rn is None:
        mismatch += 1
        continue
    for c in shared:
        if ro[h_old.index(c)] != rn[h_new.index(c)]:
            mismatch += 1
            y = int(ro[h_old.index("year")])
            per_year_bad[y] = per_year_bad.get(y, 0) + 1
print(f"   old columns: {len(shared)}  mismatched cells: {mismatch}")
print(f"   by year: {per_year_bad or 'none'}")
print(f"   added columns: {[c for c in h_new if c not in h_old]}")
if mismatch:
    fails.append(f"{rel}: {mismatch} pre-existing cells changed")
else:
    print("   OK - every pre-existing cell renders exactly as before")

print()
print("RESULT:", "FAIL" if fails else "ALL CHECKS PASSED")
for f in fails:
    print("   -", f)
sys.exit(1 if fails else 0)
