# -*- coding: utf-8 -*-
"""Determine ISOSCELES_TRIANGLE apex direction vs requested rotation, precisely,
by computing the ink centroid inside each shape's bounding box."""
import sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PNG = (r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
       r"\_build\_render2b\s01.png")
SW, SH = 13.3333, 7.5
im = Image.open(PNG).convert("RGB")
W, H = im.size
AMBER = (0xF5, 0xA0, 0x00)


def near(a, b, tol=60):
    return all(abs(a[i] - b[i]) <= tol for i in range(3))


rots = [0, 45, 90, 135, 180, 225, 270, 315]
print("%-8s %-10s %-10s %-14s %s" % ("req", "cx_frac", "cy_frac", "apex_guess", "note"))
for i, rot in enumerate(rots):
    bx = 9.4 + (i % 4) * 0.85
    by = 3.6 + (i // 4) * 0.95
    bw, bh = 0.50, 0.40
    tot = 0
    sx = sy = 0.0
    xs, ys = [], []
    for gx in range(60):
        for gy in range(60):
            xin = bx + bw * gx / 59.0
            yin = by + bh * gy / 59.0
            px = int(xin / SW * W)
            py = int(yin / SH * H)
            if 0 <= px < W and 0 <= py < H and near(im.getpixel((px, py)), AMBER):
                tot += 1
                sx += gx / 59.0
                sy += gy / 59.0
                xs.append(gx / 59.0)
                ys.append(gy / 59.0)
    if tot == 0:
        print("%-8d NO INK" % rot)
        continue
    cx, cy = sx / tot, sy / tot
    # apex is the opposite direction from the centroid relative to bbox centre
    dx, dy = 0.5 - cx, 0.5 - cy
    import math
    ang = math.degrees(math.atan2(dy, dx))     # screen coords: y down
    # convert to compass: 0 = up, clockwise
    compass = (ang + 90) % 360
    print("%-8d %-10.3f %-10.3f %-14.1f %s" % (rot, cx, cy, compass,
          "(dx=%.3f dy=%.3f)" % (dx, dy)))
