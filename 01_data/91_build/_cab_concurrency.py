# -*- coding: utf-8 -*-
"""Concurrency and drift check after the cab-class writes. Read only."""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

EXPECT = {
    "aim_master_v2.csv":
        (28612879, "8add555669baf1f75b3bb2d203d58960fff7596b26ec5d8645d7ffee45604acf"),
    "aim_pn_classification_20260920.csv":
        (None, None),
    "AIM_Master_PN_Categories_Figkey_20260924.csv":
        (None, None),
    "AIM_Master_PN_Categories_Figkey_20260921.csv":
        (13093140, "bed9c4a266aa2851e0b1c5d7e2d1f0a5b0d1f9e2a5b0d1f9e2a5b0d1f9e2a5b0"),
}

for name, (sz, h) in EXPECT.items():
    blob = (D / name).read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    flag = ""
    if sz is not None and len(blob) != sz:
        flag = "  <-- SIZE MISMATCH"
    print(f"{len(blob):>12}  {digest[:24]}  {name}{flag}")

print()
master = (D / "aim_master_v2.csv").read_bytes()
ok = hashlib.sha256(master).hexdigest() == EXPECT["aim_master_v2.csv"][1]
print("master unchanged since the write :", ok)

pair21 = (D / "AIM_Master_PN_Categories_Figkey_20260921.csv").read_bytes()
print("2026-09-21 csv bytes             :", len(pair21), "(was 13,093,140)")
