"""Read-only probe 9: the definitive 'everything we hold' crossref union, and the
'parts-only' version that strips oil, tools and fee lines out of the seed list.
"""
import pandas as pd

pd.set_option("display.width", 260)
ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


t = pd.read_csv(ROOT + r"\04_tools\delegation\state\refresh_tiers_LOCAL.csv", dtype={"part_no": str})
t["part_no"] = z(t["part_no"])
t["billed_eur_t12m"] = pd.to_numeric(t["billed_eur_t12m"])

m = pd.read_csv(ROOT + r"\01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv", dtype=str)
m["part_number"] = z(m["part_number"])
lk = dict(zip(m.part_number, m.line_kind))
t["line_kind"] = t.part_no.map(lk).fillna("(not on master)")
parts_only = t[t.line_kind == "part"].copy()
print("seed list: %d lines, EUR %s. parts only: %d lines, EUR %s (%.1f%% of the total)"
      % (len(t), f"{t.billed_eur_t12m.sum():,.0f}", len(parts_only),
         f"{parts_only.billed_eur_t12m.sum():,.0f}", 100 * parts_only.billed_eur_t12m.sum() / t.billed_eur_t12m.sum()))

A = parts_only[parts_only.tier == "A"]
print("Tier A parts only: %d lines, EUR %s" % (len(A), f"{A.billed_eur_t12m.sum():,.0f}"))
nonpart_A = t[(t.tier == "A") & (t.line_kind != "part")]
print("removed from Tier A: %s" % ", ".join(
    "%s (%s, EUR %s)" % (r.part_no, r.line_kind, f"{r.billed_eur_t12m:,.0f}") for r in nonpart_A.itertuples()))

# every crossref source
old = pd.read_csv(ROOT + r"\02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv", dtype=str)
old["pn"] = z(old.isze_pn)
e = pd.read_excel(ROOT + r"\01_data\Eucon_Online28072025.xlsx",
                  sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
em = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="Online 15032024", dtype=str)
em["pn"] = z(em["Searched Part Number"])
r = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="RRP MODE", dtype=str)
r["pn"] = z(r["Searched Part Number"])
survey = pd.read_excel(ROOT + r"\01_data\01_Pricing\_raw\Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx",
                       sheet_name=None, dtype=str)
survey_pn = set()
oem_pn = set()
for d in survey.values():
    d.columns = [c.strip() for c in d.columns]
    w = d[d["Competitor Part Number"].fillna("").str.strip() != ""]
    survey_pn |= set(z(w["Isuzu Part Number"]))
b = pd.read_csv(ROOT + r"\01_data\00_derived\genuine_bvp_crossref.csv", dtype=str)
b["genuine_pn"] = z(b["genuine_pn"])
oem = pd.read_csv(ROOT + r"\02_dashboards\Data\00_derived\eucon_comparable_oem_gap_20260810.csv", dtype=str)
oem_pn = set(z(oem.isze_pn))

sets = {
    "Eucon crossref 2026-03": set(old.pn),
    "Eucon Online 2025-07": set(e.pn),
    "Eucon March Online 2024": set(em.pn),
    "Eucon March RRP MODE": set(r.pn),
    "Eucon UK 2023 IAM survey": survey_pn,
    "Isuzu genuine -> BVP": set(b.genuine_pn),
}
union = set().union(*sets.values())
competitor_equiv = union
peer_oe = oem_pn

B = parts_only
print("\n=== against PARTS ONLY (%d lines, EUR %s) ===" % (len(B), f"{B.billed_eur_t12m.sum():,.0f}"))
tot = B.billed_eur_t12m.sum()
for name, s in sets.items():
    mm = B.part_no.isin(s)
    aa = B[(B.tier == "A") & B.part_no.isin(s)]
    print("   %-26s %5d parts EUR %12s (%4.1f%%) | tier A %3d of %d, EUR %s"
          % (name, mm.sum(), f"{B[mm].billed_eur_t12m.sum():,.0f}", 100 * B[mm].billed_eur_t12m.sum() / tot,
             len(aa), len(A), f"{aa.billed_eur_t12m.sum():,.0f}"))
mm = B.part_no.isin(competitor_equiv)
aa = B[(B.tier == "A") & B.part_no.isin(competitor_equiv)]
print("   %-26s %5d parts EUR %12s (%4.1f%%) | tier A %3d of %d (%.1f%%), EUR %s (%.1f%% of A)"
      % ("ANY competitor equivalent", mm.sum(), f"{B[mm].billed_eur_t12m.sum():,.0f}",
         100 * B[mm].billed_eur_t12m.sum() / tot, len(aa), len(A), 100 * len(aa) / len(A),
         f"{aa.billed_eur_t12m.sum():,.0f}", 100 * aa.billed_eur_t12m.sum() / A.billed_eur_t12m.sum()))
mm = B.part_no.isin(competitor_equiv | peer_oe)
aa = B[(B.tier == "A") & B.part_no.isin(competitor_equiv | peer_oe)]
print("   %-26s %5d parts EUR %12s (%4.1f%%) | tier A %3d of %d (%.1f%%), EUR %s (%.1f%% of A)"
      % ("+ peer OE map", mm.sum(), f"{B[mm].billed_eur_t12m.sum():,.0f}",
         100 * B[mm].billed_eur_t12m.sum() / tot, len(aa), len(A), 100 * len(aa) / len(A),
         f"{aa.billed_eur_t12m.sum():,.0f}", 100 * aa.billed_eur_t12m.sum() / A.billed_eur_t12m.sum()))

print("\nTier A with NOTHING (no competitor number, no peer OE): %d of %d, EUR %s (%.1f%% of A)"
      % (len(A) - len(A[A.part_no.isin(competitor_equiv | peer_oe)]), len(A),
         f"{A[~A.part_no.isin(competitor_equiv | peer_oe)].billed_eur_t12m.sum():,.0f}",
         100 * A[~A.part_no.isin(competitor_equiv | peer_oe)].billed_eur_t12m.sum() / A.billed_eur_t12m.sum()))

print("\n=== searched by Isuzu number today. What if we searched by IAM number instead? ===")
pairs = set()
for df in (e, em):
    for _, rr in df.iterrows():
        br = str(rr.get("Brand", "")).strip().upper()
        pn = str(rr.get("Part Number", "")).strip().upper()
        if br and pn and pn != "NAN":
            pairs.add((br, pn))
for _, rr in old.iterrows():
    pairs.add((str(rr.Competitor_Brand).strip().upper(), str(rr.competitor_pn).strip().upper()))
print("   IAM brand+number pairs we could search with: %d" % len(pairs))
print("   these sit under %d Isuzu numbers" % len(competitor_equiv))
