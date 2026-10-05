# -*- coding: utf-8 -*-
"""Second, wider read-only probe on the 11 orphans no route settled.

Checks (i) whether the master carries anything at all on their figure keys, (ii) every
master description that starts with the same first token, and (iii) how many master rows
carry each candidate leaf. Nothing is written to the master."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"

PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}

TARGETS = {
    "5876102381": ("PAD KIT; CALIPER, DISC BRK, FR", "302-017"),
    "7553266960": ("CAB ASM; SERVICE,W/ELECT", "604-002"),
    "1884053370": ("LLC;200L TYPE E", "999-37K"),
    "7552598420": ("CIRCUIT; PRINTED,BATTERY", "810-795"),
    "7552126065": ("BRACKET; MOTOR BATTERY", "061-248"),
    "7553196060": ("GUIDE; HARNESS", "146-231"),
    "8943633640": ("CONNECTOR; HARNESS (2P FEMAIL)", "816-002"),
    "7552360101": ("BASE; FUSE CABLE", "061-309"),
    "7552347140": ("COVER; FUSE CABLE", "810-796"),
    "8980626220": ("CONNECTOR; HEAD LAMP", "816-090"),
    "8980680830": ("CONNECTOR; HEAD LAMP", "816-090"),
}

fig_no_rows = defaultdict(list)      # fig_no (as stored) -> [(key_no, path, pn)]
desc_exact = defaultdict(list)
pooll = defaultdict(list)
leaf_rows = Counter()
head_index = defaultdict(list)       # first token -> [(desc, path)]

with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        l1 = (r.get("aim_l1_fixed") or "").strip() or (r.get("aim_l1") or "").strip()
        l2 = (r.get("aim_l2_fixed") or "").strip() or (r.get("aim_l2") or "").strip()
        l3 = (r.get("aim_l3") or "").strip()
        path = (l1, l2, l3)
        ok = all(x and x not in PH for x in path)
        if ok:
            leaf_rows[path] += 1
        fn = (r.get("fig_no") or "").strip()
        kn = (r.get("key_no") or "").strip()
        if fn:
            fig_no_rows[fn].append((kn, path if ok else None, r.get("part_number")))
        d = (r.get("description") or "").strip()
        if d and ok:
            desc_exact[d].append(path)
            head_index[d.split(";")[0].split(",")[0].strip()].append((d, path))

for pn, (desc, fk) in TARGETS.items():
    fn, kn = fk.split("-")
    print("=" * 100)
    print(f"{pn}   {desc}   fig {fk}")
    rows = fig_no_rows.get(fn.zfill(3) if fn.isdigit() else fn, [])
    exact = [r for r in rows if r[0] == kn]
    print(f"   master rows on fig_no {fn}: {len(rows)}   with key_no {kn}: {len(exact)}")
    for k, p, p2 in exact[:6]:
        print(f"      {p2} key {k} -> {p}")
    print(f"   exact description '{desc}' on master: {len(desc_exact.get(desc, []))} rows"
          f" {Counter(desc_exact.get(desc, [])).most_common(3)}")
    head = desc.split(";")[0].strip()
    hd = Counter(p for d, p in head_index.get(head, []))
    print(f"   descriptions starting '{head}': {len(head_index.get(head, []))} rows, "
          f"top paths {hd.most_common(4)}")
    for d, p in head_index.get(head, [])[:8]:
        print(f"      {d!r} -> {p}")
