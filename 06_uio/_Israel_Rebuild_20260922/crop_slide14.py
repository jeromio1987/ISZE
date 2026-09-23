"""Tight crops of the slide-14 figure so the age-band labels can be read."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922\_pdf")

src = D / "p14_img01_1254x683.jpeg"
im = Image.open(src).convert("RGB")
print("source:", im.size)
w, h = im.size

# horizontal bands
regions = {
    "top": (0, 0, w, int(h * 0.40)),
    "mid": (0, int(h * 0.33), w, int(h * 0.72)),
    "bot": (0, int(h * 0.62), w, h),
}
for name, box in regions.items():
    c = im.crop(box)
    c = c.resize((c.width * 5, c.height * 5), Image.LANCZOS)
    f = D / f"p14_fig_{name}_x5.png"
    c.save(f)
    print("wrote", f.name, c.size)

# left / right halves of the whole figure (table is usually left, chart right)
for name, box in {"left": (0, 0, int(w * 0.55), h), "right": (int(w * 0.45), 0, w, h)}.items():
    c = im.crop(box)
    c = c.resize((c.width * 4, c.height * 4), Image.LANCZOS)
    f = D / f"p14_fig_{name}_x4.png"
    c.save(f)
    print("wrote", f.name, c.size)
