"""Narrow, defensible Tier A.

Three independent-ish signals must agree before a row leaves the scraper:
  1. the exact description already carries ONE family on the master, with >=3 parts
  2. the figure key already carries the SAME family on the master, with >=3 parts
  3. the row is not assigned to a residual / non-parts family
Then every surviving triple is printed for hand audit.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

pd.set_option("display.width", 320); pd.set_option("display.max_rows", 500)
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
QUEUE = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" / "queue.csv"
MASTER = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
CLSWB = ROOT / "01_data" / "01_Pricing" / "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"

PLACE = {"", "nan", "none", "null", "unknown", "unknown review"}
RESIDUAL = {"Maintenance Service", "Literature Marketing", "Tools Equipment",
            "Logistics Packaging", "Fluids Chemicals"}

def say(*a):
    line = " ".join(str(v) for v in a); print(line); log.append(line)
def norm_pn(s): return s.fillna("").astype(str).str.strip().str.upper()
def numify(s):
    return pd.to_numeric(s.fillna("").astype(str).str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False).str.replace(",", ".", regex=False), errors="coerce")
def norm_desc(s):
    return (s.fillna("").astype(str).str.upper().str.strip().str.replace(r"\s+", " ", regex=True))
log = []

m = pd.read_csv(MASTER, dtype=str, low_memory=False)
m["pn"] = norm_pn(m["part_number"]); m = m.drop_duplicates("pn", keep="first")
m["known"] = ~m["aim_l1"].fillna("").str.strip().str.lower().isin(PLACE)
mk = m[m["known"]].copy()
mk["desc_norm"] = norm_desc(mk["description"])
mk["fk"] = mk["fig_key"].fillna("").astype(str).str.strip()

g = mk.groupby("desc_norm")["aim_l1"]
dd = pd.DataFrame({"n": g.size(), "n_l1": g.nunique(), "l1": g.agg(lambda s: s.value_counts().index[0])})
g2 = mk[mk["fk"] != ""].groupby("fk")["aim_l1"]
dk = pd.DataFrame({"n": g2.size(), "n_l1": g2.nunique(), "l1": g2.agg(lambda s: s.value_counts().index[0])})

q = pd.read_csv(QUEUE, dtype=str, encoding="utf-8-sig")
q["pn"] = norm_pn(q["pn"]); q["desc_norm"] = norm_desc(q["Description"])
q["fk"] = q["fig_key"].fillna("").astype(str).str.strip()
q["pr00"] = numify(q["pr00_value_eur"]); q["list"] = numify(q["list_eur"])
q = q.merge(m[["pn", "aim_l1", "cat_l1"]].rename(columns={"aim_l1": "m_l1"}), on="pn", how="left")

q["d_l1"] = q["desc_norm"].map(dd["l1"]); q["d_n"] = q["desc_norm"].map(dd["n"])
q["d_one"] = q["desc_norm"].map(dd["n_l1"]) == 1
q["f_l1"] = q["fk"].map(dk["l1"]); q["f_n"] = q["fk"].map(dk["n"])
q["f_one"] = q["fk"].map(dk["n_l1"]) == 1

q["agree"] = q["d_one"] & q["f_one"] & (q["d_l1"] == q["f_l1"])
q["strict"] = q["agree"] & (q["d_n"] >= 3) & (q["f_n"] >= 3) & (~q["d_l1"].isin(RESIDUAL))

say("=" * 78)
say("STRICT TIER A  (description one family >=3 parts, fig key same family >=3 parts,")
say("                family is not a residual bucket)")
A = q[q["strict"]]
B = q[~q["strict"]]
say(f"  Tier A rows={len(A):4d}  unique PN={A['pn'].nunique():4d}  PR00 EUR={A['pr00'].sum():12,.2f} "
    f"({A['pr00'].sum()/q['pr00'].sum()*100:5.1f}%)  list EUR={A['list'].sum():11,.2f}")
say(f"  Tier B rows={len(B):4d}  unique PN={B['pn'].nunique():4d}  PR00 EUR={B['pr00'].sum():12,.2f} "
    f"({B['pr00'].sum()/q['pr00'].sum()*100:5.1f}%)  list EUR={B['list'].sum():11,.2f}")

say("")
say("  WHY EACH ROW IS IN TIER B:")
b = B.copy()
why = pd.Series("description and fig_key disagree", index=b.index)
why[~b["d_one"]] = "description does not name one family on the master"
why[b["d_one"] & ~b["f_one"]] = "fig_key does not name one family on the master"
why[b["agree"] & (b["d_n"] < 3)] = "fewer than 3 master parts behind the description"
why[b["agree"] & (b["f_n"] < 3)] = "fewer than 3 master parts behind the fig_key"
why[b["agree"] & (b["d_l1"].isin(RESIDUAL))] = "family is a residual bucket"
b = b.assign(why=why)
for k, sub in b.groupby("why"):
    say(f"    {k:56s} rows={len(sub):5d}  PR00 EUR={sub['pr00'].sum():12,.2f}")

say("")
say("=" * 78)
say("EVERY STRICT TIER A TRIPLE, FOR HAND AUDIT")
dA = (A.groupby(["desc_norm", "d_l1", "fk"])
      .agg(rows=("pn", "size"), eur=("pr00", "sum"), d_n=("d_n", "max"), f_n=("f_n", "max"))
      .reset_index().sort_values("eur", ascending=False))
say(f"  triples: {len(dA)}   rows: {len(A)}   EUR {A['pr00'].sum():,.2f}")
for i, (_, r) in enumerate(dA.iterrows(), 1):
    say(f"  {i:3d}. {str(r['desc_norm'])[:42]:42s} -> {str(r['d_l1'])[:22]:22s} "
        f"fk={str(r['fk']):9s} rows={int(r['rows']):3d} EUR={float(r['eur']):10,.2f} "
        f"master(desc={int(r['d_n'])}, fk={int(r['f_n'])})")

say("")
say("=" * 78)
say("RESIDUAL-BUCKET ROWS THE STRICT RULE EXCLUDED (the ones that looked decidable)")
res = q[q["agree"] & (q["d_n"] >= 3) & (q["f_n"] >= 3) & (q["d_l1"].isin(RESIDUAL))]
for _, r in res.sort_values("pr00", ascending=False).iterrows():
    say(f"    {r['pn']}  {str(r['desc_norm'])[:38]:38s} -> {r['d_l1']:22s} "
        f"fk={r['fk']:9s} list={r['list']:10,.2f} pr00={r['pr00']:10,.2f}")

q.to_csv(OUT / "queue_strict_tiered.csv", index=False, encoding="utf-8-sig")
(OUT / "tierA_strict.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE8")
