"""Targeted crop of slide 17's fleet-count column so the 2021 and 2023 anchors can be read."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922\_pdf")
im = Image.open(D / "p17_hi.png").convert("RGB")
w, h = im.size
print("p17_hi:", im.size)

# fleet-count column sits at absolute x ~ 3350-3700, y ~ 2050-2950
box = (3280, 2020, 3780, 2980)
c = im.crop(box)
c = c.resize((c.width * 2, c.height * 2), Image.LANCZOS)
f = D / "p17_fleetcol.png"
c.save(f)
print("wrote", f.name, c.size)

# and the parts-sales-per-truck column, plus the left stacked series
box2 = (1150, 2020, 1700, 2980)
c2 = im.crop(box2)
c2 = c2.resize((c2.width * 2, c2.height * 2), Image.LANCZOS)
f2 = D / "p17_partscol.png"
c2.save(f2)
print("wrote", f2.name, c2.size)
