"""Follow-up numbers for Shard A findings note."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
j = json.loads((ISZE / "01_data/91_build/_aim_tranche1_findings_20261007.json").read_text(encoding="utf-8"))
print("desc filled", j["descriptions_filled_after_jp_enrich"], "blank", j["descriptions_still_blank"])
print("flags:")
for f in j["flags"]:
    print(f"  n={f['n']:5d} {f['confidence']:8s} {f['agree_share']:.3f}  {f['cat_path'][:75]} -> {f['propose_aim_l1']}")
    print("   ", f["reasons"][0][:140])

aim2 = pd.read_csv(ISZE / "01_data/00_derived/aim_master_v2.csv", dtype=str, low_memory=False)


def clean(s):
    return "" if pd.isna(s) else str(s).strip()


aim2["cat"] = aim2["cat_l1"].map(clean) + " > " + aim2["cat_l2"].map(clean) + " > " + aim2["cat_l3"].map(clean)
g = aim2[aim2["cat"] == "Repair parts > Gaskets / seals > Gasket set"]
print("gasket master rows", len(g))
print(g["aim_l1"].map(clean).value_counts().head().to_string())
kt = g[g["aim_l1"].map(clean) == "Transmission"]
print(
    "known Transmission gasket descs with ENG:",
    int(kt["description"].fillna("").str.contains("ENG|ENGINE|HD OVERHAUL", case=False, regex=True).sum()),
    "of",
    len(kt),
)
# JP cols
jp = pd.read_csv(ISZE / "01_data/00_derived/jp_codes_cache_20260920.csv", dtype=str, nrows=2)
print("jp columns:", list(jp.columns)[:20])
