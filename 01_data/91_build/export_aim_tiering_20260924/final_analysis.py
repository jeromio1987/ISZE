"""Final analysis: the defensible tier split for the 1,311 queue rows.

Evidence base = parts that already carry a real aim_l1 on aim_master_v2.csv
(the only source of the 21-family system vocabulary). Cross-checks come from
the independent classification file and the price flat file.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

pd.set_option("display.width", 320)
pd.set_option("display.max_columns", 80)
pd.set_option("display.max_rows", 400)

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
FLAT = ROOT / "01_data" / "00_derived" / "_audit_cls_pr00_flat.csv"
MASTER = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
CLASSIF = ROOT / "01_data" / "00_derived" / "aim_pn_classification.csv"
QUEUE = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" / "queue.csv"
EXPORT = ROOT / "01_data" / "EXPORT.XLSX"

PLACEHOLDERS = {"", "nan", "none", "null", "unknown", "unknown review"}
log = []
def say(*a):
    line = " ".join(str(v) for v in a); print(line); log.append(line)

def norm_pn(s): return s.fillna("").astype(str).str.strip().str.upper()
def hs_key(s):
    return (s.fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
            .str.replace("\u00a0", "", regex=False).str.replace(" ", "", regex=False))
def numify(s):
    return pd.to_numeric(s.fillna("").astype(str).str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")
def norm_desc(s):
    return (s.fillna("").astype(str).str.upper().str.strip().str.replace(r"\s+", " ", regex=True))
def is_known(l1): return str(l1 or "").strip().lower() not in PLACEHOLDERS

# ------------------------------------------------------------- 0. price parse
x = pd.read_excel(EXPORT, dtype=str)
bad = x["Price"].dropna().astype(str)[
    x["Price"].dropna().astype(str).str.contains(r"\.", regex=True) &
    x["Price"].dropna().astype(str).str.contains(",", regex=False)]
say("=" * 78)
say("0. PRICE COLUMN")
say(f"  values with BOTH '.' and ',' (ambiguous): {len(bad)}")
if len(bad): say(f"    examples: {bad.head(5).tolist()}")
say(f"  list-price parse: rows={numify(x['Price']).notna().sum()}, sum EUR={numify(x['Price']).sum():,.2f}")
say(f"  'Value' column  : rows={numify(x['Value']).notna().sum()}, sum EUR={numify(x['Value']).sum():,.2f}")

# ------------------------------------------------------------------ 1. inputs
flat = pd.read_csv(FLAT, dtype=str, low_memory=False)
flat["pn"] = norm_pn(flat["pn"]); flat["hs"] = hs_key(flat["hs_code"])
flat["desc_norm"] = norm_desc(flat["description"])
flat = flat.drop_duplicates("pn", keep="first")

m = pd.read_csv(MASTER, dtype=str, low_memory=False)
m["pn"] = norm_pn(m["part_number"]); m = m.drop_duplicates("pn", keep="first")
m["known"] = m["aim_l1"].map(is_known)
mk = m[m["known"]].copy()
mk["desc_norm"] = norm_desc(mk["description"])
mk["fk"] = mk["fig_key"].fillna("").astype(str).str.strip()

q = pd.read_csv(QUEUE, dtype=str, encoding="utf-8-sig")
q["pn"] = norm_pn(q["pn"]); q["hs"] = hs_key(q["Commodity Code"])
q["desc_norm"] = norm_desc(q["Description"])
q["pr00_eur"] = numify(q["pr00_value_eur"]); q["list_eur"] = numify(q["list_eur"])
q["fk"] = q["fig_key"].fillna("").astype(str).str.strip()

say("")
say("=" * 78)
say("1. QUEUE BASELINE")
say(f"  queue rows              : {len(q):,}")
say(f"  queue unique Newest P/N : {q['pn'].nunique():,}")
say(f"  queue rows with HS code : {int((q['hs'] != '').sum()):,}")
say(f"  queue rows with fig_key : {int((q['fk'] != '').sum()):,}")
say(f"  queue PR00 EUR (rows)   : {q['pr00_eur'].sum():,.2f}")
say(f"  queue PR00 EUR (dedup)  : {q.drop_duplicates('pn')['pr00_eur'].sum():,.2f}")
say(f"  queue list-price EUR    : {q['list_eur'].sum():,.2f}")

# --------------------------------------------- 2. description dictionary
grp = mk.groupby("desc_norm")["aim_l1"]
dd = pd.DataFrame({"n_parts": grp.size(), "n_l1": grp.nunique(),
                   "top_l1": grp.agg(lambda s: s.value_counts().index[0]),
                   "top_share": grp.agg(lambda s: s.value_counts().iloc[0] / len(s))})
say("")
say("=" * 78)
say("2. DESCRIPTION -> ONE FAMILY?  (master evidence, %d rows)" % len(mk))
say(f"  distinct descriptions          : {len(dd):,}")
say(f"  map to exactly ONE family      : {(dd['n_l1']==1).sum():,} ({(dd['n_l1']==1).mean()*100:.2f}%)")
say(f"  map to MORE THAN ONE family    : {(dd['n_l1']>1).sum():,} ({(dd['n_l1']>1).mean()*100:.2f}%)")
say("  the contested ones, listed:")
cont = dd[dd["n_l1"] > 1].sort_values("n_parts", ascending=False)
for k, r in cont.iterrows():
    sub = mk[mk["desc_norm"] == k]
    dist = sub["aim_l1"].value_counts()
    say(f"    {k[:46]:46s} n={r['n_parts']:4d} L1s={r['n_l1']:2d} | "
        + " | ".join(f"{a}={b}" for a, b in list(dist.items())[:5]))
say("")
say(f"  *** the audit reported 71 contested descriptions on its own basis;")
say(f"      on the current master the count is {(dd['n_l1']>1).sum()}. Report both.")

# --------------------------------------------------- 3. fig key dictionary
gfk = mk[mk["fk"] != ""].groupby("fk")["aim_l1"]
dk = pd.DataFrame({"n_parts": gfk.size(), "n_l1": gfk.nunique(),
                   "top_l1": gfk.agg(lambda s: s.value_counts().index[0]),
                   "top_share": gfk.agg(lambda s: s.value_counts().iloc[0] / len(s))})
say("")
say("=" * 78)
say("3. FIGURE KEY -> ONE FAMILY?  (master evidence)")
say(f"  distinct fig_keys              : {len(dk):,}")
say(f"  map to exactly ONE family      : {(dk['n_l1']==1).sum():,} ({(dk['n_l1']==1).mean()*100:.2f}%)")
say(f"  map to MORE THAN ONE family    : {(dk['n_l1']>1).sum():,} ({(dk['n_l1']>1).mean()*100:.2f}%)")
say("  fig_keys used by the queue that are multi-family:")
qfk = set(q["fk"]) - {""}
bad = dk[(dk.index.isin(qfk)) & (dk["n_l1"] > 1)].sort_values("n_parts", ascending=False)
for k, r in bad.iterrows():
    sub = mk[mk["fk"] == k]; dist = sub["aim_l1"].value_counts()
    nq = int((q["fk"] == k).sum())
    say(f"    {k:10s} queue={nq:3d} master={r['n_parts']:4d} L1s={r['n_l1']:2d} | "
        + " | ".join(f"{a}={b}" for a, b in list(dist.items())[:4]))
say("")
say("  THE DOCUMENTED TRAP, REPRODUCED ON THE QUEUE's OWN FIG KEYS:")
for fk in ["220-001", "011-001"]:
    sub = mk[mk["fk"] == fk]; dist = sub["aim_l1"].value_counts()
    say(f"    fig_key {fk}: master {len(sub)} parts -> {dict(dist)}")
    for _, r in sub.head(3).iterrows():
        say(f"        {r['pn']}  {str(r['description'])[:40]:40s} -> {r['aim_l1']} > {r['aim_l2']} > {r['aim_l3']}")
    for _, r in q[q["fk"] == fk].iterrows():
        say(f"        QUEUE {r['pn']}  {str(r['Description'])[:36]:36s} "
            f"list={r['list_eur']:,.2f} pr00={r['pr00_eur']:,.2f}  <-- this row")

# ------------------------------------------- 4. cross-check dictionaries
cf = pd.read_csv(CLASSIF, dtype=str, low_memory=False)
cf["pn"] = norm_pn(cf["part_number"])
cf["known"] = cf["aim_l1"].map(is_known)
cf = cf.merge(flat[["pn", "desc_norm"]], on="pn", how="left")
cf["desc_norm"] = cf["desc_norm"].fillna(norm_desc(cf["description_norm"]))
cfk = cf[cf["known"]]
g2 = cfk.groupby("desc_norm")["aim_l1"]
dc = pd.DataFrame({"n_parts": g2.size(), "n_l1": g2.nunique(),
                   "top_l1": g2.agg(lambda s: s.value_counts().index[0])})
say("")
say("=" * 78)
say("4. CROSS-CHECK: the same test on the independent classification file")
say(f"  classified rows                 : {len(cfk):,}")
say(f"  distinct descriptions           : {len(dc):,}")
say(f"  map to MORE THAN ONE family     : {(dc['n_l1']>1).sum():,} ({(dc['n_l1']>1).mean()*100:.2f}%)")

# --------------------------------------------------------- 5. the tier split
d_map = dd["top_l1"].to_dict()
d_one = set(dd[dd["n_l1"] == 1].index)
fk_map = dk["top_l1"].to_dict()
fk_one = set(dk[dk["n_l1"] == 1].index)

q["d_l1"] = q["desc_norm"].map(d_map)
q["fk_l1"] = q["fk"].map(fk_map)
q["d_single"] = q["desc_norm"].isin(d_one)
q["fk_single"] = q["fk"].isin(fk_one)
q["d_n"] = q["desc_norm"].map(dd["n_parts"]).fillna(0).astype(int)
q["d_seen"] = q["d_l1"].notna()

TEXT_RULES = [
    ("ENGINE ASM",                     r"^ENGINE ASM\b"),
    ("CAB ASM",                        r"^CAB ASM\b"),
    ("TURBOCHARGER",                   r"^TURBOCHARGER"),
    ("TRANSFER ASM",                   r"^TRANSFER ASM\b"),
    ("MOTOR ASM; REAR DRIVE",          r"^MOTOR ASM; REAR DRIVE"),
    ("STEERING UNIT",                  r"^STEERING UNIT\b"),
    ("DISC; CLUTCH",                   r"^DISC; CLUTCH\b"),
    ("HEAD ASM; CYL",                  r"^HEAD ASM; CYL\b"),
    ("TRANSMISSION ASM; MANUAL",       r"^TRANSMISSION ASM; MANUAL$"),
    ("MASTER VAC ASM; BRK",            r"^MASTER VAC ASM; BRK"),
    ("COOLER ASM; FUEL",               r"^COOLER ASM; FUEL"),
    ("HYDRAULIC UNIT; ANTI LOCK BRK",  r"^HYDRAULIC UNIT; ANTI LOCK BRK"),
]
import re
for name, pat in TEXT_RULES:
    q[f"t_{name}"] = q["desc_norm"].str.match(pat).fillna(False)

say("")
say("=" * 78)
say("5. THE TIER SPLIT")
say("   Tier A = description names exactly one family in the master evidence")
say("            AND that evidence has >=2 parts behind it AND the fig_key is not")
say("            one of the contested keys (a double signal, description + fig key).")
say("   Tier B = everything else.")

q["agree"] = q["d_single"] & q["fk_single"] & q["d_seen"] & (q["d_l1"] == q["fk_l1"])
q["tierA"] = q["agree"] & (q["d_n"] >= 2)
q["tierB"] = ~q["tierA"]

for tee, sub in [("A", q[q["tierA"]]), ("B", q[q["tierB"]])]:
    say(f"  Tier {tee}: rows={len(sub):5,d}  unique PN={sub['pn'].nunique():5,d}  "
        f"PR00 EUR={sub['pr00_eur'].sum():14,.2f}  list EUR={sub['list_eur'].sum():12,.2f}  "
        f"({sub['pr00_eur'].sum()/q['pr00_eur'].sum()*100:5.1f}% of PR00 EUR)")
say("")
say("  Tier B, broken down by why:")
b = q[q["tierB"]]
why = pd.Series("other", index=b.index)
why[~b["d_seen"]] = "description not in the master evidence at all"
why[b["d_seen"] & ~b["d_single"]] = "description maps to more than one family"
why[b["d_seen"] & b["d_single"] & ~b["fk_single"]] = "fig_key is a contested key"
why[b["d_seen"] & b["d_single"] & b["fk_single"] & (b["d_l1"] != b["fk_l1"])] = "description and fig_key disagree"
why[b["agree"] & (b["d_n"] < 2)] = "description known but only one master part behind it"
bb = b.assign(why=why)
for k, sub in bb.groupby("why"):
    say(f"    {k:52s} rows={len(sub):5,d}  PR00 EUR={sub['pr00_eur'].sum():13,.2f}")

say("")
say("  --- Tier A: the description rules that do the work ---")
dsum = (q[q["tierA"]].groupby(["desc_norm", "d_l1"]).agg(rows=("pn", "size"), eur=("pr00_eur", "sum"))
        .sort_values("eur", ascending=False))
say(f"    distinct Tier A descriptions: {len(dsum)}")
for (d, l1), r in dsum.head(60).iterrows():
    say(f"    {str(d)[:44]:44s} -> {str(l1):26s} rows={int(r['rows']):3d} EUR={float(r['eur']):12,.2f}")

say("")
say("  --- Tier A: sample of descriptions NOT carrying a text rule (the risk) ---")
q_a = q[q["tierA"]].copy()
q_a["text_hit"] = q_a[[c for c in q_a.columns if c.startswith("t_")]].any(axis=1)
say(f"    Tier A rows with an obvious system word in the description : {int(q_a['text_hit'].sum())}")
say(f"    Tier A rows WITHOUT one                                    : {int((~q_a['text_hit']).sum())}")
noText = q_a[~q_a["text_hit"]].groupby(["desc_norm", "d_l1", "fk"]).agg(
    rows=("pn", "size"), eur=("pr00_eur", "sum"), d_n=("d_n", "max")).sort_values("eur", ascending=False)
say("    (description | family assigned | fig_key | rows | EUR | master parts behind)")
for _, r in noText.head(40).iterrows():
    say(f"      {str(r.name[0])[:40]:40s} | {str(r.name[1])[:24]:24s} | {str(r.name[2]):9s} | "
        f"{int(r['rows']):3d} | {float(r['eur']):10,.2f} | {int(r['d_n'])}")

q.to_csv(OUT / "queue_tiered.csv", index=False, encoding="utf-8-sig")
dsum.to_csv(OUT / "tierA_descriptions.csv")
(OUT / "run_log4.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE4")
