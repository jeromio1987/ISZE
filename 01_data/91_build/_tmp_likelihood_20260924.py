"""Read-only probe: which competitor numbers are most likely to actually be sold as an Isuzu
replacement? Ranks the match index by evidence of being a real, widely-listed part.

Nothing written, nothing fetched.
"""
import pandas as pd

pd.set_option("display.width", 300)
ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
S = ROOT + r"\04_tools\aftermarket_intelligence\state"
mi = pd.read_csv(S + r"\match_index.csv", dtype=str)
t = pd.read_csv(ROOT + r"\04_tools\delegation\state\refresh_tiers_LOCAL.csv", dtype={"part_no": str})
t["part_no"] = t["part_no"].astype(str).str.strip()
t["billed_eur_t12m"] = pd.to_numeric(t["billed_eur_t12m"], errors="coerce")
tier = dict(zip(t.part_no, t.tier))
billed = dict(zip(t.part_no, t.billed_eur_t12m))

master = pd.read_csv(ROOT + r"\01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv", dtype=str)
master["part_no"] = master.part_number.astype(str).str.strip()
l1 = dict(zip(master.part_no, master.aim_level_1))
l2 = dict(zip(master.part_no, master.aim_level_2))

# rival only: exclude our own BVP line, our own numbers, and the peer-carrier map
rival = mi[~mi.competitor_brand_norm.fillna("").str.startswith(("Isuzu BVP", "Isuzu (our", "DAF", "Toyota", "Ford"))
           & ~mi.source.str.startswith(("Isuzu genuine", "Peer carrier"))].copy()
rival = rival[~rival.competitor_brand_norm.isin(["DAF", "TOYOTA", "FORD"])]
print("rival match rows: %d" % len(rival))

g = rival.groupby("competitor_pn").agg(
    n_sources=("source", "nunique"),
    n_brands=("competitor_brand_norm", "nunique"),
    n_isuzu_pns=("part_no", "nunique"),
    has_price=("has_competitor_price", lambda s: (s.astype(int) == 1).any()),
).reset_index()

# billed reach of each competitor number
pn_val = rival.groupby("competitor_pn").part_no.apply(lambda s: sum(billed.get(p, 0) or 0 for p in set(s)))
g["billed_eur_of_isuzu_parts"] = g.competitor_pn.map(pn_val).fillna(0)

# is the Isuzu part it replaces a wear / maintenance family?
def fam_score(pns):
    keys = [str(l1.get(p, "")) + " / " + str(l2.get(p, "")) for p in pns]
    wear = sum(1 for k in keys if any(w in k.lower() for w in
               ["filter", "brake", "disc", "pad", "clutch", "belt", "lubric", "maintenance", "fluids"]))
    return wear / max(1, len(keys))

g["wear_share"] = g.competitor_pn.map(
    rival.groupby("competitor_pn").part_no.apply(lambda s: fam_score(set(s)))).fillna(0)

# likelihood: agreement across independent sources is the strongest single signal
g["likelihood"] = (g.n_sources * 2 + g.n_brands.clip(0, 3) + g.wear_share * 2
                   + (g.billed_eur_of_isuzu_parts > 100000).astype(int)).round(2)

print("\ncompetitor numbers in the index: %d" % len(g))
print("listed by 1 source  : %d" % (g.n_sources == 1).sum())
print("listed by 2 sources : %d" % (g.n_sources == 2).sum())
print("listed by 3+ sources: %d" % (g.n_sources == 3).sum())
print("carry a price today : %d" % g.has_price.sum())
print()
print("billed value of the Isuzu parts they touch:")
for lo, hi, lbl in [(0, 1e9, "all"), (100000, 1e9, "parts billed > EUR 100k"), (0, 1, "parts never billed")]:
    m = (g.billed_eur_of_isuzu_parts.between(lo, hi, inclusive="left"))
    print("   %-24s %5d numbers" % (lbl, m.sum()))

print("\n=== the shortlist: 3+ independent sources, i.e. several vendors agree this fits ===")
short = g[g.n_sources >= 3].sort_values(["n_isuzu_pns", "billed_eur_of_isuzu_parts"], ascending=False)
print("count: %d competitor numbers" % len(short))
print(short.head(20).round(2).to_string(index=False))

print("\n=== reach of the shortlist in money ===")
pn_short = rival[rival.competitor_pn.isin(set(short.competitor_pn))].part_no.unique()
print("   Isuzu parts touched : %d of %d" % (len(pn_short), len(t)))
print("   billed value        : EUR %,.0f" .replace(",", "") % 0 if False else
      "   billed value        : EUR {:,.0f}".format(sum(billed.get(p, 0) or 0 for p in set(pn_short))))
ta = [p for p in pn_short if tier.get(p) == "A"]
print("   of which Tier A     : %d parts, EUR {:,.0f}".format(len(ta), sum(billed.get(p, 0) or 0 for p in ta)))

print("\n=== how many Isuzu parts would a scrape of ONLY the shortlist cover? ===")
print("   distinct competitor numbers to fetch: %d" % short.competitor_pn.nunique())
print("   the whole index holds              : %d" % g.competitor_pn.nunique())
