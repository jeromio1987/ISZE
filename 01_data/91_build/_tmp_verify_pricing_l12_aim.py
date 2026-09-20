"""Verify the L12M pricing weight base and its AIM join coverage."""
import json

import pandas as pd
from pathlib import Path

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
wb = pd.read_csv(D / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str})
v2 = pd.read_csv(D / "aim_pn_classification_v2.csv", dtype=str)
meta = json.loads((D / "price_bp_weighted_compare_meta.json").read_text(encoding="utf-8"))

print("=== 1. THE WEIGHT BASE ===")
print("rows                 ", len(wb))
print("distinct part numbers", wb["part_number"].nunique())
print("window               ", meta.get("window") or meta.get("period") or "see meta")

scope = wb.groupby("in_scope").agg(rows=("part_number", "size"), eur=("net_sales_value", "sum"))
print()
print("in_scope split:")
print(scope.to_string())

ins = wb[wb["in_scope"].astype(str).str.lower().isin(["true", "1"])].copy()
print()
print("in-scope rows        ", len(ins))
print("in-scope billed EUR  ", round(ins["net_sales_value"].sum(), 2))
print("in-scope qty         ", round(ins["billed_qty"].sum(), 0))

print()
print("=== 2. THE PRICE STEP ===")
ins["step"] = pd.to_numeric(ins.get("value_eur_step"), errors="coerce")
print("step EUR total       ", round(ins["step"].sum(), 2))
both = ins[pd.to_numeric(ins["bp_new_jpy"], errors="coerce").notna() & pd.to_numeric(ins["bp_prior_revised"], errors="coerce").notna()]
num = (both["billed_qty"] * pd.to_numeric(both["bp_new_jpy"], errors="coerce")).sum()
den = (both["billed_qty"] * pd.to_numeric(both["bp_prior_revised"], errors="coerce")).sum()
print("rows priced both sides", len(both))
print("weighted increase %  ", round(100 * (num / den - 1), 4))
print("PUBLISHED (must match) 5.9616% and EUR 1,652,140.71")

print()
print("=== 3. AIM JOIN ===")
aim = v2.drop_duplicates("part_number").set_index("part_number")
ins["pn"] = ins["part_number"].str.strip()
ins["aim_l1"] = ins["pn"].map(aim["workbook_l1"])
ins["aim_l2"] = ins["pn"].map(aim["workbook_l2"])
ins["aim_l3"] = ins["pn"].map(aim["workbook_l3"])
ins["cat_l1"] = ins["pn"].map(aim["catalog_l1"])
ins["cat_l2"] = ins["pn"].map(aim["catalog_l2"])
has_aim = ins["aim_l1"].notna() & (ins["aim_l1"].astype(str).str.strip() != "")
has_cat = ins["cat_l1"].notna() & (ins["cat_l1"].astype(str).str.strip() != "")

tot = ins["net_sales_value"].sum()
print("in-scope EUR                    ", round(tot, 2))
print("with an AIM Category            ", round(100 * ins.loc[has_aim, "net_sales_value"].sum() / tot, 2), "%")
print("with a catalogue node           ", round(100 * ins.loc[has_cat, "net_sales_value"].sum() / tot, 2), "%")
print("with NEITHER                    ", round(100 * ins.loc[~has_aim & ~has_cat, "net_sales_value"].sum() / tot, 2), "%")

print()
print("=== 4. AIM Class L1 on the pricing base ===")
g = (
    ins[has_aim]
    .groupby("aim_l1")
    .agg(rows=("part_number", "size"), pn=("pn", "nunique"), eur=("net_sales_value", "sum"), step=("step", "sum"))
    .sort_values("eur", ascending=False)
)
g["eur"] = g["eur"].round(0)
g["step"] = g["step"].round(0)
print(g.head(30).to_string())

print()
print("=== 5. which of these are PMS / competitive? ===")
# PMS filter/pms families per the classification
pms_l2 = {
    "Filters", "Brake parts", "Clutch parts", "Suspension", "Steering",
    "Cooling", "Exhaust", "Belts", "Fuel system", "Air system",
}
ins["is_pms_like"] = ins["cat_l2"].isin(pms_l2)
print("catalogue L2 in the PMS-like set, share of in-scope EUR:",
      round(100 * ins.loc[ins["is_pms_like"], "net_sales_value"].sum() / tot, 2), "%")
print()
print(ins.groupby("is_pms_like").agg(rows=("part_number", "size"), eur=("net_sales_value", "sum")).to_string())
