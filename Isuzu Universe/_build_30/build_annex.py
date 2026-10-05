# -*- coding: utf-8 -*-
r"""Detail annex: build_annex.py -> ISUZU_UNIVERSE_3_0_ANNEX_2026-09-23.pdf

Run from the Isuzu Universe folder:  python _build_30\build_annex.py
"""
import os

import docbuild

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

MD = os.path.join(ROOT, "01_Strategy", "ISUZU_UNIVERSE_3_0_ANNEX_2026-09-23.md")
HTMLOUT = os.path.join(HERE, "ISUZU_UNIVERSE_3_0_ANNEX.html")
PDFOUT = os.environ.get("UNIVERSE_ANNEX_OUT",
                        os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_ANNEX_2026-09-23.pdf"))
QA = os.path.join(HERE, "_qa_annex")
FIGDIR = os.path.join(HERE, "figures")
TITLE = "ISUZU / UNIVERSE 3.0 / ANNEX"

CAPS = {
    17: "Proposed collaboration pattern. One function's agreement does not display the whole proposal as approved.",
    18: "Proposed structure for a real opportunity. Blank information remains unconfirmed and is not filled with an assumption.",
    19: "Proposed analytical sequence. Each stage retains its own source period and evidence.",
    20: "Proposed source standard. It describes business meaning rather than a prescribed technical file layout.",
    21: "Proposed record structure. A complete draft remains a draft until conditions and authority are confirmed.",
    22: "Measured activity, participant statements, modelled expectations and confirmed decisions are kept separate in every output.",
}

FOOTER = "Universe 3.0 annex  ·  23 September 2026  ·  {i} of {n}"

CLOSING = """
<div style="margin-top:8mm;border-top:1px solid #d8d2c8;padding-top:3mm;font-size:8pt;color:#5b6472">
  ISUZU / UNIVERSE 3.0 annex · 23 September 2026 · companion to
  <b>ISUZU_UNIVERSE_3_0_2026-09-23.pdf</b>. Read the main paper first: the recommendations and the
  money are there, not here.
</div>
"""


def main():
    cover = {
        "org": "ISZE / Parts Europe",
        "family": "Annex",
        "title": "Universe 3.0",
        "strap": "Tender framework, the IDS studio in full,<br>and the reference rules.",
        "focus": [
            "Part A — tenders and headquarters support.",
            "Part B — the IDS Development Studio.",
            "Part C — measures, identities, periods and the recurring exchange.",
        ],
        "focus_head": "What this annex carries",
        "meta": "Annex to version 3.0 &nbsp;·&nbsp; 23 September 2026",
        "meta2": "Internal &nbsp;·&nbsp; design detail and reference rules",
    }
    res = docbuild.build(MD, HTMLOUT, PDFOUT, QA, TITLE, cover, FIGDIR, CAPS, FOOTER, CLOSING)
    print(f"annex pages={res['pages']} chars={res['chars']} bookmarks={res['bookmarks']} "
          f"bytes={res['pdf_bytes']:,}")
    print(f"near-blank pages: {res['blank'] or 'none'}")
    print(f"blocks touching the edge: {res['edges'] or 'none'}")
    print(f"markdown artefacts: {res['artefacts'] or 'none'}")
    print(f"pages missing the running header: {res['missing_header'] or 'none'}")
    print(f"page images written to {QA}")
    return res


if __name__ == "__main__":
    main()
