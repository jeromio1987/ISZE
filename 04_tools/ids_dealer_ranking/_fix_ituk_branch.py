#!/usr/bin/env python3
from pathlib import Path

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
