# -*- coding: utf-8 -*-
r"""Full-resolution page images for the index, for reading at the size it prints.

The colour and contrast verdict comes from `check_charcoal.py`, which samples the painted pixels.
This script only produces the images and reports page geometry, so there is one place that decides
whether the document is charcoal and one place that produces what gets read.

Writes into _build_index\_qa_read\ and leaves the builder's own _qa folder alone.
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(HERE), "UNIVERSE_FOLDER_INDEX_2026-09-23.pdf")
OUT = os.path.join(HERE, "_qa_read")
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

import fitz

d = fitz.open(PDF)
print("file :", PDF)
print("pages:", d.page_count)
print("size : %.1f x %.1f pt" % (d[0].rect.width, d[0].rect.height))
print()
for i, page in enumerate(d):
    pix = page.get_pixmap(dpi=150)
    name = "page%02d.png" % (i + 1)
    pix.save(os.path.join(OUT, name))
    print("wrote %-12s %dx%d" % (name, pix.width, pix.height))
print()
print("text column occupancy of each page (share of the printed column used):")
for i, page in enumerate(d):
    blocks = [b for b in page.get_text("blocks") if b[4].strip()]
    top, bot = 40.0, page.rect.height - 44.0
    y1 = max((b[3] for b in blocks), default=top)
    print("  p%d  %.2f" % (i + 1, (y1 - top) / (bot - top)))
d.close()
print()
print("images written to", OUT)
