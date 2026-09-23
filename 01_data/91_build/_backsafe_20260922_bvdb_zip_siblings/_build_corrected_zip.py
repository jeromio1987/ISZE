#!/usr/bin/env python3
"""Build the CORRECTED BVDB hand-over zip as a NEW file. Never touches the original.

Why a new file: `BVDB_PBI_Data_Upload_2026-09-23.zip` is a dated hand-over artefact
whose members (19-column GPS file, 18 part-year capture percentages, HOW_TO.md with
no period disclosure) are known to be wrong. Overwriting it would erase the evidence
of what was built and when.

New name: BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip
  - sorts immediately after the original
  - says "corrected" so the difference is visible in the folder

Also refreshes MANIFEST.csv (rows / cols / kb recomputed from the files on disk) and
_pack_meta.json (real archive member count and real size) so no shipped count is stale.
The meta's own size figure is self-referential, so the archive is rebuilt until that
number is stable.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PACK = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23"
ORIGINAL_ZIP = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23.zip"
NEW_ZIP = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip"
HERE = Path(__file__).resolve().parent
LOG = HERE / "_zip_build_log.json"

# Member layout must match the archive being superseded. The file on disk
# (`BVDB_PBI_Data_Upload_2026-09-23.zip`, written 2026-09-22 20:10) stores members
# at the root with no wrapper folder; the earlier 17:11 build used a wrapper. A
# corrected hand-over should not change its own shape, so we match today's file.
ARCHIVE_ROOT: str | None = None


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def refresh_manifest() -> int:
    """Recompute rows / cols / kb for every data file the manifest lists."""
    mp = PACK / "00_START_HERE" / "MANIFEST.csv"
    man = pd.read_csv(mp, encoding="utf-8-sig")
    changed: list[str] = []
    for i, row in man.iterrows():
        f = PACK / str(row["file"])
        if not f.is_file():
            continue
        df = pd.read_csv(f, encoding="utf-8-sig")
        new_rows, new_cols = len(df), len(df.columns)
        new_kb = round(f.stat().st_size / 1024, 1)
        if (int(row["rows"]), int(row["cols"]), float(row["kb"])) != (new_rows, new_cols, new_kb):
            changed.append(f"{row['file']}: rows {row['rows']}->{new_rows} "
                           f"cols {row['cols']}->{new_cols} kb {row['kb']}->{new_kb}")
            man.at[i, "rows"] = new_rows
            man.at[i, "cols"] = new_cols
            man.at[i, "kb"] = new_kb
    # atomic replace: some files here refuse a truncating write
    tmp = mp.with_suffix(".csv.tmp")
    man.to_csv(tmp, index=False, encoding="utf-8-sig")
    tmp.replace(mp)
    return changed


def build_zip() -> tuple[int, int]:
    """Write the corrected archive. Returns (members, bytes)."""
    files = sorted(p for p in PACK.rglob("*") if p.is_file())
    tmp = NEW_ZIP.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            rel = f.relative_to(PACK).as_posix()
            zf.write(f, f"{ARCHIVE_ROOT}/{rel}" if ARCHIVE_ROOT else rel)
    tmp.replace(NEW_ZIP)
    with zipfile.ZipFile(NEW_ZIP) as zf:
        members = len(zf.namelist())
    return members, NEW_ZIP.stat().st_size


def main() -> int:
    assert ORIGINAL_ZIP.exists(), "original zip missing"
    orig_sha_before = sha256(ORIGINAL_ZIP)
    orig_bytes_before = ORIGINAL_ZIP.stat().st_size

    manifest_changes = refresh_manifest()
    print("MANIFEST.csv refreshed:")
    for c in manifest_changes:
        print("   ", c)
    if not manifest_changes:
        print("    (already correct)")

    meta_p = PACK / "00_START_HERE" / "_pack_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    n_data_files = len(pd.read_csv(PACK / "00_START_HERE" / "MANIFEST.csv", encoding="utf-8-sig"))
    n_folder_files = sum(1 for p in PACK.rglob("*") if p.is_file())

    used_kb = float(meta.get("zip_kb", 0))
    members = 0
    size = 0
    for attempt in range(6):
        meta.update({
            "as_of": "2026-09-22",
            "meeting": "2026-09-23",
            "folder": str(PACK),
            "zip": str(NEW_ZIP),
            "zip_kb": used_kb,
            "files": n_folder_files,
            "data_files_in_manifest": n_data_files,
            "archive_members": members or None,
            "exchanges": [
                "The original BVDB_PBI_Data_Upload_2026-09-23.zip is kept unchanged; "
                "this corrected archive is a new file beside it.",
            ],
            "corrected_2026_09_22": [
                "02_GPS/gps_spu_by_distributor.csv re-annotated: 21 columns including "
                "period_basis and coverage_note; 2026 capture % and traffic light left "
                "empty/unknown on part-year rows (a part-year numerator over a full-year "
                "target is not a capture rate).",
                "00_START_HERE/HOW_TO.md carries the part-year caveat and the non-parts "
                "exclusion note.",
            ],
            "excluded": meta.get("excluded", []),
        })
        # manifest.csv is itself a file in the folder; its bytes do not depend on meta
        tmp = meta_p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        tmp.replace(meta_p)
        members, size = build_zip()
        kb = round(size / 1024, 1)
        if kb == meta["zip_kb"] and meta["archive_members"] == members:
            break
        used_kb = kb

    orig_sha_after = sha256(ORIGINAL_ZIP)
    entries = {
        "new_zip": str(NEW_ZIP),
        "new_zip_bytes": size,
        "new_zip_kb": round(size / 1024, 1),
        "new_zip_sha256": sha256(NEW_ZIP),
        "new_zip_members": members,
        "new_zip_mtime": NEW_ZIP.stat().st_mtime,
        "folder_files": n_folder_files,
        "manifest_data_files": n_data_files,
        "original_zip": str(ORIGINAL_ZIP),
        "original_zip_bytes": orig_bytes_before,
        "original_zip_sha256_after_build": orig_sha_after,
        "original_zip_untouched": orig_sha_before == orig_sha_after and
                                 orig_bytes_before == ORIGINAL_ZIP.stat().st_size,
        "archive_member_layout": "flat (no wrapper folder), matching the original",
    }
    prev = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    if not isinstance(prev, list):
        prev = [prev]
    prev.append(entries)
    LOG.write_text(json.dumps(prev, indent=2), encoding="utf-8")
    print(json.dumps(entries, indent=2))
    print("original zip untouched:", entries["original_zip_untouched"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
