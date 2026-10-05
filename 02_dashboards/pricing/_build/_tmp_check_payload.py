import json
import re
from pathlib import Path

html = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing"
    r"\ISZE_Pricing_Revision_AIM_Source.html"
).read_text(encoding="utf-8")

m = re.search(r"var D=(\{.*?\});\s*var P=", html, re.S)
if not m:
    m = re.search(r"const D=(\{.*?\});", html, re.S)
if not m:
    m = re.search(r"id=[\"']payload[\"']>(\{.*?\})</script>", html, re.S)
print("match", bool(m))
if not m:
    # show how data is embedded
    for needle in ("payload", "var D", "__PAYLOAD__", "application/json"):
        print(needle, html.find(needle))
    raise SystemExit(1)

d = json.loads(m.group(1))
nhi = d["pool"]["src"].index("Not held")
gs = [r for r in d["groups"] if r[4] == nhi]
print("nh groups", len(gs))
print("all", round(sum(r[12] for r in gs), 2))
print("billed", round(sum(r[8] for r in gs), 2))
print("totals.billed", d["totals"]["billed"])
print("totals.priced_billed", d["totals"].get("priced_billed"))
zeros = [r for r in gs if r[8] == 0 and r[12] > 0]
print("unpriced-only nh", len(zeros), "all", round(sum(r[12] for r in zeros), 2))
