import pandas as pd
from pathlib import Path

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_with_crossref.parquet")
swx = pd.read_parquet(
    p,
    columns=[
        "billing_date",
        "distributor_code",
        "billed_qty",
        "crossref_role",
        "crossref_id",
        "net_sales_value",
        "product_subgroup",
    ],
)
swx = swx[
    (swx.distributor_code == "GERMANY")
    & swx.crossref_id.notna()
    & swx.crossref_role.isin(["genuine", "bvp"])
]
swx["bd"] = pd.to_datetime(swx.billing_date)
swx["fy"] = swx.bd.dt.year.where(swx.bd.dt.month >= 4, swx.bd.dt.year - 1)
swx["cy"] = swx.bd.dt.year
swx["ym"] = swx.bd.dt.to_period("M").astype(str)

for fy in [2023, 2024, 2025]:
    g = swx[swx.fy == fy]
    b = g[g.crossref_role == "bvp"]
    ge = g[g.crossref_role == "genuine"]
    bq, gq = b.billed_qty.sum(), ge.billed_qty.sum()
    be, gee = b.net_sales_value.sum(), ge.net_sales_value.sum()
    tot = bq + gq
    months = sorted(g.ym.unique())
    print(
        f"FY{fy}/{str(fy+1)[2:]} share={bq/tot*100:.1f}% "
        f"qty BVP={bq:.0f} GEN={gq:.0f} | eur BVP={be:,.0f} GEN={gee:,.0f} | "
        f"months={len(months)} {months[0]}..{months[-1]}"
    )
    # top subgroups by qty shift
    piv = g.groupby(["product_subgroup", "crossref_role"])["billed_qty"].sum().unstack(fill_value=0)
    if "bvp" in piv.columns and "genuine" in piv.columns:
        piv["tot"] = piv["bvp"] + piv["genuine"]
        piv["bvp_share"] = piv["bvp"] / piv["tot"].replace(0, pd.NA)
        print("  top subgroups by total qty:")
        print(piv.sort_values("tot", ascending=False).head(8).to_string())

print("--- CY ---")
for y in [2023, 2024, 2025]:
    g = swx[swx.cy == y]
    bq = g[g.crossref_role == "bvp"].billed_qty.sum()
    gq = g[g.crossref_role == "genuine"].billed_qty.sum()
    tot = bq + gq
    print(f"CY{y} share={bq/tot*100:.1f}% bvp={bq:.0f} gen={gq:.0f}")
