from pathlib import Path

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html")
t = p.read_text(encoding="utf-8")
print("bytes", len(t))
for needle in ["<select", "id=", "ITUK"]:
    print(needle, t.count(needle))
# list select ids
import re

print("selects", re.findall(r'<select[^>]*id="([^"]+)"', t))
print("json blocks", re.findall(r'<script[^>]*type="application/json"[^>]*id="([^"]+)"', t))
print("toggles", re.findall(r'data-[a-z]+="[^"]*"', t)[:20])
print("ITUK count", t.count("ITUK"))
# find how entity filter works
i = t.find("ITUK")
print(t[max(0, i - 600): i + 600])
