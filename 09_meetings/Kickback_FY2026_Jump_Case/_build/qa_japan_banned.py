# -*- coding: utf-8 -*-
"""Banned-string + euro-only scan over every deck and notes text string."""
import re, sys
from pptx import Presentation

DECK = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case\ISZE_Kickback_Japan_Pack_20261007.pptx"
p = Presentation(DECK)

blobs = []
for i, s in enumerate(p.slides, 1):
    parts = []
    for sh in s.shapes:
        if sh.has_text_frame:
            parts.append(sh.text_frame.text)
    if s.has_notes_slide:
        parts.append("[NOTES] " + s.notes_slide.notes_text_frame.text)
    blobs.append((i, "\n".join(parts)))

BANNED_LITERAL = [
    "sell-out", "sellout", "sell out", "Mode A", "Mode B", "MODE: A", "MODE: B",
    "0.82", "street", "105%", "33%", "hardware PN", "List 1", "List 2",
    "1.785", "1.40", "\u00d71.785", "factor",
]
UNIT_WORDS = re.compile(r"\b(units?|pieces?|pcs|qty|quantit(?:y|ies))\b", re.I)
RATIO_ON_UNITS = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|x|\u00d7)\s*(?:on|of)\s*(?:units?|pieces?|volume)", re.I)
# "no IBX claim, no ISD claim" means no performance claim about them.  Naming ISD
# as the owner of an action item is not a claim, and the approved reference deck
# does exactly that ("load ISD Feb-Jul 2026").  So the token itself is not banned;
# what is banned is IBX / ISD attached to a figure, a share or a capture statement.
ENTITY_CLAIM = re.compile(
    r"\b(?:IBX|ISD)\b[^.\n]{0,40}?(?:EUR\s?[\d,]+|\d+(?:\.\d+)?\s?%)", re.I)
ENTITY_WORD = re.compile(r"\b(?:IBX|ISD)\b[^.\n]{0,40}?\b(?:share|capture|index|penetration|rate)\b", re.I)

fails = []
for i, blob in blobs:
    low = blob.lower()
    for b in BANNED_LITERAL:
        if b.lower() in low:
            fails.append("slide %d: banned literal %r" % (i, b))
    for m in UNIT_WORDS.finditer(blob):
        ctx = blob[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")
        # allow "volume", and allow the phrase 'no quantity' only if it is an exclusion note
        fails.append("slide %d: unit word %r in ...%s..." % (i, m.group(0), ctx))
    for m in RATIO_ON_UNITS.finditer(blob):
        fails.append("slide %d: ratio-on-units %r" % (i, m.group(0)))
    for m in ENTITY_CLAIM.finditer(blob):
        fails.append("slide %d: IBX/ISD figure claim %r" % (i, m.group(0)))
    for m in ENTITY_WORD.finditer(blob):
        fails.append("slide %d: IBX/ISD share claim %r" % (i, m.group(0)))

print("banned scan over %d slides" % len(blobs))
print("fails:", len(fails))
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
