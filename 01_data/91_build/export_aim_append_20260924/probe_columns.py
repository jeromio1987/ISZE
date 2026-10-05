# -*- coding: utf-8 -*-
"""Read-only: understand the column convention on aim_master_v2.csv."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}

m = {}
with (D / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        m[r["part_number"]] = r
print("master rows:", len(m))

c_fixed = Counter()
c_plain = Counter()
n_fixed = n_plain = 0
for r in m.values():
    f1 = (r.get("aim_l1_fixed") or "").strip()
    p1 = (r.get("aim_l1") or "").strip()
    if f1 not in PH:
        n_fixed += 1
        c_fixed[f1] += 1
    if p1 not in PH:
        n_plain += 1
        c_plain[p1] += 1
print(f"\naim_l1_fixed usable rows: {n_fixed}")
print("top aim_l1_fixed:", c_fixed.most_common(25))
print(f"\naim_l1 plain usable rows: {n_plain}")
print("top aim_l1 plain:", c_plain.most_common(25))

print("\n--- sample master rows ---")
for pn in ("8975293220", "8981560940", "7552348290"):
    r = m.get(pn)
    if not r:
        print(pn, "NOT ON MASTER")
        continue
    print(
        pn,
        "| desc:", r["description"],
        "| aim_l1:", repr(r["aim_l1"]),
        "| aim_l2:", repr(r["aim_l2"]),
        "| aim_l3:", repr(r["aim_l3"]),
        "| l1f:", repr(r["aim_l1_fixed"]),
        "| l2f:", repr(r["aim_l2_fixed"]),
        "| src:", repr(r["aim_source"]),
        "| changed:", repr(r["aim_changed"]),
        "| has_aim:", repr(r["has_aim"]),
    )

print("\n--- what has_aim is on rows with aim_l1_fixed == 'Unknown' ---")
u = [r for r in m.values() if (r.get("aim_l1_fixed") or "").strip().startswith("Unknown")]
print("count:", len(u))
print("aim_source:", Counter((r.get("aim_source") or "") for r in u).most_common(6))
print("aim_changed:", Counter((r.get("aim_changed") or "") for r in u).most_common(6))
print("has_aim:", Counter((r.get("has_aim") or "") for r in u).most_common(6))
print("aim_l1:", Counter((r.get("aim_l1") or "") for r in u).most_common(6))

print("\n--- rows already stamped by prior applies ---")
for stamp in ("eq_session_20260919", "gap_auto_residual_20260919", "4signal_agree3",
              "4signal_agree2"):
    n = sum(1 for r in m.values() if stamp in (r.get("aim_source") or ""))
    print(f"{stamp}: {n} rows")
