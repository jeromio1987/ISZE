"""Step 1d — final facts for the report (READ ONLY)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
TIER = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"


def clean(s):
    x = s.fillna("").astype(str).str.strip()
    return x.where(~x.str.lower().isin(["", "nan", "none", "null"]), "")


def pn_key(s):
    return s.fillna("").astype(str).str.strip().str.upper()


def flags(s):
    return clean(s).str.lower().eq("true")


aud = pd.read_csv(TIER / "tierA_audited.csv", dtype=str, low_memory=False)
defend = aud[~(flags(aud["undefendable"]) | flags(aud["convention"]))].copy()
defend["pn"] = pn_key(defend["pn"])

master = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
master["pn"] = pn_key(master["part_number"])

pns = sorted(defend["pn"].unique())
m_hit = master[master["pn"].isin(pns)].copy()
fx = clean(m_hit["aim_l1_fixed"]) != ""
blocked = m_hit[fx]
free = m_hit[~fx]
miss44 = sorted(set(pns) - set(master["pn"]))

# list price per group, from the audit
defender = defend.set_index(pd.Index(defend["pn"]))
eur = pd.to_numeric(defend["list_eur"], errors="coerce")
def sum_eur(pset):
    s = defend[defend["pn"].isin(pset)]
    return float(pd.to_numeric(s["list_eur"], errors="coerce").sum())

print("=== the 300 defensible PNs, split by what would actually happen ===")
print(f"total defensible unique PNs            : {len(pns)}   EUR {sum_eur(pns):,.0f}")
print(f"  write WOULD land (aim_l1_fixed empty): {int((~fx).sum())}   EUR {sum_eur(set(free['pn'])):,.0f}")
print(f"  write SILENTLY OVERRIDDEN            : {int(fx.sum())}   EUR {sum_eur(set(blocked['pn'])):,.0f}")
print(f"  not on master at all                 : {len(miss44)}   EUR {sum_eur(set(miss44)):,.0f}")
print("sum check:", int((~fx).sum()) + int(fx.sum()) + len(miss44))

print("\n=== blocked rows: current labels the builder would keep ===")
print(blocked["aim_l1"].replace("", "<empty>").value_counts().to_dict())

print("\n=== the 44 not on the master: descriptions ===")
d44 = defend[defend["pn"].isin(miss44)][["pn", "Description", "d_l1", "list_eur", "on_master"]]
print("rows:", len(d44), "unique PNs:", d44["pn"].nunique())
print(d44.head(15).to_string(index=False))

# are they in the raw export?
xl = pd.read_excel(ROOT / "01_data" / "EXPORT.XLSX", dtype=str)
epn = pn_key(xl["P/N"])
print("\nEXPORT.XLSX rows:", len(xl), "unique P/N:", epn.nunique())
print("the 44 present in EXPORT.XLSX:", len(set(miss44) & set(epn)))

# are they in the queue?
qcsv = pd.read_csv(EQ / "queue.csv", dtype=str, low_memory=False)
qpn = pn_key(qcsv["pn"])
print("the 44 present in queue.csv:", len(set(miss44) & set(qpn)))

# --- prove the builder precedence claim on the FILE, not on a simulation ---
print("\n=== does the CURRENT dated pair already show 'Unknown' for these? ===")
cands = sorted(DER.glob("AIM_Master_PN_Categories_Figkey_*.csv"))
print("dated CSVs on disk:", [(p.name, p.stat().st_size) for p in cands])
if cands:
    latest = max(cands, key=lambda p: p.stat().st_mtime)
    print("reading:", latest.name)
    d = pd.read_csv(latest, dtype=str, low_memory=False)
    d["pn"] = pn_key(d["part_number"])
    dhit = d[d["pn"].isin(pns)]
    print("rows for our 300 in the current deliverable:", len(dhit), "unique PNs:", dhit["pn"].nunique())
    print("aim_level_1 values:", clean(dhit["aim_level_1"]).replace("", "<empty>").value_counts().to_dict())
    # do the 92 blocked show Unknown?
    dd = dhit[dhit["pn"].isin(set(blocked["pn"]))]
    print("blocked-92 rows shown in deliverable:", len(dd))
    print("their aim_level_1 in the deliverable:", clean(dd["aim_level_1"]).replace("", "<empty>").value_counts().to_dict())
