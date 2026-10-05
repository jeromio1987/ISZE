# -*- coding: utf-8 -*-
"""Read-only: is the white paper charcoal throughout, and what background colour?"""
import os
import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "ISUZU_UNIVERSE_WHITE_PAPER_2026-09-23.pdf")
d = fitz.open(P)
print("pages", d.page_count)
for i in [0, 1, 5, 20, 40, 63]:
    if i >= d.page_count:
        continue
    pix = d[i].get_pixmap(dpi=40)
    # sample a corner pixel and a mid-right pixel, both likely background
    w, h = pix.width, pix.height
    corner = pix.pixel(w - 3, h - 3)
    print("page %2d  corner=%s" % (i + 1, corner))
d.close()

Y = os.path.join(ROOT, "Universe_Yellow_Paper_v0.5_2026-09-22.pdf")
d = fitz.open(Y)
pix = d[0].get_pixmap(dpi=40)
print("yellow p1 corner", pix.pixel(pix.width - 3, pix.height - 3))
d.close()
