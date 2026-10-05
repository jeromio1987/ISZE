"""Corroborate the EPC's claim independently, from the billing.

The EPC says the biggest 'loss' part numbers are D-Max/light-vehicle parts, not truck parts. The
billing can confirm or deny that without the EPC: D-Max parts should concentrate in IUK (the UK
light-commercial distributor) and the truck parts should concentrate in ITUK.

If the EPC is right, these two groups should look completely different by market.
"""

import pandas as pd

DER = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["_pn"] = sf.part_number.map(norm)
dim = pd.read_csv(DER + r"\distributor_dimension.csv")
sf["db"] = sf.sold_to_sap.map(dict(zip(dim.sold_to_sap, dim.distributor_code)))

# The EPC verdicts from the ten-part-number test.
EPC = {
    "8983767550": ("D-Max / pickup", "front brake rotor"),
    "8978808250": ("D-Max / pickup", "PM sensor"),
    "7552348290": ("D-Max / pickup", "steering gear"),
    "8982878080": ("truck F&G + N", "filter assembly"),
    "8983528481": ("truck F&G + N + bus", "NOx sensor"),
    "8982447940": ("truck N-series only", "front brake pad"),
    "8982169220": ("truck N-series only", "front brake pad (N35)"),
}

print("=" * 104)
print("WHERE EACH PART NUMBER IS ACTUALLY BILLED — top markets by euro")
print("=" * 104)
for pn, (verdict, desc) in EPC.items():
    g = sf[sf._pn == norm(pn)]
    if g.empty:
        print(f"{pn}  {desc:28s}  no billing")
        continue
    tot = g.net_sales_value.sum()
    mk = (g.groupby("db").net_sales_value.sum().sort_values(ascending=False).head(4))
    shares = ", ".join(f"{i} {100*v/tot:.0f}%" for i, v in mk.items() if pd.notna(i))
    print(f"{pn}  {desc:28s}  EUR {tot:10,.0f}")
    print(f"{'':12s}  EPC says: {verdict:22s}  billed: {shares}")

print()
print("=" * 104)
print("THE TEST — do the two groups separate by market?")
print("=" * 104)
dm = [norm(p) for p, (v, _) in EPC.items() if v.startswith("D-Max")]
tr = [norm(p) for p, (v, _) in EPC.items() if v.startswith("truck")]

for label, pns in (("EPC says D-Max / pickup", dm), ("EPC says truck", tr)):
    g = sf[sf._pn.isin(pns)]
    tot = g.net_sales_value.sum()
    by = g.groupby("db").net_sales_value.sum().sort_values(ascending=False)
    print(f"\n{label}: EUR {tot:,.0f} total")
    for i, v in by.head(6).items():
        print(f"    {i:12s} {100*v/tot:5.1f}%")
    lcv = by.get("IUK", 0) + by.get("UMI", 0)
    print(f"    -> light-vehicle distributors (IUK+UMI) = {100*lcv/tot:.1f}% of the group")

print()
print("=" * 104)
print("READING")
print("=" * 104)
print("  IUK is the UK light-commercial (D-Max) distributor; ITUK is UK trucks.")
print("  If the D-Max group loads onto IUK and the truck group onto ITUK, the EPC is corroborated")
print("  and the two must be separated in any tonnage view.")
