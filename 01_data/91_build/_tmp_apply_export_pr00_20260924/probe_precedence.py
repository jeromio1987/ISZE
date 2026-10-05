"""Step 1 — prove precedence before writing anything (READ ONLY)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
TIER = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"


def clean(s: pd.Series) -> pd.Series:
    x = s.fillna("").astype(str).str.strip()
    return x.where(~x.str.lower().isin(["", "nan", "none", "null"]), "")


def pn_key(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.upper()


def flags(s: pd.Series) -> pd.Series:
    return clean(s).str.lower().eq("true")


aud = pd.read_csv(TIER / "tierA_audited.csv", dtype=str, low_memory=False)
print("tierA_audited rows:", len(aud))
print("tierA flag:", flags(aud["tierA"]).value_counts().to_dict())
und = flags(aud["undefendable"])
conv = flags(aud["convention"])
print("undefendable true:", int(und.sum()))
print("convention true:", int(conv.sum()))
print("either true:", int((und | conv).sum()))
print("both true:", int((und & conv).sum()))
print("\ncarve-out rows, both flags, desc + d_l1:")
carve = aud[und | conv]
print(carve[["pn", "Description", "d_l1", "list_eur", "undefendable", "convention"]].to_string(index=False))

defend = aud[~(und | conv)].copy()
print("\ndefensible rows:", len(defend))
defend["pn"] = pn_key(defend["pn"])
pns = sorted(defend["pn"].unique())
print("defensible unique PNs:", len(pns))

multi = defend["pn"].value_counts()
print("defensible PNs appearing more than once:", (multi > 1).sum())
if (multi > 1).any():
    dup = multi[multi > 1]
    print(dup.to_dict())
    print(defend[defend["pn"].isin(dup.index)][["pn", "Description", "d_l1", "list_eur", "fig_key"]].to_string(index=False))

# ---- master ----
master = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
print("\nmaster rows:", len(master))
print("master cols:", list(master.columns))
master["pn"] = pn_key(master["part_number"])

m_hit = master[master["pn"].isin(pns)].copy()
print("master rows matching the defensible PNs:", len(m_hit))
print("distinct PNs matched in master:", m_hit["pn"].nunique())
missing = sorted(set(pns) - set(m_hit["pn"]))
print("PNs NOT in master:", len(missing), missing[:20])

for col in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"):
    if col in master.columns:
        v = clean(m_hit[col])
        nn = v[v != ""]
        print(f"master {col}: non-empty {len(nn)} of {len(m_hit)}; values {nn.value_counts().to_dict()}")
    else:
        print(f"master {col}: COLUMN ABSENT")

cur = clean(m_hit["aim_l1"])
print("\nmaster current aim_l1 on matched rows:", cur.replace("", "<empty>").value_counts().to_dict())

# ---- classification overlay ----
cls = pd.read_csv(DER / "aim_pn_classification_20260920.csv", dtype=str, low_memory=False)
print("\nclassification rows:", len(cls))
print("classification cols:", list(cls.columns))
cls["pn"] = pn_key(cls["part_number"])
c_hit = cls[cls["pn"].isin(pns)].copy()
print("classification rows matching the PNs:", len(c_hit))
print("distinct PNs matched:", c_hit["pn"].nunique())
c_missing = sorted(set(pns) - set(c_hit["pn"]))
print("PNs NOT in classification:", len(c_missing), c_missing[:20])

for col in ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed", "aim_l1", "aim_l2", "aim_l3"):
    if col in cls.columns:
        v = clean(c_hit[col])
        nn = v[v != ""]
        print(f"cls {col}: non-empty {len(nn)} of {len(c_hit)}; values {nn.value_counts().head(10).to_dict()}")
    else:
        print(f"cls {col}: COLUMN ABSENT")
