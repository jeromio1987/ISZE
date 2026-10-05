"""Tier analysis part 6 -- can the classified workbook's own path name the family?

The workbook has Level 1 Family / Level 2 Group / Level 3 Type (172 leaves).
Level 2 alone is too coarse (58% part accuracy). Level 3 might be fine enough.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

pd.set_option("display.width", 320); pd.set_option("display.max_columns", 80)

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
MASTER = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
QUEUE = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" / "queue.csv"
CLSWB = ROOT / "01_data" / "01_Pricing" / "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"

log = []
def say(*a):
    line = " ".join(str(v) for v in a); print(line); log.append(line)
def norm_pn(s): return s.fillna("").astype(str).str.strip().str.upper()
def is_known(l1): return str(l1 or "").strip().lower() not in ("", "nan", "none", "null", "unknown", "unknown review")

cls = pd.read_excel(CLSWB, sheet_name="Sheet1", dtype=str)
cls.columns = [str(c).strip() for c in cls.columns]
cls = cls.rename(columns={"Newest P/N": "pn_new", "Level 1 Family": "g_l1",
                          "Level 2 Group": "g_l2", "Level 3 Type": "g_l3"})
cls["pn"] = norm_pn(cls["pn_new"])
for c in ("g_l1", "g_l2", "g_l3"):
    cls[c] = cls[c].fillna("").astype(str).str.strip()
cls["path"] = cls["g_l1"] + " > " + cls["g_l2"] + " > " + cls["g_l3"]

m = pd.read_csv(MASTER, dtype=str, low_memory=False)
m["pn"] = norm_pn(m["part_number"]); m = m.drop_duplicates("pn", keep="first")
m["known"] = m["aim_l1"].map(is_known)
mk = m[m["known"]][["pn", "aim_l1"]]

# use the master's OWN 164k-row row set: the classified workbook covers more PNs
# than the 19.8k known master rows, so join on whatever overlaps.
j = cls.drop_duplicates("pn", keep="first")[["pn", "g_l1", "g_l2", "g_l3", "path"]].merge(mk, on="pn", how="inner")
say("=" * 78)
say("A. THE WORKBOOK PATH AGAINST THE MASTER'S 21 FAMILIES")
say(f"  workbook rows: {len(cls):,}   overlapping the known master: {len(j):,}")

def score(df, key, label):
    g = df.groupby(key)["aim_l1"]
    t = pd.DataFrame({"n_parts": g.size(), "n_l1": g.nunique(),
                      "top_l1": g.agg(lambda s: s.value_counts().index[0]),
                      "top_share": g.agg(lambda s: s.value_counts().iloc[0] / len(s))})
    pred = t["top_l1"].to_dict()
    d = df.assign(pred=df[key].map(pred))
    acc = float((d["pred"] == d["aim_l1"]).mean())
    say(f"  {label:34s} keys={len(t):6,d}  one-family={(t['n_l1']==1).sum():6,d} "
        f"({(t['n_l1']==1).mean()*100:5.1f}%)  median top_share={t['top_share'].median():.3f}  "
        f"part-level acc={acc:.4f}")
    return t, acc, d

t2, a2, d2 = score(j, "g_l2", "Level 2 Group")
t3, a3, d3 = score(j, "g_l3", "Level 3 Type")
tp, ap, dp = score(j, "path", "full path L1>L2>L3")

say("")
say("  Level 3 leaves that are ambiguous (top 30 by size):")
amb = t3[t3["n_l1"] > 1].sort_values("n_parts", ascending=False)
for k, r in amb.head(30).iterrows():
    sub = j[j["g_l3"] == k]; dist = sub["aim_l1"].value_counts()
    say(f"      {k[:34]:34s} n={r['n_parts']:5,d} L1s={r['n_l1']:3d} | "
        + " | ".join(f"{a}={b}" for a, b in list(dist.items())[:5]))

say("")
say("=" * 78)
say("B. QUEUE COVERAGE VIA WORKBOOK")
q = pd.read_csv(QUEUE, dtype=str, encoding="utf-8-sig")
q["pn"] = norm_pn(q["pn"])
for c in ("pr00_value_eur", "list_eur"):
    q[c] = pd.to_numeric(q[c].fillna("").astype(str).str.replace(" ", "").str.replace(",", "."), errors="coerce")
q = q.merge(cls[["pn", "g_l1", "g_l2", "g_l3", "path"]].drop_duplicates("pn"), on="pn", how="left")

say(f"  queue rows                    : {len(q):,}")
say(f"  covered by the workbook       : {q['path'].notna().sum():,}")
say(f"  not covered                   : {q['path'].isna().sum():,}")

# apply the modal family per Level 3 leaf, but only where the leaf is decisive
pred3 = t3["top_l1"].to_dict(); one3 = set(t3[t3["n_l1"] == 1].index)
q["wb_l1_l3"] = q["g_l3"].map(pred3)
q["wb_l3_single"] = q["g_l3"].isin(one3)
q["wb_l3_n"] = q["g_l3"].map(t3["n_parts"])
say("")
say("  of the covered queue rows, how many sit on a Level 3 leaf that is decisive:")
say(f"    decisive leaf (one family on the master evidence) : {int(q['wb_l3_single'].sum()):,}")
say(f"    ambiguous leaf                                    : {int((q['path'].notna() & ~q['wb_l3_single']).sum()):,}")
say(f"    PR00 EUR on a decisive leaf                       : {q[q['wb_l3_single']]['pr00_value_eur'].sum():,.2f}")
say(f"    PR00 EUR on an ambiguous leaf                     : {q[q['path'].notna() & ~q['wb_l3_single']]['pr00_value_eur'].sum():,.2f}")

say("")
say("  the decisive Level 3 leaves used by the queue, with the family they imply:")
d3sum = (q[q["wb_l3_single"]].groupby(["g_l3", "wb_l1_l3"])
         .agg(rows=("pn", "size"), eur=("pr00_value_eur", "sum"), n=("wb_l3_n", "max"))
         .sort_values("eur", ascending=False))
say(f"    distinct decisive leaves on the queue: {len(d3sum)}")
for (l3, l1), r in d3sum.iterrows():
    say(f"      {l3[:32]:32s} -> {l1:24s} rows={int(r['rows']):3d} EUR={r['eur']:11,.2f} master_parts={int(r['n'])}")

say("")
say("  the ambiguous leaves the queue lands on:")
ambq = (q[q["path"].notna() & ~q["wb_l3_single"]].groupby(["g_l3", "wb_l1_l3"])
        .agg(rows=("pn", "size"), eur=("pr00_value_eur", "sum")).sort_values("eur", ascending=False))
for (l3, l1), r in ambq.head(40).iterrows():
    sub = j[j["g_l3"] == l3]; dist = sub["aim_l1"].value_counts()
    say(f"      {l3[:30]:30s} modal={str(l1)[:20]:20s} rows={int(r['rows']):3d} EUR={r['eur']:10,.2f} "
        f"| {dict(list(dist.items())[:4])}")

q.to_csv(OUT / "queue_workbook_scored.csv", index=False, encoding="utf-8-sig")
t3.to_csv(OUT / "l3_to_family_purity.csv")
(OUT / "run_log6.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE6")
