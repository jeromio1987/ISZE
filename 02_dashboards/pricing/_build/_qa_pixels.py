"""Pixel and DOM verification of the pricing dashboard screenshots.

The previous check counted substrings in the raw DOM, which also contains the page
script, so it could not tell a rendered row from a template string. This one reads
the PNGs and counts ink per horizontal band, and counts rendered rows inside the
table bodies only.

Run: python 02_dashboards/pricing/_build/_qa_pixels.py
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_qa")
DOM = QA / "_dump_dom.txt"


def band_ink(img: Image.Image, y0: int, y1: int) -> float:
    """Share of sampled pixels that are not near-white in a horizontal band."""
    w, h = img.size
    y1 = min(y1, h)
    if y1 <= y0:
        return 0.0
    px = img.crop((0, y0, w, y1)).convert("L").resize((320, max(1, (y1 - y0) // 6)))
    data = px.getdata()
    dark = sum(1 for v in data if v < 232)
    return 100 * dark / max(1, len(data))


def analyse(name: str) -> None:
    f = QA / name
    img = Image.open(f).convert("RGB")
    w, h = img.size
    print(f"\n{name}  {w}x{h}")
    n = 14
    for i in range(n):
        y0, y1 = h * i // n, h * (i + 1) // n
        ink = band_ink(img, y0, y1)
        bar = "#" * int(ink / 2)
        flag = "  <-- BLANK" if ink < 1.0 else ""
        print(f"  band {i:2}  y{y0:5}-{y1:5}  ink {ink:5.1f}%  {bar}{flag}")


def dom_check() -> None:
    dom = DOM.read_text(encoding="utf-8", errors="replace")
    # strip the script blocks so only rendered markup is measured
    markup = re.sub(r"<script[\s\S]*?</script>", "", dom)
    tbody = lambda tid: re.search(
        r'<table id="' + tid + r'">[\s\S]*?</table>', markup)
    print("\nRENDERED MARKUP (script blocks removed)")
    print(f"  kpi chips          {markup.count('class=\"kpi')}")
    print(f"  canvas elements    {markup.count('<canvas')}")
    print(f"  select options     {markup.count('<option')}")
    for tid in ("drill", "movers", "custs"):
        m = tbody(tid)
        if not m:
            print(f"  {tid:18} table not found")
            continue
        body = re.search(r"<tbody>([\s\S]*?)</tbody>", m.group(0))
        rows = body.group(1).count("<tr") if body else 0
        print(f"  {tid:18} rendered rows {rows}")
    print(f"  KPI headline values {re.findall(r'class=.val.>([^<]+)<', markup)[:6]}")


if __name__ == "__main__":
    for n in ("01_wide_top.png", "02_narrow.png", "03_full.png"):
        analyse(n)
    dom_check()
