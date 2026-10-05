# -*- coding: utf-8 -*-
r"""Page-fill and block-position report for the index, so a short page can be seen rather than guessed."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_build_30"))

import fitz
import layoutqa

PDF = os.path.join(os.path.dirname(HERE), "UNIVERSE_FOLDER_INDEX_2026-09-23.pdf")
d = fitz.open(PDF)
print("pages", d.page_count)
for i, p in enumerate(d):
    fills = layoutqa.column_share(p)
    blocks = layoutqa._blocks(p)
    last = blocks[-1]["y1"] if blocks else 0
    first = blocks[0]["y0"] if blocks else 0
    print("p%02d fill=%.2f  first_block_y=%.0f  last_block_y=%.0f  blocks=%d"
          % (i + 1, fills, first, last, len(blocks)))
    if i + 1 in (3, 4, 5):
        for b in blocks[-4:]:
            print("      y0=%.0f y1=%.0f  %s" % (b["y0"], b["y1"], b["text"][:70].replace("\n", " | ")))
d.close()
