#!/usr/bin/env python3
"""Prove the corrected zip is a faithful copy of the folder right now, member by member."""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PACK = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23"
ZIP = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23_corrected_20260922.zip"

folder = {p.relative_to(PACK).as_posix(): p for p in PACK.rglob("*") if p.is_file()}
with zipfile.ZipFile(ZIP) as zf:
    zmembers = {i.filename: zf.read(i.filename) for i in zf.infolist()}

print(f"folder files={len(folder)}  zip members={len(zmembers)}")
missing = sorted(set(folder) - set(zmembers))
extra = sorted(set(zmembers) - set(folder))
print("in folder but NOT in zip:", missing or "none")
print("in zip but NOT in folder:", extra or "none")

bad = []
for rel, p in sorted(folder.items()):
    if rel not in zmembers:
        continue
    on_disk = p.read_bytes()
    if on_disk != zmembers[rel]:
        bad.append((rel, len(on_disk), len(zmembers[rel])))
print("members whose bytes differ from the folder:", bad or "none")

print("\nper-member sha256 of the files that changed in this pass:")
for rel in ("00_START_HERE/HOW_TO.md", "00_START_HERE/MANIFEST.csv",
            "00_START_HERE/_pack_meta.json", "02_GPS/gps_spu_by_distributor.csv",
            "02_GPS/gps_spu_by_family.csv", "02_GPS/gps_spu_pms.csv"):
    if rel in zmembers:
        print(f"   {rel:40s} {hashlib.sha256(zmembers[rel]).hexdigest()[:32]} "
              f"{len(zmembers[rel]):>7} bytes")
sys.exit(1 if (missing or extra or bad) else 0)
