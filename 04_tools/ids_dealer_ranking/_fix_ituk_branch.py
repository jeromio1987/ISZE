#!/usr/bin/env python3
"""SPENT one-shot (2026-07-28). DO NOT RE-RUN.

Rewrites the ITUK branch in build_ids_result_report.py to match label "UK LCV" —
the swapped label fixed on 2026-07-29. The branch now compares against
country_display_name("ITUK"), so this script would undo the correction.
"""
import sys
from pathlib import Path

sys.exit(
    "_fix_ituk_branch.py is spent and encodes the swapped UK label "
    '(ITUK -> "UK LCV"). ITUK is UK CV. Refusing to run.'
)

p = Path(__file__).resolve().parent / "build_ids_result_report.py"
t = p.read_text(encoding="utf-8")
needle = 'elif country.upper() == "ITUK":'
alt = 'elif country_display_name(country) == "UK (ITUK)" or country.upper() == "ITUK":'
want = (
    'elif country_display_name(country) in {"UK LCV", "UK (ITUK)"} '
    'or country.upper() == "ITUK":'
)
if want in t:
    print("already ok")
elif alt in t:
    p.write_text(t.replace(alt, want), encoding="utf-8")
    print("replaced alt")
elif needle in t:
    p.write_text(t.replace(needle, want), encoding="utf-8")
    print("replaced needle")
else:
    print("no ITUK branch found")
