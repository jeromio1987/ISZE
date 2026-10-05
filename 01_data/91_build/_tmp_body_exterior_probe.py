"""Body Exterior composition + priority count check on the L12M pricing base."""
import pandas as pd
from pathlib import Path

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
wb = pd.read_csv(D / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str})
v2 = pd.read_csv(D / "aim_pn_classification_v2.csv", dtype=str)
aim = v2.drop_duplicates("part_number").set_index("part_number")

ins = wb[wb["in_scope"].astype(str).str.lower().isin(["true", "1"])].copy()
ins["pn"] = ins["part_number"].str.strip()
for c, col in [("aim_l1", "workbook_l1"), ("aim_l2", "workbook_l2"), ("aim_l3", "workbook_l3"),
               ("cat_l1", "catalog_l1"), ("cat_l2", "catalog_l2"), ("cat_l3", "catalog_l3")]:
    ins[c] = ins["pn"].map(aim[col])

be = ins[ins["aim_l1"] == "Body Exterior"].copy()
print("=== BODY EXTERIOR on the pricing base ===")
print("rows", len(be), "| PNs", be["pn"].nunique(),
      "| EUR", round(be["net_sales_value"].sum()),
      "| step EUR", round(pd.to_numeric(be["value_eur_step"], errors="coerce").sum()))

print()
print("--- what the catalogue says these really are (cat_l1 / cat_l2) ---")
g = be.groupby(["cat_l1", "cat_l2"]).agg(
    rows=("pn", "size"), eur=("net_sales_value", "sum"),
    step=("value_eur_step", lambda s: pd.to_numeric(s, errors="coerce").sum()),
).sort_values("eur", ascending=False)
g["eur"] = g["eur"].round(0)
g["step"] = g["step"].round(0)
print(g.head(20).to_string())

print()
print("--- AIM L2 inside Body Exterior ---")
g2 = be.groupby("aim_l2").agg(rows=("pn", "size"), eur=("net_sales_value", "sum")).sort_values("eur", ascending=False)
g2["eur"] = g2["eur"].round(0)
print(g2.head(20).to_string())

print()
print("--- TOP 25 Body Exterior parts by billed euro ---")
top = be.groupby("pn").agg(
    eur=("net_sales_value", "sum"),
    step=("value_eur_step", lambda s: pd.to_numeric(s, errors="coerce").sum()),
    qty=("billed_qty", "sum"),
    desc=("billed_description", "first"),
    aim_l2=("aim_l2", "first"), aim_l3=("aim_l3", "first"),
    cat_l2=("cat_l2", "first"),
).sort_values("eur", ascending=False).head(25)
for pn, r in top.iterrows():
    print("%-12s %10s %9s %9s | %-34s | AIM %s / %s | CAT %s" % (
        pn, round(r["eur"]), round(r["step"]), round(r["qty"]),
        str(r["desc"])[:34], str(r["aim_l2"])[:18], str(r["aim_l3"])[:20], str(r["cat_l2"])[:18]))

print()
print("--- TOP 15 Body Exterior parts by STEP euro (the revision impact) ---")
topstep = be.groupby("pn").agg(
    step=("value_eur_step", lambda s: pd.to_numeric(s, errors="coerce").sum()),
    eur=("net_sales_value", "sum"),
    desc=("billed_description", "first"),
    aim_l2=("aim_l2", "first"), aim_l3=("aim_l3", "first"),
).sort_values("step", ascending=False).head(15)
for pn, r in topstep.iterrows():
    print("%-12s step %9s  eur %10s | %-36s | AIM %s / %s" % (
        pn, round(r["step"]), round(r["eur"]), str(r["desc"])[:36],
        str(r["aim_l2"])[:18], str(r["aim_l3"])[:20]))

print()
print("=== PRIORITY / COUNT CHECK ===")
print("in-scope rows            ", len(ins))
print("in-scope distinct PNs    ", ins["pn"].nunique())
print("rows with a step         ", int(pd.to_numeric(ins["value_eur_step"], errors="coerce").notna().sum()))
cand = [c for c in ins.columns if "prior" in c.lower() or "flag" in c.lower() or "tier" in c.lower()]
print("priority-like columns    ", cand if cand else "NONE in the weight base")
