"""Which months inside the billing range carry no billing rows at all?"""
import pandas as pd

D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
EXCL = ["CR", "RE", "DR", "ZDR", "FD"]

sf = pd.read_parquet(D + r"\sales_fact.parquet",
                     columns=["billing_date", "sold_to_sap", "saty", "billed_qty"])
sf["month"] = sf.billing_date.dt.strftime("%Y-%m")

axis, y, m = [], 2023, 1
while (y, m) <= (2026, 8):
    axis.append(f"{y:04d}-{m:02d}")
    m += 1
    if m == 13:
        y, m = y + 1, 1

print("ALL rows, before any exclusion:")
seen = set(sf.month.unique())
missing = [a for a in axis if a not in seen]
print("  months with no rows at all:", missing)

print("\nafter the document-type exclusion (CR, RE, DR, ZDR, FD, blank):")
k = sf[~sf.saty.isin(EXCL) & sf.saty.notna()]
seen2 = set(k.month.unique())
missing2 = [a for a in axis if a not in seen2]
print("  months with no rows:", missing2)
for a in missing2:
    tot_raw = len(sf[sf.month == a])
    print(f"    {a}: {tot_raw} raw rows, 0 kept")
    if tot_raw:
        print("      saty on those rows:", sf[sf.month == a].saty.value_counts(dropna=False).to_dict())

print("\nlate-2026 months, kept:")
for a in ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]:
    g = sf[sf.month == a]
    kk = g[~g.saty.isin(EXCL) & g.saty.notna()]
    print(f"  {a}: raw rows {len(g):>6}  kept rows {len(kk):>6}  "
          f"kept units {kk.billed_qty.sum():>12,.0f}")
