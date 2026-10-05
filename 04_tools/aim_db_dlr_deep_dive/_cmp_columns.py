"""Establish the fact-row column semantics before trusting any recomputation."""
import json, re

P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Comparison_PORTUGAL.html"
t = open(P, encoding="utf-8").read()
d = json.loads(re.search(r'id="data">(.*?)</script>', t, re.S).group(1))
PN = d["pn"]; price = PN["p"]

print("is col4 == col3 * price[pn] ?")
match = tot = 0
for r in d["facts"]:
    sp = price[r[2]]
    if sp is None:
        continue
    tot += 1
    if abs(r[3] * sp - r[4]) < 0.02:
        match += 1
print(f"  {match:,} of {tot:,} rows match  ({100*match/max(tot,1):.1f}%)")

print("\ncol5 all zero?", all(r[5] == 0 for r in d["facts"]))
print("col5 nonzero rows:", [(i, r) for i, r in enumerate(d["facts"]) if r[5] != 0][:5])

# not everything has a price; what does col4 look like when the price is missing?
nop = [r for r in d["facts"] if price[r[2]] is None]
print(f"\nrows whose part number has NO list price: {len(nop):,}")
print("  first few:", nop[:5])

# is col4 the GM figure or the plain list figure? compare one row against both
r = [x for x in d["facts"] if price[x[2]] is not None][0]
sp = price[r[2]]
print(f"\nsample row {r}")
print(f"  pn {PN['n'][r[2]]}  desc {PN['descs'][PN['d'][r[2]]] if 'descs' in PN else ''}")
print(f"  units {r[3]}  list price {sp}")
print(f"  units*list      = {r[3]*sp:>10.2f}")
print(f"  units*list/0.65 = {r[3]*sp/0.65:>10.2f}")
print(f"  col4            = {r[4]:>10.2f}")

# and the price unit: does price column hold a real list price?
print(f"\nprice values, first 10: {price[:10]}")
print(f"price min/max: {min(p for p in price if p is not None)} / {max(p for p in price if p is not None)}")
