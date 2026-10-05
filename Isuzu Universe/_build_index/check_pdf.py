# -*- coding: utf-8 -*-
r"""Final facts for the verification record: bookmarks, metadata, page geometry."""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(os.path.dirname(HERE), "UNIVERSE_FOLDER_INDEX_2026-09-23.pdf")

import fitz

d = fitz.open(PDF)
print("pages   :", d.page_count)
print("size    : %.1f x %.1f pt (A4 = 595.3 x 841.9)" % (d[0].rect.width, d[0].rect.height))
print("metadata:", {k: v for k, v in d.metadata.items() if v and k in ("title", "author", "creator")})
print("bytes   :", os.path.getsize(PDF))
print("bookmarks:")
for lvl, title, page in d.get_toc():
    print("   %s%s -> p%d" % ("  " * (lvl - 1), title, page))
print()
print("first line of each page:")
for i, p in enumerate(d):
    lines = [l for l in p.get_text().split("\n") if l.strip()]
    print("   p%d  %s" % (i + 1, (lines[1] if len(lines) > 1 else lines[0])[:78] if lines else ""))
d.close()
