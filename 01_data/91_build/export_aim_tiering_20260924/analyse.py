"""Tier analysis for the IE40 AIM queue -- read-only.

Measures whether Commodity Code and/or Description can name an AIM family on
their own, using the parts that are ALREADY classified as evidence.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_tiering_20260924"
EXPORT = ROOT / "01_data" / "EXPORT.XLSX"
QUEUE = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924" / "queue.csv"
MASTER = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
CLASSIF = ROOT / "01_data" / "00_derived" / "aim_pn_classification.csv"
FLAT = ROOT / "01_data" / "00_derived" / "_audit_cls_pr00_flat.csv"

PLACEHOLDERS = {"", "nan", "none", "null", "unknown", "unknown review"}


def norm_pn(s):
    return s.fillna("").astype(str).str.strip().str.upper()


def hs_key(s):
    return (s.fillna("").astype(str).str.strip()
            .str.replace(r"\.0$", "", regex=True)
            .str.replace("\u00a0", "", regex=False)
            .str.replace(" ", "", regex=False))


def numify(s):
    return pd.to_numeric(
        s.fillna("").astype(str)
        .str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce")


def norm_desc(s):
    return (s.fillna("").astype(str).str.upper().str.strip()
            .str.replace(r"\s+", " ", regex=True))


def is_known(l1):
    return str(l1 or "").strip().lower() not in PLACEHOLDERS


log = []
def say(*a):
    line = " ".join(str(v) for v in a)
    print(line)
    log.append(line)


# ---------------------------------------------------------------- load
x = pd.read_excel(EXPORT, dtype=str)
x["pn"] = norm_pn(x["Newest P/N"])
x["hs"] = hs_key(x["Commodity Code"])
x["list_eur"] = numify(x["Price"])
x["pr00_eur"] = numify(x["Value"])
x["desc_norm"] = norm_desc(x["Description"])

q = pd.read_csv(QUEUE, dtype=str, encoding="utf-8-sig")
q["pn"] = norm_pn(q["pn"])
q["hs"] = hs_key(q["Commodity Code"])
q["list_eur"] = numify(q["list_eur"])
q["pr00_eur"] = numify(q["pr00_value_eur"])
q["desc_norm"] = norm_desc(q["Description"])
q["fig_key"] = q["fig_key"].fillna("").astype(str).str.strip()

m = pd.read_csv(MASTER, dtype=str, low_memory=False)
m["pn"] = norm_pn(m["part_number"])
m = m.drop_duplicates("pn", keep="first")
m["known"] = m["aim_l1"].map(is_known)
known = m[m["known"]].copy()
known["desc_norm"] = norm_desc(known["description"])

flat = pd.read_csv(FLAT, dtype=str, low_memory=False)
flat["pn"] = norm_pn(flat["pn"])
flat["hs"] = hs_key(flat["hs_code"])
flat = flat.drop_duplicates("pn", keep="first")

say("=" * 78)
say("BASE")
say(f"  export rows                    : {len(x):,}")
say(f"  export unique Newest P/N       : {x['pn'].nunique():,}")
say(f"  queue rows                     : {len(q):,}")
say(f"  queue unique P/N               : {q['pn'].nunique():,}")
say(f"  master rows                    : {len(m):,}")
say(f"  master rows with real aim_l1   : {len(known):,}")
say(f"  master real l1 AND fig_key     : {known['fig_key'].notna().sum():,}")
say(f"  queue PR00 value EUR           : {q['pr00_eur'].sum():,.2f}")
say(f"  queue PR00 value EUR (dedup PN): {q.drop_duplicates('pn')['pr00_eur'].sum():,.2f}")
say(f"  queue list-price EUR sum       : {q['list_eur'].sum():,.2f}")
say(f"  queue rows with blank HS       : {(q['hs'] == '').sum()}")
say(f"  queue aim_source dist          :")
for k, v in q["cur_aim_source"].fillna("(blank)").value_counts().items():
    say(f"      {k:24s} {v:5d}")
say(f"  master known aim_source dist   :")
for k, v in known["aim_source"].fillna("(blank)").value_counts().items():
    say(f"      {k:24s} {v:5d}")

# ---------------------------------------------------------- HS structure
say("")
say("=" * 78)
say("1. COMMODITY CODE STRUCTURE (the queue)")
hsq = q[q["hs"] != ""].copy()
vc = hsq["hs"].value_counts()
say(f"  distinct HS codes on queue     : {hsq['hs'].nunique()}")
say(f"  queue PNs that carry an HS     : {len(hsq):,}")
say(f"  codes used by exactly 1 PN     : {(vc == 1).sum()}")
say(f"  codes used by >=10 PNs         : {(vc >= 10).sum()}")
say(f"  largest code                   : {vc.index[0]} = {vc.iloc[0]} PNs")
say(f"  HS values are all 10 digits    : {bool((hsq['hs'].str.len() == 10).all())}")
say("  HS chapter (first two digits) distribution on queue:")
for k, v in hsq["hs"].str[:2].value_counts().items():
    say(f"      ch {k}: {v:4d} PNs")

say("")
say("  Top 20 HS codes on the queue, with master purity behind each:")
g = hsq.groupby("hs").agg(pns=("pn", "nunique"), pr00=("pr00_eur", "sum"))
g = g.sort_values("pns", ascending=False).head(20)

# ----------------------------------------------------- HS -> L1 purity
cl_hs = known.merge(flat[["pn", "hs"]], on="pn", how="left")
cl_hs = cl_hs[(cl_hs["hs"].notna()) & (cl_hs["hs"] != "")].copy()
rows = []
for code, grp in cl_hs.groupby("hs"):
    dist = grp["aim_l1"].value_counts()
    rows.append({"hs": code, "n_parts": int(dist.sum()), "n_l1": int(dist.size),
                 "top_l1": dist.index[0], "top_share": round(float(dist.iloc[0] / dist.sum()), 4),
                 "dist": " | ".join(f"{k}={v}" for k, v in dist.head(5).items())})
hsp = pd.DataFrame(rows).sort_values("n_parts", ascending=False)
modal_hs = hsp.set_index("hs")["top_l1"].to_dict()
cl_hs["pred"] = cl_hs["hs"].map(modal_hs)
acc_hs = float((cl_hs["pred"] == cl_hs["aim_l1"]).mean())

say("")
say("=" * 78)
say("2. HS CODE -> AIM L1  (evidence base: master parts that already have a real family)")
say(f"  classified parts carrying an HS : {len(cl_hs):,}")
say(f"  HS codes measured               : {len(hsp)}")
say(f"  codes that map to ONE L1        : {(hsp['n_l1'] == 1).sum()}")
say(f"  codes that map to MORE THAN ONE : {(hsp['n_l1'] > 1).sum()}")
say(f"  codes >=95% one L1              : {(hsp['top_share'] >= 0.95).sum()}")
say(f"  codes >=80% one L1              : {(hsp['top_share'] >= 0.80).sum()}")
say(f"  median top-L1 share             : {hsp['top_share'].median():.3f}")
say(f"  PART-LEVEL accuracy, always picking the modal L1 for the code: {acc_hs:.3f}")
say(f"  --> a commodity code is a chapter-level statement, not a family.")
say("")
say("  HS codes on the queue ranked by queue PNs, with the family spread behind them:")
hsp_q = hsp.copy()
hsp_q["queue_pns"] = hsp_q["hs"].map(vc).fillna(0).astype(int)
hsp_q["queue_pr00"] = hsp_q["hs"].map(g["pr00"]).fillna(0).round(2)
hsp_q = hsp_q[hsp_q["queue_pns"] > 0].sort_values("queue_pns", ascending=False)
for _, r in hsp_q.head(28).iterrows():
    say(f"      {r['hs']}  q={r['queue_pns']:4d}  master={r['n_parts']:5d}  L1s={r['n_l1']:3d} "
        f" top={r['top_share']:.2f} {r['top_l1'][:22]:22s} | {r['dist'][:110]}")

hsp.to_csv(OUT / "hs_to_l1_purity.csv", index=False)
hsp_q.to_csv(OUT / "hs_to_l1_purity_queue.csv", index=False)

# ------------------------------------------- description -> L1 purity
say("")
say("=" * 78)
say("3. DESCRIPTION -> AIM L1")
say("   (a) against the master's own already-classified rows")
known_d = known[known["desc_norm"] != ""].copy()
grp = known_d.groupby("desc_norm")["aim_l1"]
dd_m = pd.DataFrame({
    "n_parts": grp.size(), "n_l1": grp.nunique(),
    "top_l1": grp.agg(lambda s: s.value_counts().index[0]),
    "top_share": grp.agg(lambda s: s.value_counts().iloc[0] / len(s)),
}).reset_index()
modal_d_m = dd_m.set_index("desc_norm")["top_l1"].to_dict()
known_d["pred"] = known_d["desc_norm"].map(modal_d_m)
say(f"    classified parts with a description : {len(known_d):,}")
say(f"    distinct normalised descriptions    : {len(dd_m):,}")
say(f"    descriptions -> ONE L1              : {(dd_m['n_l1'] == 1).sum():,}")
say(f"    descriptions -> MORE THAN ONE L1    : {(dd_m['n_l1'] > 1).sum():,} ({(dd_m['n_l1']>1).mean()*100:.2f}%)")
say(f"    PART-LEVEL accuracy, modal L1 per description: {(known_d['pred']==known_d['aim_l1']).mean():.4f}")
say(f"    CIRCULARITY WARNING: {int((known['aim_source']=='aim_workbook').sum()):,} of the {len(known):,} known rows")
say(f"    were themselves built by a description join, so this number is not independent.")

say("")
say("   (b) against the independent classification file (the audit's own basis)")
cf = pd.read_csv(CLASSIF, dtype=str, low_memory=False)
cf["known"] = cf["aim_l1"].map(is_known)
cfk = cf[cf["known"]].copy()
cfk["desc_norm"] = norm_desc(cfk["description_norm"].where(cfk["description_norm"].notna(), cfk["description"]))
cfk = cfk[cfk["desc_norm"] != ""]
grp2 = cfk.groupby("desc_norm")["aim_l1"]
dd_c = pd.DataFrame({
    "n_parts": grp2.size(), "n_l1": grp2.nunique(),
    "top_l1": grp2.agg(lambda s: s.value_counts().index[0]),
    "top_share": grp2.agg(lambda s: s.value_counts().iloc[0] / len(s)),
}).reset_index()
modal_d_c = dd_c.set_index("desc_norm")["top_l1"].to_dict()
cfk["pred"] = cfk["desc_norm"].map(modal_d_c)
say(f"    classified rows in that file        : {len(cfk):,}")
say(f"    distinct normalised descriptions    : {len(dd_c):,}")
say(f"    descriptions -> ONE L1              : {(dd_c['n_l1'] == 1).sum():,}")
say(f"    descriptions -> MORE THAN ONE L1    : {(dd_c['n_l1'] > 1).sum():,} ({(dd_c['n_l1']>1).mean()*100:.2f}%)")
say(f"    PART-LEVEL accuracy, modal L1 per description: {(cfk['pred']==cfk['aim_l1']).mean():.4f}")
dd_c.to_csv(OUT / "desc_to_l1_purity_classif.csv", index=False)
dd_m.to_csv(OUT / "desc_to_l1_purity_master.csv", index=False)

# ------------------------------------------------ figure key -> L1 purity
say("")
say("=" * 78)
say("4. FIGURE KEY -> AIM L1  (the shortcut the audit calls unsound)")
cl_fk = known[known["fig_key"].notna() & (known["fig_key"].astype(str).str.strip() != "")].copy()
grp3 = cl_fk.groupby("fig_key")["aim_l1"]
dd_f = pd.DataFrame({
    "n_parts": grp3.size(), "n_l1": grp3.nunique(),
    "top_l1": grp3.agg(lambda s: s.value_counts().index[0]),
    "top_share": grp3.agg(lambda s: s.value_counts().iloc[0] / len(s)),
}).reset_index()
say(f"    classified parts with a fig_key     : {len(cl_fk):,}")
say(f"    distinct fig_keys                   : {len(dd_f):,}")
say(f"    fig_keys -> ONE L1                  : {(dd_f['n_l1'] == 1).sum():,}")
say(f"    fig_keys -> MORE THAN ONE L1        : {(dd_f['n_l1'] > 1).sum():,} ({(dd_f['n_l1']>1).mean()*100:.2f}%)")
modal_f = dd_f.set_index("fig_key")["top_l1"].to_dict()
cl_fk["pred"] = cl_fk["fig_key"].map(modal_f)
say(f"    PART-LEVEL accuracy, modal L1 per fig_key: {(cl_fk['pred']==cl_fk['aim_l1']).mean():.4f}")
say("")
say("    the two traps the audit names, checked here:")
for fk, desc in [("220-001", "TRANSMISSION ASM; MANUAL"), ("011-001", "HEAD ASM; CYL")]:
    sub = cl_fk[cl_fk["fig_key"] == fk]
    if len(sub):
        d = sub["aim_l1"].value_counts()
        say(f"      fig_key {fk}: {len(sub)} known parts, {d.size} L1 -> {dict(d.head(6))}")
say("")
dd_f.sort_values("n_parts", ascending=False).to_csv(OUT / "figkey_to_l1_purity.csv", index=False)

# ------------------------------------------------------- queue coverage
say("")
say("=" * 78)
say("5. WHAT THE QUEUE CAN BE ANSWERED BY, DESCRIPTION FIRST")
q["desc_known_master"] = q["desc_norm"].isin(set(dd_m["desc_norm"]))
q["desc_known_classif"] = q["desc_norm"].isin(set(dd_c["desc_norm"]))
q["desc_contested_master"] = q["desc_norm"].isin(set(dd_m[dd_m["n_l1"] > 1]["desc_norm"]))
q["desc_contested_classif"] = q["desc_norm"].isin(set(dd_c[dd_c["n_l1"] > 1]["desc_norm"]))
q["hs_on_master_evidence"] = q["hs"].isin(set(hsp["hs"]))
q["hs_pure_master"] = q["hs"].map(hsp.set_index("hs")["n_l1"].to_dict()).fillna(99).eq(1)
q["hs_top_share"] = q["hs"].map(hsp.set_index("hs")["top_share"].to_dict())
q["desc_master_l1"] = q["desc_norm"].map(modal_d_m)
q["desc_classif_l1"] = q["desc_norm"].map(modal_d_c)

# agreement between the two description dictionaries, where both exist
both = q[q["desc_master_l1"].notna() & q["desc_classif_l1"].notna()]
agree = (both["desc_master_l1"] == both["desc_classif_l1"]).mean()
say(f"  queue rows whose description is already in the master dict : {q['desc_known_master'].sum():4d} / {len(q)}")
say(f"  queue rows whose description is already in the audit dict  : {q['desc_known_classif'].sum():4d} / {len(q)}")
say(f"  queue rows with a CONTESTED description (master dict)      : {q['desc_contested_master'].sum():4d}")
say(f"  queue rows with a CONTESTED description (audit dict)       : {q['desc_contested_classif'].sum():4d}")
say(f"  queue descriptions in BOTH dicts, and they AGREE           : {agree:.4f} on {len(both)} rows")
say(f"  queue rows whose HS code has master evidence               : {q['hs_on_master_evidence'].sum():4d}")
say(f"  queue rows whose HS code is unambiguous in the master      : {q['hs_pure_master'].sum():4d}")

q.to_csv(OUT / "queue_scored.csv", index=False, encoding="utf-8-sig")
(OUT / "run_log.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE")
