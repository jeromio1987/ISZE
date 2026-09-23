# -*- coding: utf-8 -*-
r"""Extract the 80-pager's actual colour palette and type sizes, so the critique pack can match.

Run from the Isuzu Universe folder:  python _build_30\_extract_80pager_style.py
"""
import os
import sys
from collections import Counter

import fitz

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V80 = os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pdf")

# the documented palette, for comparison
DOC = {
    "page bg": "#24282C", "deeper": "#1C2024", "panel": "#30363B",
    "isuzu red": "#D71920", "light red": "#FF686D",
    "ink": "#F6F7F7", "muted": "#C2C8CC", "faint": "#A3ADB3", "hairline": "#535B61",
}


def hx(c):
    """Accept a fitz fill tuple (0-1 floats) or a text-span colour int."""
    if c is None:
        return "none"
    if isinstance(c, int):
        return "#%06X" % c
    return "#%02X%02X%02X" % tuple(round(x * 255) for x in c[:3])


def main():
    d = fitz.open(V80)
    fills = Counter()
    strokes = Counter()
    for p in d:
        for dr in p.get_drawings():
            if dr.get("fill"):
                fills[hx(dr["fill"])] += 1
            if dr.get("color"):
                strokes[hx(dr["color"])] += 1
    print("=" * 78)
    print("DOCUMENTED PALETTE (from the brief)")
    print("=" * 78)
    for k, v in DOC.items():
        print(f"  {k:<12}{v}")

    print()
    print("=" * 78)
    print("FILL COLOURS ACTUALLY USED IN THE 80-PAGER, most common first")
    print("=" * 78)
    for c, n in fills.most_common(18):
        print(f"  {c}  x{n}")

    print()
    print("=" * 78)
    print("STROKE COLOURS")
    print("=" * 78)
    for c, n in strokes.most_common(12):
        print(f"  {c}  x{n}")

    print()
    print("=" * 78)
    print("TEXT COLOURS AND SIZES ON PAGE 2")
    print("=" * 78)
    for blk in d[1].get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                txt = sp["text"].strip()
                if txt:
                    print(f"  {hx(sp['color'])}  {sp['size']:5.1f}pt  {sp['font']:<14} {txt[:60]!r}")

    print()
    print("=" * 78)
    print("COLOURS AND SIZES ON THE COVER (page 1)")
    print("=" * 78)
    for blk in d[0].get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                txt = sp["text"].strip()
                if txt:
                    print(f"  {hx(sp['color'])}  {sp['size']:5.1f}pt  {sp['font']:<14} {txt[:60]!r}")

    print()
    print("=" * 78)
    print("FONTS EMBEDDED")
    print("=" * 78)
    seen = set()
    for p in d:
        for f in p.get_fonts(full=True):
            key = (f[3], f[4])
            if key not in seen:
                seen.add(key)
                print(f"  {f[3]:<28}{f[4]}")


if __name__ == "__main__":
    main()
