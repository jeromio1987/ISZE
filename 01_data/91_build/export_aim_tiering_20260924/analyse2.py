"""Tier analysis, part 2 -- the independent evidence base.

The master's `aim_workbook` rows were themselves built by a description join,
so testing description->family on them is circular. The `pr00_catalog` rows
came from the figure-key / EPC route, so they are the independent control.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

pd.set_option("display.width", 260)
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

flat = pd.read_csv(FLAT, dtype=str, low_memory=False)
flat["pn"] = norm_pn(flat["pn"]); flat["hs"] = hs_key(flat["hs_code"])
flat["desc_norm"] = norm_desc(flat["description"])
flat["fk"] = (flat["fig_no"].fillna("").astype(str).str.strip()
              .str.replace(r"\.0$", "", regex=True).str.zfill(3) + "-" +
              flat["key_no"].fillna("").astype(str).str.strip().str.upper())
flat = flat.drop_duplicates("pn", keep="first")

m = pd.read_csv(MASTER, dtype=str, low_memory=False)
m["pn"] = norm_pn(m["part_number"])
m = m.drop_duplicates("pn", keep="first")
m["known"] = m["aim_l1"].map(is_known)
say("=" * 78)
say("A. WHICH AXIS DOES THE QUEUE WANT?")
say("  master real aim_l1 vocabulary (top 40):")
for k, v in m[m["known"]]["aim_l1"].value_counts().head(40).items():
    say(f"      {k:32s} {v:6d}")
say("")
say("  master aim_l1 values that are POSTURE words vs SYSTEM words")
posture = {"Competitive parts","Repair parts","Accident parts","High value repair",
           "Comfort parts","Hardware & consumables","Other / review"}
km = m[m["known"]]
say(f"      posture rows : {km['aim_l1'].isin(posture).sum():,}")
say(f"      system  rows : {(~km['aim_l1'].isin(posture)).sum():,}")

known = km.copy()
known = known.merge(flat[["pn", "hs", "fk", "desc_norm", "fig_no", "price_eur"]], on="pn", how="left")
known["desc_norm"] = known["desc_norm"].fillna(norm_desc(known["description"]))
say(f"  master known rows joined to price flat: {len(known):,}")

say("")
say("=" * 78)
say("B. INDEPENDENT CONTROL: rows whose family came from the EPC / figure-key route")
pc = known[known["aim_source"].fillna("").str.strip().str.startswith("pr00_catalog")].copy()
print("pr00_catalog-ish rows:", len(pc))
for tag, sub in [("pr00_catalog starts-with", pc),
                 ("aim_workbook only", known[known["aim_source"].fillna("").str.strip() == "aim_workbook"]),
                 ("eq_session touched", known[known["aim_source"].fillna("").str.contains("eq_session")]),
                 ("gap_auto touched", known[known["aim_source"].fillna("").str.contains("gap_auto")])]:
    say(f"  {tag:26s} rows={len(sub):6,d}  distinct L1={sub['aim_l1'].nunique():3d}")

def purity(df, keycol, min_parts=1):
    d = df[(df[keycol].notna()) & (df[keycol] != "")]
    g = d.groupby(keycol)["aim_l1"]
    t = pd.DataFrame({"n_parts": g.size(), "n_l1": g.nunique(),
                      "top_l1": g.agg(lambda s: s.value_counts().index[0]),
                      "top_share": g.agg(lambda s: s.value_counts().iloc[0] / len(s))})
    t = t[t["n_parts"] >= min_parts]
    pred = t["top_l1"].to_dict()
    d = d.assign(pred=d[keycol].map(pred))
    return t, float((d["pred"] == d["aim_l1"]).mean()), len(d)

say("")
for basisname, basis in [("pr00_catalog (EPC route)", pc), ("aim_workbook (desc route)", known)]:
    say(f"  --- basis: {basisname}  n={len(basis):,} ---")
    for keyname, keycol in [("HS code", "hs"), ("description", "desc_norm"), ("figure key", "fk")]:
        t, acc, n = purity(basis, keycol)
        say(f"      {keyname:12s}: keys={len(t):5,d}  keys->1L1={(t['n_l1']==1).sum():5,d} "
            f" keys->many={(t['n_l1']>1).sum():5,d}  median top_share={t['top_share'].median():.3f}  "
            f"part-level accuracy={acc:.4f}")

say("")
say("=" * 78)
say("C. THE QUEUE'S OWN 7 ALREADY-KNOWN PARTS + the 40 highest-value unknowns")
q = pd.read_csv(QUEUE, dtype=str, encoding="utf-8-sig")
q["pn"] = norm_pn(q["pn"]); q["hs"] = hs_key(q["Commodity Code"])
q["pr00_eur"] = numify(q["pr00_value_eur"]); q["list_eur"] = numify(q["list_eur"])
q["desc_norm"] = norm_desc(q["Description"])
q["fk"] = q["fig_key"].fillna("").astype(str).str.strip()

# independent lookup tables from the EPC-route basis
t_hs, _, _ = purity(pc, "hs")
t_fk, _, _ = purity(pc, "fk")
t_ds, acc_desc_pc, n_desc_pc = purity(pc, "desc_norm")
t_hsw, _, _ = purity(known, "hs")

say(f"  description purity measured on the EPC basis: {acc_desc_pc:.4f} over {n_desc_pc:,} rows, "
    f"keys={len(t_ds):,}, keys->many={(t_ds['n_l1']>1).sum()}")
# how does HS purity actually look on the whole master (not just pr00_catalog)?
say(f"  HS purity on the whole master basis: keys={len(t_hsw):,}, keys->many={(t_hsw['n_l1']>1).sum()}")

# contested descriptions in the EPC basis
cont = t_ds[t_ds["n_l1"] > 1].sort_values("n_parts", ascending=False)
say("")
say(f"  EPC-basis descriptions that are CONTESTED ({len(cont)}):")
for i, (k, r) in enumerate(cont.head(30).iterrows()):
    sub = pc[pc["desc_norm"] == k]
    dist = sub["aim_l1"].value_counts()
    say(f"      {k[:42]:42s} n={r['n_parts']:4d} L1s={r['n_l1']:2d} | "
        + " | ".join(f"{a}={b}" for a, b in list(dist.items())[:4]))

# how many queue rows are hit by these contested descriptions
q_cont = q[q["desc_norm"].isin(set(cont.index))]
say(f"  queue rows whose description is one of those contested ones: {len(q_cont)}")

say("")
say("=" * 78)
say("D. FIGURE-KEY TRAP REPRODUCTION (the audit's two named cases)")
for fk, desc in [("220-001", "TRANSMISSION ASM; MANUAL"), ("011-001", "HEAD ASM; CYL")]:
    sub = known[known["fk"] == fk]
    d = sub["aim_l1"].value_counts()
    say(f"  fig_key {fk} on master: {len(sub)} known parts, {d.size} L1s")
    for k, v in list(d.items())[:8]:
        say(f"      {k:34s} {v}")
    ex = sub[sub["description"].fillna("").str.upper().str.contains(desc.split(";")[0])].head(4)
    for _, r in ex.iterrows():
        say(f"      e.g. {r['pn']}  {r['description'][:38]:38s} -> {r['aim_l1']} > {r['aim_l2']} > {r['aim_l3']}")

(OUT / "run_log2.txt").write_text("\n".join(log), encoding="utf-8")
print("\nDONE2")
