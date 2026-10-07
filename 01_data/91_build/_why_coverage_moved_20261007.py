"""Why did the warehouse AIM-family coverage move from 60.3% to 71.6%?

Counts the same thing three ways so the difference is visible rather than assumed.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DELAY = ROOT / "01_data" / "ISZE_Order Status as of 2 October 2026_request to check.xlsx"
AIM = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"


def norm(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v if v is not None else ""))


aim = pd.read_csv(AIM, dtype=str, low_memory=False)
aim["pn"] = aim["part_number"].fillna("").map(norm)
aim["fam_raw"] = aim["aim_l1"].fillna("").str.strip()
aim["fam_fix"] = aim["aim_l1_fixed"].fillna("").str.strip()

fam_raw, fam_both, infile = {}, {}, set()
for p, a, b in zip(aim["pn"], aim["fam_raw"], aim["fam_fix"]):
    if not p:
        continue
    k = p.lstrip("0")
    infile.add(k)
    if a and (k not in fam_raw or not fam_raw[k]):
        fam_raw[k] = a
    v = a or b
    if v and (k not in fam_both or not fam_both[k]):
        fam_both[k] = v

print(f"master part numbers      : {len(infile)}")
print(f"with a family, aim_l1 only: {len(fam_raw)}")
print(f"with a family, +aim_l1_fixed: {len(fam_both)}")
print()

dly = pd.read_excel(DELAY, sheet_name="isze", dtype=str)
dly["pn"] = dly["PN"].map(norm)
n = len(dly)


def cov(label, fammap):
    hit = sum(1 for p in dly["pn"] if fammap.get(p.lstrip("0")))
    print(f"{label:42s} {hit:5d} / {n}  = {100*hit/n:.1f}%")


cov("aim_l1 only", fam_raw)
cov("aim_l1 then aim_l1_fixed", fam_both)

# what the page's current coverage() actually counts
labels = {"in AIM, no family yet", "not in the AIM file"}
rows = []
for p in dly["pn"]:
    k = p.lstrip("0")
    if k in infile:
        v = fam_both.get(k, "")
        rows.append(v if v else "in AIM, no family yet")
    else:
        rows.append("not in the AIM file")
s = pd.Series(rows)
fam_n = int((~s.isin(list(labels))).sum())
print(f"\npage 'family' count (from the aim column):  {fam_n} / {n} = {100*fam_n/n:.1f}%")
print("counts by label:", s.value_counts().to_dict())
