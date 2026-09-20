"""Crop the band section screenshot into readable slices so each one is actually read."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa_family_deep")
src = Image.open(QA / "bands_1440.png").convert("RGB")
W, H = src.size
print("source", W, H)
# find the last row that is not blank, so the crops stop at content
import numpy as np

a = np.asarray(src).astype(int)
rows = (a.sum(axis=2) < 720).mean(axis=1)
content = [i for i, v in enumerate(rows) if v > 0.004]
end = (content[-1] + 40) if content else H
print("first content row", content[0] if content else None, "last", content[-1] if content else None)

slices = [(0, 780), (740, 1560), (1520, 2350), (2310, end if end > 3100 else 3100)]
for i, (y0, y1) in enumerate(slices, 1):
    y1 = min(y1, H)
    out = QA / f"bands_slice_{i}.png"
    src.crop((0, y0, W, y1)).save(out)
    print(f"wrote {out.name}  rows {y0}-{y1}  {out.stat().st_size} bytes")
