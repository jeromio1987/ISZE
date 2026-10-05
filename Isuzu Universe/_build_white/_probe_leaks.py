# -*- coding: utf-8 -*-
"""Find the leaked markdown on the finished PDF's pages, and show the running-header text."""
import re
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")
P = (r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe"
     r"\ISUZU_UNIVERSE_WHITE_PAPER_2026-09-23.pdf")
d = fitz.open(P)
print("pages:", d.page_count)
for n in (33, 60):
    t = d[n - 1].get_text()
    print("\n=== page", n, "===")
    for ln in t.split("\n"):
        if "**" in ln:
            print("   LEAK:", repr(ln[:220]))
print("\n=== running header, page 5, first 3 lines ===")
print("\n".join(d[4].get_text().split("\n")[:3]))
print("\n=== running header, page 40, first 3 lines ===")
print("\n".join(d[39].get_text().split("\n")[:3]))
d.close()
