"""Read-only: what did the already-harvested EPC run cover, and where did the 133 filled
parts on the EPC-only list get their family from?"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"

rows = []
for line in (EQ / "eq_results.jsonl").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line:
        rows.append(json.loads(line))
print("eq_results.jsonl rows:", len(rows))
print("distinct pn:", len({r.get("pn") for r in rows}))
print("status:", Counter(r.get("eq_status") for r in rows).most_common())
print("with a figure name:", sum(1 for r in rows if (r.get("eq_fig_name") or "").strip()))
print("with a figure key :", sum(1 for r in rows if (r.get("eq_fig_key") or "").strip()))

epc = set(json.loads((EQ / "open_worklist_epc_only_20260924.json").read_text(encoding="utf-8")))
covered = {r.get("pn") for r in rows}
print()
print("EPC-only list:", len(epc))
print("already in eq_results:", len(epc & covered), "| not covered:", len(epc - covered))

c = pd.read_csv(EQ / "classified.csv", dtype=str, low_memory=False)
c["pn"] = c["pn"].fillna("").astype(str).str.strip().str.upper()
sub = c[c["pn"].isin(epc)]
print()
print("classified.csv rows for the EPC-only list:", len(sub))
print("fill source:")
print(sub["aim_source_this_pass"].fillna("(blank)").value_counts().to_string())
print()
print("blank reasons among them:")
print(sub.loc[sub["aim_level_1"].fillna("") == "", "aim_note"].value_counts().head(10).to_string())

print()
print("--- the 43 with no master row: are they all in the EPC-only list, and what did the EPC say? ---")
cls = pd.read_csv(ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924" / "open_parts_classified.csv",
                  dtype=str, encoding="utf-8-sig")
n43 = set(cls.loc[cls["group"] == "DATA_NOT_IN_MASTER", "pnk"])
print("DATA_NOT_IN_MASTER count:", len(n43), "| inside epc-only:", len(n43 & epc))
st = Counter((r.get("eq_status"), bool((r.get("eq_fig_name") or "").strip())) for r in rows if r.get("pn") in n43)
print("their eq_results status (status, has_fig_name):", st.most_common())
