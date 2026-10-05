"""Recompute Portugal's level-1 movement from the page's own payload and compare with the report."""
import json, re

P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Comparison_PORTUGAL.html"
t = open(P, encoding="utf-8").read()
d = json.loads(re.search(r'id="data">(.*?)</script>', t, re.S).group(1))

months = d["months"]
mi = {m: i for i, m in enumerate(months)}
pair = d["pairs"]["PORTUGAL"][0]
A = {mi[m] for m in pair["months_a"]}
B = {mi[m] for m in pair["months_b"]}

PN = d["pn"]
l1 = PN["l1"]
price = PN["p"]
print(f"payload part numbers: {len(l1):,}")
print(f"price present: {sum(1 for p in price if p is not None):,}")
print(f"fact rows: {len(d['facts']):,}")
print(f"row shape: [db, month, pn, units, eur_actual?, ?] -> {d['facts'][0]}")
print()

# work out the fact columns by inspecting a row with real values
import collections
sample = d["facts"][:2000]
print("col ranges in first 2000 rows:")
for c in range(6):
    vals = [r[c] for r in sample]
    print(f"  col{c}: min {min(vals)} max {max(vals)}  distinct {len(set(vals))}")

ua = collections.defaultdict(float)
ub = collections.defaultdict(float)
for r in d["facts"]:
    m = r[1]
    p = r[2]
    u = r[3]
    sp = price[p]
    if sp is None:
        continue
    e = u * sp
    if m in A:
        ua[l1[p]] += e
    elif m in B:
        ub[l1[p]] += e

L1 = d["aim"]["l1"]
rows = [(L1[k], ub[k] - ua[k], ua[k], ub[k]) for k in set(list(ua.keys()) + list(ub.keys()))]
pos = sorted([r for r in rows if r[1] > 0], key=lambda x: -x[1])
neg = sorted([r for r in rows if r[1] < 0], key=lambda x: x[1])
print(f"\ntotal movement: EUR {sum(r[1] for r in rows):,.0f}")
print(f"growth: EUR {sum(r[1] for r in pos):,.0f}   decline: EUR {sum(r[1] for r in neg):,.0f}")
print("\nbiggest improvements at level 1 (EUR at price list):")
for n, dv, a, b in pos[:6]:
    print(f"  {n:<26} {dv:>+12,.0f}   A {a:>12,.0f}  B {b:>12,.0f}")
print("\nbiggest declines at level 1:")
for n, dv, a, b in neg[:6]:
    print(f"  {n:<26} {dv:>+12,.0f}   A {a:>12,.0f}  B {b:>12,.0f}")
