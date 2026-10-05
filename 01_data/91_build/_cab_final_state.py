# -*- coding: utf-8 -*-
"""Final state confirmation after the cab-class work. Read only."""
import hashlib
import os
import time
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")


def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


print("=== written this session ===")
EXPECT = {
    D / "aim_master_v2.csv":
        "8add555669baf1f75b3bb2d203d58960fff7596b26ec5d8645d7ffee45604acf",
    D / "aim_pn_classification_20260920.csv":
        "092e981518efc5440ac10972ed2312dcd493c851e39d3d5c278f2ad5d0c27a60",
}
for p, exp in EXPECT.items():
    d = h(p)
    print(f"  {p.name:<46} {p.stat().st_size:>12,}  {d[:16]}  match={d == exp}")

print()
print("=== must NOT have moved ===")
REF = {
    D / "AIM_Master_PN_Categories_Figkey_20260921.csv": "bed9c4a266aa2851",
    D / "AIM_Master_PN_Categories_Figkey_20260921.xlsx": "8376812d5702a89f",
    D / "OPEN_AIM_Master_PN_Categories_Figkey_20260921.cmd": "c182b0e980d62fc5",
}
for p, exp in REF.items():
    d = h(p)[:16]
    print(f"  {p.name:<46} {p.stat().st_size:>12,}  {d}  match={d == exp}")

print()
print("=== rebuilt pair ===")
for n in ["AIM_Master_PN_Categories_Figkey_20260924.csv",
          "AIM_Master_PN_Categories_Figkey_20260924.xlsx",
          "OPEN_AIM_Master_PN_Categories_Figkey_20260924.cmd"]:
    p = D / n
    print(f"  {n:<46} {p.stat().st_size:>12,}  {h(p)[:16]}")

print()
print("=== documents ===")
for p in [ROOT / "00_docs" / "agent" / "DELEGATOR_BOARD.md",
          ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" /
          "CAB_CLASS_REPORT_20260924.md"]:
    st = p.stat()
    print(f"  {p.name:<46} {st.st_size:>12,}  "
          f"{time.strftime('%H:%M:%S', time.localtime(st.st_mtime))}")

board = (ROOT / "00_docs" / "agent" / "DELEGATOR_BOARD.md").read_text(encoding="utf-8")
print()
print(f"board: replacement={board.count(chr(0xFFFD))} "
      f"em-dash={board.count(chr(0x2014))} euro={board.count(chr(0x20AC))} "
      f"rows={sum(1 for l in board.split(chr(10)) if l.strip().startswith('|'))}")
