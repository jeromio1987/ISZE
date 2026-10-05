"""Tile slide-14's figure into small native-resolution chunks that survive the image reader."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922\_pdf")
SRC = D / "p14_img01_1254x683.jpeg"

im = Image.open(SRC).convert("RGB")
w, h = im.size
cols, rows = 3, 3
tw, th = w // cols, h // rows
for r in range(rows):
    for c in range(cols):
        box = (c * tw, r * th, min((c + 1) * tw + 20, w), min((r + 1) * th + 20, h))
        crop = im.crop(box)
        crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
        f = D / f"p14_tile_r{r + 1}c{c + 1}.png"
        crop.save(f)
        print("wrote", f.name, crop.size)

# Also do the same for slide 15 (the top-15 models table)
SRC15 = D / "p15_img01_1410x629.jpeg"
im15 = Image.open(SRC15).convert("RGB")
w15, h15 = im15.size
tw15, th15 = w15 // 2, h15 // 3
for r in range(3):
    for c in range(2):
        box = (c * tw15, r * th15, min((c + 1) * tw15 + 25, w15), min((r + 1) * th15 + 25, h15))
        crop = im15.crop(box)
        crop = crop.resize((int(crop.width * 1.8), int(crop.height * 1.8)), Image.LANCZOS)
        f = D / f"p15_tile_r{r + 1}c{c + 1}.png"
        crop.save(f)
        print("wrote", f.name, crop.size)
