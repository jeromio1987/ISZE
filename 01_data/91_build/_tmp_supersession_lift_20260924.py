"""Read-only probe 6: does the price list's own supersession map unlock crossref
coverage for the Tier A parts that have none?

The price list carries part_number -> newest_pn (90,823 pairs). A Tier A part that has
been superseded should be searched on its newest number, not the number we bill.
"""
import pandas as pd

pd.set_option("display.width", 260)
ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


t = pd.read_csv(ROOT + r"\04_tools\delegation\state\refresh_tiers_LOCAL.csv", dtype={"part_no": str})
t["part_no"] = z(t["part_no"])
t["billed_eur_t12m"] = pd.to_numeric(t["billed_eur_t12m"])
tot = t["billed_eur_t12m"].sum()

pl = pd.read_parquet(ROOT + r"\01_data\00_derived\pricing_pr00_ie40.parquet",
                     columns=["part_number", "newest_pn", "description", "sp_eur"])
pl["part_no"] = z(pl["part_number"])
pl["newest"] = z(pl["newest_pn"])
sup = pl[pl.part_no != pl.newest][["part_no", "newest"]].drop_duplicates("part_no")
old2new = dict(zip(sup.part_no, sup.newest))
print("price list: %d rows, %d distinct part numbers, %d supersession pairs"
      % (len(pl), pl.part_no.nunique(), len(sup)))
print("   newest numbers that are themselves the successor of something: %d" % sup.newest.nunique())

# crossref sources
old = pd.read_csv(ROOT + r"\02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv", dtype=str)
old["isze_pn"] = z(old["isze_pn"])
e = pd.read_excel(ROOT + r"\01_data\Eucon_Online28072025.xlsx",
                  sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
r = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="RRP MODE", dtype=str)
r["pn"] = z(r["Searched Part Number"])
survey = pd.read_excel(ROOT + r"\01_data\01_Pricing\_raw\Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx",
                       sheet_name=None, dtype=str)
survey_pn = set()
for d in survey.values():
    d.columns = [c.strip() for c in d.columns]
    w = d[d["Competitor Part Number"].fillna("").str.strip() != ""]
    survey_pn |= set(z(w["Isuzu Part Number"]))
b = pd.read_csv(ROOT + r"\01_data\00_derived\genuine_bvp_crossref.csv", dtype=str)
b["genuine_pn"] = z(b["genuine_pn"])
xref = set(old.isze_pn) | set(e.pn) | set(r.pn) | survey_pn | set(b.genuine_pn)

A = t[t.tier == "A"].copy()
A["has_xref_direct"] = A.part_no.isin(xref)
A["newest"] = A.part_no.map(old2new)
A["is_superseded"] = A.newest.notna()
A["has_xref_via_newest"] = A.newest.fillna("").isin(xref)

print("\nTier A, %d parts:" % len(A))
print("   superseded in the price list : %d (%.1f%%)"
      % (A.is_superseded.sum(), 100 * A.is_superseded.mean()))
print("   already have a crossref      : %d" % A.has_xref_direct.sum())
print("   no crossref, but superseded  : %d" % ((~A.has_xref_direct) & A.is_superseded).sum())
print("   crossref found on the successor number: %d"
      % ((~A.has_xref_direct) & A.has_xref_via_newest).sum())

gain = A[(~A.has_xref_direct) & A.has_xref_via_newest]
print("\n   that path adds %d Tier A parts, EUR %s billed" % (len(gain), f"{gain.billed_eur_t12m.sum():,.0f}"))
newcov = A[A.has_xref_direct | A.has_xref_via_newest]
print("   Tier A crossref coverage: %d of %d (%.1f%%), EUR %s (%.1f%% of Tier A billed)"
      % (len(newcov), len(A), 100 * len(newcov) / len(A), f"{newcov.billed_eur_t12m.sum():,.0f}",
         100 * newcov.billed_eur_t12m.sum() / A.billed_eur_t12m.sum()))
oldcov = A[A.has_xref_direct]
print("   before the supersession path: %d of %d (%.1f%%), EUR %s (%.1f%%)"
      % (len(oldcov), len(A), 100 * len(oldcov) / len(A), f"{oldcov.billed_eur_t12m.sum():,.0f}",
         100 * oldcov.billed_eur_t12m.sum() / A.billed_eur_t12m.sum()))

print("\n   is a superseded part really the same part at a new number? check the descriptions:")
chk = A[A.is_superseded & ~A.has_xref_direct].head(8).copy()
pld = pl.drop_duplicates("part_no").set_index("part_no")
pldn = pl.drop_duplicates("newest").set_index("newest")
chk["desc_old"] = chk.part_no.map(pld.description)
chk["desc_new"] = chk.newest.map(pldn.description)
print(chk[["part_no", "newest", "desc_old", "desc_new", "billed_eur_t12m"]].to_string(index=False))

print("\n=== whole book ===")
for label, col in [("direct only", "has_xref_direct"), ("direct + successor", None)]:
    if col:
        m = t.part_no.isin(xref)
    else:
        nn = t.part_no.map(old2new)
        m = t.part_no.isin(xref) | nn.fillna("").isin(xref)
    print("   %-20s %5d parts (%.1f%%), EUR %s (%.1f%% of billed)"
          % (label, m.sum(), 100 * m.mean(), f"{t[m].billed_eur_t12m.sum():,.0f}",
             100 * t[m].billed_eur_t12m.sum() / tot))

print("\n=== how many billed parts are superseded at all ===")
nn = t.part_no.map(old2new)
print("   %d of %d (%.1f%%), EUR %s (%.1f%% of billed)"
      % (nn.notna().sum(), len(t), 100 * nn.notna().mean(),
         f"{t[nn.notna()].billed_eur_t12m.sum():,.0f}", 100 * t[nn.notna()].billed_eur_t12m.sum() / tot))
