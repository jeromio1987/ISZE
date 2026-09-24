# -*- coding: utf-8 -*-
"""One-off: make each figure's output filename match the number it carries in the paper."""
import io

P = r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_build_white\figures_white.py"
s = io.open(P, encoding="utf-8").read()

PAIRS = [
    ("f06_ids_scores.png", "f04_ids_scores.png"),
    ("f08_ituk_capture.png", "f05_ituk_capture.png"),
    ("f14_ceiling_placeholder.png", "f06_ceiling_placeholder.png"),
    ("f04_concession_by_distributor.png", "f07_concession_by_distributor.png"),
    ("f05_concession_by_family.png", "f08_concession_by_family.png"),
    ("f07_cordwallis.png", "f11_cordwallis.png"),
    ("f11_network_billed.png", "f12_network_billed.png"),
    ("f12_hurdle.png", "f13_hurdle.png"),
    ("f13_scope_effect.png", "f14_scope_effect.png"),
]
for a, b in PAIRS:
    assert s.count(a) == 1, (a, s.count(a))
    s = s.replace(a, b)
io.open(P, "w", encoding="utf-8").write(s)
print("renamed", len(PAIRS), "figures")
