"""How far down the billed-price list must we work to cover the comparable unique parts?

"Comparable unique parts" = part numbers that sit on exactly one vehicle family/band, so they can
carry a like-for-like comparison. Shared parts cannot, so they are excluded from the target.

Answers: at each depth of the euro-ranked list, how many part numbers, what share of total euro,
and what share of the comparable (single-band) euro is covered — and what that costs in EPC time.
"""

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

# ---- every PMS part number, ranked by billed euro
sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["pn"] = sf["part_number"].map(norm)

cat = pd.read_csv(DER + r"\bvp_pn_dimension.csv", dtype=str, low_memory=False)
cat["pn"] = cat.part_number.map(norm)
cat = cat[cat.pms_category.notna()].drop_duplicates("pn")[["pn", "pms_category"]]
pms_pns = set(cat.pn)

book = (sf[sf.pn.isin(pms_pns)]
        .groupby("pn")
        .agg(eur=("net_sales_value", "sum"), units=("billed_qty", "sum"))
        .reset_index()
        .sort_values("eur", ascending=False)
        .reset_index(drop=True))
book["rank"] = book.index + 1
TOTAL = book.eur.sum()

# ---- which are already comparable (single family/band) and which are not
cap = pd.read_csv(DER + r"\tonnage_capable_part_numbers.csv")
cap["pn"] = cap.pn.map(norm)
single = set(cap.loc[cap.n_bands == 1, "pn"])
shared = set(cap.loc[cap.n_bands > 1, "pn"])

book["status"] = "not yet decoded"
book.loc[book.pn.isin(single), "status"] = "comparable (single band)"
book.loc[book.pn.isin(shared), "status"] = "shared across bands"

print("=" * 100)
print("THE PMS UNIVERSE, BY STATUS")
print("=" * 100)
g = book.groupby("status").agg(pns=("pn", "count"), eur=("eur", "sum"))
g["eur_pct"] = (100 * g.eur / TOTAL).round(1)
print(g.round(0).to_string())
print(f"\n  total PMS part numbers {len(book):,}  EUR {TOTAL:,.0f}")

# ---- cumulative coverage as you descend the ranked list
print()
print("=" * 100)
print("HOW FAR DOWN THE PRICE LIST, AND WHAT IT COSTS")
print("=" * 100)
print(f"{'depth':>7s} {'PNs decoded':>12s} {'% of total EUR':>15s} "
      f"{'comparable PNs found':>21s} {'% of comparable EUR':>20s} {'EPC hours':>10s}")
print("-" * 100)
comp_total = book.loc[book.pn.isin(single), "eur"].sum()
for depth in (250, 500, 1000, 2000, 3000, 5000, 8000, 12000, len(book)):
    sub = book.head(depth)
    eur_pct = 100 * sub.eur.sum() / TOTAL
    found = sub[sub.pn.isin(single)]
    comp_pct = 100 * found.eur.sum() / comp_total if comp_total else 0
    print(f"{depth:7d} {len(sub):12,} {eur_pct:14.1f}% {len(found):20,} "
          f"{comp_pct:19.1f}% {depth*12/3600:9.1f}h")

print()
print("=" * 100)
print("THE ANSWER: how deep to reach 50% / 80% / 95% of the COMPARABLE euro")
print("=" * 100)
run = book[book.pn.isin(single)].copy()
run["cum"] = run.eur.cumsum()
run["cum_pct"] = 100 * run.cum / comp_total
for target in (50, 80, 95):
    hit = run[run.cum_pct >= target]
    if hit.empty:
        print(f"  {target}% : not reachable in the comparable set")
        continue
    n = int(hit.iloc[0]["rank"])
    pns_needed = int((book["rank"] <= n).sum())
    print(f"  {target:2d}% of comparable euro : need the top {pns_needed:,} part numbers "
          f"({pns_needed*12/3600:.1f} h at 12 s each, {pns_needed*12/3600/24:.1f} days)")

print()
print("=" * 100)
print("AND AT THE BULK RATE (if the catalogue pass works: ~12 requests per edition)")
print("=" * 100)
print("  the depth in part numbers stops mattering — a catalogue pass returns every part")
print("  for a model, so the whole N-series (556 editions) is the unit of work, not a count")
print("  of part numbers. That is the difference between 'how deep' and 'which models'.")
