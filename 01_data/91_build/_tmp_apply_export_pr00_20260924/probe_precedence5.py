"""Step 1e — lock the exact numbers for the report (READ ONLY)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
TIER = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"


def clean(s):
    x = s.fillna("").astype(str).str.strip()
    return x.where(~x.str.lower().isin(["", "nan", "none", "null"]), "")


def pn_key(s):
    return s.fillna("").astype(str).str.strip().str.upper()


def flags(s):
    return clean(s).str.lower().eq("true")


aud = pd.read_csv(TIER / "tierA_audited.csv", dtype=str, low_memory=False)
print("tierA_audited rows:", len(aud))
tA = flags(aud["tierA"])
und = flags(aud["undefendable"])
conv = flags(aud["convention"])
print("tierA True:", int(tA.sum()))
print("undefendable True:", int(und.sum()), "convention True:", int(conv.sum()),
      "either:", int((und | conv).sum()))
print("rows where tierA=False:", int((~tA).sum()))

defend = aud[tA & ~(und | conv)].copy()
defend["pn"] = pn_key(defend["pn"])
pns = sorted(defend["pn"].unique())
print("\ndefensible rows:", len(defend), "unique PNs:", len(pns))
print("EUR total:", round(float(pd.to_numeric(defend['list_eur'], errors='coerce').sum()), 2))

master = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
master["pn"] = pn_key(master["part_number"])
cls = pd.read_csv(DER / "aim_pn_classification_20260920.csv", dtype=str, low_memory=False)
cls["pn"] = pn_key(cls["part_number"])
cls_first = cls.drop_duplicates("pn", keep="first").set_index("pn")

m_hit = master[master["pn"].isin(pns)].copy()
fx = clean(m_hit["aim_l1_fixed"]) != ""
free_pns = sorted(set(m_hit.loc[~fx, "pn"]))
blocked_pns = sorted(set(m_hit.loc[fx, "pn"]))
not_in_master = sorted(set(pns) - set(master["pn"]))

def eur(pset):
    s = defend[defend["pn"].isin(pset)]
    return round(float(pd.to_numeric(s["list_eur"], errors="coerce").sum()), 2)

print("\n--- SPLIT OF THE 300 ---")
print(f"on master, aim_l1_fixed empty  (write would land) : {len(free_pns):3d}  EUR {eur(free_pns):>10,.2f}")
print(f"on master, aim_l1_fixed set    (would be ignored) : {len(blocked_pns):3d}  EUR {eur(blocked_pns):>10,.2f}")
print(f"not on master at all           (write impossible) : {len(not_in_master):3d}  EUR {eur(not_in_master):>10,.2f}")
print("total:", len(free_pns) + len(blocked_pns) + len(not_in_master))

print("\n--- master *_fixed on the matched 256 ---")
for col in ("aim_l1_fixed", "aim_l2_fixed"):
    v = clean(m_hit[col])
    print(f"  master {col}: non-empty {int((v != '').sum())}  {v[v != ''].value_counts().to_dict()}")
print(f"  master aim_l3_fixed: COLUMN ABSENT")

print("\n--- classification overlay for the 300 ---")
c_hit = cls[cls["pn"].isin(pns)]
print("present:", c_hit["pn"].nunique(), "absent:", len(set(pns) - set(c_hit["pn"])))
for col in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"):
    v = clean(c_hit[col])
    print(f"  cls {col}: non-empty {int((v != '').sum())}  {v[v != ''].value_counts().to_dict()}")

print("\n--- do any FREE (would-land) PNs carry a cls l1_fixed / l2_fixed / l3_fixed? ---")
cf = cls_first.reindex(free_pns)
for col in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"):
    v = clean(cf[col]) if col in cf.columns else pd.Series([""] * len(cf))
    print(f"  {col}: non-empty {int((v != '').sum())} {v[v != ''].value_counts().to_dict()}")

print("\n--- the 4 on master but absent from classification ---")
onmaster_notcls = sorted(set(pns) & set(master["pn"]) - set(cls["pn"]))
print(len(onmaster_notcls), onmaster_notcls)

print("\n--- do the 92 blocked share the same cls values? (i.e. two copies of Unknown) ---")
cb = cls_first.reindex(blocked_pns)
for col in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"):
    v = clean(cb[col]) if col in cb.columns else pd.Series([""] * len(cb))
    print(f"  cls {col}: non-empty {int((v != '').sum())} {v[v != ''].value_counts().to_dict()}")

print("\n--- reason string on blocked rows ---")
print(clean(master.set_index("pn").reindex(blocked_pns)["aim_source"]).value_counts().to_dict())
print("master-wide aim_l1_fixed non-empty:", int((clean(master['aim_l1_fixed']) != '').sum()),
      "of", len(master))
print("of those, value 'Unknown':", int((clean(master['aim_l1_fixed']) == 'Unknown').sum()),
      "| 'Unknown Review':", int((clean(master['aim_l1_fixed']) == 'Unknown Review').sum()))
