"""Tier analysis, part 3 -- build the actual tier split.

Independent evidence = aim_pn_classification.csv rows coming from the EPC /
catalogue route (aim_source = pr00_catalog), joined to the price flat file for
description and commodity code. The master's own aim_workbook rows are the
description-route product, so they are used only as a cross-check.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

pd.set_option("display.width", 300)
pd.set_option("display.max_columns", 60)

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
    line = " ".join(str(v) for v in a)
    print(line); log.append(line)

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

# ------------------------------------------------------------------ inputs
flat = pd.read_csv(FLAT, dtype=str, low_memory=False)
flat["pn"] = norm_pn(flat["pn"]); flat["hs"] = hs_key(flat["hs_code"])
flat["desc_norm"] = norm_desc(flat["description"])
flat = flat.drop_duplicates("pn", keep="first")

cf = pd.read_csv(CLASSIF, dtype=str, low_memory=False)
cf["pn"] = norm_pn(cf["part_number"])
cf["known"] = cf["aim_l1"].map(is_known)
cf = cf.merge(flat[["pn", "desc_norm", "hs", "description", "price_eur"]], on="pn", how="left")
cf["desc_norm"] = cf["desc_norm"].fillna(norm_desc(cf["description_norm"]))

say("=" * 78)
say("A. THE TWO EVIDENCE BASES")
say(f"  classification file rows            : {len(cf):,}")
say(f"  of which real aim_l1                : {cf['known'].sum():,}")
say("  classification file aim_source x vocabulary check:")
cfk = cf[cf["known"]].copy()
cfk["axes"] = np.where(cfk["aim_source"] == "pr00_catalog", "pr00_catalog", cfk["aim_source"].fillna("(blank)"))
for src, sub in cfk.groupby("axes"):
    top = sub["aim_l1"].value_counts().head(6)
    say(f"    {src:16s} n={len(sub):7,d} distinct L1={sub['aim_l1'].nunique():3d}  top: {dict(top)}")

epc = cfk[cfk["aim_source"] == "pr00_catalog"].copy()
say("")
say(f"  INDEPENDENT BASIS (aim_source=pr00_catalog): {len(epc):,} rows")
say(f"    with a description : {epc['desc_norm'].notna().sum():,}")
say(f"    with an HS code    : {(epc['hs'].notna() & (epc['hs'] != '')).sum():,}")
say(f"    vocabulary         : {epc['aim_l1'].nunique()} families")

m = pd.read_csv(MASTER, dtype=str, low_memory=False)
m["pn"] = norm_pn(m["part_number"]); m = m.drop_duplicates("pn", keep="first")
m["known"] = m["aim_l1"].map(is_known)
mk = m[m["known"]].copy()
mk["desc_norm"] = norm_desc(mk["description"])
say(f"  CROSS-CHECK BASIS (master_v2 real aim_l1): {len(mk):,} rows, "
    f"{mk['aim_l1'].nunique()} families")

# ------------------------------------------------------------------ purity
def purity_table(df, keycol):
    d = df[(df[keycol].notna()) & (df[keycol] != "")].copy()
    g = d.groupby(keycol)["aim_l1"]
    t = pd.DataFrame({"n_parts": g.size(), "n_l1": g.nunique(),
                      "top_l1": g.agg(lambda s: s.value_counts().index[0]),
                      "top_share": g.agg(lambda s: s.value_counts().iloc[0] / len(s))})
    pred = t["top_l1"].to_dict()
    d["pred"] = d[keycol].map(pred)
    acc = float((d["pred"] == d["aim_l1"]).mean())
    return t, acc, d

say("")
say("=" * 78)
say("B. JOIN-KEY QUALITY, HONESTLY")
for keyname, col in [("commodity code (HS)", "hs"), ("description", "desc_norm")]:
    te, ae, de = purity_table(epc, col)
    tm, am, dm = purity_table(mk, col)
    say(f"  --- {keyname} ---")
    say(f"      EPC basis   : keys={len(te):5,d}  one-L1={(te['n_l1']==1).sum():5,d} "
        f" many-L1={(te['n_l1']>1).sum():5,d} ({(te['n_l1']>1).mean()*100:5.1f}%)  "
        f" median top_share={te['top_share'].median():.3f}  part-level acc={ae:.4f}")
    say(f"      master basis: keys={len(tm):5,d}  one-L1={(tm['n_l1']==1).sum():5,d} "
        f" many-L1={(tm['n_l1']>1).sum():5,d} ({(tm['n_l1']>1).mean()*100:5.1f}%)  "
        f" median top_share={tm['top_share'].median():.3f}  part-level acc={am:.4f}")

te_hs, _, _ = purity_table(epc, "hs")
te_ds, _, _ = purity_table(epc, "desc_norm")
tm_ds, _, _ = purity_table(mk, "desc_norm")
tm_hs, _, _ = purity_table(mk, "hs")

# ---------------------------------------------------------------- the queue
x = pd.read_excel(EXPORT, dtype=str)
x["pn"] = norm_pn(x["Newest P/N"])
x["hs"] = hs_key(x["Commodity Code"])
x["desc_norm"] = norm_desc(x["Description"])
x["list_eur"] = numify(x["Price"]); x["val_eur"] = numify(x["Value"])

q = pd.read_csv(QUEUE, dtype=str, encoding="utf-8-sig")
q["pn"] = norm_pn(q["pn"]); q["hs"] = hs_key(q["Commodity Code"])
q["desc_norm"] = norm_desc(q["Description"])
q["pr00_eur"] = numify(q["pr00_value_eur"]); q["list_eur"] = numify(q["list_eur"])
q["fk"] = q["fig_key"].fillna("").astype(str).str.strip()

say("")
say("=" * 78)
say("C. THE QUEUE AGAINST THE TWO DICTIONARIES")
desc_epc = te_ds["top_l1"].to_dict(); desc_epc_multi = set(te_ds[te_ds["n_l1"] > 1].index)
desc_mst = tm_ds["top_l1"].to_dict(); desc_mst_multi = set(tm_ds[tm_ds["n_l1"] > 1].index)
hs_epc = te_hs["top_l1"].to_dict();  hs_epc_multi = set(te_hs[te_hs["n_l1"] > 1].index)

q["d_epc"] = q["desc_norm"].map(desc_epc)
q["d_mst"] = q["desc_norm"].map(desc_mst)
say(f"  queue rows                                        : {len(q):,}")
say(f"  description already named in the EPC basis        : {q['d_epc'].notna().sum():,}")
say(f"  description already named in the master basis     : {q['d_mst'].notna().sum():,}")
say(f"  description in BOTH, agreeing                     : "
    f"{int((q['d_epc'].notna() & q['d_mst'].notna() & (q['d_epc']==q['d_mst'])).sum()):,}")
say(f"  description in BOTH, DISAGREEING                  : "
    f"{int((q['d_epc'].notna() & q['d_mst'].notna() & (q['d_epc']!=q['d_mst'])).sum()):,}")
dis = q[(q["d_epc"].notna()) & (q["d_mst"].notna()) & (q["d_epc"] != q["d_mst"])]
if len(dis):
    say("    the disagreements (description | EPC says | master says | queue PNs):")
    dd = dis.groupby(["desc_norm", "d_epc", "d_mst"]).agg(pns=("pn", "nunique"), eur=("pr00_eur", "sum")).reset_index()
    for _, r in dd.sort_values("eur", ascending=False).head(25).iterrows():
        say(f"      {r['desc_norm'][:44]:44s} | {r['d_epc'][:22]:22s} | {r['d_mst'][:22]:22s} | "
            f"pcs={r['pns']:3d} eur={r['eur']:,.0f}")

say("")
say(f"  queue descriptions NOT in either dictionary       : "
    f"{int(q[['d_epc','d_mst']].isna().all(axis=1).sum()):,}")
say(f"  queue rows on a contested description (EPC basis) : {q['desc_norm'].isin(desc_epc_multi).sum():,}")
say(f"  queue rows on a contested description (mstr basis): {q['desc_norm'].isin(desc_mst_multi).sum():,}")

# ---------------------------------------------------------- figure key trap
say("")
say("=" * 78)
say("D. FIGURE-KEY TRAP, AND WHERE THIS QUEUE IS EXPOSED")
mk["fk"] = (mk["fig_key"].fillna("").astype(str).str.strip())
fk_pur = purity_table(mk, "fk")[0]
say(f"  master fig_keys: {len(fk_pur):,}  one-L1={(fk_pur['n_l1']==1).sum():,}  "
    f"many-L1={(fk_pur['n_l1']>1).sum():,} ({(fk_pur['n_l1']>1).mean()*100:.2f}%)")
bad_fk = fk_pur[(fk_pur["n_l1"] > 1)].sort_values("n_parts", ascending=False)
say("  the worst fig_keys (many families behind one key):")
for k, r in bad_fk.head(12).iterrows():
    say(f"      {k:10s} parts={r['n_parts']:4d} L1s={r['n_l1']:3d} top={r['top_share']:.2f} {r['top_l1']}")
qfk = set(q["fk"]) - {""}
hit_bad = qfk & set(bad_fk.index)
say(f"  fig_keys used by the queue that are multi-family : {len(hit_bad)} "
    f"covering {q[q['fk'].isin(hit_bad)]['pn'].nunique():,} queue PNs")
say("  the two cases the audit names:")
for fk in ["220-001", "011-001"]:
    sub = mk[mk["fk"] == fk]
    d = sub["aim_l1"].value_counts()
    say(f"      {fk}: {len(sub)} parts -> {dict(d)}")
    e = sub.head(2)
    for _, r in e.iterrows():
        say(f"          {r['pn']}  {str(r['description'])[:38]:38s} -> {r['aim_l1']} > {r['aim_l2']} > {r['aim_l3']}")
say(f"  queue rows sitting on 220-001: {int((q['fk']=='220-001').sum())}  "
    f"on 011-001: {int((q['fk']=='011-001').sum())}")
for fk in ["220-001", "011-001"]:
    sub = q[q["fk"] == fk]
    for _, r in sub.iterrows():
        say(f"      queue {r['pn']}  {str(r['Description'])[:36]:36s} fk={fk} "
            f"list={r['list_eur']:,.2f} value={r['pr00_eur']:,.2f}")

(OUT / "run_log3.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE3")
