# -*- coding: utf-8 -*-
"""Crop the ring region from the solo render, upscale it, and map every bearing so
the ring, its accent arcs and the arrowheads can be read directly."""
import math
import sys

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = (r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
       r"\_build\_render_ring\s01.png")
DST = (r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
       r"\_build\_render_ring\_zoom_ring.png")
SW, SH = 13.3333, 7.5
CX, CY = 6.6667, 4.15
im = Image.open(SRC).convert("RGB")
W, H = im.size

# crop 3.9in square around the centre, upscale so the ring fills the frame
half = 2.35
box = (int((CX - half) / SW * W), int((CY - half) / SH * H),
       int((CX + half) / SW * W), int((CY + half) / SH * H))
crop = im.crop(box)
crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
crop.save(DST)
print("wrote", DST, crop.size)

BG = (0x26, 0x26, 0x26)
RED = (0xE3, 0x06, 0x13)
AMBER = (0xF5, 0xA0, 0x00)
GREY = (0x4B, 0x4B, 0x4B)


def near(a, b, tol=34):
    return all(abs(a[i] - b[i]) <= tol for i in range(3))


def at(xin, yin):
    x = min(max(int(round(xin / SW * W)), 0), W - 1)
    y = min(max(int(round(yin / SH * H)), 0), H - 1)
    return im.getpixel((x, y))


print()
print("bearing map: each row is a bearing, R = red, A = amber, g = grey ring,")
print("             . = background, X = something else")
print("      radius -> 1.10 1.20 1.30 1.40 1.50 1.60")
for deg in range(0, 360, 6):
    rad = math.radians(deg)
    row = ""
    for rr in (1.10, 1.20, 1.30, 1.40, 1.50, 1.60):
        c = at(CX + rr * math.cos(rad), CY + rr * math.sin(rad))
        row += ("R" if near(c, RED) else
                "A" if near(c, AMBER) else
                "g" if near(c, GREY) else
                "." if near(c, BG) else "X")
    print("  %3d  %s" % (deg, "    ".join(row)))
