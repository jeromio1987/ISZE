"""Reconstruct the level-1 movement for Portugal from the comparison page's own payload."""
import json, re

P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_AIM_Comparison_PORTUGAL.html"
t = open(P, encoding="utf-8").read()
d = json.loads(re.search(r'id="data">(.*?)</script>', t, re.S).group(1))

print("pairs:", json.dumps(d["pairs"])[:600])
print("\nmin_side_months:", d.get("min_side_months"), " gm_divisor:", d.get("gm_divisor"))
print("months:", d["months"])
print("\nviews:", json.dumps(d["views"])[:400] if "views" in d else "-")
print("\nfact row sample:", d["facts"][:3])
print("pn keys:", sorted(d["pn"].keys()) if isinstance(d["pn"], dict) else type(d["pn"]))
print("aim keys:", sorted(d["aim"].keys()))
print("L1 labels:", d["aim"]["l1"])
