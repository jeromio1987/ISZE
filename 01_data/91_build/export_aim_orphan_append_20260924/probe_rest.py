# -*- coding: utf-8 -*-
"""Detail dump for the 11 orphans that no route settled, plus the figure-key evidence
classified.csv recorded for them. Read-only."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_orphan_append_20260924"

PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}

probe = json.loads((OUT / "evidence_43_probe.json").read_text(encoding="utf-8"))
rest = [r for r in probe if not r["route_a_triple"]]
print("rows with no EPC figure-name answer:", len(rest))

# master fig_key -> path, only where unanimous
found = Counter()
fig_paths = defaultdict(list)
with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        l1 = (r.get("aim_l1_fixed") or "").strip() or (r.get("aim_l1") or "").strip()
        l2 = (r.get("aim_l2_fixed") or "").strip() or (r.get("aim_l2") or "").strip()
        l3 = (r.get("aim_l3") or "").strip()
        if l1 in PH or l2 in PH or l3 in PH:
            continue
        fk = (r.get("fig_key") or "").strip()
        if fk:
            fig_paths[fk].append((l1, l2, l3))

for r in rest:
    fk = r["fig_key"]
    ps = fig_paths.get(fk, [])
    c = Counter(ps)
    top = c.most_common(3)
    print()
    print(f"{r['pn']}  {r['description']}")
    print(f"   fig {fk}  abc {r['abc']}  epc status note: {r['classified_note']!r}")
    print(f"   classified.csv said: {r['classified_l1']} > {r['classified_l2']} > {r['classified_l3']}"
          f"   [{r['classified_source']}]")
    print(f"   master parts on that figure key: {len(ps)}  distinct paths: {len(c)}")
    for p, n in top:
        print(f"      {n:>4}  {p}")
    print("   description pool on the master:", r["desc_pool"])
