import pandas as pd

pn = pd.read_csv(r"01_data\00_derived\price_bp_weighted_compare_pn.csv")
ins = pn[pn.in_scope == True]
pairs = (
    ins.groupby(["distributor_code", "gps_db_label"], dropna=False)["customer_code"]
    .agg(["nunique", "first", "size"])
    .reset_index()
)
print(pairs.to_string())
print()
cust = pd.read_csv(r"01_data\00_derived\price_bp_weighted_compare_customer.csv")
print(cust[cust.level == "customer"][["customer_code", "label", "weighted_increase_pct", "value_step_eur", "l12m_billed_eur"]].to_string(index=False))
