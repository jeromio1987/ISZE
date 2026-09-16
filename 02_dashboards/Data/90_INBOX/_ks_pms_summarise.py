"""Summarise KS PMS scan vs Duncan Rev2 + Jerome FINAL. Prints overview with URLs."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ks_pms_scan_20260818")
products = json.loads((OUT / "products.json").read_text(encoding="utf-8"))
pn_hits = json.loads((OUT / "pn_search.json").read_text(encoding="utf-8"))

print("=== CATEGORY PRODUCTS", len(products), "===")
by_model = Counter(p["model"] for p in products)
print("by model", dict(by_model))
brands = Counter((p.get("brand") or ("GENUINE" if p["is_genuine"] else "UNNAMED/KS")).upper() for p in products)
print("brands", brands.most_common(30))
print("genuine", sum(1 for p in products if p["is_genuine"]), "iam", sum(1 for p in products if not p["is_genuine"]))

# PMS-ish names
keys = ("filter", "oil", "fuel", "air", "pad", "disc", "rotor", "clutch", "cabin", "pollen", "urea", "def")
pmsish = [p for p in products if any(k in p["name"].lower() for k in keys)]
print("pmsish", len(pmsish))
print("\n--- PMS-ish listings by family ---")
fam = defaultdict(list)
for p in pmsish:
    n = p["name"].upper()
    if "OIL" in n and "FILTER" in n:
        f = "oil_filter"
    elif "AIR" in n and "FILTER" in n:
        f = "air_filter"
    elif "FUEL" in n and "FILTER" in n:
        f = "fuel_filter"
    elif "CABIN" in n or "POLLEN" in n:
        f = "cabin_filter"
    elif "PAD" in n:
        f = "brake_pad"
    elif "DISC" in n or "ROTOR" in n:
        f = "brake_disc"
    elif "CLUTCH" in n:
        f = "clutch"
    elif "CALIPER" in n:
        f = "caliper"
    else:
        f = "other_pms"
    fam[f].append(p)

for f, rows in sorted(fam.items(), key=lambda x: -len(x[1])):
    print(f"\n## {f} n={len(rows)}")
    # unique by sku+name
    seen = set()
    for p in rows:
        key = (p.get("sku"), p["name"], p["model"])
        if key in seen:
            continue
        seen.add(key)
        g = "GEN" if p["is_genuine"] else "IAM"
        px = p["price_ex_gbp"]
        print(f"  {g:3} £{px}  {p.get('brand') or '-':12}  {p['name'][:55]:55}  SKU {p.get('sku')}  {p['model']}")
        print(f"      {p.get('product_url') or p.get('listing_url')}")

print("\n=== PN SEARCH ===")
for rec in pn_hits:
    n = rec.get("n_products") or 0
    flag = "HIT" if n else "MISS"
    print(f"{flag} {rec['pn']} n={n} {rec['search_url']}")
    for p in rec.get("products") or []:
        g = "GEN" if p["is_genuine"] else "IAM"
        print(f"    {g} £{p['price_ex_gbp']} {p.get('brand') or '-'} {p['name'][:70]}")
        print(f"       {p.get('product_url') or rec['search_url']}")
