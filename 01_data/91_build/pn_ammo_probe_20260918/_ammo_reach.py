import pandas as pd

DER = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")

sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["_pn"] = sf.part_number.map(norm)
book = sf.groupby("_pn").net_sales_value.sum()
tot = book.sum()

mar = pd.read_csv(DER + r"\margin_opportunity_top200.csv", dtype=str, low_memory=False)
mar["_pn"] = mar.pn.map(norm)
mar["cost"] = pd.to_numeric(mar.cost_fob, errors="coerce")

ks = pd.read_csv(DER + r"\competitor_common_basis.csv", dtype=str, low_memory=False)
ks["_pn"] = ks.pn.map(norm)
ks = ks.assign(
    comp=pd.to_numeric(ks.competitor_price_eur, errors="coerce"),
    ours=pd.to_numeric(ks.k3_reference_dealer_eur, errors="coerce"),
    src="KS trade",
)
br = pd.read_csv(DER + r"\price_collection_worklist_filled.csv", dtype=str, low_memory=False)
br = br[br.status.astype(str).str.lower() == "resolved"].copy()
br["_pn"] = br.pn.map(norm)
br = br.assign(
    comp=pd.to_numeric(br.competitor_price_eur, errors="coerce"),
    ours=pd.to_numeric(br.our_reference_dealer_price_eur, errors="coerce"),
    src="bridge",
)

comp = pd.concat([ks[["_pn", "comp", "ours", "src"]], br[["_pn", "comp", "ours", "src"]]])
comp = comp.dropna(subset=["comp"]).groupby("_pn").agg(
    comp=("comp", "min"), ours=("ours", "median"), src=("src", "first")
).reset_index()

d = mar.merge(comp, on="_pn", how="inner")
d["billed"] = pd.to_numeric(d.billed_eur, errors="coerce")
d["our_cost"] = d["cost"]
d["gap_ratio"] = d["ours"] / d["comp"]
d["comp_below_our_cost"] = d["comp"] < d["our_cost"]
d["headroom_to_cost"] = d["ours"] - d["our_cost"]

below = d[d.comp_below_our_cost]
above = d[~d.comp_below_our_cost]
print(f"part numbers with cost + a competitor price : {len(d)}")
print(f"   ... where the competitor sits BELOW our landed cost : {len(below)}"
      f"   (EUR {below.billed.sum():,.0f} billed, {100*below.billed.sum()/tot:.1f}% of book)")
print(f"   ... where we still have room above our cost        : {len(above)}"
      f"   (EUR {above.billed.sum():,.0f} billed)")
print()
print("The ones where room exists are the only place a price or incentive lever can be sized:")
cols = ["pn", "description", "aim_l1", "cost", "ours", "comp", "gap_ratio", "billed"]
a = above.sort_values("billed", ascending=False).head(15).copy()
a["cost"] = a.cost.astype(float).round(2)
a["ours"] = a.ours.astype(float).round(2)
a["comp"] = a.comp.astype(float).round(2)
a["gap_ratio"] = a.gap_ratio.astype(float).round(2)
a["billed"] = a.billed.astype(float).round(0)
print(a[cols].to_string(index=False))
print()
print("Brakes only, all of them:")
bz = d[d.aim_l1 == "Brakes"].sort_values("billed", ascending=False).copy()
for c in ["cost", "ours", "comp", "gap_ratio"]:
    bz[c] = bz[c].astype(float).round(2)
bz["billed"] = bz.billed.astype(float).round(0)
bz["comp<cost"] = bz.comp_below_our_cost
print(bz[["pn", "description", "cost", "ours", "comp", "gap_ratio", "billed", "comp<cost"]].to_string(index=False))
