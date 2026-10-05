# -*- coding: utf-8 -*-
r"""Sixth pass: an axis-based chart detector, so the chart count is measured not eyeballed.

A page carries a chart when its words form a numeric y-axis (several numeric labels sharing a
left-edge x position) and a numeric x-axis (several numeric labels sharing a bottom-edge y
position). Tables fail this because their numbers sit in columns at different y positions.

Run from the Isuzu Universe folder:  python _build_30\_check_critique_facts6.py
"""
import os
import re
import sys
from collections import Counter

import fitz

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PDFS = {
    "80-pager": os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pdf"),
    "33-pager": os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_TOOLS_WHITE_PAPER.pdf"),
    "25-pager": os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_2026-09-23.pdf"),
}

NUMWORD = re.compile(r"^[+-]?\d[\d.,]*\s*(?:k|K|%)?$")


def chart_score(page):
    """Return (y_axis_labels, x_axis_labels) for one page."""
    r = page.rect
    words = page.get_text("words")  # x0,y0,x1,y1,word
    nums = [w for w in words if NUMWORD.match(w[4].strip())]
    # y-axis candidates: numeric words in the left 16% of the width
    left = [w for w in nums if w[0] < r.x0 + r.width * 0.16]
    bot = [w for w in nums if w[3] > r.y1 - r.height * 0.14]
    yx = Counter(round(w[0]) for w in left)
    xy = Counter(round(w[1]) for w in bot)
    y_axis = max(yx.values()) if yx else 0
    x_axis = max(xy.values()) if xy else 0
    return y_axis, x_axis


def main():
    print("=" * 78)
    print("CHART DETECTOR: a page needs 3+ numeric labels on a shared left edge AND")
    print("3+ numeric labels on a shared bottom edge.")
    print("=" * 78)
    for label, path in PDFS.items():
        if not os.path.exists(path):
            print(f"  {label}: missing")
            continue
        d = fitz.open(path)
        hits = []
        for i, p in enumerate(d):
            y, x = chart_score(p)
            if y >= 3 and x >= 3:
                hits.append((i + 1, y, x))
        print(f"  {label} ({d.page_count} pages): chart pages "
              + (", ".join(f"p{n}(y{a}/x{b})" for n, a, b in hits) if hits else "none"))
        print(f"      count = {len(hits)}")
        d.close()


if __name__ == "__main__":
    main()
