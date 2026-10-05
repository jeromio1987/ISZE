import pandas as pd

from pathlib import Path

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")

PNS = [
    "8975509392", "8975554002", "8983860446", "8975525690", "8975595830",
    "8978461152", "8975594390", "8975509372", "8983621213", "8982606020",
    "8981532774", "8978429890",
]

# ---- basis B: 18-month billing window (what the earlier table used)
m = pd.read_csv(D / "aim_master_v1.csv", dtype=str, low_memory=False)
m["eur_b"] = pd.to_numeric(m["l12m_billed_eur"], errors="coerce").fillna(0)
b = m[m["part_number"].isin(PNS)][["part_number", "description", "aim_l2", "eur_b"]]

# ---- basis A: pricing revision base (the total I just published)
wb = pd.read_csv(D / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str})
df = wb[wb["in_scope"].astype(str).str.lower().isin(["true", "1"])].copy()
df["pn"] = df["part_number"].str.strip()
df["eur_a"] = pd.to_numeric(df["net_sales_value"], errors="coerce")
a = df.groupby("pn", as_index=False)["eur_a"].sum().rename(columns={"pn": "part_number"})

# ---- basis B total for Accident & Body (18 months)
ab_b = m[(m["aim_l1"] == "Accident & Body")]["eur_b"].sum()
# ---- basis A total for Accident & Body (pricing base)
m2 = m.drop_duplicates("part_number").set_index("part_number")
df["aim_l1"] = df["pn"].map(m2["aim_l1"])
ab_a = df.loc[df["aim_l1"] == "Accident & Body", "eur_a"].sum()

print("=" * 84)
print("THE TWELVE LINES YOU PASTED - shown on BOTH bases")
print("=" * 84)
j = b.merge(a, on="part_number", how="left").sort_values("eur_b", ascending=False)
print(j.to_string(index=False))
print()
print(f"sum of the 12, BASIS B (18-month billing window)  EUR {j['eur_b'].sum():>12,.0f}")
print(f"sum of the 12, BASIS A (pricing revision base)    EUR {j['eur_a'].sum():>12,.0f}")
print()
print("-" * 84)
print("THE TOTAL THEY SHOULD RECONCILE TO")
print("-" * 84)
print(f"Accident & Body, BASIS B (18-month window)       EUR {ab_b:>12,.0f}")
print(f"Accident & Body, BASIS A (pricing base)          EUR {ab_a:>12,.0f}")
print()
print("-" * 84)
print("RECONCILIATION")
print("-" * 84)
print(f"12 lines as share of Acc&Body on BASIS B          {100*float(j['eur_b'].sum())/ab_b:.1f}%")
print(f"12 lines as share of Acc&Body on BASIS A          {100*float(j['eur_a'].sum())/ab_a:.1f}%")
print()
print("VERDICT: the 12 lines were never a sum of the class total.")
print("They are a top-N excerpt from the 18-month window, and the totals I")
print("published later are on the pricing base. The two bases differ ~40%.")
