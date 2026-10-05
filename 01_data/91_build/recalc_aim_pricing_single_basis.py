#!/usr/bin/env python3
"""
FULL RECALCULATION on ONE declared basis.

Basis: the live pricing-revision weight base.
  price_bp_weighted_compare_pn.csv, in_scope == True
  window 2025-07-01 .. 2026-06-30 (L12M)
  billed EUR 34,993,609.39 | step EUR 1,652,140.71 | weighted 5.9616%

Everything below is derived from that single frame. No second window, no gross
billing, no mixed scope. If a figure cannot be produced on this basis it is
labelled NOT ON THIS BASIS.

Both taxonomies are reported side by side and each is labelled for what it is.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
OUT_JSON = D / "aim_pricing_recalc_2026-09-17.json"
OUT_L1 = D / "aim_pricing_recalc_l1.csv"
OUT_L2 = D / "aim_pricing_recalc_l2.csv"

# ---------------------------------------------------------------- load one base
wb = pd.read_csv(D / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str})
df = wb[wb["in_scope"].astype(str).str.lower().isin(["true", "1"])].copy()
df["pn"] = df["part_number"].str.strip()
df["eur"] = pd.to_numeric(df["net_sales_value"], errors="coerce")
df["qty"] = pd.to_numeric(df["billed_qty"], errors="coerce")
df["step"] = pd.to_numeric(df["value_eur_step"], errors="coerce")
df["bp_new"] = pd.to_numeric(df["bp_new_jpy"], errors="coerce")
df["bp_prior"] = pd.to_numeric(df["bp_prior_revised"], errors="coerce")

# ---------------------------------------------------------------- attach both taxonomies
m = pd.read_csv(D / "aim_master_v1.csv", dtype=str, low_memory=False)
code_cols = {c: pd.to_numeric(m[c], errors="coerce") for c in ()}
m = m.drop_duplicates("part_number").set_index("part_number") if False else m
m = m.drop_duplicates("part_number").set_index("part_number") if False else m
master = pd.read_csv(D / "aim_master_v1.csv", dtype=str, low_memory=False).drop_duplicates("part_number")
master = master.set_index("part_number")
for c in ("aim_l1", "aim_l2", "aim_l3", "cat_l1", "cat_l2", "cat_l3",
          "has_aim", "cat_pms_flag", "fig_key", "price_class_iml"):
    df[c] = df["pn"].map(master[c])

# ---------------------------------------------------------------- 1. totals + tie-out
total_eur = float(df["eur"].sum())
total_step = float(df["step"].sum())
both = df[df["bp_new"].notna() & df["bp_prior"].notna()]
num = float((both["qty"] * both["bp_new"]).sum())
den = float((both["qty"] * both["bp_prior"]).sum())
weighted = 100 * (num / den - 1)

print("=" * 78)
print("BASIS: pricing revision weight base, in-scope, L12M 2025-07-01..2026-06-30")
print("=" * 78)
print(f"rows                    {len(df):,}")
print(f"distinct part numbers   {df['pn'].nunique():,}")
print(f"billed EUR              {total_eur:,.2f}")
print(f"step EUR                {total_step:,.2f}   (published 1,652,140.71)")
print(f"weighted increase       {weighted:.4f}%        (published 5.9616%)")
print(f"TIE OUT                 {'PASS' if abs(total_step-1652140.71)<0.02 and abs(weighted-5.9616)<0.0001 else 'FAIL'}")
print()

# ---------------------------------------------------------------- 2. coverage, labelled honestly
has_aim = df["has_aim"] == "1"
aim_eur = float(df.loc[has_aim, "eur"].sum())
cat_node = df["cat_l1"].fillna("").ne("") & df["cat_l1"].fillna("") != "Other / review"
cat_eur = float(df.loc[cat_node, "eur"].sum())
print("COVERAGE, share of the billed euro on this basis")
print(f"  genuine AIM Category      {100*aim_eur/total_eur:6.2f}%   EUR {aim_eur:,.0f}")
print(f"  catalogue node (real)     {100*cat_eur/total_eur:6.2f}%   EUR {cat_eur:,.0f}")
print(f"  PMS-flagged (catalogue)   {100*float(df.loc[df['cat_pms_flag']=='1','eur'].sum())/total_eur:6.2f}%")
print()

# ---------------------------------------------------------------- 3. AIM L1 on this base
print("AIM CATEGORY L1 - sales taxonomy (governed spine)")
g1 = (df[has_aim].groupby("aim_l1")
      .agg(pn=("pn", "nunique"), rows=("pn", "size"),
           billed_eur=("eur", "sum"), step_eur=("step", "sum"))
      .sort_values("billed_eur", ascending=False))
g1["billed_share_pct"] = (100 * g1["billed_eur"] / total_eur).round(2)
g1["step_share_pct"] = (100 * g1["step_eur"] / total_step).round(2)
print(g1.round(0).to_string())
print()

# ---------------------------------------------------------------- 4. AIM L2 within top classes
print("AIM CATEGORY L2 - top 30 by euro")
g2 = (df[has_aim].groupby(["aim_l1", "aim_l2"])
      .agg(pn=("pn", "nunique"), billed_eur=("eur", "sum"), step_eur=("step", "sum"))
      .sort_values("billed_eur", ascending=False))
g2["billed_share_pct"] = (100 * g2["billed_eur"] / total_eur).round(2)
print(g2.head(30).round(0).to_string())
print()

# ---------------------------------------------------------------- 5. catalogue posture on this base
print("CATALOGUE POSTURE L1 - price-list attribute (NOT the spine)")
g3 = (df[df["cat_l1"].fillna("") != ""].groupby("cat_l1")
      .agg(pn=("pn", "nunique"), billed_eur=("eur", "sum"), step_eur=("step", "sum"))
      .sort_values("billed_eur", ascending=False))
g3["billed_share_pct"] = (100 * g3["billed_eur"] / total_eur).round(2)
print(g3.round(0).to_string())
print()

# ---------------------------------------------------------------- 6. unclassified bucket, named
not_aim = df[~has_aim]
print("NOT ON THE AIM SPINE (named residual, not hidden)")
print(f"  rows {len(not_aim):,} | PN {not_aim['pn'].nunique():,} | EUR {not_aim['eur'].sum():,.0f} "
      f"({100*not_aim['eur'].sum()/total_eur:.2f}% of billed)")
nb = (not_aim.groupby(not_aim["cat_l1"].fillna("(no catalogue node)"))
      .agg(rows=("pn", "size"), eur=("eur", "sum")).sort_values("eur", ascending=False))
print(nb.round(0).to_string())
print()

# ---------------------------------------------------------------- write
g1.reset_index().to_csv(OUT_L1, index=False)
g2.reset_index().to_csv(OUT_L2, index=False)
meta = {
    "generated": datetime.now(timezone.utc).isoformat(),
    "basis": {
        "file": "price_bp_weighted_compare_pn.csv",
        "filter": "in_scope == True",
        "window": {"start": "2025-07-01", "end": "2026-06-30"},
        "billed_eur": round(total_eur, 2),
        "step_eur": round(total_step, 2),
        "weighted_pct": round(weighted, 4),
    },
    "tie_out": {
        "step_matches_published": abs(total_step - 1652140.71) < 0.02,
        "weighted_matches_published": abs(weighted - 5.9616) < 0.0001,
    },
    "coverage_pct_eur": {
        "genuine_aim": round(100 * aim_eur / total_eur, 2),
        "catalogue_node": round(100 * cat_eur / total_eur, 2),
    },
    "aim_l1": g1.reset_index().to_dict(orient="records"),
    "note": "Single basis. Every figure in this file is on the pricing revision base only.",
}
OUT_JSON.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
print(f"-> {OUT_JSON}")
print(f"-> {OUT_L1}")
print(f"-> {OUT_L2}")
