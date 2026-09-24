# -*- coding: utf-8 -*-
r"""Layout QA for the Universe papers, shared by the builder and the standalone checker.

The faults this measures, all on the rendered PDF rather than the source:

  A  a heading stranded at the foot of a page, with nothing under it
  B  a figure parted from its caption (caption on another page, or far below)
  C  a table split from the sentence that introduces it
  D  a figure page that then leaves most of the column empty
  E  a chapter that could have opened at the top of a fresh page and did not

Run standalone:
  python _build_30\layout_check.py [_build_30\_staged.pdf]
"""
import os
import re
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")

# geometry of the printed A4 page; mirrors docbuild.CSS margin 19mm 15mm 16mm 15mm
PAGE_W, PAGE_H = 595.28, 841.89
CONTENT_TOP = 40.0            # below the running-header rule at y=35
CONTENT_BOT = PAGE_H - 44.0   # above the footer at PAGE_H - 25
HEAD_BAND = 0.78              # a heading below this share of the text column is "at the foot"
COL_H = CONTENT_BOT - CONTENT_TOP
# A chapter heading that lands below this share of the column has no room for its own opening
# paragraph, so it reads as squeezed against the foot of the page. The builder breaks such
# chapters onto a fresh page and the checker reports the ones it deliberately left in place.
CHAPTER_LOW = 0.42

FIGURE_RE = re.compile(r"^Figure \d+\.")
PAIR_RE = FIGURE_RE


def _blocks(page):
    out = []
    for b in page.get_text("blocks"):
        x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], b[4]
        if y1 < CONTENT_TOP or y0 > CONTENT_BOT or not txt.strip():
            continue
        out.append({"y0": y0, "y1": y1, "x0": x0, "x1": x1, "text": txt.strip()})
    return sorted(out, key=lambda b: b["y0"])


def _heads(page, min_size=11.0):
    found = []
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line["spans"]:
                face = ("Georgia" in sp["font"] or "Times" in sp["font"]
                        or "Arial" in sp["font"] or "Helvetica" in sp["font"])
                if face and sp["text"].strip() and sp["size"] >= min_size:
                    found.append({"y1": line["bbox"][3], "size": round(sp["size"], 1),
                                  "text": sp["text"].strip(), "x0": line["bbox"][0]})
    return found


def _images(page):
    return [i["bbox"] for i in page.get_image_info()
            if CONTENT_TOP < i["bbox"][1] < CONTENT_BOT]

def _pair_captions(page):
    """Pair every caption with the nearest figure above it; return (paired, unpaired_caps)."""
    imgs = [b for b in _images(page) if b[3] < CONTENT_BOT]
    caps = [c for c in _blocks(page) if PAIR_RE.match(c["text"])]
    pairs, orphan_caps = [], []
    for c in caps:
        above = [im for im in imgs if im[3] <= c["y0"] + 4]
        if not above:
            orphan_caps.append(c)
            continue
        nearest = max(above, key=lambda im: im[3])
        pairs.append((nearest, c))
    used = {id(p[0]) for p in pairs}
    return pairs, [im for im in imgs if id(im) not in used], orphan_caps


def figure_caption_faults(doc):
    """Captions that are not on the same page as, and just under, their figure."""
    faults = []
    for i, page in enumerate(doc):
        if i == 0:                      # the cover carries a figure without a numbered caption
            continue
        pairs, unpaired, orphan = _pair_captions(page)
        for im, c in pairs:
            gap = c["y0"] - im[3]
            if gap > 60:
                faults.append({"page": i + 1,
                               "why": f"caption {round(gap)} pt below its figure"})
        for im in unpaired:
            if im[3] - im[1] > 40:      # a real figure, not a rule
                faults.append({"page": i + 1, "why": "figure with no caption under it"})
        if orphan:
            faults.append({"page": i + 1, "why": "caption with no figure above it"})
    return faults


def table_split_faults(doc, md_path):
    """A table whose introducing sentence sits on a different page from the table itself.

    Read from the source markdown, so the pairing is exact. A table is located in the PDF by its
    own header row, which cannot occur in running prose; the introducing sentence by its last 60
    characters.
    """
    src = open(md_path, encoding="utf-8").read()
    lines = src.split("\n")
    items = []
    for k, ln in enumerate(lines):
        if not ln.lstrip().startswith("|"):
            continue
        if k and lines[k - 1].lstrip().startswith("|"):
            continue                    # not the table's header row
        j = k - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        intro_tail = ""
        if j >= 0 and not lines[j].lstrip().startswith(("|", "#", "[")):
            intro_tail = " ".join(lines[j].split())[-60:]
        cells = [c.strip().replace("**", "") for c in ln.strip().strip("|").split("|")]
        head = " ".join(cells[:2]).replace("|", " ")
        if intro_tail and len(head) > 6:
            items.append((intro_tail, head))

    pages_flat = [" ".join(p.get_text().split()).replace("**", "") for p in doc]
    faults = []
    for intro_tail, head in items:
        intro_pg = next((i + 1 for i, t in enumerate(pages_flat) if intro_tail in t), None)
        table_pg = next((i + 1 for i, t in enumerate(pages_flat) if head in t), None)
        if intro_pg and table_pg and intro_pg != table_pg:
            faults.append({"page": table_pg, "intro_page": intro_pg,
                           "table_starts": head,
                           "introducing_sentence": "..." + intro_tail})
    return faults


def content_end(page):
    bl = _blocks(page)
    return max((b["y1"] for b in bl), default=CONTENT_TOP)


def column_share(page):
    return (content_end(page) - CONTENT_TOP) / (CONTENT_BOT - CONTENT_TOP)


def page_fills(doc):
    """How full each page is, 0..1, measured on the text column."""
    return [column_share(p) for p in doc]


def analyse(doc, md_path=None, fresh_page_share=0.42, figure_tail=0.42, plain_tail=0.58):
    """Return the five fault lists plus the per-page fill, for the rendered document."""
    col_h = CONTENT_BOT - CONTENT_TOP
    stranded, cap_splits, table_splits, figure_tails, early_ends = [], [], [], [], []
    fills = []

    for i, page in enumerate(doc):
        fills.append(round(column_share(page), 3))
        if i == 0:
            continue
        bl = _blocks(page)
        heads = _heads(page)
        if heads:
            lowest = max(h["y1"] for h in heads)
            after = [b for b in bl if b["y0"] > lowest + 2]
            lines_after = sum(len(b["text"].split("\n")) for b in after)
            pos = (lowest - CONTENT_TOP) / col_h
            if pos > HEAD_BAND and bl:
                # stranded when nothing follows the heading at all, or when the only thing
                # under it is a first line that runs on to the next page
                tail = after[-1]["text"].strip() if after else ""
                cut_off = bool(tail) and not re.search(r"[.!?:;\"')\]]$", tail)
                first_lines = len(after[0]["text"].split("\n")) if after else 0
                if not after or (cut_off and lines_after < 3):
                    label = [h for h in heads if h["y1"] == lowest][0]["text"]
                    stranded.append({"page": i + 1, "heading": label,
                                     "at": round(pos, 2), "lines_after": lines_after,
                                     "reason": "nothing under it" if not after
                                               else "paragraph cut off at the page foot"})
        if not bl:
            # A page with no text block at all in the print area carries only the running header
            # and footer. That is a blank sheet in the middle of the document, not a chapter end:
            # a chapter end still has its chapter's closing text on it. Report it under the
            # early-ends list with zero fill so it cannot pass unnoticed.
            fills.append(0.0)
            early_ends.append({"page": i + 1, "empty_pt": round(col_h), "pct": 100,
                               "words": len(page.get_text().split()), "blank": True})
            continue

        imgs = _images(page)
        pairs, unpaired, orphan = _pair_captions(page)
        for im, c in pairs:
            gap = c["y0"] - im[3]
            if gap > 60:
                cap_splits.append({"page": i + 1,
                                   "why": f"caption {round(gap)} pt below its figure"})
        for im in unpaired:
            if im[3] - im[1] > 40:
                cap_splits.append({"page": i + 1, "why": "figure with no caption under it"})
        for c in orphan:
            cap_splits.append({"page": i + 1, "why": "caption with no figure above it"})

        end = content_end(page)
        tail = CONTENT_BOT - end
        share = tail / col_h
        if share > figure_tail and imgs:
            figure_tails.append({"page": i + 1, "empty_pt": round(tail),
                                 "pct": round(share * 100), "words": len(page.get_text().split())})
        elif share > plain_tail:
            early_ends.append({"page": i + 1, "empty_pt": round(tail),
                               "pct": round(share * 100), "words": len(page.get_text().split())})

        fresh_page = []
        for i, page in enumerate(doc):
            for h in _heads(page, min_size=14.5):
                if h["x0"] >= 120 or i == 0:
                    continue
                prev_fill = fills[i - 1] if i - 1 < len(fills) else 0
                starts_low = (h["y1"] - CONTENT_TOP) / COL_H > CHAPTER_LOW
                if starts_low and prev_fill > fresh_page_share:
                    fresh_page.append({"page": i + 1, "heading": h["text"][:60],
                                       "starts_at_pt": round(h["y1"]),
                                       "previous_page_fill": prev_fill})
                break

    return {
        "fills": fills,
        "stranded_headings": stranded,
        "figure_caption_splits": cap_splits,
        "table_splits": table_split_faults(doc, md_path) if md_path else [],
        "figure_tails": figure_tails,
        "early_ends": early_ends,
        "chapters_that_could_open_fresh": fresh_page,
    }


def chapter_breaks(doc):
    """Which level-2 headings should start a fresh page.

    A chapter may not begin in the lower part of a page: below CHAPTER_LOW of the text column
    there is no room for its own opening paragraph, so the heading and its first lines are torn
    apart. The check is a pure function of the pagination it is given, so the builder can apply
    the answer and re-ask until the pagination stops moving.
    """
    fills = page_fills(doc)
    wanted, seen = [], set()
    for i, page in enumerate(doc):
        if i == 0:
            continue
        prev_fill = fills[i - 1] if i > 0 else 0
        for h in _heads(page, min_size=14.5):
            if h["x0"] >= 120 or h["text"] in seen:
                continue
            seen.add(h["text"])
            if (h["y1"] - CONTENT_TOP) / COL_H > CHAPTER_LOW and prev_fill > 0.42:
                wanted.append(h["text"])
    return wanted


def report(path, md_path=None):
    d = fitz.open(path)
    res = analyse(d, md_path=md_path)
    n = d.page_count
    d.close()
    print("=" * 78)
    print(f"LAYOUT CHECK  {os.path.basename(path)}  ({n} pages)")
    print("=" * 78)
    print()
    print("PAGE FILL (share of the text column used, page 1 = cover, excluded)")
    line = "  "
    for i, f in enumerate(res["fills"], start=1):
        line += f"{i}:{int(f * 100):>3}%  "
        if i % 8 == 0:
            print(line)
            line = "  "
    if line.strip():
        print(line)

    print()
    print("A  HEADING AT THE FOOT OF A PAGE")
    if res["stranded_headings"]:
        for h in res["stranded_headings"]:
            print(f"   page {h['page']:>3}  at {h['at']:.0%} of the column, "
                  f"{h['lines_after']} line(s) under it ({h['reason']})  -> {h['heading'][:52]!r}")
    else:
        print("   none")

    print()
    print("B  FIGURE PARTED FROM ITS CAPTION")
    if res["figure_caption_splits"]:
        for h in res["figure_caption_splits"]:
            print(f"   page {h['page']:>3}  {h['why']}")
    else:
        print("   none")

    print()
    print("C  TABLE SPLIT FROM THE SENTENCE THAT INTRODUCES IT")
    if res["table_splits"]:
        for h in res["table_splits"]:
            print(f"   table on page {h['page']}, introducing sentence on page "
                  f"{h['intro_page']}")
            print(f"            {h['introducing_sentence']}")
    else:
        print("   none")

    print()
    print("D  FIGURE PAGE WITH MOST OF THE COLUMN LEFT EMPTY")
    if res["figure_tails"]:
        for h in res["figure_tails"]:
            print(f"   page {h['page']:>3}  {h['pct']}% of the column empty "
                  f"({h['words']} words on the page)")
    else:
        print("   none")
    print()
    print("D2 PAGES THAT END EARLY (informational: usually a chapter ending)")
    if res["early_ends"]:
        print("   " + ", ".join(f"p{h['page']} ({h['pct']}%)" for h in res["early_ends"]))
    else:
        print("   none")

    print()
    print("E  A CHAPTER THAT COULD OPEN A FRESH PAGE AND DOES NOT")
    if res["chapters_that_could_open_fresh"]:
        for h in res["chapters_that_could_open_fresh"]:
            print(f"   page {h['page']:>3}  starts at y={h['starts_at_pt']}, previous page "
                  f"{h['previous_page_fill']:.0%} full  -> {h['heading']}")
    else:
        print("   none")
    print()


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(HERE)
    default = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_2026-09-23.pdf")
    md_default = os.path.join(ROOT, "01_Strategy", "ISUZU_UNIVERSE_3_0_2026-09-23.md")
    target = sys.argv[1] if len(sys.argv) > 1 else default
    md = sys.argv[2] if len(sys.argv) > 2 else (md_default if os.path.exists(md_default) else None)
    report(target, md_path=md)
