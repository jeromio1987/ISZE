# -*- coding: utf-8 -*-
"""Clean census of the cab rows left in place. Read only."""
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
m = pd.read_csv(r"01_data\00_derived\aim_master_v2.csv", dtype=str, keep_default_na=False)
d = m.description.str.upper()
PLACED = ["7551847570", "7552044930", "7552612100", "7552625790", "7552824860",
          "7553142130", "7551847580", "7552060250", "7552349740", "7552427800",
          "7552641820", "7552650510", "7552825890", "8974877720", "8980115942",
          "8980115951", "8980425220", "8980554611", "8980554621", "7553266960"]

cab = m[d.str.contains(r"\bCAB\b", regex=True)].copy()
left = cab[~cab.part_number.isin(PLACED)].copy()
for c in ("aim_l1", "aim_l2", "aim_l3"):
    left[c] = left[c].str.strip().replace("", "(blank)")

print("standalone CAB today          :", len(cab))
print("of which placed (19 + added 1):", len(cab[cab.part_number.isin(PLACED)]))
print("left in place                 :", len(left))
print()
g = left.groupby(["aim_l1", "aim_l2", "aim_l3"]).size().sort_values(ascending=False)
print(g.to_string())
print()
print("sum:", int(g.sum()))
print()
print("description families among the 264 left:")
desc = left.description.str.upper().str.split(r"[;,()]").str[0].str.strip()
print(desc.value_counts().head(20).to_string())
