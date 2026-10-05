# -*- coding: utf-8 -*-
r"""Fifth pass: the open questions the brief raises that the first four passes did not settle.

Run from the Isuzu Universe folder:  python _build_30\_check_critique_facts5.py
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


def flat(path):
    d = fitz.open(path)
    return d, re.sub(r"\s+", " ", "".join(p.get_text() for p in d)).lower()


def main():
    d80, low80 = flat(V80)
    d33, low33 = flat(V33)

    print("=" * 78)
    print("A  WHAT NOTE ACCOMPANIES EACH 'PROPOSED SEQUENCE' CAPTION")
    print("=" * 78)
    for w in ["each stage retains its own evidence", "retains its own evidence and decision",
              "proposed sequence", "proposed feedback mechanism", "illustrative design",
              "no measured causal effect is implied"]:
        print(f"  {w:<44}80:{low80.count(w):>4}  33:{low33.count(w):>4}")

    print()
    print("=" * 78)
    print("B  'HELP' AS A VERB IN THE 80-PAGER")
    print("=" * 78)
    print(f"  help / helps / helping: {len(re.findall(r'help|helps|helping', low80))}")
    print(f"  help desk: {low80.count('help desk')}   support desk: {low80.count('support desk')}")
    for m in list(re.finditer(r".{70}\bhelps?\b.{90}", low80))[:6]:
        print("   *", m.group(0))

    print()
    print("=" * 78)
    print("C  THE 33-PAGER'S ARITHMETIC PAGES (14-15 and 25-28)")
    print("=" * 78)
    for n in (14, 15, 26, 27, 28):
        t = re.sub(r"\s+", " ", d33[n - 1].get_text())
        print(f"  --- page {n} ---")
        print("  " + t[:1600])
        print()

    print("=" * 78)
    print("D  DOES THE 80-PAGER CARRY THE SAME ARITHMETIC?")
    print("=" * 78)
    for w in ["40", "120 qualifying", "44 actions", "action-count", "count of actions",
              "per action", "contribution per", "2,500", "5,000"]:
        print(f"  {w:<20}80:{low80.count(w):>4}  33:{low33.count(w):>4}")
    print()
    print("  the 80-pager around 'break-even':")
    for m in list(re.finditer(r".{200}break-even.{240}", low80)):
        print("   *", m.group(0))
    print()
    print("  the 33-pager around 'break-even':")
    for m in list(re.finditer(r".{200}break-even.{240}", low33)):
        print("   *", m.group(0))
    print()
    print("  the 33-pager around '5,000':")
    for m in list(re.finditer(r".{150}5,000.{180}", low33))[:8]:
        print("   *", m.group(0))
        print()


if __name__ == "__main__":
    main()
