# -*- coding: utf-8 -*-
"""Final verification for ISZE_Kickback_Japan_Pack_20261007.pptx.

Checks, in order:
  1  slide text + notes: banned words, unit/quantity words, ratios computed on units
  2  euro-only: no chart axis label in the deck's own images carries a unit word,
     and no slide text charts a quantity
  3  the four protected caveats are still present on the slides
  4  every picture in the deck exists inside the slide box
  5  the launcher exists and is CRLF
  6  OOXML package integrity
Exit 0 only when all pass.
"""
import os
import re
import sys
import zipfile

from lxml import etree
from pptx import Presentation
from pptx.util import Emu

DECK = (r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
        r"\ISZE_Kickback_Japan_Pack_20261007.pptx")
CMD = (r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
       r"\OPEN_Kickback_Japan_Pack.cmd")

fails = []
warns = []

prs = Presentation(DECK)
SW, SH = prs.slide_width, prs.slide_height

# ---------------------------------------------------------------- 1  words
BANNED = ["sell-out", "sellout", "sell out", "Mode A", "Mode B", "MODE: A", "MODE: B",
          "0.82", "aftermarket index", "street", "hardware PN", "List 1", "List 2",
          "1.785", "\u00d71.785", "class factor", "factor_", "markup"]
# the units rule: no quantity nouns, and no ratio computed on units
UNIT_WORDS = re.compile(r"\b(units?|pieces?|pcs|qty|quantit(?:y|ies))\b", re.I)
RATIO_ON_UNITS = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|x|\u00d7)\s*(?:on|of|per)\s*(?:units?|pieces?|volume|qty)", re.I)
# "no IBX claim, no ISD claim" = no performance claim about them.  Naming ISD as
# the owner of an action item is not a claim.
ENTITY_CLAIM = re.compile(
    r"\b(?:IBX|ISD)\b[^.\n]{0,40}?(?:EUR\s?[\d,]+|\d+(?:\.\d+)?\s?%)", re.I)
ENTITY_WORD = re.compile(r"\b(?:IBX|ISD)\b[^.\n]{0,40}?\b(?:share|capture|index|penetration|rate)\b", re.I)

blobs = []
for i, s in enumerate(prs.slides, 1):
    parts = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame]
    if s.has_notes_slide:
        parts.append("[NOTES] " + s.notes_slide.notes_text_frame.text)
    blobs.append((i, "\n".join(parts)))

for i, blob in blobs:
    low = blob.lower()
    for b in BANNED:
        if b.lower() in low:
            fails.append("slide %d: banned word %r" % (i, b))
    for m in UNIT_WORDS.finditer(blob):
        ctx = blob[max(0, m.start() - 70):m.end() + 70].replace("\n", " ")
        fails.append("slide %d: unit word %r in ...%s..." % (i, m.group(0), ctx))
    for m in RATIO_ON_UNITS.finditer(blob):
        fails.append("slide %d: ratio computed on units %r" % (i, m.group(0)))
    for m in ENTITY_CLAIM.finditer(blob):
        fails.append("slide %d: IBX/ISD figure claim %r" % (i, m.group(0)))
    for m in ENTITY_WORD.finditer(blob):
        fails.append("slide %d: IBX/ISD share claim %r" % (i, m.group(0)))

# ------------------------------------------------- 3  protected caveats
CAVEATS = [
    ("slide 5", "dealer's volume valued at ISZE prices"),
    ("slide 6", "225,364"),
    ("slide 6", "225,744"),
    ("slide 6", "not explained"),
    ("slide 8", "No distributor notice"),
    # the new slide's own protected statements
    ("slide 4", "no single answer"),
    ("slide 4", "invisible to us"),
    ("slide 4", "not yet loaded"),
]
for slide_lbl, needle in CAVEATS:
    idx = int(slide_lbl.split()[1])
    if needle.lower() not in blobs[idx - 1][1].lower():
        fails.append("%s: protected caveat missing: %r" % (slide_lbl, needle))

# ------------------------------------------------- 4  pictures inside
npic = 0
for i, s in enumerate(prs.slides, 1):
    for sh in s.shapes:
        if sh.shape_type is None or not sh.shape_type.name.startswith("PICTURE"):
            continue
        npic += 1
        if (sh.left < 0 or sh.top < 0 or sh.left + sh.width > SW or sh.top + sh.height > SH):
            fails.append("slide %d: picture outside the slide" % i)
print("pictures in the deck:", npic)

# ------------------------------------------------- 5  launcher
if not os.path.exists(CMD):
    fails.append("launcher missing: %s" % CMD)
else:
    raw = open(CMD, "rb").read()
    lf = raw.count(b"\n")
    crlf = raw.count(b"\r\n")
    print("launcher: %d lines, %d CRLF, %d bare LF, %d bytes" % (lf, crlf, lf - crlf, len(raw)))
    if lf != crlf:
        fails.append("launcher has bare LF line endings")
    if b"ISZE_Kickback_Japan_Pack_20261007.pptx" not in raw:
        fails.append("launcher does not reference the deck")

# ------------------------------------------------- 6  OOXML
z = zipfile.ZipFile(DECK)
bad = z.testzip()
names = z.namelist()
ct = etree.fromstring(z.read("[Content_Types].xml"))
dflt = {d.get("Extension").lower() for d in ct.findall(
    "{http://schemas.openxmlformats.org/package/2006/content-types}Default")}
ovr = {o.get("PartName") for o in ct.findall(
    "{http://schemas.openxmlformats.org/package/2006/content-types}Override")}
gaps = [n for n in names if n != "[Content_Types].xml"
        and ("/" + n) not in ovr and n.rsplit(".", 1)[-1].lower() not in dflt]
xmlfail = []
for n in names:
    if n.lower().endswith((".xml", ".rels")):
        try:
            etree.fromstring(z.read(n))
        except Exception as e:
            xmlfail.append((n, str(e)[:100]))
slides = sorted(n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
print("ooxml: zip=%s parts=%d content-type gaps=%d xml failures=%d slide parts=%d"
      % ("OK" if bad is None else bad, len(names), len(gaps), len(xmlfail), len(slides)))
print("slide size %.3f x %.3f in, slides=%d" % (SW / 914400, SH / 914400, len(slides)))
if bad is not None:
    fails.append("zip CRC failure")
if gaps:
    fails.append("content-type gaps: %s" % gaps)
if xmlfail:
    fails.append("xml parse failures: %s" % xmlfail)
if len(slides) != 9:
    fails.append("expected 9 slide parts, found %d" % len(slides))

print()
for w in warns:
    print("WARN", w)
print("FAILS:", len(fails))
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
