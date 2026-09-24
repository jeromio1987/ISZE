# -*- coding: utf-8 -*-
r"""Pixel check: is every page field charcoal, and is any text white on a pale panel?

Fails loudly (exit 1) rather than warning. Run on the finished PDF:

    python _build_index\check_charcoal.py [path-to.pdf]

The trap this guards against is the one that cost the white paper two attempts: a background set on
`body` or `@page` prints as white pages with a coloured block in the middle. So this samples the
painted pixels, including the page margins, not the CSS.
"""
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(HERE), "UNIVERSE_FOLDER_INDEX_2026-09-23.pdf")

# the palette the document is built from
CHARCOAL = (36, 40, 43)          # #24282C   page and section field
DEEPER = (28, 32, 36)            # #1C2024
PANEL = (53, 59, 62)             # #353B3E
PALE = {"#F2F4F7": (242, 244, 247), "#E4E9F0": (228, 233, 240),
        "#FFFFFF": (255, 255, 255)}
RED = (215, 25, 32)


def near(a, b, tol=8):
    return all(abs(a[k] - b[k]) <= tol for k in range(3))


def is_pale(c):
    return all(v >= 224 for v in c[:3])


d = fitz.open(PDF)
print("file :", PDF)
print("pages:", d.page_count)
print()

fail = []

# ---- 1. the page field, sampled across the whole sheet including the margins
print("== page field (whole sheet, margins included)")
for i, page in enumerate(d):
    pix = page.get_pixmap(dpi=64)
    n, s = pix.n, pix.samples
    c = Counter()
    step = max(1, (pix.width * pix.height) // 8000)
    for k in range(0, pix.width * pix.height, step):
        o = k * n
        c[(s[o], s[o + 1], s[o + 2])] += 1
    dom, dom_n = c.most_common(1)[0]
    share = dom_n / max(1, sum(c.values()))
    # the four corners and the four margin mid-points, which are outside the printed block
    probes = [(2, 2), (pix.width - 3, 2), (2, pix.height - 3), (pix.width - 3, pix.height - 3),
              (pix.width // 2, 2), (pix.width // 2, pix.height - 3),
              (2, pix.height // 2), (pix.width - 3, pix.height // 2)]
    corners = [pix.pixel(x, y)[:3] for x, y in probes]
    white_corners = [c2 for c2 in corners if is_pale(c2)]
    ok = near(dom, CHARCOAL, 10) and not white_corners
    print("  p%d  dominant=%s (%.0f%%)  margins=%s  %s"
          % (i + 1, dom, share * 100, corners[0], "OK" if ok else "FAIL"))
    if not ok:
        fail.append("page %d: field %s, margins %s" % (i + 1, dom, corners))

# ---- 2. text on a pale panel must be ink, never white
print()
print("== text sitting on a pale panel")
n_spans = 0
for i, page in enumerate(d):
    pix = page.get_pixmap(dpi=100)
    n, s = pix.n, pix.samples
    W, H = pix.width, pix.height
    scale = 100.0 / 72.0
    # the fill colour under each scan line, read from the painted pixels
    fill_of_row = {}
    for y in range(0, H, 2):
        c = Counter()
        for x in range(40, W - 40, 3):
            o = (y * W + x) * n
            c[(s[o], s[o + 1], s[o + 2])] += 1
        colour, count = c.most_common(1)[0]
        if count > max(1, (W - 80) / 3) * 0.5:
            fill_of_row[y] = colour
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                if not sp["text"].strip():
                    continue
                col = sp["color"]
                ink = ((col >> 16) & 255, (col >> 8) & 255, col & 255)
                ymid = int((line["bbox"][1] + line["bbox"][3]) / 2 * scale) // 2 * 2
                fill = None
                for dy in (0, 2, -2, 4, -4):
                    if ymid + dy in fill_of_row:
                        fill = fill_of_row[ymid + dy]
                        break
                if fill is None or not is_pale(fill):
                    continue
                n_spans += 1
                if all(v >= 224 for v in ink):
                    fail.append("page %d: white text on pale %s: %r"
                                % (i + 1, fill, sp["text"][:60]))
print("  %d spans found on a pale panel; %s"
      % (n_spans, "all ink" if not fail else "faults below"))

# ---- 3. low-contrast grey body text
print()
print("== body text colour")
greys = Counter()
for page in d:
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                if not sp["text"].strip() or sp["size"] < 9.4:
                    continue
                col = sp["color"]
                greys[((col >> 16) & 255, (col >> 8) & 255, col & 255)] += 1
for c2, cnt in greys.most_common(8):
    verdict = "OK"
    if not (all(v >= 200 for v in c2) or near(c2, RED, 40)):
        verdict = "LOW CONTRAST"
        fail.append("body text colour %s used %d times" % (c2, cnt))
    print("  %-18s %3d spans  %s" % (c2, cnt, verdict))

# ---- 4. text and glyph artefacts
print()
text = "".join(p.get_text() for p in d)
hits = [p2 for p2 in ["**", "##", "|---", "&nbsp;", "&amp;", "<strong>", "[[", "`"] if p2 in text]
print("== markdown left unrendered:", hits or "none")
if hits:
    fail.append("markdown artefacts %s" % hits)
tofu = text.count("\ufffd") + text.count("\u25a1")
print("== unmapped glyphs:", tofu)
if tofu:
    fail.append("%d unmapped glyphs" % tofu)

d.close()
print()
if fail:
    print("FAIL - %d problem(s):" % len(fail))
    for f in fail:
        print("   " + f)
    sys.exit(1)
print("PASS - every page is charcoal, no page is white, and no white text sits on a pale panel.")
