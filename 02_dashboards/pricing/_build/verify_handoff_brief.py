"""Check the handoff brief's own tables add up, so a reader is not the first person
to test its arithmetic.

Run: python 02_dashboards/pricing/_build/verify_handoff_brief.py
"""
from __future__ import annotations

import re
from pathlib import Path

B = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
         r"\HANDOFF_AIR_FILTER_AND_FOCUS_CUT.md")
text = B.read_text(encoding="utf-8")
lines = text.splitlines()
print(f"lines: {len(lines)}")
print("headings:")
for ln in lines:
    if ln.startswith("#"):
        print("  ", ln)
print()

num = re.compile(r"€([\d,]+\.\d\d)")


def eur(s: str) -> float:
    return float(s.replace(",", ""))


# 1. the 12-part misfile table must sum to its own stated total
block = text.split("| Part number | Description | 12M billed EUR |")[1].split("\n\n")[0]
rows = [ln for ln in block.splitlines() if ln.startswith("| ") and "€" in ln]
vals, total = [], None
for ln in rows:
    cells = [c.strip() for c in ln.strip("|").split("|")]
    if "Total" in cells[0] or cells[0] == "**Total**":
        total = eur(num.search(cells[-1]).group(1))
    else:
        vals.append((cells[0], eur(num.search(cells[-1]).group(1))))
print(f"misfile table: {len(vals)} part numbers")
print(f"  sum of rows      €{sum(v for _, v in vals):,.2f}")
print(f"  stated total     €{total:,.2f}")
print(f"  AGREES           {abs(sum(v for _, v in vals) - total) < 0.005}")

# 2. the two-tree table: catalogue total must equal the AIM spine split
m = re.search(r"\| Tree \| Placement \| Part numbers \| Billed EUR \| Step EUR \|\n"
              r"\|[-| ]+\|\n((?:\|.*\n)+)", text)
rows2 = [ln for ln in m.group(1).splitlines() if ln.strip()]
cat = aim = 0.0
catpn = aimpn = 0
for ln in rows2:
    cells = [c.strip() for c in ln.strip("|").split("|")]
    billed = eur(num.search(cells[3]).group(1))
    pn = int(cells[2])
    if cells[0] == "Catalogue":
        cat, catpn = billed, pn
    else:
        aim += billed
        aimpn += pn
print()
print(f"catalogue tree   €{cat:,.2f} on {catpn} PN")
print(f"AIM spine split  €{aim:,.2f} on {aimpn} PN")
print(f"  AGREES         {abs(cat - aim) < 0.005 and catpn == aimpn}")

# 3. the two largest misfiled parts should equal the ELEMENT; AIR CLEANER row
top2 = sum(v for pn, v in sorted(vals, key=lambda x: -x[1])[:2])
print()
print(f"two largest misfiled PNs        €{top2:,.2f}")
cat_tbl = re.search(r"\| `ELEMENT; AIR CLEANER` \| (\d+) \| €([\d,]+\.\d\d) \|", text)
if cat_tbl:
    print(f"category row 'ELEMENT; AIR CLEANER' {cat_tbl.group(1)} PN  €{eur(cat_tbl.group(2)):,.2f}")
    print(f"  AGREES         {abs(top2 - eur(cat_tbl.group(2))) < 0.005}"
          f"  ({cat_tbl.group(1)} = 2 PN)")
