"""Read-only: what moved between the saved before-copy and the rebuilt pages."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")

BEFORE = ISZE / "02_dashboards/_build/_aim_refresh2/before/ISZE_DB_DLR_Replenishment_CY2025.html"
NOW = ISZE / "02_dashboards/sales/ISZE_DB_DLR_Replenishment_CY2025.html"

old = BEFORE.read_text(encoding="utf-8", errors="replace")
new = NOW.read_text(encoding="utf-8", errors="replace")
print("replenishment page bytes", len(old), "->", len(new))

# page header KPIs
for pat in [r"gap_eur[^,]{0,40}", r"biggest_db", r"built_at[\"']?\s*[:=]\s*[\"']([^\"']+)"]:
    o = re.findall(pat, old)[:2]
    n = re.findall(pat, new)[:2]
    print("  ", pat, "| before", o, "| after", n)


def kpis(text: str) -> dict:
    m = re.search(r'"hero":\s*\{(.*?)\}', text, re.S)
    if not m:
        return {}
    return {k: v.strip('"') for k, v in re.findall(r'"([a-z_]+)":\s*("[^"]*"|[\d.]+)', m.group(1))}


ko, kn = kpis(old), kpis(new)
print("\nhero block changed keys:")
for k in sorted(set(ko) | set(kn)):
    if ko.get(k) != kn.get(k):
        print(f"   {k}: {ko.get(k)} -> {kn.get(k)}")
print("   (no differences)" if ko == kn else "")

# tonnage page: compare with the version at the last push
import subprocess
r = subprocess.run(["git", "show", "77edae82:02_dashboards/sales/ISZE_PMS_Tonnage_Evolution.html"],
                   cwd=ISZE, capture_output=True)
if r.returncode == 0:
    old_t = r.stdout.decode("utf-8", errors="replace")
    new_t = (ISZE / "02_dashboards/sales/ISZE_PMS_Tonnage_Evolution.html").read_text(
        encoding="utf-8", errors="replace")
    print("\ntonnage page (git 77edae82 -> now) bytes", len(old_t), "->", len(new_t))
    for pat in [r'"gap_eur":\s*([\d.]+)', r'"billed_eur":\s*([\d.]+)', r'"capture_rate":\s*([\d.]+)',
                r'"l1":"Unclassified"', r'"l1":"[A-Za-z &]+"']:
        o = re.findall(pat, old_t)
        n = re.findall(pat, new_t)
        so = sum(float(x) for x in o if x.replace('.', '', 1).isdigit())
        sn = sum(float(x) for x in n if x.replace('.', '', 1).isdigit())
        print(f"   {pat[:42]:<44} hits {len(o):>5} -> {len(n):>5}   sum {so:,.0f} -> {sn:,.0f}")
