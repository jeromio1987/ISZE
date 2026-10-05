"""Check what sits outside the four market codes on the 2026-09-22 simulation base."""
import pandas as pd
from pathlib import Path

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
d = pd.read_csv(D / "price_bp_weighted_compare_pn.csv",
                dtype={"part_number": str, "customer_code": str})
d = d[d["in_scope"] == True].copy()  # noqa: E712
REG = ("WEST", "SOUTH", "EAST", "NORDICS", "MIDDLE_EAST")
in4 = (d["region"].isin(REG)
       | d["customer_code"].astype(str).str.strip().eq("1799")
       | d["customer_code"].astype(str).str.strip().eq("1797")
       | d["region"].eq("CIS"))
out = d[~in4]
print("outside lines", len(out), "billed", round(out["net_sales_value"].sum(), 2))
print(out.groupby(["region", "gps_db_label"]).agg(
    lines=("part_number", "size"), billed=("net_sales_value", "sum")).to_string())
print()
print("immovable rows by source label presence, whole book")
d["pn"] = d["part_number"].astype(str).str.strip().str.zfill(10)
pl = pd.read_parquet(D / "pricing_list_pn.parquet",
                     columns=["part_number", "source", "is_superseded_row"])
pl = pl[pl["is_superseded_row"] != True]  # noqa: E712
pl["pn"] = pl["part_number"].astype(str).str.strip().str.zfill(10)
pl = pl.drop_duplicates("pn")[["pn", "source"]]
d = d.merge(pl, on="pn", how="left")
rec = d["unpriced_reason"].isna()
print("published recipe rows", int(rec.sum()), "px_both rows",
      int((d["bp_new_jpy"].notna() & d["bp_prior_revised"].notna()).sum()))
print("recipe == px_both:", bool((rec == (d["bp_new_jpy"].notna() & d["bp_prior_revised"].notna())).all()))
