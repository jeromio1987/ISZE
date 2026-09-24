# -*- coding: utf-8 -*-
"""Read-only evidence probe for the 44 PNs not on aim_master_v2.csv."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
T = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
A = ROOT / "01_data" / "91_build" / "_tmp_apply_export_pr00_20260924"

not_in_master = [
    l.strip() for l in (A / "carried_out_not_in_master.txt").read_text().splitlines() if l.strip()
]
print(f"not_in_master: {len(not_in_master)}")

# ---- tierA_audited rows for the 44 ----
tier = {}
with (T / "tierA_audited.csv").open(encoding="utf-8-sig", newline="") as fh:
    rd = csv.DictReader(fh)
    cols = rd.fieldnames
    print("tierA cols:", cols)
    for r in rd:
        tier.setdefault(r["pn"], []).append(r)

print("\n--- tierA rows for the 44 ---")
missing = []
for pn in not_in_master:
    rows = tier.get(pn)
    if not rows:
        missing.append(pn)
        print(f"{pn}  <no tierA row>")
        continue
    for r in rows:
        print(
            f"{pn} | {r.get('Description')} | EUR {r.get('list_eur')} | fig={r.get('fig_key')} "
            f"| d_l1={r.get('d_l1')} | tierA={r.get('tierA')} | undef={r.get('undefendable')} "
            f"| conv={r.get('convention')} | on_master={r.get('on_master')}"
        )
print("no tierA row for:", missing)

# ---- queue_final_tiered ----
q = {}
with (T / "queue_final_tiered.csv").open(encoding="utf-8-sig", newline="") as fh:
    rd = csv.DictReader(fh)
    print("\nqueue cols:", rd.fieldnames)
    for r in rd:
        q.setdefault(r.get("pn") or r.get("part_number"), []).append(r)
print("queue unique pns:", len(q))
print("\n--- queue rows for the 44 ---")
for pn in not_in_master:
    rows = q.get(pn)
    if not rows:
        print(f"{pn}  <no queue row>")
        continue
    for r in rows:
        print(f"{pn} | {r}")
