"""Read-only probe 10: the KS_AllProducts column is a free, already-collected
crossref we have never parsed. Plus the final 'searchable object' count.
"""
import re
import pandas as pd

pd.set_option("display.width", 260)
ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


t = pd.read_csv(ROOT + r"\04_tools\delegation\state\refresh_tiers_LOCAL.csv", dtype={"part_no": str})
t["part_no"] = z(t["part_no"])
t["billed_eur_t12m"] = pd.to_numeric(t["billed_eur_t12m"])
tier = dict(zip(t.part_no, t.tier))
billed = dict(zip(t.part_no, t.billed_eur_t12m))
tot = t.billed_eur_t12m.sum()

out = {}
for f in [ROOT + r"\04_tools\autodoc_scraper\_snapshots\2026-09-22\ks_results.csv",
          ROOT + r"\04_tools\autodoc_scraper\_snapshots\2026-09-22\ks_bfs_high_euro_results.csv"]:
    d = pd.read_csv(f, dtype=str)
    d["pn"] = z(d["PN"])
    for _, r in d.iterrows():
        s = r.get("KS_AllProducts")
        if isinstance(s, str) and s.strip():
            out.setdefault(r.pn, []).append((r.get("Status"), s.strip()[:400]))

print("part numbers with a KS_AllProducts string: %d" % len(out))
sample = list(out.items())[:3]
for pn, v in sample:
    print("\n--- %s (status %s)" % (pn, v[0][0]))
    print("   ", v[0][1])

# try to count brand/number pairs
pair_re = re.compile(r"\b([A-Z][A-Za-z0-9+&\.\- ]{2,28}?)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-\./ ]{2,20})\b")
n_with_pairs = 0
allpairs = set()
for pn, lst in out.items():
    s = lst[0][1]
    hits = pair_re.findall(s)
    if hits:
        n_with_pairs += 1
        for b, c in hits:
            allpairs.add((b.strip().upper(), c.strip().upper()))
print("\npart numbers where the string looks parseable: %d of %d" % (n_with_pairs, len(out)))
print("raw brand/number pairs extracted: %d" % len(allpairs))

# how far do our IAM search objects reach?
e = pd.read_excel(ROOT + r"\01_data\Eucon_Online28072025.xlsx",
                  sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
em = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="Online 15032024", dtype=str)
em["pn"] = z(em["Searched Part Number"])
old = pd.read_csv(ROOT + r"\02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv", dtype=str)
old["pn"] = z(old.isze_pn)
survey = pd.read_excel(ROOT + r"\01_data\01_Pricing\_raw\Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx",
                       sheet_name=None, dtype=str)
survey_pairs = set()
for d in survey.values():
    d.columns = [c.strip() for c in d.columns]
    for _, r in d.iterrows():
        b = str(r.get("Manufacturer Brand", "")).strip().upper()
        c = str(r.get("Competitor Part Number", "")).strip().upper()
        if b and c and b != "NAN" and c != "NAN":
            survey_pairs.add((b, c))

iam_objects = set()
under = {}
for df, bcol, ccol in [(e, "Brand", "Part Number"), (em, "Brand", "Part Number")]:
    for _, r in df.iterrows():
        b = str(r.get(bcol, "")).strip().upper()
        c = str(r.get(ccol, "")).strip().upper()
        if b and c and b != "NAN" and c != "NAN":
            iam_objects.add((b, c))
            under.setdefault(c, set()).add(r["pn"])
for _, r in old.iterrows():
    b = str(r.Competitor_Brand).strip().upper()
    c = str(r.competitor_pn).strip().upper()
    if b and c:
        iam_objects.add((b, c))
        under.setdefault(c, set()).add(r["pn"])
for b, c in survey_pairs:
    iam_objects.add((b, c))

print("\nsearchable IAM brand+number objects: %d" % len(iam_objects))
print("distinct IAM numbers               : %d" % len(set(c for _, c in iam_objects)))
print("distinct IAM brands               : %d" % len(set(b for b, _ in iam_objects)))

# the value of the Isuzu numbers those IAM objects sit under
covered = set()
for c, pns in under.items():
    covered |= pns
covered = {p for p in covered if p in tier}
print("\nthe Isuzu numbers those objects sit under: %d, EUR %s (%.1f%% of the billed book)"
      % (len(covered), f"{sum(billed.get(p, 0) for p in covered):,.0f}",
         100 * sum(billed.get(p, 0) for p in covered) / tot))

A = t[t.tier == "A"]
print("\nTier A that a KS sitemap or IAM search could reach today:")
reach = set(covered) | set(out.keys())
ra = A[A.part_no.isin(reach)]
print("   %d of %d, EUR %s (%.1f%% of Tier A)" % (len(ra), len(A), f"{ra.billed_eur_t12m.sum():,.0f}",
                                                 100 * ra.billed_eur_t12m.sum() / A.billed_eur_t12m.sum()))
print("\nTier A still with NO seed object at all: %d, EUR %s (%.1f%% of Tier A)"
      % (len(A) - len(ra), f"{A[~A.part_no.isin(reach)].billed_eur_t12m.sum():,.0f}",
         100 * A[~A.part_no.isin(reach)].billed_eur_t12m.sum() / A.billed_eur_t12m.sum()))
