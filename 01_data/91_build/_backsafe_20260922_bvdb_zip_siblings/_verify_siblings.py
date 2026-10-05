#!/usr/bin/env python3
"""Task 3 evidence: pre-2026 integrity, schema, and what is inside the zip.

The strongest available proof for the two spliced files: **strip the two new
columns out of the new file and the result must be byte-identical to the backup,
including CRLF endings, the BOM decision and the trailing newline.** If a single
pre-existing byte anywhere had drifted, that round-trip would not match.
"""
from __future__ import annotations

import csv
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BAK = ROOT / "01_data" / "91_build" / "_backsafe_20260922_bvdb_zip_siblings" / "original"
ZIP = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip"

NEW_COLS = ("period_basis", "coverage_note")
fails: list[str] = []


def strip_added_columns(path: Path) -> tuple[bytes, int]:
    """Rebuild the file as it was before the two columns were added."""
    raw = path.read_bytes()
    bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw.decode("utf-8-sig")
    ending = "\r\n" if text.endswith("\r\n") else ("\n" if text.endswith("\n") else "")
    body = text[: len(text) - len(ending)] if ending else text
    rows = list(csv.reader(io.StringIO(body)))
    out = io.StringIO()
    w = csv.writer(out, lineterminator=ending)
    for row in rows:
        w.writerow(row[:-2])
    text2 = out.getvalue()
    if ending and not text2.endswith(ending):
        text2 += ending
    return (b"\xef\xbb\xbf" if bom else b"") + text2.encode("utf-8"), len(rows) - 1


print("=" * 100)
print("1. Round-trip: strip the two new columns -> must equal the backup byte-for-byte")
print("=" * 100)
for rel in ("01_data/00_derived/gps_spu_by_family.csv",
            "01_data/00_derived/gps_spu_pms.csv"):
    new_p, old_p = ROOT / rel, BAK / rel
    rebuilt, n = strip_added_columns(new_p)
    original = old_p.read_bytes()
    same = rebuilt == original
    print(f"{rel}")
    print(f"   rows={n}  rebuilt_bytes={len(rebuilt)}  backup_bytes={len(original)}")
    print(f"   BYTE-IDENTICAL to the backup: {same}")
    if not same:
        fails.append(f"{rel}: strip-round-trip differs from the backup")
        for i, (a, b) in enumerate(zip(rebuilt, original)):
            if a != b:
                print(f"   first difference at byte {i}: {rebuilt[i-40:i+40]!r} "
                      f"vs {original[i-40:i+40]!r}")
                break

print()
print("=" * 100)
print("2. Files I did not touch must be byte-identical to their backup, in full")
print("=" * 100)
for rel in ("01_data/00_derived/aim_gps_matrix.csv",
            "01_data/00_derived/aim_gps_matrix.parquet",
            "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/04_AIM/aim_gps_matrix.csv",
            "01_data/00_derived/gps_spu_by_distributor.csv",
            "09_meetings/_build_bvdb_pbi_pack_20260923.py"):
    new_p, old_p = ROOT / rel, BAK / rel
    if not old_p.exists():
        print(f"   (not in the backup set)  {rel}")
        continue
    same = new_p.read_bytes() == old_p.read_bytes()
    print(f"   {'UNCHANGED' if same else 'CHANGED  '}  {rel}")
    if not same:
        fails.append(f"{rel}: changed but should not have been")

print()
print("=" * 100)
print("3. The corrected files: schema and per-year period coverage")
print("=" * 100)
for rel in ("01_data/00_derived/gps_spu_by_family.csv",
            "01_data/00_derived/gps_spu_pms.csv"):
    df = pd.read_csv(ROOT / rel)
    print(f"{rel}\n   cols={len(df.columns)} rows={len(df)}")
    print(f"   header={list(df.columns)}")
    print(df.groupby(["year", "period_basis"]).size().to_string())

print()
print("=" * 100)
print("4. What is actually INSIDE the corrected zip (read from the archive, not the folder)")
print("=" * 100)
with zipfile.ZipFile(ZIP) as zf:
    print(f"members={len(zf.namelist())}")
    for member in ("02_GPS/gps_spu_by_distributor.csv", "02_GPS/gps_spu_by_family.csv",
                   "02_GPS/gps_spu_pms.csv", "04_AIM/aim_gps_matrix.csv",
                   "00_START_HERE/MANIFEST.csv", "00_START_HERE/HOW_TO.md"):
        raw = zf.read(member)
        if member.endswith(".md"):
            txt = raw.decode("utf-8", "replace")
            print(f"   {member:42s} bytes={len(raw):>7}  part-year caveat present="
                  f"{'part year' in txt.lower()}  non-parts note present={'178,453' in txt}")
            continue
        df = pd.read_csv(io.BytesIO(raw))
        print(f"   {member:42s} bytes={len(raw):>7} rows={len(df):>5} cols={len(df.columns)}")
        if "period_basis" in df.columns:
            parts = df.groupby(["year", "period_basis"]).size().to_dict()
            print(f"       (year,basis): {dict(sorted(parts.items()))}")
        if "spu_eur" in df.columns:
            y26 = df[df["year"] == 2026]
            print(f"       2026 spu_eur non-null {int(y26['spu_eur'].notna().sum())}/{len(y26)} "
                  f"range {y26['spu_eur'].min():.2f}-{y26['spu_eur'].max():.2f} "
                  f"-> kept, it is a correct part-year rate")
        if "quadrant_label" in df.columns:
            y26 = df[df["year"] == 2026]
            print(f"       2026 quadrant_label: {dict(y26['quadrant_label'].value_counts())} "
                  f"-> unchanged, see the build note on units")

print()
print("RESULT:", "FAIL" if fails else "ALL CHECKS PASSED")
for f in fails:
    print("   -", f)
sys.exit(1 if fails else 0)
