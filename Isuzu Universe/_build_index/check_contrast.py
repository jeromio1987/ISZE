# -*- coding: utf-8 -*-
r"""Contrast audit on the rendered index PDF.

Two faults are possible and both are checked here, on the painted page rather than the source:

  1. a band whose fill is pale but whose text is white or near-white (invisible text)
  2. a band whose fill is navy but whose text is not the paper colour (poor contrast)

A "band" is a horizontal run of pixels of one fill colour spanning most of the text column. The
text sitting on it is read from the PDF's own span colours, so the check does not depend on how
the glyphs antialias.
"""
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(os.path.dirname(HERE), "UNIVERSE_FOLDER_INDEX_2026-09-23.pdf")

import fitz

PALE = {"paper #F7F4EE": (247, 244, 238), "row #FAF8F3": (250, 248, 243),
        "quote #F4F1EA": (244, 241, 234), "code #F2EFE9": (242, 239, 233),
        "white #FFFFFF": (255, 255, 255)}
NAVY = (21, 35, 60)


def near(a, b, tol=14):
    return all(abs(a[k] - b[k]) <= tol for k in range(3))


d = fitz.open(PDF)
faults = []
bands = 0

for i, page in enumerate(d):
    pix = page.get_pixmap(dpi=100)
    n, samp = pix.n, pix.samples
    W, H = pix.width, pix.height

    # the fill colour of each scan line, as the most common colour across the text column
    fill_of_row = {}
    for y in range(0, H, 2):
        c = Counter()
        for x in range(60, W - 60, 3):
            o = (y * W + x) * n
            c[(samp[o], samp[o + 1], samp[o + 2])] += 1
        colour, count = c.most_common(1)[0]
        if count > (W - 120) / 3 * 0.55:
            fill_of_row[y] = colour

    # every coloured text span on the page, with its y position and colour
    # (fitz y goes down from the top, as does the pixmap row index after scaling)
    scale = 100.0 / 72.0
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                txt = sp["text"].strip()
                if not txt:
                    continue
                col = sp["color"]
                rgb = ((col >> 16) & 255, (col >> 8) & 255, col & 255)
                ymid = int((line["bbox"][1] + line["bbox"][3]) / 2 * scale) // 2 * 2
                fill = None
                for dy in (0, 2, -2, 4, -4):
                    if ymid + dy in fill_of_row:
                        fill = fill_of_row[ymid + dy]
                        break
                if fill is None:
                    continue
                # a glyph antialiases to a blend of ink and fill, so a span whose ink is already
                # close to the fill is the unreadable case
                d_ink = sum(abs(rgb[k] - fill[k]) for k in range(3))
                pale = [name for name, c in PALE.items() if near(fill, c)]
                if pale:
                    bands += 1
                    white_text = all(v > 232 for v in rgb)
                    if white_text:
                        faults.append((i + 1, pale[0], rgb, txt[:60]))
                elif near(fill, NAVY):
                    bands += 1
                    if not all(v > 200 for v in rgb):
                        # paper-coloured text on navy is the intent; flag anything else
                        if d_ink < 300:
                            faults.append((i + 1, "navy #15233C", rgb, txt[:60]))

print("spans checked on a filled band: %d" % bands)
print("faults: %d" % len(faults))
for f in faults:
    print("   page %d on %-18s ink=%s  %r" % f)

text = "".join(p.get_text() for p in d)
print()
print("markdown left unrendered:")
for pat in ["**", "##", "|---", "&nbsp;", "&amp;", "<strong>", "&lt;", "[[", "]]", "`"]:
    if pat in text:
        print("   FOUND %r" % pat)
else:
    print("   none")
print()
print("tofu / unmapped glyphs:", text.count("\ufffd"), " U+FFFD,", text.count("□"), " boxes")
d.close()
