"""Read the shipped page's own embedded payload, so "before" is the page's numbers not a guess."""
from __future__ import annotations

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

H = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_PMS_Family_Evolution.html"
h = open(H, encoding="utf-8").read()
m = re.search(r'<script id="pmfe-data" type="application/json">(.*?)</script>', h, re.S)
if not m:
    print("NO PAYLOAD FOUND")
    raise SystemExit(1)
D = json.loads(m.group(1))
t = D["trend"]["CY"]["service_parts_only"]
print("SHIPPED PAGE, CY, service parts only, network, the 18 markets on the page")
print("=" * 84)
print(f"{'family':42s} {'2023':>11s} {'2024':>11s} {'2025':>11s} {'2026(6m)':>11s}")
for f, v in t["family"].items():
    row = " ".join(f"{v['eur'][k]:>11,.0f}" for k in sorted(v["eur"]))
    print(f"{f:42s} {row}")
print()
print("units")
for f, v in t["family"].items():
    row = " ".join(f"{v['units'][k]:>11,.0f}" for k in sorted(v["units"]))
    print(f"{f:42s} {row}")
print()
print("net:", json.dumps(D["net"]))
fr = D["meta"]["familyResolution"]
print("family resolution as published:", json.dumps({k: fr[k] for k in fr if k != "by_source"}))
print("  by_source:", json.dumps(fr.get("by_source")))
print("tie1:", json.dumps(D["meta"]["tie1"]))
print("tie2:", json.dumps(D["meta"]["tie2"]))
