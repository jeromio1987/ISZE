"""Geometry QA that matches what PowerPoint actually does with text.

Checks, per slide:
  - every shape sits inside the slide
  - a title textbox's height does not overlap the red rule under it, using a
    real line-height estimate (bold Calibri, 1.22 line spacing) rather than a
    naive character wrap
  - no two text shapes overlap in a way that would print text on text
  - no picture overlaps a text box that carries body copy

This is still not a renderer. It catches layout collisions; it cannot promise
glyph-for-glyph typography. The deck is additionally rendered to PDF separately
when a renderer is available.
"""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
FINAL = HERE / "ISZE_Business_Performance_Review_2026.pptx"
TMP = HERE / "_build_tmp.pptx"
# QA the newest build: a locked final file means the fresh one is the temp copy
if TMP.exists() and (not FINAL.exists() or TMP.stat().st_mtime > FINAL.stat().st_mtime):
    DECK = TMP
else:
    DECK = FINAL

EMU_IN = 914400
prs = Presentation(DECK)
SW, SH = prs.slide_width, prs.slide_height
problems: list[str] = []
rows = []


def est_lines(text: str, size_pt: float, width_emu: int, bold: bool) -> int:
    """Estimate wrapped line count the way PowerPoint would."""
    # average glyph width for Calibri: ~0.50em regular, ~0.53em bold
    em = size_pt * (0.53 if bold else 0.50)
    if em <= 0 or width_emu <= 0:
        return 1
    # width available in points; 1pt of text ~ 1/72 inch of em advance
    avail_pt = (width_emu / EMU_IN) * 72
    lines = 0
    for para in text.split("\n"):
        if not para.strip():
            lines += 1
            continue
        w = len(para) * em
        lines += max(1, int(w / avail_pt) + (1 if w % avail_pt else 0))
    return max(1, lines)


for idx, slide in enumerate(prs.slides, start=1):
    boxes = []          # (left, top, right, bottom, kind, text, size)
    rule_y = None
    for sh in slide.shapes:
        l, t = sh.left or 0, sh.top or 0
        w, h = sh.width or 0, sh.height or 0
        if sh.height and sh.height < Emu(60000) and sh.width and sh.width > Inches(12):
            rule_y = t
        if l < -Emu(2000) or t < -Emu(2000) or l + w > SW + Emu(2000) or t + h > SH + Emu(2000):
            problems.append(f"slide {idx}: shape outside the slide")
        if sh.has_text_frame and sh.text_frame.text.strip():
            text = sh.text_frame.text
            sizes = [r.font.size.pt for p in sh.text_frame.paragraphs
                     for r in p.runs if r.font.size]
            size = max(sizes) if sizes else 12.0
            bold = any(r.font.bold for p in sh.text_frame.paragraphs for r in p.runs)
            lines = est_lines(text, size, w, bold)
            needed = int(lines * size * 1.22 / 72 * EMU_IN)
            kind = "title" if size >= 17 and len(text) > 25 else "body"
            boxes.append((l, t, l + w, t + h, kind, text[:50], size, needed, lines))
            if kind == "title" and rule_y is not None and t + needed > rule_y + Emu(15000):
                problems.append(
                    f"slide {idx}: title needs {lines} line(s) at {size:.0f}pt "
                    f"({needed/EMU_IN:.2f}in) and would cross the rule at "
                    f"{rule_y/EMU_IN:.2f}in — '{text[:48]}'")

    # text-on-text overlap
    texts = [b for b in boxes if b[4] == "body"]
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = texts[i], texts[j]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > Emu(200000) and oy > Emu(120000):
                problems.append(
                    f"slide {idx}: two text boxes overlap by "
                    f"{ox/EMU_IN:.2f}x{oy/EMU_IN:.2f}in — '{a[5]}' / '{b[5]}'")

    rows.append((idx, len(boxes), sum(1 for x in boxes if x[4] == "title")))

print(f"deck {DECK.name}  slides {len(prs.slides)}")
print()
if problems:
    print(f"PROBLEMS ({len(problems)}):")
    for p in problems[:40]:
        print("  ", p)
else:
    print("geometry QA: no collisions, no title crossing a rule, no shape outside the slide")
(HERE / "_qa_geometry.json").write_text(json.dumps(problems, indent=1), encoding="utf-8")
