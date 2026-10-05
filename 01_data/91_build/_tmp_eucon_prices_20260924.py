"""Read-only probe 2: what prices the new Eucon files actually carry, and what the
existing ledger already holds. Nothing is written or fetched.
"""
import pandas as pd

pd.set_option("display.width", 260)
ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


print("=" * 100)
print("A. Eucon_Online28072025 - 'Fresh list_Export_28072025_0932'")
e = pd.read_excel(ROOT + r"\01_data\Eucon_Online28072025.xlsx",
                  sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
print("rows %d, searched PNs %d" % (len(e), e.pn.nunique()))
print("\ncountry x whether a competitor price exists:")
e["has_p"] = e["RRP"].notna().map({True: "has RRP", False: "no RRP"})
print(pd.crosstab(e.Country, e["has_p"]).to_string())
print("\nPrice Type ID x has RRP:")
print(pd.crosstab(e["Price Type ID"], e["has_p"]).to_string())
print("\nCountries present per searched PN (how many of the 5):")
per = e.groupby("pn").Country.agg(lambda s: "|".join(sorted(set(s))))
print(per.value_counts().to_string())
print("\n'Additional Part Numbers' non-empty examples:")
add = e[e["Additional Part Numbers"].notna() & (e["Additional Part Numbers"].astype(str).str.strip() != "")]
print(add[["Searched Part Number", "Brand", "Part Number", "Additional Part Numbers", "Description"]].head(12).to_string())
print("\nBrands that appear as the OE/brand row (Eucon ID 46 = Isuzu?):")
print(e[e["Part Number"].astype(str).str.match(r"^\d{10}$")].Brand.value_counts().head(10).to_string())
print("\nrows where Part Number is a 10-digit Isuzu-style number (i.e. genuine rows):",
      e["Part Number"].astype(str).str.match(r"^\d{10}$").sum())

print("\n" + "=" * 100)
print("B. Eucon_March.xlsx 'RRP MODE' - OE prices and supersession")
r = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="RRP MODE", dtype=str)
r["pn"] = z(r["Searched Part Number"])
print("rows %d, searched PNs %d" % (len(r), r.pn.nunique()))
print("Country:", r.Country.value_counts().to_dict())
print("Brand:", r.Brand.value_counts().head(6).to_dict())
print("OE Brand:", r["OE Brand"].value_counts().head(6).to_dict())
print("Supersession Info ID:", r["Supersession Info ID"].value_counts(dropna=False).head(8).to_dict())
print("Currency (RRP):", r["Currency (RRP)"].value_counts(dropna=False).to_dict())
print("rows with supersession != 0:", (r["Supersession Info ID"].fillna("0") != "0").sum())
print(r[["Country", "Searched Part Number", "Description", "Brand", "ISZE price 2024", "RRP",
         "RRP Date", "Currency (RRP)", "Supersession Info ID", "OE RRP"]].head(8).to_string())

print("\n" + "=" * 100)
print("C. existing price observations ledger")
p = pd.read_parquet(ROOT + r"\01_data\00_derived\price_observations.parquet")
print("rows %d, columns:" % len(p))
print(p.columns.tolist())
for c in p.columns:
    if p[c].nunique(dropna=True) <= 14:
        print("  %-22s %s" % (c, p[c].value_counts(dropna=False).to_dict()))
print("\npart numbers: %d unique" % p["part_no"].nunique() if "part_no" in p.columns else "")
print(p.head(4).to_string())
