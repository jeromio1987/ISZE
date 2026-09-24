"""Read-only probe: what is the real reason the two DATA_FAMILY_ONE_LEAF_SPLIT parts stayed open?

open_why.py prints "split over 1 leave-paths" for them, which looks like a wording bug:
the column it prints as n_leaves is the distinct-family count, so the message is nonsense.
This reproduces the dictionary the same way open_why.py does and shows the wording's full
path evidence (distinct L1>L2>L3 paths, parts behind each), so we can tell whether the
report is right to put these two in the catalogue group.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
TARGET_WORDINGS = ["BAR; BACK,RR", "BAR; BACK,FRT"]


def norm_pn(s):
    return s.fillna("").astype(str).str.strip().str.upper()


def norm_desc(s):
    return s.fillna("").astype(str).str.upper().str.strip().str.replace(r"\s+", " ", regex=True)


def bl(s):
    x = s.fillna("").astype(str).str.strip()
    return x.where(~x.str.lower().isin(["", "nan", "none", "null"]), "")


def is_marker(label):
    return label.strip().lower().startswith("unknown")


m = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
m["pnk"] = norm_pn(m["part_number"])
m["dn"] = norm_desc(m["description"])
m["label"] = bl(m["aim_l1_fixed"]).where(lambda s: s != "", bl(m["aim_l1"]))
m["l2"] = bl(m["aim_l2_fixed"]).where(lambda s: s != "", bl(m["aim_l2"]))
m["l3"] = bl(m["aim_l3"])

o = pd.read_csv(DER / "aim_pn_classification_20260920.csv", dtype=str, low_memory=False)
o["pnk"] = norm_pn(o["part_number"])
o["label"] = bl(o["aim_l1_fixed"])
oi = o.drop_duplicates("pnk", keep="first").set_index("pnk")
ov = bl(oi["label"].reindex(m["pnk"]).reset_index(drop=True))
ov.index = m.index
m["label_eff"] = m["label"].where(ov == "", ov)

known = m[(m["label_eff"] != "") & (~m["label_eff"].map(is_marker))].copy()
known["path"] = (known["label_eff"] + " > " + known["l2"] + " > " + known["l3"]).str.strip()

for dn in TARGET_WORDINGS:
    sub = known[known["dn"] == dn]
    print("=" * 70)
    print("wording:", dn)
    print("  master rows with this wording and a usable family:", len(sub))
    print("  families :", sub["label_eff"].value_counts().to_dict())
    print("  full paths:", sub["path"].value_counts().to_dict())
    print("  figure keys:", sub["fig_key"].fillna("").value_counts().to_dict())
    print("  example parts:", sub["pnk"].head(6).tolist())

print()
print("Reading: one family but more than one full path means the master itself files the")
print("wording under two sub-groups, which is what the report calls a sub-group split.")
