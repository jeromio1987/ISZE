# -*- coding: utf-8 -*-
r"""Layout QA for the Universe papers: find the defects Jerome named.

The five faults:
  A  chapter heading stranded at the foot of a page
  B  figure separated from its caption
  C  table split from the sentence that introduces it
  D  a page that is mostly whitespace after a figure
  E  a chapter that could start on a fresh page and does not

Run from the Isuzu Universe folder:
  python _build_30\layout_check.py [_build_30\_staged_baseline.pdf]
"""
import os
import re
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DEFAULT = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_2026-09-23.pdf")

# geometry of the printed page, mirrors docbuild.CSS
PAGE_W, PAGE_H = 595.28, 841.89
M_TOP, M_BOT, M_LEFT, M_RIGHT = 19 / 25.4 * 72, 16 / 25.4 * 72, 15 / 25.4 * 72, 15 / 25.4 * 72
CONTENT_TOP = 40.0           # below the running header rule
CONTENT_BOT = PAGE_H - 44.0  # above the footer
HEAD_BAND = 0.80             # a heading below this fraction of the text column is at the foot

H_RE = re.compile(r"^(?:ISUZU / UNIVERSE[^a-z]*)$")


def text_blocks(page):
    """Text blocks inside the content band, top to bottom."""
    out = []
    for b in page.get_text("blocks"):
        x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], b[4]
        if y1 < CONTENT_TOP or y0 > CONTENT_BOT:
            continue
        if not txt.strip():
            continue
        out.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "text": txt.strip()})
    return sorted(out, key=lambda b: b["y0"])


def heading_lines(page):
    """Lines set in the heading face (Georgia) - the renderer's own markers."""
    found = []
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                if "Georgia" in sp["font"] or "Times" in sp["font"]:
                    if sp["text"].strip():
                        found.append({
                            "y0": line["bbox"][1], "y1": line["bbox"][3],
                            "size": round(sp["size"], 1), "text": sp["text"].strip(),
                            "x0": line["bbox"][0],
                        })
    return found


def image_blocks(page, page_no):
    out = []
    for info in page.get_image_info():
        bb = info["bbox"]
        if bb[3] < CONTENT_TOP or bb[1] > CONTENT_BOT:
            continue
        out.append({"x0": bb[0], "y0": bb[1], "x1": bb[2], "y1": bb[3]})
    return out


def last_content_y(page):
    blocks = text_blocks(page)
    return max((b["y1"] for b in blocks), default=CONTENT_TOP)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    d = fitz.open(path)
    n = d.page_count
    print("=" * 78)
    print(f"LAYOUT CHECK  {os.path.basename(path)}  ({n} pages)")
    print("=" * 78)

    # ---- A: heading stranded at the foot of a page -------------------------
    print()
    print("A  HEADING AT THE FOOT OF A PAGE")
    print("   (a heading in the bottom fifth of a page, with less than 3 lines of")
    print("    body text after it on that same page)")
    stranded = []
    for i, page in enumerate(d):
        heads = [h for h in heading_lines(page) if h["size"] >= 11.0]
        heads = [h for h in heads if h["y0"] < CONTENT_BOT]
        if not heads:
            continue
        blocks = text_blocks(page)
        lowest = max(h["y1"] for h in heads)
        after = [b for b in blocks if b["y0"] > lowest + 2]
        lines_after = sum(len(b["text"].split("\n")) for b in after)
        col_h = CONTENT_BOT - CONTENT_TOP
        pos = (lowest - CONTENT_TOP) / col_h
        if pos > HEAD_BAND and lines_after < 3:
            stranded.append((i + 1, heads[-1]["text"], round(pos, 2), lines_after))
    if stranded:
        for pg, txt, pos, la in stranded:
            print(f"   page {pg:>3}  at {pos:.0%} of the column, {la} line(s) after  "
                  f"-> {txt[:60]!r}")
    else:
        print("   none")

    # ---- B: figure separated from its caption -----------------------------
    print()
    print("B  FIGURE SEPARATED FROM ITS CAPTION")
    seps = []
    for i, page in enumerate(d):
        imgs = image_blocks(page, i + 1)
        if not imgs:
            continue
        cap = [b for b in text_blocks(page)
               if re.match(r"^Figure \d+\.", b["text"])]
        low = max(im["y1"] for im in imgs)
        if not cap:
            seps.append((i + 1, "figure with no caption on the same page", round(low, 1)))
            continue
        top = min(c["y0"] for c in cap)
        if top - low > 60:
            seps.append((i + 1, "caption far below the figure", round(top - low, 1)))
        if top < min(im["y0"] for im in imgs):
            seps.append((i + 1, "caption above the figure", 0.0))
    if seps:
        for pg, why, gap in seps:
            print(f"   page {pg:>3}  {why}  (gap {gap} pt)")
    else:
        print("   none")

    # ---- C: table split from the sentence that introduces it ---------------
    print()
    print("C  TABLE SPLIT FROM ITS INTRODUCING SENTENCE")
    splits = []
    for i, page in enumerate(d):
        # a table row is a text block whose lines all start with a rule-like cell pattern
        blocks = text_blocks(page)
        tops = [b for b in blocks if len(b["text"].split("\n")) >= 2
                and sum(1 for l in b["text"].split("\n") if len(l) < 40) >= 2]
        if not tops:
            continue
        first = tops[0]
        above = [b for b in blocks if b["y1"] <= first["y0"] + 1]
        if not above:
            # the table starts the page: check whether the previous page ended mid-flow
            if i > 0:
                prev = text_blocks(d[i - 1])
                if prev and last_content_y(d[i - 1]) > CONTENT_BOT - 90:
                    tail = prev[-1]["text"].replace("\n", " ")[-70:]
                    splits.append((i + 1, "table starts the page, previous page ends mid-flow",
                                   tail))
    if splits:
        for pg, why, tail in splits:
            print(f"   page {pg:>3}  {why}")
            print(f"            previous page ended: ...{tail}")
    else:
        print("   none")

    # ---- D: page mostly whitespace after a figure --------------------------
    print()
    print("D  PAGE MOSTLY WHITESPACE")
    blanks = []
    for i, page in enumerate(d):
        if i == 0:
            continue
        low = last_content_y(page)
        tail = CONTENT_BOT - low
        col_h = CONTENT_BOT - CONTENT_TOP
        if tail > col_h * 0.42:
            has_img = bool(image_blocks(page, i + 1))
            blanks.append((i + 1, round(tail), round(tail / col_h * 100), has_img,
                           low, len(page.get_text().split())))
    if blanks:
        for pg, tail, pct, img, low, words in blanks:
            print(f"   page {pg:>3}  {tail} pt of empty column ({pct}% of the text area), "
                  f"content ends at y={low:.0f}, {words} words"
                  f"{', carries a figure' if img else ''}")
    else:
        print("   none")

    # ---- E: chapter start ---------------------------------------------------
    print()
    print("E  WHERE EACH CHAPTER STARTS")
    starts = []
    for i, page in enumerate(d):
        for h in heading_lines(page):
            if h["size"] >= 14.5 and h["x0"] < 120:
                starts.append((h["text"], i + 1, round(h["y0"], 1)))
    for txt, pg, y in starts:
        prev = d[pg - 2].get_text().strip().split("\n") if pg > 1 else [""]
        prevlow = last_content_y(d[pg - 2]) if pg > 1 else 0
        note = ""
        if pg > 1:
            note = (f"  (previous page filled to y={prevlow:.0f} of {CONTENT_BOT:.0f})")
            if prevlow < CONTENT_BOT - 150:
                note += "  <- could have started higher"
        print(f"   page {pg:>3}  y={y:>6}  {txt[:56]}{note}")

    d.close()
    print()


if __name__ == "__main__":
    main()
