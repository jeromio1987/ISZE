# -*- coding: utf-8 -*-
r"""Third pass: the 33-pager's own content, and the chart inventory.

Run from the Isuzu Universe folder:  python _build_30\_check_critique_facts3.py
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


def main():
    d80 = fitz.open(V80)
    d33 = fitz.open(V33)
    low80 = re.sub(r"\s+", " ", "".join(p.get_text() for p in d80)).lower()
    low33 = re.sub(r"\s+", " ", "".join(p.get_text() for p in d33)).lower()

    print("=" * 78)
    print("A  THE HURDLE TABLE: 33-PAGER vs 80-PAGER")
    print("=" * 78)
    for label, low in (("80-pager", low80), ("33-pager", low33)):
        print(f"  --- {label} ---")
        for w in ["hurdle", "qualifying action", "successful action", "200", "600",
                  "contribution per action", "2,500", "5,000"]:
            print(f"    {w:<26}{low.count(w)}")
    print()
    print("  33-pager passages containing 'hurdle' or 'action':")
    for m in list(re.finditer(r".{150}(?:hurdle|qualifying action|successful action).{200}", low33))[:6]:
        print("   *", m.group(0))
        print()

    print("=" * 78)
    print("B  THE FIVE TOOLS AS THE 33-PAGER NAMES THEM")
    print("=" * 78)
    for m in list(re.finditer(r".{100}aim commercial atlas.{200}", low33))[:2]:
        print("  |", m.group(0))
        print()

    print("=" * 78)
    print("C  CHART INVENTORY BY PAGE")
    print("=" * 78)
    print("  A chart page is scored on how much of its text is axis/legend text:")
    print("  short numeric tokens (1-4 chars), 'k' suffixes and percentages.")
    for label, doc in (("80-pager", d80), ("33-pager", d33)):
        scored = []
        for i, p in enumerate(doc):
            t = re.sub(r"\s+", " ", p.get_text())
            toks = t.split()
            if not toks:
                continue
            numeric = sum(1 for x in toks if re.fullmatch(r"[\d.,%+-]+k?", x))
            share = numeric / len(toks)
            scored.append((round(share, 3), numeric, len(toks), i + 1))
        scored.sort(reverse=True)
        print(f"  --- {label}: top eight pages by numeric share of the words ---")
        for share, n, tot, pg in scored[:8]:
            print(f"    page {pg:>3}   numeric tokens {n:>3} of {tot:>4}   share {share:.3f}")
        print(f"  pages with a numeric share above 0.18: "
              f"{[pg for s, _n, _t, pg in sorted(scored, key=lambda z: z[3]) if s > 0.18]}")
        print()

    print("=" * 78)
    print("D  PAGE 2 OF THE 80-PAGER (first mention of Deal of the Day)")
    print("=" * 78)
    print(d80[1].get_text())

    print("=" * 78)
    print("E  LAUNCHER SIBLINGS, BY STEM")
    print("=" * 78)
    cmds = {}
    for f in sorted(os.listdir(ROOT)):
        if f.startswith("OPEN_") and f.endswith(".cmd"):
            body = open(os.path.join(ROOT, f)).read()
            m = re.search(r"%~dp0([^\"]+)", body) or re.search(r"(?i)([\w.\\-]+\.(?:pdf|html))", body)
            cmds[f] = m.group(1).strip() if m else "?"
    for k, v in cmds.items():
        print(f"  {k:<44}-> {v}")


if __name__ == "__main__":
    main()
