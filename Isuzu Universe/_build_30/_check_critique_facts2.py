# -*- coding: utf-8 -*-
r"""Second pass: the claims that need a closer look.

Run from the Isuzu Universe folder:  python _build_30\_check_critique_facts2.py
"""
import csv
import os
import re
import sys

import fitz

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DERIVED = os.path.join(os.path.dirname(ROOT), "01_data", "00_derived")

V80 = os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_VISION_3_0.pdf")
V33 = os.path.join(ROOT, "ISUZU_UNIVERSE_COMMERCIAL_TOOLS_WHITE_PAPER.pdf")


def flat(path):
    d = fitz.open(path)
    return d, re.sub(r"\s+", " ", "".join(p.get_text() for p in d)).lower()


def main():
    d80, low80 = flat(V80)
    d33, low33 = flat(V33)

    print("=" * 78)
    print("A  ARROW / DISCLAIMER PHRASES IN THE 80-PAGER")
    print("=" * 78)
    for w in ["no measured causal effect is implied", "does not imply", "not a verdict",
              "no causal", "conditional", "arrow", "sequence", "indicative"]:
        print(f"  {w:<38}{low80.count(w)}")

    print()
    print("=" * 78)
    print("B  SCORED PARTICIPATION IN THE TWO PAPERS")
    print("=" * 78)
    for label, low in (("80-pager", low80), ("33-pager", low33)):
        for w in ["base rate", "/100", "score /100", "likely to", "probability",
                  "willingness", "willing", "would accept", "expect"]:
            print(f"  {label:<10}{w:<16}{low.count(w)}")
        print()

    print("=" * 78)
    print("C  132 AND 120 IN THE 80-PAGER")
    print("=" * 78)
    for m in list(re.finditer(r".{130}(?:132|120 unit).{130}", low80))[:8]:
        print("  |", m.group(0))

    print()
    print("=" * 78)
    print("D  WHAT IS ON PAGES 49 AND 63")
    print("=" * 78)
    for n in (48, 62):
        t = re.sub(r"\s+", " ", d80[n].get_text())
        print(f"  --- page {n + 1} ---")
        print("  " + t[:700])
        print()

    print("=" * 78)
    print("E  CHART-LIKE PAGES: pages whose text carries axis tick labels")
    print("=" * 78)
    for label, doc in (("80-pager", d80), ("33-pager", d33)):
        hits = []
        for i, p in enumerate(doc):
            t = p.get_text()
            signals = 0
            for pat in [r"\b\d+k\b", r"\b\d+\s*%", r"(?m)^\s*\d{1,3}\s*$"]:
                signals += len(re.findall(pat, t))
            if signals >= 6:
                hits.append((signals, i + 1))
        print(f"  {label}: " + ", ".join(f"p{n}({s})" for s, n in sorted(hits, reverse=True)))

    print()
    print("=" * 78)
    print("F  IDS FILE: NETWORKS AND PORTUGAL")
    print("=" * 78)
    ids = list(csv.DictReader(open(os.path.join(DERIVED, "ids_dealer_network_cleaned_2026-09-20.csv"),
                                   encoding="utf-8-sig")))
    tabs = {}
    for r in ids:
        tabs[r["ids_tab"]] = tabs.get(r["ids_tab"], 0) + 1
    print(f"  rows {len(ids)}  distinct ids_tab {len(tabs)}")
    for k in sorted(tabs):
        print(f"    {k:<28}{tabs[k]}")

    print()
    print("=" * 78)
    print("G  RECEIPT AND LAUNCHER INVENTORY")
    print("=" * 78)
    for f in sorted(os.listdir(ROOT)):
        if f.endswith(".SHIP_RECEIPT.json") or (f.startswith("OPEN_") and f.endswith(".cmd")):
            print("  " + f)
    print("  OPEN_ISUZU_UNIVERSE_3_0.cmd starts:")
    print("    " + open(os.path.join(ROOT, "OPEN_ISUZU_UNIVERSE_3_0.cmd")).read().strip())
    for name in ["OPEN_Universe_Opportunity_Page.cmd", "OPEN_Universe_Yellow_Paper_v0.5.cmd"]:
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            print(f"  {name} starts: {open(p).read().strip()}")


if __name__ == "__main__":
    main()
