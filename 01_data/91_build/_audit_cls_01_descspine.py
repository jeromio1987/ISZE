#!/usr/bin/env python3
"""Audit step 1: build the widest possible part_number -> description spine,
plus a part_number -> billed euro spine, so the classification can be tested
against the words on the part and weighted by money."""
from __future__ import annotations
import csv, collections, json, sys
from pathlib import Path

csv.field_size_limit(10_000_000)
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
OUT = D / "_audit_cls_desc_spine.csv"

def norm_pn(s: str) -> str:
    s = (s or "").strip().upper()
    if not s:
        return ""
    if s.isdigit():
        return s.zfill(10)
    return s

# ---------------------------------------------------------------- sales_fact
print("== sales_fact.parquet ==")
sf = D / "sales_fact.parquet"
desc: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
eur: dict[str, float] = collections.defaultdict(float)
qty: dict[str, float] = collections.defaultdict(float)
if sf.is_file():
    import pandas as pd
    import pyarrow.parquet as pq
    cols = pq.ParquetFile(sf).schema.names
    print("columns:", cols)
    dcol = next((c for c in cols if "desc" in c.lower()), None)
    print("description column ->", dcol)
    use = [c for c in ["part_number", "billing_date", "net_sales_value", "billed_quantity"] if c in cols]
    if dcol:
        use.append(dcol)
    df = pd.read_parquet(sf, columns=use)
    print("rows", len(df))
    dt = pd.to_datetime(df["billing_date"], errors="coerce")
    w = df[(dt >= "2025-01-01") & (dt <= "2026-06-30")]
    print("rows in 2025-01-01..2026-06-30", len(w))
    for pn, g in w.groupby(w["part_number"].astype(str)):
        k = norm_pn(pn)
        eur[k] += float(g["net_sales_value"].sum())
        if "billed_quantity" in g:
            qty[k] += float(g["billed_quantity"].sum())
    if dcol:
        sub = w[["part_number", dcol]].dropna()
        for pn, dsc in zip(sub["part_number"].astype(str), sub[dcol].astype(str)):
            k = norm_pn(pn)
            if dsc.strip():
                desc[k][dsc.strip().upper()] += 1
    print(f"sales_fact: {len(eur):,} PNs with euro, {len(desc):,} PNs with description")
else:
    print("MISSING")

# ------------------------------------------------- other description sources
SOURCES = [
    ("price_bp_weighted_compare_pn.csv", "part_number", "billed_description"),
    ("aim_master_v2.csv", "part_number", "description"),
    ("aim_master_v1.csv", "part_number", "description"),
    ("mislabelled_sku_audit.csv", "part_number", "description"),
    ("pn_coverage_classification.csv", "part_number", "description"),
    ("warranty_raw_grain.csv", "part_no", "part_desc"),
    ("no_pr00_gap_cy2025_ranked.csv", "part_number", "description"),
    ("competitiveness_autodoc_risk.csv", "part_number", "description"),
    ("sellout_aim_top_pn_2025.csv", "part_number", "description"),
    ("apl_pn_list_long_20260812.csv", "\ufeffpart_number", "description"),
    ("aim_gap_suggestions_20260702.csv", "pn", "description"),
    ("unpriced_no_price_one_side_list.csv", "\ufeffPart number", "Description"),
    ("aim_pn_classification_v2.csv", "part_number", "description_norm"),
]
print("\n== other description sources ==")
for fname, pncol, dcol in SOURCES:
    p = D / fname
    if not p.is_file():
        print(f"  {fname:<48} MISSING")
        continue
    added = 0
    try:
        with p.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                pn = norm_pn(r.get(pncol) or r.get(pncol.lstrip("\ufeff")) or "")
                d = (r.get(dcol) or "").strip().upper()
                if pn and d:
                    desc[pn][d] += 1
                    added += 1
    except Exception as e:
        print(f"  {fname:<48} ERR {e}")
        continue
    print(f"  {fname:<48} +{added:,} desc rows   (spine now {len(desc):,} PNs)")

# ----------------------------------------------------------------- PR00 raw
print("\n== PR00 price list (raw, for description) ==")
cands = list((ISZE / "01_data" / "01_Pricing").glob("**/*PR00*"))
for c in cands[:40]:
    print("  ", c.name, f"{c.stat().st_size/1e6:.1f} MB")

# ------------------------------------------------------------------- write
V2 = D / "aim_pn_classification_v2.csv"
rows = list(csv.DictReader(V2.open(encoding="utf-8", newline="")))
with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["part_number", "description_best", "n_desc_variants", "all_variants",
                "l12m_eur", "l12m_qty"])
    for r in rows:
        pn = r["part_number"]
        c = desc.get(pn)
        best = c.most_common(1)[0][0] if c else ""
        w.writerow([pn, best, len(c) if c else 0,
                    " | ".join(sorted(c)) if c and len(c) > 1 else "",
                    f"{eur.get(pn, 0.0):.2f}", f"{qty.get(pn, 0.0):.0f}"])

have = sum(1 for r in rows if desc.get(r["part_number"]))
tot_eur = sum(eur.values())
class_eur = sum(eur.get(r["part_number"], 0.0) for r in rows)
print(f"\nclassification rows {len(rows):,}")
print(f"  with a description from ANY source: {have:,} ({100*have/len(rows):.1f}%)")
print(f"  euro in window on classified PNs : {class_eur:,.0f} of {tot_eur:,.0f} total "
      f"({100*class_eur/tot_eur:.2f}%)")
print(f"-> {OUT}")
