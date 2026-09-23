"""Upscale the chart images so labels are legible, and crop the hi-res page renders."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922\_pdf")

def upscale(name: str, factor: int = 3):
    src = D / name
    im = Image.open(src).convert("RGB")
    out = im.resize((im.width * factor, im.height * factor), Image.LANCZOS)
    f = D / (src.stem + f"_x{factor}.png")
    out.save(f)
    print(f"{name} {im.size} -> {f.name} {out.size}")

for n in [
    "p14_img01_1254x683.jpeg",
    "p15_img01_1410x629.jpeg",
    "p17_img01_1319x607.jpeg",
    "p17_img02_1050x267.jpeg",
    "p13_img01_1244x541.png",
    "p18_img01_1267x680.jpeg",
]:
    try:
        upscale(n, 3)
    except Exception as e:  # noqa: BLE001
        print("skip", n, e)

# Crop the hi-res page 14 into thirds (left/middle/right) so the axis labels are crisp.
for p in (14, 15, 17):
    f = D / f"p{p:02d}_hi.png"
    im = Image.open(f).convert("RGB")
    w, h = im.size
    for i in range(3):
        box = (int(w * i / 3), 0, int(w * (i + 1) / 3), h)
        crop = im.crop(box)
        name = D / f"p{p:02d}_hi_part{i + 1}.png"
        crop.save(name)
        print("crop:", name.name, crop.size)
