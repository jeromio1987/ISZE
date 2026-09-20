import re
from pathlib import Path

P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_design\chart_gallery"
         r"\ISZE_Chart_Forms_Gallery.html")
h = P.read_text(encoding="utf-8", errors="ignore")
print("canvases:", len(re.findall(r"<canvas", h)))
print("external src/href:", re.findall(r'(?:src|href)="https?://[^"]+', h)[:6])
print("external script tags:", len(re.findall(r'<script[^>]+src=', h)))
print("chart.js inlined:", ("Chart.register" in h) or ("chart.umd" in h.lower()))
print("size KB:", round(len(h) / 1024))
print()
print("panel titles (h2/h3):")
for m in re.finditer(r"<h[23][^>]*>(.*?)</h[23]>", h, re.S):
    t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    if t:
        print("  -", t[:110])
print()
print("weakness captions found:", len(re.findall(r"(?i)weakness", h)))
print("strength captions found:", len(re.findall(r"(?i)strength", h)))
