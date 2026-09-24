"""Step 1b — prove what the builder would actually show, and chase the 44 missing PNs (READ ONLY)."""
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
defend = aud[~(flags(aud["undefendable"]) | flags(aud["convention"]))].copy()
defend["pn"] = pn_key(defend["pn"])
pns = sorted(defend["pn"].unique())

master = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
master["pn"] = pn_key(master["part_number"])

cls = pd.read_csv(DER / "aim_pn_classification_20260920.csv", dtype=str, low_memory=False)
cls["pn"] = pn_key(cls["part_number"])
cls_first = cls.drop_duplicates("pn", keep="first").set_index("pn")

m_hit = master[master["pn"].isin(pns)].copy()
print("=== what the builder would show for the 300 ===")
# replicate the builder exactly
aim_l1 = clean(m_hit["aim_l1_fixed"]).where(clean(m_hit["aim_l1_fixed"]) != "", clean(m_hit["aim_l1"]))
got = clean(m_hit["pn"].map(cls_first["aim_l1_fixed"]).fillna(""))
aim_l1_final = got.where(got != "", aim_l1)

fixed_nonempty = clean(m_hit["aim_l1_fixed"]) != ""
print("matched rows in master:", len(m_hit))
print("rows where master aim_l1_fixed is non-empty:", int(fixed_nonempty.sum()))
print("rows where master aim_l1_fixed is empty  :", int((~fixed_nonempty).sum()))

# simulate a write: new family 'Engine' placed on ALL 256 rows, then apply the builder precedence
sim = m_hit.copy()
sim["new_l1"] = "Engine"
after_master = clean(sim["aim_l1_fixed"]).where(clean(sim["aim_l1_fixed"]) != "", clean(sim["new_l1"]))
got2 = clean(sim["pn"].map(cls_first["aim_l1_fixed"]).fillna(""))
after_cls = got2.where(got2 != "", after_master)
print("\nIf we wrote a real family on all 256 rows, the delivered CSV would show:")
print(after_cls.replace("", "<empty>").value_counts().to_dict())
print("rows where our write survives to the deliverable:", int((after_cls == "Engine").sum()))
print("rows where 'Unknown'/'Unknown Review'/'Unclassified' wins :", int((after_cls != "Engine").sum()))

print("\n=== after_cls detail on blocked rows ===")
blocked = sim[after_cls != "Engine"]
print(blocked[["pn", "aim_l1", "aim_l1_fixed", "aim_l2_fixed"]].head(12).to_string(index=False))

# ---- the 44 PNs not in master: do they exist under a different spelling? ----
missing = sorted(set(pns) - set(master["pn"]))
print("\n=== PNs not found in master:", len(missing), "===")
mstr = master["part_number"].fillna("").astype(str).str.strip()
mstr_nolz = mstr.str.lstrip("0")
mstr_zero = mstr.str.zfill(10)
miss_set = set(missing)
hit_nolz = {p for p in missing if p.lstrip("0") in set(mstr_nolz)}
hit_z = {p for p in missing if p.zfill(10) in set(mstr_zero)}
print("found if leading zeros ignored :", len(hit_nolz), sorted(hit_nolz)[:10])
print("found if zero-padded to 10     :", len(hit_z), sorted(hit_z)[:10])
print("still missing both ways        :", len(miss_set - hit_nolz - hit_z))
print("length distribution of missing :", pd.Series([len(x) for x in missing]).value_counts().to_dict())
print("length distribution of all master PNs:", mstr.str.len().value_counts().head(8).to_dict())

# also check the tiering file's own on_master column
if "on_master" in aud.columns:
    print("\naud on_master value counts:", flags(aud["on_master"]).value_counts().to_dict())
    om = aud[~(flags(aud["undefendable"]) | flags(aud["convention"]))]
    print("defensible on_master:", flags(om["on_master"]).value_counts().to_dict())
