"""Tier analysis part 5 -- the GPT-classified workbook as a second, wider label.

The classified workbook (IE40 price list, 164k rows) carries a Level 1/2/3
assignment made on the whole row. Its Level 2 Group is a fine-grained name
("Brake parts", "Filters", "Exhaust"). If Level 2 maps cleanly onto the 21-family
system vocabulary that the master uses, it becomes a second route into the queue
that does not depend on the master's own description join.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

pd.set_option("display.width", 320)
pd.set_option("display.max_columns", 80)

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
FLAT = ROOT / "01_data" / "00_derived" / "_audit_cls_pr00_flat.csv"
MASTER = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
QUEUE = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" / "queue.csv"
CLSWB = ROOT / "01_data" / "01_Pricing" / "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"

log = []
def say(*a):
    line = " ".join(str(v) for v in a); print(line); log.append(line)
def norm_pn(s): return s.fillna("").astype(str).str.strip().str.upper()
def norm_desc(s):
    return (s.fillna("").astype(str).str.upper().str.strip().str.replace(r"\s+", " ", regex=True))
def is_known(l1): return str(l1 or "").strip().lower() not in ("", "nan", "none", "null", "unknown", "unknown review")

say("=" * 78)
say("A. READ THE CLASSIFIED WORKBOOK (Sheet1)")
cls = pd.read_excel(CLSWB, sheet_name="Sheet1", dtype=str)
cls.columns = [str(c).strip() for c in cls.columns]
say(f"  rows: {len(cls):,}   cols: {list(cls.columns)}")
cls = cls.rename(columns={"P/N": "pn_raw", "Newest P/N": "pn_new",
                          "Description": "description",
                          "Level 1 Family": "g_l1", "Level 2 Group": "g_l2",
                          "Level 3 Type": "g_l3", "Fig No.": "fig_no", "Key No.": "key_no"})
cls["pn"] = norm_pn(cls["pn_new"])
cls["desc_norm"] = norm_desc(cls["description"])
cls["l2"] = cls["g_l2"].fillna("").astype(str).str.strip()
say(f"  distinct Level 2 groups: {cls['l2'].nunique()}")
say(f"  Level 1 values ({cls['g_l1'].nunique()}): {sorted(cls['g_l1'].dropna().unique())}")
say("  the 25 largest Level 2 groups:")
for k, v in cls["l2"].value_counts().head(25).items():
    say(f"      {k:34s} {v:7,d}")

say("")
say("=" * 78)
say("B. DOES LEVEL 2 GROUP -> ONE SYSTEM FAMILY?")
m = pd.read_csv(MASTER, dtype=str, low_memory=False)
m["pn"] = norm_pn(m["part_number"]); m = m.drop_duplicates("pn", keep="first")
m["known"] = m["aim_l1"].map(is_known)
mk = m[m["known"]][["pn", "aim_l1", "aim_l2", "aim_l3"]]

j = cls[["pn", "l2", "g_l1", "g_l3", "desc_norm"]].merge(mk, on="pn", how="inner")
say(f"  classified-workbook rows that also have a real family on the master: {len(j):,}")
g = j.groupby("l2")["aim_l1"]
dd = pd.DataFrame({"n_parts": g.size(), "n_l1": g.nunique(),
                   "top_l1": g.agg(lambda s: s.value_counts().index[0]),
                   "top_share": g.agg(lambda s: s.value_counts().iloc[0] / len(s))})
pred = dd["top_l1"].to_dict()
j["pred"] = j["l2"].map(pred)
acc = float((j["pred"] == j["aim_l1"]).mean())
say(f"  distinct Level 2 groups measured : {len(dd):,}")
say(f"  groups -> ONE family             : {(dd['n_l1']==1).sum():,} ({(dd['n_l1']==1).mean()*100:.2f}%)")
say(f"  groups -> MORE THAN ONE family   : {(dd['n_l1']>1).sum():,} ({(dd['n_l1']>1).mean()*100:.2f}%)")
say(f"  median top-family share          : {dd['top_share'].median():.4f}")
say(f"  PART-LEVEL accuracy, modal family per Level 2 group: {acc:.4f}")
say("")
say("  groups that are ambiguous, with the family spread:")
amb = dd[dd["n_l1"] > 1].sort_values("n_parts", ascending=False)
for k, r in amb.head(30).iterrows():
    sub = j[j["l2"] == k]; dist = sub["aim_l1"].value_counts()
    say(f"      {k[:34]:34s} n={r['n_parts']:5,d} L1s={r['n_l1']:3d} | "
        + " | ".join(f"{a}={b}" for a, b in list(dist.items())[:5]))

say("")
say("=" * 78)
say("C. COVERAGE OF THE QUEUE")
q = pd.read_csv(QUEUE, dtype=str, encoding="utf-8-sig")
q["pn"] = norm_pn(q["pn"])
q = q.merge(cls[["pn", "l2", "g_l1", "g_l3"]].drop_duplicates("pn"), on="pn", how="left")
say(f"  queue rows                    : {len(q):,}")
say(f"  queue rows with a Level 2 group: {q['l2'].notna().sum():,}")
say(f"  queue rows WITHOUT one         : {q['l2'].isna().sum():,}")
say("  queue rows per Level 2 group (top 30):")
for k, v in q["l2"].value_counts().head(30).items():
    l1 = dd.set_index("l2")["top_l1"].get(k, "?")
    n1 = dd.set_index("l2")["n_l1"].get(k, "?")
    say(f"      {k[:34]:34s} {v:4d}  -> {l1}  (L1s behind={n1})")

q.to_csv(OUT / "queue_with_l2.csv", index=False, encoding="utf-8-sig")
dd.to_csv(OUT / "l2_to_family_purity.csv")
(OUT / "run_log5.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE5")
