"""Read-only probe: which competitor numbers are most likely to be a real, saleable Isuzu
replacement? Two things to settle first:

  1. competitor numbers are written with and without spaces/dots ('F 026 402 115' vs
     'F026402115'), so 'confirmed by 3 sources' is partly a formatting artefact. Normalise and
     re-count.
  2. rank by independent confirmation, not by our billed value, because our billed value says
     nothing about whether a rival part is on a shelf.

Nothing written, nothing fetched.
"""
import re
import pandas as pd

pd.set_option("display.width", 320)
ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
S = ROOT + r"\04_tools\aftermarket_intelligence\state"

mi = pd.read_csv(S + r"\match_index.csv", dtype=str)
t = pd.read_csv(ROOT + r"\04_tools\delegation\state\refresh_tiers_LOCAL.csv", dtype={"part_no": str})
t["part_no"] = t.part_no.astype(str).str.strip()
t["billed_eur_t12m"] = pd.to_numeric(t.billed_eur_t12m, errors="coerce")
tier = dict(zip(t.part_no, t.tier))
billed = dict(zip(t.part_no, t.billed_eur_t12m))

# --- rival rows only: drop our own BVP line, our own numbers, and the peer-carrier map
r = mi[~mi.source.str.startswith(("Isuzu genuine", "Peer carrier"))].copy()
r = r[~r.competitor_brand_norm.fillna("").str.startswith(("Isuzu BVP", "Isuzu (our"))]
r = r[~r.competitor_brand_norm.fillna("").isin(["DAF", "TOYOTA", "FORD"])]
print("rival match rows: %d, distinct numbers as written: %d" % (len(r), r.competitor_pn.nunique()))


def compact(x):
    """Same number written two ways should be one number."""
    return re.sub(r"[\s\.\-/]", "", str(x)).upper()


r["cpn_compact"] = r.competitor_pn.map(compact)
print("distinct numbers after removing spaces/dots/dashes: %d  (%.0f%% of the written forms)"
      % (r.cpn_compact.nunique(), 100 * r.cpn_compact.nunique() / r.competitor_pn.nunique()))

# how many written forms collapse?
forms = r.groupby("cpn_compact").competitor_pn.nunique()
print("numbers written in more than one way: %d" % (forms > 1).sum())
if (forms > 1).any():
    ex = forms[forms > 1].index[:5]
    for c in ex:
        print("   %s -> %s" % (c, sorted(r[r.cpn_compact == c].competitor_pn.unique())))

# --- independent confirmation
g = r.groupby("cpn_compact").agg(
    forms=("competitor_pn", "nunique"),
    n_sources=("source", "nunique"),
    n_brands=("competitor_brand_norm", "nunique"),
    n_isuzu_pns=("part_no", "nunique"),
    has_price=("has_competitor_price", lambda s: (s.astype(int) == 1).any()),
    n_price_rows=("has_competitor_price", lambda s: int(s.astype(int).sum())),
).reset_index()

pn_val = r.groupby("cpn_compact").part_no.apply(lambda s: sum(billed.get(p, 0) or 0 for p in set(s)))
g["billed_of_isuzu_parts"] = g.cpn_compact.map(pn_val).fillna(0)
g["top_isuzu_part"] = g.cpn_compact.map(
    r.groupby("cpn_compact").part_no.apply(lambda s: sorted(set(s), key=lambda p: -billed.get(p, 0))[0]))

print()
print("confirmation, before and after normalising the number:")
print("   %-18s %8s %8s" % ("", "written", "normalised"))
for lab, col in [("1 source", "n_sources"), ("2 sources", None), ("3+ sources", None)]:
    pass
gw = r.groupby("competitor_pn").source.nunique()
for lab, fn in [("1 source", lambda s: s == 1), ("2 sources", lambda s: s == 2), ("3+ sources", lambda s: s >= 3)]:
    print("   %-18s %8d %8d" % (lab, int(fn(gw).sum()), int(fn(g.n_sources).sum())))

print()
print("competitor numbers that are only a spacing variant of another: %d" % ((forms > 1).sum()))

# --- the shortlist
short = g[g.n_sources >= 3].sort_values(["n_sources", "n_isuzu_pns"], ascending=False)
print("\n=== numbers several independent vendors agree on (3+ sources after normalising) ===")
print("count: %d" % len(short))
print(short.head(25)[["cpn_compact", "n_sources", "n_brands", "n_isuzu_pns",
                      "billed_of_isuzu_parts", "top_isuzu_part"]].to_string(index=False))

print("\n=== what a scrape of ONLY the shortlist would cover ===")
pns = r[r.cpn_compact.isin(set(short.cpn_compact))].part_no.unique()
val = sum(billed.get(p, 0) or 0 for p in set(pns))
ta = [p for p in pns if tier.get(p) == "A"]
val_a = sum(billed.get(p, 0) or 0 for p in ta)
print("   competitor numbers to fetch : %d" % short.cpn_compact.nunique())
print("   Isuzu parts reached         : %d of %d" % (len(pns), len(t)))
print("   billed value                : EUR {:,.0f}".format(val))
print("   Tier A                      : {} parts, EUR {:,.0f}".format(len(ta), val_a))

for lo, hi, lbl in [(0, 1, "never billed"), (1, 50000, "under 50k"), (50000, 200000, "50k-200k"),
                    (200000, 1e12, "over 200k")]:
    m = (g[g.n_sources >= 3].billed_of_isuzu_parts >= lo) & (g[g.n_sources >= 3].billed_of_isuzu_parts < hi)
    print("   shortlist touching parts %-12s: %4d numbers" % (lbl, int(m.sum())))

print("\n=== the same shortlist, but counting sources BEFORE normalising (the inflated view) ===")
short_w = gw[gw >= 3]
print("   inflated count: %d  -> real count: %d  (difference %d, all spacing variants)"
      % (len(short_w), len(short), len(short_w) - len(short)))
