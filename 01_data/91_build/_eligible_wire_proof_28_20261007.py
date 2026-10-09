import json
from pathlib import Path
from collections import Counter

aim = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29c_ids_ituk_pt\Isuzu Universe\05_AIM_Universe")
payload = json.loads((aim/"payload/aim_payload_u29c_real_feeds.local.json").read_text(encoding="utf-8"))
offers = payload.get("offers") or {}
cases = payload.get("cases") or []

elig_hooks = [c for c in cases if str(c.get("id") or "").endswith("-ELIG")]
shop_ids = []
eucon_ids = []
by_case = {}
sellers = Counter()
for c in elig_hooks:
    cid = c["id"]
    oids = list(c.get("offers") or [])
    shop = []
    eu = []
    for oid in oids:
        o = offers.get(oid) or {}
        seller = o.get("seller") or ""
        sellers[seller] += 1
        if seller == "Eucon survey" or str(oid).startswith("EUCON-"):
            eu.append(oid)
        else:
            shop.append(oid)
    by_case[cid] = {"pn": c.get("pn"), "shop": len(shop), "eucon": len(eu)}
    shop_ids.extend(shop)
    eucon_ids.extend(eu)

omega = [i for i in shop_ids if i.startswith("OMEGA-")]
ks = [i for i in shop_ids if i.startswith("KS-")]
print("ELIG cases", len(elig_hooks))
print("shop unique", len(set(shop_ids)), "refs", len(shop_ids))
print("eucon unique", len(set(eucon_ids)))
print("OMEGA", len(omega), "KS", len(ks))
print("sellers", dict(sellers))
print("AXL", by_case.get("ITUK-AXL-ELIG"))
print("AIR062", by_case.get("ITUK-AIR-062-ELIG"))
out = {
    "eligible_shop_offers": len(set(shop_ids)),
    "eligible_cases": len(elig_hooks),
    "by_case": by_case,
    "omega_offers": len(omega),
    "ks_offers": len(ks),
    "eucon_offers": len(set(eucon_ids)),
    "new_case_ids": ["ITUK-AXL-ELIG"],
}
(aim/"dist/_eligible_wire_proof_20261007.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("wrote proof")
