import pandas as pd

DER = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")

sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["_pn"] = sf.part_number.map(norm)
book = sf.groupby("_pn").net_sales_value.sum()
tot = book.sum()

def load(f, col="pn"):
    d = pd.read_csv(DER + "\\" + f, dtype=str, low_memory=False)
    d["_pn"] = d[col].map(norm)
    return d

mar = load("margin_opportunity_top200.csv")
cost = set(mar[mar.cost_fob.notna() & (mar.cost_fob.astype(str).str.strip() != "")]._pn)
floor = load("pricing_cost_floor_reach.csv")
comp_ks = load("competitor_common_basis.csv")
comp_bridge = load("price_collection_worklist_filled.csv")
bridged = comp_bridge[comp_bridge.status.astype(str).str.lower() == "resolved"]

sets = {
    "billed part numbers (book)": set(book.index),
    "with cost and margin (top-200 file)": cost,
    "with our list + a KS competitor price": set(comp_ks._pn),
    "with our list + bridge competitor price": set(bridged._pn),
}
print(f"{'set':46s} {'PNs':>6s} {'EUR covered':>16s} {'% of book':>10s}")
for name, s in sets.items():
    e = book.reindex(list(s)).sum()
    print(f"{name:46s} {len(s):6d} {e:16,.0f} {100*e/tot:9.1f}%")

both = cost & (set(comp_ks._pn) | set(bridged._pn))
e = book.reindex(list(both)).sum()
print()
print(f"{'COST + COMPETITOR PRICE on the same PN':46s} {len(both):6d} {e:16,.0f} {100*e/tot:9.1f}%")
print()
print("Those PNs (cost + a real competitor price, so a price-position lever can be sized):")
d = mar[mar._pn.isin(both)][["pn", "description", "aim_l1", "aim_l2", "margin_pct", "cost_fob", "billed_eur", "qty"]]
d["margin_pct"] = d.margin_pct.astype(float).round(1)
d["cost_fob"] = d.cost_fob.astype(float).round(2)
d["billed_eur"] = d.billed_eur.astype(float).round(0)
print(d.sort_values("billed_eur", ascending=False).head(25).to_string(index=False))
