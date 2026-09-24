# -*- coding: utf-8 -*-
r"""Main paper: build.py -> ISUZU_UNIVERSE_3_0_2026-09-23.pdf

Regenerates the figures from the named source files first, so the paper cannot carry a chart that
disagrees with its source.

Run from the Isuzu Universe folder:  python _build_30\build.py
"""
import os
import sys

import docbuild

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

MD = os.path.join(ROOT, "01_Strategy", "ISUZU_UNIVERSE_3_0_2026-09-23.md")
HTMLOUT = os.path.join(HERE, "ISUZU_UNIVERSE_3_0.html")
# The root PDF may be open in a reader; allow a staging path for mid-iteration builds.
PDFOUT = os.environ.get("UNIVERSE_PDF_OUT",
                        os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_2026-09-23.pdf"))
QA = os.path.join(HERE, "_qa")
FIGDIR = os.path.join(HERE, "figures")
TITLE = "ISUZU / UNIVERSE 3.0"

FIGS = [
    (1, "the argument for the whole programme",
     "Recorded ISZE billing and quantity, ITUK brake-pad source category, full calendar 2024 and 2025. Measured; source snapshot 19 September 2026, arithmetic rechecked 23 September 2026."),
    (2, "the boundary",
     "A normal service stays a normal service. Evidence from it may inform an agreed analysis; its workflow does not become a module."),
    (3, "the portfolio",
     "Four foundations, five tools, one class of decision. Each tool uses only the evidence relevant to its own question."),
    (4, "the reduction is concentrated in one product form",
     "Magnitude of billing reduction across three selected ITUK source categories, CY2025 vs CY2024. Measured."),
    (5, "the combined offer grew while Genuine fell",
     "ISZE parts billed to I Motors, clutch-kit source category, full calendar years. Measured. Quantity was almost unchanged: 462 kits to 461."),
    (6, "network parts billed and deep concession, 2025",
     "PMS lines carrying a reference price, 24 distributors. The ten largest deep-discount shares are shown. Measured."),
    (7, "where the deep concession is, by family",
     "The eight largest PMS families by 2025 billing. Measured."),
    (8, "the hurdle the money implies",
     "Qualifying actions needed to cover each envelope at four assumed contribution levels. Hypothetical arithmetic on stated inputs, not a forecast of dealer profitability."),
    (9, "the scope effect on contribution",
     "Hypothetical arithmetic: 100-unit baseline at EUR 100 net and EUR 70 parts cost, 20 additional units, 5% concession. Not an Isuzu price, offer or forecast."),
    (10, "how a user moves through the Atlas",
     "Proposed analytical sequence. Each stage retains its own source period and evidence."),
    (11, "a filter element is not a filter housing",
     "Proposed product-form distinction. It prevents an average unit price from describing a mix change as a price change."),
    (12, "three records, kept apart",
     "Proposed record structure. No actual dealer score, date or progress is represented."),
    (13, "five checks before a range becomes an initiative",
     "Proposed decision gate. A missing purchase is not evidence of unmet demand."),
    (14, "how the dealer joins",
     "Proposed participant journey. No dealer has been invited and no access has been accepted."),
    (15, "the recorded IDS scores behind the opening offer",
     "Dealer network file of 20 September 2026: 519 rows across 19 networks. 490 carry a recorded score, mean 79.3; the remaining 29 recorded no answers at all and are held apart. Measured."),
    (16, "the exchange, and what each side puts in",
     "Proposed participation design. Payment for data volume is excluded and ordinary service is never conditional on a contribution."),
]

FOOTER = "Universe 3.0  ·  23 September 2026  ·  {i} of {n}"

READING_GUIDE = [
    ("How to read this", "The three decisions, and where the paper takes each one."),
    ("Executive summary", "What the programme is, what it is not, and the three decisions."),
    ("1. The commercial promise and the scope boundary",
     "The promise, and the exclusion that keeps routine service out."),
    ("2. The portfolio", "Five tools, the three developed examples, and what connects them."),
    ("3. Why product detail, shown on real numbers",
     "ITUK, Portugal and the concession picture, on measured billing."),
    ("4. The economics, and what the investment must earn",
     "The denominator, the hurdle, the price of a dealer, the funding line."),
    ("5. AIM Commercial Atlas", "How a user moves from a total to a chosen range decision."),
    ("6. IDS Development Studio", "The self-assessment turned into a plan the dealer owns."),
    ("7. Range, pricing and market tools", "The planner, the margin lab and market intelligence."),
    ("8. Participation: will they actually join?",
     "What each side receives, scored step by step against the base rate."),
    ("9. What to build first, what to fund, and what to stop",
     "The sequence, the funding recommendation and the stop condition."),
    ("10. Delivery, ownership and risk", "Ownership, the access limits, and the legal boundary."),
    ("11. What we measured, what we inferred, what we assume",
     "The evidence labels, the elasticity disclosure and the open unknowns."),
    ("12. Reference: measures", "What each commercial term means in this paper."),
    ("13. Reference: periods, populations and identities", "Period, population and identity rules."),
    ("14. Reference: sources and revision record",
     "The source codes, and what changed in this edition."),
]

CLOSING = """
<div style="margin-top:8mm;border-top:1px solid #d8d2c8;padding-top:3mm;font-size:8pt;color:#5b6472">
  ISUZU / UNIVERSE 3.0 · 23 September 2026 · supersedes the Commercial Vision 3.0 and the
  Commercial Tools Edition of 22 September 2026. The design detail behind chapters 5 to 7 and the
  reference rules sit in the companion annex, <b>ISUZU_UNIVERSE_3_0_ANNEX_2026-09-23.pdf</b>.
</div>
"""


def main():
    print("regenerating figures ...")
    import figures
    figs = figures.build_all()
    caps = {n: c for n, _t, c in FIGS}
    cover = {
        "org": "ISZE / Parts Europe",
        "family": "Commercial Vision",
        "title": "Universe 3.0",
        "strap": "Give distributors and dealers tools worth using.<br>"
                 "Earn the information that makes those tools better.",
        "figure": [f for f in sorted(os.listdir(FIGDIR)) if f.startswith("f01_")][0],
        "figure_caption": caps[1],
        "focus": [
            "The scope boundary: routine service is not the product.",
            "One portfolio of five tools, not two competing product stories.",
            "What the campaign investment must earn, and the size floor.",
            "What a dealer and a distributor actually receive, and where each will stop.",
        ],
        "meta": "Version 3.0 &nbsp;·&nbsp; 23 September 2026",
        "meta2": "Internal &nbsp;·&nbsp; proposed product and participation paper",
    }
    res = docbuild.build(MD, HTMLOUT, PDFOUT, QA, TITLE, cover, FIGDIR, caps,
                         FOOTER, CLOSING, chapters_fresh_page=True,
                         reading_guide=READING_GUIDE,
                         guide_heading="", 
                         guide_intro="Every chapter, its pages in this edition, and the one thing it "
                                     "settles. Page numbers refer to this 23 September 2026 file.",
                         guide_head=("Chapter", "Pages", "What it settles"))
    print(f"pages={res['pages']} chars={res['chars']} bookmarks={res['bookmarks']} "
          f"bytes={res['pdf_bytes']:,} figures={len(figs)}")
    print(f"near-blank pages: {res['blank'] or 'none'}")
    print(f"blocks touching the edge: {res['edges'] or 'none'}")
    print(f"markdown artefacts: {res['artefacts'] or 'none'}")
    print(f"pages missing the running header: {res['missing_header'] or 'none'}")

    lay = res["layout"]
    print("--- layout ---")
    print(f"chapter page breaks inserted:            {res['chapter_breaks'] or 'none'}")
    print(f"headings stranded at the foot of a page: {lay['stranded_headings'] or 'none'}")
    print(f"figures parted from their caption:       {lay['figure_caption_splits'] or 'none'}")
    print(f"tables split from their introduction:    {lay['table_splits'] or 'none'}")
    print(f"figure pages left mostly empty:          {lay['figure_tails'] or 'none'}")
    print(f"chapters that could open fresh:          "
          f"{lay['chapters_that_could_open_fresh'] or 'none'}")
    print("--- reading guide ---")
    for title_txt, pages, _purpose in res["guide_rows"]:
        print(f"  {pages:<10} {title_txt}")
    print(f"page images written to {QA}")
    return res


if __name__ == "__main__":
    main()
