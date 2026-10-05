# -*- coding: utf-8 -*-
r"""Seventh pass: a geometric chart detector.

A chart has axes: a long ruled line and clusters of numeric labels beside them. This looks for
  * a near-horizontal line at least 120 pt long, or a near-vertical line at least 80 pt long,
  * at least three numeric text labels whose left edges line up (a value axis), or whose
    baselines line up (a category axis),
all inside the content area (header and footer bands excluded).

Run from the Isuzu Universe folder:  python _build_30\_check_critique_facts7.py
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

NUM = re.compile(r"^[+-]?\d[\d.,]*\s*(?:k|K|%)?$")


def inside(p):
    """True when the point is inside the content band, excluding header and footer rules."""
    return 46 < p.y < 756


def axes(page):
    long_h = long_v = 0
    for d in page.get_drawings():
        for item in d["items"]:
            if item[0] == "l":
                a, b = item[1], item[2]
                if abs(a.y - b.y) < 1.2 and abs(a.x - b.x) >= 120 and inside(a):
                    long_h += 1
                if abs(a.x - b.x) < 1.2 and abs(a.y - b.y) >= 80 and inside(a):
                    long_v += 1
            elif item[0] == "re":
                r = item[1]
                if r.width >= 120 and r.height <= 12 and inside(r.tl):
                    long_h += 1
    return long_h, long_v


def label_clusters(page):
    words = [w for w in page.get_text("words") if inside(fitz.Point(w[0], w[1]))]
    nums = [w for w in words if NUM.match(w[4].strip())]
    col = Counter(round(w[0] / 2) for w in nums)
    row = Counter(round(w[3] / 2) for w in nums)
    return (max(col.values()) if col else 0), (max(row.values()) if row else 0)


def main():
    print("=" * 78)
    print("CHART DETECTOR v2 - ruled axis + aligned numeric labels, content band only")
    print("=" * 78)
    for label, path in PDFS.items():
        if not os.path.exists(path):
            print(f"  {label}: missing")
            continue
        d = fitz.open(path)
        hits = []
        for i, p in enumerate(d):
            h, v = axes(p)
            c, r = label_clusters(p)
            chartlike = (h >= 1 or v >= 1) and (c >= 3 or r >= 3)
            if chartlike:
                hits.append((i + 1, h, v, c, r))
        print(f"  --- {label}: {d.page_count} pages ---")
        for n, h, v, c, r in hits:
            print(f"      page {n:>3}   h-lines {h:>2}  v-lines {v:>2}  "
                  f"aligned-x {c:>2}  aligned-y {r:>2}")
        print(f"      chart pages: {len(hits)}")
        d.close()
        print()


if __name__ == "__main__":
    main()
