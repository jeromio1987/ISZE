"""Extract the ITUK (and network) leakage figures from the shipped leakage HTML."""
import json
import re
from pathlib import Path

HTML = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html")
t = HTML.read_text(encoding="utf-8")

# the payload is a JS array of objects assigned to something like const DATA = [...]
start = t.find('[{"db":')
assert start > 0, "payload start not found"
# find matching close bracket by scanning
depth = 0
end = None
for i in range(start, len(t)):
    ch = t[i]
    if ch == "[":
        depth += 1
    elif ch == "]":
        depth -= 1
        if depth == 0:
            end = i + 1
            break
assert end, "payload end not found"
payload = json.loads(t[start:end])
print("entities", len(payload))
out = {}
for row in payload:
    db = row.get("db")
    out[db] = row
    if db == "ITUK":
        print(json.dumps(row, indent=1)[:3000])

Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Business_Performance_Review_2026\_leakage_payload.json").write_text(
    json.dumps(out, indent=1), encoding="utf-8"
)
print("dbs:", sorted(out.keys()))
