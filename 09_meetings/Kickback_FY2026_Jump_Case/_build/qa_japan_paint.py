# -*- coding: utf-8 -*-
"""Objective paint check on the rendered PNGs:
 - any ink inside a 6 px edge margin (=> possible clipping / off-slide)
 - distinct colours present (panel/red/ink really painted)
 - coverage share of non-background pixels per slide
"""
import os, sys
from PIL import Image

D = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\_qa_japan"
BG = (0x26, 0x26, 0x26)
fails = []
for i in range(1, 10):
    p = os.path.join(D, "s%02d.png" % i)
    im = Image.open(p).convert("RGB")
    w, h = im.size
    px = im.load()
    m = 6
    edge_ink = 0
    for x in range(w):
        for y in list(range(0, m)) + list(range(h - m, h)):
            if px[x, y] != BG:
                edge_ink += 1
    for y in range(h):
        for x in list(range(0, m)) + list(range(w - m, w)):
            if px[x, y] != BG:
                edge_ink += 1
    cols = im.getcolors(maxcolors=1 << 24)
    nonbg = sum(c for c, v in cols if v != BG)
    share = nonbg / float(w * h)
    # a cover accent bar sits at x<10 deliberately on slide 1 and slide 3/8 use x=0.42in
    print("s%02d %dx%d edge_ink=%d nonbg_share=%.3f colours=%d" % (i, w, h, edge_ink, share, len(cols)))
    # slide 1 carries a deliberate full-bleed red accent bar at x=0 (house style)
    if edge_ink > 0 and i != 1:
        fails.append("slide %d: %d ink pixels inside the %dpx edge margin" % (i, edge_ink, m))
    if share < 0.02:
        fails.append("slide %d: only %.1f%% of the page is painted" % (i, share * 100))
print("paint fails:", len(fails))
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
