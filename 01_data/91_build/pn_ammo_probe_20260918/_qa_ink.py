"""Measure ink per horizontal band of the rendered page.

Image-reading alone misled the builder twice on this file, so measure instead of judging by eye:
for each band of the screenshot, count the share of pixels that are not the page background. An
empty chart container shows as a band with almost no ink.
"""

from pathlib import Path

from PIL import Image

QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_tonnage")

for name in ("page-1440.png", "page-1000.png"):
    p = QA / name
    if not p.is_file():
        print(f"{name}: MISSING")
        continue
    im = Image.open(p).convert("RGB")
    w, h = im.size
    print(f"\n=== {name}: {w} x {h} ===")
    # Paper background is #f7f4ee; anything materially different is content.
    band = 100
    empty = []
    for y in range(0, h, band):
        crop = im.crop((0, y, w, min(h, y + band)))
        px = list(crop.getdata())
        n = len(px)
        ink = sum(1 for r, g, b in px if abs(r - 247) > 12 or abs(g - 244) > 12 or abs(b - 238) > 12)
        share = 100 * ink / n
        flag = ""
        if share < 1.0:
            flag = "  <-- NEARLY EMPTY"
            empty.append(y)
        print(f"  y {y:5d}-{min(h, y+band):5d}  ink {share:6.2f}%{flag}")
    if empty:
        print(f"  RESULT: {len(empty)} empty band(s) at y = {empty}")
    else:
        print("  RESULT: every band carries content — no blank region")
