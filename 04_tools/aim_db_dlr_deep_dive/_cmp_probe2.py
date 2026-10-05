"""Probe: GREECE billing presence, blank doc types, ITUK dealer-level file."""
from pathlib import Path
import pandas as pd

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
EXCL = ["CR", "RE", "DR", "ZDR", "FD"]

dd = pd.read_csv(DER / "distributor_dimension.csv", dtype=str)
print(dd[["sold_to_sap", "distributor_code", "gps_db_label", "scope", "network_role"]]
      .to_string())

sf = pd.read_parquet(DER / "sales_fact.parquet",
                     columns=["billing_date", "sold_to_sap", "saty", "billed_qty"])
sf["sap"] = sf["sold_to_sap"].astype(str).str.replace(r"\.0$", "", regex=True)
print("\nsold_to_sap present in sales_fact:", sorted(sf["sap"].unique()))
print("sold_to_sap 66 rows:", int((sf["sap"] == "66").sum()))

for sap in ["519", "92", "76", "2575", "2574", "1799"]:
    g = sf[sf["sap"] == sap]
    if not len(g):
        continue
    m = g["billing_date"].dt.strftime("%Y-%m")
    print(f"\nsap {sap}: {len(g)} rows, {m.min()}..{m.max()}")
    print("  saty:", g["saty"].value_counts(dropna=False).to_dict())
    blank = g[g["saty"].isna()]
    if len(blank):
        print("  blank saty months:", blank["billing_date"].dt.strftime("%Y-%m")
              .value_counts().sort_index().to_dict())
    # months with rows at all
    print("  months with any rows:", sorted(m.unique()))

print("\n--- ITUK dealer-level file ---")
f = DER / "dealer_sellout_long_ITUK_CY2025.csv"
d = pd.read_csv(f, dtype=str, low_memory=False)
d["q"] = pd.to_numeric(d["qty"], errors="coerce").fillna(0)
mo = d[d["period_grain"] == "month"]
to = d[d["period_grain"].isin(["year", "ytd"])]
print(f.name, "month rows qty", mo["q"].sum(), "total row qty", to["q"].sum(),
      "| periods", sorted(to["period"].unique()))
print("dealers:", d["dealer_name"].nunique())
