import json
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "04_tools" / "ISZE_Tender_Monitor_Install" / "_source_health.json"
# Install lives under ISZE/04_tools — parents[2] from 91_build/_scratch is 01_data; go via ISZE root
p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ISZE_Tender_Monitor_Install\_source_health.json")
h = json.loads(p.read_text(encoding="utf-8"))
counts: dict[str, int] = {}
for v in h.values():
    if isinstance(v, dict):
        counts[v.get("status") or "?"] = counts.get(v.get("status") or "?", 0) + 1
print("entries", len(h), counts)
for k, v in sorted(h.items()):
    if isinstance(v, dict) and v.get("status") in ("AWAITING_KEY", "CODE_READY", "BROKEN"):
        print(f"  {v.get('status'):12} {k}: count={v.get('last_count')} err={v.get('last_error')}")
