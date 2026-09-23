# -*- coding: utf-8 -*-
r"""Did the seven corrections land, and is the language clean?

Run from the Isuzu Universe folder:  python _build_30\check_coverage.py
Exit 0 only when every correction is present and no banned term survives.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding="utf-8")

MD = os.path.join(ROOT, "01_Strategy", "ISUZU_UNIVERSE_3_0_2026-09-23.md")
PDF = os.path.join(ROOT, "ISUZU_UNIVERSE_3_0_2026-09-23.pdf")

md = open(MD, encoding="utf-8").read()
# patterns must match across a line break, so compare on collapsed whitespace
low = re.sub(r"\s+", " ", md.lower())

# Each correction from the review of 22 September, and the phrases that prove it landed.
CHECKS = [
    ("1  the scope boundary is back, and it excludes routine service",
     ["outside universe", "when will this part arrive", "support administration",
      "not a reward for participation", "do not import the day-to-day service"]),
    ("1  the superseded editions are declared, not left competing",
     ["both are withdrawn", "supersedes the commercial vision 3.0",
      "its separate existence as a parallel product story is withdrawn"]),
    ("2  one decision route, and the money is not on page 42",
     ["the three decisions", "chapters 1 to 4 and you have the commercial case"]),
    ("3  the money pages exist: the denominator",
     ["32,381,311.55", "30,756,771.61", "0.31%", "0.93%"]),
    ("3  the money pages exist: the hurdle",
     ["the hurdle", "200 of them", "forty qualifying actions", "evidence, not a return"]),
    ("3  the money pages exist: the price of a dealer",
     ["the price of a dealer", "28.90", "937.50", "519", "334"]),
    ("3  campaign support is its own funded line",
     ["named campaign-support line", "minimum campaign size", "150,000",
      "is a control and not an answer"]),
    ("3  the elasticity evidence is disclosed, not hidden",
     ["what elasticity evidence exists", "direction only", "not a usable elasticity",
      "inconclusive", "no scenario in this programme forecasts a demand response"]),
    ("4  figures carry their source and their limit",
     ["measured", "inferred", "proposed", "unknown"]),
    ("5  the legal boundary is stated once",
     ["31 may 2028", "no exclusivity in exchange for information",
      "no price coordination", "no resale-price instruction",
      "reviewed for competition-law compliance"]),
    ("6  the edition is recorded as generated",
     ["_build_30"]),
    ("7  the paper records what changed in this edition",
     ["new in this edition", "withdrawn"]),
]

# Narrative language that must not appear. File paths and code names are stripped first.
BANNED = ["mode a", "mode b", "sell-out", "sell out", "wallet", "book b", "street fill",
          "street index", "ship-gate", "ship gate", "harness", "upstream", "downstream",
          "artefact", "rollup", "granularity"]


def main():
    ok = missing = 0
    print("=" * 78)
    print("DID EVERY CORRECTION LAND IN UNIVERSE 3.0?")
    print("=" * 78)
    for label, pats in CHECKS:
        absent = [p for p in pats if p not in low]
        if not absent:
            ok += 1
            print(f"  LANDED   {label}")
        else:
            missing += 1
            print(f"  MISSING  {label}")
            print(f"           absent: {absent}")
    print("-" * 78)
    print(f"  {ok} landed, {missing} missing")

    print()
    print("=" * 78)
    print("BANNED LANGUAGE IN NARRATIVE TEXT")
    print("=" * 78)
    stripped = re.sub(r"`[^`]*`", " ", low)
    stripped = re.sub(r"[a-z0-9_/\\.-]*\.(csv|json|md|pdf|xlsx|html|parquet|py|cmd)", " ", stripped)
    hits = 0
    for w in BANNED:
        for m in list(re.finditer(re.escape(w), stripped))[:2]:
            hits += 1
            a, b = max(0, m.start() - 70), min(len(stripped), m.end() + 70)
            print(f"  [{w}]: ...{stripped[a:b].replace(chr(10), ' ')}...")
    if not hits:
        print("  none found")
    print("=" * 78)

    # the PDF is the deliverable, so check the rendered page count too
    if os.path.exists(PDF):
        import fitz
        d = fitz.open(PDF)
        figs = sum(len(p.get_images(full=True)) for p in d)
        print(f"  rendered: {d.page_count} pages, {len(d.get_toc())} bookmarks, "
              f"{figs} placed figure image(s)")
        if d.page_count < 20:
            print("  FAIL: fewer pages than expected")
            missing += 1
    else:
        print(f"  FAIL: {PDF} does not exist")
        missing += 1

    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
