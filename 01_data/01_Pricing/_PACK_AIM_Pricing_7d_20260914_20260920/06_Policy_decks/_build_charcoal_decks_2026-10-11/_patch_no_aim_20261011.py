"""One-shot: strip spoken AIM + reframe competitive-label slide in build_aim_deck.py."""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = HERE / "build_aim_deck.py"
t = p.read_text(encoding="utf-8")

OUT_OLD = 'OUT = HERE.parents[1] / "05_AIM_classification" / "ISZE_AIM_Parts_Classification_Management_CHARCOAL_2026-10-11.pptx"'
OUT_NEW = 'OUT = HERE.parents[1] / "05_AIM_classification" / "ISZE_Parts_Classification_Management_CHARCOAL_2026-10-11.pptx"'
if OUT_OLD in t:
    t = t.replace(OUT_OLD, OUT_NEW)

repls = [
    ("AIM management presentation", "Parts classification management presentation"),
    ("he uses AIM", "he uses our parts classification"),
    ("I use AIM", "I use our parts classification"),
    ("use AIM", "use our parts classification"),
    ("AIM parts classification", "Parts classification"),
    ("AIM's top level", "The new top level"),
    ("AIM top level", "New top level"),
    ("AIM PLACES IT", "NEW PLACES IT"),
    ("AIM places it", "New places it"),
    ("AIM reads five", "The classification reads five"),
    ("AIM gives every", "Our parts classification gives every"),
    ("AIM gives that", "Our parts classification gives that"),
    ("That is what AIM provides", "That is what the classification provides"),
    ("what AIM provides", "what the classification provides"),
    ("AIM keeps them", "The classification keeps them"),
    ("assembly in AIM", "assembly in the classification"),
    ("cannot replace AIM", "cannot replace our parts classification"),
    ("AIM says what", "Our classification says what"),
    ("Every AIM result", "Every classification result"),
    ("analyse in AIM", "analyse with our parts classification"),
    ("reinforces AIM", "reinforces the classification"),
    ("gaps in AIM", "gaps in the classification"),
    ("gap in AIM", "gap in the classification"),
    ("With AIM it is", "With the classification it is"),
    ("AIM traces it", "The classification traces it"),
    ("What I use AIM for", "What I use the classification for"),
    ("Four things I use AIM for", "Four things I use the classification for"),
    ("HOW I USE AIM FROM NOW ON", "HOW I USE THE CLASSIFICATION FROM NOW ON"),
    ("AIM is the product language", "Our parts classification is the product language"),
    ("AIM: one parts classification", "One parts classification"),
    ("I use AIM as", "I use our parts classification as"),
    ("AIM (our parts classification)", "Our parts classification"),
    ("by AIM product", "by product"),
    ("by AIM family", "by family"),
    (" AIM part types", " part types"),
    ("AIM part types", "part types"),
    ('["AIM parts classification"]', '["Parts classification"]'),
]

for a, b in repls:
    t = t.replace(a, b)

# Reframe slide 2: stop leading with "42% competitive parts" as a share of competition
old_frame = '''frame(s, "The problem", "42% of what we bill sat under one label: “Competitive parts”",
      "Five of the seven top-level labels in the old price-list tree were commercial opinions. None named a product.",
      source=f"Base: €{BOOK / 1e6:.1f}M billed to distributors in the price revision book, July 2025 – June 2026 "
             f"({N['base']['part_numbers']:,} part numbers), including {eur_m(NONPART, 2)} of rebate, transport and "
             "lubricant lines. Old top level: price-list classification. AIM: approved release of 7 October 2026.",
      page=nxt(), panel=[
          ("The old top level mixed views on competition with product names. You could not ask “how are brakes "
           "selling?” from it.", RED),
          (f"The new top level names what the part is: {L[0]} families, from brakes to lighting.", AMBER),
          ("Purpose: one product view of everything we bill, so sales and prices can be read per product.", AMBER)])'''

# After first AIM strip, source line may already say AIM or not — match flexibly
old_frame2 = '''frame(s, "The problem", "42% of what we bill sat under one label: “Competitive parts”",
      "Five of the seven top-level labels in the old price-list tree were commercial opinions. None named a product.",'''

new_frame_head = '''frame(s, "The problem", "The old price list filed steering units as “Competitive parts”",
      "Nobody else makes a steering unit. That label mixed captive parts with wear parts under one commercial opinion.",'''

if old_frame2 in t:
    t = t.replace(old_frame2, new_frame_head)
else:
    raise SystemExit("slide-2 frame head not found")

# Fix source line that still says AIM approved release
t = t.replace(
    "lubricant lines. Old top level: price-list classification. AIM: approved release of 7 October 2026.",
    "lubricant lines. Old top level: price-list classification. New classification: approved release of 7 October 2026.",
)
t = t.replace(
    "lubricant lines. Old top level: price-list classification. Our parts classification: approved release of 7 October 2026.",
    "lubricant lines. Old top level: price-list classification. New classification: approved release of 7 October 2026.",
)

# Band under the charts: keep the euro, kill "42% competitive" reading
old_band = '''band(s, 0.25, 5.8, 9.4, 0.95, [[(f"{eur_m(comp['eur'])}, {comp['pct']:.0f}% of what we billed, sat under one label. ",
                                  {"bold": True}),
                                 ("Steering units, brake discs, brake pad kits, air filters and EGR components all read "
                                  "“Competitive parts”.", {})]], size=12.5)'''
new_band = '''band(s, 0.25, 5.8, 9.4, 0.95, [[(f"{eur_m(comp['eur'])} sat under one commercial label — not a measure of competition. ",
                                  {"bold": True}),
                                 ("Steering units alone are €1.26M of that pile; they are captive, not competitive.", {})]], size=12.5)'''
if old_band not in t:
    raise SystemExit("slide-2 band not found")
t = t.replace(old_band, new_band)

# Panel line on slide 4 that still praises AIM
t = t.replace(
    '("Purpose: let price evidence, per product and per market, decide where we compete. Our parts classification gives that evidence a '
    'product to attach to.", AMBER)]',
    '("Purpose: let price evidence, per product and per market, decide where we compete. The classification gives that evidence a '
    'product to attach to.", AMBER)]',
)

# Docstring / stance
t = t.replace(
    "Stance of the deck: Jerome informs management that he uses our parts classification. It asks for no decision.",
    "Stance of the deck: Jerome informs management that he uses our parts classification. It asks for no decision. Spoken name: parts classification — never AIM.",
)

# Any leftover spoken AIM (not identifiers)
leftover = []
for i, line in enumerate(t.splitlines(), 1):
    if "AIM" not in line:
        continue
    if any(
        k in line
        for k in (
            "aim_numbers",
            "build_aim",
            "['aim']",
            '["aim"]',
            "aim_l1",
            "aim_l2",
            "aim_l3",
            "top_code_aim",
            "05_AIM",
            "_aim_",
            "aim_short",
        )
    ):
        continue
    leftover.append(f"{i}: {line.strip()[:140]}")

p.write_text(t, encoding="utf-8")
print("written", p)
print("leftover spoken AIM lines:", len(leftover))
for x in leftover:
    print(x)
