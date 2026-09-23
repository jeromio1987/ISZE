#!/usr/bin/env python3
"""Copy the two corrected sibling files into the meeting pack, refresh the manifest,
and rebuild the corrected zip. Prints before/after for every file it touches."""
from __future__ import annotations

import hashlib
import json
import shutil
import time
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PACK = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23"
NEW_ZIP = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip"
ORIGINAL_ZIP = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23.zip"
HERE = Path(__file__).resolve().parent

PAIRS = [
    (DER / "gps_spu_by_family.csv", PACK / "02_GPS" / "gps_spu_by_family.csv"),
    (DER / "gps_spu_pms.csv", PACK / "02_GPS" / "gps_spu_pms.csv"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def replace_with_retry(tmp: Path, dst: Path) -> None:
    """os.replace can hit a transient Windows lock on these files. Retry, then
    fall back to a copy."""
    for attempt in range(6):
        try:
            tmp.replace(dst)
            return
        except PermissionError:
            time.sleep(0.4 * (attempt + 1))
    shutil.copyfile(tmp, dst)
    tmp.unlink(missing_ok=True)


def main() -> int:
    orig_sha_before = sha256(ORIGINAL_ZIP)
    orig_size_before = ORIGINAL_ZIP.stat().st_size

    for src, dst in PAIRS:
        src_bytes = src.read_bytes()
        if dst.is_file() and dst.read_bytes() == src_bytes:
            print(f"{dst.relative_to(ROOT)}  already identical, nothing to copy")
            continue
        before_cols = len(pd.read_csv(dst).columns)
        assert "period_basis" in pd.read_csv(src).columns, f"src missing period_basis: {src}"
        tmp = dst.with_suffix(".csv.tmp")
        shutil.copy2(src, tmp)
        replace_with_retry(tmp, dst)
        after_cols = len(pd.read_csv(dst).columns)
        print(f"{dst.relative_to(ROOT)}  cols {before_cols} -> {after_cols}  "
              f"sha256 {sha256(dst)[:16]}  bytes {dst.stat().st_size}")

    # manifest rows/cols/kb
    mp = PACK / "00_START_HERE" / "MANIFEST.csv"
    man = pd.read_csv(mp, encoding="utf-8-sig")
    for i, row in man.iterrows():
        f = PACK / str(row["file"])
        if not f.is_file():
            continue
        df = pd.read_csv(f, encoding="utf-8-sig")
        man.at[i, "rows"] = len(df)
        man.at[i, "cols"] = len(df.columns)
        man.at[i, "kb"] = round(f.stat().st_size / 1024, 1)
    tmp = mp.with_suffix(".csv.tmp")
    man.to_csv(tmp, index=False, encoding="utf-8-sig")
    # pandas does not quote fields containing a colon or a period, but it does quote
    # anything with a comma; the count/cols/kb columns are left exactly as written.
    tmp.replace(mp)
    print("MANIFEST.csv refreshed from the files on disk")

    # rebuild zip, then settle _pack_meta.json's self-referential size
    meta_p = PACK / "00_START_HERE" / "_pack_meta.json"
    n_folder = sum(1 for p in PACK.rglob("*") if p.is_file())
    used_kb = float(json.loads(meta_p.read_text(encoding="utf-8")).get("zip_kb", 0))
    members = 0
    size = 0
    for _ in range(6):
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        meta.update({"zip": str(NEW_ZIP), "zip_kb": used_kb, "files": n_folder,
                     "data_files_in_manifest": len(man), "archive_members": members or None})
        tmp = meta_p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        tmp.replace(meta_p)
        files = sorted(p for p in PACK.rglob("*") if p.is_file())
        tz = NEW_ZIP.with_suffix(".zip.tmp")
        with zipfile.ZipFile(tz, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, f.relative_to(PACK).as_posix())
        tz.replace(NEW_ZIP)
        with zipfile.ZipFile(NEW_ZIP) as zf:
            members = len(zf.namelist())
        size = NEW_ZIP.stat().st_size
        kb = round(size / 1024, 1)
        if kb == used_kb and meta.get("archive_members") == members:
            break
        used_kb = kb

    out = {
        "new_zip": str(NEW_ZIP),
        "new_zip_bytes": size,
        "new_zip_kb": round(size / 1024, 1),
        "new_zip_members": members,
        "new_zip_sha256": sha256(NEW_ZIP),
        "original_zip_bytes": orig_size_before,
        "original_zip_untouched": (orig_sha_before == sha256(ORIGINAL_ZIP)
                                   and orig_size_before == ORIGINAL_ZIP.stat().st_size),
    }
    log = HERE / "_zip_build_log.json"
    prev = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []
    prev.append(out)
    log.write_text(json.dumps(prev, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
