# -*- coding: utf-8 -*-
"""Read-only: dominant page colour, so the index can state the white paper's field honestly."""
import os
from collections import Counter

import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dominant(path, pages):
    d = fitz.open(path)
    print(os.path.basename(path), "pages =", d.page_count)
    for i in pages:
        if i >= d.page_count:
            continue
        pix = d[i].get_pixmap(dpi=30)
        n = pix.n
        samp = pix.samples
        c = Counter()
        step = max(1, (pix.width * pix.height) // 4000)
        for k in range(0, pix.width * pix.height, step):
            off = k * n
            c[(samp[off], samp[off + 1], samp[off + 2])] += 1
        top = c.most_common(2)
        print("  page %2d  dominant=%s  second=%s" % (i + 1, top[0], top[1] if len(top) > 1 else None))
    d.close()


dominant(os.path.join(ROOT, "ISUZU_UNIVERSE_WHITE_PAPER_2026-09-23.pdf"), [0, 10, 30, 63])
dominant(os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_2026-09-23.pdf"), [0, 10, 28])
dominant(os.path.join(ROOT, "Universe_Yellow_Paper_v0.5_2026-09-22.pdf"), [0, 10, 22])
