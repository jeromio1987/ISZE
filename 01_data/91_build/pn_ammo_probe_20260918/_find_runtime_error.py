"""Locate the runtime error: which element ids does the script expect but the page lacks?"""

import re
from pathlib import Path

P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales"
         r"\ISZE_PMS_Family_Evolution_v2.html")
h = P.read_text(encoding="utf-8", errors="ignore")

ids = set(re.findall(r'id="([A-Za-z0-9_\-]+)"', h))
lookups = set(re.findall(r"getElementById\(['\"]([A-Za-z0-9_\-]+)['\"]\)", h))

print("ids defined in the page      :", len(ids))
print("getElementById targets in js :", len(lookups))
missing = sorted(x for x in lookups if x not in ids)
print()
print("MISSING ids the script expects but the page does not define:")
for m in missing:
    n = len(re.findall(re.escape(m), h))
    print(f"   {m:28s} referenced {n}x")
print("total missing:", len(missing))

# Where is handleEvent used, and could a listener be undefined?
print()
print("=" * 92)
print("handleEvent context")
print("=" * 92)
for m in re.finditer(r".{140}handleEvent.{140}", h, re.S):
    print(re.sub(r"\s+", " ", m.group(0))[:300])
    print("  ---")

# Is Chart.js called with a canvas that does not exist?
print()
print("=" * 92)
print("canvas ids vs getContext calls")
print("=" * 92)
canv = set(re.findall(r'<canvas[^>]*id="([A-Za-z0-9_\-]+)"', h))
ctx = set(re.findall(r"getElementById\(['\"]([A-Za-z0-9_\-]+)['\"]\)\.getContext", h))
print("  canvases:", sorted(canv))
print("  getContext targets:", sorted(ctx))
print("  ctx target without canvas:", sorted(ctx - canv))
