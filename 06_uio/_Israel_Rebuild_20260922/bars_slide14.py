"""Locate the bars in the slide-14 chart via OpenCV so the series can be read off reliably."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Israel_Rebuild_20260922\_pdf")
SRC = D / "p14_img01_1254x683.jpeg"

img = cv2.imread(str(SRC))
print("image:", img.shape)
h, w = img.shape[:2]

# Dominant colours (quantised) to find the bar fill colour
small = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
flat = small.reshape(-1, 3)
q = (flat // 16 * 16)
cols, counts = np.unique(q, axis=0, return_counts=True)
order = np.argsort(-counts)
print("\ntop 15 quantised colours (BGR, count, share):")
for i in order[:15]:
    print(f"  {tuple(int(v) for v in cols[i])}  {counts[i]:>7}  {counts[i] / len(flat) * 100:5.2f}%")

# Try a saturation mask: bars are usually the saturated thing on a white slide
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
sat = hsv[:, :, 1]
val = hsv[:, :, 2]
print("\nsaturation: max", int(sat.max()), "mean", round(float(sat.mean()), 1))
print("value: max", int(val.max()), "mean", round(float(val.mean()), 1))
hist = np.histogram(sat, bins=10, range=(0, 256))[0]
print("saturation histogram:", hist.tolist())

for thresh in (40, 60, 80, 100):
    mask = (sat > thresh).astype(np.uint8) * 255
    n = int((mask > 0).sum())
    print(f"  sat>{thresh}: {n} px ({n / (w * h) * 100:.2f}%)")

# Connected components on the saturated mask
mask = (sat > 60).astype(np.uint8) * 255
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
num, labels, stats, cents = cv2.connectedComponentsWithStats(mask, connectivity=8)
cands = []
for i in range(1, num):
    x, y, bw, bh, area = stats[i]
    if bh >= h * 0.06 and bw >= 3 and bw <= w * 0.08:
        cands.append((x, y, bw, bh, area, cents[i]))
cands.sort(key=lambda t: t[0])
print(f"\ncandidate bars (tall thin saturated blobs): {len(cands)}")
for x, y, bw, bh, area, c in cands:
    print(f"  x={x:>4} y={y:>4} w={bw:>3} h={bh:>4} area={area:>6} cx={c[0]:7.1f}")

cv2.imwrite(str(D / "p14_satmask.png"), mask)
print("\nwrote:", D / "p14_satmask.png")
