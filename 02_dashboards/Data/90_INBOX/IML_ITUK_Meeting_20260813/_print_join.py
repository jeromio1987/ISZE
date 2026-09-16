import json
from pathlib import Path

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IML_ITUK_Meeting_20260813\_pms_join.json")
d = json.loads(p.read_text(encoding="utf-8"))
print("=== CAT SPLIT WS2025 ===")
for cat, buckets in d["cat_split_ws2025"].items():
    print(cat)
    for b, v in buckets.items():
        print(f"  {b}: ws={v['ws']:.0f} n={len(v['pns'])}")
print()
print("=== KEY JOINS ===")
keys = [
    "8982705240",
    "1876102890",
    "8983282070",
    "8983282071",
    "5876101170",
    "8975439050",
    "8980188580",
    "8975425400",
    "8981596930",
    "8981941190",
    "1876100934",
    "1876102860",
    "8975425390",
    "8980374810",
    "5876101570",
    "8981772710",
    "8976739570",
    "5876102500",
    "8983214130",
    "5876102900",
    "8982447940",
    "8982169210",
    "8982169220",
    "5876102380",
    "8981649171",
    "8982551391",
    "8970388314",
]
idx = {r["pn"]: r for r in d["joined"]}
for pn in keys:
    r = idx.get(pn)
    if not r:
        print(pn, "NOT IN DUNCAN")
        continue
    isze = r["isze"]
    pk = r["peek"]
    q25 = (isze.get("2025") or {}).get("qty")
    q26 = (isze.get("2026") or {}).get("qty")
    print(
        f"{pn} {str(r['category'])[:20]:20} sl={r['n_model_slides']} ytd={r['duncan_ytd']} mo={r['duncan_monthly']} "
        f"ws={pk.get('ws2025')} isze25={q25} isze26={q26} model={pk.get('model_ituk')} cover={pk.get('cover')}"
    )
print()
print("=== MISSING AUDIT ===")
for x in d["missing_from_duncan_audit2025_qty_ge_200"]:
    print(x)
print()
print("=== DUP PNS ===")
prev = json.loads(
    Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IML_ITUK_Meeting_20260813\_pms_anomaly_check.json").read_text(
        encoding="utf-8"
    )
)
seen = {}
for r in prev["duplicates"]:
    seen.setdefault(r["pn"], []).append(r["model_sheet"])
for pn, models in seen.items():
    print(pn, models)
