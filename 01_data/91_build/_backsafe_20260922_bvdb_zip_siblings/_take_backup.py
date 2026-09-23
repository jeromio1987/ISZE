#!/usr/bin/env python3
"""Byte-for-byte backup of everything the BVDB zip / sibling-file pass touches.

Writes into .\\original\\ preserving relative paths, plus _before.json with sha256.
Idempotent: refuses to overwrite an existing original unless --force.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = Path(__file__).resolve().parent
ORIG = HERE / "original"

SCOPE = [
    "01_data/00_derived/gps_spu_by_family.csv",
    "01_data/00_derived/gps_spu_pms.csv",
    "01_data/00_derived/aim_gps_matrix.csv",
    "01_data/00_derived/aim_gps_matrix.parquet",
    "01_data/00_derived/gps_spu_by_distributor.csv",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/_pack_meta.json",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/HOW_TO.md",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/00_START_HERE/MANIFEST.csv",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_by_family.csv",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/02_GPS/gps_spu_pms.csv",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23/04_AIM/aim_gps_matrix.csv",
    "09_meetings/BVDB_PBI_Data_Upload_2026-09-23.zip",
    "09_meetings/_build_bvdb_pbi_pack_20260923.py",
    "03_analytics/Isuzu/prism/scripts/build_bvp_p4_p5.py",
    "03_analytics/Isuzu/prism/scripts/build_aim_gps_matrix.py",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    force = "--force" in sys.argv
    ORIG.mkdir(parents=True, exist_ok=True)
    before: dict[str, dict] = {}
    missing: list[str] = []
    for rel in SCOPE:
        src = ROOT / rel
        if not src.is_file():
            missing.append(rel)
            continue
        dst = ORIG / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and not force:
            print(f"  keep (exists)  {rel}")
        else:
            shutil.copy2(src, dst)
            print(f"  copied         {rel}")
        before[rel] = {
            "sha256_before": sha256(src),
            "sha256_original_copy": sha256(dst),
            "bytes": src.stat().st_size,
            "mtime": src.stat().st_mtime,
        }
    (HERE / "_before.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
    if missing:
        print("MISSING (not backed up):", missing)
    ok = all(v["sha256_before"] == v["sha256_original_copy"] for v in before.values())
    print("backup copies verified identical:", ok)
    print("files backed up:", len(before))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
