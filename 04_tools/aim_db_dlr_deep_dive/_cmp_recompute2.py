"""Recompute Portugal level-1 movement on the CORRECT basis: sales-to-dealer units x list price.

Fact row is [db, month, pn, billed_units, billed_eur_actual, sold_units] - the same shape the
deep-dive page uses. Sales-to-dealer euro = col5 * list price.
"""
import json, re, collections

P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Comparison_PORTUGAL.html"
t = open(P, encoding="utf-8").read()
d = json.loads(re.search(r'id="data">(.*?)</script>', t, re.S).group(1))
PN = d["pn"]; price = PN["p"]; l1 = PN["l1"]; L1 = d["aim"]["l1"]
months = d["months"]; mi = {m: i for i, m in enumerate(months)}
pair = d["pairs"]["PORTUGAL"][0]
A = {mi[m] for m in pair["months_a"]}
B = {mi[m] for m in pair["months_b"]}
print(f"period A {pair['a_from']}..{pair['a_to']}   period B {pair['b_from']}..{pair['b_to']}")

ua = collections.defaultdict(float)
ub = collections.defaultdict(float)
na = nb = 0
for r in d["facts"]:
    m, p, sold = r[1], r[2], r[5]
    sp = price[p]
    if sp is None:
        continue
    e = sold * sp
    if m in A:
        ua[l1[p]] += e; na += sold
    elif m in B:
        ub[l1[p]] += e; nb += sold

rows = [(L1[k], ub[k] - ua[k]) for k in set(list(ua) + list(ub))]
pos = sorted([r for r in rows if r[1] > 0], key=lambda x: -x[1])
neg = sorted([r for r in rows if r[1] < 0], key=lambda x: x[1])
print(f"\nsold units: A {na:,.0f}   B {nb:,.0f}")
print(f"net movement EUR {sum(r[1] for r in rows):,.0f}  "
      f"growth EUR {sum(r[1] for r in pos):,.0f}  decline EUR {sum(r[1] for r in neg):,.0f}")
print(f"families up {len(pos)}  down {len(neg)}")

print("\nbiggest improvements at level 1, sales to dealer at list price:")
for n, dv in pos[:6]:
    print(f"  {n:<26} {dv:>+12,.0f}   A {ua[L1.index(n)]:>10,.0f}  B {ub[L1.index(n)]:>10,.0f}")
print("\nbiggest declines:")
for n, dv in neg[:6]:
    print(f"  {n:<26} {dv:>+12,.0f}   A {ua[L1.index(n)]:>10,.0f}  B {ub[L1.index(n)]:>10,.0f}")
