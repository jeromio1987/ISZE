import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = json.load(open(r'01_data\00_derived\_verification_report.json', encoding='utf-8'))
print("summary:", d["summary"], "generated_at:", d["generated_at"])
for c in d["checks"]:
    cid = c["id"]
    if cid.startswith("schema.") or "gps" in cid.lower() or "aim" in cid.lower():
        print(f"[{c['status']}] {cid}: {c['message']}")
