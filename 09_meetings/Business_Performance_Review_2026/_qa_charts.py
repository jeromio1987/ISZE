"""Numeric paint check on every chart PNG: size, ink coverage, whether it is blank."""
from pathlib import Path
import numpy as np
from PIL import Image

d = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Business_Performance_Review_2026\charts_out")
rows = []
for f in sorted(d.glob("*.png")):
    im = Image.open(f).convert("RGB")
    a = np.array(im)
    g = np.array(im.convert("L"))
    ink = float((g < 245).mean() * 100)
    # colour diversity: how many distinct non-white colours in a coarse sample
    small = a[::8, ::8].reshape(-1, 3)
    nonwhite = small[(small.sum(axis=1) < 720)]
    uniq = len(np.unique(nonwhite // 24, axis=0)) if len(nonwhite) else 0
    flag = "BLANK?" if ink < 0.6 else ("THIN" if ink < 1.5 else "ok")
    rows.append((f.name, im.size, round(ink, 2), uniq, flag))

for r in rows:
    print(f"{r[0]:34s} {str(r[1]):14s} ink {r[2]:6.2f}%  colours {r[3]:4d}  {r[4]}")
print()
print("total", len(rows), "| problems:", [r[0] for r in rows if r[4] != "ok"])
