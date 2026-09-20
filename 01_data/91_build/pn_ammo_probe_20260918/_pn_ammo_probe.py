import pandas as pd

DER = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")

sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["_pn"] = sf.part_number.map(norm)
sf["year"] = pd.to_datetime(sf.billing_date, errors="coerce").dt.year
dim = pd.read_csv(DER + r"\distributor_dimension.csv")
sf["db"] = sf.sold_to_sap.map(dict(zip(dim.sold_to_sap, dim.distributor_code)))

mar = pd.read_csv(DER + r"\margin_opportunity_top200.csv", dtype=str, low_memory=False)
mar["_pn"] = mar.pn.map(norm)
floor = pd.read_csv(DER + r"\pricing_cost_floor_reach.csv", dtype=str, low_memory=False)
floor["_pn"] = floor.pn.map(norm)

# The two part numbers Duncan built his case on, plus the biggest brake PN we bill.
targets = ["8982447940", "8982169220", "8983767550", "8975546610"]

for pn in targets:
    row = mar[mar._pn == pn]
    print("=" * 96)
    if row.empty:
        print(f"{pn}: not in the top-200 margin file")
    else:
        r = row.iloc[0]
        print(f"{pn}  {r['description']}")
        print(f"  family       : {r['aim_l1']} > {r['aim_l2']}   criticality {r['criticality']}"
              f"   competition {r['competition']}   price class {r['price_class']}")
        print(f"  margin today : {float(r['margin_pct']):.1f}%   cost FOB EUR {float(r['cost_fob']):.2f}")
        print(f"  billed       : EUR {float(r['billed_eur']):,.0f} on {float(r['qty']):,.0f} units"
              f"   across {r['distributors']} markets   rank {r['rank_by_revenue']}")

    # our own billing history across markets
    g = sf[sf._pn == pn]
    if not g.empty:
        yb = g.groupby("year").agg(q=("billed_qty", "sum"), s=("net_sales_value", "sum"))
        print("  billed by year  : " + "  ".join(
            f"{int(y)}: {r2['q']:,.0f}u/EUR{r2['s']:,.0f}" for y, r2 in yb.iterrows()))
        mk = (g.groupby("db").agg(u=("billed_qty", "sum"), e=("net_sales_value", "sum"))
              .sort_values("e", ascending=False).head(6))
        print("  top markets     : " + ", ".join(
            f"{i} {int(r2['u'])}u/EUR{r2['e']:,.0f}" for i, r2 in mk.iterrows()))

    f = floor[floor._pn == pn]
    if not f.empty:
        fr = f.iloc[0]
        print(f"  competitor      : IAM EUR {float(fr['iam']):.2f}   our list EUR {float(fr['pr00']):.2f}"
              f"   index {float(fr['idx']):.2f}x")
        print(f"  margin today {float(fr['gm_today']):.1%} -> to match IAM needs "
              f"{float(fr['gm_to_match']):.1%}  (change {100*(float(fr['gm_to_match'])-float(fr['gm_today'])):+.0f} pts)")
    print()
