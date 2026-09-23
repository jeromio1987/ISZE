"""Refresh the single pack metadata copy from the derived meta, safely.

Uses temp-file + os.replace because some files in this tree reject a truncating
open with OSError 22. Copies ONLY 12_nseries_band_evolution.meta.json.
"""
import os
import shutil
import hashlib
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
PACK = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920")

src = DER / "nseries_tonnage_evolution.meta.json"
dst = PACK / "data_nseries_bands" / "12_nseries_band_evolution.meta.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


before = sha(dst)
print(f"before: pack {before}")
print(f"        derived {sha(src)}")
print(f"        identical before: {before == sha(src)}")

tmp = dst.with_suffix(".meta.json.tmp_refresh")
shutil.copy2(src, tmp)
os.replace(tmp, dst)

print(f"after : pack {sha(dst)}")
print(f"        derived {sha(src)}")
print(f"        identical after: {sha(dst) == sha(src)}")

files = [p for p in PACK.rglob("*") if p.is_file()]
print(f"pack file count: {len(files)}")
