"""Verify the comparison page's headline claims from its own embedded payload."""
import json, re, io, os

P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Comparison_PORTUGAL.html"
t = open(P, encoding="utf-8").read()
print("html MB:", round(os.path.getsize(P) / 1024 / 1024, 2))

m = re.search(r'<script type="application/json" id="data">(.*?)</script>', t, re.S)
print("embedded json found:", bool(m))
d = json.loads(m.group(1))
print("top-level keys:", sorted(d.keys()))
print()
for k in ("periods", "period_a", "period_b", "pair", "periods_available", "rule"):
    if k in d:
        print(f"{k}: {json.dumps(d[k])[:400]}")
print()
# look for anything period-like
for k, v in d.items():
    if "period" in k.lower():
        s = json.dumps(v)
        print(f"  {k}: {s[:300]}")
print()
print("NaN in payload:", "NaN" in m.group(1))

# check the verification report numbers
V = r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\aim_db_dlr_deep_dive\VERIFY_COMPARISON_PORTUGAL.json"
if os.path.exists(V):
    v = json.load(open(V, encoding="utf-8"))
    print(f"\nverify: passed {v.get('passed')} failed {v.get('failed')}")
    for c in v.get("checks", []):
        nm = c.get("name", "")
        if any(x in nm.lower() for x in ("run", "split", "period", "reconcil", "sum back", "growth")):
            print(f"  [{'PASS' if c.get('pass') else 'FAIL'}] {nm}")
            print(f"        expected {c.get('expected')}  actual {c.get('actual')}")
