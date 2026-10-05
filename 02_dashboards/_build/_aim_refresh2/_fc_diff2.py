"""Read-only: what moved in the family compare page between git 77edae82 and now."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
rel = "02_dashboards/sales/ISZE_PMS_Family_Compare.html"
old = subprocess.run(["git", "show", f"77edae82:{rel}"], cwd=ISZE,
                     capture_output=True).stdout.decode("utf-8", errors="replace")
new = (ISZE / rel).read_text(encoding="utf-8", errors="replace")
print("bytes", len(old), "->", len(new))

for pat in [r'"aim_l1":\s*"([^"]+)"', r'"bvp":[^,]{0,30}', r"Unclassified", r'"urea"[^,]{0,30}',
            r'"gap_eur":\s*([\d.]+)']:
    o = re.findall(pat, old)
    n = re.findall(pat, new)
    print(f"  {pat[:36]:<38} hits {len(o):>5} -> {len(n):>5}")

# family-level euro, if present
for key in ["bvp_expose", "aim_family"]:
    po = re.findall(rf'"{key}"[^\]]{{0,400}}', old)
    pn = re.findall(rf'"{key}"[^\]]{{0,400}}', new)
    if po or pn:
        print(f"\n{key} before:\n  {po[0][:300] if po else '-'}")
        print(f"{key} after:\n  {pn[0][:300] if pn else '-'}")
