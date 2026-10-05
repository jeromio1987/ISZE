"""Read-only probe 3: how much NEW matching material the two just-added Eucon files
carry, and what billed value it reaches. Nothing written, nothing fetched.
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

old = pd.read_csv(ROOT + r"\02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv", dtype=str)
old["isze_pn"] = z(old["isze_pn"])
old["key"] = old.isze_pn + "|" + old.Competitor_Brand.fillna("").str.strip().str.upper() + "|" + old.competitor_pn.fillna("").str.strip().str.upper()

e = pd.read_excel(ROOT + r"\01_data\Eucon_Online28072025.xlsx",
                  sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
e["key"] = e.pn + "|" + e.Brand.fillna("").str.strip().str.upper() + "|" + e["Part Number"].fillna("").str.strip().str.upper()

new_pairs = set(e.key) - set(old.key)
print("exact brand+number pairs, existing crossref : %d" % len(set(old.key)))
print("exact brand+number pairs, July 2025 file   : %d" % len(set(e.key)))
print("pairs in the July file NOT in the crossref : %d (%.0f%%)"
      % (len(new_pairs), 100 * len(new_pairs) / len(set(e.key))))

print("\nIsuzu part numbers:")
print("  in the existing crossref : %d" % old.isze_pn.nunique())
print("  in the July 2025 file    : %d" % e.pn.nunique())
print("  in July 2025, not in crossref : %d" % len(set(e.pn) - set(old.isze_pn)))
print("  union of the two         : %d" % len(set(e.pn) | set(old.isze_pn)))

covered = sorted(set(e.pn) | set(old.isze_pn))
in_tier = [p for p in covered if p in tier]
print("\nThose %d Isuzu numbers in the billed tier list: %d" % (len(covered), len(in_tier)))
for tr in ["A", "B", "C"]:
    s = [p for p in in_tier if tier[p] == tr]
    v = sum(billed.get(p, 0) for p in s)
    print("   tier %s: %4d PNs, EUR %13s" % (tr, len(s), f"{v:,.0f}"))

union_eur = sum(billed.get(p, 0) for p in in_tier)
print("   total EUR %s (%.1f%% of the %s billed book)"
      % (f"{union_eur:,.0f}", 100 * union_eur / tot, f"{tot:,.0f}"))

# what the July file adds on its own
add = sorted(set(e.pn) - set(old.isze_pn))
add_in = [p for p in add if p in tier]
add_eur = sum(billed.get(p, 0) for p in add_in)
print("\nBy itself the July 2025 file adds %d Isuzu numbers, %d of them billed, EUR %s"
      % (len(add), len(add_in), f"{add_eur:,.0f}"))
for tr in ["A", "B", "C"]:
    s = [p for p in add_in if tier[p] == tr]
    print("   tier %s: %3d" % (tr, len(s)))

# price availability in the new file
print("\nPrice availability inside the July 2025 file:")
print("   rows with a competitor price          : %d of %d (%.0f%%)"
      % (e.RRP.notna().sum(), len(e), 100 * e.RRP.notna().mean()))
print("   rows with only our own Isuzu price    : %d" % e["OE RRP"].notna().sum())
print("   distinct Isuzu numbers WITH a competitor price : %d" % e[e.RRP.notna()].pn.nunique())
print("   distinct Isuzu numbers with crossref but no price : %d"
      % len(set(e.pn) - set(e[e.RRP.notna()].pn)))

print("\nThe 'Additional Part Numbers' column as an extra matching source:")
extra = e[e["Additional Part Numbers"].notna()].copy()
print("   rows carrying it : %d" % len(extra))
alt = set()
for _, row in extra.iterrows():
    for n in str(row["Additional Part Numbers"]).split(","):
        n = n.strip().upper()
        if n:
            alt.add(n)
print("   distinct alternative numbers listed : %d" % len(alt))

# --- the true union, all four sources, against billed value -------------------
b = pd.read_csv(ROOT + r"\01_data\00_derived\genuine_bvp_crossref.csv", dtype=str)
r = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="RRP MODE", dtype=str)
r["pn"] = z(r["Searched Part Number"])
crossref_like = set(old.isze_pn) | set(z(b["genuine_pn"])) | set(e.pn)
price_like = set(r.pn) | set(z(pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx",
                                              sheet_name="Online 15032024", dtype=str)["Searched Part Number"]))
everything = crossref_like | price_like
print("\n=== union, all four Eucon/BVP sources ===")
for label, s in [("any competitor-equivalent number", crossref_like),
                 ("any own-number price observation", price_like),
                 ("either", everything)]:
    m = t.part_no.isin(s)
    print("   %-36s %5d PNs (%.1f%% of parts), EUR %13s (%.1f%% of billed)"
          % (label, m.sum(), 100 * m.mean(), f"{t[m].billed_eur_t12m.sum():,.0f}",
             100 * t[m].billed_eur_t12m.sum() / tot))
    for tr in ["A", "B", "C"]:
        tt = t[t.tier == tr]
        mm = tt.part_no.isin(s)
        print("        tier %s: %4d of %4d (%.1f%%), EUR %s"
              % (tr, mm.sum(), len(tt), 100 * mm.mean(), f"{tt[mm].billed_eur_t12m.sum():,.0f}"))

print("\n=== country coverage of the two Eucon generations ===")
print("   July 2025 file :", e.Country.value_counts().to_dict())
print("   March 2024 file:", r.Country.value_counts().to_dict())
print("   existing crossref:", old.Country.value_counts().to_dict(), "(countries with a crossref row)")

# supersession
r = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="RRP MODE", dtype=str)
r["pn"] = z(r["Searched Part Number"])
sup = r[r["Supersession Info ID"].fillna("0") != "0"]
print("\nSupersession rows in RRP MODE: %d. Distinct IDs: %s"
      % (len(sup), sorted(sup["Supersession Info ID"].fillna('').unique())))
print("   (the sheet carries an ID, not the successor part number)")
print("   distinct Isuzu numbers involved: %d" % sup.pn.nunique())
