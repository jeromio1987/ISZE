"""Final verification of the v2 deck after the slide addition + master repair.

A. text of slides 1..20 must be IDENTICAL to the backup (no existing slide touched)
B. banned strings absent: sell-out / Mode A / Mode B / the false '20%' maintenance claim /
   any 'minimum months of stock' figure for IBX
C. allowed-vs-forbidden wording present: 'sales to dealer' used
D. slide 21 text verbatim
E. slide 21 speaker notes present and carrying the corrections
"""
from __future__ import annotations
import sys
from pathlib import Path
from pptx import Presentation

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case")
NEW = HERE / "ISZE_Kickback_Management_Revised_v2_2026-10-07.pptx"
OLD = HERE / "_build" / "_backup" / "ISZE_Kickback_Management_Revised_v2_2026-10-07.orig.pptx"


def texts(path):
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


a = texts(OLD)
b = texts(NEW)
print("A. backup slides:", len(a), " new slides:", len(b))
diffs = []
for i in range(len(a)):
    if a[i] != b[i]:
        diffs.append(i + 1)
print("   slides whose text changed:", diffs if diffs else "NONE  (existing slides untouched)")
assert len(b) == len(a) + 1
assert not diffs

alltext = "\n".join(b) + "\n" + "\n".join(
    s.notes_slide.notes_text_frame.text for s in Presentation(str(NEW)).slides
    if s.has_notes_slide and s.notes_slide.notes_text_frame is not None)

print("\nB. banned-string scan")
BANNED = ["sell-out", "sellout", "sell out", "Mode A", "Mode B",
          "reduced 20", "Maintenance family reduced", "minimum months of stock",
          "minimum 3 months", "minimum months"]
hits = []
for bs in BANNED:
    if bs.lower() in alltext.lower():
        for line in alltext.splitlines():
            if bs.lower() in line.lower():
                hits.append("[%s] %s" % (bs, line.strip()[:150]))
print("   hits:", len(hits))
for h in hits:
    print("    ", h)

print("\nC. wording check on slide 21")
s21 = b[20]
print("   'sales to dealer' occurrences:", s21.lower().count("sales to dealer"))
print("   'sales-to-dealer' occurrences:", s21.lower().count("sales-to-dealer"))
for tok in ["16.2%", "25.0%", "2.2 months", "3.0-month", "EUR 764,436", "EUR 678,464",
            "EUR 29.19M", "EUR 31.82M", "EUR 2.63M", "EUR 52.1M", "EUR 29.6M",
            "95%", "92%", "15 lines", "60 to 75", "75 to 90", "90 to 120",
            "32 to 63", "21 reported months", "17 of 24", "January 2025", "14,662", "15,007",
            "brakes, body and electrical"]:
    print("   contains %-30s %s" % (tok, tok in s21 or tok in alltext))

print("\nC2. slide 21 text verbatim")
print("-" * 90)
for sh in list(Presentation(str(NEW)).slides)[20].shapes:
    if sh.has_text_frame and sh.text_frame.text.strip():
        print("[" + sh.name + "]")
        print(sh.text_frame.text)
        print()
print("-" * 90)

print("E. slide 21 notes")
n = list(Presentation(str(NEW)).slides)[20].notes_slide.notes_text_frame.text
print("   notes chars:", len(n))
print("   mentions maintenance correction:", "14,662" in n and "15,007" in n)
print("   mentions no order-mix claim:", "No order-mix improvement" in n)
print("   mentions IBX band not minimum:", "not a minimum" in n)
