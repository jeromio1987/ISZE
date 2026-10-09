"""Final verification of the pass-2 rebuild.

A. package + relationship validation
B. banned strings: sell-out / Mode A / Mode B / 'reduced 20%' / 'top six' / IBX minimum months
C. wording: 'sales to dealer' present, no 'sell-out'
D. slides that should be untouched vs the pass-1 backup
E. verbatim text of the two new slides
F. speaker notes present on both new slides
"""
from __future__ import annotations
import sys
import subprocess
from pathlib import Path
from pptx import Presentation

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
NEW = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
OLD = HERE / "_build" / "_backup" / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pass1.pptx"
SCRATCH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_scratch")


def slide_texts(path):
    prs = Presentation(str(path))
    out = []
    for s in prs.slides:
        parts = []
        for sh in s.shapes:
            if sh.has_text_frame:
                parts.append(sh.text_frame.text)
            if getattr(sh, "has_table", False):
                for row in sh.table.rows:
                    for c in row.cells:
                        parts.append(c.text)
        out.append("\n".join(parts))
    return out


a = slide_texts(OLD)
b = slide_texts(NEW)
print("A. slides before:", len(a), " after:", len(b))

print("\nB. package + relationship validation")
for script in ("_ooxml_validate_20261007.py", "_ooxml_refs_20261007.py"):
    r = subprocess.run([sys.executable, str(SCRATCH / script), str(NEW)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("  %s -> %s" % (script, " | ".join(r.stdout.strip().splitlines()[-2:])))

print("\nC. banned-string scan (whole deck + notes)")
allt = "\n".join(b)
prs = Presentation(str(NEW))
notes = []
for i, s in enumerate(prs.slides, 1):
    if s.has_notes_slide and s.notes_slide.notes_text_frame is not None:
        notes.append(s.notes_slide.notes_text_frame.text)
alln = "\n".join(notes)
BANNED_VISIBLE = ["sell-out", "sellout", "sell out", "Mode A", "Mode B",
                  "reduced 20", "Maintenance family reduced", "top six",
                  "minimum months of stock", "minimum 3 months", "minimum of 3 months"]
hits = []
for bs in BANNED_VISIBLE:
    if bs.lower() in allt.lower():
        for line in allt.splitlines():
            if bs.lower() in line.lower():
                hits.append("[VISIBLE %s] %s" % (bs, line.strip()[:140]))
print("  visible-text hits:", len(hits))
for h in hits:
    print("   ", h)

print("\n  notes: does any note still assert the false claim as fact?")
for phrase in ["reduced 20%", "fell 20%", "cut 20%", "family fell 20"]:
    n = alln.lower().count(phrase)
    if n:
        print("    note contains %r x%d (check context is a correction)" % (phrase, n))

print("\nD. untouched slides (text must be identical to pass 1)")
# pass1 order: 1..9, 10=wider-review(old10), 11..20, 21=decision, and the two new ones at the end
old_by_label = {}
for i, t in enumerate(a, 1):
    old_by_label[i] = t
changed = []
for i, t in enumerate(b, 1):
    if i == 10 or i == 11 or i == 21:
        changed.append(i)
        continue
    # find the matching pass1 slide by its section label
    if t in a:
        continue
for i, t in enumerate(b, 1):
    if i in (10, 11, 21):
        continue
    if t not in a:
        print("    UNEXPECTED CHANGE on slide", i, "->", t[:70].replace("\n", " / "))
print("    slide 10 = new persuasion, 11 = wider review (corrected), 21 = european logic")
print("    slides expected to differ from pass1 by text:", changed)

print("\nE. verbatim text of the two new slides")
for idx in (10, 21):
    print("=" * 100)
    print("SLIDE %d" % idx)
    for sh in list(prs.slides)[idx - 1].shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            print("  [" + sh.name + "]")
            for line in sh.text_frame.text.splitlines():
                print("     " + line)

print("\nF. notes")
for idx in (10, 21):
    t = list(prs.slides)[idx - 1].notes_slide.notes_text_frame.text
    print("  slide %d notes chars: %d  starts: %r" % (idx, len(t), t[:40]))

print("\nG. slide 11 (corrected wider review) text")
for sh in list(prs.slides)[10].shapes:
    if sh.has_text_frame and sh.text_frame.text.strip():
        for line in sh.text_frame.text.splitlines():
            if any(k in line for k in ("Reporting shows", "net build sat", "Maintenance family",
                                       "Sources: headline", "brakes, body", "225,364")):
                print("     " + line)
