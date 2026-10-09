# -*- coding: utf-8 -*-
"""Precise 1-degree scan of the ring radius: how many red arcs, where, and where
does the ring show grey?"""
import math
import sys

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = (r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
       r"\_build\_render_ring\s01.png")
SW, SH = 13.3333, 7.5
CX, CY = 6.6667, 4.15
im = Image.open(SRC).convert("RGB")
W, H = im.size

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


def scan(rr):
    seq = []
    for deg in range(360):
        rad = math.radians(deg)
        c = at(CX + rr * math.cos(rad), CY + rr * math.sin(rad))
        seq.append("R" if near(c, RED) else
                   "A" if near(c, AMBER) else
                   "G" if near(c, GREY) else ".")
    return seq


for rr in (1.33, 1.40, 1.47):
    seq = scan(rr)
    print("== r = %.2f in ==" % rr)
    cur = seq[0]
    start = 0
    spans = []
    for i in range(1, 360):
        if seq[i] != cur:
            spans.append((cur, start, i - 1))
            cur, start = seq[i], i
    spans.append((cur, start, 359))
    # merge the wrap-around
    if len(spans) > 1 and spans[0][0] == spans[-1][0]:
        c, s, _ = spans.pop()
        spans[0] = (c, s - 360, spans[0][2])
    for c, a, b in spans:
        if b - a + 1 >= 3:
            print("   %s  %4d -> %4d   (%d deg)" % (c, a, b, b - a + 1))
    print()
