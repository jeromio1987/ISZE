# -*- coding: utf-8 -*-
"""Read-only: see exactly how a previously-appended row looks, so the new append mirrors it."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"

want = {}
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    rd = csv.DictReader(fh)
    hdr = rd.fieldnames
    n = 0
    for r in rd:
        n += 1
        src = r.get("aim_source") or ""
        if "eq_session_20260919" in src and "eq1" not in want:
            want["eq1"] = r
        if "gap_auto_residual_20260919" in src and "gap1" not in want:
            want["gap1"] = r
        if "4signal_agree3" in src and "s1" not in want:
            want["s1"] = r
        if (r.get("description") or "") == "ENGINE ASM" and "eng1" not in want:
            want["eng1"] = r
        if len(want) == 4:
            break
print("total data rows:", n)
for tag, r in want.items():
    print("\n" + "=" * 90)
    print(tag, r["part_number"], "|", r["description"])
    for c in hdr:
        print(f"   {c:<24} = {r.get(c)!r}")
