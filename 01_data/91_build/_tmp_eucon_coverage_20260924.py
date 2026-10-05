"""Read-only probe: how much of the billed book does each crossref source actually cover?

Answers the open question from the Opus review of the scraper redesign (2026-09-24):
what is the cross-reference coverage of the 491 Tier A parts?

Nothing is written. Nothing is fetched.
"""
import pandas as pd

pd.set_option("display.width", 250)

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


# --- billed value base -------------------------------------------------------
t = pd.read_csv(
    ROOT + r"\04_tools\delegation\state\refresh_tiers_LOCAL.csv", dtype={"part_no": str}
)
t["part_no"] = z(t["part_no"])
t["billed_eur_t12m"] = pd.to_numeric(t["billed_eur_t12m"])
tot = t["billed_eur_t12m"].sum()
print("tier list: %d parts, EUR %s billed over 12 months" % (len(t), f"{tot:,.0f}"))
for tier in ["A", "B", "C"]:
    s = t[t.tier == tier]
    print(
        "   tier %s  %6d parts  EUR %13s  %5.1f%%"
        % (tier, len(s), f"{s.billed_eur_t12m.sum():,.0f}", 100 * s.billed_eur_t12m.sum() / tot)
    )

# --- crossref sources on disk ------------------------------------------------
x = pd.read_csv(ROOT + r"\02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv", dtype=str)
x["isze_pn"] = z(x["isze_pn"])
print("\neucon_crossref_iam_20260329.csv: %d rows, %d Isuzu PNs, %d brands, %d IAM numbers"
      % (len(x), x.isze_pn.nunique(), x.Competitor_Brand.nunique(), x.competitor_pn.nunique()))

b = pd.read_csv(ROOT + r"\01_data\00_derived\genuine_bvp_crossref.csv", dtype=str)
b["genuine_pn"] = z(b["genuine_pn"])
b["bvp_pn"] = z(b["bvp_pn"])
print("genuine_bvp_crossref.csv: %d rows, %d genuine PNs, %d BVP numbers"
      % (len(b), b.genuine_pn.nunique(), b.bvp_pn.nunique()))

e25 = pd.read_excel(
    ROOT + r"\01_data\Eucon_Online28072025.xlsx",
    sheet_name="Fresh list_Export_28072025_0932",
    dtype=str,
)
e25["pn"] = z(e25["Searched Part Number"])
print("Eucon_Online28072025.xlsx: %d rows, %d searched PNs, %d brands, %d brand+pn pairs"
      % (len(e25), e25.pn.nunique(), e25.Brand.nunique(),
         (e25.Brand.fillna("") + "|" + e25["Part Number"].fillna("")).nunique()))

em = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="Online 15032024", dtype=str)
em["pn"] = z(em["Searched Part Number"])
print("Eucon_March.xlsx, 'Online 15032024': %d rows, %d searched PNs" % (len(em), em.pn.nunique()))

r = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="RRP MODE", dtype=str)
r["pn"] = z(r["Searched Part Number"])
print("Eucon_March.xlsx, 'RRP MODE': %d rows, %d searched PNs" % (len(r), r.pn.nunique()))

# --- coverage ----------------------------------------------------------------
sources = [
    ("eucon_crossref (44 PN, 2026-03)", set(x.isze_pn)),
    ("BVP genuine->BVP", set(b.genuine_pn)),
    ("Eucon Online (88 PN, 2025-07)", set(e25.pn)),
    ("Eucon March Online (42 PN, 2024-03)", set(em.pn)),
    ("Eucon March RRP MODE", set(r.pn)),
]
anyx = t.part_no.isin(set().union(*[s for _, s in sources]))

print("\n=== of the %d billed part numbers ===" % len(t))
print("any crossref today: %d (%.1f%%), EUR %s (%.1f%% of billed)"
      % (anyx.sum(), 100 * anyx.mean(), f"{t[anyx].billed_eur_t12m.sum():,.0f}",
         100 * t[anyx].billed_eur_t12m.sum() / tot))
for name, s in sources:
    m = t.part_no.isin(s)
    print("   %-36s %5d PNs  EUR %13s  %5.1f%% of billed"
          % (name, m.sum(), f"{t[m].billed_eur_t12m.sum():,.0f}", 100 * t[m].billed_eur_t12m.sum() / tot))

A = t[t.tier == "A"]
print("\n=== Tier A only: %d parts, EUR %s ===" % (len(A), f"{A.billed_eur_t12m.sum():,.0f}"))
for name, s in sources:
    m = A.part_no.isin(s)
    print("   %-36s %3d of %d (%5.1f%%)  EUR %13s  %5.1f%% of tier A"
          % (name, m.sum(), len(A), 100 * m.mean(), f"{A[m].billed_eur_t12m.sum():,.0f}",
             100 * A[m].billed_eur_t12m.sum() / A.billed_eur_t12m.sum()))
mA = A.part_no.isin(set().union(*[s for _, s in sources]))
print("   %-36s %3d of %d (%5.1f%%)  EUR %13s  %5.1f%% of tier A"
      % ("ANY", mA.sum(), len(A), 100 * mA.mean(), f"{A[mA].billed_eur_t12m.sum():,.0f}",
         100 * A[mA].billed_eur_t12m.sum() / A.billed_eur_t12m.sum()))

# --- overlap between the two Eucon generations -------------------------------
print("\n=== Eucon generations ===")
print("2026-03 crossref PN also in 2025-07 file : %d" % len(set(x.isze_pn) & set(e25.pn)))
print("2025-07 file PN also in 2024-03 file     : %d" % len(set(e25.pn) & set(em.pn)))
print("union of all three Eucon generations     : %d PNs" % len(set(x.isze_pn) | set(e25.pn) | set(em.pn)))

# --- per part: how many IAM numbers ------------------------------------------
g = x.groupby("isze_pn").competitor_pn.nunique()
print("\nIAM numbers per Isuzu PN in the 2026-03 crossref: median %.0f, min %d, max %d"
      % (g.median(), g.min(), g.max()))
gb = b.groupby("genuine_pn").bvp_pn.nunique()
print("BVP numbers per genuine PN: median %.0f, min %d, max %d" % (gb.median(), gb.min(), gb.max()))

# --- supersessions -----------------------------------------------------------
print("\n=== supersession columns present in the Eucon files? ===")
for label, df in [("Eucon_Online28072025", e25), ("Eucon_March Online", em), ("Eucon_March RRP MODE", r)]:
    cols = [c for c in df.columns if "supers" in c.lower()]
    print("   %-22s %s" % (label, cols if cols else "none"))
