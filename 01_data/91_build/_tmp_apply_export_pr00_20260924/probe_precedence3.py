"""Step 1c — mechanism behind the *_fixed columns + queue reconciliation (READ ONLY)."""
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
pns = sorted(defend["pn"].unique())

master = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
master["pn"] = pn_key(master["part_number"])
m_hit = master[master["pn"].isin(pns)].copy()

fx = clean(m_hit["aim_l1_fixed"]) != ""
print("=== mechanism: rows where aim_l1_fixed is non-empty ===")
sub = m_hit[fx]
for col in ("aim_source", "aim_l1", "aim_l2_fixed", "aim_changed", "jp_class_new",
            "jp_class_current", "jp_code_source", "has_aim", "desc_ambiguous"):
    if col in sub.columns:
        print(f"  {col}: {clean(sub[col]).replace('', '<empty>').value_counts().head(6).to_dict()}")

print("\n=== rows where aim_l1_fixed is EMPTY (our write would show) ===")
sub2 = m_hit[~fx]
for col in ("aim_source", "aim_l1", "aim_l2", "aim_changed", "has_aim", "desc_ambiguous"):
    if col in sub2.columns:
        print(f"  {col}: {clean(sub2[col]).replace('', '<empty>').value_counts().head(6).to_dict()}")

print("\nwrite would show for:", int((~fx).sum()), "of", len(m_hit))
print("silently overridden for:", int(fx.sum()), "of", len(m_hit))

# ---- master-wide: how common is aim_l1_fixed == Unknown? ----
allfx = clean(master["aim_l1_fixed"])
print("\n=== master-wide aim_l1_fixed ===")
print("non-empty:", int((allfx != "").sum()), "of", len(master))
print(allfx.replace("", "<empty>").value_counts().head(8).to_dict())

# ---- queue reconciliation ----
print("\n=== queue reconciliation ===")
qf = pd.read_csv(TIER / "queue_final_tiered.csv", dtype=str, low_memory=False)
print("queue_final_tiered rows:", len(qf), "cols:", list(qf.columns)[:14])
if "part_number" in qf.columns:
    qpn = pn_key(qf["part_number"])
else:
    qpn = pn_key(qf[qf.columns[qf.columns.str.lower().isin(["pn", "part_number"])][0]])
print("unique queue PNs:", qpn.nunique())

for name in ("queue.csv", "queue.json"):
    p = EQ / name
    print(f"{name} exists: {p.exists()}", p.stat().st_size if p.exists() else "")

qcsv = pd.read_csv(EQ / "queue.csv", dtype=str, low_memory=False)
print("queue.csv rows:", len(qcsv), "cols:", list(qcsv.columns)[:12])
if "part_number" in qcsv.columns:
    print("queue.csv unique PNs:", pn_key(qcsv["part_number"]).nunique())

# the 44 not on master: present in the export?
xl = pd.read_excel(ROOT / "01_data" / "EXPORT.XLSX", dtype=str)
print("\nEXPORT.XLSX rows:", len(xl), "cols:", list(xl.columns))
miss44 = sorted(set(pns) - set(master["pn"]))
epn = pn_key(xl["Part Number"]) if "Part Number" in xl.columns else None
if epn is not None:
    print("EXPORT.XLSX unique PNs:", epn.nunique())
    print("missing-44 found in export:", len(set(miss44) & set(epn)))
