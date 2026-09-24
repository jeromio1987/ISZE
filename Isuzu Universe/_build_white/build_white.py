# -*- coding: utf-8 -*-
r"""Main build: the Isuzu Universe white paper (internal draft).

Regenerates every figure from source first, then renders the markdown to the charcoal PDF with a
two-pass contents, figure list and table list, then checks the printed page numbers against the
finished file's own text.

Run from the Isuzu Universe folder:  python _build_white\build_white.py
"""
import os
import re
import sys

import docbuild_white

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

MD = os.path.join(ROOT, "01_Strategy", "ISUZU_UNIVERSE_WHITE_PAPER_2026-09-23.md")
HTMLOUT = os.path.join(HERE, "ISUZU_UNIVERSE_WHITE_PAPER.html")
PDFOUT = os.environ.get(
    "WHITE_PDF_OUT",
    os.path.join(ROOT, "ISUZU_UNIVERSE_WHITE_PAPER_2026-09-23.pdf"))
QA = os.path.join(HERE, "_qa")
FIGDIR = os.path.join(HERE, "figures")
TITLE = "ISUZU / UNIVERSE - the white paper"

FOOTER = "Internal draft for the business owner  |  23 September 2026  |  page {i} of {n}"
COVER = {
    "org": "ISZE / Parts Europe",
    "family": "Internal draft",
    "title": "Isuzu<br>Universe",
    "strap": "Five pillars. Measured evidence, the questions it<br>answers, and the limits stated in full.",
    "focus_head": "What this paper settles",
    "focus": [
        "The Aftermarket Intelligence Model, Isuzu Dealer Standards, the analytics",
        "codebase, the competitive-quotation support programme and the tender",
        "feed — each with a worked example and its limit. The scope boundary,",
        "which keeps routine service out of the product. The hurdle a funding",
        "envelope implies, stated rather than forecast. The one decision that",
        "closes two pillars at once: record the outcome.",
    ],
    "meta": "23 September 2026",
    "meta2": "Internal · draft for the business owner",
}

CLOSING = """
<div class="closing">
  <b>ISUZU / UNIVERSE — the white paper.</b> 23 September 2026. Internal draft for the business owner;
  not for circulation. Supersedes the white paper of 21 September 2026 (58 pages), its visual edition
  (71 pages), the Commercial Vision 3.0 of 22 September 2026 (80 pages, withdrawn) and the Commercial
  Tools Edition of 22 September 2026 (33 pages, withdrawn) as a statement of the programme. Every
  earlier edition remains on disk for reference. All figures are regenerated from their named source
  files at build time by <b>_build_white\\figures_white.py</b>.
</div>
"""


def main():
    print("regenerating figures ...")
    import figures_white
    figures_white.build_all()
    caps = {n: (t, note) for n, t, _fn, note in figures_white.FIGURES}

    res = docbuild_white.build(MD, HTMLOUT, PDFOUT, QA, TITLE, COVER, FIGDIR, caps,
                               FOOTER, CLOSING)

    print()
    print("pages={pages}  (before the lists: {pages_before_lists})".format(**res))
    print("chars={chars:,}  bookmarks={bookmarks}".format(**res))
    c = res["checks"]
    print("thin pages (<60 chars):        {}".format(c["thin_pages"] or "none"))
    print("pages missing running header:  {}".format(c["missing_header"] or "none"))
    print("markdown artefacts left in:    {}".format(c["artefacts"] or "none"))
    print("blocks touching the page edge: {}".format(c["edge_bleed"] or "none"))

    # ---- verify the printed index against the finished file's own text
    import fitz
    doc = fitz.open(PDFOUT)
    pages = [re.sub(r"\s+", " ", p.get_text()) for p in doc]
    bad = []

    def page_has(pno, needle):
        if pno is None or pno < 1 or pno > len(pages):
            return False
        return needle in pages[pno - 1]

    checked = 0
    for title, pno in res["toc_rows"]:
        want = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
        if not want:
            continue
        m = re.search(r"\b(\d{1,3})\s*$", title)
        if not pno or not pno.isdigit():
            bad.append(("contents", title, pno, "no page number"))
            continue
        if not page_has(int(pno), title[:24]):
            # a heading may be abbreviated in the table; check the words instead
            words = [w for w in want.split() if len(w) > 4][:3]
            if not words or not all(w in pages[int(pno) - 1].lower() for w in words):
                bad.append(("contents", title, pno, "heading not found on that page"))
        checked += 1

    for label, pno in res["fig_rows"]:
        n = re.match(r"Figure (\d+)", label)
        if not n:
            continue
        if not pno or not pno.isdigit():
            bad.append(("figures", label[:40], pno, "no page number"))
            continue
        if "Figure {}.".format(n.group(1)) not in pages[int(pno) - 1]:
            bad.append(("figures", label[:40], pno, "caption not found on that page"))
        checked += 1

    for label, pno in res["tab_rows"]:
        n = re.match(r"Table (\d+)", label)
        if not n:
            continue
        if not pno or not pno.isdigit():
            bad.append(("tables", label[:40], pno, "no page number"))
            continue
        if "Table {}.".format(n.group(1)) not in pages[int(pno) - 1]:
            bad.append(("tables", label[:40], pno, "caption not found on that page"))
        checked += 1

    doc.close()
    print()
    print("index entries checked against the finished PDF: {}".format(checked))
    print("index entries that failed: {}".format(bad if bad else "none"))
    print("page images in {}".format(QA))
    return res, bad


if __name__ == "__main__":
    main()
