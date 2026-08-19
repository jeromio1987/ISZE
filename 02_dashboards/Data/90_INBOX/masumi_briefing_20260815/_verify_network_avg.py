import json
import re
from pathlib import Path

base = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\ids")
files = [
    "IDS_2026_dealer_compare_Belgium.html",
    "IDS_2026_dealer_compare_France.html",
    "IDS_2026_dealer_compare_Israel_LCV.html",
    "IDS_2026_dealer_compare_Netherlands.html",
    "IDS_2026_dealer_compare_Portugal.html",
    "IDS_2026_dealer_compare_UK_LCV.html",
    "IDS_2026_dealer_compare_Spain.html",
    "IDS_2026_dealer_compare_Italy.html",
]
avgs = []
for name in files:
    t = (base / name).read_text(encoding="utf-8")
    m = re.search(r"const DATA = (\{.*\});", t)
    d = json.loads(m.group(1))
    net = d.get("network") or {}
    c = (d.get("countries") or ["?"])[0]
    p = (d.get("country_profiles") or {}).get(c) or {}
    navg = net.get("total_pct") or net.get("avg_pct")
    avgs.append(navg)
    print(
        f"{c:14} network={None if navg is None else round(navg*100,1)}"
        f"  E={None if (net.get('sections_pct') or {}).get('E') is None else round((net.get('sections_pct') or {}).get('E')*100,1)}"
        f"  national={round((p.get('total_pct') or p.get('avg_pct') or 0)*100,1)}"
        f"  excl={p.get('excluded_from_average_count')}"
    )
print("unique network avgs", set(avgs))
