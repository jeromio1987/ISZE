"""Read-only probe 7: the full matching asset inventory, and what each source can be
searched by. Answers 'what do we actually hold, and what is it worth as a seed list?'
"""
import json
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
A = set(t[t.tier == "A"].part_no)
AB = set(t[t.tier.isin(["A", "B"])].part_no)

rows = []

# 1. Eucon PartsPool 2026-03 crossref (the current 44)
x = pd.read_csv(ROOT + r"\02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv", dtype=str)
x["isze_pn"] = z(x["isze_pn"])
rows.append(("Eucon crossref 2026-03 (PartsPool, Autodoc DE/NO)", "Isuzu PN -> IAM brand+number, DE/NO online price",
             x.isze_pn.nunique(), x.competitor_pn.nunique(), "2026-03-29"))

# 2. Eucon Online 2025-07 (new)
e = pd.read_excel(ROOT + r"\01_data\Eucon_Online28072025.xlsx",
                  sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
e_pairs = (e.Brand.fillna("") + "|" + e["Part Number"].fillna("")).nunique()
rows.append(("Eucon Online 2025-07 (NEW file)", "Isuzu PN -> IAM brand+number; own-number EUR price", 
             e.pn.nunique(), e_pairs, "2025-07-28"))

# 3. Eucon March 2024 - Online sheet
m = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="Online 15032024", dtype=str)
m["pn"] = z(m["Searched Part Number"])
m_pairs = (m.Brand.fillna("") + "|" + m["Part Number"].fillna("")).nunique()
rows.append(("Eucon March 2024 - Online (NEW file)", "Isuzu PN -> IAM brand+number + webshop price",
             m.pn.nunique(), m_pairs, "2024-03-15"))

# 4. Eucon March 2024 - RRP MODE
r = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="RRP MODE", dtype=str)
r["pn"] = z(r["Searched Part Number"])
rows.append(("Eucon March 2024 - RRP MODE (NEW file)", "Isuzu PN -> OE RRP EUR + supersession flag",
             r.pn.nunique(), 0, "various 2022-06 / 2023"))

# 5. Eucon UK/ITUK 2023 IAM survey (crossref content unused today)
survey = pd.read_excel(ROOT + r"\01_data\01_Pricing\_raw\Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx",
                       sheet_name=None, dtype=str)
sp = []
for d in survey.values():
    d.columns = [c.strip() for c in d.columns]
    sp.append(d)
s = pd.concat(sp, ignore_index=True)
s["pn"] = z(s["Isuzu Part Number"])
sw = s[s["Competitor Part Number"].fillna("").str.strip() != ""]
rows.append(("Eucon UK/ITUK 2023 IAM survey", "Isuzu PN -> IAM brand+number; UK workshop price",
             sw.pn.nunique(), sw["Competitor Part Number"].nunique(), "2023 (file 2024-01-09)"))

# 6. Eucon UK/ITUK 2023 OEM survey -> peer OE numbers (not aftermarket)
oem = pd.read_csv(ROOT + r"\02_dashboards\Data\00_derived\eucon_comparable_oem_gap_20260810.csv", dtype=str)
rows.append(("Eucon UK/ITUK 2023 OEM survey", "Isuzu PN -> peer OE number (DAF/Toyota/Ford), COMPARABLE flagged",
             oem.isze_pn.nunique(), oem.peer_oe_pn.nunique(), "2023"))

# 7. price list supersession
pl = pd.read_parquet(ROOT + r"\01_data\00_derived\pricing_pr00_ie40.parquet",
                     columns=["part_number", "newest_pn"])
pl["part_no"] = z(pl["part_number"]); pl["newest"] = z(pl["newest_pn"])
sup = pl[pl.part_no != pl.newest]
rows.append(("Price list IE40 supersession", "old Isuzu PN -> newest Isuzu PN",
             sup.part_no.nunique(), sup.newest.nunique(), "as of the current list"))

# 8. BVP crossref (Isuzu Japan -> the BVP value line)
b = pd.read_csv(ROOT + r"\01_data\00_derived\genuine_bvp_crossref.csv", dtype=str)
b["genuine_pn"] = z(b["genuine_pn"])
rows.append(("Isuzu genuine -> BVP value line", "Isuzu PN -> BVP PN (the maker's own cheaper range)",
             b.genuine_pn.nunique(), b.bvp_pn.nunique(), "catalogue"))

# 9. spareto probe
try:
    sp2 = json.load(open(ROOT + r"\01_data\01_Pricing\_raw\spareto_crossrefs_20260918.json"))
    n_pn = len(sp2); n_iam = sum(len(v) for v in sp2.values())
    rows.append(("Spareto probe 2026-09", "Isuzu PN -> IAM brand+number + EUR price",
                 n_pn, n_iam, "2026-09-18"))
except Exception as ex:
    print("spareto unreadable:", ex)

print("%-46s %-62s %6s %7s %s" % ("source", "what it holds", "Isuzu", "other", "vintage"))
print("-" * 170)
for a, bb, c, d, ee in rows:
    print("%-46s %-62s %6d %7d %s" % (a, bb, c, d, ee))

print("\n=== value of each source as a SEED LIST for tier A ===")
print("%-46s %10s %8s %14s" % ("source", "tier A pns", "% of A", "billed EUR"))
print("-" * 90)
sets = {
    "Eucon crossref 2026-03": set(x.isze_pn),
    "Eucon Online 2025-07": set(e.pn),
    "Eucon March Online 2024": set(m.pn),
    "Eucon March RRP MODE": set(r.pn),
    "Eucon UK 2023 IAM survey": set(sw.pn),
    "BVP crossref": set(b.genuine_pn),
}
for name, ss in sets.items():
    tt = t[t.part_no.isin(ss)]
    ta = tt[tt.tier == "A"]
    print("%-46s %10d %7.1f%% %14s" % (name, len(ta), 100 * len(ta) / 491, f"{ta.billed_eur_t12m.sum():,.0f}"))
allx = set().union(*sets.values())
tt = t[t.part_no.isin(allx)]
ta = tt[tt.tier == "A"]
print("%-46s %10d %7.1f%% %14s" % ("UNION", len(ta), 100 * len(ta) / 491, f"{ta.billed_eur_t12m.sum():,.0f}"))

print("\n=== how many IAM brand+number pairs do we hold as searchable objects? ===")
pairs = set()
for df, brand_col, pn_col, tag in [(e, "Brand", "Part Number", "eucon2025"),
                                   (m, "Brand", "Part Number", "eucon2024")]:
    for _, rr in df.iterrows():
        br = str(rr[brand_col]).strip().upper()
        pn = str(rr[pn_col]).strip().upper()
        if br and pn and pn != "NAN":
            pairs.add((br, pn, tag))
for _, rr in sw.iterrows():
    br = str(rr["Manufacturer Brand"]).strip().upper()
    pn = str(rr["Competitor Part Number"]).strip().upper()
    if br and pn:
        pairs.add((br, pn, "survey2023"))
for _, rr in x.iterrows():
    pairs.add((str(rr.Competitor_Brand).strip().upper(), str(rr.competitor_pn).strip().upper(), "crossref2026"))
allp = set((a2, b2) for a2, b2, _ in pairs)
print("   distinct IAM brand+number combinations: %d" % len(allp))
print("   distinct IAM numbers alone           : %d" % len(set(p2 for _, p2 in allp)))
print("   distinct brands                      : %d" % len(set(b2 for b2, _ in allp)))
top = pd.Series([b2 for b2, _ in allp]).value_counts().head(20)
print("\n   most frequent brands:")
print(top.to_string())
