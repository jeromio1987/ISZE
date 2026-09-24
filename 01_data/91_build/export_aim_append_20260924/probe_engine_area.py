# -*- coding: utf-8 -*-
"""Read-only: inspect the Engine > Cylinder Head area and remaining truncated PNs."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}


def mp(r):
    l1 = (r.get("aim_l1") or "").strip()
    l2 = (r.get("aim_l2") or "").strip()
    l3 = (r.get("aim_l3") or "").strip()
    f1 = (r.get("aim_l1_fixed") or "").strip()
    f2 = (r.get("aim_l2_fixed") or "").strip()
    if f1 not in PH:
        l1 = f1
    if f2 not in PH:
        l2 = f2
    return l1, l2, l3


rows = []
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)

print("=== all master L3 under Engine > Cylinder Head ===")
print(Counter(mp(r)[2] for r in rows if mp(r)[:2] == ("Engine", "Cylinder Head")).most_common())

print("\n=== master rows where description contains 'CYL HD' or 'HEAD ASM' ===")
seq = Counter()
for r in rows:
    d = (r.get("description") or "").upper()
    if "CYL HD" in d or "HEAD ASM" in d or "CYLINDER HEAD" in d:
        seq[(r.get("description"), mp(r))] += 1
for k, n in seq.most_common(30):
    print(f"  {k}  x{n}")

print("\n=== what L3s exist under Engine (master), by count ===")
print(Counter(mp(r)[1:3] for r in rows if mp(r)[0] == "Engine").most_common(30))

print("\n=== the 3 truncated PNs ===")
want = {"7552413240", "7552973320", "8982703783", "8981391311", "7552325061"}
for r in rows:
    if r["part_number"] in want:
        print(r["part_number"], "|", r["description"], "|", mp(r), "| fig", r.get("fig_key"))

# per description master path evidence for those
for desc in ("HARNESS; RR COMB LAMP", "INJECTOR ASM; DEF DCM", "CLAMP; BATTERY"):
    print(f"\n=== master rows with description {desc!r} ===")
    c = Counter(mp(r) for r in rows if (r.get("description") or "") == desc)
    for k, n in c.most_common(10):
        print("  ", k, "x", n)
    print("  figure keys:", Counter(r.get("fig_key") for r in rows if (r.get("description") or "") == desc).most_common(8))
