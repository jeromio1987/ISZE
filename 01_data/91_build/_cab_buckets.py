# -*- coding: utf-8 -*-
"""Measure the exact buckets for the report. Read only."""
import re
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
m = pd.read_csv(r"01_data\00_derived\aim_master_v2.csv", dtype=str, keep_default_na=False)
d = m.description.str.upper()
cab = m[d.str.contains(r"\bCAB\b", regex=True)]
print("rows with the standalone word CAB :", len(cab))

placed = ["7551847570", "7552044930", "7552612100", "7552625790", "7552824860",
          "7553142130", "7551847580", "7552060250", "7552349740", "7552427800",
          "7552641820", "7552650510", "7552825890", "8974877720", "8980115942",
          "8980115951", "8980425220", "8980554611", "8980554621"]
left = cab[~cab.part_number.isin(placed)]
print("placed from that set              :", len(cab[cab.part_number.isin(placed)]))
print("left in place                     :", len(left))
print()
print("=== what is left, grouped ===")
print(left.groupby(["aim_l1", "aim_l2", "aim_l3"]).size()
      .sort_values(ascending=False).to_string())
print()
print("=== the categories I claimed, measured ===")


def n(pat: str) -> int:
    return int(left.description.str.upper().str.contains(pat, regex=True).sum())


groups = {
    "cab MTG/FRAME/RR MTG brackets, members, bolts, washers, rubbers, plates":
        r"CAB MTG|CAB RR MTG|CAB FRAME|CUSHION RUBBER|MTG,CAB|CAB BRKT|CAB EARTH|MTG RAIL",
    "cab suspension rubbers/bushes (same families, other wording)":
        r"RUBBER; MTG,CAB|BUSHING; RUBBER,CAB|CAB MTG RUBBER",
    "cab harnesses and connectors": r"HARNESS; CAB",
    "cab locks / hinges / tilt stays / rods / pins": r"CAB LOCK|CAB TILT|CAB STAY|LOCK ASM; CAB|CAB SIDE UPR",
    "cab silencer and floor mats": r"SILENCER|MAT; FLOOR",
    "cab emblems and decals": r"EMBLEM|DECAL|PLATE; CAUTION",
    "cab doors, seals, fenders, assist grips, side sill": r"CAB SIDE|CAB BACK|FENDER TO CAB|SIDE SILL",
    "on the Unknown marker": r"^$",
}
covered = set()
for name, pat in groups.items():
    sub = left[left.description.str.upper().str.contains(pat, regex=True)]
    covered |= set(sub.index)
    print(f"{len(sub):>4}  {name}")
rest = left[~left.index.isin(covered)]
print(f"{len(rest):>4}  everything else")
print(rest.description.value_counts().to_string())
print()
print("check: total classified", len(left))
print()
print("=== the 'PANEL;' claim ===")
p = m[d.str.contains(r"^PANEL;", regex=True)]
print("master rows whose description starts 'PANEL;':", len(p))
print(p.groupby(["aim_l1", "aim_l2", "aim_l3"]).size().sort_values(ascending=False).head(6).to_string())
print()
print("=== Cabin Interior rows (for the report) ===")
print(len(m[m.aim_l1 == "Cabin Interior"]))
print("=== Accident & Body rows ===")
print(len(m[m.aim_l1 == "Accident & Body"]))
