"""Read-only: pin down what the published pair dated 2026-09-24 shows for the EPC-only list,
and exactly where the 133 fills came from. No writes."""
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


def mtime(p: Path) -> str:
    return pd.Timestamp(p.stat().st_mtime, unit="s", tz="UTC").tz_convert("Europe/Berlin").isoformat()


pns = json.loads((EQ / "open_worklist_epc_only_20260924.json").read_text(encoding="utf-8"))
pset = set(pns)

for name in [
    "aim_master_v2.csv",
    "AIM_Master_PN_Categories_Figkey_20260921.csv",
    "AIM_Master_PN_Categories_Figkey_20260924.csv",
    "AIM_Master_PN_Categories_Figkey_20260924.xlsx",
]:
    p = DER / name
    if p.exists():
        print(f"{name:48s} {p.stat().st_size:>12,}  {mtime(p)}")
print()

# --- the pair Power BI loads -------------------------------------------------
pair = DER / "AIM_Master_PN_Categories_Figkey_20260924.csv"
p = pd.read_csv(pair, dtype=str, low_memory=False)
p["k"] = p["part_number"].fillna("").astype(str).str.strip().str.upper()
pi = p.drop_duplicates("k", keep="first").set_index("k")
pg = pi.reindex(pns)
l1 = pg["aim_level_1"]
print("published 2026-09-24 pair, for the 199:")
print("  rows present            :", int(pg["part_number"].notna().sum()))
print("  real family             :", int(real(l1).sum()))
print("  blank / Unknown         :", int((~real(l1)).sum()))
print("  values of aim_level_1 on the blanks:", l1[~real(l1)].replace("", "(blank)").value_counts().to_dict())
print()
print("  the same 199 in the 2026-09-21 pair:")
p21 = pd.read_csv(DER / "AIM_Master_PN_Categories_Figkey_20260921.csv", dtype=str, low_memory=False)
p21["k"] = p21["part_number"].fillna("").astype(str).str.strip().str.upper()
g21 = p21.drop_duplicates("k", keep="first").set_index("k").reindex(pns)
print("    rows present          :", int(g21["part_number"].notna().sum()))
print("    real family           :", int(real(g21["aim_level_1"]).sum()))
print()

# --- where the fills came from ----------------------------------------------
c = pd.read_csv(EQ / "classified.csv", dtype=str, low_memory=False)
c["pn"] = c["pn"].fillna("").astype(str).str.strip().str.upper()
sub = c[c["pn"].isin(pset)].drop_duplicates("pn")
filled = sub[sub["aim_level_1"].fillna("") != ""]
print("classified.csv, one row per part number of the 199:")
print("  filled                 :", len(filled), "| blank:", len(sub) - len(filled))
print("  fill source            :", filled["aim_source_this_pass"].value_counts().to_dict())
print()
print("  how many of those fills are on a part number the master actually has:",
      int(filled["pn"].isin(pi.index).sum()))

m = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
m["k"] = m["part_number"].fillna("").astype(str).str.strip().str.upper()
mi = m.drop_duplicates("k", keep="first").set_index("k")
g = mi.reindex(pns)
base_ok, fixed_ok = real(g["aim_l1"]), real(g["aim_l1_fixed"])
carry = (base_ok | fixed_ok).values
print()
print("master right now, for the 199:")
print("  carry a real family    :", int(carry.sum()))
print("  no real family         :", int((~carry).sum()))
print("  aim_source on the filled:", g.loc[carry, "aim_source"].value_counts().to_dict())
no_row = g["part_number"].isna().values
print("  no master row at all   :", int(no_row.sum()), "(all inside the still-open set)")
print()
print("  the 66 still open, by the analysis group:")
cls = pd.read_csv(ROOT / "01_data" / "91_build" / "export_aim_open_why_20260924" / "open_parts_classified.csv",
                  dtype=str, encoding="utf-8-sig")
cls = cls[cls["pnk"].isin(pset)].copy()
status = pd.DataFrame({
    "pnk": pns,
    "carry": (real(g["aim_l1"]) | real(g["aim_l1_fixed"])).values,
    "no_row": g["part_number"].isna().values,
})
cls = cls.merge(status, on="pnk", how="left")
print(cls[~cls["carry"].astype(bool)].groupby("group").size().to_string())
print("  reconcile: sum of groups =", int((~cls['carry'].astype(bool)).sum()), "| no-row =", int(cls['no_row'].astype(bool).sum()))
print()
print("  the 133 with a family: did the earlier EPC harvest (eq_results.jsonl) already cover them?")
rows = [json.loads(x) for x in (EQ / "eq_results.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
have = {r["pn"]: r for r in rows}
covered = [k for k in pns if not carry[list(pns).index(k)] is False]  # placeholder
filled_pns = [k for k, ok in zip(pns, carry) if ok]
in_run = sum(1 for k in filled_pns if k in have)
print(f"    of the 133 already filled, {in_run} are in the earlier harvest file")
