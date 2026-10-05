#!/usr/bin/env python3
from pathlib import Path

pre = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\Data\dashboards\isze_data.preload.js")
print("preload", pre.exists(), pre.stat().st_size if pre.exists() else 0)
if pre.exists():
    print(pre.read_text(encoding="utf-8", errors="replace")[:240])

html = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_Competitiveness_Dashboard.html").read_text(
    encoding="utf-8"
)
for needle in ("Data unavailable", "isze_data.preload", "__PRELOADS__", "Data/dashboards/isze_data"):
    print(needle, html.count(needle))
