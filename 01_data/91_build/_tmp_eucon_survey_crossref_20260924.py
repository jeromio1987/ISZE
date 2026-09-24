"""Read-only probe 4: the 2023 UK/ITUK Eucon IAM survey as a CROSSREF source
(competitor brand + competitor part number), not as a price source.

The ledger currently loads this file as prices (68 rows). Its crossref content is
unused. This probe measures what it would add to the matching graph.
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
tier = dict(zip(t.part_no, t.tier))
billed = dict(zip(t.part_no, t.billed_eur_t12m))

iam = pd.read_excel(ROOT + r"\01_data\01_Pricing\_raw\Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx",
                    sheet_name=None, dtype=str)
parts = []
for sheet, d in iam.items():
    d = d.copy()
    d["sheet"] = sheet
    parts.append(d)
s = pd.concat(parts, ignore_index=True)
s.columns = [c.strip() for c in s.columns]
s["pn"] = z(s["Isuzu Part Number"])
s["brand"] = s["Manufacturer Brand"].fillna("").str.strip()
s["cpn"] = s["Competitor Part Number"].fillna("").str.strip()
print("UK IAM survey rows: %d across sheets %s" % (len(s), list(iam.keys())))
print("   distinct Isuzu PNs              : %d" % s.pn.nunique())
print("   distinct Isuzu PNs WITH a competitor number : %d"
      % s[s.cpn != ""].pn.nunique())
print("   competitor pairs (pn|brand|cpn) : %d" % s[(s.cpn != "")].assign(
    k=s.pn + "|" + s.brand.str.upper() + "|" + s.cpn.str.upper()).k.nunique())
print("   brands                          : %d" % s[s.cpn != ""].brand.nunique())
print("   comparability values            : %s" % s["Comparability Quality"].value_counts(dropna=False).to_dict())
print("   rows with a workshop price      : %d" % s["Workshop Purchase Price"].notna().sum())

# reach into the billed book
withx = s[s.cpn != ""].pn.unique()
m = t.part_no.isin(withx)
print("\nThose %d PNs against the billed tier list: %d present, EUR %s (%.1f%% of the billed book)"
      % (len(withx), m.sum(), f"{t[m].billed_eur_t12m.sum():,.0f}", 100 * t[m].billed_eur_t12m.sum() / tot))
for tr in ["A", "B", "C"]:
    tt = t[t.tier == tr]
    mm = tt.part_no.isin(withx)
    print("     tier %s: %4d of %4d (%.1f%%), EUR %s"
          % (tr, mm.sum(), len(tt), 100 * mm.mean(), f"{tt[mm].billed_eur_t12m.sum():,.0f}"))

# overlap with what we already have
old = pd.read_csv(ROOT + r"\02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv", dtype=str)
old["isze_pn"] = z(old["isze_pn"])
e = pd.read_excel(ROOT + r"\01_data\Eucon_Online28072025.xlsx",
                  sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
have = set(old.isze_pn) | set(e.pn)
new_by_survey = sorted(set(withx) - have)
print("\nof the survey's %d crossref PNs, %d are NOT in the newer Eucon sources" % (len(withx), len(new_by_survey)))
new_in_book = [p for p in new_by_survey if p in tier]
print("   of those, %d are on the billed book, EUR %s"
      % (len(new_in_book), f"{sum(billed.get(p, 0) for p in new_in_book):,.0f}"))
for tr in ["A", "B", "C"]:
    print("     tier %s: %4d" % (tr, len([p for p in new_in_book if tier[p] == tr])))

# ITUK / HCV share - the CV hole
print("\nBy sheet:")
for sheet, d in iam.items():
    d = d.copy()
    d["pn"] = z(d["Isuzu Part Number"])
    w = d[d["Competitor Part Number"].fillna("").str.strip() != ""]
    print("   %-6s rows %4d, PNs %3d, PNs with a competitor number %3d" % (sheet, len(d), d.pn.nunique(), w.pn.nunique()))

# how many survey PNs does the ledger already price?
p = pd.read_parquet(ROOT + r"\01_data\00_derived\price_observations.parquet")
led = set(p.part_no)
print("\nledger currently holds %d Isuzu PNs. Survey crossref PNs already in the ledger: %d"
      % (len(led), len(set(withx) & led)))
print("Survey PNs with a workshop price already in the ledger: %d"
      % len(set(s[s['Workshop Purchase Price'].notna()].pn) & led))
