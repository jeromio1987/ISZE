import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rows = list(
    csv.DictReader(
        Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_spu_by_distributor.csv").open(
            encoding="utf-8-sig"
        )
    )
)
print("=== SPU vs max wallet per UIO (2026) ===")
for r in sorted(
    [x for x in rows if x["year"] == "2026" and x.get("spend_per_unit_eur")],
    key=lambda x: x["country"],
):
    uio = float(r["uio_units"] or 0)
    mx = float(r["max_spend_eur"] or 0)
    spu = float(r["spend_per_unit_eur"])
    max_pu = (mx / uio) if uio else None
    print(
        f"{r['country']:20s} actual_spu={spu:7.1f}  max_per_uio={max_pu:7.1f}  "
        f"uio={uio:.0f} capture={r.get('gps_capture_vs_max')}"
    )

d = json.loads(
    Path(
        r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\isze_dashboard_v4_data.json"
    ).read_text(encoding="utf-8")
)
opps = d["opportunities"]
notices = d["notices"]

random.seed(7)
sample = random.sample(opps, 40)
print("\n=== 40-opportunity relevance sample ===")
for o in sample:
    title = (o.get("title") or o.get("title_raw") or "")[:95]
    print(
        f"{o.get('decision', '?'):10s} rm={str(o.get('rm_contract')):5s} "
        f"{(o.get('country') or '?'):16s} | {title}"
    )

cpvs = Counter()
for n in notices:
    c = str(n.get("CPV Code") or "")[:8]
    cpvs[c] += 1
print("\n--- top CPV ---")
for c, n in cpvs.most_common(15):
    print(n, c)

keys = [
    "electric",
    "bus",
    "coach",
    "ambulance",
    "refuse",
    "fire",
    "passenger",
    "carsharing",
    "sedan",
    "estate",
    "van",
    "pickup",
    "pick-up",
    "d-max",
    "isuzu",
    "truck",
    "4x4",
    "chassis",
]
print("\n--- title keyword hits among opportunities ---")
for k in keys:
    n = sum(
        1
        for o in opps
        if k in (o.get("title") or "").lower() or k in (o.get("title_raw") or "").lower()
    )
    print(f"  {k!r}: {n}")

# Est value totals
vals = [o.get("value_amount") for o in opps if o.get("value_amount")]
print(f"\nopps with contract value: {len(vals)} / {len(opps)}")
print(f"sum contract value where known: {sum(float(v) for v in vals):,.0f}")
