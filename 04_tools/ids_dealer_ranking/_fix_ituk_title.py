#!/usr/bin/env python3
"""SPENT one-shot (2026-07-28). DO NOT RE-RUN.

Hardcodes the ITUK ranking sheet title to "UK LCV" — the swapped label fixed on
2026-07-29. build_ituk_ranking.py now takes the title from ids_paths.country_label,
so this script would undo the correction. Kept for history only.
"""
import sys
from pathlib import Path
import re

sys.exit(
    "_fix_ituk_title.py is spent and encodes the swapped UK label "
    '(ITUK -> "UK LCV"). ITUK is UK CV. Refusing to run.'
)

p = Path(__file__).resolve().parent / "build_ituk_ranking.py"
t = p.read_text(encoding="utf-8")
t2, n = re.subn(
    r"write_ranking_workbook\(\s*\"[^\"]+\",",
    'write_ranking_workbook(\n        "UK LCV",',
    t,
    count=1,
)
p.write_text(t2, encoding="utf-8")
print("replaced", n, "UK LCV" in t2)
