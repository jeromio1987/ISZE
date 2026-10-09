# -*- coding: utf-8 -*-
"""Objective check on the solo ring render:
 - is the centre open (background, no ink)?
 - is there a closed ring of ink at radius R (all bearings)?
 - where are the accent arcs (should be the four diagonal gaps)?
 - which way do the arrowheads point (should be clockwise)?
"""
import math
import sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PNG = (r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
       r"\_build\_render_ring\s01.png")
SW, SH = 13.3333, 7.5
CX, CY, R = 6.6667, 4.15, 1.50
im = Image.open(PNG).convert("RGB")
W, H = im.size
print("render", W, "x", H)

BG = (0x26, 0x26, 0x26)
RED = (0xE3, 0x06, 0x13)
AMBER = (0xF5, 0xA0, 0x00)
GREY = (0x4B, 0x4B, 0x4B)
WHITE = (0xF2, 0xF2, 0xF2)
PANEL = (0x30, 0x30, 0x30)


def px(xin, yin):
    x = int(round(xin / SW * W))
    y = int(round(yin / SH * H))
    x = min(max(x, 0), W - 1)
    y = min(max(y, 0), H - 1)
    return im.getpixel((x, y))


def near(a, b, tol=34):
    return all(abs(a[i] - b[i]) <= tol for i in range(3))


def tag(c):
    for n, v in (("BG", BG), ("RED", RED), ("AMBER", AMBER), ("GREY", GREY),
                 ("WHITE", WHITE), ("PANEL", PANEL)):
        if near(c, v):
            return n
    return "?"


print()
print("== centre open?  4x4 samples inside r < 0.55R ==")
bad = []
for dx in (-0.35, -0.15, 0.0, 0.15, 0.35):
    row = []
    for dy in (-0.30, -0.10, 0.10, 0.30):
        c = px(CX + dx, CY + dy)
        t = tag(c)
        row.append(t)
        if t in ("RED", "AMBER", "GREY"):
            bad.append((dx, dy, t))
    print("  dx=%+.2f  %s" % (dx, " ".join("%-6s" % x for x in row)))
print("  ink found in the centre:", bad if bad else "NONE  -> centre is open")

print()
print("== ring closure: sample 72 bearings at r = R (and at R +/- 0.09) ==")
for rr, nm in ((R - 0.09, "inner edge"), (R, "R"), (R + 0.09, "outer edge")):
    marks = []
    for deg in range(0, 360, 5):
        a = math.radians(deg)
        c = px(CX + rr * math.cos(a), CY + rr * math.sin(a))
        marks.append((deg, tag(c)))
    hits = [d for d, t in marks if t in ("RED", "AMBER", "GREY", "WHITE")]
    gaps = []
    for d in range(0, 360, 5):
        if d not in hits:
            gaps.append(d)
    # collapse
    segs = []
    if gaps:
        cur = [gaps[0], gaps[0]]
        for g in gaps[1:]:
            if g - cur[1] <= 5:
                cur[1] = g
            else:
                segs.append(tuple(cur))
                cur = [g, g]
        segs.append(tuple(cur))
    print("  %-11s empty bearings: %s" % (nm, segs if segs else "none"))

print()
print("== accent arc bearings (red at r = R) ==")
reds = []
for deg in range(0, 360, 2):
    a = math.radians(deg)
    if near(px(CX + R * math.cos(a), CY + R * math.sin(a)), RED):
        reds.append(deg)
segs = []
if reds:
    cur = [reds[0], reds[0]]
    for d in reds[1:]:
        if d - cur[1] <= 2:
            cur[1] = d
        else:
            segs.append(tuple(cur))
            cur = [d, d]
    segs.append(tuple(cur))
    if len(segs) > 1 and segs[0][0] == 0 and segs[-1][1] >= 358:
        segs[0] = (segs[-1][0] - 360, segs[0][1])
        segs.pop()
print("  red arc spans:", segs)
print("  expected gaps at 315, 45, 135, 225  (+/- the arc half-width)")

print()
print("== arrowheads: amber ink bearings at r in [R-0.30, R+0.05] ==")
amber = {}
for deg in range(0, 360, 2):
    a = math.radians(deg)
    for rr in [R - 0.30 + k * 0.02 for k in range(18)]:
        if near(px(CX + rr * math.cos(a), CY + rr * math.sin(a)), AMBER):
            amber.setdefault(deg, []).append(rr)
segs = []
ks = sorted(amber)
if ks:
    cur = [ks[0], ks[0]]
    for d in ks[1:]:
        if d - cur[1] <= 2:
            cur[1] = d
        else:
            segs.append(tuple(cur))
            cur = [d, d]
    segs.append(tuple(cur))
    if len(segs) > 1 and segs[0][0] == 0 and segs[-1][1] >= 358:
        segs[0] = (segs[-1][0] - 360, segs[0][1])
        segs.pop()
print("  amber spans:", segs)
for s0, s1 in segs:
    mid = ((s0 + s1) / 2.0) % 360
    rads = amber.get(int(mid) - (int(mid) % 2), [])
    tip_r = max(rads) if rads else None
    base_r = min(rads) if rads else None
    print("    span %s mid %.0f deg  ink radius %.3f -> %.3f in  (tip outward = %s)"
          % ((s0, s1), mid, base_r, tip_r, tip_r and tip_r > base_r))
