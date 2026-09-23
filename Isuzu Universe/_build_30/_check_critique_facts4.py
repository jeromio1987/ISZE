# -*- coding: utf-8 -*-
r"""Fourth pass: the 33-pager's own substance, plus page renders to settle the chart count.

Run from the Isuzu Universe folder:  python _build_30\_check_critique_facts4.py
"""
import os
import re
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

V80 = os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pdf")
V33 = os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_TOOLS_WHITE_PAPER.pdf")
OUT = os.path.join(HERE, "_qa_critique_src")


def flat(path):
    d = fitz.open(path)
    return d, re.sub(r"\s+", " ", "".join(p.get_text() for p in d)).lower()


def main():
    d80, low80 = flat(V80)
    d33, low33 = flat(V33)

    print("=" * 78)
    print("A  THE 33-PAGER PAGE 4 (where the scope statement sits)")
    print("=" * 78)
    for i in range(d33.page_count):
        t = d33[i].get_text()
        if "routine" in t.lower() and i < 8:
            print(f"  --- page {i + 1} ---")
            print(t)
            print()

    print("=" * 78)
    print("B  TICKET / RESPONSE / SUPPORT WORDING IN BOTH")
    print("=" * 78)
    for label, low in (("80-pager", low80), ("33-pager", low33)):
        print(f"  --- {label} ---")
        for w in ["ticket", "response service", "response", "support desk", "help desk",
                  "support", "the dealer needs help", "needs help"]:
            print(f"    {w:<24}{low.count(w)}")
        print()

    print("=" * 78)
    print("C  'PROBABILITY' AND 'WOULD ACCEPT' CONTEXT IN THE 80-PAGER")
    print("=" * 78)
    for w in ["probability", "would accept", "conditional"]:
        for m in list(re.finditer(r".{140}" + re.escape(w) + r".{140}", low80)):
            print(f"  [{w}]", m.group(0))
            print()

    print("=" * 78)
    print("D  DOES EITHER PAPER CARRY A CONTRIBUTION-PER-ACTION TABLE?")
    print("=" * 78)
    for label, low in (("80-pager", low80), ("33-pager", low33)):
        print(f"  --- {label} ---")
        for w in ["actions", "action", "break-even", "break even", "envelope",
                  "100,000", "300,000", "payback", "return"]:
            print(f"    {w:<16}{low.count(w)}")
        print()
    print("  33-pager around 100,000 / 300,000:")
    for m in list(re.finditer(r".{120}(?:100,000|300,000).{200}", low33))[:8]:
        print("   *", m.group(0))
        print()

    print("=" * 78)
    print("E  THE 33-PAGER'S OWN READING GUIDE")
    print("=" * 78)
    for i in range(min(6, d33.page_count)):
        t = d33[i].get_text()
        if "chapter" in t.lower() and "pages" in t.lower():
            print(f"  --- page {i + 1} ---")
            print(t)
            print()

    print("=" * 78)
    print("F  RENDERING THE PAGES THAT COULD CARRY A CHART")
    print("=" * 78)
    os.makedirs(OUT, exist_ok=True)
    for label, doc, pages in (("v80", d80, [14, 15, 16, 49, 50, 51, 63]),
                              ("v33", d33, [9, 13, 15, 28])):
        for n in pages:
            doc[n - 1].get_pixmap(dpi=110).save(os.path.join(OUT, f"{label}_p{n:02d}.png"))
    for f in sorted(os.listdir(OUT)):
        print("  " + f)

    print()
    print("=" * 78)
    print("G  THE 33-PAGER'S COMPANION DECK")
    print("=" * 78)
    p = os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_TOOLS_PRESENTATION.pptx")
    try:
        from pptx import Presentation
        pr = Presentation(p)
        slides = list(pr.slides)
        words = shapes = charts = pics = tbls = 0
        for s in slides:
            for sh in s.shapes:
                shapes += 1
                if sh.has_text_frame:
                    words += len(sh.text_frame.text.split())
                st = str(sh.shape_type)
                if "CHART" in st:
                    charts += 1
                if "PICTURE" in st:
                    pics += 1
                if getattr(sh, "has_table", False):
                    tbls += 1
        print(f"  {os.path.basename(p)}: slides {len(slides)} words {words} "
              f"autoshapes {shapes} charts {charts} images {pics} tables {tbls}")
    except Exception as exc:  # noqa: BLE001
        print(f"  failed: {exc}")


if __name__ == "__main__":
    main()
