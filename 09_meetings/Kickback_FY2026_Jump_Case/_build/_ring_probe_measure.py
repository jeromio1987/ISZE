# -*- coding: utf-8 -*-
"""Measure the probe render: does each candidate leave an open centre, and what
does it look like at the ring radius? Reads the exported PNG pixel by pixel."""
import sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PNG = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\_build\_render\s01.png"
SW, SH = 13.3333, 7.5
im = Image.open(PNG).convert("RGB")
W, H = im.size
print("render", W, "x", H)


def px(xin, yin):
    return im.getpixel((int(xin / SW * W), int(yin / SH * H)))


CANDS = {
    "A DONUT solid RED":            (0.4, 0.8, 2.2, 2.2),
    "B DONUT no fill":              (3.0, 0.8, 2.2, 2.2),
    "C BLOCK_ARC solid RED":        (5.6, 0.8, 2.2, 2.2),
    "D CIRCULAR_ARROW solid RED":   (8.2, 0.8, 2.6, 2.2),
    "E ARC no fill +line":          (11.4, 0.8, 1.6, 1.6),
    "F OVAL no fill +8pt line":     (0.4, 3.5, 2.2, 2.2),
    "G PIE solid RED":              (3.0, 3.5, 2.2, 2.2),
    "H ARC default":                (5.6, 3.5, 2.2, 2.2),
    "I DONUT nofill 14pt + text":   (8.2, 3.5, 2.2, 2.2),
}

BG = (0x26, 0x26, 0x26)
RED = (0xE3, 0x06, 0x13)
AMBER = (0xF5, 0xA0, 0x00)
GREEN = (0x31, 0xA3, 0x54)
WHITE = (0xF2, 0xF2, 0xF2)


def near(a, b, tol=26):
    return all(abs(a[i] - b[i]) <= tol for i in range(3))


def name(c):
    for n, v in (("BG", BG), ("RED", RED), ("AMBER", AMBER), ("GREEN", GREEN),
                 ("WHITE", WHITE)):
        if near(c, v):
            return n
    return str(c)


print()
print("%-30s %-22s %-22s" % ("candidate", "geometric centre", "edge of bbox (mid-left)"))
for k, (x, y, w, h) in CANDS.items():
    cx, cy = x + w / 2.0, y + h / 2.0
    print("%-30s %-22s %-22s" % (k, name(px(cx, cy)), name(px(x + 0.03, cy))))

print()
print("ring cross-section along the horizontal centre line of each candidate")
print("(values sampled at bbox-relative fractions; R = ink, . = background)")
for k, (x, y, w, h) in CANDS.items():
    cy = y + h / 2.0
    row = ""
    for i in range(41):
        fx = x + w * i / 40.0
        c = px(fx, cy)
        row += "R" if near(c, RED) else ("A" if near(c, AMBER) else
                                        ("G" if near(c, GREEN) else
                                         ("W" if near(c, WHITE) else ".")))
    print("%-30s %s" % (k, row))

print()
print("vertical cross-section through the centre of each candidate")
for k, (x, y, w, h) in CANDS.items():
    cx = x + w / 2.0
    col = ""
    for i in range(41):
        fy = y + h * i / 40.0
        c = px(cx, fy)
        col += "R" if near(c, RED) else ("A" if near(c, AMBER) else
                                        ("G" if near(c, GREEN) else
                                         ("W" if near(c, WHITE) else ".")))
    print("%-30s %s" % (k, col))
