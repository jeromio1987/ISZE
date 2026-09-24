"""Read-only: the 43 parts with no master row. What did the earlier EPC harvest return for them,
and did the classifier manage to turn that into a family?"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
DER = ROOT / "01_data" / "00_derived"

cls = pd.read_csv(ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924" / "open_parts_classified.csv",
                  dtype=str, encoding="utf-8-sig")
n43 = set(cls.loc[cls["group"] == "DATA_NOT_IN_MASTER", "pnk"])
print("DATA_NOT_IN_MASTER:", len(n43))

hits = {}
for line in (EQ / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        r = json.loads(line)
        hits[r["pn"]] = r
print("EPC harvest result for those 43:", Counter(
    (hits.get(p, {}).get("eq_status", "(not in harvest)"), bool((hits.get(p, {}).get("eq_fig_name") or "").strip()))
    for p in n43
).most_common())

c = pd.read_csv(EQ / "classified.csv", dtype=str, low_memory=False)
c["pn"] = c["pn"].fillna("").astype(str).str.strip().str.upper()
sub = c[c["pn"].isin(n43)].drop_duplicates("pn")
filled = sub[sub["aim_level_1"].fillna("") != ""]
print("the classifier turned an EPC answer into a family for:", len(filled), "of the 43")
print("  source:", filled["aim_source_this_pass"].value_counts().to_dict())
print("blank reasons on the rest:")
print(sub.loc[sub["aim_level_1"].fillna("") == "", "aim_note"].value_counts().to_string())

m = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
m["k"] = m["part_number"].fillna("").astype(str).str.strip().str.upper()
print()
print("rows on the master for those 43:", int(m["k"].isin(n43).sum()))
print("=> the 43 cannot be written at all: there is no row to write a family to.")
