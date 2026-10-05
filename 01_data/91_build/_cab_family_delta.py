# -*- coding: utf-8 -*-
"""Before/after family counts, from the backup and the live master. Read only."""
import csv
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
BAK = D / "aim_master_v2.csv.bak_pre_cab_class_20260924_191700"
LIVE = D / "aim_master_v2.csv"


def counts(p: Path) -> tuple[Counter, int, dict[str, int]]:
    with p.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    hdr, data = rows[0], rows[1:]
    i = {c: n for n, c in enumerate(hdr)}
    l1 = Counter(r[i["aim_l1"]] for r in data)
    cabasm = Counter()
    for r in data:
        if (r[i["aim_l1"]], r[i["aim_l2"]], r[i["aim_l3"]]) == (
                "Accident & Body", "Complete Assembly", "Cab Assembly"):
            cabasm[r[0]] = 1
    return l1, len(data), cabasm


b_l1, b_n, b_cab = counts(BAK)
a_l1, a_n, a_cab = counts(LIVE)

print(f"rows: {b_n:,} -> {a_n:,}")
for k in ["Accident & Body", "Cabin Interior", "Unknown", "Unknown Review", ""]:
    print(f"  {k or '(blank)':<18} {b_l1[k]:>7,} -> {a_l1[k]:>7,}   delta {a_l1[k] - b_l1[k]:+,}")
print()
print("families before:", len([k for k in b_l1 if k]), " after:", len([k for k in a_l1 if k]))
print("new family value present:", sorted(set(a_l1) - set(b_l1)))
print("families gone:", sorted(set(b_l1) - set(a_l1)))
print()
print("rows on the new class before:", len(b_cab), " after:", len(a_cab))
