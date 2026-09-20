"""Why does heavy truck show as a sliver in almost every PMS category?

Jerome: "what does this mean no F series parts were sold for other PMS categories???"

Three candidate explanations, and they need separating:
  A. F-series parts exist but their billing is genuinely small
  B. F-series parts exist and bill, but they are SHARED with N-series so they go to 'shared'
  C. F-series-only part numbers were never decoded, so they cannot be placed at all
"""

import json

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

# ---- 1. What does the cross-reference say F-series-only parts are, by category?
xref = pd.read_csv(DER + r"\genuine_bvp_crossref.csv", dtype=str, low_memory=False)
pms = xref[xref.pms_category.notna()].copy()
pms["vm"] = pms.vehicle_model.astype(str).str.upper()


def is_f(s):
    return any(k in s for k in ("FRR", "FSR", "FTR", "FVR", "FVM", "FSS", "FTS", "FVZ",
                                "GVR", "FV*", "FS*", "F*"))


def is_n(s):
    return any(k in s for k in ("NPR", "NQR", "NMR", "NLR", "NKR", "NPS", "N*R", "NNR"))


pms["only_f"] = pms.vm.map(lambda s: is_f(s) and not is_n(s))
f_only_pns = set(pms.loc[pms.only_f, "genuine_pn"].map(norm))

# ---- 2. What is actually billed on them?
sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["pn"] = sf.part_number.map(norm)
sf["year"] = pd.to_datetime(sf.billing_date, errors="coerce").dt.year
cat = pd.read_csv(DER + r"\bvp_pn_dimension.csv", dtype=str, low_memory=False)
cat["pn"] = cat.part_number.map(norm)
cat = cat[cat.pms_category.notna()].drop_duplicates("pn")[["pn", "pms_category"]]

f_bill = sf[sf.pn.isin(f_only_pns)].merge(cat, on="pn", how="left")
print("=" * 100)
print("A. F-SERIES-ONLY PART NUMBERS FROM THE CROSS-REFERENCE: what do they bill?")
print("=" * 100)
print(f"  distinct F-only PNs : {len(f_only_pns)}")
print(f"  billed on them      : EUR {f_bill.net_sales_value.sum():,.0f} "
      f"({100*f_bill.net_sales_value.sum()/sf.net_sales_value.sum():.2f}% of the book)")
print()
if not f_bill.empty:
    g = (f_bill.groupby("pms_category")
         .agg(pns=("pn", "nunique"), eur=("net_sales_value", "sum"),
              units=("billed_qty", "sum"))
         .sort_values("eur", ascending=False))
    print(g.round(0).to_string())

# ---- 3. How did those same part numbers get classified in the shipped output?
band = pd.read_csv(DER + r"\epc_decode_batch1_banded_20260919.csv")
band["pn"] = band.pn.map(norm)
print()
print("=" * 100)
print("B. WERE THE F-ONLY PARTS EVEN DECODED?")
print("=" * 100)
decoded = set(band.pn)
in_dec = f_only_pns & decoded
print(f"  F-only PNs in the decode batch : {len(in_dec)} of {len(f_only_pns)}")
print(f"  -> NOT decoded                : {len(f_only_pns - decoded)}")
if in_dec:
    sub = band[band.pn.isin(in_dec)]
    print()
    print("  how the decoded ones were classed:")
    print(sub.band_status.value_counts().to_string())
    print()
    print(sub[["pn", "tonnage_band", "band_count", "band_status"]].head(15).to_string(index=False))

# ---- 4. The shipped family file: what is heavy_truck holding?
ev = pd.read_csv(DER + r"\pms_family_evolution_both_clocks.csv")
cy = ev[(ev.clock == "CY") & (ev.period == 2025)]
print()
print("=" * 100)
print("C. 2025 BILLED EURO BY FAMILY VALUE, AS SHIPPED")
print("=" * 100)
g = cy.groupby("family_label").billed_eur.sum().sort_values(ascending=False)
for k, v in g.items():
    print(f"  {k:44s} EUR {v:14,.0f}  {100*v/g.sum():5.1f}%")

print()
print("=" * 100)
print("D. WHERE DOES F-SERIES BILLING ACTUALLY SIT?")
print("=" * 100)
# Heavy parts that ALSO fit trucks land in shared. Quantify that.
pms["also_n"] = pms.vm.map(lambda s: is_n(s) and is_f(s))
f_touch = set(pms.loc[pms.vm.map(is_f), "genuine_pn"].map(norm))
shared_f = f_touch & set(pms.loc[pms.also_n, "genuine_pn"].map(norm))
print(f"  PNs that fit F-series            : {len(f_touch)}")
print(f"  ... of which ALSO fit N-series   : {len(shared_f)}")
sh_bill = sf[sf.pn.isin(shared_f)].net_sales_value.sum()
print(f"  billed on the F+N shared ones    : EUR {sh_bill:,.0f}")
print()
print("  So F-series money is split three ways and only one of them is visible above:")
print(f"    - F-only, decoded, single-band : small (see B)")
print(f"    - F+N shared                   : EUR {sh_bill:,.0f} -> pooled as shared_across_families")
print(f"    - F-only but never decoded     : see B")
