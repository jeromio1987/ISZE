# -*- coding: utf-8 -*-
"""Measure probe 2: where does each ARC actually sit, and where do the rotated
triangles point? Polar sampling around each shape centre."""
import math
import sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PNG = (r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
       r"\_build\_render2\s01.png")
SW, SH = 13.3333, 7.5
im = Image.open(PNG).convert("RGB")
W, H = im.size


def px(xin, yin):
    return im.getpixel((int(xin / SW * W), int(yin / SH * H)))


RED = (0xE3, 0x06, 0x13)
AMBER = (0xF5, 0xA0, 0x00)


def near(a, b, tol=40):
    return all(abs(a[i] - b[i]) <= tol for i in range(3))


def arc_span(x, y, d, tag, colour=RED):
    """sample 72 angles at 0.88R (inside the stroke) and report filled bearings"""
    cx, cy = x + d / 2.0, y + d / 2.0
    r = d / 2.0 * 0.80
    hits = []
    for deg in range(0, 360, 2):
        # screen bearings: 0 = 3 o'clock, increasing clockwise (y grows down)
        a = math.radians(deg)
        sx = cx + r * math.cos(a)
        sy = cy + r * math.sin(a)
        if near(px(sx, sy), colour):
            hits.append(deg)
    if not hits:
        print("%-16s NO INK at 0.80R" % tag)
        return
    # collapse to contiguous ranges
    segs = []
    cur = [hits[0], hits[0]]
    for h in hits[1:]:
        if h - cur[1] <= 2:
            cur[1] = h
        else:
            segs.append(tuple(cur))
            cur = [h, h]
    segs.append(tuple(cur))
    if len(segs) > 1 and segs[0][0] == 0 and segs[-1][1] >= 358:
        segs[0] = (segs[-1][0] - 360, segs[0][1])
        segs.pop()
    print("%-16s ink bearings %s" % (tag, segs))


print("== A: ARC explicit angle pairs, each on its own 2.4in square ==")
for tag, x in (("0-90", 0.6), ("90-180", 3.4), ("180-270", 6.2), ("270-360", 9.0)):
    arc_span(x, 0.7, 2.4, tag)

print()
print("== B: same ARC (270-360) rotated 90/180/270 ==")
for tag, x in (("rot90", 0.6), ("rot180", 3.4), ("rot270", 6.2)):
    arc_span(x, 3.6, 2.4, tag)

print()
print("== C: rotated triangles, apex bearing (0 = up/12 o'clock) ==")
rots = [0, 45, 90, 135, 180, 225, 270, 315]
for i, rot in enumerate(rots):
    bx = 9.4 + (i % 4) * 0.85
    by = 3.6 + (i // 4) * 0.95
    cx, cy = bx + 0.25, by + 0.20
    best, bang = -1, None
    for deg in range(0, 360, 2):
        a = math.radians(deg - 90)          # deg 0 = up
        sx = cx + 0.16 * math.cos(a)
        sy = cy + 0.16 * math.sin(a)
        c = px(sx, sy)
        if near(c, AMBER):
            d = abs(((deg + 180) % 360) - 180)
            # score: how far from centre the ink is, weighted by pointing up
            if d < 40 and best < 0:
                best, bang = deg, deg
    print("  rotation request %3d -> ink found near up: %s" % (rot, bang is not None))

print()
print("== D: DONUT hole=0.28 cross-section (bbox fractions) ==")
cy = 0.7 + 2.4 / 2.0
row = ""
for i in range(41):
    fx = 10.2 + 2.4 * i / 40.0
    c = px(fx, cy)
    row += "R" if near(c, RED) else "."
print("  %s" % row)
