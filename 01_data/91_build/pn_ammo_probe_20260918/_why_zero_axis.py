"""Inspect the decomposition payload and the axisTick formatter."""

import json
import re
from pathlib import Path

P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales"
         r"\ISZE_PMS_Family_Evolution_v2.html")
h = P.read_text(encoding="utf-8", errors="ignore")

print("=" * 92)
print("1. THE axisTick FORMATTER")
print("=" * 92)
for m in re.finditer(r"function axisTick[^{]*\{(.{0,420}?)\}", h, re.S):
    print(re.sub(r"\s+", " ", m.group(0))[:420])
for m in re.finditer(r"axisTick\s*=\s*function[^{]*\{(.{0,420}?)\}", h, re.S):
    print(re.sub(r"\s+", " ", m.group(0))[:420])
for m in re.finditer(r"(var|const|let)\s+axisTick\s*=\s*[^;]{0,420};", h, re.S):
    print(re.sub(r"\s+", " ", m.group(0))[:420])

print()
print("=" * 92)
print("2. THE atoms PAYLOAD — the per-part-number decomposition")
print("=" * 92)
m = re.search(r'<script id="[^"]*" type="application/json">(.*?)</script>', h, re.S)
d = json.loads(m.group(1))
atoms = d.get("atoms")
print("  type:", type(atoms).__name__)
if isinstance(atoms, list) and atoms:
    print("  rows:", f"{len(atoms):,}")
    print("  cols:", list(atoms[0].keys()))
    print("  first row:", json.dumps(atoms[0])[:500])
    print()
    for c in atoms[0].keys():
        vals = [a.get(c) for a in atoms if isinstance(a.get(c), (int, float))]
        if vals:
            print(f"    {c:22s} min {min(vals):12.4f}  max {max(vals):12.4f}")
elif isinstance(atoms, dict):
    print("  keys:", list(atoms.keys())[:20])
    k = list(atoms.keys())[0]
    print(f"  {k}:", json.dumps(atoms[k])[:400])

print()
print("=" * 92)
print("3. splitCheck — does the page know its own split is consistent?")
print("=" * 92)
print(json.dumps(d.get("splitCheck"), indent=2)[:900])

print()
print("=" * 92)
print("4. comparability — what does it say is NOT comparable?")
print("=" * 92)
print(json.dumps(d.get("comparability"), indent=2)[:800])
