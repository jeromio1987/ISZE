from pathlib import Path
import re

root = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards")
assets = root / "propertiq-assets"
side_assets = root / "side" / "propertiq-assets"
print("root assets exists", assets.exists(), "count", len(list(assets.glob('*'))) if assets.exists() else 0)
print("side assets exists", side_assets.exists())
if assets.exists():
    print([p.name for p in assets.iterdir()][:30])

html = (root / "side" / "PROPERTIQ.html").read_text(encoding="utf-8")
refs = re.findall(r"propertiq-assets/[^\s\"']+", html)
print("refs", refs[:40])
missing = []
for r in refs:
    # resolve relative to side/
    p = (root / "side" / r).resolve()
    alt = (root / r).resolve()
    if not p.exists() and not alt.exists():
        missing.append((r, str(p), str(alt)))
print("missing", missing[:20])
