import json
from pathlib import Path

p = Path(__file__).with_name("products.json")
d = json.loads(p.read_text(encoding="utf-8"))
for k, v in d["trees"].items():
    print("===", k, "n=", v.get("n_items"), v.get("status"))
    for i in v.get("items") or []:
        px = i.get("price_ex_gbp")
        if px is None:
            continue
        flag = "G" if i.get("is_genuine") else "A"
        name = (i.get("name") or "")[:72]
        sku = i.get("sku") or ""
        print(f"  {flag} {px:7.2f}  {sku:14} {name}")
        print("     ", (i.get("url") or "")[:120])
