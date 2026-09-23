"""Did my ceiling rebuild change the exec paper's sell-out framing, or did it already fail?

Compares the sell-out sentence in the backup copy against the rebuilt file.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OLD = ROOT / ("01_data/91_build/_backsafe_20260922_ceiling/original/02_dashboards/sales/"
              "ISZE_Exec_Aftersales_Paper.html")
NEW = ROOT / "02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html"

PATTERNS = [
    r"sell[\s-]?out.{0,160}(?:\d+(?:[.,]\d+)?\s*%\s*of\s*(?:GPS\s+)?billed|"
    r"percent of (?:the )?(?:GPS\s+)?billed|share of (?:the )?(?:GPS\s+)?billed)",
    r"(?:\d+(?:[.,]\d+)?\s*%|percent).{0,40}of\s+(?:GPS\s+)?billed.{0,80}sell[\s-]?out",
    r"sell[\s-]?out.{0,80}(?:covers?|coverage).{0,40}\d+(?:[.,]\d+)?\s*%",
]


def strip_styles(t: str) -> str:
    t = re.sub(r'style\s*=\s*"[^"]*"', " ", t, flags=re.I)
    return re.sub(r"style\s*=\s*'[^']*'", " ", t, flags=re.I)


def report(path: Path, tag: str) -> bool:
    t = path.read_text(encoding="utf-8")
    b = strip_styles(t)
    hit = any(re.search(p, b, flags=re.I) for p in PATTERNS)
    print(f"== {tag}: gate pattern present = {hit}")
    for m in re.finditer(r"sell[\s-]?out", b, flags=re.I):
        s = max(0, m.start() - 120)
        e = min(len(b), m.end() + 220)
        print("   ...", " ".join(b[s:e].split()), "...")
    return hit


def main() -> int:
    old_hit = report(OLD, "BACKUP (state before my rebuild)")
    new_hit = report(NEW, "NOW (after my rebuild)")
    print()
    if old_hit and not new_hit:
        print("MY REBUILD DROPPED the framing -> my problem, restore or fix the builder.")
    elif old_hit and new_hit:
        print("The framing was passing before and passes now - nothing to do.")
    elif not old_hit and not new_hit:
        print("Pre-existing failure: the paper did not carry this framing before my rebuild")
        print("either. Nothing in this pass caused it, and nothing in this pass was asked to")
        print("rewrite the paper's narrative.")
    else:
        print("Odd: absent before, present now.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
