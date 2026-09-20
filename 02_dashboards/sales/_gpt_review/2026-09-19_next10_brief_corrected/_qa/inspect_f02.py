"""F02 payload surgery — inspect exact bytes before editing. Read-only."""
import re, sys

P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\02_ISZE_Leakage_Cockpit.html"
with open(P, encoding="utf-8", newline="") as f:
    t = f.read()

lines = t.split("\n")
for n in (309, 363, 364, 365, 366, 710, 711, 712, 713, 714, 715, 716, 726, 57636, 57637, 57638, 57639, 57640, 57641, 57642):
    print(f"--- L{n} ---")
    print(repr(lines[n - 1]))

print("\n=== forward block count (top-level, 18 expected) ===")
fw = re.findall(r'\n(?P<i>[ \t]*)"forward": \{\n(?P=i)  "year": 2030,\n(?P=i)  "ceiling_2030_eur": [0-9.]+,\n(?P=i)  "vs_2024_pct": [0-9.\-]+,\n(?P=i)  "cum_ceiling_eur": [0-9.]+,\n(?P=i)  "modelled": true\n(?P=i)\},', t)
print("matched forward blocks:", len(fw))
print("literal ceiling_2030 occurrences:", t.count("ceiling_2030_eur"))
print("forward key occurrences:", t.count('"forward": {'))
