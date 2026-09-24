# -*- coding: utf-8 -*-
r"""Critique pack: build_critique.py -> GPT_HANDOVER_2026-09-23\UNIVERSE_3_0_CRITIQUE_2026-09-23.pdf

The review of the two 22 September papers, rendered in the 80-pager's own charcoal and Isuzu red.
That palette is the point of the request: it is the styling the other tool recognises as its own.

Run from the Isuzu Universe folder:  python _build_30\build_critique.py
"""
import os

import docbuild

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PACK = os.path.join(ROOT, "GPT_HANDOVER_2026-09-23")
MD = os.path.join(PACK, "UNIVERSE_3_0_CRITIQUE_2026-09-23.md")
HTMLOUT = os.path.join(HERE, "UNIVERSE_3_0_CRITIQUE.html")
PDFOUT = os.environ.get("CRITIQUE_PDF_OUT",
                        os.path.join(PACK, "UNIVERSE_3_0_CRITIQUE_2026-09-23.pdf"))
QA = os.path.join(HERE, "_qa_critique")
FIGDIR = os.path.join(HERE, "figures")
TITLE = "UNIVERSE 3.0 / CRITIQUE"

FOOTER = "Review of the 22 September papers  ·  23 September 2026  ·  {i} of {n}"


def main():
    cover = {
        "org": "ISZE / Parts Europe",
        "family": "Review",
        "title": "Universe 3.0",
        "strap": "Thirteen findings on the two 22 September papers,<br>"
                 "and what the current edition changed.",
        "focus": [
            "The scope boundary missing from the flagship.",
            "Two product catalogues, and no authority declared.",
            "The economics: four gaps, and the arithmetic that closes them.",
            "What changed, and what is still open.",
        ],
        "focus_head": "What this review covers",
        "meta": "Review pack &nbsp;·&nbsp; 23 September 2026",
        "meta2": "Safe to forward &nbsp;·&nbsp; aggregate figures only",
    }
    # No chapters_fresh_page and no reading guide: this is a short review, read front to back.
    # The layout checks still run, so the rendered file is measured rather than assumed.
    res = docbuild.build(MD, HTMLOUT, PDFOUT, QA, TITLE, cover, FIGDIR, {},
                         FOOTER, theme="charcoal")
    print(f"critique pages={res['pages']} chars={res['chars']} bookmarks={res['bookmarks']} "
          f"bytes={res['pdf_bytes']:,}")
    print(f"near-blank pages: {res['blank'] or 'none'}")
    print(f"blocks touching the edge: {res['edges'] or 'none'}")
    print(f"markdown artefacts: {res['artefacts'] or 'none'}")
    print(f"pages missing the running header: {res['missing_header'] or 'none'}")
    lay = res["layout"]
    print("--- layout ---")
    print(f"headings stranded at the foot of a page: {lay['stranded_headings'] or 'none'}")
    print(f"figures parted from their caption:       {lay['figure_caption_splits'] or 'none'}")
    print(f"tables split from their introduction:    {lay['table_splits'] or 'none'}")
    print(f"figure pages left mostly empty:          {lay['figure_tails'] or 'none'}")
    print(f"pages that end early:                    "
          f"{[h['page'] for h in lay['early_ends']] or 'none'}")
    print(f"page images written to {QA}")
    return res


if __name__ == "__main__":
    main()
