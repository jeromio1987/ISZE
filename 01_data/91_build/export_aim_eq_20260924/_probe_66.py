"""Read-only: the 66 parts of the EPC-only list that are still open after the 16:20 write.
What did the earlier harvest return for each, and why did the classifier not settle it?"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
PLACE = {"", "nan", "none", "null", "unknown", "unknown review", "unclassified", "to review"}


def real(s):
    return ~s.fillna("").astype(str).str.strip().str.lower().isin(PLACE)


pns = json.loads((EQ / "open_worklist_epc_only_20260924.json").read_text(encoding="utf-8"))
m = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
m["k"] = m["part_number"].fillna("").astype(str).str.strip().str.upper()
g = m.drop_duplicates("k", keep="first").set_index("k").reindex(pns)
open_now = (~(real(g["aim_l1"]) | real(g["aim_l1_fixed"]))).values
opened = [p for p, o in zip(pns, open_now) if o]
print("still open:", len(opened))

hits = {}
for line in (EQ / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        r = json.loads(line)
        hits[r["pn"]] = r

c = pd.read_csv(EQ / "classified.csv", dtype=str, low_memory=False)
c["pn"] = c["pn"].fillna("").astype(str).str.strip().str.upper()
c = c.drop_duplicates("pn").set_index("pn")

rows = []
for p in opened:
    h = hits.get(p, {})
    cr = c.loc[p] if p in c.index else None
    rows.append({
        "pn": p,
        "desc": (cr["Description"] if cr is not None else ""),
        "on_master": p in g.index and pd.notna(g.loc[p, "part_number"]),
        "eq_status": h.get("eq_status", "(not harvested)"),
        "has_fig_name": bool((h.get("eq_fig_name") or "").strip()),
        "classifier_note": (cr["aim_note"] if cr is not None else ""),
    })
df = pd.DataFrame(rows)
print()
print("eq_status / has figure name:")
print(df.groupby(["eq_status", "has_fig_name"]).size().to_string())
print()
print("classifier note:")
print(df["classifier_note"].value_counts().to_string())
print()
print("on the master:")
print(df["on_master"].value_counts().to_string())
