import json
from pathlib import Path

d = json.loads(Path(__file__).with_name("pn_search.json").read_text(encoding="utf-8"))
want = {
    "8971482700", "8980370110", "8970622940", "8971686340",
    "8975439050", "8983752250", "8976739570", "1313100120", "5876101040",
}
for rec in d:
    if rec["pn"] not in want:
        continue
    print("PN", rec["pn"], "n", len(rec["items"]))
    for i in rec["items"]:
        print(" ", i.get("price_ex_gbp"), "G" if i.get("is_genuine") else "A", i.get("name"))
        print("   ", i.get("url"))
