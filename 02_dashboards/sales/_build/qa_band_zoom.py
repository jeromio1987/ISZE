"""Zoomed crops of the band cards and the two tables, so small text can be read."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_family_deep")
src = Image.open(QA / "bands_1440.png").convert("RGB")
W, H = src.size

zones = {
    "zoom_cards": (0, 150, W, 560),
    "zoom_chart": (0, 560, W, 1000),
    "zoom_split_head": (0, 2100, W, 2400),
    "zoom_split_rows": (0, 2350, W, 2900),
    "zoom_evidence": (0, 1500, W, 1900),
}
for name, box in zones.items():
    im = src.crop(box)
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    out = QA / f"{name}.png"
    im.save(out)
    print(f"wrote {out.name}  {im.size}  {out.stat().st_size} bytes")
