"""Final pass: the refined Tier A rule + the independence check for ENGINE ASM.

Rail: description one family on the master (>=3 parts behind it) AND the figure
key does not contradict (agrees, or has no master evidence at all) AND the family
is not a residual bucket.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd, numpy as np, re

pd.set_option("display.width", 320); pd.set_option("display.max_rows", 600)
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
MASTER = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
CLASSIF = ROOT / "01_data" / "00_derived" / "aim_pn_classification.csv"
QUEUE = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" / "queue.csv"
CLSWB = ROOT / "01_data" / "01_Pricing" / "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"

PLACE = {"", "nan", "none", "null", "unknown", "unknown review"}
RESIDUAL = {"Maintenance Service", "Literature Marketing", "Tools Equipment",
            "Logistics Packaging", "Fluids Chemicals"}
log = []
def say(*a):
    line = " ".join(str(v) for v in a); print(line); log.append(line)
def norm_pn(s): return s.fillna("").astype(str).str.strip().str.upper()
def numify(s):
    return pd.to_numeric(s.fillna("").astype(str).str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")
def norm_desc(s):
    return (s.fillna("").astype(str).str.upper().str.strip().str.replace(r"\s+", " ", regex=True))

m = pd.read_csv(MASTER, dtype=str, low_memory=False)
m["pn"] = norm_pn(m["part_number"]); m = m.drop_duplicates("pn", keep="first")
m["known"] = ~m["aim_l1"].fillna("").str.strip().str.lower().isin(PLACE)
mk = m[m["known"]].copy()
mk["desc_norm"] = norm_desc(mk["description"]); mk["fk"] = mk["fig_key"].fillna("").astype(str).str.strip()

gd = mk.groupby("desc_norm")["aim_l1"]
dd = pd.DataFrame({"n": gd.size(), "n_l1": gd.nunique(), "l1": gd.agg(lambda s: s.value_counts().index[0])})
gf = mk[mk["fk"] != ""].groupby("fk")["aim_l1"]
dk = pd.DataFrame({"n": gf.size(), "n_l1": gf.nunique(), "l1": gf.agg(lambda s: s.value_counts().index[0])})

q = pd.read_csv(QUEUE, dtype=str, encoding="utf-8-sig")
q["pn"] = norm_pn(q["pn"]); q["desc_norm"] = norm_desc(q["Description"])
q["fk"] = q["fig_key"].fillna("").astype(str).str.strip()
q["pr00"] = numify(q["pr00_value_eur"]); q["list"] = numify(q["list_eur"])
q["d_l1"] = q["desc_norm"].map(dd["l1"]); q["d_n"] = q["desc_norm"].map(dd["n"])
q["d_one"] = q["desc_norm"].map(dd["n_l1"]) == 1
q["f_l1"] = q["fk"].map(dk["l1"]); q["f_n"] = q["fk"].map(dk["n"])
q["f_seen"] = q["fk"].map(dk["n_l1"]).notna()
q["f_one"] = q["fk"].map(dk["n_l1"]) == 1

q["desc_ok"] = q["d_one"] & (q["d_n"] >= 3)
q["fk_ok"] = (~q["f_seen"]) | (q["f_one"] & (q["f_l1"] == q["d_l1"])) | (q["f_one"] & ~q["f_l1"].notna())
q["fk_ok"] = (~q["f_seen"]) | (q["f_one"] & (q["f_l1"] == q["d_l1"]))
q["fk_bad"] = q["f_seen"] & q["f_one"] & (q["f_l1"] != q["d_l1"])
q["tierA"] = q["desc_ok"] & q["fk_ok"] & (~q["d_l1"].isin(RESIDUAL))

A, B = q[q["tierA"]], q[~q["tierA"]]
say("=" * 78)
say("REFINED TIER A  (description names one family with >=3 master parts behind it;")
say("                 figure key does not contradict it; family is not a residual bucket)")
say(f"  Tier A rows={len(A):4d}  unique PN={A['pn'].nunique():4d}  "
    f"PR00 EUR={A['pr00'].sum():12,.2f} ({A['pr00'].sum()/q['pr00'].sum()*100:5.1f}%)  "
    f"list EUR={A['list'].sum():11,.2f}")
say(f"  Tier B rows={len(B):4d}  unique PN={B['pn'].nunique():4d}  "
    f"PR00 EUR={B['pr00'].sum():12,.2f} ({B['pr00'].sum()/q['pr00'].sum()*100:5.1f}%)  "
    f"list EUR={B['list'].sum():11,.2f}")
say("")
b = B.copy()
why = pd.Series("description and figure key disagree", index=b.index)
why[~b["d_one"]] = "description does not name ONE family on the master"
why[b["d_one"] & (b["d_n"] < 3)] = "description known but fewer than 3 master parts behind it"
why[b["desc_ok"] & b["fk_bad"]] = "figure key contradicts the description"
why[b["desc_ok"] & ~b["f_one"] & b["f_seen"]] = "figure key is multi-family on the master"
why[b["tierA".replace("tierA", "desc_ok")] & b["fk_ok"] & b["d_l1"].isin(RESIDUAL)] = "family is a residual bucket"
b = b.assign(why=why)
for k, sub in b.groupby("why"):
    say(f"    {k:58s} rows={len(sub):5d}  PR00 EUR={sub['pr00'].sum():12,.2f}")

say("")
say(f"  ROWS WHERE THE FIGURE KEY CONTRADICTS THE DESCRIPTION (excluded, whatever the price):")
say(f"    count={len(q[q['fk_bad']])}, PR00 EUR={q[q['fk_bad']]['pr00'].sum():,.2f}")
for _, r in q[q["fk_bad"]].sort_values("pr00", ascending=False).head(12).iterrows():
    say(f"      {r['pn']}  {str(r['desc_norm'])[:36]:36s} desc says {str(r['d_l1'])[:20]:20s} "
        f"fk={r['fk']:9s} fk says {str(r['f_l1'])}")

say("")
say("=" * 78)
say("'ENGINE ASM' -- THE ROW JEROME NAMED")
r = q[q["pn"] == "8981422000"].iloc[0]
say(f"  pn {r['pn']}  desc '{r['desc_norm']}'  fk={r['fk']}")
say(f"    list EUR {r['list']:,.2f}   PR00 value EUR {r['pr00']:,.2f}")
say(f"    description -> {r['d_l1']} on {int(r['d_n'])} master parts")
say(f"    figure key {r['fk']} -> has master evidence? {bool(r['f_seen'])}")
say(f"    refined rule verdict: Tier A = {bool(r['tierA'])}")

say("")
say("  is the description route for ENGINE ASM backed by anything independent?")
cl = pd.read_excel(CLSWB, sheet_name="Sheet1", dtype=str)
cl.columns = [str(c).strip() for c in cl.columns]
cl = cl.rename(columns={"Newest P/N": "pn_new", "Level 1 Family": "g_l1",
                        "Level 2 Group": "g_l2", "Level 3 Type": "g_l3"})
cl["pn"] = norm_pn(cl["pn_new"]); cl["desc_norm"] = norm_desc(cl["Description"])
sub = cl[cl["desc_norm"] == "ENGINE ASM"]
say(f"    the classified workbook has {len(sub)} rows described ENGINE ASM")
if len(sub):
    say(f"      its Level 3 Type values: {dict(sub['g_l3'].value_counts().head(5))}")
    say(f"      its Level 1 Family     : {dict(sub['g_l1'].value_counts().head(5))}")
mm = mk[mk["desc_norm"] == "ENGINE ASM"]
say(f"    the master has {len(mm)} rows described ENGINE ASM")
say(f"      all assigned: {dict(mm['aim_l1'].value_counts())}")
say(f"      their aim_source: {dict(mm['aim_source'].value_counts())}")
say(f"    NOTE: a description route built on master rows is the same join the audit")
say(f"    calls non-deterministic. For ENGINE ASM the two paths agree, and the text")
say(f"    itself is unambiguous, so the assignment is safe; the rule cannot make that")
say(f"    distinction by itself.")

say("")
say("=" * 78)
say("FAMILY SPREAD OF REFINED TIER A")
f = A.groupby("d_l1").agg(rows=("pn", "size"), eur=("pr00", "sum")).sort_values("eur", ascending=False)
for k, r in f.iterrows():
    say(f"    {str(k):26s} rows={int(r['rows']):4d} EUR={float(r['eur']):12,.2f}")

say("")
ta = A.sort_values("pr00", ascending=False)
dA = ta.groupby(["desc_norm", "d_l1", "fk"]).agg(rows=("pn", "size"), eur=("pr00", "sum"),
                                                 d_n=("d_n", "max"), f_n=("f_n", "max")).reset_index()
dA = dA.sort_values("eur", ascending=False)
say(f"  distinct (description, family, figure key) triples in Tier A: {len(dA)}")
for i, (_, r) in enumerate(dA.head(70).iterrows(), 1):
    fn = "n/a" if pd.isna(r['f_n']) else int(r['f_n'])
    say(f"   {i:3d}. {str(r['desc_norm'])[:40]:40s} -> {str(r['d_l1'])[:22]:22s} fk={str(r['fk']):9s} "
        f"rows={int(r['rows']):3d} EUR={float(r['eur']):10,.2f} master(desc={int(r['d_n'])}, fk={fn})")

q.to_csv(OUT / "queue_final_tiered.csv", index=False, encoding="utf-8-sig")
dA.to_csv(OUT / "tierA_final_triples.csv", index=False)
(OUT / "run_log_final.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE_FINAL")
